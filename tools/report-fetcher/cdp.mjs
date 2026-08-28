/*
 * Minimal Chrome DevTools Protocol client — zero dependencies (Node 22+ global
 * WebSocket + fetch). Used to run the report fetch in the page's REAL main world
 * (which has fetch + the logged-in session), driven from the terminal.
 *
 * `ensureChrome()` starts or reuses the dedicated headless browser.
 * `assertChrome()` remains a read-only probe for setup checks and diagnostics.
 */

import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

const HOST = process.env.CDP_HOST || "127.0.0.1";
const PORT = process.env.CDP_PORT || "9222";
const URL_HOST = HOST.includes(":") && !HOST.startsWith("[") ? `[${HOST}]` : HOST;
const BASE = `http://${URL_HOST}:${PORT}`;
const LAUNCHER = process.env.CDP_LAUNCHER
  || fileURLToPath(new URL("./launch-chrome-debug.py", import.meta.url));
let startupPromise = null;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// CDP_DEBUG=1 prints one stderr line per protocol call with its round-trip time,
// which is how a hang gets localized to a method without touching the code.
const DEBUG = /^(1|true|yes|on)$/i.test(String(process.env.CDP_DEBUG || ""));

function autoStartEnabled() {
  return !/^(0|false|no|off)$/i.test(String(process.env.CDP_AUTOSTART || "1"));
}

function isLoopback(host) {
  const normalized = String(host).toLowerCase();
  return normalized === "localhost" || normalized === "127.0.0.1";
}

async function runLauncher() {
  const configured = process.env.CDP_PYTHON;
  const candidates = configured
    ? [configured]
    : (process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"]);
  let missing = null;
  for (const python of candidates) {
    try {
      const result = await new Promise((resolve, reject) => {
        const child = spawn(python, [LAUNCHER, "--mode", "headless"], {
          env: process.env,
          stdio: ["ignore", "pipe", "pipe"],
          windowsHide: true,
        });
        let stdout = "";
        let stderr = "";
        child.stdout.on("data", (chunk) => { stdout += chunk; });
        child.stderr.on("data", (chunk) => { stderr += chunk; });
        child.on("error", reject);
        child.on("close", (code) => resolve({ code, stdout, stderr }));
      });
      if (result.code !== 0) {
        const detail = (result.stderr || result.stdout || `exit ${result.code}`).trim();
        throw new Error(`dedicated Chrome launcher failed: ${detail}`);
      }
      return;
    } catch (error) {
      if (error?.code === "ENOENT") {
        missing = error;
        continue;
      }
      throw error;
    }
  }
  throw new Error(
    `No Python interpreter could run ${LAUNCHER}${missing ? ` (${missing.message})` : ""}`,
  );
}

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
      `Use --mode recovery only if Seller Central login is required. (${e.message})`);
  }
}

/** Start or reuse the dedicated headless Chrome, then return its version.
 *
 * The optional `start` injection exists for tests; production callers should
 * call `ensureChrome()` with no arguments. Concurrent callers share one launch.
 */
export async function ensureChrome({ start = runLauncher, timeoutMs = 15000, pollMs = 250 } = {}) {
  try { return await assertChrome(); }
  catch (initialError) {
    if (!autoStartEnabled()) {
      throw new Error(`CDP automatic startup is disabled by CDP_AUTOSTART. ${initialError.message}`);
    }
    if (!isLoopback(HOST)) {
      throw new Error(
        `Refusing to start a local browser for non-local CDP_HOST=${HOST}. ${initialError.message}`,
      );
    }
  }

  if (!startupPromise) {
    startupPromise = Promise.resolve().then(start).finally(() => { startupPromise = null; });
  }
  await startupPromise;

  const deadline = Date.now() + timeoutMs;
  let lastError;
  do {
    try { return await assertChrome(); }
    catch (error) { lastError = error; }
    await sleep(pollMs);
  } while (Date.now() < deadline);
  throw new Error(
    `Dedicated headless Chrome did not become ready at ${BASE}. ${lastError?.message || ""}`.trim(),
  );
}

export async function listPages() {
  return (await httpJson("/json/list")).filter((t) => t.type === "page");
}

// A live CDP session over one target's WebSocket.
export class Session {
  constructor(ws) { this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; }

