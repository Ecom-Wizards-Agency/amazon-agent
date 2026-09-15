"""Regression for identity changes between resolution and image submission."""
import copy
from unittest.mock import patch
import test_image_safety as base


class AttendedIdentityPreflightTests(base.ImageSafetyTests):
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
                if mutation == 'added_optional': fresh['rows']['a']['model_name.0.value'] = 'Wrong model'
                elif mutation == 'removed_optional': fresh['rows']['a'].pop('size.0.value')
                else: fresh['rows']['a'][mutation] = 'Changed'
                with patch.object(self.service, 'collect_image_catalog', return_value=fresh), patch.object(base.op.subprocess, 'run') as adapter:
                    with self.assertRaisesRegex(base.op.OperationError, 'identity changed'):
                        self.service.execute(self.execute)
                    adapter.assert_not_called()
