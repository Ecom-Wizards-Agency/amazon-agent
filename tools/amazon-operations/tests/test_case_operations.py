import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

PATH = Path(__file__).resolve().parents[1] / 'operations.py'
spec = importlib.util.spec_from_file_location('case_test_operations', PATH)
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)


class CaseOperationsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.service = op.Operations(self.root / 'operations',case_state_dir=self.root)
        self.cases = op.case_tools()
        self.patcher = patch.object(op, 'case_tools', return_value=self.cases)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        env_patch=patch.object(op,'session_environment',return_value={'CDP_PORT':'9223'})
        env_patch.start();self.addCleanup(env_patch.stop)
        self.account = {'client_slug':'brand','profile_key':'brand-us','marketplace':'US'}
        self.binding = {'registry_id':'registered-case','owner_revision':1,'mandate_id':'request-1','mandate_revision':1,'authorization_revision':1}
        self.request = {'schema_version':1,'operation_id':'reply-1','operation':'case.reply','account':self.account,'targets':[{'case_id':'12345678'}],'inputs':{
            'signed_body':'Please confirm the remaining fee.\n\nBest,\nDanica',
            'owner':{'member_id':'UDANICA','signature_name':'Danica','revision':1},
            'mandate':{'id':'request-1','revision':1},'case_binding':self.binding,
            'attachments':[],'baseline':{'observed_at':op.now(),'contact_ids':['old'],'case_ids':['12345678']}}}

    def prepare(self):
        result = self.service.prepare(self.request)
        self.plan = json.loads(Path(result['plan_path']).read_text())
        return result

    def execute_request(self,result):
        return {'schema_version':1,'operation_id':result['operation_id'],'plan_hash':result['plan_hash'],'grant':{
            'execute':True,'account':self.account,'operation':self.request['operation'],'targets':self.request['targets'],
            'plan_hash':result['plan_hash'],'case_binding':self.binding,'allow_live_canary':True}}

    def started(self):
        result=self.prepare()
        state=self.service.view(self.service.directory(result['operation_id']))
        self.service.persist(self.service.directory(result['operation_id']),state,'uncertain',execution_started_at=op.now(),effects_started=True)
        return result

    def observation(self,result):
        when=op.now()
        return {'status':'collected','account':self.account,'plan_hash':result['plan_hash'],'observed_at':when,'history_complete':True,
                'case_id':'12345678','login_identity':{'session':'grimoire','login_name':None},'contacts':[
                    {'id':'new','is_amazon':False,'timestamp':when,'message':self.request['inputs']['signed_body'],'attachments':[]}]}

    def reconcile(self,result,observation):
        with patch.object(self.service,'run_collector',return_value=observation):
            return self.service.reconcile({'schema_version':1,'operation_id':result['operation_id'],'plan_hash':result['plan_hash']})

    def test_alternate_state_directory_cannot_create_second_send_journal(self):
        for root in [self.root/'alternate',self.root/'operations']:
            alternate=op.Operations(root)
            with self.assertRaisesRegex(ValueError,'canonical shared case journal'):
                alternate.prepare(self.request)

    def test_typed_case_target_does_not_accept_sku_or_plain_string(self):
        for targets in [['12345678'],[{'sku':'12345678'}],[{'case_id':'12345678','issue_key':'x'}]]:
            self.request['targets']=targets
            with self.assertRaisesRegex(ValueError,'target'):self.prepare()

    def test_stable_plan_and_owner_signature(self):
        first=self.prepare()
        self.assertEqual(first['plan_hash'],self.service.prepare(self.request)['plan_hash'])
        self.assertEqual(self.plan['body']['owner']['member_id'],'UDANICA')
        self.request['inputs']['signed_body']='Different\nVictor'
        with self.assertRaisesRegex(ValueError,'reused'):self.prepare()

    def test_attachment_is_copied_and_checked_after_preparation(self):
        path=self.root/'evidence.pdf';path.write_bytes(b'%PDF-evidence')
        self.request['inputs']['attachments']=[{'name':'evidence.pdf','path':str(path),'sha256':op.file_hash(path)}]
        result=self.prepare(); copied=Path(self.plan['body']['attachments'][0]['path'])
        self.assertNotEqual(copied,path)
        path.write_bytes(b'changed original')
        self.assertEqual(copied.read_bytes(),b'%PDF-evidence')
        copied.write_bytes(b'changed copy')
        with self.assertRaisesRegex(ValueError,'artifact changed'):self.service.execute(self.execute_request(result))

    def test_stale_owner_is_checked_before_adapter_call(self):
        result=self.prepare()
        registry=Mock();registry.validate_send_binding.side_effect=ValueError('stale owner')
        with patch.object(self.cases,'case_service',return_value=registry),patch.object(op.subprocess,'run') as runner:
            with self.assertRaisesRegex(ValueError,'stale owner'):self.service.execute(self.execute_request(result))
            runner.assert_not_called()

    def test_unknown_submission_is_never_retried(self):
        result=self.prepare()
        with patch.object(self.cases,'case_service',return_value=Mock()),patch.object(op.subprocess,'run',side_effect=op.subprocess.TimeoutExpired('node',1)) as runner:
            self.assertEqual(self.service.execute(self.execute_request(result))['status'],'uncertain')
            self.assertEqual(self.service.execute(self.execute_request(result))['status'],'uncertain')
            self.assertEqual(runner.call_count,1)

    def test_failed_response_after_attempt_remains_uncertain(self):
        result=self.prepare();response=Mock(stdout=json.dumps({'plan_hash':result['plan_hash'],'status':'failed','attempted':True}))
        with patch.object(self.cases,'case_service',return_value=Mock()),patch.object(op.subprocess,'run',return_value=response):
            self.assertEqual(self.service.execute(self.execute_request(result))['status'],'uncertain')

    def test_exact_new_correspondence_verifies_danica(self):
        result=self.started();observed=self.observation(result)
        verified=self.reconcile(result,observed)
        self.assertEqual(verified['status'],'verified')
        self.assertEqual(verified['case_id'],'12345678')
        self.assertEqual(verified['owner']['signature_name'],'Danica')

    def test_old_contact_amazon_echo_and_wrong_signature_do_not_verify(self):
        for change in [{'id':'old'},{'is_amazon':True},{'message':'Please confirm the remaining fee.\n\nBest,\nVictor'}]:
            self.request['operation_id']='run-'+str(len(list(self.service.root.iterdir())))
            result=self.started();observed=self.observation(result);observed['contacts'][0].update(change)
            self.assertEqual(self.reconcile(result,observed)['status'],'uncertain')

    def test_missing_attachment_digest_cannot_verify(self):
        path=self.root/'proof.txt';path.write_text('proof')
        self.request['inputs']['attachments']=[{'name':'proof.txt','path':str(path),'sha256':op.file_hash(path)}]
        result=self.started();observed=self.observation(result)
        observed['contacts'][0]['attachments']=[{'name':'proof.txt'}]
        self.assertEqual(self.reconcile(result,observed)['status'],'uncertain')
        observed['contacts'][0]['attachments'][0]['sha256']=op.file_hash(path)
        self.assertEqual(self.reconcile(result,observed)['status'],'verified')

    def test_incomplete_history_and_caller_evidence_are_rejected(self):
        result=self.started();observed=self.observation(result);observed['history_complete']=False
        with self.assertRaisesRegex(ValueError,'complete correspondence'):self.reconcile(result,observed)
        with self.assertRaisesRegex(ValueError,'fresh correspondence'):
            self.service.reconcile({'schema_version':1,'operation_id':result['operation_id'],'plan_hash':result['plan_hash'],'evidence':self.observation(result)})

    def test_multiple_identical_new_contacts_are_uncertain(self):
        result=self.started();observed=self.observation(result)
        observed['contacts'].append(dict(observed['contacts'][0],id='second'))
        self.assertEqual(self.reconcile(result,observed)['reason'],'case_readback_ambiguous')

    def test_create_targets_issue_and_requires_new_case_id(self):
        self.request['operation']='case.create';self.request['targets']=[{'issue_key':'shipment-defect'}]
        self.request['inputs']['subject']='Shipment defect';self.request['inputs']['baseline']['duplicate_query']='Shipment defect'
        result=self.started();observed=self.observation(result);observed['subject']='Shipment defect'
        self.assertEqual(self.reconcile(result,observed)['status'],'uncertain')
        observed['case_id']='99999999'
        self.assertEqual(self.reconcile(result,observed)['status'],'verified')

    def test_full_approved_signature_can_include_company_after_name(self):
        self.request['inputs']['owner']['signature']='Danica\nEcom Wizards'
        self.request['inputs']['signed_body']+='\nEcom Wizards'
        self.assertEqual(self.prepare()['status'],'prepared')

    def test_validated_adapter_boolean_requires_trusted_verified_canary(self):
        result=self.prepare();request=self.execute_request(result)
        request['grant'].pop('allow_live_canary');request['grant']['allow_validated_adapter']=True
        with patch.object(self.cases,'case_service',return_value=Mock()),patch.object(self.cases,'validate_adapter_readiness',side_effect=ValueError('verified canary missing')),patch.object(op.subprocess,'run') as runner:
            with self.assertRaisesRegex(ValueError,'verified canary'):self.service.execute(request)
            runner.assert_not_called()

    def test_readiness_requires_matching_journal_and_independent_evidence(self):
        directory=self.root/'cases'/'operations'/'canary-1';directory.mkdir(parents=True)
        evidence=directory/'readback.json';evidence.write_text(json.dumps({'account':self.account,'plan_hash':'hash','history_complete':True}))
        journal={'verified':True,'status':'verified','account':self.account,'operation':'case.reply','plan_hash':'hash','evidence_path':str(evidence)}
        (directory/'journal.json').write_text(json.dumps(journal))
        readiness={'account':self.account,'reply_access':True,'create_access':False,'canaries':{'case.reply':{'operation_id':'canary-1','plan_hash':'hash','evidence_path':str(evidence),'verified_at':op.now()}}}
        policy=self.root/'policy.json';policy.write_text(json.dumps({'profile_readiness':{'brand-us':readiness}}))
        check=lambda:self.cases.validate_adapter_readiness(self.account,'case.reply',policy_path=policy,cases_root=self.root/'cases')
        self.assertEqual(check(),readiness)
        journal['status']='uncertain';(directory/'journal.json').write_text(json.dumps(journal))
        with self.assertRaisesRegex(ValueError,'does not verify'):check()
        journal['status']='verified';journal['operation']='case.create';(directory/'journal.json').write_text(json.dumps(journal))
        with self.assertRaisesRegex(ValueError,'does not verify'):check()

if __name__=='__main__':unittest.main()
