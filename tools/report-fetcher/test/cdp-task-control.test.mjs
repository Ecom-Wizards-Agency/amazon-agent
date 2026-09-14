// Explicit isolated ephemeral WebSocket fixtures; managed port mismatches still reject.
process.env.CDP_ENABLE_TEST_LEASES = "1";
import assert from "node:assert/strict";
import test from "node:test";
import vm from "node:vm";
import { Session, installLeaseActivityTracker, readLeaseInteraction } from "../cdp.mjs";
import { switchAccount, waitFor, waitForAppPage } from "../sc-account.mjs";
import { startFakeCdp } from "./helpers/fake-cdp.mjs";

function fakeSession({ reply = true } = {}) {
  const commands = [];
  const ws = { closed: false, close() { this.closed = true; }, send(payload) {
    const command = JSON.parse(payload);
    commands.push(command);
    if (reply) queueMicrotask(() => respond(command.id));
  } };
  const session = new Session(ws);
  function respond(id, result = { value: "private account data" }) {
    const pending = session.pending.get(id);
    session.pending.delete(id);
    pending?.resolve(result);
  }
  return { session, ws, commands, respond };
}

test("lost control prevents dispatch and permanently invalidates the session", async () => {
  const { session, ws, commands } = fakeSession();
  session.setTaskControlGuard(async () => { throw new Error("expired"); });
  await assert.rejects(session.send("Runtime.evaluate"), { code: "TASK_TAB_CONTROL_LOST" });
  await assert.rejects(session.send("Page.navigate"), { code: "TASK_TAB_CONTROL_LOST" });
  assert.equal(commands.length, 0);
  assert.equal(ws.closed, true);
});

test("control is checked again before returning an in-flight result", async () => {
  const { session, ws, commands } = fakeSession();
  let checks = 0;
  session.setTaskControlGuard(async () => ++checks === 1);
  await assert.rejects(session.send("Runtime.evaluate"), { code: "TASK_TAB_CONTROL_LOST" });
  assert.equal(commands.length, 1);
  assert.equal(checks, 2);
  assert.equal(ws.closed, true);
});

test("heartbeat invalidation rejects pending commands with the stable error code", async () => {
  const { session, ws } = fakeSession({ reply: false });
  session.setTaskControlGuard(async () => true);
  const pending = session.send("Runtime.evaluate");
  const rejected = assert.rejects(pending, { code: "TASK_TAB_CONTROL_LOST" });
  await new Promise(setImmediate);
  assert.equal(session.pending.size, 1);
  session.invalidateTaskControl(new Error("heartbeat failed"));
  await rejected;
  assert.equal(session.pending.size, 0);
  assert.equal(ws.closed, true);
});

test("a detached managed target permanently invalidates its session", async () => {
  const fake = await startFakeCdp({ targets: [{ id: "guarded", url: "about:blank",
    behavior: { detachOn: "Runtime.enable" } }] });
  try {
    const session = await Session.open(fake.wsUrl("guarded"));
    session.setTaskControlGuard(async () => true);
    await assert.rejects(session.send("Runtime.enable"), { code: "TASK_TAB_CONTROL_LOST" });
    await assert.rejects(session.send("Runtime.evaluate"), { code: "TASK_TAB_CONTROL_LOST" });
    assert.equal(fake.sent.length, 1);
  } finally { await fake.close(); }
});

test("exclusive sessions pass the requirement on every guard check", async () => {
  const { session } = fakeSession();
  const requirements = [];
  session.setTaskControlGuard(async (requirement) => {
    requirements.push(requirement); return true;
  }, { exclusiveContext: true });
  await session.send("Runtime.evaluate");
  assert.deepEqual(requirements, [{ exclusiveContext: true }, { exclusiveContext: true }]);
  session.close();
});

test("regional ownership is immutable and passed to every registry assertion", async () => {
  const { session } = fakeSession();
  const requirements = [];
  session.setTaskControlGuard(async (requirement) => { requirements.push(requirement); return true; },
    { exclusiveContext: true, contextScope: "sc:eu", initialUrl: "https://sellercentral.amazon.de/home" });
  await session.assertTaskControl({ exclusiveContext: true,
    sellerCentral: { marketplace: "fr", origin: "https://sellercentral.amazon.de" } });
  await session.send("Page.navigate", { url: "https://sellercentral.amazon.co.uk/home" });
  assert.throws(() => { session._taskContextScope = "sc:na"; }, TypeError);
  assert.deepEqual(requirements, Array(3).fill({ exclusiveContext: true, contextScope: "sc:eu" }));
  session.close();
});

