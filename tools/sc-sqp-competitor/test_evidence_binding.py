import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
