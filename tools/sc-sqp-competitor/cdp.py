import json, time, websocket, urllib.request, sys

def tabs():
    return json.load(urllib.request.urlopen('http://localhost:9222/json/list'))

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
