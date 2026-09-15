"""Collector process budgets and graceful termination, without browser processes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, call, patch

spec = importlib.util.spec_from_file_location('collector_operations', Path(__file__).resolve().parents[1] / 'operations.py')
op = importlib.util.module_from_spec(spec)
spec.loader.exec_module(op)


class CollectorTimeoutTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.service = op.Operations(self.directory / 'state')
        self.request = {'account': {'marketplace': 'US'}, 'plan_hash': 'hash', 'task_key': 'job', 'complete_task': True}
        self.session = patch.object(op, 'session_environment', return_value={'CDP_PORT': '9223'})
        self.session.start()
        self.addCleanup(self.session.stop)

    def run_child(self, process, **options):
        with patch.object(op.subprocess, 'Popen', return_value=process) as spawn:
            result = self.service.run_collector(self.directory, 'image-evidence.mjs', self.request, **options)
            self.assertEqual(spawn.call_args.kwargs['stdout'], subprocess.PIPE)
            self.assertEqual(spawn.call_args.kwargs['stderr'], subprocess.PIPE)
            saved = json.loads((self.directory / 'image-evidence-input.json').read_text())
            self.assertEqual(saved, self.request)
            return result

    def test_timeout_sends_sigterm_and_allows_fifteen_seconds_for_release(self):
        process = Mock()
        process.communicate.side_effect = [subprocess.TimeoutExpired('node', 180), ('late result', '')]
        self.assertEqual(self.run_child(process), {'status': 'blocked', 'reason': 'collector_result_unavailable'})
        self.assertEqual(process.mock_calls, [call.communicate(timeout=180), call.terminate(), call.communicate(timeout=15)])
        process.kill.assert_not_called()

    def test_unresponsive_child_is_killed_only_after_sigterm_grace(self):
        process = Mock()
        process.communicate.side_effect = [subprocess.TimeoutExpired('node', 180), subprocess.TimeoutExpired('node', 15), ('', '')]
        self.assertEqual(self.run_child(process), {'status': 'blocked', 'reason': 'collector_result_unavailable'})
        self.assertEqual(process.mock_calls, [call.communicate(timeout=180), call.terminate(), call.communicate(timeout=15), call.kill(), call.communicate()])

    def test_custom_budget_preserves_result_shape_and_does_not_accept_late_success(self):
        process = Mock()
        process.communicate.side_effect = [subprocess.TimeoutExpired('node', 3), (json.dumps({'status': 'collected', **self.request}), '')]
        self.assertEqual(self.run_child(process, timeout=3), {'status': 'blocked', 'reason': 'collector_result_unavailable'})
        self.assertEqual(process.mock_calls, [call.communicate(timeout=3), call.terminate(), call.communicate(timeout=15)])

    def test_normal_result_keeps_identity_check_and_never_signals(self):
        response = {'status': 'collected', **self.request}
        process = Mock(communicate=Mock(return_value=(json.dumps(response), '')))
        self.assertEqual(self.run_child(process), response)
        self.assertEqual(process.mock_calls, [call.communicate(timeout=180)])
        process.communicate.return_value = (json.dumps({**response, 'plan_hash': 'wrong'}), '')
        self.assertEqual(self.run_child(process), {'status': 'blocked', 'reason': 'collector_result_unavailable'})

    def test_invalid_json_keeps_unavailable_result(self):
        process = Mock(communicate=Mock(return_value=('broken', '')))
        self.assertEqual(self.run_child(process), {'status': 'blocked', 'reason': 'collector_result_unavailable'})
