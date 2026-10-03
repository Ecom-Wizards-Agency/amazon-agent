import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

// Attended tools on 9222 take turns on a busy Seller Central region; Grimoire's
// 9223 keeps the single attempt. Real lease registry in a temporary runtime,
// fake CDP.
const runtime = mkdtempSync(join(tmpdir(), "region-wait-test-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
process.env.CDP_PORT = "9222";
process.env.CDP_ENABLE_TEST_LEASES = "1";
delete process.env.WIZARDS_AI_MODE;
delete process.env.AMAZON_BROWSER_REGION_WAIT_MS;

const registry = await import(`../lease-registry.mjs?region-wait=${Date.now()}`);
const taskTabs = await import(`../task-tabs.mjs?region-wait=${Date.now()}`);
const { regionHolder, describeRegionHolder } = await import("../region-holder.mjs");
const TASK_TABS = fileURLToPath(new URL("../task-tabs.mjs", import.meta.url));
const HOLDER_OWNER = "region-step.mjs:4242";

const policy = {
  schema_version: 1,
  cleanup: {
    mode: "audit", adopt_unregistered_tabs: false,
    background_grace_ms: 600_000, interactive_idle_ms: 7_200_000,
    heartbeat_interval_ms: 30_000, heartbeat_stale_ms: 90_000,
    auth_retry_cooldown_ms: 300_000,
  },
  ports: { "9222": { mode: "headed", profile: "/tmp/test", anchors: [] } },
};

let fakeSequence = 0;
function fakeCdp() {
  const sequence = ++fakeSequence;
  const pages = [];
  let created = 0;
  const sessionFor = (targetId) => ({
    targetId,
    setTaskControlGuard(guard) { this.guard = guard; },
    async assertTaskControl(options) { return this.guard(options); },
    invalidateTaskControl() { this.close(); },
    async send() { return {}; },
    close() { if (this._taskHeartbeat) clearInterval(this._taskHeartbeat); },
  });
  return {
    ensureChrome: async () => ({}),
    listPages: async () => pages.map((entry) => ({ ...entry })),
    Session: { open: async (url) => sessionFor(url.split("/").pop()) },
    setDesktopViewport: async () => {},
    installLeaseActivityTracker: async () => {},
    readLeaseInteraction: async () => ({ ok: true, version: 1, startedAt: 1, lastInteractionAt: 0 }),
    closePageImmediately: async () => {},
    createPage: async (url) => {
      const targetId = `region-${sequence}-${++created}`;
      pages.push({ id: targetId, type: "page", url, webSocketDebuggerUrl: `ws://test/devtools/page/${targetId}` });
      return { targetId, session: sessionFor(targetId) };
    },
  };
}

/** The registry, counting reservation attempts. */
function countingRegistry() {
  const counted = { ...registry, attempts: 0 };
  counted.reserveTaskTab = (spec) => { counted.attempts++; return registry.reserveTaskTab(spec); };
  return counted;
}

const spec = (taskId, extra = {}) => ({
  port: Number(process.env.CDP_PORT), taskId, slot: "primary", workflow: "test",
  initialUrl: "https://sellercentral.amazon.com/work", exclusiveContext: true,
  sellerCentral: { marketplace: "us" }, ...extra,
});

async function withEnv(vars, fn) {
  const saved = Object.fromEntries(Object.keys(vars).map((key) => [key, process.env[key]]));
  for (const [key, value] of Object.entries(vars)) {
    if (value === undefined) delete process.env[key]; else process.env[key] = value;
  }
  try { return await fn(); } finally {
    for (const [key, value] of Object.entries(saved)) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
  }
}

test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("on 9222 a busy region is waited out, onWaiting runs once with token-free holder facts", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const holder = await taskTabs.acquireTaskPage(spec("holder-free", { owner: HOLDER_OWNER }), { registry, cdp, policy });
  const counted = countingRegistry();
  const waits = [];
  try {
    const page = await taskTabs.acquireTaskPageWithRegionWait(spec("waiter-free"), {
      waitMs: 10_000, pollMs: 20,
      onWaiting: (event) => {
        waits.push(event);
        setTimeout(() => taskTabs.releaseTaskPage(holder, { outcome: "success" }), 80);
      },
    }, { registry: counted, cdp, policy });
    assert.equal(page.contextScope, "sc:na");
    assert.equal(waits.length, 1, "onWaiting runs once");
    assert.ok(counted.attempts >= 3, `retried (${counted.attempts} attempts)`);
    const [{ holder: facts, waitMs, since, until }] = waits;
    assert.equal(waitMs, 10_000);
    assert.equal(until - since, 10_000);
    assert.deepEqual({ ...facts, heartbeat_age_s: typeof facts.heartbeat_age_s }, {
      blocking_scope: "sc:na", owner: HOLDER_OWNER, workflow: "test", task_id: "holder-free", heartbeat_age_s: "number",
    });
    assert.equal(JSON.stringify(waits).includes(holder.controlToken), false, "the holder control token is never passed on");
    await taskTabs.releaseTaskPage(page, { outcome: "success" });
  } finally {
    await taskTabs.releaseTaskPage(holder, { outcome: "success" }).catch(() => {});
  }
});

test("on 9222 a region held past the bound rethrows TASK_TAB_BUSY with holder facts and leaves no claim", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const holder = await taskTabs.acquireTaskPage(spec("holder-bound", { owner: HOLDER_OWNER }), { registry, cdp, policy });
  const waits = [];
  try {
    const started = Date.now();
    const error = await taskTabs.acquireTaskPageWithRegionWait(spec("waiter-bound"), {
      waitMs: 150, pollMs: 20, onWaiting: (event) => waits.push(event),
    }, { registry, cdp, policy }).then(() => assert.fail("acquired a held region"), (caught) => caught);
    assert.equal(error.code, "TASK_TAB_BUSY");
    assert.equal(error.blockingScope, "sc:na");
    assert.ok(error.waitedMs >= 150 && Date.now() - started >= 150, `waited ${error.waitedMs} ms`);
    assert.equal(error.holder.owner, HOLDER_OWNER);
    assert.equal(error.holder.task_id, "holder-bound");
    assert.match(error.message, /^TASK_TAB_BUSY: browser-context-busy: sc:na on port 9222; Seller Central sc:na is held by region-step\.mjs:4242 \(test\), heartbeat \d+ s ago; waited 0 s$/);
    assert.equal(JSON.stringify({ message: error.message, holder: error.holder }).includes(holder.controlToken), false);
    assert.equal(waits.length, 1);
    const tasks = await registry.listTaskTabs();
    assert.equal(tasks.find((entry) => entry.taskId === "waiter-bound"), undefined, "a busy answer creates no task record");
    assert.equal(tasks.find((entry) => entry.taskId === "holder-bound").controller.owner, HOLDER_OWNER);
  } finally {
    await taskTabs.releaseTaskPage(holder, { outcome: "success" });
  }
});

