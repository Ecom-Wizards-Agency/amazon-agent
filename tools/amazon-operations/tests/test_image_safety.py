import copy
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

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
        self.rows = {'a': {MAIN: 'https://example.com/main.png', PT1: 'https://example.com/old.png', PT2: 'https://example.com/keep.png', SWATCH: 'https://example.com/swatch.png', 'asin': 'B000000001', 'parentage_level.0.value': 'child', 'child_parent_sku_relationship.0.parent_sku': 'parent'}}
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

    def test_upload_contains_only_requested_secondaries_and_freezes_other_images(self):
        self.prepare()
        self.assertEqual(self.plan['body']['mapping'], [PT1])
        self.assertEqual(self.plan['body']['expected_rows'], {'a': {PT1: 'https://example.com/new.png'}})
        before = self.plan['body']['image_before_rows']['a']
        self.assertEqual(before[MAIN], self.rows['a'][MAIN])
        self.assertEqual(before[PT2], self.rows['a'][PT2])
        self.assertEqual(before[SWATCH], self.rows['a'][SWATCH])

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
        with self.assertRaisesRegex(op.OperationError, 'complete exact-run'):
            self.service.reconcile(request)
        evidence['ffp_processing'] = {'status': 'collected', 'complete': True, 'account': self.account,
            'plan_hash': self.execute['plan_hash'], 'submission_id': 'run-1', 'attributes': [
                {'sku': 'a', 'field': PT1, 'status': 'reflected'}, {'sku': 'a', 'field': PT2, 'status': 'rejected'}]}
        result = self.service.reconcile(request)
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(result['matched'], ['a/PT01'])
        self.assertEqual(result['pending'], [])
        self.assertEqual(result['failures'], ['a/PT02: rejected'])


if __name__ == '__main__':
    unittest.main()