test("a regional session cannot navigate or switch another region before dispatch", async () => {
  for (const action of [
    (session) => session.send("Page.navigate", { url: "https://sellercentral.amazon.de/home" }),
    (session) => session.send("Page.navigate", { url: "https://sellercentral.amazon.co.nz/home" }),
    (session) => switchAccount(session, "https://sellercentral.amazon.com", { marketplace: "de" }),
    (session) => switchAccount(session, "https://sellercentral.amazon.com", { marketplaceLabel: "Germany" }),
    (session) => session.assertTaskControl({ sellerCentral: { origin: "https://sellercentral.amazon.com.br" } }),
  ]) {
    const { session, commands, ws } = fakeSession();
    session.setTaskControlGuard(async () => true, { exclusiveContext: true, contextScope: "sc:na", initialUrl: "about:blank" });
    await assert.rejects(action(session), { code: "TASK_TAB_CONTROL_LOST" });
    assert.equal(commands.length, 0);
    assert.equal(ws.closed, true);
  }
});

test("a conflicting main-frame redirect rejects pending responses and later commands", async () => {
  const { session, respond, ws, commands } = fakeSession({ reply: false });
  session.setTaskControlGuard(async () => true,
    { exclusiveContext: true, contextScope: "sc:na", initialUrl: "https://sellercentral.amazon.com/home" });
  const pending = session.send("Runtime.evaluate");
  const rejected = assert.rejects(pending, { code: "TASK_TAB_CONTROL_LOST" });
  await new Promise(setImmediate);
  session._observeTaskNavigation({ method: "Page.frameNavigated",
    params: { frame: { id: "main", url: "https://sellercentral.amazon.de/home" } } });
  respond(commands[0].id, { value: "must be discarded" });
  await rejected;
  await assert.rejects(session.send("Input.insertText", { text: "must not dispatch" }), { code: "TASK_TAB_CONTROL_LOST" });
  assert.equal(commands.length, 1);
  assert.equal(ws.closed, true);
});

test("transport discards subscriptions and event history after a conflicting redirect", async () => {
  const fake = await startFakeCdp({ targets: [{ id: "regional", url: "about:blank" }] });
  try {
    const session = await Session.open(fake.wsUrl("regional"));
    session.setTaskControlGuard(async () => true, { exclusiveContext: true, contextScope: "sc:na", initialUrl: "about:blank" });
    const seen = [];
    session.subscribe("*", (params, method) => seen.push({ params, method }));
    session.ws.onmessage({ data: JSON.stringify({ method: "Page.frameNavigated",
      params: { frame: { id: "main", url: "https://sellercentral.amazon.de/home" } } }) });
    session.ws.onmessage({ data: JSON.stringify({ method: "Network.responseReceived", params: { status: 200 } }) });
    assert.equal(seen.length, 0);
    assert.equal(session.events.length, 0);
    await assert.rejects(session.send("Runtime.enable"), { code: "TASK_TAB_CONTROL_LOST" });
  } finally { await fake.close(); }
});

test("authentication navigation and foreign subframes preserve the held regional claim", async () => {
  const { session } = fakeSession();
  session.setTaskControlGuard(async () => true,
    { exclusiveContext: true, contextScope: "sc:eu", initialUrl: "https://sellercentral.amazon.de/home" });
  session._observeTaskNavigation({ method: "Page.frameNavigated",
    params: { frame: { id: "child", parentId: "main", url: "https://sellercentral.amazon.com" } } });
  await session.send("Page.navigate", { url: "https://www.amazon.de/ap/signin" });
  session._observeTaskNavigation({ method: "Page.frameNavigated",
    params: { frame: { id: "main", url: "https://www.amazon.de/ap/signin" } } });
  session._observeTaskNavigation({ method: "Page.frameNavigated",
    params: { frame: { id: "main", url: "https://sellercentral.amazon.fr/home" } } });
  await session.assertTaskControl({ sellerCentral: { marketplace: "fr", origin: "https://sellercentral.amazon.fr" } });
  assert.equal(session._taskContextScope, "sc:eu");
  session.close();
});

test("retained targets cannot start a regional session from another group's page", () => {
  const { session, ws } = fakeSession();
  assert.throws(() => session.setTaskControlGuard(async () => true,
    { exclusiveContext: true, contextScope: "sc:au", initialUrl: "https://sellercentral.amazon.com" }),
  { code: "TASK_TAB_CONTROL_LOST" });
  assert.equal(ws.closed, true);
});

test("cached events cannot be accepted after controller expiry or invalidation", async () => {
  for (const invalidate of [false, true]) {
    const { session } = fakeSession();
    session.events.push({ method: "Page.loadEventFired", params: { timestamp: 1 } });
    session.setTaskControlGuard(async () => false);
    if (invalidate) session.invalidateTaskControl(new Error("claim replaced"));
    await assert.rejects(session.waitEvent("Page.loadEventFired"), { code: "TASK_TAB_CONTROL_LOST" });
  }
});

test("ownership loss immediately rejects event waiters and removes their timeout", async () => {
  const { session } = fakeSession();
  session.setTaskControlGuard(async () => true);
  const waiting = session.waitEvent("Page.loadEventFired", 60_000);
  const rejected = assert.rejects(waiting, { code: "TASK_TAB_CONTROL_LOST" });
  await new Promise(setImmediate);
  assert.equal(session._waiters.length, 1);
  session.invalidateTaskControl(new Error("claim replaced"));
  await rejected;
  assert.equal(session._waiters.length, 0);
});

