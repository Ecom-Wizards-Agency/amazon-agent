"""Regression for identity changes between resolution and image submission."""
import copy
import json
import re
from pathlib import Path
from unittest.mock import Mock, patch
import test_image_safety as base


class AttendedIdentityPreflightTests(base.ImageSafetyTests):
    def test_periodic_full_read_checks_changed_identity_despite_unchanged_import(self):
        directory, evidence, collected = self.image_poll_fixture()
        with patch.object(self.service, 'run_collector', side_effect=collected) as collector:
            skipped = self.service.reconcile(self.execute)
        self.assertEqual(collector.call_count, 1)
        self.assertEqual(skipped['evidence_skipped'], 'activity-unchanged')
        evidence['protected_rows']['a']['asin'] = 'B000000002'
        with patch.object(self.service, 'run_collector', side_effect=collected) as collector:
            result = self.service.reconcile({**self.execute, 'full_verify_seconds': 0})
        self.assertEqual(collector.call_count, 3)
        self.assertNotIn('evidence_skipped', result)
        self.assertEqual(result['image_completion']['preservation'], 'conflict')
        self.assertFalse(result['image_completion']['release_eligible'])
        self.assertFalse(result['verified'])

    def test_exact_identity_is_frozen_and_changed_attributes_block_adapter(self):
        self.request['inputs']['image_catalog_source'] = 'flatfilepro_listing_read'
        self.rows['a'].update(itemName='Navy rain set', product_type='SNOWSUIT',
                             **{'model_number.0.value': '11010040', 'color.0.value': 'Navy',
                                'size.0.value': '86', 'part_number.0.value': ''})
        self.prepare()
        expected = self.plan['body']['image_identity_rows']['a']
        self.assertEqual(expected['model_number.0.value'], '11010040')
        for mutation in ('model_number.0.value', 'color.0.value', 'size.0.value', 'part_number.0.value',
                         'added_optional', 'removed_optional'):
            with self.subTest(mutation=mutation):
                fresh = {'rows': copy.deepcopy(self.rows), 'path': str(self.source),
                         'sha256': base.op.file_hash(self.source), 'observed_at': base.op.now()}
                if mutation == 'added_optional': fresh['rows']['a']['model_name.1.value'] = 'Wrong model'
                elif mutation == 'removed_optional': fresh['rows']['a'].pop('size.0.value')
                else: fresh['rows']['a'][mutation] = 'Changed'
                with patch.object(self.service, 'collect_image_catalog', return_value=fresh), patch.object(base.op.subprocess, 'run') as adapter:
                    if mutation == 'added_optional':
                        result = self.service.execute(self.execute)
                        self.assertEqual(result['reason'], 'identity_map_incomplete')
                        self.assertIn('a (missing fields: model_name.1.value)', result['message'])
                    else:
                        with self.assertRaisesRegex(base.op.OperationError, 'identity changed'):
                            self.service.execute(self.execute)
                    adapter.assert_not_called()

    def rewrite_identity_map(self, expected):
        if expected is None:
            self.plan['body'].pop('image_identity_rows')
        else:
            self.plan['body']['image_identity_rows'] = expected
        directory = Path(self.service.view(self.root / 'state/image-test')['plan_path']).parent
        base.op.atomic_json(directory / 'plan.json', self.plan)
        state = self.service.view(directory)
        state['plan_hash'] = base.op.digest(self.plan)
        self.service.persist(directory, state, 'prepared')
        self.execute['plan_hash'] = self.execute['grant']['plan_hash'] = state['plan_hash']

    def test_legacy_and_incomplete_maps_block_before_any_browser_work(self):
        self.request['inputs']['image_catalog_source'] = 'flatfilepro_listing_read'
        self.rows['a'].update(itemName='Navy rain set', product_type='SNOWSUIT')
        self.prepare()
        for expected in (None, {}, {'other': {'asin': 'B000000002'}}, {'a': {}}):
            with self.subTest(expected=expected):
                self.rewrite_identity_map(expected)
                before = copy.deepcopy(self.plan)
                with patch.object(self.service, 'collect_image_catalog') as catalog, \
                     patch.object(self.service, 'collect_export') as export, \
                     patch.object(self.service, 'run_collector') as collector, \
                     patch.object(base.op.subprocess, 'run') as adapter:
                    result = self.service.execute(self.execute)
                self.assertEqual(result['status'], 'blocked')
                self.assertEqual(result['reason'], 'identity_map_incomplete')
                self.assertFalse(result['effects_started'])
                self.assertIn('IDENTITY_MAP_INCOMPLETE:', result['message'])
                self.assertIn('SKUs: a', result['message'])
                self.assertIn('re-prepare the plan', result['message'])
                if expected is None:
                    self.assertIn('Plan predates identity capture', result['message'])
                    self.service.prepare(self.request)
                for mocked in (catalog, export, collector, adapter):
                    mocked.assert_not_called()
                self.assertEqual(json.loads(Path(result['plan_path']).read_text()), before)
                self.assertFalse((Path(result['plan_path']).parent / 'adapter-input.json').exists())

    def test_legacy_map_missing_canonical_key_blocks_before_any_collector(self):
        self.rows['a'].update(**{'model_number.0.value': '11010040', 'color.0.value': 'Navy',
                                'size.0.value': '86', 'part_number.0.value': ''})
        self.prepare()
        complete = copy.deepcopy(self.plan['body']['image_identity_rows'])
        for field in ('model_number.0.value', 'color.0.value', 'size.0.value', 'part_number.0.value'):
            with self.subTest(field=field):
                expected = copy.deepcopy(complete)
                expected['a'].pop(field)
                self.rewrite_identity_map(expected)
                with patch.object(self.service, 'collect_export', return_value=self.fresh()) as collector, \
                     patch.object(self.service, 'collect_image_catalog') as catalog, \
                     patch.object(self.service, 'run_collector') as dispatch, \
                     patch.object(base.op.subprocess, 'run') as adapter:
                    result = self.service.execute(self.execute)
                collector.assert_not_called()
                catalog.assert_not_called()
                dispatch.assert_not_called()
                adapter.assert_not_called()
                self.assertEqual(result['status'], 'blocked')
                self.assertEqual(result['reason'], 'identity_map_incomplete')
                self.assertIn(f'a (missing fields: {field})', result['message'])
                self.assertIn('re-prepare the plan', result['message'])
                self.assertFalse(result['effects_started'])

    def test_complete_attended_identity_reaches_adapter(self):
        self.request['inputs']['image_catalog_source'] = 'flatfilepro_listing_read'
        self.rows['a'].update(itemName='Navy rain set', product_type='SNOWSUIT',
                             **{'model_number.0.value': '11010040', 'color.0.value': 'Navy', 'size.0.value': '86'})
        self.prepare()
        fresh = {**self.fresh(), 'observed_at': base.op.now()}
        response = {'plan_hash': self.execute['plan_hash'], 'status': 'processing', 'attempted': True, 'submission_id': 'run-1'}
        with patch.object(self.service, 'collect_image_catalog', return_value=fresh) as collector, \
             patch.object(base.op.subprocess, 'run', return_value=Mock(stdout=json.dumps(response))) as adapter:
            result = self.service.execute(self.execute)
        collector.assert_called_once()
        adapter.assert_called_once()
        self.assertEqual(result['status'], 'processing')
        self.assertEqual(result['submission_id'], 'run-1')

    def test_canonical_identity_keys_match_javascript_source_byte_for_byte(self):
        root = Path(__file__).resolve().parents[1]
        python = (root / 'operations.py').read_text()
        javascript = (root / 'image-identity.mjs').read_text()
        literal = re.search(r'IMAGE_IDENTITY_KEYS = (\[[\s\S]*?\n\])', python)[1]
        self.assertEqual(literal, re.search(r'IMAGE_IDENTITY_KEYS=Object.freeze\((\[[\s\S]*?\n\])\)', javascript)[1])
        self.assertEqual(re.findall(r"'([^']+)'", literal), base.op.IMAGE_IDENTITY_KEYS)

    def test_prepare_captures_every_canonical_key_with_explicit_blanks(self):
        self.rows['a'].pop('color.0.value')
        self.rows['a']['model_number.1.value'] = 'Additional model'
        self.prepare()
        expected = self.plan['body']['image_identity_rows']['a']
        self.assertTrue(set(base.op.IMAGE_IDENTITY_KEYS) <= set(expected))
        self.assertEqual(expected['color.0.value'], '')
        self.assertEqual(expected['model_number.1.value'], 'Additional model')
        self.assertEqual(expected['asin'], self.rows['a']['asin'])

    def test_simultaneous_canonical_omission_from_map_and_fresh_row_blocks(self):
        self.prepare()
        self.plan['body']['image_identity_rows']['a'].pop('color.0.value')
        fresh = copy.deepcopy(self.rows)
        fresh['a'].pop('color.0.value')
        with self.assertRaisesRegex(base.op.OperationError, r'IDENTITY_MAP_INCOMPLETE:.*a \(missing fields: color\.0\.value\).*re-prepare the plan') as caught:
            self.service.validate_image_baseline(self.plan, fresh)
        self.assertEqual(caught.exception.code, 'identity_map_incomplete')

    def test_additional_captured_paths_and_blank_canonical_fields_cannot_disappear(self):
        self.rows['a']['color.1.value'] = 'Red'
        self.prepare()
        self.service.validate_image_baseline(self.plan, self.rows)
        for field in ('color.1.value', 'part_number.0.value'):
            with self.subTest(field=field):
                fresh = copy.deepcopy(self.rows)
                fresh['a'].pop(field)
                with self.assertRaisesRegex(base.op.OperationError, 'identity changed') as caught:
                    self.service.validate_image_baseline(self.plan, fresh)
                self.assertEqual(caught.exception.code, 'image_state_conflict')
        fresh = copy.deepcopy(self.rows)
        fresh['a']['color.1.value'] = 'Blue'
        with self.assertRaisesRegex(base.op.OperationError, 'identity changed'):
            self.service.validate_image_baseline(self.plan, fresh)
