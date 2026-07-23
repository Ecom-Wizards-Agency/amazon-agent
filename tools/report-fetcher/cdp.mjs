/*
 * Minimal Chrome DevTools Protocol client — zero dependencies (Node 22+ global
 * WebSocket + fetch). Used to run the report fetch in the page's REAL main world
 * (which has fetch + the logged-in session), driven from the terminal.
 *
 * Chrome must be running with --remote-debugging-port (see launch-chrome-debug.sh).
 */

const HOST = process.env.CDP_HOST || "127.0.0.1";
const PORT = process.env.CDP_PORT || "9222";
const BASE = `http://${HOST}:${PORT}`;

export async function httpJson(path) {
  const r = await fetch(BASE + path);
  if (!r.ok) throw new Error(`CDP HTTP ${r.status} on ${path}`);
  return r.json();
}

export async function assertChrome() {
  try { return await httpJson("/json/version"); }
  catch (e) {
    throw new Error(
      `Cannot reach Chrome debug port at ${BASE}. Launch Chrome with the debug port first:\n` +
      `  tools/report-fetcher/launch-chrome-debug.sh\n` +
      `then open Seller Central and log in. (${e.message})`);
  }
}

export async function listPages() {
  return (await httpJson("/json/list")).filter((t) => t.type === "page");
}

// A live CDP session over one target's WebSocket.
export class Session {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; }

  static async open(webSocketDebuggerUrl) {
    const ws = new WebSocket(webSocketDebuggerUrl);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = () => rej(new Error("CDP WebSocket failed to open")); });
    const s = new Session(ws);
    ws.onmessage = (m) => {
      const msg = JSON.parse(m.data);
      if (msg.id && s.pending.has(msg.id)) {
        const { resolve, reject } = s.pending.get(msg.id); s.pending.delete(msg.id);
        msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
      } else if (msg.method) {
        s.events.push(msg);
        for (const w of s._waiters || []) if (w.method === msg.method) w.resolve(msg);
        const subs = s._subs || {};
        for (const fn of [...(subs[msg.method] || []), ...(subs["*"] || [])]) {
          try { fn(msg.params, msg.method); } catch (_) { /* subscriber errors must not kill the socket */ }
        }
      }
    };
    return s;
  }

  // Streaming event hook (used by long-running listeners, e.g. the POE endpoint
  // discovery logger). `method` may be "*" for all events.
  subscribe(method, fn) {
    this._subs = this._subs || {};
    (this._subs[method] = this._subs[method] || []).push(fn);
  }

  send(method, params = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      // Node's built-in global WebSocket does not keep the event loop alive while
      // idly awaiting an inbound frame, so a slow Runtime.evaluate (awaitPromise
      // for a multi-second page fetch, e.g. POE data) lets the process exit early
      // with "unsettled top-level await" (exit 13) before Chrome replies. A ref'd
      // keepalive timer holds the loop open until the response lands.
      const keepalive = setInterval(() => {}, 1 << 30);
      const done = (fn) => (v) => { clearInterval(keepalive); fn(v); };
      this.pending.set(id, { resolve: done(resolve), reject: done(reject) });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  waitEvent(method, timeoutMs = 20000) {
    const hit = this.events.find((e) => e.method === method);
    if (hit) return Promise.resolve(hit);
    return new Promise((resolve, reject) => {
      this._waiters = this._waiters || [];
      const w = { method, resolve };
      this._waiters.push(w);
      setTimeout(() => reject(new Error(`timeout waiting for ${method}`)), timeoutMs);
    });
  }

  close() { try { this.ws.close(); } catch (_) {} }
}

// Create a fresh page at `url`, return {targetId, session}. Uses the browser-level
// endpoint so we don't disturb the operator's existing tabs.
export async function createPage(url) {
  const ver = await httpJson("/json/version");
  const browser = await Session.open(ver.webSocketDebuggerUrl);
  // background: true keeps the temp tab from stealing focus / flashing to the
  // front while the operator is using the debug window (e.g. logging in).
  const { targetId } = await browser.send("Target.createTarget", { url, background: true });
  browser.close();
  // find the new target's page WS
  for (let i = 0; i < 40; i++) {
    const pages = await listPages();
    const p = pages.find((x) => x.id === targetId);
    if (p && p.webSocketDebuggerUrl) return { targetId, session: await Session.open(p.webSocketDebuggerUrl) };
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("created target never appeared in the page list");
}

export async function closePage(targetId) {
  try { await fetch(`${BASE}/json/close/${targetId}`); } catch (_) {}
}

// Run an async expression in the page main world and return its (JSON) value.
export async function evaluate(session, expression, timeoutMs = 120000) {
  await session.send("Runtime.enable");
  const r = await session.send("Runtime.evaluate", {
    expression, awaitPromise: true, returnByValue: true, timeout: timeoutMs,
  });
  if (r.exceptionDetails) {
    throw new Error("page evaluate threw: " + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  }
  return r.result?.value;
}
