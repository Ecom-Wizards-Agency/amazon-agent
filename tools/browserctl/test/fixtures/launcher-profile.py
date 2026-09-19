import contextlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import patch

with tempfile.TemporaryDirectory(prefix="launcher-profile-") as directory:
    root = Path(directory)
    profile = root / "profile"
    profile.mkdir()
    alias = root / "alias"
    alias.symlink_to(profile, target_is_directory=True)
    launcher = Path(__file__).resolve().parents[3] / "report-fetcher/launch-chrome-debug.py"
    with patch.dict(os.environ, {"CDP_PORT": "19323", "CDP_PROFILE": str(alias),
                                 "AMAZON_BROWSER_POLICY": str(root / "policy.json")}):
        spec = importlib.util.spec_from_file_location("launcher", launcher)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    proc = root / "proc"
    (proc / "net").mkdir(parents=True)
    (proc / "net/tcp").write_text("header\n0: 0100007F:4B7B 00000000:0000 0A 0 0 0 0 0 123\n")
    (proc / "10/fd").mkdir(parents=True)
    (proc / "10/fd/7").symlink_to("socket:[123]")
    with patch.object(module, "Path", side_effect=lambda value: proc / str(value).removeprefix("/proc/")
                      if str(value).startswith("/proc/") else proc if str(value) == "/proc" else Path(value)):
        assert module.listening_processes() == {10}
    good = ["chrome", "--remote-debugging-port=19323", f"--user-data-dir={profile}"]
    wrong = ["chrome", "--remote-debugging-port=19323", f"--user-data-dir={root / 'wrong'}"]
    with patch.object(module, "process_arguments", return_value=good):
        assert module.process_matches(10)
    with patch.object(module, "process_arguments", return_value=wrong):
        assert not module.process_matches(10)
    with patch.object(module, "process_arguments", return_value=["chrome", "--remote-debugging-port", "19323", "--user-data-dir", str(profile)]):
        assert module.process_matches(10)
    with patch.object(module, "process_arguments", return_value=good + ["--type=renderer"]):
        assert not module.process_matches(10)
    # A matching decoy process cannot verify the different process owning the socket.
    with patch.object(module, "listening_processes", return_value={20}), patch.object(
        module, "process_arguments", side_effect=lambda pid: good if pid == 10 else wrong
    ):
        assert module.find_matching_process() is None
    with patch.object(module, "listening_processes", return_value={10}), patch.object(
        module, "process_arguments", return_value=good
    ):
        assert module.find_matching_process() == (10, "headed")
    assert module.devtools_active_port() is None
    (profile / "DevToolsActivePort").write_text("19323\n/devtools/browser/fixture\n")
    assert module.devtools_active_port() == "19323"
    with patch.object(module.sys, "platform", "win32"):
        assert module.process_matches(10) is None
        assert module.listening_processes() is None
        assert module.listener_profile_status() == (None, None)
        with patch.object(module.subprocess, "run") as kill, patch.object(module, "port_is_up", return_value=False), patch.object(module.time, "sleep"):
            module.stop_managed_browser({"pid": 10})
            assert kill.call_args.args[0] == ["taskkill", "/PID", "10", "/T"]
    with patch.object(module.sys, "platform", "darwin"), patch.object(module.subprocess, "run", side_effect=FileNotFoundError):
        assert module.listening_processes() is None
    with patch.object(module, "listening_processes", return_value={10}), patch.object(module, "process_arguments", return_value=[]):
        assert module.listener_profile_status() == (None, None)
    statuses = []
    for owners, arguments, expected in [(None, good, None), ({10}, good, True), ({20}, wrong, False)]:
        output = io.StringIO()
        with patch.object(module, "parse_args", return_value=type("Args", (), {"mode": "status"})()), patch.object(
            module, "read_state", return_value={"pid": 99, "mode": "headed"}
        ), patch.object(module, "port_is_up", return_value=True), patch.object(
            module, "listening_processes", return_value=owners
        ), patch.object(module, "process_arguments", return_value=arguments), contextlib.redirect_stdout(output):
            module.main()
        status = json.loads(output.getvalue())
        assert status["profile_verified"] is expected
        assert status["devtools_active_port"] == "19323"
        assert status["managed"] is True
        statuses.append(status)
if '--json' in sys.argv:
    print(json.dumps(statuses))
else:
    print("launcher profile checks: symlink, wrong profile, exact flags, listener ownership, Windows restart, unknown owners, tri-state status PASS")
