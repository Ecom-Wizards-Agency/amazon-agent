"""Package failures must happen before either deliverable is generated."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which("node"), "Node required")
class RuntimePreflightTests(unittest.TestCase):
    def assert_failed_before_output(self, incompatible=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = json.loads((HERE / "fixtures/generic.json").read_text())
            output = root / "deliverables"
            config["client"]["output_dir"] = str(output)
            source = root / "config.json"
            source.write_text(json.dumps(config))
            packages = root / "runtime/dependencies/node/node_modules"
            if incompatible:
                package = packages / "@oai/artifact-tool"
                package.mkdir(parents=True)
                (root / "runtime/runtime.json").write_text(json.dumps({
                    "bundleVersion": "test", "artifactToolVersion": "1.0.0",
                    "targetPlatform": "incompatible-platform", "targetArch": "incompatible-arch"}))
                (package / "package.json").write_text('{"version":"2.0.0"}')
            run = subprocess.run([sys.executable, str(HERE.parent / "build_launch_strategy.py"),
                                  "--config", str(source), "--build", "--node-modules",
                                  str(packages)],
                                 capture_output=True, text=True, env=os.environ.copy())
            self.assertNotEqual(0, run.returncode)
            self.assertIn("Artifact runtime unavailable", run.stderr)
            self.assertFalse(output.exists(), "runtime failure created partial deliverables")

    def test_missing_explicit_runtime_leaves_no_output(self):
        self.assert_failed_before_output()

    def test_incompatible_runtime_leaves_no_output(self):
        self.assert_failed_before_output(incompatible=True)


if __name__ == "__main__":
    unittest.main()