test("9223 and WIZARDS_AI_MODE make the single acquireTaskPage attempt, with no wait and no holder lookup", { concurrency: false }, async () => {
  for (const [label, env] of [["9223", { CDP_PORT: "9223" }], ["WIZARDS_AI_MODE", { WIZARDS_AI_MODE: "1" }]]) {
    await withEnv(env, async () => {
      const cdp = fakeCdp();
      const holder = await taskTabs.acquireTaskPage(spec(`holder-once-${label}`, { owner: HOLDER_OWNER }), { registry, cdp, policy });
      const counted = countingRegistry();
      counted.listTaskTabs = async () => assert.fail("no holder lookup");
      const waits = [];
      try {
        const plain = await taskTabs.acquireTaskPage(spec(`plain-${label}`), { registry, cdp, policy })
          .then(() => assert.fail("acquired a held region"), (caught) => caught);
        const started = Date.now();
        const error = await taskTabs.acquireTaskPageWithRegionWait(spec(`waiter-once-${label}`), {
          waitMs: 5_000, pollMs: 20, onWaiting: (event) => waits.push(event),
        }, { registry: counted, cdp, policy }).then(() => assert.fail("acquired a held region"), (caught) => caught);
        assert.ok(Date.now() - started < 2_000, `${label}: failed at once`);
        assert.equal(counted.attempts, 1, `${label}: one attempt`);
        assert.equal(waits.length, 0);
        assert.equal(error.code, "TASK_TAB_BUSY");
        assert.equal(error.message, plain.message, `${label}: the plain busy error`);
        assert.equal(error.holder, undefined);
      } finally {
        await taskTabs.releaseTaskPage(holder, { outcome: "success" });
      }
    });
  }
});

test("other busy answers fail at once on 9222", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const holder = await taskTabs.acquireTaskPage(spec("same-task", { owner: HOLDER_OWNER }), { registry, cdp, policy });
  const counted = countingRegistry();
  try {
    // The same task held by another controller carries no blocking scope.
    const error = await taskTabs.acquireTaskPageWithRegionWait(spec("same-task"), {
      waitMs: 5_000, pollMs: 20, onWaiting: () => assert.fail("no wait"),
    }, { registry: counted, cdp, policy }).then(() => assert.fail("acquired a held task"), (caught) => caught);
    assert.equal(error.code, "TASK_TAB_BUSY");
    assert.equal(error.blockingScope, null);
    assert.equal(counted.attempts, 1);
  } finally {
    await taskTabs.releaseTaskPage(holder, { outcome: "success" });
  }
});

