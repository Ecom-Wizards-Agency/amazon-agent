"""Offline subprocess contracts for the public delivery entrypoints."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import forward


HELPER = '''import argparse, hashlib, json, os
from pathlib import Path
import sys
p = argparse.ArgumentParser()
p.add_argument('file', type=Path)
p.add_argument('destination')
p.add_argument('--name')
p.add_argument('--receipt-file', type=Path)
p.add_argument('--dry-run', action='store_true')
p.add_argument('--keep-local', action='store_true')
p.add_argument('--keep-upload', '--keep-docx', action='store_true')
a = p.parse_args()
Path(os.environ['CALLS']).write_text(json.dumps(sys.argv[1:]))
print('helper stdout')
print('helper stderr', file=sys.stderr)
mode = os.environ.get('SCENARIO', '')
if a.dry_run or mode == 'missing':
    sys.exit(0)
receipt = dict(provider='google-drive', verified=True, verified_at='2026-09-07T00:00:00Z',
               parents=['example-folder'], remote_id='example-file',
               mime_type='application/vnd.google-apps.spreadsheet',
               local_sha256=hashlib.sha256(a.file.read_bytes()).hexdigest())
if mode == 'unverified': receipt['verified'] = False
if mode == 'wrong_hash': receipt['local_sha256'] = '0' * 64
if mode == 'wrong_mime': receipt['mime_type'] = 'application/vnd.google-apps.document'
if mode == 'wrong_provider': receipt['provider'] = 'other'
if mode == 'missing_parents': receipt['parents'] = []
if mode == 'changed_source': a.file.write_bytes(b'changed during delivery')
if a.receipt_file:
    a.receipt_file.parent.mkdir(parents=True, exist_ok=True)
    a.receipt_file.write_text('invalid JSON' if mode == 'malformed' else json.dumps(receipt))
sys.exit(7 if mode == 'failed' else 0)
'''

REGISTRAR = '''import json, os, sys
from pathlib import Path
Path(os.environ['REGISTRATION']).write_text(json.dumps(sys.argv[1:]))
print('registrar stdout')
print('registrar stderr', file=sys.stderr)
sys.exit(int(os.environ.get('REGISTRATION_EXIT', '0')))
'''


class ForwardContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.wrapper = self.root / 'checkout' / 'tools' / 'gdrive-deliver'
        self.wrapper.mkdir(parents=True)
        for name in ('forward.py', 'deliver.py', 'update_sheet.py'):
            shutil.copyfile(Path(__file__).with_name(name), self.wrapper / name)
        artifact = self.wrapper.parent / 'artifactctl' / 'artifactctl.py'
        artifact.parent.mkdir()
        artifact.write_text(REGISTRAR)
        self.company = self.root / 'company-lib' / 'gdrive-deliver'
        self.company.mkdir(parents=True)
        for name in ('deliver.py', 'update_sheet.py'):
            (self.company / name).write_text(HELPER)
        self.source = self.root / 'input with spaces.xlsx'
        self.source.write_bytes(b'offline workbook bytes')
        self.receipt = self.root / 'receipts' / 'requested.json'
        self.calls = self.root / 'helper-call.json'
        self.registered = self.root / 'registration.json'
        self.env = dict(os.environ, EW_COMPANY_LIB=str(self.company.parent), HOME=str(self.root),
                        CALLS=str(self.calls), REGISTRATION=str(self.registered))

    def run_wrapper(self, name='deliver.py', extra=(), scenario='', register=True, env=None):
        args = [str(self.source), 'example-destination', *extra]
        if register:
            args += ['--artifact-run', 'example-run']
        return subprocess.run([sys.executable, str(self.wrapper / name), *args],
                              env=dict(self.env, SCENARIO=scenario, **(env or {})),
                              text=True, capture_output=True, check=False)

    def test_both_entrypoints_register_fresh_receipts_and_preserve_options(self):
        for name in ('deliver.py', 'update_sheet.py'):
            with self.subTest(name=name):
                extra = ['--receipt-file', str(self.receipt)]
                if name == 'deliver.py':
                    extra += ['--name', 'Example title', '--keep-local', '--keep-docx']
                result = self.run_wrapper(name, extra)
                self.assertEqual(result.returncode, 0, result.stderr)
                call = json.loads(self.calls.read_text())
                self.assertNotIn('--artifact-run', call)
                self.assertNotEqual(call[call.index('--receipt-file') + 1], str(self.receipt))
                registered = json.loads(self.registered.read_text())
                self.assertEqual(registered[:3], ['register', '--run', 'example-run'])
                self.assertEqual(registered[registered.index('--path') + 1], str(self.source))
                receipt = json.loads(registered[registered.index('--receipt') + 1])
                self.assertEqual(receipt, json.loads(self.receipt.read_text()))
                self.assertEqual(receipt['local_sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())
                self.assertIn('helper stdout', result.stdout)
                self.assertIn('helper stderr', result.stderr)
                self.assertIn('registrar stdout', result.stdout)
                self.assertTrue(self.source.is_file())

    def test_equals_options_are_consumed(self):
        result = self.run_wrapper(extra=['--artifact-run=equal-run', f'--receipt-file={self.receipt}'], register=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.registered.read_text())[2], 'equal-run')
        self.assertTrue(self.receipt.is_file())

    def test_register_without_requested_receipt(self):
        result = self.run_wrapper()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.registered.is_file())
        self.assertFalse(self.receipt.exists())

    def test_no_registration_request_passes_arguments_through(self):
        result = self.run_wrapper(extra=['--receipt-file', str(self.receipt), '--name', 'Example title'], register=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.calls.read_text()),
                         [str(self.source), 'example-destination', '--receipt-file', str(self.receipt), '--name', 'Example title'])
        self.assertFalse(self.registered.exists())

    def test_dry_run_leaves_existing_receipt_untouched(self):
        self.receipt.parent.mkdir()
        self.receipt.write_text('old receipt')
        result = self.run_wrapper('update_sheet.py', ['--dry-run', '--receipt-file', str(self.receipt)])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.registered.exists())
        self.assertEqual(self.receipt.read_text(), 'old receipt')

    def test_failed_helper_preserves_exit_output_and_new_receipt_without_registration(self):
        result = self.run_wrapper(extra=['--receipt-file', str(self.receipt)], scenario='failed')
        self.assertEqual(result.returncode, 7)
        self.assertIn('helper stderr', result.stderr)
        self.assertTrue(self.receipt.exists())
        self.assertFalse(self.registered.exists())

    def test_stale_caller_receipt_never_counts_as_new_delivery(self):
        self.receipt.parent.mkdir()
        self.receipt.write_text(json.dumps({'verified': True}))
        result = self.run_wrapper(extra=['--receipt-file', str(self.receipt)], scenario='missing')
        self.assertEqual(result.returncode, 2)
        self.assertIn('no new valid receipt', result.stderr)
        self.assertFalse(self.registered.exists())
        self.assertEqual(json.loads(self.receipt.read_text()), {'verified': True})

    def test_invalid_receipts_cannot_register(self):
        for mode in ('missing', 'malformed', 'unverified', 'wrong_hash', 'wrong_mime',
                     'wrong_provider', 'missing_parents', 'changed_source'):
            with self.subTest(mode=mode):
                result = self.run_wrapper(scenario=mode)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertFalse(self.registered.exists())

    def test_registration_failure_preserves_receipt_file_and_source(self):
        result = self.run_wrapper(extra=['--receipt-file', str(self.receipt)], env={'REGISTRATION_EXIT': '9'})
        self.assertEqual(result.returncode, 9)
        self.assertIn('artifact registration failed', result.stderr)
        self.assertIn('registrar stderr', result.stderr)
        self.assertTrue(self.receipt.exists())
        self.assertTrue(self.source.exists())

    def test_receipt_must_not_overwrite_source(self):
        result = self.run_wrapper(extra=['--receipt-file', str(self.source)])
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.calls.exists())
        self.assertEqual(self.source.read_bytes(), b'offline workbook bytes')

    def test_missing_upstream_update_helper_has_clear_failure(self):
        (self.company / 'update_sheet.py').unlink()
        result = self.run_wrapper('update_sheet.py')
        self.assertEqual(result.returncode, 2)
        self.assertIn('update_sheet.py is missing', result.stderr)
        self.assertIn('Update or clone company-ai-skills', result.stderr)
        self.assertFalse(self.registered.exists())

    def test_help_does_not_deliver_or_register(self):
        result = self.run_wrapper(extra=['--help'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.calls.exists())
        self.assertFalse(self.registered.exists())

    def test_missing_or_empty_run_id_fails_before_delivery(self):
        for extra in (['--artifact-run'], ['--artifact-run=']):
            with self.subTest(extra=extra):
                result = self.run_wrapper(extra=extra, register=False)
                self.assertEqual(result.returncode, 2)
                self.assertFalse(self.calls.exists())


class CompanyReceiptContract(unittest.TestCase):
    def test_real_company_receipts_satisfy_wrapper_and_artifact_registry(self):
        library = Path(os.environ.get('EW_COMPANY_LIB',
                       str(Path.home() / 'os' / 'company-ai-skills' / 'lib'))).expanduser()
        if not all((library / 'gdrive-deliver' / name).is_file()
                   for name in ('deliver.py', 'update_sheet.py')):
            self.skipTest('set EW_COMPANY_LIB to the release company library for this cross-repo gate')

        def load(name, path):
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module

        delivery = load('company_delivery_contract', library / 'gdrive-deliver' / 'deliver.py')
        sheets = load('company_sheets_contract', library / 'gdrive-deliver' / 'update_sheet.py')
        artifact = load('artifact_receipt_contract',
                        Path(__file__).resolve().parents[1] / 'artifactctl' / 'artifactctl.py')
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / 'example.xlsx'
            source.write_bytes(b'offline receipt contract')
            checksum = forward.sha256(source)
            meta = dict(id='example-file', name='Example', parents=['example-folder'],
                        mimeType='application/vnd.google-apps.spreadsheet',
                        webViewLink='https://docs.google.com/spreadsheets/d/example-file')
            receipts = [delivery.drive_receipt(source, meta),
                        sheets.build_receipt(source, dict(id=meta['id'], title=meta['name'],
                                             url=meta['webViewLink']), [], [], True, meta['parents'])]
            receipt_path = Path(scratch) / 'receipt.json'
            for receipt in receipts:
                with self.subTest(kind=receipt.get('kind', 'delivery')):
                    receipt_path.write_text(json.dumps(receipt))
                    self.assertEqual(forward.verified_receipt(receipt_path, source, checksum), receipt)
                    self.assertTrue(artifact.ArtifactRegistry._drive_receipt_valid(
                        {'receipt_json': json.dumps(receipt), 'sha256': checksum}))
                    receipt['verified'] = False
                    receipt_path.write_text(json.dumps(receipt))
                    with self.assertRaises(ValueError):
                        forward.verified_receipt(receipt_path, source, checksum)
                    self.assertFalse(artifact.ArtifactRegistry._drive_receipt_valid(
                        {'receipt_json': json.dumps(receipt), 'sha256': checksum}))


if __name__ == '__main__':
    unittest.main()
