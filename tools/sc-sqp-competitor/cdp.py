import json, os, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

import websocket
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "browserctl"))
from browser_session import session_environment, assert_session_lock
os.environ.update(session_environment(os.environ.get("AMAZON_BROWSER_SESSION", "grimoire"), inherit=True))

HOST = os.environ.get("CDP_HOST", "127.0.0.1")
PORT = os.environ.get("CDP_PORT", "9223")
URL_HOST = f"[{HOST}]" if ":" in HOST and not HOST.startswith("[") else HOST
BASE = f"http://{URL_HOST}:{PORT}"
BROWSERCTL = Path(__file__).resolve().parents[1] / "browserctl" / "browserctl.mjs"


def _auto_start_enabled():
    return os.environ.get("CDP_AUTOSTART", "1").lower() not in {"0", "false", "no", "off"}


def _json(path):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return json.load(opener.open(BASE + path, timeout=3))


def ensure_chrome():
    try:
        return _json("/json/version")
    except (OSError, urllib.error.URLError):
        if not _auto_start_enabled():
            raise RuntimeError("CDP automatic startup is disabled by CDP_AUTOSTART")
        normalized = HOST.lower()
        loopback = normalized in {"localhost", "127.0.0.1"}
        if not loopback:
            raise RuntimeError(f"refusing local Chrome startup for non-local CDP_HOST={HOST}")
    launched = subprocess.run(
        ["node", str(BROWSERCTL), "ensure", "--port", str(PORT)],
        capture_output=True, text=True, env=os.environ.copy(), check=False,
    )
    if launched.returncode:
        detail = (launched.stderr or launched.stdout or "launcher failed").strip()
        raise RuntimeError(f"could not ensure managed Chrome: {detail}")
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            return _json("/json/version")
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise RuntimeError(f"dedicated Chrome did not become ready at {BASE}")

def tabs():
    ensure_chrome()
    return _json("/json/list")

class Tab:
    def __init__(self, ws_url):
        assert_session_lock(PORT)
        parsed = urllib.parse.urlparse(ws_url)
        if parsed.hostname not in {HOST, "localhost", "127.0.0.1"} or parsed.port != int(PORT):
            raise RuntimeError("BROWSER_SESSION_CONFLICT: tab endpoint differs from selected session")
        self.target_id = parsed.path.rsplit("/", 1)[-1]
        self.ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
        self.mid = 0
    def cmd(self, method, **params):
        assert_session_lock(PORT)
        self.mid += 1
        self.ws.send(json.dumps({'id': self.mid, 'method': method, 'params': params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == self.mid:
                assert_session_lock(PORT)
                if 'error' in msg: raise RuntimeError(msg['error'])
                return msg.get('result', {})
    def js(self, expr, await_promise=False):
        r = self.cmd('Runtime.evaluate', expression=expr, returnByValue=True, awaitPromise=await_promise)
        res = r.get('result', {})
        if res.get('subtype') == 'error': raise RuntimeError(res.get('description'))
        return res.get('value')
    def navigate(self, url, wait=4):
        self.cmd('Page.navigate', url=url)
        time.sleep(wait)
    def wait_ready(self, timeout=20):
        t0=time.time()
        while time.time()-t0 < timeout:
            if self.js("document.readyState") == 'complete': return True
            time.sleep(0.5)
        return False
    def screenshot(self, path, *, evidence_spec=None):
        # Legacy extraction must use the same owned-task evidence checks.
        import tempfile
        assert_session_lock(PORT)
        spec = dict(evidence_spec or {})
        if (not spec.get("expected") or not spec.get("task")
                or spec["task"].get("targetId") != self.target_id):
            raise RuntimeError("EVIDENCE_TASK_REQUIRED: supply the released managed task and verified account specification")
        destination = Path(path).resolve()
        if destination.suffix != ".png":
            raise ValueError("Screenshot destination must be PNG")
        spec.update(output_dir=str(destination.parent), captures=[{
            "id": destination.stem, "source_kind": "seller_central",
            "finding": "SQP competitor query", "caption": "Verified Seller Central query evidence"}])
        with tempfile.TemporaryDirectory(prefix="sqp-evidence-") as tmp:
            request = Path(tmp) / "capture.json"
            request.write_text(json.dumps(spec))
            command = ["node", str(Path(__file__).resolve().parents[1] / "amazon-ad-audit/capture_audit_evidence.mjs"), str(request)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=60, check=False)
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or "Task evidence capture failed")
    def close(self):
        self.ws.close()

def get_tab(match):
    matches = [t for t in tabs() if t.get('type') == 'page' and match in (t.get('url') or '')]
    if len(matches) > 1:
        raise RuntimeError("CDP_TARGET_AMBIGUOUS: supply an exact task target")
    if matches:
        t = matches[0]
        return Tab(t['webSocketDebuggerUrl']), t
    return None, None
