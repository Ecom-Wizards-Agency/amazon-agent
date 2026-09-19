"""Filesystem regression tests; no browser or authentication process is started."""
import errno
import importlib.util
import os
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


LAUNCHER = Path(__file__).resolve().parents[1] / "launch-chrome-debug.py"
BROKER_UID = 70001
OTHER_UID = 70002
UNDEFINED = 0xFFFFFFFF


def access_acl(*, broker_permissions=1, mask=1, extra_user=False):
    entries = [(1, 7, UNDEFINED), (2, broker_permissions, BROKER_UID)]
    if extra_user:
        entries.append((2, 7, OTHER_UID))
    entries.extend([(4, 0, UNDEFINED), (16, mask, UNDEFINED), (32, 0, UNDEFINED)])
    return struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *row) for row in entries)


@unittest.skipUnless(sys.platform.startswith("linux") and shutil.which("getfacl"),
                     "requires Linux POSIX ACLs and getfacl for independent verification")
class LauncherPermissionsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        self.parent = self.home / ".amazon-agent"
        self.parent.mkdir()
        self.profile = self.parent / "wizards-ai-chrome"
        try:
            os.setxattr(self.parent, "system.posix_acl_access", access_acl())
        except OSError as exc:
            if exc.errno in (errno.EOPNOTSUPP, errno.EPERM):
                self.skipTest("test filesystem does not support writable POSIX ACLs")
            raise
        with patch.dict(os.environ, {"CDP_PORT": "9333", "CDP_PROFILE": str(self.profile),
                                     "AMAZON_BROWSER_POLICY": str(self.home / "absent-policy.json")}):
            spec = importlib.util.spec_from_file_location("test_chrome_launcher", LAUNCHER)
            self.launcher = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.launcher)
        self.launcher.PROFILE = self.profile
        for context in (patch.object(Path, "home", return_value=self.home),
                        patch("pwd.getpwnam", return_value=SimpleNamespace(pw_uid=BROKER_UID))):
            context.start()
            self.addCleanup(context.stop)

    def acl(self, path):
        result = subprocess.run(["getfacl", "--omit-header", "--numeric", "--access", str(path)],
                                check=True, capture_output=True, text=True)
        return set(line.strip() for line in result.stdout.splitlines() if line.strip())

    def assert_private_profile(self):
        self.assertEqual(stat.S_IMODE(self.profile.stat().st_mode), 0o700)
        for row in self.acl(self.profile):
            if row.startswith(f"user:{BROKER_UID}:"):
                self.assertIn("#effective:---", row)

    def test_existing_broker_traverse_survives_repeated_profile_hardening(self):
        self.profile.mkdir()
        os.setxattr(self.profile, "system.posix_acl_access", access_acl(broker_permissions=7, mask=7))
        for _ in range(2):
            self.launcher.protect_profile()
            self.assertEqual(self.acl(self.parent), {
                "user::rwx", f"user:{BROKER_UID}:--x", "group::---", "mask::--x", "other::---"})
            self.assertEqual(stat.S_IMODE(self.parent.stat().st_mode), 0o710)
            self.assert_private_profile()

    def test_masked_installed_grant_is_restored_without_activating_other_users(self):
        os.setxattr(self.parent, "system.posix_acl_access", access_acl(mask=0, extra_user=True))
        self.launcher.protect_profile()
        self.assertEqual(self.acl(self.parent), {
            "user::rwx", f"user:{BROKER_UID}:--x", "group::---", "mask::--x", "other::---"})
        self.assert_private_profile()

    def test_no_broker_entry_means_no_new_access_grant(self):
        os.removexattr(self.parent, "system.posix_acl_access")
        os.chmod(self.parent, 0o777)
        self.launcher.protect_profile()
        self.assertEqual(stat.S_IMODE(self.parent.stat().st_mode), 0o700)
        self.assertFalse(any(row.startswith(f"user:{BROKER_UID}:") for row in self.acl(self.parent)))
        self.assert_private_profile()

    def test_non_traverse_broker_permissions_are_not_preserved(self):
        os.setxattr(self.parent, "system.posix_acl_access", access_acl(broker_permissions=7, mask=7))
        self.launcher.protect_profile()
        self.assertEqual(stat.S_IMODE(self.parent.stat().st_mode), 0o700)
        self.assertTrue(any(row.startswith(f"user:{BROKER_UID}:rwx") and "#effective:---" in row
                            for row in self.acl(self.parent)))
        self.assert_private_profile()

    def test_existing_custom_parent_permissions_and_acl_remain_unchanged(self):
        shared = self.home / "shared"
        shared.mkdir()
        os.setxattr(shared, "system.posix_acl_access", access_acl(mask=7, extra_user=True))
        before = self.acl(shared), stat.S_IMODE(shared.stat().st_mode)
        self.launcher.PROFILE = shared / "custom-profile"
        self.launcher.protect_profile()
        self.assertEqual((self.acl(shared), stat.S_IMODE(shared.stat().st_mode)), before)
        self.assertEqual(stat.S_IMODE(self.launcher.PROFILE.stat().st_mode), 0o700)

    def test_new_private_root_has_no_automatically_installed_broker_acl(self):
        self.parent.rmdir()
        self.launcher.protect_profile()
        self.assertEqual(stat.S_IMODE(self.parent.stat().st_mode), 0o700)
        self.assertEqual(self.acl(self.parent), {"user::rwx", "group::---", "other::---"})
        self.assert_private_profile()


if __name__ == "__main__":
    unittest.main()
