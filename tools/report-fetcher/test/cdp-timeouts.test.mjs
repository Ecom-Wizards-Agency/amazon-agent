process.env.CDP_ENABLE_TEST_LEASES = "1";
/*
 * Regression tests for the 13.08.2026 account-chooser stall: a live socket
 * whose target stops answering must reject within its budget, never hang the
 * process. See the incident notes in the PR that introduced this file.
 */
import assert from "node:assert/strict";
import test from "node:test";
import { spawn } from "node:child_process";

import { Session, evaluate } from "../cdp.mjs";
import { startFakeCdp } from "./helpers/fake-cdp.mjs";

test("evaluate rejects within budget when Runtime.enable is never answered", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "https://sellercentral.amazon.com/home", behavior: { neverReply: ["Runtime.enable"] } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    const t0 = Date.now();
    // budget 100ms -> hard timer at 5100ms; pre-fix this hung forever
    await assert.rejects(evaluate(s, "1+1", 100), /timed out/);
    const elapsed = Date.now() - t0;
    assert.ok(elapsed < 9000, `rejected in ${elapsed} ms, expected well under 9 s`);
  } finally {
    await fake.close();
  }
});

test("Session.send honors an opt-in timeoutMs", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { neverReply: ["Foo.bar"] } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    const t0 = Date.now();
    await assert.rejects(s.send("Foo.bar", {}, { timeoutMs: 300 }), /CDP Foo\.bar timed out after 300 ms/);
    assert.ok(Date.now() - t0 < 2000);
    s.close();
  } finally {
    await fake.close();
  }
});

test("Session.send without timeoutMs still waits for a slow reply", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { delayMs: 1200, results: { "Foo.slow": { ok: true } } } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    const r = await s.send("Foo.slow");
    assert.deepEqual(r, { ok: true });
    s.close();
  } finally {
    await fake.close();
  }
});

test("Session.open rejects when the WebSocket handshake stalls", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { stallUpgrade: true } }],
  });
  try {
    await assert.rejects(Session.open(fake.wsUrl("T1"), { timeoutMs: 300 }), /handshake timed out/);
  } finally {
    await fake.close();
  }
});

test("Session.open rejects when the target refuses the upgrade", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { refuseUpgrade: true } }],
  });
  try {
    await assert.rejects(Session.open(fake.wsUrl("T1")), /failed to open/);
  } finally {
    await fake.close();
  }
});

test("Inspector.detached rejects every pending send with a named reason", { concurrency: false }, async () => {
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: "about:blank", behavior: { detachOn: "Runtime.enable" } }],
  });
  try {
    const s = await Session.open(fake.wsUrl("T1"));
    await assert.rejects(s.send("Runtime.enable"), /CDP target detached: target_closed/);
    s.close();
  } finally {
    await fake.close();
  }
});

test("unanswered direct sends default to 30 seconds and clear their keepalive", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "setInterval"] });
  const clearKeepalive = t.mock.method(globalThis, "clearInterval");
  const s = new Session({ send() {}, close() {} });
  t.after(() => s.close());
  const pending = s.send("Page.enable");
  const rejected = assert.rejects(pending, /CDP Page\.enable timed out after 30000 ms/);
  t.mock.timers.tick(29999);
  assert.equal(s.pending.size, 1);
  assert.equal(clearKeepalive.mock.callCount(), 0);
  t.mock.timers.tick(1);
  await rejected;
  assert.equal(s.pending.size, 0);
  assert.equal(clearKeepalive.mock.callCount(), 1);
});

test("an explicit longer send timeout survives the default deadline", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "setInterval"] });
  const s = new Session({ send() {}, close() {} });
  t.after(() => s.close());
  const rejected = assert.rejects(s.send("Foo.long", {}, { timeoutMs: 60000 }),
    /CDP Foo\.long timed out after 60000 ms/);
  t.mock.timers.tick(30000);
  assert.equal(s.pending.size, 1);
  t.mock.timers.tick(30000);
  await rejected;
  assert.equal(s.pending.size, 0);
});

test("evaluate can return after the direct-send deadline", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "setInterval"] });
  let dispatched;
  const evaluating = new Promise((resolve) => { dispatched = resolve; });
  const s = new Session({ close() {}, send(payload) {
    const command = JSON.parse(payload);
    if (command.method === "Runtime.enable") {
      const entry = s.pending.get(command.id);
      s.pending.delete(command.id);
      entry.resolve({});
    } else dispatched(command);
  } });
  t.after(() => s.close());
  const result = evaluate(s, "longPromise()", 120000);
  const command = await evaluating;
  assert.equal(command.params.timeout, 120000);
  t.mock.timers.tick(30001);
  assert.equal(s.pending.size, 1);
  const entry = s.pending.get(command.id);
  s.pending.delete(command.id);
  entry.resolve({ result: { value: "finished" } });
  assert.equal(await result, "finished");
});

test("an unanswered evaluate keeps its own hard deadline and closes the session", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout", "setInterval"] });
  let dispatched;
  const evaluating = new Promise((resolve) => { dispatched = resolve; });
  const ws = { closed: false, close() { this.closed = true; }, send(payload) {
    const command = JSON.parse(payload);
    if (command.method === "Runtime.enable") {
      const entry = s.pending.get(command.id);
      s.pending.delete(command.id);
      entry.resolve({});
    } else dispatched();
  } };
  const s = new Session(ws);
  t.after(() => s.close());
  const rejected = assert.rejects(evaluate(s, "neverSettles()", 60000),
    /CDP Runtime\.evaluate timed out after 65000 ms/);
  await evaluating;
  t.mock.timers.tick(64999);
  assert.equal(s.pending.size, 1);
  assert.equal(ws.closed, false);
  t.mock.timers.tick(1);
  await rejected;
  assert.equal(s.pending.size, 0);
  assert.equal(ws.closed, true);
});

test("a timed-out direct send lets the process exit without closing the session", async () => {
  // Accelerate only the 30-second default in the child; the keepalive is real.
  const source = `
    import { Session } from ${JSON.stringify(new URL("../cdp.mjs", import.meta.url).href)};
    const originalTimeout = globalThis.setTimeout;
    globalThis.setTimeout = (fn, ms, ...args) => originalTimeout(fn, ms === 30000 ? 20 : ms, ...args);
    const s = new Session({ send() {}, close() {} });
    try { await s.send("Foo.missing"); process.exitCode = 1; }
    catch (error) {
      if (!/CDP Foo.missing timed out after 30000 ms/.test(error.message)) throw error;
      if (s.pending.size) throw new Error("pending command leaked");
    }
  `;
  const child = spawn(process.execPath, ["--input-type=module", "-e", source], {
    stdio: ["ignore", "ignore", "pipe"],
  });
  let stderr = "";
  child.stderr.on("data", (chunk) => { stderr += chunk; });
  let killed = false;
  const watchdog = setTimeout(() => { killed = true; child.kill("SIGKILL"); }, 3000);
  try {
    const code = await new Promise((resolve, reject) => {
      child.on("error", reject);
      child.on("close", resolve);
    });
    assert.equal(killed, false, "timeout left a referenced keepalive running");
    assert.equal(code, 0, stderr);
  } finally {
    clearTimeout(watchdog);
    if (child.exitCode === null) child.kill("SIGKILL");
  }
});
