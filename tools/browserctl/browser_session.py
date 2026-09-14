"""Python adapter to Amazon Agent's canonical named-session resolver."""
import json
import os
import subprocess
import shutil
from pathlib import Path


CONTROLLER = Path(__file__).resolve().with_name("browserctl.mjs")
NODE = shutil.which("node") or "node"


def _assert_pid_exists(pid):
    if int(pid) <= 0:
        raise ValueError("invalid owner")
    try:
        os.kill(int(pid), 0)
    except PermissionError:
        # The credential broker has a different UID from the workflow owner.
        pass


def session_environment(name="grimoire", overrides=None, *, inherit=False):
    allowed = {"HOME", "PATH", "LANG", "LC_ALL", "TMPDIR", "AMAZON_BROWSER_POLICY",
               "AMAZON_BROWSER_RUNTIME_DIR", "AMAZON_BROWSER_SESSION", "CDP_PORT", "CDP_PROFILE", "CDP_HOST"}
    env = {key: value for key, value in os.environ.items() if key in allowed}
    # A worker's selected session is explicit, never the caller's operator route.
    if not inherit:
        for key in ("CDP_PORT", "CDP_PROFILE", "CDP_HOST", "AMAZON_BROWSER_SESSION"):
            env.pop(key, None)
    for key, value in (overrides or {}).items():
        value = str(value)
        prior = env.get(key)
        if inherit and prior and key in {"CDP_PORT", "CDP_PROFILE", "CDP_HOST", "AMAZON_BROWSER_SESSION"}:
            comparable = lambda item: str(Path(item).expanduser().resolve()) if key == "CDP_PROFILE" else item
            if comparable(prior) != comparable(value):
                raise RuntimeError(f"BROWSER_SESSION_CONFLICT: inherited {key} disagrees with workflow configuration")
        env[key] = value
    result = subprocess.run([NODE, str(CONTROLLER), "session", "--session", name],
                            env=env, capture_output=True, text=True, timeout=15, check=False)
    if result.returncode:
        raise RuntimeError(result.stdout.strip() or "browser session resolution failed")
    return json.loads(result.stdout)


def bind_process_session():
    if os.environ.get("CDP_PORT", "9223") not in {"9222", "9223"} and not os.environ.get("AMAZON_BROWSER_SESSION"):
        return
    name = os.environ.get("AMAZON_BROWSER_SESSION") or ("operator" if os.environ.get("CDP_PORT") == "9222" else "grimoire")
    os.environ.update(session_environment(name, inherit=True))


def assert_session_lock(port):
    if int(port) != 9223:
        return
    path = Path(os.environ.get("AMAZON_BROWSER_LOCK_DIR", str(Path.home() / ".amazon-agent/locks"))) / "cdp-9223.lock"
    try:
        record = json.loads(path.read_text())
        if not os.environ.get("AMAZON_BROWSER_LOCK_TOKEN") or record.get("token") != os.environ["AMAZON_BROWSER_LOCK_TOKEN"]:
            raise ValueError("not owned")
        if int(record.get("pid", 0)) <= 0:
            raise ValueError("invalid owner")
        _assert_pid_exists(record["pid"])
        parent_token = record["token"]
        chain = json.loads(os.environ.get("AMAZON_BROWSER_LOCK_CHAIN", "[]"))
        import re
        if not isinstance(chain, list) or len(chain) > 32:
            raise ValueError("invalid chain")
        for token in chain:
            if not isinstance(token, str) or not re.fullmatch(r"[a-f0-9-]{16,64}", token):
                raise ValueError("invalid chain")
            child = json.loads(path.with_name(path.name + ".child-" + parent_token).read_text())
            if child.get("token") != token or int(child.get("pid", 0)) <= 0:
                raise ValueError("child control lost")
            _assert_pid_exists(child["pid"])
            parent_token = token
    except (OSError, ValueError, KeyError, TypeError):
        raise RuntimeError("BROWSER_SESSION_LOCK_REQUIRED: use browserctl run --session grimoire -- command") from None
