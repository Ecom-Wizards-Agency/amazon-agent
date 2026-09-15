import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch


spec = importlib.util.spec_from_file_location('task_completion_operations', Path(__file__).resolve().parents[1] / 'operations.py')
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)


class TaskCompletionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.service = op.Operations(Path(temporary.name) / 'state')
        self.account = {'client_slug': 'brand', 'profile_key': 'brand-us', 'marketplace': 'US'}
        resolver = patch.object(op, 'session_environment', return_value={'CDP_PORT': '9223'})
        resolver.start()
        self.addCleanup(resolver.stop)

    def fixture(self, operation='seo.update', body=None, status='processing', key='rollout-1'):
        directory = self.service.directory('revision-1')
        plan = {'operation_id': 'revision-1', 'operation': operation, 'account': self.account,
                'prepared_at': op.now(), 'artifacts': [],
                'body': body or {'expected_rows': {'sku': {'generic_keyword.0.value': 'new'}}}}
        state = {'plan_hash': op.digest(plan), 'submission_id': 'submission', 'task_key': key}
        op.atomic_json(directory / 'plan.json', plan)
        self.service.persist(directory, state, status)
        request = {'schema_version': 1, 'operation_id': plan['operation_id'],
                   'plan_hash': state['plan_hash'], 'complete_task': True}
        evidence = {'account': self.account, 'plan_hash': state['plan_hash'], 'source_id': 'live',
                    'observed_at': op.now(), 'submission_id': 'submission', 'processing_status': 'complete'}
        return directory, state, plan, request, evidence

    def test_hash_matches_node_for_stable_key_and_operation_fallback(self):
        keys = ['bulk-images:rollout', 'rollout-\u00e4-\U0001f680', '', None]
        stable_keys = [key or 'revision-1' for key in keys]
        script = "import {taskIdFor} from './tools/browserctl/task-tabs.mjs'; console.log(JSON.stringify(JSON.parse(process.argv[1]).map(key=>taskIdFor('amazon-operations',key))));"
        result = subprocess.run(['node', '--input-type=module', '-e', script, json.dumps(stable_keys)],
                                cwd=op.ROOT, capture_output=True, text=True, check=True)
        expected = json.loads(result.stdout)
        for key, task_id in zip(keys, expected):
            for port in ['9222', '9223']:
                with self.subTest(key=key, port=port), patch.object(op, 'session_environment', return_value={'CDP_PORT': port}), patch.object(op.subprocess, 'run') as runner:
                    self.service._complete_reconciled_task({'complete_task': True}, {'task_key': key}, {'operation_id': 'revision-1'}, 'verified')
                    runner.assert_called_once()
                    self.assertEqual(runner.call_args.args[0], ['node', str(op.ROOT / 'tools/browserctl/browserctl.mjs'),
                                     'task', 'complete', '--port', port, '--task-id', task_id])
                    self.assertTrue(runner.call_args.kwargs['check'])
                    self.assertEqual(runner.call_args.kwargs['env']['CDP_PORT'], port)

    def test_only_boolean_true_and_terminal_statuses_complete(self):
        for flag in [None, False, 'true', 1, True]:
            for status in ['processing', 'partial', 'uncertain', 'verified', 'failed', 'blocked', 'stalled']:
                with self.subTest(flag=flag, status=status), patch.object(op.subprocess, 'run') as runner:
                    self.service._complete_reconciled_task({'complete_task': flag}, {}, {'operation_id': 'revision-1'}, status)
                    self.assertEqual(runner.call_count, int(flag is True and status in {'verified', 'failed', 'blocked', 'stalled'}))

    def test_completion_failures_are_logged_before_terminal_persist(self):
        for error in [OSError('node unavailable'), subprocess.TimeoutExpired('node', 30), subprocess.CalledProcessError(1, 'node')]:
            with self.subTest(error=type(error).__name__):
                directory, state, plan, request, evidence = self.fixture()
                request['evidence'] = {**evidence, 'processing_status': 'failed'}
                def fail(*args, **kwargs):
                    self.assertEqual(self.service.view(directory)['status'], 'processing')
                    raise error
                with patch.object(op.subprocess, 'run', side_effect=fail) as runner, patch.object(op.sys, 'stderr', new_callable=io.StringIO) as logged:
                    self.assertEqual(self.service.reconcile(request)['status'], 'failed')
                    runner.assert_called_once()
                    self.assertIn('Browser task completion failed:', logged.getvalue())
                self.assertEqual(self.service.view(directory)['status'], 'failed')

    def test_session_resolution_failure_is_logged(self):
        with patch.object(op, 'session_environment', side_effect=RuntimeError('Session conflict')), patch.object(op.subprocess, 'run') as runner, patch.object(op.sys, 'stderr', new_callable=io.StringIO) as logged:
            self.service._complete_reconciled_task({'complete_task': True}, {}, {'operation_id': 'revision-1'}, 'verified')
            runner.assert_not_called()
            self.assertIn('Browser task completion failed: Session conflict', logged.getvalue())

    def test_seo_and_catalog_collect_without_completion_until_terminal_persist(self):
        catalog = {'stages': [{'full_update_values': {'sku': {'title': 'New'}}}],
                   'manifest': {'operation': 'delete_parent', 'family': {'parent': {'sku': 'parent'}}},
                   'protected_children': []}
        for operation, body in [('seo.update', None), ('catalog.change', catalog)]:
            with self.subTest(operation=operation):
                directory, state, plan, request, evidence = self.fixture(operation, body)
                rows = plan['body'].get('expected_rows', {'sku': {'title': 'New'}})
                exported = {'rows': rows, 'source_id': 'fresh-report'}
                catalog_evidence = {'stage': 1, 'catalog_rows': rows, 'deleted_parents': ['parent']}
                evidence_tools = op.evidence_tools()
                evidence_tools.catalog_evidence = Mock(return_value=catalog_evidence)
                def completed(*args, **kwargs):
                    self.assertEqual(self.service.view(directory)['status'], 'processing')
                with patch.object(self.service, 'collect_export', side_effect=[None, exported]) as collector, patch.object(op, 'evidence_tools', return_value=evidence_tools), patch.object(op.subprocess, 'run', side_effect=completed) as runner:
                    self.assertEqual(self.service.reconcile(request)['status'], 'processing')
                    runner.assert_not_called()
                    self.assertEqual(self.service.reconcile(request)['status'], 'verified')
                    runner.assert_called_once()
                    for call in collector.call_args_list:
                        self.assertIs(call.kwargs['complete_task'], False)

    def test_provided_evidence_does_not_complete_while_processing_or_partial(self):
        directory, state, plan, request, evidence = self.fixture(body={'expected_rows': {'sku': {'generic_keyword.0.value': 'new', 'item_name.0.value': 'New'}}})
        with patch.object(op.subprocess, 'run') as runner:
            for processing, rows, expected in [('processing', {}, 'processing'), ('live_observed', {}, 'processing'), ('complete', {'sku': {'generic_keyword.0.value': 'new'}}, 'partial')]:
                self.assertEqual(self.service.reconcile({**request, 'evidence': {**evidence, 'processing_status': processing, 'rows': rows}})['status'], expected)
                runner.assert_not_called()
            self.assertEqual(self.service.reconcile({**request, 'evidence': {**evidence, 'rows': plan['body']['expected_rows']}})['status'], 'verified')
            runner.assert_called_once()

    def test_catalog_create_products_completes_at_its_terminal_return(self):
        body = {'stages': [{}], 'manifest': {'operation': 'create_products'}, 'protected_children': [],
                'products': [{'sku': 'sku', 'product_type': 'BOOK', 'title': 'New'}]}
        directory, state, plan, request, evidence = self.fixture('catalog.change', body)
        with patch.object(op.subprocess, 'run') as runner:
            result = self.service.reconcile({**request, 'evidence': {**evidence, 'stage': 1,
                'products': {'sku': {'asin': 'B000000001', 'product_type': 'BOOK', 'title': 'New'}}}})
            self.assertEqual(result['status'], 'verified')
            runner.assert_called_once()

    def test_no_change_image_verification_completes_at_final_persist(self):
        body = {'no_changes': True, 'images': [{'sku': 'sku', 'slot': 'PT01', 'sha256': 'approved'}]}
        directory, state, plan, request, evidence = self.fixture('listing.images', body)
        with patch.object(op.subprocess, 'run') as runner:
            self.assertEqual(self.service.reconcile({**request, 'evidence': {**evidence, 'processing_status': 'live_observed', 'images': []}})['status'], 'processing')
            runner.assert_not_called()
            result = self.service.reconcile({**request, 'evidence': {**evidence, 'images': [
                {'sku': 'sku', 'slot': 'PT01', 'source_sha256': 'approved', 'visually_verified': True, 'live_url': 'https://example.com/image'}]}})
            self.assertEqual(result['status'], 'verified')
            runner.assert_called_once()

    def test_catalog_intermediate_stage_does_not_complete(self):
        body = {'stages': [{}, {}], 'manifest': {'operation': 'replace_parent', 'family': {'parent': {'sku': 'parent'}}}, 'protected_children': []}
        directory, state, plan, request, evidence = self.fixture('catalog.change', body)
        with patch.object(op.subprocess, 'run') as runner:
            result = self.service.reconcile({**request, 'evidence': {**evidence, 'stage': 1, 'deleted_parents': ['parent']}})
            self.assertEqual(result['status'], 'partial')
            self.assertEqual(result['next_stage'], 2)
            runner.assert_not_called()

    def test_blocked_without_evidence_completes_once(self):
        directory, state, plan, request, evidence = self.fixture(status='blocked')
        with patch.object(self.service, 'collect', return_value=None) as collector, patch.object(op.subprocess, 'run') as runner:
            self.assertEqual(self.service.reconcile(request)['status'], 'blocked')
            self.assertIs(collector.call_args.kwargs['complete_task'], False)
            runner.assert_called_once()

    def test_stalled_finalize_preserves_evidence_completes_once_and_resumes_explicitly(self):
        directory, state, plan, request, evidence = self.fixture()
        evidence_path = directory / 'last-evidence.json'
        op.atomic_json(evidence_path, evidence)
        retained = {'evidence_path': str(evidence_path), 'last_collection': {'observed_at': op.now()},
                    'last_processing_collection': {'pending': 2}, 'image_completion': {'matched': []}}
        self.service.persist(directory, state, 'processing', **retained)
        original = evidence_path.read_bytes()
        def completed(*args, **kwargs):
            self.assertEqual(self.service.view(directory)['status'], 'stalled')
        with patch.object(self.service, 'collect') as collect, patch.object(self.service, 'collect_images') as images, patch.object(op.subprocess, 'Popen') as reads, patch.object(op.subprocess, 'run', side_effect=completed) as complete:
            result = self.service.reconcile({**request, 'finalize': 'stalled', 'close_tabs': True, 'evidence': {'invalid': True}})
            self.assertEqual(result['status'], 'stalled')
            self.assertEqual(result['journal_note'], 'Finalized as stalled by request; last evidence retained.')
            self.assertEqual({key: result[key] for key in retained}, retained)
            self.assertEqual(self.service.view(directory), result)
            self.assertEqual(self.service.reconcile({**request, 'finalize': 'stalled'}), result)
            complete.assert_called_once()
            collect.assert_not_called()
            images.assert_not_called()
            reads.assert_not_called()
        self.assertEqual(evidence_path.read_bytes(), original)
        with patch.object(self.service, 'collect', return_value=None) as collect, patch.object(op.subprocess, 'run') as complete:
            resumed = self.service.reconcile({**request, 'complete_task': False})
            collect.assert_called_once()
            self.assertEqual(resumed['status'], 'processing')
            self.assertNotIn('stalled_from_status', resumed)
            complete.assert_not_called()

    def test_stalled_finalize_precedes_preflight_and_case_reads(self):
        for operation, phase in [('listing.images', 'image_preflight'), ('catalog.change', 'preflight'), ('case.create', None)]:
            with self.subTest(operation=operation):
                directory, state, plan, request, evidence = self.fixture(operation)
                self.service.persist(directory, state, 'processing', phase=phase, effects_started=False)
                with patch.object(self.service, 'collect_export') as export, patch.object(self.service, 'case_journal_boundary') as cases, patch.object(op.subprocess, 'run') as complete:
                    self.assertEqual(self.service.reconcile({**request, 'finalize': 'stalled'})['status'], 'stalled')
                    export.assert_not_called()
                    cases.assert_not_called()
                    complete.assert_called_once()

    def test_close_tabs_reaches_every_serialized_collector_envelope_and_does_not_leak(self):
        directory, state, plan, request, evidence = self.fixture()
        scripts = ['flatfilepro-activity.mjs', 'image-evidence.mjs', 'flatfilepro-listings.mjs',
                   'catalog-export.mjs', 'flatfilepro-export.mjs', 'flatfilepro-discovery.mjs',
                   'flatfilepro.mjs', 'cases.mjs']
        envelope = {'schema_version': 1, 'plan': plan, 'task_key': state['task_key'], 'complete_task': False}
        def collect(*args, **kwargs):
            for script in scripts:
                self.service.run_collector(directory, script, envelope)
            return None
        child = Mock(communicate=Mock(return_value=(json.dumps({'status': 'blocked'}), '')))
        for flag in [True, False, 'true', None]:
            with self.subTest(flag=flag), patch.object(self.service, 'collect', side_effect=collect), patch.object(op.subprocess, 'Popen', return_value=child) as process:
                self.service.reconcile({**request, 'close_tabs': flag, 'complete_task': False})
                self.assertEqual(process.call_count, len(scripts))
                for script in scripts:
                    saved = json.loads((directory / (script.removesuffix('.mjs') + '-input.json')).read_text())
                    self.assertEqual(saved, {**envelope, **({'close_tab_after': True} if flag is True else {})})
                    self.assertNotIn('close_tab_after', saved['plan'])
                self.assertNotIn('close_tab_after', envelope)
        with patch.object(self.service, '_reconcile', side_effect=RuntimeError('Interrupted')):
            with self.assertRaises(RuntimeError):
                self.service.reconcile({**request, 'close_tabs': True})
        with patch.object(op.subprocess, 'Popen', return_value=child):
            self.service.run_collector(directory, scripts[0], envelope)
        self.assertEqual(json.loads((directory / 'flatfilepro-activity-input.json').read_text()), envelope)


if __name__ == '__main__':
    unittest.main()
