import concurrent.futures
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / 'case_service.py'
spec = importlib.util.spec_from_file_location('case_service_under_test', PATH)
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class CaseServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.policy = self.root / 'policy.json'
        self.policy_value = {'members': {
            'UDANICA': {'signature_name': 'Danica', 'signature': 'Danica\nEcom Wizards', 'approved': True},
            'UVICTOR': {'signature_name': 'Victor Uhl', 'signature': 'Victor Uhl\nEcom Wizards', 'approved': True}},
            'attended_operator_id': 'UVICTOR'}
        self.policy.write_text(json.dumps(self.policy_value))
        self.now = dt.datetime(2026, 9, 9, 10, tzinfo=core.ZONE)
        self.service = core.CaseService(self.root / 'cases', self.policy, clock=lambda: self.now)
        self.account = {'profile_key': 'brand-us', 'client_slug': 'brand', 'marketplace': 'US', 'seller_id': 'SELLER', 'marketplace_id': 'ATVPDKIKX0DER'}

    def auth(self, member='UDANICA', message='100.1'):
        return {'kind': 'slack', 'requester_id': member, 'source': {'channel': 'CCLIENT', 'message_ts': message, 'message_digest': 'digest-' + message, 'requester_id': member}}

    def start(self, member='UDANICA', message='100.1', issue='shipment:001:defect'):
        return self.service.start({'account': self.account, 'issue_key': issue, 'subject': 'Review shipment defect', 'authorization': self.auth(member, message)})['case']

    def prepare(self, case, purpose='create', body='Please confirm the defect review.', daily_key=None):
        return self.service.prepare_send({'registry_id': case['registry_id'], 'purpose': purpose, 'body': body, 'daily_key': daily_key, 'baseline': {'observed_at': self.now.isoformat(), 'contact_ids': case['contact_ids'], 'case_ids': [case['case_id']] if case['case_id'] else []}, 'assessment': self.assessment(body)})

    def assessment(self, body):
        return {'decision': 'routine', 'category': 'status_check', 'reason': 'Requests status of the evidenced existing defect review', 'evidence': [{'kind': 'request', 'source_id': 'request-100.1'}], 'body_sha256': hashlib.sha256(body.encode()).hexdigest()}

    def receipt(self, case, prepared, status='verified', remote_id='21912345678'):
        op_id = prepared['operation_request']['operation_id']
        path = self.service.root / 'operations' / op_id / 'journal.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({'operation_id': op_id, 'account': self.account, 'operation': prepared['operation_request']['operation'], 'status': status, 'verified': status == 'verified', 'effects_started': status in {'uncertain', 'verified'}, 'case_id': remote_id, 'updated_at': self.now.isoformat()}))
        return self.service.record_receipt({'registry_id': case['registry_id'], 'operation_id': op_id, 'receipt_path': str(path)})

    def created(self):
        case = self.start()
        return self.receipt(case, self.prepare(case))['case']

    def observe(self, case, contacts=None, **extra):
        contacts = [{**c, 'timestamp': c.get('timestamp') or (self.now + dt.timedelta(seconds=1)).isoformat()} for c in contacts or []]
        key = f'{self.now.date().isoformat()}:{case["registry_id"]}'
        observed = {'observed_at': self.now.isoformat(), 'account': self.account, 'case_id': case['case_id'], 'case_status': 'Pending Amazon action', 'history_complete': True, 'contacts': contacts or [], 'can_edit': True, 'assessment': {'decision': 'routine', 'reason': 'Evidence-backed routine status request', 'evidence_contact_ids': [c['id'] for c in contacts or []]}, **extra}
        return self.service.observe({'registry_id': case['registry_id'], 'daily_key': key, 'observation': observed})

    def assertCode(self, code, fn):
        with self.assertRaises(core.CaseError) as caught:
            fn()
        self.assertEqual(code, caught.exception.code)

    def test_shared_issue_keeps_original_owner_and_requester(self):
        first = self.start()
        second = self.start('UVICTOR', '100.2')
        self.assertEqual(first['registry_id'], second['registry_id'])
        self.assertEqual('UDANICA', second['owner']['member_id'])
        self.assertEqual('UDANICA', second['requester_id'])
        self.assertEqual(1, len(self.service.list()['cases']))

    def test_concurrent_start_and_prepare_share_one_action(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            cases = list(executor.map(lambda _: self.start(), range(8)))
            prepared = list(executor.map(self.prepare, cases))
        self.assertEqual(1, len({c['registry_id'] for c in cases}))
        self.assertEqual(1, len({p['operation_request']['operation_id'] for p in prepared}))
        self.assertEqual(1, len(self.service.list()['cases'][0]['actions']))

    def test_source_cannot_authorize_another_issue(self):
        self.start()
        self.assertCode('source_reused', lambda: self.start(issue='unrelated'))

    def test_explicit_new_case_assignment_keeps_requester_distinct(self):
        authorization = self.auth('UVICTOR')
        request = {'account': self.account, 'issue_key': 'assigned', 'subject': 'Assigned case', 'assigned_owner': 'UDANICA', 'authorization': authorization}
        self.assertCode('unverified_assignment', lambda: self.service.start(request))
        authorization['source']['assigned_owner'] = 'UDANICA'
        case = self.service.start(request)['case']
        self.assertEqual('UVICTOR', case['requester_id'])
        self.assertEqual('UDANICA', case['owner']['member_id'])

    def test_import_owner_needs_attribution_evidence(self):
        request = {'account': self.account, 'issue_key': 'legacy', 'subject': 'Legacy case', 'case_id': '10001', 'owner_member_id': 'UDANICA'}
        self.assertCode('missing_owner_evidence', lambda: self.service.adopt(request))
        request['owner_evidence'] = {'kind': 'seller_signature', 'member_id': 'UDANICA', 'source_id': 'contact-123', 'excerpt': 'Best regards, Danica'}
        case = self.service.adopt(request)['case']
        self.assertEqual('UDANICA', case['owner']['member_id'])
        self.assertIsNone(case['mandate'])

    def adoption(self, case, remote_id='12345678', owner=None):
        observation = {'account': self.account, 'observed_at': self.now.isoformat(), 'history_complete': True, 'cases': [{'case_id': remote_id, 'history_complete': True, 'subject': 'Existing defect review', 'case_status': 'Work in progress', 'contacts': [{'id': 'seller-original', 'is_amazon': False, 'message': 'Please review this defect.\n\nVictor Uhl', 'timestamp': (self.now - dt.timedelta(days=1)).isoformat()}]}]}
        request = {'account': self.account, 'issue_key': case['issue_key'], 'subject': case['subject'], 'case_id': remote_id, 'candidate_evidence': {'observation': observation, 'matched_case_id': remote_id, 'match_reason': 'Same shipment identifier and same defect request'}}
        if owner:
            request.update(owner_member_id=owner, owner_evidence={'kind': 'seller_signature', 'member_id': owner, 'source_id': 'seller-original', 'excerpt': 'Victor Uhl'})
        return request

    def test_pending_case_adopts_existing_with_unknown_owner_and_blocks_send(self):
        case = self.start()
        old_inputs = self.prepare(case)['operation_request']['inputs']
        result = self.service.adopt(self.adoption(case))
        self.assertEqual('12345678', result['case']['case_id'])
        self.assertIsNone(result['case']['owner'])
        self.assertFalse(result['send_authorized'])
        self.assertEqual(['reply', 'chaser'], result['case']['mandate']['permitted_actions'])
        self.assertTrue(result['case']['actions'][0]['invalidated'])
        self.assertCode('unknown_owner', lambda: self.service.validate_binding(old_inputs['case_binding'], old_inputs))
        self.assertEqual('observe', self.service.daily_due()['cases'][0]['next_action'])

    def test_pending_adoption_uses_evidenced_historical_owner(self):
        case = self.start()
        result = self.service.adopt(self.adoption(case, owner='UVICTOR'))
        self.assertEqual('UDANICA', result['case']['requester_id'])
        self.assertEqual('UVICTOR', result['case']['owner']['member_id'])
        self.assertEqual(2, result['case']['owner']['revision'])
        self.assertTrue(result['send_authorized'])
        self.assertEqual('existing', self.service.adopt(self.adoption(case, owner='UVICTOR'))['status'])

    def test_pending_adoption_requires_real_candidate_and_signature(self):
        case = self.start()
        request = self.adoption(case, owner='UDANICA')
        self.assertCode('owner_evidence_mismatch', lambda: self.service.adopt(request))
        request = self.adoption(case)
        request['candidate_evidence']['observation']['account'] = {**self.account, 'seller_id': 'OTHER'}
        self.assertCode('candidate_evidence_mismatch', lambda: self.service.adopt(request))
        request.pop('candidate_evidence')
        self.assertCode('missing_candidate_evidence', lambda: self.service.adopt(request))

    def test_attempted_creation_cannot_convert_to_another_existing_case(self):
        case = self.start()
        prepared = self.prepare(case)
        self.receipt(case, prepared, 'uncertain')
        self.assertCode('creation_attempted', lambda: self.service.adopt(self.adoption(case)))

    def test_duplicate_pending_request_reuses_already_registered_case(self):
        existing = self.service.adopt({'account': self.account, 'case_id': '12345678', 'issue_key': 'legacy', 'subject': 'Existing defect review', 'owner_member_id': 'UVICTOR', 'owner_evidence': {'kind': 'seller_signature', 'member_id': 'UVICTOR', 'source_id': 'seller-original', 'excerpt': 'Victor Uhl'}})['case']
        pending = self.start()
        old_inputs = self.prepare(pending)['operation_request']['inputs']
        result = self.service.adopt(self.adoption(pending))
        self.assertEqual(existing['registry_id'], result['case']['registry_id'])
        self.assertEqual('UVICTOR', result['case']['owner']['member_id'])
        self.assertEqual(1, len(self.service.list()['cases']))
        self.assertEqual(1, len(self.service.list()['superseded']))
        self.assertEqual(existing['registry_id'], self.start()['registry_id'])
        self.assertCode('stale_case_binding', lambda: self.service.validate_binding(old_inputs['case_binding'], old_inputs))

    def test_reuse_preserves_existing_active_mandate_and_pending_reply(self):
        existing = self.created()
        self.now += dt.timedelta(days=1)
        observed = self.observe(existing, [{'id': 'amazon-question', 'is_amazon': True}])
        reply = self.prepare(observed['case'], 'reply', daily_key=observed['daily_key'])
        pending = self.start('UVICTOR', '200.2', issue='same-issue-other-wording')
        result = self.service.adopt(self.adoption(pending, remote_id=existing['case_id']))
        self.assertEqual(existing['mandate'], result['case']['mandate'])
        inputs = reply['operation_request']['inputs']
        self.assertEqual('valid', self.service.validate_binding(inputs['case_binding'], inputs, operation_id=reply['operation_request']['operation_id'])['status'])

    def test_requester_removed_after_delegation_revokes_effective_authority(self):
        authorization = self.auth('UVICTOR')
        authorization['source']['assigned_owner'] = 'UDANICA'
        case = self.service.start({'account': self.account, 'issue_key': 'assigned', 'subject': 'Assigned case', 'assigned_owner': 'UDANICA', 'authorization': authorization})['case']
        inputs = self.prepare(case)['operation_request']['inputs']
        self.policy_value['members']['UVICTOR']['approved'] = False
        self.policy.write_text(json.dumps(self.policy_value))
        self.assertCode('unknown_owner', lambda: self.service.validate_binding(inputs['case_binding'], inputs))

    def test_caller_cannot_supply_signature(self):
        case = self.start()
        result = self.prepare(case)
        self.assertTrue(result['operation_request']['inputs']['signed_body'].endswith('Danica\nEcom Wizards'))
        self.assertNotIn('Victor', result['operation_request']['inputs']['signed_body'])

    def test_initial_creation_requires_scoped_body_review(self):
        case = self.start()
        body = 'We admit liability and accept a $10,000 settlement.'
        request = {'registry_id': case['registry_id'], 'purpose': 'create', 'body': body, 'baseline': {'observed_at': self.now.isoformat(), 'contact_ids': [], 'case_ids': []}}
        self.assertCode('missing_scope_assessment', lambda: self.service.prepare_send(request))
        for category in ['appeal', 'admission', 'financial_commitment', 'refund', 'account_change', 'unsupported_claim']:
            request['assessment'] = {**self.assessment(body), 'category': category}
            self.assertCode('scope_requires_human', lambda: self.service.prepare_send(request))
        request['assessment'] = {**self.assessment(body), 'decision': 'human'}
        self.assertCode('scope_requires_human', lambda: self.service.prepare_send(request))

    def test_scope_assessment_must_bind_content_and_identified_evidence(self):
        case = self.start()
        body = 'Please confirm review status.'
        request = {'registry_id': case['registry_id'], 'purpose': 'create', 'body': body, 'baseline': {'observed_at': self.now.isoformat(), 'contact_ids': [], 'case_ids': []}, 'assessment': self.assessment('Different body')}
        self.assertCode('scope_body_mismatch', lambda: self.service.prepare_send(request))
        request['assessment'] = {**self.assessment(body), 'evidence': []}
        self.assertCode('missing_scope_evidence', lambda: self.service.prepare_send(request))
        request['assessment'] = {**self.assessment(body), 'evidence': [{'kind': 'case_contact', 'source_id': 'nonexistent'}]}
        self.assertCode('scope_evidence_mismatch', lambda: self.service.prepare_send(request))

    def test_prepared_scope_cannot_be_changed_before_execution(self):
        case = self.start()
        inputs = self.prepare(case)['operation_request']['inputs']
        inputs['scope_assessment']['reason'] = 'A different assessment'
        self.assertCode('unprepared_message', lambda: self.service.validate_binding(inputs['case_binding'], inputs))

    def test_distinct_issue_candidates_require_complete_nonmatch_review(self):
        case = self.start()
        body = 'Please review the separately documented shipment defect.'
        request = {'registry_id': case['registry_id'], 'purpose': 'create', 'body': body, 'baseline': {'observed_at': self.now.isoformat(), 'case_ids': ['12345678', '23456789'], 'contact_ids': [], 'duplicate_query': 'FBA12345678'}, 'assessment': self.assessment(body)}
        self.assertCode('missing_duplicate_review', lambda: self.service.prepare_send(request))
        request['duplicate_review'] = [{'case_id': '12345678', 'reason': 'This case concerns a different shipment fee'}]
        self.assertCode('missing_duplicate_review', lambda: self.service.prepare_send(request))
        request['duplicate_review'].append({'case_id': '23456789', 'reason': 'This case concerns missing units, not the placement defect'})
        prepared = self.service.prepare_send(request)['operation_request']
        self.assertEqual(request['duplicate_review'], prepared['inputs']['duplicate_review'])
        self.assertEqual(request['baseline'], prepared['inputs']['baseline'])
        altered = copy.deepcopy(prepared)
        altered['inputs']['duplicate_review'][0]['reason'] = 'Changed after case review'
        inputs = prepared['inputs']
        self.assertCode('unprepared_message', lambda: self.service.validate_binding(inputs['case_binding'], inputs, operation_id=prepared['operation_id'], request_hash=core.digest(altered)))
        self.assertEqual('valid', self.service.validate_binding(inputs['case_binding'], inputs, operation_id=prepared['operation_id'], request_hash=core.digest(prepared))['status'])

    def test_attended_and_daily_replies_share_the_scope_gate(self):
        authorization = {'kind': 'attended', 'requester_id': 'UVICTOR', 'source': {'session_id': 's1', 'instruction': 'Open and manage this case'}}
        case = self.service.start({'account': self.account, 'issue_key': 'attended', 'subject': 'Review defect', 'authorization': authorization})['case']
        case = self.receipt(case, self.prepare(case))['case']
        self.now += dt.timedelta(days=1)
        observed = self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}])
        request = {'registry_id': case['registry_id'], 'purpose': 'reply', 'daily_key': observed['daily_key'], 'body': 'We accept the requested refund.', 'baseline': {'observed_at': self.now.isoformat(), 'contact_ids': ['amazon-1'], 'case_ids': [case['case_id']]}}
        self.assertCode('missing_scope_assessment', lambda: self.service.prepare_send(request))
        request['assessment'] = {**self.assessment(request['body']), 'category': 'refund'}
        self.assertCode('scope_requires_human', lambda: self.service.prepare_send(request))

    def test_attended_operator_requires_configured_identity_and_instruction(self):
        request = {'account': self.account, 'issue_key': 'attended', 'subject': 'Case', 'authorization': {'kind': 'attended', 'requester_id': 'UDANICA', 'source': {'session_id': 's1', 'instruction': 'Open the case'}}}
        self.assertCode('operator_mismatch', lambda: self.service.start(request))
        request['authorization']['requester_id'] = 'UVICTOR'
        self.assertEqual('UVICTOR', self.service.start(request)['case']['owner']['member_id'])

    def test_import_does_not_authorize_or_invent_owner(self):
        case = self.service.adopt({'account': self.account, 'issue_key': 'legacy', 'subject': 'Legacy case', 'case_id': '10001', 'historical': {'contact_ids': ['old'], 'source_state_path': '/legacy.json'}})['case']
        self.assertIsNone(case['owner'])
        self.assertIsNone(case['mandate'])
        self.assertEqual(['old'], case['contact_ids'])
        self.assertCode('unknown_owner', lambda: self.prepare(case, 'reply'))
        due = self.service.daily_due()['cases'][0]
        self.assertTrue(due['owner_issue_new'])
        self.assertEqual('observe', due['next_action'])
        self.assertFalse(due['send_authorized'])
        self.assertFalse(self.service.daily_due()['cases'][0]['owner_issue_new'])

    def test_request_for_unassigned_import_reports_owner_once(self):
        self.service.adopt({'account': self.account, 'issue_key': 'legacy', 'subject': 'Legacy case', 'case_id': '10001'})
        request = {'account': self.account, 'issue_key': 'legacy', 'subject': 'Legacy case', 'authorization': self.auth()}
        self.assertTrue(self.service.start(request)['report_owner_issue'])
        self.assertFalse(self.service.start(request)['report_owner_issue'])

    def test_reassignment_invalidates_old_signed_message(self):
        case = self.start()
        prepared = self.prepare(case)
        self.service.reassign({'registry_id': case['registry_id'], 'owner_member_id': 'UVICTOR', 'authorization': self.auth('UVICTOR', '100.2')})
        inputs = prepared['operation_request']['inputs']
        self.assertCode('stale_case_binding', lambda: self.service.validate_binding(inputs['case_binding'], inputs))
        fresh = self.prepare(case)
        self.assertNotEqual(prepared['operation_request']['operation_id'], fresh['operation_request']['operation_id'])
        self.assertTrue(fresh['operation_request']['inputs']['signed_body'].endswith('Victor Uhl\nEcom Wizards'))

    def test_concurrent_admin_replay_changes_revisions_once(self):
        case = self.start()
        request = {'registry_id': case['registry_id'], 'owner_member_id': 'UVICTOR', 'authorization': self.auth('UVICTOR', '100.2')}
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            outcomes = list(executor.map(lambda _: self.service.reassign(request), range(8)))
        self.assertEqual(1, sum(result['status'] == 'reassigned' for result in outcomes))
        self.assertEqual(2, self.service.list()['cases'][0]['owner']['revision'])
        revoke = {'registry_id': case['registry_id'], 'authorization': self.auth('UVICTOR', '100.3')}
        first = self.service.revoke(revoke)
        second = self.service.revoke(revoke)
        self.assertEqual(first['case']['authorization_revision'], second['case']['authorization_revision'])
        self.assertEqual('already_revoked', second['status'])

    def test_admin_source_edit_requires_new_instruction(self):
        case = self.start()
        request = {'registry_id': case['registry_id'], 'owner_member_id': 'UVICTOR', 'authorization': self.auth('UVICTOR', '100.2')}
        self.service.reassign(request)
        request['owner_member_id'] = 'UDANICA'
        self.assertCode('admin_source_changed', lambda: self.service.reassign(request))

    def test_revoke_and_policy_change_checked_at_send(self):
        case = self.start()
        inputs = self.prepare(case)['operation_request']['inputs']
        self.assertEqual('valid', self.service.validate_binding(inputs['case_binding'], inputs)['status'])
        self.policy_value['members']['UDANICA']['approved'] = False
        self.policy.write_text(json.dumps(self.policy_value))
        self.assertCode('unknown_owner', lambda: self.service.validate_binding(inputs['case_binding'], inputs))
        self.policy_value['members']['UDANICA']['approved'] = True
        self.policy.write_text(json.dumps(self.policy_value))
        self.service.revoke({'registry_id': case['registry_id'], 'authorization': self.auth('UVICTOR', '100.2')})
        self.assertCode('mandate_revoked', lambda: self.service.validate_binding(inputs['case_binding'], inputs))

    def test_message_tampering_and_pending_content_changes_block(self):
        case = self.start()
        inputs = self.prepare(case)['operation_request']['inputs']
        inputs['signed_body'] = 'Different claim\n\nDanica\nEcom Wizards'
        self.assertCode('unprepared_message', lambda: self.service.validate_binding(inputs['case_binding'], inputs))
        self.assertCode('immutable_action', lambda: self.prepare(case, body='Changed claim'))

    def test_unknown_delivery_never_creates_second_send(self):
        case = self.start()
        prepared = self.prepare(case)
        self.assertEqual('reconciliation_required', self.receipt(case, prepared, 'uncertain')['status'])
        self.assertEqual(prepared, self.prepare(case))
        self.assertEqual('recorded', self.receipt(case, prepared)['status'])
        self.assertEqual('already_recorded', self.receipt(case, prepared)['status'])
        self.assertCode('already_created', lambda: self.prepare(case))

    def test_reassign_during_uncertain_creation_requires_reconciliation(self):
        case = self.start()
        prepared = self.prepare(case)
        self.receipt(case, prepared, 'uncertain')
        self.service.reassign({'registry_id': case['registry_id'], 'owner_member_id': 'UVICTOR', 'authorization': self.auth('UVICTOR', '100.2')})
        self.assertCode('reconciliation_required', lambda: self.prepare(case))
        # Historical delivery still reconciles after ownership changes.
        self.assertEqual('recorded', self.receipt(case, prepared)['status'])

    def test_daily_checks_start_at_nine_bangkok(self):
        self.created()
        self.now = self.now.replace(hour=8, minute=59)
        self.assertEqual('not_due', self.service.daily_due()['status'])
        self.now = self.now.replace(hour=9, minute=0)
        self.assertEqual(1, len(self.service.daily_due()['cases']))

    def test_daily_observation_idempotent_even_if_later_reply_arrives(self):
        case = self.created()
        first = self.observe(case)
        second = self.observe(case, [{'id': 'amazon-new', 'is_amazon': True}])
        self.assertEqual('wait', first['next_action'])
        self.assertEqual('already_observed', second['status'])
        self.assertEqual('wait', second['next_action'])
        self.assertEqual([], self.service.daily_due()['cases'])

    def test_daily_reply_retains_owner_once_and_expires_next_day(self):
        case = self.created()
        observed = self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}])
        prepared = self.prepare(observed['case'], 'reply', daily_key=observed['daily_key'])
        inputs = prepared['operation_request']['inputs']
        self.assertEqual('UDANICA', inputs['owner']['member_id'])
        self.now += dt.timedelta(days=1)
        self.assertCode('daily_not_observed', lambda: self.service.validate_binding(inputs['case_binding'], inputs))

    def test_confirmed_daily_reply_cannot_send_twice(self):
        case = self.created()
        observed = self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}])
        prepared = self.prepare(observed['case'], 'reply', daily_key=observed['daily_key'])
        self.receipt(case, prepared)
        self.assertCode('daily_action_blocked', lambda: self.prepare(observed['case'], 'reply', daily_key=observed['daily_key']))
        self.assertEqual([], self.service.daily_due()['cases'])

    def test_three_business_days_and_two_unanswered_chasers(self):
        case = self.created()
        self.assertEqual('2026-09-14T09:00:00+07:00', case['next_due_at'])
        for date in ['2026-09-14T10:00:00+07:00', '2026-09-17T10:00:00+07:00']:
            self.now = core.timestamp(date)
            observed = self.observe(case)
            self.assertEqual('chaser', observed['next_action'])
            prepared = self.prepare(observed['case'], 'chaser', daily_key=observed['daily_key'])
            case = self.receipt(case, prepared)['case']
        self.now = core.timestamp('2026-09-22T10:00:00+07:00')
        self.assertEqual('human', self.observe(case)['next_action'])
        self.now += dt.timedelta(days=1)
        observed = self.observe(case, [{'id': 'amazon-finally', 'is_amazon': True}])
        self.assertEqual(0, observed['case']['unanswered_chasers'])
        self.assertEqual('reply', observed['next_action'])

    def test_promised_deadline_overrides_default_and_survives_reply(self):
        case = self.created()
        promised = '2026-09-25T17:00:00+07:00'
        observed = self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}], promised_deadline=promised)
        prepared = self.prepare(observed['case'], 'reply', daily_key=observed['daily_key'])
        case = self.receipt(case, prepared)['case']
        self.assertEqual(promised, case['next_due_at'])
        self.now = core.timestamp('2026-09-24T10:00:00+07:00')
        self.assertEqual('wait', self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}])['next_action'])

    def test_writable_case_monitoring_and_wrong_account_or_partial_history(self):
        case = self.created()
        self.assertCode('observation_mismatch', lambda: self.observe(case, account={**self.account, 'seller_id': 'OTHER'}))
        self.assertCode('incomplete_history', lambda: self.observe(case, history_complete=False))
        self.assertEqual('wait', self.observe(case, can_edit=True)['next_action'])

    def test_substantive_or_unassessed_response_stays_human(self):
        for assessment in ({}, {'decision': 'human', 'reason': 'Amazon requests legal declaration'}):
            with self.subTest(assessment=assessment):
                case = self.created() if not self.service.list()['cases'] else self.service.list()['cases'][0]
                self.now += dt.timedelta(days=1)
                observed = self.observe(case, [{'id': self.now.isoformat(), 'is_amazon': True}], assessment=assessment)
                self.assertEqual('human', observed['next_action'])

    def test_assessment_wait_overrides_new_reply(self):
        case = self.created()
        observed = self.observe(case, [{'id': 'amazon-wait', 'is_amazon': True}], assessment={'decision': 'wait', 'reason': 'Amazon is still investigating', 'evidence_contact_ids': ['amazon-wait']})
        self.assertEqual('wait', observed['next_action'])

    def test_amazon_closed_status_needs_evidenced_business_resolution(self):
        case = self.created()
        self.assertEqual('human', self.observe(case, case_status='Closed')['next_action'])
        self.now += dt.timedelta(days=1)
        self.assertEqual(1, len(self.service.daily_due()['cases']))
        self.service.resolve({'registry_id': case['registry_id'], 'authorization': self.auth(), 'evidence': {'source_id': 'fee-audit', 'summary': 'Restriction removed and fee corrected'}})
        self.assertEqual([], self.service.daily_due()['cases'])

    def test_newest_first_transcript_uses_latest_amazon_contact(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        observed = self.observe(case, [{'id': 'new', 'is_amazon': True, 'timestamp': self.now.isoformat()}, {'id': 'older', 'is_amazon': True, 'timestamp': (self.now - dt.timedelta(hours=1)).isoformat()}])
        self.assertEqual('new', observed['case']['last_remote_contact'])

    def test_existing_seller_reply_prevents_reply_to_stale_amazon_contact(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        observed = self.observe(case, [{'id': 'seller-reply', 'is_amazon': False, 'timestamp': self.now.isoformat()}, {'id': 'amazon-question', 'is_amazon': True, 'timestamp': (self.now - dt.timedelta(hours=1)).isoformat()}])
        self.assertEqual('wait', observed['next_action'])
        self.assertEqual(self.now.isoformat(), observed['case']['last_sent_at'])

    def test_registry_binding_rejects_other_account_and_case_target(self):
        case = self.start()
        prepared = self.prepare(case)['operation_request']
        inputs = prepared['inputs']
        self.assertCode('account_mismatch', lambda: self.service.validate_binding(inputs['case_binding'], inputs, account={**self.account, 'seller_id': 'OTHER'}))
        self.assertCode('target_mismatch', lambda: self.service.validate_binding(inputs['case_binding'], inputs, operation='case.reply', targets=[{'case_id': 'wrong'}]))
        self.assertCode('unprepared_message', lambda: self.service.validate_binding(inputs['case_binding'], inputs, operation_id='case-new-journal'))


if __name__ == '__main__':
    unittest.main()