test("events are revalidated before acceptance and successful waiters are removed", async () => {
  const { session } = fakeSession();
  let checks = 0;
  session.setTaskControlGuard(async () => ++checks === 1);
  const waiting = session.waitEvent("Page.loadEventFired", 60_000);
  const rejected = assert.rejects(waiting, { code: "TASK_TAB_CONTROL_LOST" });
  await new Promise(setImmediate);
  session._waiters[0].resolve({ method: "Page.loadEventFired", params: {} });
  await rejected;
  assert.equal(session._waiters.length, 0);
  assert.equal(checks, 2);
});

test("an ownership guard cannot recursively issue CDP commands", async () => {
  const { session, commands } = fakeSession();
  session.setTaskControlGuard(() => session.send("Runtime.evaluate"));
  await assert.rejects(session.send("Runtime.evaluate"), { code: "TASK_TAB_CONTROL_LOST" });
  assert.equal(commands.length, 0);
});

test("unguarded cleanup sessions retain their existing CDP access", async () => {
  const { session } = fakeSession();
  assert.deepEqual(await session.send("Runtime.evaluate"), { value: "private account data" });
  session.close();
});

test("account navigation waits propagate ownership loss without retrying it as navigation", async () => {
  for (const wait of [
    (session) => waitFor(session, "true", "page"),
    (session) => waitForAppPage(session),
  ]) {
    const { session, commands } = fakeSession();
    session.setTaskControlGuard(async () => { throw new Error("browser context ownership expired"); });
    await assert.rejects(wait(session), { code: "TASK_TAB_CONTROL_LOST" });
    assert.equal(commands.length, 0);
  }
});

test("managed account switching rejects unguarded and nonexclusive sessions before CDP", async () => {
  const previousPort = process.env.CDP_PORT;
  process.env.CDP_PORT = "9222";
  try {
    for (const guarded of [false, true]) {
      const { session, commands } = fakeSession();
      if (guarded) session.setTaskControlGuard(async () => true);
      await assert.rejects(switchAccount(session, "https://sellercentral.amazon.com", {}),
        { code: "TASK_TAB_CONTROL_LOST" });
      assert.equal(commands.length, 0);
    }
  } finally {
    if (previousPort === undefined) delete process.env.CDP_PORT;
    else process.env.CDP_PORT = previousPort;
  }
});

function trackerPage() {
  let now = 1000;
  const listeners = new Map();
  const add = (name, fn) => {
    if (!listeners.has(name)) listeners.set(name, []);
    listeners.get(name).push(fn);
  };
  const context = vm.createContext({ Date: { now: () => now }, addEventListener: add,
    document: { addEventListener: add }, location: { href: "https://sellercentral.amazon.de/home" } });
  const session = { async send(method, params) {
    if (method === "Runtime.evaluate") {
      return { result: { value: vm.runInContext(params.expression, context) } };
    }
    return {};
  }, close() {} };
  return { session, context, emit(name) {
    now += 100;
    for (const listener of listeners.get(name) || []) listener({ isTrusted: true });
  } };
}

test("interaction tracker installs beside an old tracker without manufacturing input", async () => {
  const page = trackerPage();
  vm.runInContext("globalThis.__ewBrowserLeaseTrackerInstalled=true;globalThis.__ewBrowserLeaseActivityAt=500", page.context);
  assert.equal((await readLeaseInteraction(page.session)).ok, false);
  await installLeaseActivityTracker(page.session);
  assert.deepEqual(await readLeaseInteraction(page.session),
    { ok: true, version: 1, startedAt: 1000, lastInteractionAt: 0, targetUrl: "https://sellercentral.amazon.de/home" });
  for (const name of ["focus", "pageshow", "visibilitychange", "scroll"]) page.emit(name);
  assert.equal((await readLeaseInteraction(page.session)).lastInteractionAt, 0);
  for (const name of ["pointerdown", "keydown", "wheel"]) {
    page.emit(name);
    const before = await readLeaseInteraction(page.session);
    assert.ok(before.lastInteractionAt > before.startedAt);
    await installLeaseActivityTracker(page.session);
    assert.deepEqual(await readLeaseInteraction(page.session), before);
  }
});

test("malformed or failed interaction probes remain unknown", async () => {
  const page = trackerPage();
  assert.deepEqual(await readLeaseInteraction(page.session), { ok: false, version: 1,
    startedAt: null, lastInteractionAt: null, targetUrl: "https://sellercentral.amazon.de/home" });
  vm.runInContext("globalThis.__ewBrowserLeaseInteractionV1={version:1,startedAt:2000,lastInteractionAt:1000}", page.context);
  assert.equal((await readLeaseInteraction(page.session)).ok, false);
  const result = await readLeaseInteraction({ send: async () => { throw new Error("detached"); }, close() {} });
  assert.equal(result.ok, false);
  assert.match(result.error, /detached/);
});