test("the wait bound comes from AMAZON_BROWSER_REGION_WAIT_MS, else 120 s, and rejects nonsense", () => {
  assert.equal(taskTabs.regionWaitMs({}), 120_000);
  assert.equal(taskTabs.regionWaitMs({ AMAZON_BROWSER_REGION_WAIT_MS: "" }), 120_000);
  assert.equal(taskTabs.regionWaitMs({ AMAZON_BROWSER_REGION_WAIT_MS: "0" }), 0);
  assert.equal(taskTabs.regionWaitMs({ AMAZON_BROWSER_REGION_WAIT_MS: "45000" }), 45_000);
  for (const bad of ["-1", "1.5", "abc", "1e400"]) {
    assert.throws(() => taskTabs.regionWaitMs({ AMAZON_BROWSER_REGION_WAIT_MS: bad }), { code: "TASK_TAB_WAIT_INVALID" }, bad);
  }
});

test("maxWaitMs caps the configured bound", { concurrency: false }, async () => {
  await withEnv({ AMAZON_BROWSER_REGION_WAIT_MS: "600000" }, async () => {
    const fake = { reserveTaskTab: async () => ({ kind: "busy", reason: "browser-context-busy", blockingScope: "sc:eu", blockingTask: null }), listTaskTabs: async () => [] };
    const waits = [];
    const error = await taskTabs.acquireTaskPageWithRegionWait(spec("capped", { sellerCentral: { marketplace: "de" }, initialUrl: "https://sellercentral.amazon.de/home" }), {
      maxWaitMs: 60, pollMs: 20, onWaiting: (event) => waits.push(event),
    }, { registry: fake, cdp: fakeCdp(), policy }).then(() => assert.fail("acquired"), (caught) => caught);
    assert.equal(waits[0].waitMs, 60);
    assert.equal(error.code, "TASK_TAB_BUSY");
    assert.deepEqual(error.holder, { blocking_scope: "sc:eu", owner: null, workflow: null, task_id: null, heartbeat_age_s: null });
    assert.match(error.message, /Seller Central sc:eu is held by another controller; waited 0 s$/);
  });
});

test("holder facts never copy the control token", async () => {
  const token = "00000000-0000-4000-8000-00000000c0de";
  const now = 1_800_000_000_000;
  const fake = { listTaskTabs: async () => [{ key: "9222:held:primary", taskId: "held", workflow: "seller-central-region",
    controller: { token, owner: HOLDER_OWNER, heartbeatAt: now - 4_000, expiresAt: now + 60_000 } }] };
  const facts = await regionHolder(fake, { blockingScope: "sc:na", blockingTask: "9222:held:primary" }, now);
  assert.deepEqual(facts, { blocking_scope: "sc:na", owner: HOLDER_OWNER, workflow: "seller-central-region", task_id: "held", heartbeat_age_s: 4 });
  assert.equal(JSON.stringify(facts).includes(token), false);
  assert.equal(describeRegionHolder(facts), "Seller Central sc:na is held by region-step.mjs:4242 (seller-central-region)");
  const failing = { listTaskTabs: async () => { throw new Error("registry unreadable"); } };
  assert.deepEqual(await regionHolder(failing, { blockingScope: "global", blockingTask: "k" }),
    { blocking_scope: "global", owner: null, workflow: null, task_id: null, heartbeat_age_s: null });
});

test("the wait keeps the process alive and logs one stderr line", () => {
  // A top-level await on an unref'd timer would exit 13 before the bound passes.
  const script = `
    const { acquireTaskPageWithRegionWait } = await import(${JSON.stringify(TASK_TABS)});
    const registry = { reserveTaskTab: async () => ({ kind: "busy", reason: "browser-context-busy", blockingScope: "sc:na", blockingTask: null }), listTaskTabs: async () => [] };
    const cdp = { ensureChrome: async () => ({}) };
    try {
      await acquireTaskPageWithRegionWait({ port: 9222, taskId: "child", workflow: "test", exclusiveContext: true, sellerCentral: { marketplace: "us" } },
        { waitMs: 300, pollMs: 50 }, { registry, cdp, policy: ${JSON.stringify(policy)} });
    } catch (error) { console.log(JSON.stringify({ code: error.code, waitedMs: error.waitedMs })); }`;
  const child = spawnSync(process.execPath, ["--input-type=module", "-e", script], {
    encoding: "utf8", timeout: 20_000,
    env: { ...process.env, CDP_PORT: "9222", WIZARDS_AI_MODE: "" },
  });
  assert.equal(child.status, 0, child.stderr);
  const result = JSON.parse(child.stdout.trim());
  assert.equal(result.code, "TASK_TAB_BUSY");
  assert.ok(result.waitedMs >= 300, `waited ${result.waitedMs} ms`);
  const lines = child.stderr.trim().split("\n").filter(Boolean);
  assert.deepEqual(lines, ["Seller Central sc:na is held by another controller; waiting up to 0 s for it"]);
});
