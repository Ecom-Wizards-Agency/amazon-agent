/*
 * Minimal Chrome DevTools Protocol client, zero dependencies (Node 22+ global
 * WebSocket + fetch). Used to run the report fetch in the page's REAL main world
 * (which has fetch + the logged-in session), driven from the terminal.
 *
 * `ensureChrome()` starts or reuses the policy-configured dedicated browser.
 * `assertChrome()` remains a read-only probe for setup checks and diagnostics.
 */

import { spawn } from "node:child_process";
import { AsyncLocalStorage } from "node:async_hooks";
import { fileURLToPath } from "node:url";
import {
  acquireLease, defaultLeaseOwner, releaseLease, touchLease,
} from "../browserctl/lease-registry.mjs";
import { loadBrowserPolicy } from "../browserctl/policy.mjs";
import { assertContextCovers, isRegionalScope, scopeForOrigin } from "../browserctl/context-scopes.mjs";
import { bindProcessSession } from "../browserctl/session.mjs";
import { acquireSessionLock, assertSessionLock } from "../browserctl/session-lock.mjs";

bindProcessSession();

const HOST = process.env.CDP_HOST || "127.0.0.1";
const PORT = process.env.CDP_PORT || "9223";
const URL_HOST = HOST.includes(":") && !HOST.startsWith("[") ? `[${HOST}]` : HOST;
const BASE = `http://${URL_HOST}:${PORT}`;
const LAUNCHER = process.env.CDP_LAUNCHER
  || fileURLToPath(new URL("./launch-chrome-debug.py", import.meta.url));
let startupPromise = null;
const taskControlCheck = new AsyncLocalStorage();

function leaseTrackingEnabled() {
  return [9222, 9223].includes(Number(PORT))
    || /^(1|true|yes|on)$/i.test(String(process.env.CDP_ENABLE_TEST_LEASES || ""));
}

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

