import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# A fixture policy and runtime, so importing cdp.py never reads the machine's live policy.
_runtime = tempfile.TemporaryDirectory()
os.environ.update({"AMAZON_BROWSER_RUNTIME_DIR": _runtime.name,
                   "AMAZON_BROWSER_POLICY": str(Path(_runtime.name) / "policy.json"),
                   "AMAZON_BROWSER_LOCK_DIR": str(Path(_runtime.name) / "locks")})
for _key in ("AMAZON_BROWSER_SESSION", "CDP_PORT", "CDP_PROFILE", "CDP_HOST", "WIZARDS_AI_MODE"):
    os.environ.pop(_key, None)
Path(os.environ["AMAZON_BROWSER_POLICY"]).write_text(json.dumps({"schema_version": 1, "routing": {"default_cdp_port": 9222},
    "ports": {"9222": {"profile": str(Path(_runtime.name) / "operator")}, "9223": {"profile": str(Path(_runtime.name) / "grimoire")}}}))

spec = importlib.util.spec_from_file_location("sqp_cdp", Path(__file__).with_name("cdp.py"))
cdp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cdp)


class EvidenceBindingTests(unittest.TestCase):
    def test_unowned_or_other_target_never_launches_capture(self):
        tab = object.__new__(cdp.Tab)
        tab.target_id = "owned"
        with tempfile.TemporaryDirectory() as tmp, patch.object(cdp, "assert_session_lock"), \
                patch.object(cdp.subprocess, "run") as run:
            for evidence in [None, {"task": {"targetId": "other"}, "expected": {"kind": "seller-central"}}]:
                with self.assertRaisesRegex(RuntimeError, "EVIDENCE_TASK_REQUIRED"):
                    tab.screenshot(Path(tmp) / "capture.png", evidence_spec=evidence)
            run.assert_not_called()

    def test_operator_session_is_refused_before_resolution(self):
        for env in [{"AMAZON_BROWSER_SESSION": "operator"}, {"CDP_PORT": "9222"}, {"CDP_PORT": "09222"}]:
            module = importlib.util.module_from_spec(spec)
            with self.subTest(env=env), patch.dict(os.environ, env), \
                    patch("subprocess.run") as run:
                with self.assertRaisesRegex(RuntimeError, "SQP_COMPETITOR_GRIMOIRE_ONLY"):
                    spec.loader.exec_module(module)
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