  static async open(webSocketDebuggerUrl, { timeoutMs = 10000 } = {}) {
    const ws = new WebSocket(webSocketDebuggerUrl);
    // A destroyed target's ws endpoint can accept the TCP connection and then
    // never complete the upgrade, firing neither onopen nor onerror.
    await new Promise((res, rej) => {
      const timer = setTimeout(() => {
        // reject before close: closing a half-open socket fires onerror synchronously
        rej(new Error(`CDP WebSocket handshake timed out after ${timeoutMs} ms`));
        try { ws.close(); } catch (_) {}
      }, timeoutMs);
      ws.onopen = () => { clearTimeout(timer); res(); };
      ws.onerror = () => { clearTimeout(timer); rej(new Error("CDP WebSocket failed to open")); };
    });
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
        // A detached/crashed target keeps its socket open but will never answer
        // another command (an account switch navigating the tab does exactly
        // this). Fail every in-flight call now, with a name, instead of hanging.
        if (msg.method === "Inspector.detached" || msg.method === "Inspector.targetCrashed") {
          s._rejectPending(`CDP target detached${msg.params?.reason ? `: ${msg.params.reason}` : ""}`);
        }
      }
    };
    ws.onclose = () => s._rejectPending("CDP WebSocket closed");
    ws.onerror = () => s._rejectPending("CDP WebSocket error");
    return s;
  }

  _rejectPending(message) {
    const pending = [...this.pending.values()];
    this.pending.clear();
    for (const { reject } of pending) reject(new Error(message));
  }

  // Streaming event hook (used by long-running listeners, e.g. the POE endpoint
  // discovery logger). `method` may be "*" for all events.
  subscribe(method, fn) {
    this._subs = this._subs || {};
    (this._subs[method] = this._subs[method] || []).push(fn);
  }

  // `timeoutMs` is opt-in: the default remains wait-forever because long-lived
  // callers (POE evaluates, endpoint-discovery listeners) legitimately wait
  // minutes. Control-plane calls (Runtime.enable, Page.enable) should pass one.
  send(method, params = {}, { timeoutMs } = {}) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      // Node's built-in global WebSocket does not keep the event loop alive while
      // idly awaiting an inbound frame, so a slow Runtime.evaluate (awaitPromise
      // for a multi-second page fetch, e.g. POE data) lets the process exit early
      // with "unsettled top-level await" (exit 13) before Chrome replies. A ref'd
      // keepalive timer holds the loop open until the response lands.
      const keepalive = setInterval(() => {}, 1 << 30);
      const t0 = DEBUG ? Date.now() : 0;
      let timer;
      const done = (fn) => (v) => {
        clearInterval(keepalive);
        if (timer) clearTimeout(timer);
        if (DEBUG) console.error(`[cdp] ${method} → ${Date.now() - t0} ms`);
        fn(v);
      };
      this.pending.set(id, { resolve: done(resolve), reject: done(reject) });
      if (timeoutMs) {
        timer = setTimeout(() => {
          const entry = this.pending.get(id);
          if (!entry) return;
          this.pending.delete(id);
          entry.reject(new Error(`CDP ${method} timed out after ${timeoutMs} ms`));
        }, timeoutMs);
      }
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

  close() {
    this._rejectPending("CDP session closed");
    try { this.ws.close(); } catch (_) {}
  }
}

// Full desktop viewport on every programmatically created tab.
//
// The launcher already passes --window-size, but a tab created over CDP does not
// always inherit it, and a page that renders at 800x600 is a different page: Amazon
// serves a narrow layout, lazy-loaded gallery and A+ modules never enter the
// viewport, and screenshots come out cramped or clipped. Setting it per tab makes
// the size independent of how Chrome happened to be started. Failure is non-fatal,
// because a data fetch does not care about layout.
export const DESKTOP_VIEWPORT = { width: 1920, height: 1080, deviceScaleFactor: 1 };

export async function setDesktopViewport(session, viewport = DESKTOP_VIEWPORT) {
  try {
    await session.send("Emulation.setDeviceMetricsOverride", { mobile: false, ...viewport });
  } catch (_) { /* older target or a page that refuses emulation: keep going */ }
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
    if (p && p.webSocketDebuggerUrl) {
      const session = await Session.open(p.webSocketDebuggerUrl);
      await setDesktopViewport(session);
      return { targetId, session };
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("created target never appeared in the page list");
}

export async function closePage(targetId) {
  try { await fetch(`${BASE}/json/close/${targetId}`); } catch (_) {}
}

// Run an async expression in the page main world and return its (JSON) value.
export async function evaluate(session, expression, timeoutMs = 120000) {
  let hardTimer;
  const hardTimeoutMs = timeoutMs + 5000;
  const timeout = new Promise((_, reject) => {
    hardTimer = setTimeout(() => {
      reject(new Error(`CDP Runtime.evaluate timed out after ${hardTimeoutMs} ms`));
      session.close();
    }, hardTimeoutMs);
  });
  let r;
  try {
    // The hard timer is armed BEFORE Runtime.enable so the whole call is
    // budgeted. A mid-navigation target that never answers Runtime.enable used
    // to hang the process forever here (13.08.2026 account-chooser incident).
    r = await Promise.race([
      (async () => {
        await session.send("Runtime.enable", {}, { timeoutMs: 10000 });
        return session.send("Runtime.evaluate", {
          expression, awaitPromise: true, returnByValue: true, timeout: timeoutMs,
        });
      })(),
      timeout,
    ]);
  } finally {
    clearTimeout(hardTimer);
  }
  if (r.exceptionDetails) {
    throw new Error("page evaluate threw: " + (r.exceptionDetails.exception?.description || r.exceptionDetails.text));
  }
  return r.result?.value;
}