async function runLauncherArguments(args) {
  const configured = process.env.CDP_PYTHON;
  const candidates = configured
    ? [configured]
    : (process.platform === "win32" ? ["py", "python", "python3"] : ["python3", "python"]);
  let missing = null;
  for (const python of candidates) {
    try {
      const result = await new Promise((resolve, reject) => {
        const child = spawn(python, [LAUNCHER, ...args], {
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
      return result;
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

async function runLauncher() {
  await runLauncherArguments([]);
}

async function assertConfiguredMode() {
  const result = await runLauncherArguments(["--mode", "status"]);
  const status = JSON.parse(result.stdout || "{}");
  if (!status.managed) {
    throw new Error(`UNMANAGED_CDP_BROWSER: port ${PORT} is reachable but is not owned by browserctl`);
  }
  if (!status.mode) throw new Error(`MANAGED_BROWSER_MODE_UNKNOWN: port ${PORT}`);
  const configured = loadBrowserPolicy().ports[String(Number(PORT))]?.mode;
  if (configured && status.mode !== configured) {
    throw new Error(
      `MODE_CHANGE_REQUIRES_RESTART: port ${PORT} is ${status.mode}; configured mode is ${configured}`,
    );
  }
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
      `  node tools/browserctl/browserctl.mjs ensure --port ${PORT}\n` +
      `Use browserctl auth for allowlisted login and an explicit recovery restart only for a human challenge. (${e.message})`);
  }
}

/** Start or reuse the policy-configured dedicated Chrome, then return its version.
 *
 * The optional `start` injection exists for tests; production callers should
 * call `ensureChrome()` with no arguments. Concurrent callers share one launch.
 */
export async function ensureChrome({ start = runLauncher, timeoutMs = 15000, pollMs = 250 } = {}) {
  try {
    const version = await assertChrome();
    if (start === runLauncher) await assertConfiguredMode();
    return version;
  }
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
    `Dedicated Chrome did not become ready at ${BASE}. ${lastError?.message || ""}`.trim(),
  );
}

export async function listPages() {
  return (await httpJson("/json/list")).filter((t) => t.type === "page");
}

// A live CDP session over one target's WebSocket.
export class Session {
  constructor(ws, { targetId = null } = {}) {
    this.ws = ws; this.id = 0; this.pending = new Map(); this.events = []; this.targetId = targetId;
  }

  static async open(webSocketDebuggerUrl, { timeoutMs = 10000 } = {}) {
    const endpoint = new URL(webSocketDebuggerUrl);
    const testEndpoint = process.env.CDP_ENABLE_TEST_LEASES === "1" &&
      ![9222, 9223].includes(Number(endpoint.port)) && ["127.0.0.1", "localhost"].includes(endpoint.hostname);
    if (!testEndpoint && (Number(endpoint.port) !== Number(PORT) || ![HOST, "localhost", "127.0.0.1"].includes(endpoint.hostname))) {
      throw new Error("BROWSER_SESSION_CONFLICT: target belongs to a different browser");
    }
    const unlock = testEndpoint ? () => {} : acquireSessionLock(Number(PORT));
    try {
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
    const targetId = /\/devtools\/page\/([^/?#]+)/.exec(webSocketDebuggerUrl)?.[1] || null;
    const s = new Session(ws, { targetId });
    s._unlockSession = testEndpoint ? null : unlock;
    ws.onmessage = (m) => {
      if (s._taskControlError) return;
      const msg = JSON.parse(m.data);
      if (msg.id && s.pending.has(msg.id)) {
        const { resolve, reject } = s.pending.get(msg.id); s.pending.delete(msg.id);
        msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
      } else if (msg.method) {
        s._observeTaskNavigation(msg);
        if (s._taskControlError) return;
        s.events.push(msg);
        for (const w of [...(s._waiters || [])]) if (w.method === msg.method) w.resolve(msg);
        const subs = s._subs || {};
        for (const fn of [...(subs[msg.method] || []), ...(subs["*"] || [])]) {
          try { fn(msg.params, msg.method); } catch (_) { /* subscriber errors must not kill the socket */ }
        }
        // A detached/crashed target keeps its socket open but will never answer
        // another command (an account switch navigating the tab does exactly
        // this). Fail every in-flight call now, with a name, instead of hanging.
        if (msg.method === "Inspector.detached" || msg.method === "Inspector.targetCrashed") {
          const message = `CDP target detached${msg.params?.reason ? `: ${msg.params.reason}` : ""}`;
          if (s._taskControlGuard) s.invalidateTaskControl(new Error(message));
          else s._rejectPending(message);
        }
      }
    };
    const transportFailed = (message) => {
      if (s._taskControlGuard) s.invalidateTaskControl(new Error(message));
      else s._rejectPending(message);
      s._unlockSession?.();
      s._unlockSession = null;
    };
    ws.onclose = () => transportFailed("CDP WebSocket closed");
    ws.onerror = () => transportFailed("CDP WebSocket error");
    return s;
    } catch (error) { unlock(); throw error; }
  }

  _rejectPending(message) {
    const pending = [...this.pending.values()];
    this.pending.clear();
    const error = message instanceof Error ? message : new Error(message);
    for (const { reject } of pending) reject(error);
    for (const waiter of [...(this._waiters || [])]) waiter.reject(error);
  }

  setTaskControlGuard(guard, { exclusiveContext = false, contextScope, initialUrl = null } = {}) {
    if (typeof guard !== "function" || this._taskControlGuard || this._taskControlError) {
      throw new Error("TASK_TAB_GUARD_INVALID: a task guard must be installed exactly once");
    }
    this._taskControlGuard = guard;
    this._taskExclusiveContext = Boolean(exclusiveContext);
    if (contextScope !== undefined && contextScope !== null && contextScope !== "global" && !isRegionalScope(contextScope)) {
      throw this.invalidateTaskControl(new Error("invalid browser context scope"));
    }
    if (contextScope && !exclusiveContext) {
      throw this.invalidateTaskControl(new Error("a context scope requires exclusive ownership"));
    }
    Object.defineProperty(this, "_taskContextScope", { value: contextScope, writable: false });
    this._taskCurrentUrl = initialUrl;
    if (initialUrl) this._assertTaskNavigation(initialUrl);
  }

  _assertTaskNavigation(url) {
    if (!isRegionalScope(this._taskContextScope)) return;
    try {
      const destination = scopeForOrigin(url);
      if (!destination && new URL(url).hostname.startsWith("sellercentral.amazon.")) {
        throw Object.assign(new Error("TASK_TAB_CONTEXT_INVALID: unrecognized Seller Central navigation origin"),
          { code: "TASK_TAB_CONTEXT_INVALID" });
      }
      if (destination) assertContextCovers(this._taskContextScope, { origin: url });
    } catch (error) {
      throw this.invalidateTaskControl(error);
    }
  }

  _observeTaskNavigation(message) {
    if (!this._taskControlGuard) return;
    let url = null;
    if (message.method === "Page.frameNavigated" && !message.params?.frame?.parentId) {
      this._taskMainFrameId = message.params?.frame?.id;
      url = message.params?.frame?.url;
    } else if (message.method === "Page.navigatedWithinDocument"
        && this._taskMainFrameId && message.params?.frameId === this._taskMainFrameId) {
      url = message.params?.url;
    }
    if (!url) return;
    this._taskCurrentUrl = url;
    try { this._assertTaskNavigation(url); } catch { /* invalidation already rejected pending calls */ }
  }

  invalidateTaskControl(cause) {
    if (!this._taskControlError) {
      this._taskControlError = new Error(
        `TASK_TAB_CONTROL_LOST: ${cause?.message || cause || "task ownership is unavailable"}`,
        cause instanceof Error ? { cause } : undefined,
      );
      this._taskControlError.code = "TASK_TAB_CONTROL_LOST";
      this.close();
    }
    return this._taskControlError;
  }

  async assertTaskControl({ exclusiveContext = false, sellerCentral } = {}) {
    if (this._taskControlError) throw this._taskControlError;
    try {
      if (this._unlockSession) assertSessionLock(Number(PORT));
      if (!this._taskControlGuard) throw new Error("session has no task control guard");
      if (exclusiveContext && !this._taskExclusiveContext) {
        throw new Error("session does not hold exclusive browser context");
      }
      if (sellerCentral !== undefined) {
        assertContextCovers(this._taskContextScope ?? (this._taskExclusiveContext ? "global" : null), sellerCentral);
      }
      if (this._taskCurrentUrl) this._assertTaskNavigation(this._taskCurrentUrl);
      if (taskControlCheck.getStore() === this) {
        throw new Error("task control guard must not issue CDP commands");
      }
      const result = await taskControlCheck.run(this, () => this._taskControlGuard({
        exclusiveContext: Boolean(exclusiveContext || this._taskExclusiveContext),
        ...(this._taskContextScope !== undefined ? { contextScope: this._taskContextScope } : {}),
      }));
      if (!result) throw new Error("task control guard did not confirm ownership");
      if (this._taskControlError) throw this._taskControlError;
      return result;
    } catch (error) {
      throw this.invalidateTaskControl(error);
    }
  }

  // Streaming event hook (used by long-running listeners, e.g. the POE endpoint
  // discovery logger). `method` may be "*" for all events.
  subscribe(method, fn) {
    this._subs = this._subs || {};
    (this._subs[method] = this._subs[method] || []).push(fn);
  }

  // Direct commands get a deadline; longer operations can pass their own budget.
  async send(method, params = {}, { timeoutMs = 30000 } = {}) {
    if (this._unlockSession) assertSessionLock(Number(PORT));
    if (this._taskControlError) throw this._taskControlError;
    if (this._taskControlGuard) await this.assertTaskControl();
    if (this._taskControlGuard && method === "Page.navigate" && params.url) {
      this._assertTaskNavigation(params.url);
    }
    if (!this._taskControlGuard && this.targetId && leaseTrackingEnabled()
        && (method.startsWith("Input.") || method === "Page.navigate" || method === "Page.bringToFront")) {
      touchLease({ port: Number(PORT), targetId: this.targetId, kind: "automation" }).catch(() => {});
    }
    const id = ++this.id;
    const result = await new Promise((resolve, reject) => {
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
      try { this.ws.send(JSON.stringify({ id, method, params })); }
      catch (error) {
        const entry = this.pending.get(id);
        this.pending.delete(id);
        entry.reject(error);
      }
    });
    if (this._taskControlGuard) await this.assertTaskControl();
    if (this._taskControlError) throw this._taskControlError;
    try { if (this._unlockSession) assertSessionLock(Number(PORT)); }
    catch (error) { throw this.invalidateTaskControl(error); }
    return result;
  }

  async waitEvent(method, timeoutMs = 20000) {
    if (this._taskControlError) throw this._taskControlError;
    if (this._taskControlGuard) await this.assertTaskControl();
    const hit = this.events.find((e) => e.method === method);
    const event = hit || await new Promise((resolve, reject) => {
      this._waiters = this._waiters || [];
      const done = (fn) => (value) => {
        clearTimeout(timer);
        const index = this._waiters.indexOf(w);
        if (index >= 0) this._waiters.splice(index, 1);
        fn(value);
      };
      const w = { method, resolve: done(resolve), reject: done(reject) };
      const timer = setTimeout(() => w.reject(new Error(`timeout waiting for ${method}`)), timeoutMs);
      this._waiters.push(w);
    });
    if (this._taskControlGuard) await this.assertTaskControl();
    if (this._taskControlError) throw this._taskControlError;
    try { if (this._unlockSession) assertSessionLock(Number(PORT)); }
    catch (error) { throw this.invalidateTaskControl(error); }
    return event;
  }

  close() {
    if (this._leaseHeartbeat) clearInterval(this._leaseHeartbeat);
    if (this._taskHeartbeat) clearInterval(this._taskHeartbeat);
    this._rejectPending(this._taskControlError || "CDP session closed");
    try { this.ws.close(); } catch (_) {}
    this._unlockSession?.();
    this._unlockSession = null;
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
const ACTIVITY_TRACKER = `(()=>{
  if(globalThis.__ewBrowserLeaseTrackerInstalled)return globalThis.__ewBrowserLeaseActivityAt||Date.now();
  Object.defineProperty(globalThis,"__ewBrowserLeaseTrackerInstalled",{value:true,writable:false});
  globalThis.__ewBrowserLeaseActivityAt=Date.now();
  const touch=()=>{globalThis.__ewBrowserLeaseActivityAt=Date.now()};
  for(const name of ["pointerdown","keydown","scroll","focus","pageshow"]){
    addEventListener(name,touch,{capture:true,passive:true});
  }
  document.addEventListener("visibilitychange",touch,{capture:true,passive:true});
  return globalThis.__ewBrowserLeaseActivityAt;
})()`;

// This is input evidence, not proof of a human: CDP input can emit these events
// too. Initialization and page lifecycle only belong to the cleanup tracker.
const INTERACTION_TRACKER = `(()=>{
  if(globalThis.__ewBrowserLeaseInteractionV1)return;
  const state={version:1,startedAt:Date.now(),lastInteractionAt:0};
  Object.defineProperty(globalThis,"__ewBrowserLeaseInteractionV1",{value:state,writable:false});
  const touch=()=>{state.lastInteractionAt=Date.now()};
  for(const name of ["pointerdown","keydown","wheel"]){
    addEventListener(name,touch,{capture:true,passive:true});
  }
})()`;

export async function installLeaseActivityTracker(session) {
  await session.send("Page.enable", {}, { timeoutMs: 10000 });
  await session.send("Page.addScriptToEvaluateOnNewDocument", { source: ACTIVITY_TRACKER }, { timeoutMs: 10000 });
  await evaluate(session, ACTIVITY_TRACKER, 10000);
  await session.send("Page.addScriptToEvaluateOnNewDocument", { source: INTERACTION_TRACKER }, { timeoutMs: 10000 });
  await evaluate(session, INTERACTION_TRACKER, 10000);
}

export async function readLeaseInteraction(session) {
  try {
    const value = await evaluate(session,
      "({...globalThis.__ewBrowserLeaseInteractionV1, targetUrl: location.href})", 10000);
    const targetUrl = typeof value?.targetUrl === "string" ? value.targetUrl : null;
    if (value?.version !== 1 || !Number.isFinite(value.startedAt) || value.startedAt <= 0
        || !Number.isFinite(value.lastInteractionAt)
        || (value.lastInteractionAt !== 0 && value.lastInteractionAt < value.startedAt)) {
      return { ok: false, version: 1, startedAt: null, lastInteractionAt: null, targetUrl };
    }
    return { ok: true, version: 1, startedAt: value.startedAt, lastInteractionAt: value.lastInteractionAt, targetUrl };
  } catch (error) {
    return { ok: false, version: 1, startedAt: null, lastInteractionAt: null, targetUrl: null, error: error.message };
  }
}

export async function readLeaseActivity(session) {
  try {
    const value = await evaluate(session,
      `typeof globalThis.__ewBrowserLeaseActivityAt==="number"?globalThis.__ewBrowserLeaseActivityAt:null`,
      10000);
    return { ok: Number.isFinite(value), value: Number.isFinite(value) ? value : null };
  } catch (error) {
    return { ok: false, value: null, error: error.message };
  }
}

const CREATE_PAGE_OPTIONS = new Set([
  "leaseClass", "owner", "anchorKey", "register", "freshPageReason",
]);

export async function createPage(url, options = {}) {
  const unknown = Object.keys(options).filter((key) => !CREATE_PAGE_OPTIONS.has(key));
  if (unknown.length) {
    throw new Error(`CREATE_PAGE_UNKNOWN_OPTION: ${unknown.join(", ")}`);
  }
  const {
    leaseClass = "background-active", owner = defaultLeaseOwner(), anchorKey = null,
    register = leaseTrackingEnabled(), freshPageReason = null,
  } = options;
  if (register && !anchorKey && !String(freshPageReason || "").trim()) {
    throw new Error(
      "FRESH_PAGE_REASON_REQUIRED: normal workflows must use task-tabs.mjs so steps and retries reuse one target",
    );
  }
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
      if (register) {
        let origin = null;
        try { origin = new URL(url).origin; } catch (_) {}
        await acquireLease({
          port: Number(PORT), targetId, leaseClass, owner, origin, anchorKey,
        });
        await installLeaseActivityTracker(session).catch(() => {});
        if (leaseClass === "background-active") {
          const interval = loadBrowserPolicy().cleanup.heartbeat_interval_ms;
          session._leaseHeartbeat = setInterval(() => {
            touchLease({ port: Number(PORT), targetId, kind: "heartbeat" }).catch(() => {});
          }, interval);
          session._leaseHeartbeat.unref?.();
        }
      }
      return { targetId, session };
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  throw new Error("created target never appeared in the page list");
}

export async function releasePage(targetId, { outcome = "success" } = {}) {
  if (!leaseTrackingEnabled()) return null;
  return releaseLease({ port: Number(PORT), targetId, outcome });
}

export async function closePageImmediately(targetId, { explicit = false, reason = "" } = {}) {
  if (!explicit || !String(reason).trim()) {
    throw new Error("RAW_TAB_CLOSE_REFUSED: explicit authorization and reason are required");
  }
  const response = await fetch(`${BASE}/json/close/${encodeURIComponent(targetId)}`);
  if (!response.ok) throw new Error(`CDP HTTP ${response.status} while closing target`);
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
        }, { timeoutMs: hardTimeoutMs });
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
