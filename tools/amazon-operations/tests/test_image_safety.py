import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('image_safety_operations', Path(__file__).resolve().parents[1] / 'operations.py')
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)

MAIN = 'main_product_image_locator.0.media_location'
PT1 = 'other_product_image_locator_1.0.media_location'
PT2 = 'other_product_image_locator_2.0.media_location'
SWATCH = 'swatch_product_image_locator.0.media_location'


class ImageSafetyTests(unittest.TestCase):
    def setUp(self):
        from PIL import Image
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.service = op.Operations(self.root / 'state')
        self.account = {'client_slug': 'brand', 'profile_key': 'brand-us', 'marketplace': 'US'}
        self.rows = {'a': {**dict.fromkeys(op.IMAGE_IDENTITY_KEYS, ''), MAIN: 'https://example.com/main.png', PT1: 'https://example.com/old.png', PT2: 'https://example.com/keep.png', SWATCH: 'https://example.com/swatch.png', 'asin': 'B000000001', 'parentage_level.0.value': 'child', 'child_parent_sku_relationship.0.parent_sku': 'parent'}}
        self.source = self.root / 'export.csv'
        with self.source.open('w') as stream:
            writer = csv.DictWriter(stream, fieldnames=['sku', MAIN, PT1, PT2, SWATCH])
            writer.writeheader()
            writer.writerow({'sku': 'a', **{field: self.rows['a'][field] for field in (MAIN, PT1, PT2, SWATCH)}})
        asset = self.root / 'asset.png'
        Image.new('RGB', (800, 800), 'red').save(asset)
        self.request = {'schema_version': 1, 'operation_id': 'image-test', 'operation': 'listing.images', 'account': self.account, 'targets': ['a'], 'inputs': {
            'image_policy': 'secondary_slots_only', 'source_export': {'path': str(self.source), 'sha256': op.file_hash(self.source)},
            'live': {'account': self.account, 'observed_at': op.now(), 'rows': self.rows}, 'sku_asins': {'a': 'B000000001'},
            'images': [{'sku': 'a', 'slot': 'PT01', 'artifact': {'path': str(asset), 'sha256': op.file_hash(asset)}, 'url': 'https://example.com/new.png'}],
            'image_fields': {'PT01': PT1}}}
        for patcher in (patch.object(op, 'verify_hosted_asset', return_value={'verified_at': op.now()}),
                        patch.object(op, 'session_environment', return_value={})):
            patcher.start()
            self.addCleanup(patcher.stop)

    def prepare(self):
        result = self.service.prepare(self.request)
        self.plan = json.loads(Path(result['plan_path']).read_text())
        self.execute = {'schema_version': 1, 'operation_id': 'image-test', 'plan_hash': result['plan_hash'], 'grant': {
            'execute': True, 'account': self.account, 'operation': 'listing.images', 'targets': ['a'], 'plan_hash': result['plan_hash'], 'allow_live_canary': True}}
        return result

    def fresh(self):
        return {'path': str(self.source), 'sha256': op.file_hash(self.source), 'report_generated_at': op.now(), 'rows': copy.deepcopy(self.rows)}

    def test_task_key_persists_outside_plan_and_prepare_hash(self):
        plain = copy.deepcopy(self.request)
        self.request.update(task_key='bulk-images:rollout', complete_task=True)
        state = self.prepare()
        self.assertEqual(state['task_key'], 'bulk-images:rollout')
        self.assertEqual(self.plan['request_hash'], op.digest(plain))
        self.assertNotIn('task_key', self.plan)
        self.assertNotIn('complete_task', state)
        self.assertNotIn('complete_task', self.plan)
        self.assertEqual(self.service.prepare(plain)['plan_hash'], state['plan_hash'])
        rebound, plan = self.service.bound(Path(state['plan_path']).parent, self.execute)
        self.assertEqual(rebound['task_key'], 'bulk-images:rollout')
        self.assertEqual(op.digest(plan), state['plan_hash'])

    def test_execute_persists_new_task_key_even_on_noop_return(self):
        state = self.prepare()
        directory = Path(state['plan_path']).parent
        self.service.persist(directory, state, 'verified')
        self.service.execute({**self.execute, 'task_key': 'bulk-images:execute', 'complete_task': True})
        self.assertEqual(self.service.view(directory)['task_key'], 'bulk-images:execute')
        self.assertNotIn('complete_task', self.service.view(directory))

    def test_execute_forwards_saved_key_to_adapter_and_both_preflight_routes(self):
        for source in ['flatfilepro_listing_read', 'category_report']:
            with self.subTest(source=source):
                self.request['operation_id'] = source
                self.request['task_key'] = 'bulk-images:rollout'
                self.request['inputs']['image_catalog_source'] = source if source == 'flatfilepro_listing_read' else None
                self.rows['a'].update(itemName='Blue', product_type='SUPPLEMENT')
                state = self.prepare()
                execute = {**self.execute, 'operation_id': source, 'complete_task': True}
                directory = Path(state['plan_path']).parent
                def collected(_directory, script, envelope, **kwargs):
                    self.assertEqual(envelope['task_key'], 'bulk-images:rollout')
                    self.assertIs(envelope['complete_task'], False)
                    response = {'status': 'collected', 'complete': True, 'complete_report': True,
                                'source_kind': 'flatfilepro_listing_read', 'account': self.account,
                                'plan_hash': state['plan_hash'], 'observed_at': op.now(),
                                'report_generated_at': op.now(), 'rows': self.rows}
                    path = directory / 'fresh.json'
                    path.write_text(json.dumps(response))
                    return {**response, 'path': str(path), 'sha256': op.file_hash(path)}
                response = {'plan_hash': state['plan_hash'], 'status': 'processing', 'submission_id': 'run'}
                with patch.object(self.service, 'run_collector', side_effect=collected) as collector, patch.object(op, 'evidence_tools', return_value=Mock(report_rows=Mock(return_value=self.rows), field_value=op.evidence_tools().field_value)), patch.object(op.subprocess, 'run', return_value=Mock(stdout=json.dumps(response))):
                    self.service.execute(execute)
                self.assertEqual(collector.call_count, 1)
                self.assertEqual(collector.call_args.args[1], 'flatfilepro-listings.mjs' if source == 'flatfilepro_listing_read' else 'catalog-export.mjs')
                envelope = json.loads((directory / 'adapter-input.json').read_text())
                self.assertEqual(envelope['task_key'], 'bulk-images:rollout')
                self.assertIs(envelope['complete_task'], False)
                self.assertEqual(op.digest(envelope['plan']), state['plan_hash'])

    def test_reconcile_completion_only_reaches_final_preservation_collector(self):
        for source in ['flatfilepro_listing_read', 'category_report']:
            for complete_task in [False, True]:
                with self.subTest(source=source, complete_task=complete_task):
                    operation_id = f'{source}-{complete_task}'
                    self.request.update(operation_id=operation_id, task_key='bulk-images:rollout')
                    self.request['inputs']['image_catalog_source'] = source if source == 'flatfilepro_listing_read' else None
                    self.rows['a'].update(itemName='Blue', product_type='SUPPLEMENT')
                    state = self.prepare()
                    directory = Path(state['plan_path']).parent
                    if source == 'category_report':
                        self.plan['body']['adapter'] = 'catalog.cdp'
                    op.atomic_json(directory / 'plan.json', self.plan)
                    state['plan_hash'] = op.digest(self.plan)
                    self.service.persist(directory, state, 'processing', effects_started=True, submission_id='run')
                    request = {'schema_version': 1, 'operation_id': operation_id,
                               'plan_hash': state['plan_hash'], 'complete_task': complete_task}
                    pending = {'processing_pending': True, 'processing': 'pending', 'preservation': 'pending',
                               'release_eligible': False, 'matched': [], 'pending': [], 'failures': []}
                    complete = {**pending, 'processing_pending': False, 'processing': 'complete',
                                'preservation': 'verified', 'release_eligible': True, 'matched': ['a/PT01']}
                    # Keep actual collector dispatch, with empty PDP results avoiding downloads.
                    with patch.object(self.service, 'run_collector', return_value={'status': 'blocked', 'images': []}) as collector, patch.object(self.service, 'image_completion', side_effect=[pending, complete]), patch.object(op, 'session_environment', return_value={'CDP_PORT': '9223'}), patch.object(op.subprocess, 'run') as completion:
                        self.assertEqual(self.service.reconcile(request)['status'], 'processing')
                        completion.assert_not_called()
                        first_calls = list(collector.call_args_list)
                        self.assertEqual(self.service.reconcile(request)['status'], 'verified')
                        self.assertEqual(completion.call_count, int(complete_task))
                    scripts = [call.args[1] for call in first_calls]
                    self.assertEqual(scripts, ['flatfilepro-activity.mjs', 'image-evidence.mjs', 'flatfilepro-listings.mjs' if source == 'flatfilepro_listing_read' else 'catalog-export.mjs'])
                    self.assertEqual(collector.call_count, 2 * len(scripts))
                    for call in collector.call_args_list:
                        self.assertEqual(call.args[2]['task_key'], 'bulk-images:rollout')
                        self.assertIs(call.args[2]['complete_task'], False)
                    self.assertNotIn('complete_task', self.service.view(directory))

    def test_reconcile_persists_late_key_and_recovery_does_not_complete(self):
        state = self.prepare()
        directory = Path(state['plan_path']).parent
        self.service.persist(directory, state, 'uncertain', effects_started=True)
        request = {**self.execute, 'task_key': 'bulk-images:recovery', 'complete_task': True}
        def collected(_directory, script, envelope, **kwargs):
            if script == 'flatfilepro.mjs':
                return {'status': 'collected', 'submission_id': 'recovered', 'processing_status': 'processing'}
            return {'status': 'blocked', 'images': []}
        with patch.object(self.service, 'run_collector', side_effect=collected) as collector, patch.object(self.service, 'image_completion', return_value={'processing_pending': True, 'processing': 'pending', 'preservation': 'pending', 'release_eligible': False, 'matched': [], 'pending': [], 'failures': []}):
            self.service.reconcile(request)
        self.assertEqual(collector.call_args_list[0].args[1], 'flatfilepro.mjs')
        for index, call in enumerate(collector.call_args_list):
            self.assertEqual(call.args[2]['task_key'], 'bulk-images:recovery')
            self.assertIs(call.args[2]['complete_task'], False)
        self.assertEqual(self.service.bound(directory, self.execute)[0]['task_key'], 'bulk-images:recovery')

    def test_case_observe_hash_excludes_browser_lifecycle_fields(self):
        request = {'schema_version': 1, 'operation_id': 'observe', 'operation': 'case.create',
                   'account': self.account, 'targets': [{'issue_key': 'test-case'}]}
        for extras in [{}, {'task_key': 'bulk-images:rollout', 'complete_task': True}]:
            with self.subTest(extras=extras), patch.object(self.service, 'run_collector', return_value={}) as collector:
                self.service.observe({**request, **extras})
                envelope = collector.call_args.args[2]
                self.assertEqual(envelope['plan_hash'], op.digest(request))
                for key, value in extras.items():
                    self.assertEqual(envelope[key], value)

    def test_upload_contains_only_requested_secondaries_and_freezes_other_images(self):
        self.prepare()
        self.assertEqual(self.plan['body']['mapping'], [PT1])
        self.assertEqual(self.plan['body']['expected_rows'], {'a': {PT1: 'https://example.com/new.png'}})
        before = self.plan['body']['image_before_rows']['a']
        self.assertEqual(before[MAIN], self.rows['a'][MAIN])
        self.assertEqual(before[PT2], self.rows['a'][PT2])
        self.assertEqual(before[SWATCH], self.rows['a'][SWATCH])

    def test_standalone_requires_explicit_ffp_route_and_no_parent(self):
        row = self.request['inputs']['live']['rows']['a']
        row.update({'parentage_level.0.value': '', 'child_parent_sku_relationship.0.parent_sku': '',
                    'listing_relationship_evidence': 'standalone', 'itemName': 'Blue', 'product_type': 'SUPPLEMENT'})
        with self.assertRaisesRegex(op.OperationError, 'child listings'):
            self.prepare()
        self.request['operation_id'] = 'standalone-valid'
        self.request['inputs'].update(image_catalog_source='flatfilepro_listing_read', allow_standalone_images=True)
        self.prepare()
        self.assertEqual(self.plan['body']['image_before_rows']['a']['parentage_level.0.value'], '')
        self.assertEqual(self.plan['body']['image_before_rows']['a']['listing_relationship_evidence'], 'standalone')
        self.assertEqual(self.plan['body']['image_preview_metadata']['a']['productType'], 'SUPPLEMENT')
        self.request['operation_id'] = 'standalone-invalid'
        row['child_parent_sku_relationship.0.parent_sku'] = 'PARENT'
        with self.assertRaisesRegex(op.OperationError, 'child listings'):
            self.prepare()

    def test_ffp_catalog_path_does_not_request_category_report(self):
        self.request['inputs'].update(image_catalog_source='flatfilepro_listing_read')
        self.request['inputs']['live']['rows']['a'].update(itemName='Blue', product_type='SUPPLEMENT')
        result = self.prepare()
        fresh = {'rows': copy.deepcopy(self.rows), 'path': str(self.source), 'sha256': op.file_hash(self.source),
                 'observed_at': op.now(), 'source_kind': 'flatfilepro_listing_read'}
        response = {'plan_hash': result['plan_hash'], 'status': 'blocked', 'attempted': False, 'reason': 'test_stop_before_apply'}
        with patch.object(self.service, 'collect_image_catalog', return_value=fresh) as ffp, \
             patch.object(self.service, 'collect_export', side_effect=AssertionError('CLR must not run')), \
             patch.object(op.subprocess, 'run', return_value=type('Result', (), {'stdout': json.dumps(response)})()):
            executed = self.service.execute(self.execute)
        self.assertEqual(executed['status'], 'blocked')
        ffp.assert_called_once()

    def test_ffp_listing_collector_uses_real_dispatch_and_rejects_unknown_script(self):
        self.request['inputs']['image_catalog_source'] = 'flatfilepro_listing_read'
        self.request['inputs']['live']['rows']['a'].update(itemName='Blue', product_type='SUPPLEMENT')
        result = self.prepare()
        directory = Path(result['plan_path']).parent
        response = {'status': 'collected', 'complete': True, 'source_kind': 'flatfilepro_listing_read',
                    'account': self.account, 'plan_hash': result['plan_hash'], 'observed_at': op.now(), 'rows': self.rows}
        path = self.root / 'ffp-listings.json'
        path.write_text(json.dumps(response))
        response.update(path=str(path), sha256=op.file_hash(path))
        with patch.object(op.subprocess, 'Popen', return_value=Mock(communicate=Mock(return_value=(json.dumps(response), '')))) as child:
            observed = self.service.collect_image_catalog(directory, {'plan_hash': result['plan_hash']}, self.plan, purpose='preflight')
            self.assertEqual(observed['rows'], self.rows)
            self.assertTrue(child.call_args.args[0][1].endswith('/flatfilepro-listings.mjs'))
            saved_input = json.loads((directory / 'flatfilepro-listings-input.json').read_text())
            self.assertEqual(saved_input['targets'], [{'sku': 'a', 'asin': 'B000000001'}])
            self.assertEqual(saved_input['account'], self.account)
            child.reset_mock()
            with self.assertRaisesRegex(op.OperationError, 'Unknown fixed collector'):
                self.service.run_collector(directory, 'untrusted-script.mjs', saved_input)
            child.assert_not_called()

    def test_main_or_swatch_cannot_enter_secondary_upload(self):
        for slot, field in [('MAIN', MAIN), ('SWCH', SWATCH)]:
            with self.subTest(slot=slot):
                self.request['inputs']['images'][0]['slot'] = slot
                self.request['inputs']['image_fields'] = {slot: field}
                with self.assertRaisesRegex(op.OperationError, 'cannot change MAIN'):
                    self.prepare()

    def test_colliding_mangled_and_canonical_headers_are_rejected(self):
        self.request['inputs']['image_fields'] = {'PT01': PT1, 'PT02': 'other_product_image_locator_1__1__media_location'}
        with self.assertRaisesRegex(op.OperationError, 'own template attribute'):
            self.prepare()

    def test_mangled_ffp_header_accepts_canonical_live_catalog_evidence(self):
        mangled = 'other_product_image_locator_1__1__media_location'
        self.source.write_text(self.source.read_text().replace(PT1, mangled))
        self.request['inputs']['source_export']['sha256'] = op.file_hash(self.source)
        self.request['inputs']['image_fields']['PT01'] = mangled
        self.prepare()
        self.assertEqual(self.plan['body']['mapping'], [mangled])
        self.assertEqual(set(self.plan['body']['expected_rows']['a']), {mangled})
        from openpyxl import load_workbook
        workbook = load_workbook(self.plan['body']['upload'], read_only=True)
        try:
            self.assertEqual(list(next(workbook.active.values)), ['sku', mangled])
        finally:
            workbook.close()
        self.assertEqual(self.plan['body']['image_before_rows']['a'][PT1], self.rows['a'][PT1])

    def test_secondary_cannot_map_to_main_or_another_slot(self):
        for field in (MAIN, PT2):
            self.request['inputs']['image_fields']['PT01'] = field
            with self.assertRaisesRegex(op.OperationError, 'exact supported'):
                self.prepare()

    def test_parent_and_wrong_asin_rejected(self):
        self.rows['a']['parentage_level.0.value'] = 'parent'
        with self.assertRaisesRegex(op.OperationError, 'child listings'):
            self.prepare()
        self.rows['a']['parentage_level.0.value'] = 'child'
        self.rows['a']['asin'] = 'B000000002'
        with self.assertRaisesRegex(op.OperationError, 'exact ASIN'):
            self.prepare()

    def test_missing_protected_image_evidence_rejected(self):
        del self.rows['a'][SWATCH]
        with self.assertRaisesRegex(op.OperationError, 'including protected slots'):
            self.prepare()

    def test_fresh_preflight_detects_main_child_and_untouched_slot_changes(self):
        self.prepare()
        for field in (MAIN, SWATCH, PT2, 'asin', 'child_parent_sku_relationship.0.parent_sku'):
            fresh = self.fresh()
            fresh['rows']['a'][field] = 'changed'
            with self.subTest(field=field), patch.object(self.service, 'collect_export', return_value=fresh), patch.object(op.subprocess, 'run') as adapter:
                with self.assertRaisesRegex(op.OperationError, 'protected image changed'):
                    self.service.execute(self.execute)
                adapter.assert_not_called()

    def test_pending_preflight_retries_collection_without_submitting(self):
        self.prepare()
        with patch.object(self.service, 'collect_export', return_value=None), patch.object(op.subprocess, 'run') as adapter:
            for _ in range(2):
                result = self.service.execute(self.execute)
                self.assertEqual(result['phase'], 'image_preflight')
                self.assertFalse(result['effects_started'])
            adapter.assert_not_called()

    def test_preflight_expiry_and_future_dates_never_reach_adapter(self):
        self.prepare()
        for delta in (op.dt.timedelta(minutes=-6), op.dt.timedelta(minutes=1)):
            fresh = self.fresh()
            fresh['report_generated_at'] = (op.timestamp(op.now()) + delta).isoformat()
            with patch.object(self.service, 'collect_export', return_value=fresh), patch.object(op.subprocess, 'run') as adapter:
                with self.assertRaisesRegex(op.OperationError, 'five minutes old'):
                    self.service.execute(self.execute)
                adapter.assert_not_called()

    def test_timeout_does_not_resubmit_and_recovery_can_resolve_import(self):
        self.prepare()
        with patch.object(self.service, 'collect_export', return_value=self.fresh()), patch.object(op.subprocess, 'run', side_effect=op.subprocess.TimeoutExpired('node', 1)) as adapter:
            self.assertEqual(self.service.execute(self.execute)['status'], 'uncertain')
            self.assertEqual(self.service.execute(self.execute)['status'], 'uncertain')
            self.assertEqual(adapter.call_count, 1)
        state = self.service.view(self.root / 'state/image-test')
        recovery = {'status': 'collected', 'submission_id': 'import-1', 'processing_status': 'processing'}
        with patch.object(self.service, 'run_collector', return_value=recovery) as collector, patch.object(self.service, 'collect_images', return_value=None):
            self.service.collect(self.root / 'state/image-test', state, self.plan)
            self.assertEqual(state['submission_id'], 'import-1')
            self.assertEqual(collector.call_args.args[1], 'flatfilepro.mjs')
            self.assertEqual(collector.call_args.args[2]['mode'], 'reconcile')

    def test_new_receipt_route_flags_come_only_from_bound_grant(self):
        from types import SimpleNamespace
        self.prepare()
        self.execute['allow_validated_image_adapter'] = True
        response = SimpleNamespace(stdout=json.dumps({'plan_hash': self.execute['plan_hash'], 'status': 'blocked', 'attempted': False}))
        with patch.object(self.service, 'collect_export', return_value=self.fresh()), patch.object(op.subprocess, 'run', return_value=response):
            self.service.execute(self.execute)
        envelope = json.loads((self.root / 'state/image-test/adapter-input.json').read_text())
        self.assertTrue(envelope['allow_attended_canary'])
        self.assertFalse(envelope['allow_validated_image_adapter'])
        self.execute['grant'].pop('allow_live_canary')
        self.execute['grant']['allow_validated_adapter'] = True
        with patch.object(self.service, 'collect_export', return_value=self.fresh()), patch.object(op.subprocess, 'run', return_value=response):
            self.service.execute(self.execute)
        envelope = json.loads((self.root / 'state/image-test/adapter-input.json').read_text())
        self.assertFalse(envelope['allow_attended_canary'])
        self.assertTrue(envelope['allow_validated_image_adapter'])

    def test_verification_requires_preserved_main_and_swatches(self):
        self.prepare()
        rows = copy.deepcopy(self.rows)
        rows['a'][PT1] = 'new'
        self.service.validate_image_baseline(self.plan, rows, protected_only=True)
        rows['a'][MAIN] = 'changed'
        with self.assertRaisesRegex(op.OperationError, 'protected image changed'):
            self.service.validate_image_baseline(self.plan, rows, protected_only=True)

    def test_partial_processing_reports_failed_slots_separately_from_verified_images(self):
        from types import SimpleNamespace
        second = copy.deepcopy(self.request['inputs']['images'][0]); second.update(slot='PT02', url='https://example.com/new2.png')
        self.request['inputs']['images'].append(second)
        self.request['inputs']['image_fields']['PT02'] = PT2
        self.prepare()
        response = SimpleNamespace(stdout=json.dumps({'plan_hash': self.execute['plan_hash'], 'status': 'processing', 'attempted': True, 'submission_id': 'run-1'}))
        with patch.object(self.service, 'collect_export', return_value=self.fresh()), patch.object(op.subprocess, 'run', return_value=response):
            self.service.execute(self.execute)
        evidence = {'account': self.account, 'plan_hash': self.execute['plan_hash'], 'submission_id': 'run-1',
                    'observed_at': op.now(), 'source_id': 'Amazon exact children', 'processing_status': 'live_observed',
                    'protected_rows': self.rows, 'images': [
                        {'sku': image['sku'], 'slot': image['slot'], 'source_sha256': image['sha256'], 'visually_verified': True, 'live_url': 'https://amazon.example/image.png'}
                        for image in self.plan['body']['images']]}
        request = {'schema_version': 1, 'operation_id': 'image-test', 'plan_hash': self.execute['plan_hash'], 'evidence': evidence}
        incomplete = self.service.reconcile(request)
        self.assertEqual(incomplete['image_completion']['processing'], 'unknown')
        evidence['preservation_source'] = {'observed_at': op.now()}
        archive = self.root / 'state/image-test/observed-images'
        archive.mkdir()
        for image, observed in zip(self.plan['body']['images'], evidence['images']):
            path = archive / image['sha256']
            path.write_bytes(Path(image['path']).read_bytes())
            observed.update(observed_path=str(path), observed_sha256=image['sha256'], asin='B000000001',
                            observed_at=op.now(), source_id='https://www.amazon.com/dp/B000000001')
        self.add_protected_fixture(evidence, path)
        evidence['ffp_processing'] = {'status': 'collected', 'complete': True, 'account': self.account,
            'plan_hash': self.execute['plan_hash'], 'submission_id': 'run-1', 'observed_at': op.now(), 'attributes': [
                {'sku': 'a', 'field': PT1, 'status': 'reflected', 'submitted_value': 'https://example.com/new.png'},
                {'sku': 'a', 'field': PT2, 'status': 'rejected', 'submitted_value': 'https://example.com/new2.png'}]}
        result = self.service.reconcile(request)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['matched'], ['a/PT01', 'a/PT02'])
        self.assertEqual(result['pending'], [])
        self.assertEqual(result['failures'], ['a/PT02: rejected'])

    def completion_fixture(self):
        self.prepare()
        directory = self.root / 'state/image-test'
        state = self.service.view(directory)
        state.update(submission_id='run-1', execution_started_at=op.now(), effects_started=True)
        self.service.persist(directory, state, 'processing')
        image = self.plan['body']['images'][0]
        path = directory / 'observed-images' / image['sha256']
        path.parent.mkdir()
        path.write_bytes(Path(image['path']).read_bytes())
        evidence = {'account': self.account, 'plan_hash': self.execute['plan_hash'], 'submission_id': 'run-1',
            'observed_at': op.now(), 'source_id': 'amazon-live-imageblock', 'processing_status': 'live_observed',
            'protected_rows': copy.deepcopy(self.rows), 'preservation_source': {'observed_at': op.now()},
            'images': [{'sku': 'a', 'slot': 'PT01', 'asin': 'B000000001', 'source_sha256': image['sha256'],
                'observed_path': str(path), 'observed_sha256': image['sha256'], 'observed_at': op.now(),
                'live_url': 'https://m.media-amazon.com/images/I/test.jpg', 'source_id': 'https://www.amazon.com/dp/B000000001'}],
            'ffp_processing': {'status': 'collected', 'complete': True, 'account': self.account,
                'plan_hash': self.execute['plan_hash'], 'submission_id': 'run-1', 'observed_at': op.now(),
                'attributes': [{'sku': 'a', 'field': PT1, 'status': 'in_progress', 'submitted_value': 'https://example.com/new.png'}]}}
        self.add_protected_fixture(evidence, path)
        return directory, state, evidence

    def add_protected_fixture(self, evidence, path):
        evidence['protected_images'] = [
            {'sku': sku, 'slot': slot, 'asin': self.plan['body']['sku_asins'][sku], 'observed_at': op.now(),
             'expected_url': url, 'expected_path': str(path), 'observed_path': str(path),
             'expected_sha256': op.file_hash(path), 'observed_sha256': op.file_hash(path)}
            for (sku, slot), url in self.service.public_protected_images(self.plan).items()]

    def test_publication_release_keeps_processing_pending_and_never_submits(self):
        directory, state, evidence = self.completion_fixture()
        request = {**self.execute, 'evidence': evidence}
        with patch.object(self.service, 'execute', side_effect=AssertionError('Must never submit')):
            for _ in range(2):
                result = self.service.reconcile(request)
                completion = result['image_completion']
                self.assertEqual(completion['publication'], 'verified')
                self.assertEqual(completion['processing'], 'pending')
                self.assertTrue(completion['release_eligible'])
                self.assertFalse(result['verified'])
            proof = self.service.image_release_proof(self.execute)
            self.assertTrue(proof['release_eligible'])
            self.assertEqual(proof['proof_digest'], op.digest(evidence))
        evidence['ffp_processing']['attributes'][0]['status'] = 'reflected'
        self.assertTrue(self.service.reconcile(request)['verified'])

    def test_release_rejects_stale_wrong_missing_or_changed_evidence(self):
        directory, state, baseline = self.completion_fixture()
        mutations = [
            lambda e: e['ffp_processing'].update(observed_at='2020-01-01T00:00:00Z'),
            lambda e: e['ffp_processing'].update(submission_id='other'),
            lambda e: e['ffp_processing']['attributes'][0].update(submitted_value='wrong'),
            lambda e: e['ffp_processing']['attributes'].append(copy.deepcopy(e['ffp_processing']['attributes'][0])),
            lambda e: e['images'][0].update(asin='B000000002'),
            lambda e: e['images'][0].update(observed_at='2020-01-01T00:00:00Z'),
            lambda e: e['protected_rows']['a'].pop(SWATCH),
            lambda e: e['protected_rows']['a'].update({MAIN: 'changed'}),
            lambda e: e.pop('preservation_source'),
            lambda e: e.pop('protected_images'),
            lambda e: e['ffp_processing']['attributes'][0].update(status='rejected'),
        ]
        for mutation in mutations:
            evidence = copy.deepcopy(baseline)
            mutation(evidence)
            with self.subTest(mutation=mutation):
                self.assertFalse(self.service.image_completion(directory, state, self.plan, evidence)['release_eligible'])
        wrong = copy.deepcopy(baseline)
        wrong['account'] = {'client_slug': 'kabooki'}
        with self.assertRaisesRegex(op.OperationError, 'identity mismatch'):
            self.service.image_completion(directory, state, self.plan, wrong)

    def test_attended_review_reuses_only_exact_reviewed_pair_and_slot(self):
        from PIL import Image
        directory, state, evidence = self.completion_fixture()
        image = self.plan['body']['images'][0]
        original = Path(image['path']).read_bytes()
        jpeg = self.root / 'observed.jpg'
        Image.open(image['path']).save(jpeg, quality=80)
        self.assertIsNone(op.evidence_tools().same_image_content(original, jpeg.read_bytes()))
        review = {'sku': 'a', 'slot': 'PT01', 'asin': 'B000000001', 'source_sha256': image['sha256'],
                  'observed_path': str(jpeg), 'observed_sha256': op.file_hash(jpeg),
                  'source_id': 'https://www.amazon.com/dp/B000000001', 'decision': 'match'}
        request = {**self.execute, 'reviews': [review], 'reviewed_at': op.now(),
                   'reviewer': {'kind': 'attended_agent', 'id': 'test-agent', 'context': 'test-attended-review'}}
        receipt = self.service.record_image_review(request)
        self.assertEqual(receipt, self.service.record_image_review(request))
        self.assertEqual(len(list(directory.glob('image-review-*.json'))), 1)
        archived = directory / 'observed-images' / op.file_hash(jpeg)
        archived.write_bytes(jpeg.read_bytes())
        evidence['images'][0].update(observed_path=str(archived), observed_sha256=op.file_hash(jpeg))
        self.assertTrue(self.service.image_completion(directory, state, self.plan, evidence)['release_eligible'])
        # A tiny pixel change is never accepted based on visual metrics.
        changed = Image.open(jpeg)
        changed.putpixel((1, 1), (0, 0, 255))
        changed.save(archived, format='PNG')
        evidence['images'][0]['observed_sha256'] = op.file_hash(archived)
        self.assertFalse(self.service.image_completion(directory, state, self.plan, evidence)['release_eligible'])

    def test_collectors_fail_independently(self):
        directory, state, evidence = self.completion_fixture()
        response = {'status': 'blocked', 'images': [], 'message': 'PDP timeout'}
        with patch.object(self.service, 'run_collector', side_effect=[{'status': 'blocked'}, response]) as collector, \
             patch.object(self.service, 'collect_image_catalog', return_value={'rows': self.rows, 'observed_at': op.now()}) as preserved, \
             patch.object(self.service, 'collect_export', side_effect=AssertionError('Historical FFP image plans must not request CLR')):
            original_hash = op.digest(self.plan)
            self.assertNotIn('image_catalog_source', self.plan['body'])
            result = self.service.collect_images(directory, state, self.plan)
            self.assertEqual(collector.call_count, 2)
            preserved.assert_called_once()
            self.assertEqual(result['protected_rows'], self.rows)
            self.assertEqual(result['pdp_collection']['message'], 'PDP timeout')
            self.assertEqual(op.digest(self.plan), original_hash)

    def image_poll_fixture(self, *, published=False):
        directory, state, evidence = self.completion_fixture()
        evidence['ffp_processing']['summary'] = {'reflected': 0, 'inProgress': 1, 'rejected': 0, 'failed': 0}
        def collected(_directory, script, envelope, **kwargs):
            self.assertIs(envelope['complete_task'], False)
            if script == 'flatfilepro-activity.mjs':
                return {**copy.deepcopy(evidence['ffp_processing']), 'observed_at': op.now()}
            if script == 'image-evidence.mjs':
                return {'status': 'collected', 'operation_id': self.plan['operation_id'],
                        'account': self.account, 'plan_hash': state['plan_hash'],
                        'observed_at': op.now(), 'images': [
                            {**item, 'observed_at': op.now(), 'live_url': item.get('live_url', item.get('expected_url')),
                             'source_id': 'https://www.amazon.com/dp/B000000001'}
                            for item in evidence['images'] + evidence['protected_images']
                        ] if published else []}
            self.assertEqual(script, 'flatfilepro-listings.mjs')
            result = {'status': 'collected', 'complete': True, 'source_kind': 'flatfilepro_listing_read',
                      'account': self.account, 'plan_hash': state['plan_hash'], 'observed_at': op.now(),
                      'rows': copy.deepcopy(evidence['protected_rows'])}
            path = directory / 'poll-listings.json'
            op.atomic_json(path, result)
            return {**result, 'path': str(path), 'sha256': op.file_hash(path)}
        with patch.object(self.service, 'run_collector', side_effect=collected) as collector, \
             patch.object(op.evidence_tools(), 'fetch_public_image', return_value=Path(self.plan['body']['images'][0]['path']).read_bytes()):
            result = self.service.reconcile(self.execute)
        self.assertEqual(result['status'], 'partial' if published else 'processing')
        self.assertEqual(collector.call_count, 3)
        return directory, evidence, collected

    def test_skipped_partial_keeps_publication_after_freshness_expiry(self):
        directory, evidence, collected = self.image_poll_fixture(published=True)
        before = self.service.view(directory)
        for age in (1800, 3599):
            with self.subTest(age=age):
                clock = (op.timestamp(before['last_image_full_read_at']) + op.dt.timedelta(seconds=age)).isoformat()
                with patch.object(op, 'now', return_value=clock), \
                     patch.object(self.service, 'run_collector', side_effect=collected) as collector, \
                     patch.object(self.service, '_complete_reconciled_task') as complete:
                    result = self.service.reconcile(self.execute)
                    proof = self.service.image_release_proof(self.execute)
                self.assertEqual([call.args[1] for call in collector.call_args_list], ['flatfilepro-activity.mjs'])
                self.assertEqual(result['evidence_skipped'], 'activity-unchanged')
                for key in ('status', 'verified', 'matched', 'pending', 'failures', 'image_completion', 'last_image_full_read_at'):
                    self.assertEqual(result[key], before[key])
                self.assertEqual((len(result['matched']), len(result['pending'])), (1, 0))
                self.assertFalse(proof['release_eligible'])
                self.assertEqual(proof['matched'], [])
                complete.assert_not_called()

    def test_partial_past_full_read_bound_runs_pdp_and_preservation_reads(self):
        directory, evidence, collected = self.image_poll_fixture(published=True)
        before = self.service.view(directory)
        clock = (op.timestamp(before['last_image_full_read_at']) + op.dt.timedelta(seconds=3601)).isoformat()
        with patch.object(op, 'now', return_value=clock), \
             patch.object(self.service, 'run_collector', side_effect=collected) as collector, \
             patch.object(op.evidence_tools(), 'fetch_public_image', return_value=Path(self.plan['body']['images'][0]['path']).read_bytes()):
            result = self.service.reconcile(self.execute)
        self.assertEqual([call.args[1] for call in collector.call_args_list],
                         ['flatfilepro-activity.mjs', 'image-evidence.mjs', 'flatfilepro-listings.mjs'])
        self.assertNotIn('evidence_skipped', result)
        self.assertEqual(result['last_image_full_read_at'], clock)
        for key in ('status', 'matched', 'pending', 'failures'):
            self.assertEqual(result[key], before[key])
        saved = json.loads(Path(result['evidence_path']).read_text())
        self.assertEqual(saved['images'][0]['observed_at'], clock)
        self.assertEqual(saved['preservation_source']['observed_at'], clock)

    def test_unchanged_processing_skips_reads_and_preserves_evidence_and_result(self):
        directory, evidence, collected = self.image_poll_fixture()
        before = self.service.view(directory)
        previous_evidence = json.loads(Path(before['evidence_path']).read_text())
        clock = previous_evidence['observed_at']
        with patch.object(op, 'now', return_value=clock), \
             patch.object(self.service, 'run_collector', side_effect=collected) as collector, \
             patch.object(self.service, '_complete_reconciled_task') as complete:
            skipped = self.service.reconcile(self.execute)
            self.assertEqual([call.args[1] for call in collector.call_args_list], ['flatfilepro-activity.mjs'])
            self.assertEqual(skipped['evidence_skipped'], 'activity-unchanged')
            self.assertEqual(skipped['last_collection'], before['last_collection'])
            self.assertEqual(skipped['last_catalog_collection'], before['last_catalog_collection'])
            self.assertEqual(skipped['last_image_full_read_at'], before['last_image_full_read_at'])
            self.assertEqual(skipped['image_completion'], before['image_completion'])
            complete.assert_not_called()
            saved = json.loads(Path(skipped['evidence_path']).read_text())
            for key in ('images', 'pdp_collection', 'protected_images', 'preservation_source', 'protected_rows'):
                self.assertEqual(saved[key], previous_evidence[key])
            # Restore the same starting journal to compare with a forced full pass.
            op.atomic_json(directory / 'journal.json', before)
            full = self.service.reconcile({**self.execute, 'full_verify_seconds': 0})
            self.assertNotIn('evidence_skipped', full)
            self.assertEqual(collector.call_count, 4)
        # Collection timestamps and evidence digests describe the reads performed.
        for key in ('status', 'verified', 'matched', 'pending', 'failures', 'submission_id'):
            self.assertEqual(skipped[key], full[key])
        self.assertEqual(set(skipped), set(full) | {'evidence_skipped'})
        for key in skipped['image_completion']:
            if key != 'proof_digest':
                self.assertEqual(skipped['image_completion'][key], full['image_completion'][key])
        complete.assert_called_once()
        self.assertEqual(complete.call_args.args[3], 'processing')

    def test_changed_activity_always_runs_all_reads(self):
        directory, evidence, collected = self.image_poll_fixture()
        baseline = self.service.view(directory)
        activity = copy.deepcopy(evidence['ffp_processing'])
        mutations = [
            lambda a: a['attributes'][0].update(status='pending'),
            lambda a: a['summary'].update(inProgress=2),
            lambda a: a['summary'].update(failed=1),
            lambda a: a.update(errors=['New rejection']),
            lambda a: a['attributes'][0].update(status='reflected'),
            lambda a: a['attributes'][0].update(status='failed'),
            lambda a: a['attributes'][0].update(status='rejected'),
            lambda a: a.update(status='blocked', complete=False),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                op.atomic_json(directory / 'journal.json', baseline)
                evidence['ffp_processing'] = copy.deepcopy(activity)
                mutation(evidence['ffp_processing'])
                with patch.object(self.service, 'run_collector', side_effect=collected) as collector:
                    result = self.service.reconcile(self.execute)
                self.assertEqual(collector.call_count, 3)
                self.assertNotIn('evidence_skipped', result)

    def test_periodic_bound_and_request_override_force_full_reads(self):
        directory, evidence, collected = self.image_poll_fixture()
        baseline = self.service.view(directory)
        for age, override, count in [(3599, None, 1), (3600, None, 3), (3601, None, 3),
                                     (61, 60, 3), (60, 120, 1), (0, 0, 3)]:
            with self.subTest(age=age, override=override):
                op.atomic_json(directory / 'journal.json', baseline)
                clock = (op.timestamp(baseline['last_image_full_read_at']) + op.dt.timedelta(seconds=age)).isoformat()
                request = {**self.execute, **({'full_verify_seconds': override} if override is not None else {})}
                with patch.object(op, 'now', return_value=clock), patch.object(self.service, 'run_collector', side_effect=collected) as collector:
                    result = self.service.reconcile(request)
                self.assertEqual(collector.call_count, count)
                self.assertEqual(result.get('evidence_skipped'), 'activity-unchanged' if count == 1 else None)

    def test_complete_task_forces_full_reads_without_completing_processing_task(self):
        directory, evidence, collected = self.image_poll_fixture()
        with patch.object(self.service, 'run_collector', side_effect=collected) as collector, \
             patch.object(op.subprocess, 'run') as complete:
            result = self.service.reconcile({**self.execute, 'complete_task': True})
        self.assertEqual(collector.call_count, 3)
        self.assertEqual(result['status'], 'processing')
        self.assertNotIn('evidence_skipped', result)
        complete.assert_not_called()

    def test_unchanged_terminal_activity_never_skips(self):
        directory, evidence, collected = self.image_poll_fixture()
        baseline = self.service.view(directory)
        for status in ('reflected', 'failed', 'rejected'):
            with self.subTest(status=status):
                evidence['ffp_processing']['attributes'][0]['status'] = status
                journal = copy.deepcopy(baseline)
                journal['last_processing_collection'] = copy.deepcopy(evidence['ffp_processing'])
                saved = json.loads(Path(baseline['evidence_path']).read_text())
                saved['ffp_processing'] = copy.deepcopy(evidence['ffp_processing'])
                path = directory / f'evidence-{op.digest(saved)}.json'
                op.atomic_json(path, saved)
                journal['evidence_path'] = str(path)
                op.atomic_json(directory / 'journal.json', journal)
                with patch.object(self.service, 'run_collector', side_effect=collected) as collector:
                    result = self.service.reconcile(self.execute)
                self.assertEqual(collector.call_count, 3)
                self.assertNotIn('evidence_skipped', result)
                if status in {'failed', 'rejected'}:
                    self.assertEqual(result['status'], 'failed')

    def test_terminal_candidate_from_cached_evidence_forces_current_reads(self):
        directory, evidence, collected = self.image_poll_fixture()
        baseline = self.service.view(directory)
        completion = copy.deepcopy(baseline['image_completion'])
        for processing, preservation in [('complete', 'verified'), ('failed', 'verified'), ('unknown', 'conflict')]:
            with self.subTest(processing=processing, preservation=preservation):
                op.atomic_json(directory / 'journal.json', baseline)
                terminal = {**completion, 'processing': processing, 'preservation': preservation,
                            'processing_pending': [], 'release_eligible': True}
                with patch.object(self.service, 'run_collector', side_effect=collected) as collector, \
                     patch.object(self.service, 'image_completion', side_effect=[terminal, completion]), \
                     patch.object(self.service, '_complete_reconciled_task') as complete:
                    result = self.service.reconcile(self.execute)
                self.assertEqual([call.args[1] for call in collector.call_args_list],
                    ['flatfilepro-activity.mjs', 'flatfilepro-activity.mjs', 'image-evidence.mjs', 'flatfilepro-listings.mjs'])
                self.assertEqual(result['status'], 'processing')
                self.assertNotIn('evidence_skipped', result)
                complete.assert_called_once()
                self.assertEqual(complete.call_args.args[3], 'processing')

    def test_missing_or_invalid_full_read_history_forces_reads(self):
        directory, evidence, collected = self.image_poll_fixture()
        baseline = self.service.view(directory)
        for field, value in [('last_image_full_read_at', None), ('last_image_full_read_at', 'invalid'),
                             ('last_image_full_read_at', '2999-01-01T00:00:00Z'), ('evidence_path', '/missing'),
                             ('last_processing_collection', None), ('image_completion', None)]:
            with self.subTest(field=field, value=value):
                op.atomic_json(directory / 'journal.json', {**baseline, field: value})
                with patch.object(self.service, 'run_collector', side_effect=collected) as collector:
                    self.service.reconcile(self.execute)
                self.assertEqual(collector.call_count, 3)

    def test_invalid_full_verify_bound_is_rejected_before_collectors(self):
        directory, evidence, collected = self.image_poll_fixture()
        for value in (-1, True, '60', None, float('inf'), float('nan')):
            with self.subTest(value=value), patch.object(self.service, 'run_collector') as collector:
                with self.assertRaisesRegex(op.OperationError, 'finite nonnegative number'):
                    self.service.reconcile({**self.execute, 'full_verify_seconds': value})
                collector.assert_not_called()

    def test_complete_and_partial_pdp_observations_survive_busy_read_without_refresh(self):
        directory, state, evidence = self.completion_fixture()
        original_time = evidence['images'][0]['observed_at']
        image = self.plan['body']['images'][0]
        prior_images = [{key: item[key] for key in ('sku', 'slot', 'asin', 'observed_at', 'live_url', 'source_id')}
                        for item in evidence['images']]
        prior_images += [{**item, 'live_url': 'https://m.media-amazon.com/images/I/protected.jpg'}
                         for item in evidence['protected_images']]
        busy = {'status': 'blocked', 'message': 'BROWSER_SESSION_BUSY: another task holds session'}
        evidence_module = op.evidence_tools()
        for prior_status in ('collected', 'partial'):
            with self.subTest(prior_status=prior_status):
                previous = {'status': prior_status, 'operation_id': self.plan['operation_id'],
                            'account': self.account, 'plan_hash': state['plan_hash'],
                            'observed_at': original_time, 'images': copy.deepcopy(prior_images),
                            'observations': [{'asin': 'B000000001', 'complete': True, 'observed_at': original_time}]}
                state['last_collection'] = copy.deepcopy(previous)
                later = (op.timestamp(original_time) + op.dt.timedelta(seconds=901)).isoformat()
                with patch.object(op, 'now', return_value=later), \
                     patch.object(self.service, 'run_collector', side_effect=[{'status': 'blocked'}, busy]), \
                     patch.object(self.service, 'collect_image_catalog', return_value=None), \
                     patch.object(op, 'evidence_tools', return_value=evidence_module), \
                     patch.object(evidence_module, 'fetch_public_image', return_value=Path(image['path']).read_bytes()):
                    result = self.service.collect_images(directory, state, self.plan)
                    completion = self.service.image_completion(directory, state, self.plan, result)
                self.assertEqual(state['last_collection'], previous)
                self.assertEqual(state['last_collection_error'], busy)
                self.assertEqual(result['pdp_collection_error'], busy)
                self.assertEqual(result['pdp_collection'], previous)
                self.assertEqual(result['images'][0]['observed_at'], original_time)
                self.assertTrue(result['images'][0]['visually_verified'])
                self.assertEqual(result['protected_images'][0]['observed_at'], prior_images[1]['observed_at'])
                self.assertFalse(completion['release_eligible'])
                self.assertNotEqual(completion['publication'], 'verified')

    def test_blocked_pdp_read_does_not_reuse_another_plan_observations(self):
        directory, state, evidence = self.completion_fixture()
        state['last_collection'] = {'status': 'collected', 'operation_id': self.plan['operation_id'],
            'account': self.account, 'plan_hash': 'other', 'images': evidence['images']}
        busy = {'status': 'blocked', 'message': 'BROWSER_SESSION_BUSY'}
        with patch.object(self.service, 'run_collector', side_effect=[{'status': 'blocked'}, busy]), \
             patch.object(self.service, 'collect_image_catalog', return_value=None):
            result = self.service.collect_images(directory, state, self.plan)
        self.assertEqual(result['images'], [])
        self.assertEqual(state['last_collection'], busy)
        self.assertNotIn('pdp_collection_error', result)

    def test_protected_image_review_requires_exact_collected_baseline_and_rendition(self):
        from PIL import Image
        directory, state, evidence = self.completion_fixture()
        protected = evidence['protected_images'][0]
        protected['source_id'] = 'https://www.amazon.com/dp/B000000001'
        jpeg = self.root / 'preserved-main.jpg'
        Image.open(protected['expected_path']).save(jpeg, quality=80)
        archived = directory / 'observed-images' / op.file_hash(jpeg)
        archived.write_bytes(jpeg.read_bytes())
        protected.update(observed_path=str(archived), observed_sha256=op.file_hash(archived))
        self.assertEqual(self.service.image_completion(directory, state, self.plan, evidence)['preservation'], 'conflict')
        proof_hash = op.digest(evidence)
        op.atomic_json(directory / f'evidence-{proof_hash}.json', evidence)
        review = {'purpose': 'preservation', 'sku': protected['sku'], 'slot': protected['slot'],
            'asin': protected['asin'], 'source_sha256': protected['expected_sha256'],
            'observed_path': str(archived), 'observed_sha256': protected['observed_sha256'],
            'source_id': protected['source_id'], 'decision': 'match'}
        request = {**self.execute, 'review_evidence_digest': proof_hash, 'reviews': [review], 'reviewed_at': op.now(),
            'reviewer': {'kind': 'attended_agent', 'id': 'test-agent', 'context': 'test-protected-review'}}
        for mutate in (lambda r: r.pop('review_evidence_digest'),
                       lambda r: r['reviews'][0].update(source_sha256='f' * 64),
                       lambda r: r['reviews'][0].update(slot='PT01'),
                       lambda r: r['reviews'][0].update(observed_sha256='e' * 64)):
            invalid = copy.deepcopy(request)
            mutate(invalid)
            with self.assertRaises(op.OperationError):
                self.service.record_image_review(invalid)
        receipt = self.service.record_image_review(request)
        self.assertEqual(receipt['pairs'][0]['purpose'], 'preservation')
        self.assertEqual(receipt['pairs'][0]['baseline_url'], protected['expected_url'])
        self.assertEqual(receipt['pairs'][0]['baseline_evidence_digest'], proof_hash)
        self.assertEqual(self.service.record_image_review(request), receipt)
        self.assertTrue(self.service.image_completion(directory, state, self.plan, evidence)['release_eligible'])
        # Future collections may reuse only the identical before/after bytes.
        changed = Image.open(archived)
        changed.putpixel((1, 1), (0, 0, 255))
        changed.save(archived, format='PNG')
        protected['observed_sha256'] = op.file_hash(archived)
        self.assertEqual(self.service.image_completion(directory, state, self.plan, evidence)['preservation'], 'conflict')

    def test_protected_receipt_does_not_approve_submitted_image(self):
        from PIL import Image
        directory, state, evidence = self.completion_fixture()
        source = self.plan['body']['images'][0]
        jpeg = self.root / 'alternate.jpg'
        Image.open(source['path']).save(jpeg, quality=80)
        protected_source = {**source, 'purpose': 'preservation', 'baseline_url': self.rows['a'][MAIN], 'baseline_evidence_digest': 'd' * 64}
        review = {'purpose': 'preservation', 'sku': 'a', 'slot': 'PT01', 'asin': 'B000000001',
            'source_sha256': source['sha256'], 'observed_path': str(jpeg), 'observed_sha256': op.file_hash(jpeg),
            'source_id': 'https://www.amazon.com/dp/B000000001', 'decision': 'match'}
        module = op.evidence_tools()
        receipt = module.build_image_review(self.plan, [review], {'kind': 'attended_agent', 'id': 'test', 'context': 'test'}, op.now(),
                                           protected_sources={('a', 'PT01'): protected_source})
        checked = module.verify_public_rendition(self.plan, source, Path(source['path']).read_bytes(), jpeg.read_bytes(), [receipt])
        self.assertIsNone(checked['content_match'])

    def test_historical_release_revalidates_pinned_proof_without_extending_initial_freshness(self):
        directory, state, evidence = self.completion_fixture()
        evidence['observed_at'] = op.now()
        self.service.reconcile({**self.execute, 'evidence': evidence})
        pinned = {**self.execute, 'proof_digest': op.digest(evidence)}
        future = (op.timestamp(op.now()) + op.dt.timedelta(minutes=30)).isoformat()
        with patch.object(op, 'now', return_value=future):
            self.assertFalse(self.service.image_release_proof(self.execute)['release_eligible'])
            self.assertTrue(self.service.image_release_proof(pinned)['release_eligible'])
        archive = Path(evidence['images'][0]['observed_path'])
        archive.write_bytes(b'changed')
        self.assertFalse(self.service.image_release_proof(pinned)['release_eligible'])

    def test_mixed_rejected_and_processing_stays_partial_until_every_contribution_resolves(self):
        second = copy.deepcopy(self.request['inputs']['images'][0])
        second.update(slot='PT02', url='https://example.com/new2.png')
        self.request['inputs']['images'].append(second)
        self.request['inputs']['image_fields']['PT02'] = PT2
        directory, state, evidence = self.completion_fixture()
        evidence['ffp_processing']['attributes'].append(
            {'sku': 'a', 'field': PT2, 'status': 'rejected', 'submitted_value': 'https://example.com/new2.png'})
        request = {**self.execute, 'evidence': evidence}
        with patch.object(self.service, 'execute', side_effect=AssertionError('Reconciliation must not submit')):
            for _ in range(2):
                result = self.service.reconcile(request)
                self.assertEqual(result['status'], 'partial')
                self.assertEqual(result['image_completion']['processing'], 'failed')
                self.assertEqual(result['image_completion']['processing_pending'], ['a/' + PT1])
                self.assertEqual(result['failures'], ['a/PT02: rejected'])
                self.assertFalse(result['image_completion']['release_eligible'])
            evidence['ffp_processing']['attributes'][0]['status'] = 'reflected'
            result = self.service.reconcile(request)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['image_completion']['processing_pending'], [])


    def test_reporting_keeps_last_verified_when_next_read_is_busy_and_stale(self):
        directory, state, evidence = self.completion_fixture()
        first = self.service.reconcile({**self.execute, 'evidence': evidence})
        fact = copy.deepcopy(first['image_observations']['publication']['last_successful'])
        later = (op.timestamp(evidence['observed_at']) + op.dt.timedelta(seconds=901)).isoformat()
        blocked = copy.deepcopy(evidence)
        blocked.update(observed_at=later, pdp_collection_error={'status': 'blocked', 'message': 'BROWSER_SESSION_BUSY'})
        blocked['ffp_processing'] = {'status': 'blocked', 'message': 'BROWSER_SESSION_BUSY'}
        blocked.pop('preservation_source')
        with patch.object(op, 'now', return_value=later):
            result = self.service.reconcile({**self.execute, 'evidence': blocked})
            self.assertFalse(self.service.image_release_proof(self.execute)['release_eligible'])
        self.assertEqual(result['image_observations']['publication']['last_successful'], fact)
        self.assertEqual(result['image_collection_attempt']['outcome'], 'deferred')
        self.assertEqual(result['image_completion']['publication'], 'pending')

    def test_reporting_fresh_mismatch_and_rejection_replace_historical_success(self):
        from PIL import Image
        directory, state, evidence = self.completion_fixture()
        self.service.reconcile({**self.execute, 'evidence': evidence})
        mismatch = copy.deepcopy(evidence)
        path = directory / 'observed-images' / 'different.png'
        Image.new('RGB', (800, 800), 'blue').save(path)
        mismatch['images'][0].update(observed_path=str(path), observed_sha256=op.file_hash(path))
        mismatch['ffp_processing']['attributes'][0]['status'] = 'rejected'
        result = self.service.reconcile({**self.execute, 'evidence': mismatch})
        self.assertEqual(result['image_observations']['publication']['last_successful']['value'], 'pending')
        self.assertEqual(result['image_observations']['processing']['last_successful']['value'], 'failed')
        self.assertFalse(result['verified'])

    def test_reporting_invalid_provenance_cannot_erase_verified_fact(self):
        directory, state, evidence = self.completion_fixture()
        first = self.service.reconcile({**self.execute, 'evidence': evidence})
        fact = copy.deepcopy(first['image_observations']['publication']['last_successful'])
        evidence['images'][0].pop('source_id')
        result = self.service.reconcile({**self.execute, 'evidence': evidence})
        self.assertEqual(result['image_observations']['publication']['last_successful'], fact)
        self.assertFalse(result['image_completion']['release_eligible'])

    def test_reporting_rebuild_is_local_scoped_and_idempotent(self):
        directory, state, evidence = self.completion_fixture()
        self.service.reconcile({**self.execute, 'evidence': evidence})
        state = self.service.view(directory)
        state.pop('image_observations')
        op.atomic_json(directory / 'journal.json', state)
        wrong = copy.deepcopy(evidence)
        wrong.update(plan_hash='other-plan', observed_at=(op.timestamp(op.now()) + op.dt.timedelta(days=1)).isoformat())
        op.atomic_json(directory / f'evidence-{op.digest(wrong)}.json', wrong)
        op.atomic_json(directory / f'evidence-{op.digest(42)}.json', 42)
        nullable = copy.deepcopy(evidence)
        nullable.update(observed_at=op.now(), ffp_processing=None, images=[], protected_images=[], preservation_source=None)
        op.atomic_json(directory / f'evidence-{op.digest(nullable)}.json', nullable)
        with patch.object(self.service, 'run_collector', side_effect=AssertionError('No live reads')):
            first = self.service.refresh_image_observations(self.execute, persist=True)
            second = self.service.refresh_image_observations(self.execute, persist=True)
        self.assertEqual(first['image_observations'], second['image_observations'])
        self.assertEqual(first['image_observations']['publication']['last_successful']['value'], 'verified')
        self.assertEqual(first['image_observations']['publication']['last_successful']['observed_at'], evidence['images'][0]['observed_at'])
        self.assertEqual(first['submission_id'], 'run-1')

    def test_retry_after_busy_collection_does_not_skip_pdp_read(self):
        directory, evidence, collected = self.image_poll_fixture(published=True)
        state = self.service.view(directory)
        state['image_collection_attempt'] = {'outcome': 'deferred'}
        op.atomic_json(directory / 'journal.json', state)
        clock = (op.timestamp(state['last_image_full_read_at']) + op.dt.timedelta(seconds=300)).isoformat()
        with patch.object(op, 'now', return_value=clock), patch.object(self.service, 'run_collector', side_effect=collected) as collector, patch.object(op.evidence_tools(), 'fetch_public_image', return_value=Path(self.plan['body']['images'][0]['path']).read_bytes()):
            result = self.service.reconcile(self.execute)
        self.assertIn('image-evidence.mjs', [call.args[1] for call in collector.call_args_list])
        self.assertNotIn('evidence_skipped', result)


if __name__ == '__main__':
    unittest.main()
