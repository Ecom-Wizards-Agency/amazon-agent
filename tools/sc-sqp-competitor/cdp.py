import json, os, subprocess, time, urllib.error, urllib.request
from pathlib import Path

import websocket

HOST = os.environ.get("CDP_HOST", "127.0.0.1")
PORT = os.environ.get("CDP_PORT", "9222")
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
        self.ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
        self.mid = 0
    def cmd(self, method, **params):
        self.mid += 1
        self.ws.send(json.dumps({'id': self.mid, 'method': method, 'params': params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == self.mid:
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
    def screenshot(self, path):
        import base64
        r = self.cmd('Page.captureScreenshot', format='png')
        open(path,'wb').write(base64.b64decode(r['data']))
    def close(self):
        self.ws.close()

def get_tab(match):
    for t in tabs():
        if t.get('type')=='page' and match in (t.get('url') or ''):
            return Tab(t['webSocketDebuggerUrl']), t
    return None, None
