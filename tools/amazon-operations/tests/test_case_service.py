import concurrent.futures
import contextlib
import copy
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

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
        # Attended paths read the environment and cgroup; pin both to an attended terminal.
        self.cgroup = self.root / 'cgroup'
        self.cgroup.write_text('0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-com.t3tools.T3Code-1.scope\n')
        for patcher in (mock.patch.object(core, 'CGROUP', self.cgroup), mock.patch.dict(os.environ)):
            patcher.start()
            self.addCleanup(patcher.stop)
        os.environ.pop('WIZARDS_AI_MODE', None)

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

    # Attended sends: sign, claim-attended, the attended record-receipt branch and release.

    def attended(self, instruction='this is perfect, send it', member='UVICTOR'):
        return {'kind': 'attended', 'requester_id': member, 'source': {'session_id': 's-chat', 'request_id': 'send-1', 'instruction': instruction}}

    def current(self, case):
        return next(c for c in self.service.list()['cases'] if c['registry_id'] == case['registry_id'])

    def driver_run(self, case, texts, statuses=None, run_id='evora-1-r1', label='routine', account=None, at=None, approvals=None, claim=True, registry=True):
        """A Seller Assistant run directory: run.json plus approvals.jsonl attempt and result lines.

        The run claims the case first, a second before its first click, as the driver does."""
        at = at or self.now - dt.timedelta(minutes=10)
        if claim:
            saved, self.now = self.now, min(self.now, at - dt.timedelta(seconds=1))
            try:
                self.claim(case, self.current(case)['last_sent_at'], run_id=run_id)
            finally:
                self.now = saved
        run_dir = self.root / 'runs' / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        acct = {**self.account, 'seller_central_name': 'Brand', 'marketplace_label': 'United States', 'parent_account_name': 'Brand', **(account or {})}
        (run_dir / 'run.json').write_text(json.dumps({'schema_version': 1, 'run_id': run_id, 'account': acct, **({'registry_id': case['registry_id']} if registry else {})}))
        lines, messages = [], []
        for index, (item, text) in enumerate(texts.items()):
            sha = hashlib.sha256(text.encode()).hexdigest()
            path = run_dir / f'{item}.txt'
            path.write_text(text)
            stamp = (at + dt.timedelta(seconds=index)).isoformat()
            approval = {'schema_version': 1, 'plan_item': item, 'sha256': sha, 'run_id': run_id, 'seller_id': acct['seller_id'], 'approved_at': at.isoformat(), 'approval_text': 'this is perfect, send it', 'label': label, **(approvals or {}).get(item, {})}
            lines.append({'at': stamp, 'queue_id': f'00{index}', 'phase': 'attempt', 'command': 'submit', 'sha256': sha, 'plan_item': item, 'approval': approval})
            status = (statuses or {}).get(item, 'sent')
            if status:
                lines.append({'at': stamp, 'queue_id': f'00{index}', 'phase': 'result', 'command': 'submit', 'sha256': sha, 'status': status, 'delivery': status})
            messages.append({'plan_item': item, 'sha256': sha, 'text_path': str(path)})
        (run_dir / 'approvals.jsonl').write_text(''.join(json.dumps(line) + '\n' for line in lines))
        return run_dir, messages

    def record_attended(self, case, run_dir, messages, **extra):
        """By default the readback is a fresh case log that does not show the message, as for a chat reply."""
        if 'readback_path' not in extra:
            extra['readback_path'] = str(self.case_log(case, [], name=f'observe-after-{run_dir.name}.json'))
        receipt = {'schema_version': 1, 'kind': 'driver_run', 'run_dir': str(run_dir), 'purpose': 'reply', 'label': 'routine', 'channel': 'case_chat', 'authorization': self.attended(), 'messages': messages, **extra}
        return self.service.record_receipt({'registry_id': case['registry_id'], 'attended_receipt': receipt})

    def manual(self, case, sha, sent, evidence, **extra):
        receipt = {'schema_version': 1, 'kind': 'manual_receipt', 'purpose': 'reply', 'label': 'routine', 'channel': 'case_chat', 'sent_at': sent.isoformat(), 'signed_body_sha256': sha, 'evidence_path': str(evidence), 'authorization': self.attended(), **extra}
        return self.service.record_receipt({'registry_id': case['registry_id'], 'attended_receipt': receipt})

    def evidence(self, name, value):
        path = self.root / name
        path.write_text(json.dumps(value))
        return path

    def case_log(self, case, contacts, observed=None, name='readback.json'):
        return self.evidence(name, {'schema_version': 1, 'status': 'collected', 'account': self.account, 'case_id': case['case_id'], 'history_complete': True, 'contacts': contacts, 'observed_at': (observed or self.now).isoformat()})

    def claim(self, case, last, run_id='evora-1-r1', **extra):
        return self.service.claim_attended({'registry_id': case['registry_id'], 'run_id': run_id, 'account': {'seller_id': 'SELLER', 'marketplace_id': 'ATVPDKIKX0DER'}, 'case_id': case['case_id'], 'baseline': {'last_sent_at': last}, 'authorization': self.attended(), **extra})

    def test_sign_keeps_owner_signature_refuses_other_signoffs_and_appends(self):
        case = self.start()
        sign = lambda body: self.service.sign({'registry_id': case['registry_id'], 'body': body})  # noqa: E731
        first = sign('Please confirm the review.')
        self.assertEqual('Please confirm the review.\n\nDanica\nEcom Wizards', first['signed_body'])
        self.assertEqual(hashlib.sha256(first['signed_body'].encode()).hexdigest(), first['sha256'])
        self.assertEqual(('UDANICA', 'case_owner', 'Danica'), (first['owner_member_id'], first['owner_source'], first['signature_name']))
        self.assertEqual(case['last_sent_at'], first['baseline']['last_sent_at'])
        self.assertEqual(first['signed_body'], sign(first['signed_body'].replace('\n', '\r\n') + '\n')['signed_body'])
        for body in ['Please confirm.\n\nVictor Uhl\nEcom Wizards', 'Please confirm.\n\nBest,\nDanica', 'Please confirm.\n\nThanks,\nVictor Uhl', 'Please confirm.\n\nEcom Wizards', 'Please confirm.\n\nBest regards, Danica', 'Please confirm.\n\nThanks - Victor Uhl.']:
            with self.subTest(body=body):
                self.assertCode('signature_conflict', lambda: sign(body))
        self.assertCode('missing_body', lambda: sign('Danica\nEcom Wizards'))
        unregistered = self.service.sign({'body': 'Please open a case.'})
        self.assertEqual(('UVICTOR', 'attended_operator'), (unregistered['owner_member_id'], unregistered['owner_source']))
        self.assertTrue(unregistered['signed_body'].endswith('\n\nVictor Uhl\nEcom Wizards'))
        imported = self.service.adopt({'account': self.account, 'issue_key': 'legacy', 'subject': 'Legacy case', 'case_id': '10001'})['case']
        self.assertEqual('attended_operator', self.service.sign({'registry_id': imported['registry_id'], 'body': 'Status?'})['owner_source'])

    def test_sign_treats_a_name_inside_a_word_as_body_text_on_both_paths(self):
        self.policy_value['members']['UDAVE'] = {'signature_name': 'Dave', 'signature': 'Dave\nEcom Wizards', 'approved': True}
        self.policy.write_text(json.dumps(self.policy_value))
        case = self.start('UDAVE', '100.5', 'dave')
        body = 'Please check the Davenport warehouse shipment FBA123.'
        self.assertEqual(body + '\n\nDave\nEcom Wizards', self.service.sign({'registry_id': case['registry_id'], 'body': body})['signed_body'])
        self.assertEqual(body + '\n\nDave\nEcom Wizards', self.prepare(case, body=body)['operation_request']['inputs']['signed_body'])
        self.assertCode('signature_conflict', lambda: self.service.sign({'registry_id': case['registry_id'], 'body': 'Please check it.\n\nThanks, Dave'}))

    def test_prepare_send_signs_once_and_keeps_unsigned_bodies_unchanged(self):
        plain = self.prepare(self.start())['operation_request']['inputs']['signed_body']
        self.assertEqual('Please confirm the defect review.\n\nDanica\nEcom Wizards', plain)
        body = 'Please confirm the defect review.\n\nDanica\nEcom Wizards'
        inputs = self.prepare(self.start(message='100.8', issue='signed'), body=body)['operation_request']['inputs']
        self.assertEqual(body, inputs['signed_body'])
        self.assertEqual('valid', self.service.validate_binding(inputs['case_binding'], inputs)['status'])
        conflict = self.start(message='100.9', issue='conflict')
        self.assertCode('signature_conflict', lambda: self.prepare(conflict, body='Please confirm.\n\nVictor Uhl\nEcom Wizards'))

    def test_attended_driver_run_records_reply_and_grimoire_readers_keep_working(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        observed = self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}])
        self.assertEqual('reply', observed['next_action'])
        before = self.service.list()['cases'][0]
        grimoire = self.service._binding(before)
        self.now += dt.timedelta(minutes=30)
        run_dir, messages = self.driver_run(case, {'P1': 'Hello, I need help with case 21912345678.', 'P3': 'Here is the invoice.\n\nDanica\nEcom Wizards'})
        result = self.record_attended(case, run_dir, messages)
        self.assertEqual(('recorded', 'driver_result'), (result['status'], result['verified_by']))
        recorded, action = result['case'], result['case']['actions'][-1]
        self.assertLessEqual({'operation_id', 'request_hash', 'purpose', 'daily_key', 'binding', 'signed_body_hash', 'scope_hash', 'applied', 'receipt_path'}, set(action))
        self.assertEqual((True, None, 'routine', 'driver_result'), (action['applied'], action['scope_hash'], action['attended']['label'], action['attended']['verified_by']))
        self.assertEqual('this is perfect, send it', action['attended']['approval_text'])
        self.assertEqual(before['authorization_revision'] + 2, recorded['authorization_revision'], 'one bump for the claim, one for the record')
        self.assertEqual(action['operation_id'], recorded['daily'][self.now.date().isoformat()]['sent_operation_id'])
        self.assertEqual((self.now - dt.timedelta(minutes=10, seconds=-1)).isoformat(), recorded['last_sent_at'])
        self.assertEqual('awaiting_amazon', recorded['lifecycle'])
        self.assertCode('stale_case_binding', lambda: self.service.validate_binding(grimoire))
        # The recorded claim no longer holds Grimoire back; today's sent marker does.
        self.assertCode('daily_action_blocked', lambda: self.prepare(recorded, 'reply', daily_key=observed['daily_key']))
        self.assertEqual([], self.service.daily_due()['cases'])
        self.assertCode('run_recorded', lambda: self.claim(case, recorded['last_sent_at']))
        # Next day, Grimoire's daily path reads every action, the attended one included.
        self.now += dt.timedelta(days=1)
        self.assertEqual('observe', self.service.daily_due()['cases'][0]['next_action'])
        observed = self.observe(recorded, [{'id': 'amazon-2', 'is_amazon': True}])
        self.assertEqual('reply', observed['next_action'])
        fresh = self.prepare(observed['case'], 'reply', daily_key=observed['daily_key'])['operation_request']
        self.assertEqual('valid', self.service.validate_binding(fresh['inputs']['case_binding'], fresh['inputs'], operation_id=fresh['operation_id'], request_hash=core.digest(fresh))['status'])

    def test_attended_manual_receipt_needs_evidence_of_the_exact_message(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        text = 'Thanks, the requested invoice is attached.\n\nDanica\nEcom Wizards'
        sha, sent = hashlib.sha256(text.encode()).hexdigest(), self.now - dt.timedelta(minutes=20)
        receipt = {'case_id': case['case_id'], 'seller_id': 'SELLER', 'marketplace_id': 'ATVPDKIKX0DER', 'message_sha256': sha, 'attempted': True, 'status': 'verified', 'attempted_at': sent.isoformat(), 'verified_at': (sent + dt.timedelta(minutes=3)).isoformat()}
        self.assertCode('unverified_send', lambda: self.manual(case, sha, sent, self.evidence('wrong.json', {**receipt, 'message_sha256': '0' * 64})))
        self.assertCode('account_mismatch', lambda: self.manual(case, sha, sent, self.evidence('other.json', {**receipt, 'seller_id': 'OTHER'})))
        self.assertCode('unbound_readback', lambda: self.manual(case, sha, sent, self.evidence('chat.json', {'captured_at': self.now.isoformat(), 'text': text})))
        path = self.evidence('send-chat-receipt.json', receipt)
        result = self.manual(case, sha, sent, path)
        self.assertEqual(('recorded', 'chat_transcript', sent.isoformat()), (result['status'], result['verified_by'], result['case']['last_sent_at']))
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), result['case']['actions'][-1]['attended']['evidence_sha256'])
        self.assertEqual('already_recorded', self.manual(case, sha, sent, path)['status'])
        # A case-log readback upgrades the record and merges the seller contact.
        later = self.now + dt.timedelta(hours=2)
        self.now += dt.timedelta(hours=3)
        second = 'One more document is attached.\n\nDanica\nEcom Wizards'
        log = self.case_log(case, [{'id': 'seller-chat', 'is_amazon': False, 'message': second, 'timestamp': later.isoformat()}])
        logged = self.manual(case, hashlib.sha256(second.encode()).hexdigest(), later, log)
        self.assertEqual(('case_log', later.isoformat()), (logged['verified_by'], logged['case']['last_sent_at']))
        self.assertIn('seller-chat', logged['case']['contact_ids'])

    def test_attended_receipt_is_idempotent(self):
        case = self.created()
        run_dir, messages = self.driver_run(case, {'P3': 'Please confirm.\n\nDanica\nEcom Wizards'})
        first = self.record_attended(case, run_dir, messages)
        second = self.record_attended(case, run_dir, messages)
        self.assertEqual(('recorded', 'already_recorded'), (first['status'], second['status']))
        self.assertEqual(first['case']['authorization_revision'], second['case']['authorization_revision'])
        self.assertEqual(1, sum(a['operation_id'].startswith('attended-') for a in second['case']['actions']))
        self.assertCode('receipt_conflict', lambda: self.record_attended(case, run_dir, messages, label='appeal'))

    def test_attended_entry_points_refuse_slack_and_other_member_authorization(self):
        case = self.created()
        run_dir, messages = self.driver_run(case, {'P3': 'Please confirm.'})
        for authorization, code in ((self.auth('UVICTOR', '300.1'), 'attended_required'), (self.attended(member='UDANICA'), 'operator_mismatch')):
            with self.subTest(code=code):
                self.assertCode(code, lambda: self.claim(case, case['last_sent_at'], authorization=authorization))
                self.assertCode(code, lambda: self.record_attended(case, run_dir, messages, authorization=authorization))
                self.assertCode(code, lambda: self.manual(case, messages[0]['sha256'], self.now, self.root / 'none.json', authorization=authorization))
                self.assertCode(code, lambda: self.service.release({'registry_id': case['registry_id'], 'operation_id': 'case-x', 'authorization': authorization, 'evidence': {'readback_path': 'x', 'summary': 'x'}}))

    def test_attended_paths_refuse_grimoire_but_persisted_attended_mandate_still_validates(self):
        mandate = self.service.start({'account': self.account, 'issue_key': 'attended', 'subject': 'Review defect', 'authorization': self.attended('Open and manage this case')})['case']
        prepared = self.prepare(mandate)['operation_request']['inputs']
        case = self.created()
        run_dir, messages = self.driver_run(case, {'P3': 'Please confirm.'})
        grimoire_cgroup = '0::/user.slice/user-1000.slice/user@1000.service/app.slice/wizards-ai-case-daily.service\n'
        for name, enter in (('environment', lambda: os.environ.__setitem__('WIZARDS_AI_MODE', '1')), ('cgroup', lambda: self.cgroup.write_text(grimoire_cgroup))):
            with self.subTest(name=name):
                enter()
                for call in (lambda: self.service.sign({'body': 'Status?'}),
                             lambda: self.claim(case, case['last_sent_at']),
                             lambda: self.record_attended(case, run_dir, messages),
                             lambda: self.service.release({'registry_id': case['registry_id'], 'operation_id': 'case-x', 'authorization': self.attended(), 'evidence': {'readback_path': 'x', 'summary': 'x'}}),
                             lambda: self.service.start({'account': self.account, 'issue_key': 'other', 'subject': 'Other', 'authorization': self.attended('Open another')})):
                    self.assertCode('attended_context_required', call)
                # Grimoire's verify_case and send path re-validate the persisted attended mandate.
                current = next(c for c in self.service.list()['cases'] if c['registry_id'] == mandate['registry_id'])
                self.assertEqual('valid', self.service.validate_binding(self.service._binding(current))['status'])
                self.assertEqual('valid', self.service.validate_binding(prepared['case_binding'], prepared)['status'])
                os.environ.pop('WIZARDS_AI_MODE', None)
                self.cgroup.write_text('0::/user.slice/user-1000.slice/user@1000.service/app.slice/vte-spawn-1.scope\n')

    def test_claim_attended_stales_grimoire_binding_and_refuses_racing_sends(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        current = self.service.list()['cases'][0]
        baseline = current['last_sent_at']
        binding = self.service._binding(current)
        self.assertEqual('valid', self.service.validate_binding(binding)['status'])
        first = self.claim(case, baseline)
        self.assertCode('stale_case_binding', lambda: self.service.validate_binding(binding))
        again = self.claim(case, baseline)
        self.assertEqual((first['operation_id'], first['authorization_revision'] + 1), (again['operation_id'], again['authorization_revision']))
        self.assertEqual(2, self.service.list()['cases'][0]['attended_claims']['evora-1-r1']['count'])
        self.assertCode('account_mismatch', lambda: self.claim(case, baseline, account={'seller_id': 'OTHER', 'marketplace_id': 'ATVPDKIKX0DER'}))
        self.assertCode('case_mismatch', lambda: self.claim(case, baseline, case_id='99999999'))
        self.assertCode('case_mismatch', lambda: self.claim(case, baseline, case_id=None))
        self.assertCode('baseline_changed', lambda: self.claim(case, (core.timestamp(baseline) - dt.timedelta(hours=1)).isoformat()))
        self.assertCode('baseline_changed', lambda: self.claim(case, None))
        self.assertCode('case_not_created', lambda: self.claim(self.start(message='100.4', issue='pending'), None))
        # A Grimoire reply prepared before the claim blocks the click; once it is recorded, today's marker does.
        other = self.start(message='100.6', issue='other')
        other = self.receipt(other, self.prepare(other), remote_id='21900000002')['case']
        observed = self.observe(other, [{'id': 'amazon-9', 'is_amazon': True}])
        prepared = self.prepare(observed['case'], 'reply', daily_key=observed['daily_key'])
        self.assertCode('reconciliation_required', lambda: self.claim(other, other['last_sent_at'], run_id='other-r1'))
        latest = self.receipt(other, prepared, remote_id='21900000002')['case']['last_sent_at']
        self.assertCode('daily_sent', lambda: self.claim(self.current(other), latest, run_id='other-r1'))

    def test_open_claim_holds_grimoire_back_until_recorded_or_released(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        claimed_at = self.now
        self.claim(case, self.current(case)['last_sent_at'])
        # Amazon's answer arrives while the attended chat may already have replied: Grimoire hands it to a human.
        observed = self.observe(self.current(case), [{'id': 'amazon-1', 'is_amazon': True}])
        self.assertEqual('human', observed['next_action'])
        self.assertEqual([], self.service.daily_due()['cases'])
        self.assertCode('reconciliation_required', lambda: self.prepare(observed['case'], 'chaser', daily_key=observed['daily_key']))
        self.now += dt.timedelta(minutes=20)
        # The chat closed before any outbound click: run.json only, no approvals.jsonl.
        run_dir, _ = self.driver_run(case, {}, claim=False)
        (run_dir / 'approvals.jsonl').unlink()
        release = lambda path, run_id='evora-1-r1', **extra: self.service.release({'registry_id': case['registry_id'], 'run_id': run_id, 'run_dir': str(run_dir), 'authorization': self.attended('Nothing went out; release it'), 'evidence': {'readback_path': str(path), 'summary': 'Chat closed before Send'}, **extra})  # noqa: E731
        self.assertCode('missing_run_dir', lambda: release(self.case_log(case, []), run_dir=None))
        self.assertCode('run_mismatch', lambda: release(self.case_log(case, []), run_id='evora-9'))
        ghost, _ = self.driver_run(case, {}, run_id='evora-9', claim=False)
        self.assertCode('unknown_claim', lambda: release(self.case_log(case, []), run_id='evora-9', run_dir=str(ghost)))
        self.assertCode('stale_readback', lambda: release(self.case_log(case, [], observed=claimed_at - dt.timedelta(minutes=1))))
        other_case = self.evidence('other-case.json', {'account': self.account, 'history_complete': True, 'observed_at': self.now.isoformat(), 'cases': [{'case_id': '1', 'contacts': []}]})
        self.assertCode('readback_mismatch', lambda: release(other_case))
        sent = {'id': 'seller-chat', 'is_amazon': False, 'message': 'Here is the invoice.', 'timestamp': (claimed_at + dt.timedelta(minutes=2)).isoformat()}
        self.assertCode('message_observed', lambda: release(self.case_log(case, [sent])))
        self.assertCode('message_observed', lambda: release(self.case_log(case, [{'id': 'seller-new', 'is_amazon': False, 'message': 'x'}])))
        earlier = {'id': 'seller-original', 'is_amazon': False, 'message': 'Please review.', 'timestamp': (claimed_at - dt.timedelta(days=1)).isoformat()}
        released = release(self.case_log(case, [earlier, {'id': 'amazon-1', 'is_amazon': True}]))
        self.assertEqual('released', released['status'])
        self.assertEqual('already_released', release(self.case_log(case, []))['status'])
        self.assertCode('claim_released', lambda: self.claim(case, self.current(case)['last_sent_at']))
        # Next day Grimoire answers as usual.
        self.now += dt.timedelta(days=1)
        observed = self.observe(self.current(case), [{'id': 'amazon-2', 'is_amazon': True}])
        self.assertEqual('reply', observed['next_action'])
        self.assertEqual('ready', self.prepare(observed['case'], 'reply', daily_key=observed['daily_key'])['status'])

    def test_recorded_claim_cannot_be_released(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        run_dir, messages = self.driver_run(case, {'P3': 'Here is the invoice.\n\nDanica\nEcom Wizards'})
        self.record_attended(case, run_dir, messages)
        self.assertEqual([], self.service._open_claims(self.current(case)))
        self.assertCode('run_recorded', lambda: self.service.release({'registry_id': case['registry_id'], 'run_id': 'evora-1-r1', 'run_dir': str(run_dir), 'authorization': self.attended(), 'evidence': {'readback_path': str(self.case_log(case, [])), 'summary': 'x'}}))

    def test_release_refuses_a_run_whose_driver_log_shows_a_submit(self):
        # Review F1: a chat reply can be missing from the case log, so a clean case log cannot release a run
        # whose own log says it submitted. Otherwise Grimoire answers the same Amazon message again that day.
        case = self.created()
        self.now += dt.timedelta(days=1)
        observed = self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}])
        self.assertEqual('reply', observed['next_action'])
        self.now += dt.timedelta(minutes=30)
        text = 'Here is the invoice.\n\nDanica\nEcom Wizards'
        release = lambda run_dir, run_id: self.service.release({'registry_id': case['registry_id'], 'run_id': run_id, 'run_dir': str(run_dir), 'authorization': self.attended('Nothing went out; release it'), 'evidence': {'readback_path': str(self.case_log(case, [])), 'summary': 'Case log shows no seller message'}})  # noqa: E731
        # An uncertain submit needs the operator's statement and the driver's transcript as well.
        for status, code in (('sent', 'run_sent'), ('uncertain', 'missing_operator_statement'), (None, 'run_sent')):
            with self.subTest(status=status):
                run_id = f'evora-1-{status}'
                run_dir, _ = self.driver_run(case, {'P3': text}, statuses={'P3': status}, run_id=run_id)
                self.assertCode(code, lambda: release(run_dir, run_id))
        current = self.current(case)
        self.assertEqual(3, len(self.service._open_claims(current)))
        self.assertCode('reconciliation_required', lambda: self.prepare(current, 'reply', daily_key=observed['daily_key']))
        # The sent run is recorded instead; a run whose only submit was blocked before dispatch is released.
        sent_dir = self.root / 'runs' / 'evora-1-sent'
        messages = [{'plan_item': 'P3', 'sha256': hashlib.sha256(text.encode()).hexdigest(), 'text_path': str(sent_dir / 'P3.txt')}]
        self.assertEqual('recorded', self.record_attended(case, sent_dir, messages)['status'])
        blocked, _ = self.driver_run(case, {'P3': text}, statuses={'P3': 'blocked'}, run_id='evora-1-blocked')
        self.assertEqual('released', release(blocked, 'evora-1-blocked')['status'])
        # run.json must name this run, account and case.
        other, _ = self.driver_run(case, {}, run_id='evora-1-other', account={'seller_id': 'OTHER'})
        self.assertCode('account_mismatch', lambda: release(other, 'evora-1-other'))
        unbound, _ = self.driver_run(case, {}, run_id='evora-1-unbound', registry=False)
        self.assertCode('registry_binding_required', lambda: release(unbound, 'evora-1-unbound'))
        self.assertCode('run_mismatch', lambda: release(blocked, 'evora-1-unbound'))

    def transcript(self, run_dir, captured, url, text='', page_text='', deep='', messages=(), step='07'):
        """The driver's transcript command output: transcripts/NN-transcript.json with its -deep.txt."""
        (run_dir / 'transcripts').mkdir(exist_ok=True)
        (run_dir / 'transcripts' / f'{step}-transcript-deep.txt').write_text(deep)
        record = {'schema_version': 1, 'captured_at': captured.isoformat(), 'url': url, 'conversation_url': None, 'frame_id': 'F1', 'composer_label': 'Type your message', 'text_sha256': hashlib.sha256(text.encode()).hexdigest(),
                  'basis': 'container', 'text': text, 'message_count': len(messages), 'message_detection': 'structural', 'messages': [{'text': m, 'role': 'listitem'} for m in messages], 'page_text': page_text}
        return self.evidence(f'runs/{run_dir.name}/transcripts/{step}-transcript.json', record)

    def test_release_frees_an_uncertain_run_only_with_statement_transcript_and_readback(self):
        # stackFix open item: an uncertain submit that in truth sent nothing can be neither recorded nor released.
        case = self.created()
        self.now += dt.timedelta(days=1)
        observed = self.observe(case, [{'id': 'amazon-1', 'is_amazon': True}])
        self.now += dt.timedelta(minutes=30)
        text = 'Here is the invoice for shipment FBA15ABCDEF. It lists the units we sent on 12 September and the carrier receipt for the same pallet count.\n\nDanica\nEcom Wizards'
        clicked = self.now - dt.timedelta(minutes=10)
        run_dir, messages = self.driver_run(case, {'P3': text}, statuses={'P3': 'uncertain'}, run_id='evora-1-u', at=clicked)
        url = 'https://sellercentral.amazon.com/cu/case-dashboard/view-case?caseID=21912345678'
        (run_dir / 'steps').mkdir()
        self.evidence('runs/evora-1-u/steps/00-submit.json', {'schema_version': 1, 'id': '000', 'command': 'submit', 'result': {'status': 'uncertain'}, 'url': url})
        chat = 'Amazon: Thanks, what else can I help with?\n\nYou: Hello.'
        page = self.transcript(run_dir, clicked + dt.timedelta(minutes=2), url, chat, chat + '\nType your message', chat, ['Thanks, what else can I help with?', 'Hello.'])
        statement = 'The invoice message did not go out, the composer was empty and nothing new is in the chat'
        current = self.current(case)
        self.assertCode('reconciliation_required', lambda: self.prepare(current, 'reply', daily_key=observed['daily_key']))

        def release(readback=None, **extra):
            evidence = {'readback_path': str(readback or self.case_log(case, [])), 'summary': 'Case log and transcript show no seller message', 'page_evidence_path': str(page), 'text_paths': [messages[0]['text_path']], **extra.pop('evidence', {})}
            request = {'registry_id': case['registry_id'], 'run_id': 'evora-1-u', 'run_dir': str(run_dir), 'authorization': self.attended('It was not sent, release the run'), 'operator_statement': statement, 'evidence': evidence, **extra}
            return self.service.release({k: v for k, v in request.items() if v is not None})

        # Each of the four pieces is required.
        for name, extra, code in (('statement', {'operator_statement': None}, 'missing_operator_statement'), ('blank statement', {'operator_statement': '  '}, 'missing_operator_statement'),
                                  ('page evidence', {'evidence': {'page_evidence_path': None}}, 'missing_page_evidence'), ('text', {'evidence': {'text_paths': []}}, 'missing_approved_text'),
                                  ('readback', {'evidence': {'readback_path': None}}, 'missing_release_evidence'), ('authorization', {'authorization': None}, 'attended_required'),
                                  ('slack', {'authorization': self.auth('UVICTOR', '300.2')}, 'attended_required')):
            with self.subTest(missing=name):
                self.assertCode(code, lambda: release(**extra))
        other_text = self.root / 'other.txt'
        other_text.write_text('Another approved text')
        self.assertCode('missing_approved_text', lambda: release(evidence={'text_paths': [str(other_text)]}))
        os.environ['WIZARDS_AI_MODE'] = '1'
        self.assertCode('attended_context_required', lambda: release())
        os.environ.pop('WIZARDS_AI_MODE')
        # Evidence older than the attempt: a readback after the claim but before the click, a transcript before it.
        self.assertCode('stale_readback', lambda: release(self.case_log(case, [], observed=clicked - dt.timedelta(milliseconds=500))))
        early = self.transcript(run_dir, clicked - dt.timedelta(seconds=30), url, chat, chat, chat, step='06')
        self.assertCode('stale_page_evidence', lambda: release(evidence={'page_evidence_path': str(early)}))
        # A transcript of another page, or one outside the run, cannot speak for the submit.
        elsewhere = self.transcript(run_dir, clicked + dt.timedelta(minutes=3), url + '&chat=1', chat, chat, chat, step='08')
        self.assertCode('page_evidence_mismatch', lambda: release(evidence={'page_evidence_path': str(elsewhere)}))
        outside = self.evidence('07-transcript.json', json.loads(page.read_text()))
        self.assertCode('page_evidence_mismatch', lambda: release(evidence={'page_evidence_path': str(outside)}))
        # The approved text in any part of the transcript refuses: exact, whitespace-collapsed, or its first 120 characters.
        collapsed = ' '.join(text.split())
        for name, kwargs in (('text', {'text': chat + '\n\n' + text}), ('page_text', {'page_text': chat + '\n' + text}), ('deep', {'deep': collapsed}),
                             ('message', {'messages': ['Hello.', text]}), ('prefix', {'text': chat + '\n' + collapsed[:125]})):
            with self.subTest(shown=name):
                fields = {'text': chat, 'page_text': chat, 'deep': chat, 'messages': ['Hello.'], **kwargs}
                shown = self.transcript(run_dir, clicked + dt.timedelta(minutes=4), url, step='09', **fields)
                self.assertCode('message_in_page_evidence', lambda: release(evidence={'page_evidence_path': str(shown)}))
        capped = self.transcript(run_dir, clicked + dt.timedelta(minutes=4), url, chat, 'x' * 200000, chat, step='10')
        self.assertCode('page_evidence_truncated', lambda: release(evidence={'page_evidence_path': str(capped)}))
        # All four pieces release the run; the record keeps the evidence, its hashes, the statement and the time.
        readback = self.case_log(case, [], name='observe-after-u.json')
        released = release(readback)
        self.assertEqual('released', released['status'])
        record = released['case']['attended_claims']['evora-1-u']['released']
        self.assertEqual((statement, self.now.isoformat()), (record['operator_statement'], record['at']))
        self.assertEqual((str(page.resolve()), hashlib.sha256(page.read_bytes()).hexdigest()), (record['page_evidence']['path'], record['page_evidence']['sha256']))
        self.assertEqual(hashlib.sha256(chat.encode()).hexdigest(), record['page_evidence']['deep_text_sha256'])
        self.assertEqual([{'path': messages[0]['text_path'], 'sha256': messages[0]['sha256']}], record['texts'])
        self.assertEqual(hashlib.sha256(readback.read_bytes()).hexdigest(), record['evidence']['readback_sha256'])
        self.assertEqual(['000'], [s['queue_id'] for s in record['uncertain_submits']])
        self.assertEqual('already_released', release(readback)['status'])
        # The case is sendable again, and the released run cannot click again.
        self.assertEqual([], self.service._open_claims(self.current(case)))
        self.assertEqual('ready', self.prepare(self.current(case), 'reply', daily_key=observed['daily_key'])['status'])
        self.assertCode('claim_released', lambda: self.claim(case, self.current(case)['last_sent_at'], run_id='evora-1-u'))

    def test_release_refuses_a_run_with_a_sent_and_an_uncertain_submit(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        clicked = self.now - dt.timedelta(minutes=10)
        run_dir, messages = self.driver_run(case, {'P3': 'Here is the invoice.\n\nDanica\nEcom Wizards', 'followup': 'Also attached: the packing list.\n\nDanica\nEcom Wizards'},
                                            statuses={'P3': 'uncertain', 'followup': 'sent'}, run_id='evora-1-mixed', at=clicked)
        url = 'https://sellercentral.amazon.com/cu/case-dashboard/view-case?caseID=21912345678'
        (run_dir / 'steps').mkdir()
        for queue_id in ('000', '001'):
            self.evidence(f'runs/evora-1-mixed/steps/{queue_id[1:]}-submit.json', {'schema_version': 1, 'id': queue_id, 'command': 'submit', 'url': url})
        page = self.transcript(run_dir, clicked + dt.timedelta(minutes=2), url, 'Hello.', 'Hello.', 'Hello.')
        request = {'registry_id': case['registry_id'], 'run_id': 'evora-1-mixed', 'run_dir': str(run_dir), 'authorization': self.attended('It was not sent, release the run'), 'operator_statement': 'Neither message went out',
                   'evidence': {'readback_path': str(self.case_log(case, [])), 'summary': 'Case log shows no seller message', 'page_evidence_path': str(page), 'text_paths': [m['text_path'] for m in messages]}}
        self.assertCode('run_sent', lambda: self.service.release(request))
        self.assertEqual(['evora-1-mixed'], self.service._open_claims(self.current(case)))

    def test_claim_checks_the_chat_name_against_the_case_owner(self):
        case = self.created()
        last = case['last_sent_at']
        name = self.service.sign({'registry_id': case['registry_id'], 'body': 'Status?'})['signature_name']
        self.assertEqual('Danica', name)
        self.assertCode('signature_name_mismatch', lambda: self.claim(case, last, signature_name='Victor Uhl'))
        self.assertEqual('claimed', self.claim(case, last, signature_name=name)['status'])
        self.assertEqual('claimed', self.claim(case, last)['status'], 'a run without the chat form passes no name')

    def test_next_day_observe_waits_after_attended_reply_missing_from_case_log(self):
        case = self.created()
        created_at = self.now
        self.now += dt.timedelta(days=1)
        amazon_at = self.now - dt.timedelta(minutes=30)
        run_dir, messages = self.driver_run(case, {'P3': 'Here is the invoice.\n\nDanica\nEcom Wizards'}, at=self.now - dt.timedelta(minutes=5))
        self.record_attended(case, run_dir, messages)
        self.now += dt.timedelta(days=1)
        contacts = [{'id': 'seller-original', 'is_amazon': False, 'timestamp': created_at.isoformat()}, {'id': 'amazon-1', 'is_amazon': True, 'timestamp': amazon_at.isoformat()}]
        self.assertEqual('wait', self.observe(self.service.list()['cases'][0], contacts)['next_action'])

    def test_uncertain_driver_send_needs_a_fresh_readback_showing_the_text(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        text ='Please confirm the review.\n\nDanica\nEcom Wizards'
        run_dir, messages = self.driver_run(case, {'P3': text}, statuses={'P3': 'uncertain'})
        self.assertCode('missing_readback', lambda: self.record_attended(case, run_dir, messages, readback_path=None))
        self.assertCode('unverified_send', lambda: self.record_attended(case, run_dir, messages))
        empty = self.case_log(case, [], name='empty.json')
        self.assertCode('unverified_send', lambda: self.record_attended(case, run_dir, messages, readback_path=str(empty)))
        stale = self.case_log(case, [], observed=self.now - dt.timedelta(hours=1), name='stale.json')
        self.assertCode('stale_readback', lambda: self.record_attended(case, run_dir, messages, readback_path=str(stale)))
        contact_at = self.now - dt.timedelta(minutes=9)
        shown = self.case_log(case, [{'id': 'seller-reply', 'is_amazon': False, 'message': text, 'timestamp': contact_at.isoformat()}])
        result = self.record_attended(case, run_dir, messages, readback_path=str(shown))
        self.assertEqual(('recorded', 'case_log', contact_at.isoformat()), (result['status'], result['verified_by'], result['case']['last_sent_at']))
        self.assertIn('seller-reply', result['case']['contact_ids'])
        # A run that stopped without a result line verifies through the chat transcript.
        later = 'One more question about the invoice.'
        run_dir, messages = self.driver_run(case, {'followup': later}, statuses={'followup': None}, run_id='evora-1-r2')
        transcript = self.evidence('transcript.json', {'schema_version': 1, 'captured_at': self.now.isoformat(), 'text': 'Me\n' + later + '\nAssociate\nThanks, checking.', 'messages': []})
        self.assertCode('readback_not_case_log', lambda: self.record_attended(case, run_dir, messages, readback_path=str(transcript)))
        self.assertEqual('chat_transcript', self.record_attended(case, run_dir, messages, transcript_path=str(transcript))['verified_by'])

    def test_driver_run_record_names_the_evidence_that_shows_each_message(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        texts = {'P1': 'Hello, I need help with case 21912345678.', 'P3': 'Here is the invoice.\n\nDanica\nEcom Wizards'}
        run_dir, messages = self.driver_run(case, texts)
        logged = self.case_log(case, [{'id': 'seller-p3', 'is_amazon': False, 'message': texts['P3'], 'timestamp': (self.now - dt.timedelta(minutes=9)).isoformat()}], name='after.json')
        result = self.record_attended(case, run_dir, messages, readback_path=str(logged))
        recorded = result['case']['actions'][-1]['attended']
        self.assertEqual(('driver_result', ['driver_result', 'case_log']), (result['verified_by'], [m['verified_by'] for m in recorded['messages']]), 'the record names the weakest evidence')
        self.assertEqual(hashlib.sha256(logged.read_bytes()).hexdigest(), recorded['readback_sha256'])
        # A transcript that shows the opening message lifts it to chat_transcript.
        self.now += dt.timedelta(hours=1)
        run_dir, messages = self.driver_run(case, {'P1': 'Hello again about case 21912345678.'}, run_id='evora-1-r2')
        transcript = self.evidence('transcript-r2.json', {'schema_version': 1, 'captured_at': self.now.isoformat(), 'text': 'Me\nHello again about case 21912345678.', 'messages': []})
        second = self.record_attended(case, run_dir, messages, transcript_path=str(transcript))
        self.assertEqual('chat_transcript', second['verified_by'])
        self.assertEqual(hashlib.sha256(transcript.read_bytes()).hexdigest(), second['case']['actions'][-1]['attended']['transcript_sha256'])

    def test_driver_run_records_a_second_text_approved_later_in_the_same_chat(self):
        case = self.created()
        self.now += dt.timedelta(days=1)
        later = self.attended('Yes, send the order ID')
        texts = {'P3': 'Here is the invoice.\n\nDanica\nEcom Wizards', 'followup': 'The order ID is 111-1234567-1234567.\n\nDanica\nEcom Wizards'}
        run_dir, messages = self.driver_run(case, texts, approvals={'followup': {'approval_text': later['source']['instruction'], 'label': 'admission', 'authorization': later}})
        labelled = [messages[0], {**messages[1], 'label': 'admission'}]
        # Unclaimed, the second sentence is not an approval this run may record.
        self.assertCode('approval_mismatch', lambda: self.record_attended(case, run_dir, labelled))
        self.claim(case, self.current(case)['last_sent_at'], authorization=later)
        self.assertCode('label_mismatch', lambda: self.record_attended(case, run_dir, messages))
        result = self.record_attended(case, run_dir, labelled)
        self.assertEqual('recorded', result['status'])
        self.assertEqual(['routine', 'admission'], [m['label'] for m in result['case']['actions'][-1]['attended']['messages']])
        self.assertEqual(2, len(result['case']['attended_claims']['evora-1-r1']['authorizations']))

    def test_backfilled_receipt_marks_its_own_day_and_leaves_today_to_grimoire(self):
        case = self.created()
        self.now += dt.timedelta(days=1, hours=4)
        sent = self.now
        text = 'Thanks, the invoice is attached.\n\nDanica\nEcom Wizards'
        sha = hashlib.sha256(text.encode()).hexdigest()
        # Amazon answers the next morning; the hand-sent reply is recorded only after the daily observation.
        self.now += dt.timedelta(days=1, hours=-4)
        observed = self.observe(self.current(case), [{'id': 'amazon-1', 'is_amazon': True}])
        self.assertEqual('reply', observed['next_action'])
        receipt = {'case_id': case['case_id'], 'seller_id': 'SELLER', 'marketplace_id': 'ATVPDKIKX0DER', 'message_sha256': sha, 'status': 'verified', 'verified_at': (sent + dt.timedelta(minutes=3)).isoformat()}
        result = self.manual(case, sha, sent, self.evidence('backfill.json', receipt))
        action = result['case']['actions'][-1]
        sent_day = sent.astimezone(core.ZONE).date().isoformat()
        self.assertEqual((f'{sent_day}:{case["registry_id"]}', action['operation_id']), (action['daily_key'], result['case']['daily'][sent_day]['sent_operation_id']))
        self.assertNotIn('sent_operation_id', result['case']['daily'][self.now.date().isoformat()])
        self.assertEqual('ready', self.prepare(self.current(case), 'reply', daily_key=observed['daily_key'])['status'])

    def test_attended_receipt_refuses_account_mismatch_and_unlisted_or_unapproved_sends(self):
        case = self.created()
        run_dir, messages = self.driver_run(case, {'P3': 'Please confirm.'}, run_id='other', account={'seller_id': 'OTHER'})
        self.assertCode('account_mismatch', lambda: self.record_attended(case, run_dir, messages))
        run_dir, messages = self.driver_run(case, {'P1': 'Hello.', 'P3': 'Please confirm.'}, run_id='partial')
        self.assertCode('receipt_incomplete', lambda: self.record_attended(case, run_dir, messages[1:]))
        self.assertCode('label_mismatch', lambda: self.record_attended(case, run_dir, messages, label='appeal'))
        self.assertCode('invalid_label', lambda: self.record_attended(case, run_dir, messages, label='complaint'))
        unapproved, listed = self.driver_run(case, {'P3': 'Please confirm.'}, run_id='unapproved', approvals={'P3': {'approval_text': 'yes'}})
        self.assertCode('approval_mismatch', lambda: self.record_attended(case, unapproved, listed))
        # The pre-click claim cannot be skipped: an unbound run, a run that never claimed, or claimed only after clicking.
        unbound, listed = self.driver_run(case, {'P3': 'Please confirm.'}, run_id='unbound', registry=False)
        self.assertCode('registry_binding_required', lambda: self.record_attended(case, unbound, listed))
        unclaimed, listed = self.driver_run(case, {'P3': 'Please confirm.'}, run_id='unclaimed', claim=False)
        self.assertCode('claim_missing', lambda: self.record_attended(case, unclaimed, listed))
        self.claim(case, self.current(case)['last_sent_at'], run_id='unclaimed')
        self.assertCode('claim_after_click', lambda: self.record_attended(case, unclaimed, listed))
        pending = self.start(message='100.7', issue='pending')
        self.assertCode('case_not_created', lambda: self.record_attended(pending, run_dir, messages))

    def test_release_only_from_stalled_and_released_actions_stop_blocking(self):
        case = self.start()
        prepared = self.prepare(case)
        op = prepared['operation_request']['operation_id']
        directory = self.service.root / 'operations' / op
        directory.mkdir(parents=True)
        (directory / 'plan.json').write_text(json.dumps({'body': prepared['operation_request']['inputs']}))
        started = self.now - dt.timedelta(hours=1)
        journal = lambda status: (directory / 'journal.json').write_text(json.dumps({'operation_id': op, 'account': self.account, 'status': status, 'verified': False, 'effects_started': True, 'execution_started_at': started.isoformat(), 'updated_at': self.now.isoformat()}))  # noqa: E731
        search = lambda contacts, observed=None: self.evidence('search.json', {'account': self.account, 'history_complete': True, 'observed_at': (observed or self.now).isoformat(), 'cases': [{'case_id': '555', 'contacts': contacts}]})  # noqa: E731
        request = {'registry_id': case['registry_id'], 'operation_id': op, 'authorization': self.attended('Nothing was created; release it'), 'evidence': {'readback_path': str(search([])), 'summary': 'Seller Assistant refused; no case created'}}
        journal('uncertain')
        self.assertCode('creation_attempted', lambda: self.service.adopt(self.adoption(case)))
        self.assertCode('not_stalled', lambda: self.service.release(request))
        journal('stalled')
        # The stuck action still blocks another creation under the same binding.
        self.assertCode('immutable_action', lambda: self.prepare(case, body='Please review the separately documented defect.'))
        search([], observed=started - dt.timedelta(minutes=1))
        self.assertCode('stale_readback', lambda: self.service.release(request))
        search([{'id': 'sent', 'is_amazon': False, 'message': prepared['operation_request']['inputs']['signed_body']}])
        self.assertCode('message_observed', lambda: self.service.release(request))
        search([])
        released = self.service.release(request)
        self.assertEqual('released', released['status'])
        self.assertEqual('already_released', self.service.release(request)['status'])
        fresh = self.prepare(case, body='Please review the separately documented defect.')
        self.assertNotEqual(op, fresh['operation_request']['operation_id'])
        adopted = self.service.adopt(self.adoption(case))['case']
        self.assertEqual('claimed', self.claim(adopted, adopted['last_sent_at'])['status'])
        # A journal that leaves stalled blocks again until it is reconciled.
        journal('uncertain')
        self.assertTrue(self.service._uncertain_action(released['case']['actions'][0]))

    def test_cli_exposes_attended_commands(self):
        request = self.root / 'sign.json'
        request.write_text(json.dumps({'body': 'Status?'}))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = core.main(['sign', '--request', str(request), '--state-dir', str(self.root / 'cases'), '--config', str(self.policy)])
        self.assertEqual((0, 'signed'), (code, json.loads(out.getvalue())['status']))
        for command in ('claim-attended', 'release'):
            request.write_text(json.dumps({'authorization': self.auth()}))
            with contextlib.redirect_stdout(io.StringIO()) as out:
                code = core.main([command, '--request', str(request), '--state-dir', str(self.root / 'cases'), '--config', str(self.policy)])
            self.assertEqual((2, 'attended_required'), (code, json.loads(out.getvalue())['reason']))


if __name__ == '__main__':
    unittest.main()
