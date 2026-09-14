import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const runtime = mkdtempSync(join(tmpdir(), "task-coordination-test-"));
const statePath = join(runtime, "leases.json");
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
process.env.CDP_ENABLE_TEST_LEASES = "1";
process.env.CDP_PORT = "9222";
const registry = await import(`../lease-registry.mjs?coordination-test=${Date.now()}`);
const taskTabs = await import("../task-tabs.mjs");
const { cleanupPort } = await import("../browserctl.mjs");
const { Session } = await import("../../report-fetcher/cdp.mjs");
const policy = {
  cleanup: {
    heartbeat_interval_ms: 30_000, heartbeat_stale_ms: 90_000,
    background_grace_ms: 600_000, interactive_idle_ms: 7_200_000,
  },
};
const start = 1_000_000;
const state = () => JSON.parse(readFileSync(statePath, "utf8"));
function changeState(change) {
  const value = state();
  change(value);
  writeFileSync(statePath, JSON.stringify(value));
}
const spec = (taskId, extra = {}) => ({
  port: 9222, taskId, workflow: "coordination-test", owner: "test-owner",
  exclusiveContext: true, now: start, policy, ...extra,
});

async function create(taskId, extra = {}) {
  const args = spec(taskId, extra);
  const reservation = await registry.reserveTaskTab(args);
  assert.equal(reservation.kind, "create");
  const targetId = `${taskId}-target`;
  await registry.bindReservedTaskTab({
    ...args, targetId, reservationToken: reservation.reservationToken,
    controlToken: reservation.controlToken,
  });
  return { ...args, targetId, controlToken: reservation.controlToken };
}

async function retry(taskId, now, interaction = {}, extra = {}) {
  const args = spec(taskId, { now, ...extra });
  const probe = await registry.reserveTaskTab(args);
  assert.equal(probe.kind, "probe");
  return registry.reserveTaskTab({
    ...args,
    interactionProbe: {
      ...probe.probeToken, ok: true, version: 1,
      startedAt: start, lastInteractionAt: 0, ...interaction,
    },
  });
}

test.beforeEach(() => rmSync(statePath, { force: true }));
test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("atomic renewal advances controller, claim and active lease together", async () => {
  const handle = await create("renew");
  const renewed = await registry.touchTaskTabControl({ ...handle, now: start + 10_000 });
  assert.equal(renewed.controller.heartbeatAt, start + 10_000);
  const current = state();
  assert.equal(current.context_claims["9222"].expiresAt, renewed.controller.expiresAt);
  assert.equal(current.leases[`9222:${handle.targetId}`].heartbeatAt, start + 10_000);
});

test("an unexpired context claim cannot be replaced even by its own expired task", async () => {
  const handle = await create("claim-outlives-controller");
  changeState((value) => { Object.values(value.task_tabs)[0].controller.expiresAt = start + 10; });
  const claim = state().context_claims["9222"];
  const attempt = await registry.reserveTaskTab({ ...handle, now: start + 20 });
  assert.equal(attempt.reason, "browser-context-busy");
  assert.deepEqual(state().context_claims["9222"], claim);
});

for (const loss of ["missing", "stolen", "expired"]) {
  test(`${loss} context claim cannot partially renew task control`, async () => {
    const handle = await create(`claim-${loss}`);
    changeState((value) => {
      if (loss === "missing") delete value.context_claims["9222"];
      if (loss === "stolen") value.context_claims["9222"].controlToken = "another-controller";
      if (loss === "expired") value.context_claims["9222"].expiresAt = start + 5_000;
    });
    const before = state();
    await assert.rejects(
      registry.touchTaskTabControl({ ...handle, now: start + 10_000 }),
      /TASK_TAB_CONTROL_LOST/,
    );
    assert.deepEqual(state(), before);
  });
}

test("expired task control cannot revive even when nobody has reclaimed it", async () => {
  const handle = await create("expired-control");
  const before = state();
  await assert.rejects(
    registry.touchTaskTabControl({ ...handle, now: start + policy.cleanup.heartbeat_stale_ms }),
    /TASK_TAB_CONTROL_LOST/,
  );
  assert.deepEqual(state(), before);
});

test("control assertion is read-only and rejects a different target", async () => {
  const handle = await create("assert-control");
  const before = state();
  await registry.assertTaskTabControl({ ...handle, now: start + 1 });
  assert.deepEqual(state(), before);
  await assert.rejects(
    registry.assertTaskTabControl({ ...handle, targetId: "different-target", now: start + 1 }),
    /TASK_TAB_CONTROL_LOST/,
  );
  assert.deepEqual(state(), before);
});

test("Seller Central claims serialize one port while other services and ports remain usable", async () => {
  const first = await create("context-first");
  const busy = await registry.reserveTaskTab(spec("context-second", { now: start + 1 }));
  assert.equal(busy.kind, "busy");
  assert.equal(busy.reason, "browser-context-busy");
  await create("figma", { exclusiveContext: false, now: start + 1 });
  await create("other-browser", { port: 9223, now: start + 1 });
  await registry.releaseTaskTabControl({ ...first, outcome: "success", now: start + 2 });
  const next = await registry.reserveTaskTab(spec("context-second", { now: start + 3 }));
  assert.equal(next.kind, "create");
});

test("retained-page probe grants no ownership and preserves the expired controller", async () => {
  const handle = await create("probe-no-ownership");
  const before = state();
  const probe = await registry.reserveTaskTab(spec(handle.taskId, { now: start + 90_001 }));
  assert.equal(probe.kind, "probe");
  assert.equal(probe.targetId, handle.targetId);
  assert.ok(probe.probeToken);
  assert.equal(probe.controlToken, undefined);
  assert.deepEqual(state().task_tabs, before.task_tabs);
});

test("release, reuse, automated activity and crash can retry the same target", async () => {
  const first = await create("crash-retry");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  const second = await retry(first.taskId, start + 20);
  assert.equal(second.kind, "reuse");
  assert.equal(second.targetId, first.targetId);
  const active = Object.values(state().task_tabs)[0];
  assert.equal(active.releasedAt, null);
  await registry.touchLease({ port: 9222, targetId: first.targetId, kind: "activity", now: start + 30, policy });
  await registry.transitionMissedHeartbeat({ port: 9222, targetId: first.targetId, now: start + 100_000, policy });
  const retained = state().leases[`9222:${first.targetId}`];
  assert.equal(retained.class, "inspection");
  assert.equal(retained.expiresAt, start + 100_000 + policy.cleanup.interactive_idle_ms);
  const third = await retry(first.taskId, start + 100_001);
  assert.equal(third.kind, "reuse");
  assert.equal(third.targetId, first.targetId);
  await assert.rejects(
    registry.releaseTaskTabControl({ ...first, outcome: "success", now: start + 100_002 }),
    /TASK_TAB_STALE_CONTROL|TASK_TAB_CONTROL_LOST/,
  );
  assert.equal(state().leases[`9222:${first.targetId}`].class, "background-active");
});

test("restoring retention measurement does not manufacture operator interaction", async () => {
  const first = await create("measurement-retry");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  await registry.restartActivityMeasurement({ port: 9222, targetId: first.targetId, now: start + 20, policy });
  const second = await retry(first.taskId, start + 30);
  assert.equal(second.kind, "reuse");
  assert.equal(second.targetId, first.targetId);
});

test("interaction after the current release blocks retained-page reuse", async () => {
  const first = await create("operator-release");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  const before = state().task_tabs;
  const attempt = await retry(first.taskId, start + 30, { lastInteractionAt: start + 20 });
  assert.equal(attempt.kind, "busy");
  assert.equal(attempt.reason, "observed-interaction");
  assert.deepEqual(state().task_tabs, before);
});

test("activity during the latest controller epoch does not block its crash retry", async () => {
  const first = await create("controller-boundary");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  assert.equal((await retry(first.taskId, start + 20)).kind, "reuse");
  const attempt = await retry(first.taskId, start + 100_000, { lastInteractionAt: start + 30 });
  assert.equal(attempt.kind, "reuse");
});

test("interaction after controller expiry blocks crash retry", async () => {
  const first = await create("operator-expiry");
  const attempt = await retry(first.taskId, start + 100_000, { lastInteractionAt: start + 95_000 });
  assert.equal(attempt.kind, "busy");
  assert.equal(attempt.reason, "observed-interaction");
});

test("legacy activity is uncertainty rather than proven operator interaction", async () => {
  const first = await create("legacy-uncertainty");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  changeState((value) => {
    delete Object.values(value.task_tabs)[0].interactionVersion;
    delete value.leases[`9222:${first.targetId}`].interactionVersion;
    value.leases[`9222:${first.targetId}`].lastActivityAt = start + 20;
  });
  const attempt = await retry(first.taskId, start + 30);
  assert.equal(attempt.kind, "busy");
  assert.equal(attempt.reason, "interaction-evidence-unavailable");
  assert.equal(Object.values(state().task_tabs)[0].controller, null);
});

for (const [name, evidence] of [
  ["failed probe", { ok: false }],
  ["tracker installed after release", { startedAt: start + 20 }],
]) {
  test(`${name} cannot be mistaken for an idle retained page`, async () => {
    const first = await create("uncertain-probe");
    await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
    const attempt = await retry(first.taskId, start + 30, evidence);
    assert.equal(attempt.kind, "busy");
    assert.equal(attempt.reason, "interaction-evidence-unavailable");
    assert.equal(Object.values(state().task_tabs)[0].controller, null);
  });
}

test("cleanup changing a lease invalidates an in-flight reacquisition probe", async () => {
  const first = await create("stale-probe");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  const args = spec(first.taskId, { now: start + 30 });
  const probe = await registry.reserveTaskTab(args);
  assert.equal(probe.kind, "probe");
  await registry.restartActivityMeasurement({ port: 9222, targetId: first.targetId, now: start + 20, policy });
  const attempt = await registry.reserveTaskTab({
    ...args,
    interactionProbe: {
      ...probe.probeToken, ok: true, version: 1,
      startedAt: start, lastInteractionAt: 0,
    },
  });
  assert.equal(attempt.kind, "probe");
  assert.notEqual(attempt.probeToken.leaseGeneration, probe.probeToken.leaseGeneration);
  assert.equal(Object.values(state().task_tabs)[0].controller, null);
});

test("two accepted copies of one probe can grant only one controller", async () => {
  const first = await create("competing-probe");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  const args = spec(first.taskId, { now: start + 30 });
  const probe = await registry.reserveTaskTab(args);
  const interactionProbe = {
    ...probe.probeToken, ok: true, version: 1,
    startedAt: start, lastInteractionAt: 0,
  };
  const attempts = await Promise.all([
    registry.reserveTaskTab({ ...args, interactionProbe }),
    registry.reserveTaskTab({ ...args, interactionProbe }),
  ]);
  assert.equal(attempts.filter((entry) => entry.kind === "reuse").length, 1);
  assert.equal(attempts.filter((entry) => entry.kind === "busy").length, 1);
});

test("an explicit operator-activity override reclaims the same inspected target", async () => {
  const first = await create("explicit-reclaim");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  assert.equal((await retry(first.taskId, start + 30, { lastInteractionAt: start + 20 })).kind, "busy");
  const accepted = await retry(first.taskId, start + 40,
    { lastInteractionAt: start + 20 }, { allowOperatorActivity: true });
  assert.equal(accepted.kind, "reuse");
  assert.equal(accepted.targetId, first.targetId);
  assert.equal(Object.values(state().task_tabs)[0].releasedAt, null);
});

for (const failure of ["connection timeout", "missing connection endpoint", "target listing failure"]) {
  test(`an interaction override cannot replace a target after ${failure}`, async () => {
    let reservations = 0;
    let replacements = 0;
    const fakeRegistry = {
      async reserveTaskTab() {
        reservations++;
        return reservations === 1
          ? { kind: "probe", targetId: "retained", probeToken: { targetId: "retained" } }
          : { kind: "reuse", targetId: "retained", controlToken: "token" };
      },
      async prepareMissingTaskTabReplacement() {
        replacements++;
        throw new Error("replacement must not be reached");
      },
      async abandonTaskTabReservation() {},
    };
    const cdp = {
      async ensureChrome() {},
      async listPages() {
        if (failure === "target listing failure") throw new Error("listing unavailable");
        return [{ id: "retained", ...(failure === "missing connection endpoint"
          ? {} : { webSocketDebuggerUrl: "ws://retained" }) }];
      },
      Session: { async open() { throw new Error("connection timeout"); } },
    };
    await assert.rejects(taskTabs.acquireTaskPage({
      taskId: "unavailable-retained", workflow: "test", allowOperatorActivity: true,
    }, { registry: fakeRegistry, cdp, policy }), /TASK_TAB_TARGET_UNAVAILABLE/);
    assert.equal(replacements, 0);
    assert.equal(reservations, 1);
  });
}

test("registry I/O failure after an interaction probe closes its connection", async () => {
  let reservations = 0;
  let closed = 0;
  const fakeRegistry = {
    async reserveTaskTab() {
      if (++reservations === 1) return { kind: "probe", targetId: "retained", probeToken: { targetId: "retained" } };
      throw new Error("EIO registry unavailable");
    },
  };
  const cdp = {
    async ensureChrome() {},
    async listPages() { return [{ id: "retained", webSocketDebuggerUrl: "ws://retained" }]; },
    Session: { async open() { return { close() { closed++; } }; } },
    async readLeaseInteraction() { return { ok: true, version: 1, startedAt: start, lastInteractionAt: 0 }; },
  };
  await assert.rejects(taskTabs.acquireTaskPage({
    taskId: "probe-io-failure", workflow: "test",
  }, { registry: fakeRegistry, cdp, policy }), /EIO registry unavailable/);
  assert.equal(closed, 1);
});

test("renewal queued before expiry cannot revive control after acquiring the lock", async () => {
  const realNow = Date.now;
  const acquiredAt = realNow();
  const handle = await create("queued-renewal", { now: acquiredAt });
  changeState((value) => {
    Object.values(value.task_tabs)[0].controller.expiresAt = acquiredAt + 100;
    value.context_claims["9222"].expiresAt = acquiredAt + 100;
  });
  const before = state();
  const lockPath = join(runtime, ".leases.lock");
  mkdirSync(lockPath);
  let clock = acquiredAt;
  Date.now = () => clock;
  try {
    const pending = registry.touchTaskTabControl({ ...handle, now: undefined });
    // The call has entered asynchronous lock acquisition. Advance the clock
    // before releasing that lock without depending on scheduler timing.
    clock = acquiredAt + 200;
    rmSync(lockPath, { recursive: true, force: true });
    await assert.rejects(pending, /TASK_TAB_CONTROL_LOST/);
    assert.deepEqual(state(), before);
  } finally {
    Date.now = realNow;
    rmSync(lockPath, { recursive: true, force: true });
  }
});

test("a failed periodic renewal permanently invalidates the acquired session", async () => {
  let renewals = 0;
  let closed = 0;
  let notifyClosed;
  const disconnected = new Promise((resolve) => { notifyClosed = resolve; });
  const session = new Session({ close() { closed++; notifyClosed(); } }, { targetId: "heartbeat-target" });
  const fakeRegistry = {
    async reserveTaskTab() { return { kind: "create", reservationToken: "reservation", controlToken: "controller" }; },
    async bindReservedTaskTab() {},
    async assertTaskTabControl() { return { controller: { token: "controller" } }; },
    async touchTaskTabControl() { renewals++; throw new Error("EIO renewal unavailable"); },
    async releaseTaskTabControl() {},
  };
  const cdp = {
    async ensureChrome() {},
    async listPages() { return []; },
    async createPage() { return { targetId: "heartbeat-target", session }; },
    async setDesktopViewport() {},
    async installLeaseActivityTracker() {},
  };
  const handle = await taskTabs.acquireTaskPage({
    taskId: "heartbeat-failure", workflow: "test", initialUrl: null,
  }, { registry: fakeRegistry, cdp, policy: { cleanup: { ...policy.cleanup, heartbeat_interval_ms: 5 } } });
  let timeout;
  try {
    await Promise.race([
      disconnected,
      new Promise((_, reject) => { timeout = setTimeout(() => reject(new Error("heartbeat did not invalidate session")), 1000); }),
    ]);
    assert.equal(renewals, 1);
    assert.equal(closed, 1);
    await assert.rejects(handle.session.assertTaskControl(), /TASK_TAB_CONTROL_LOST/);
    await assert.rejects(handle.session.send("Runtime.evaluate", { expression: "1" }), /TASK_TAB_CONTROL_LOST/);
  } finally {
    clearTimeout(timeout);
    await taskTabs.releaseTaskPage(handle, { outcome: "error" });
  }
});

test("cleanup persists sampled input before tracker restoration and later document reset", async () => {
  const first = await create("cleanup-persistence");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  let reads = 0;
  let closed = 0;
  const cdp = {
    async assertChrome() {},
    async listPages() { return [{ id: first.targetId, url: "https://sellercentral.amazon.com/work", webSocketDebuggerUrl: "ws://retained" }]; },
    Session: { async open() { return { close() { closed++; } }; } },
    async readLeaseActivity() { return ++reads === 1 ? { ok: false } : { ok: true, value: start + 30 }; },
    async readLeaseInteraction() { return { ok: true, version: 1, startedAt: start, lastInteractionAt: start + 20 }; },
    async installLeaseActivityTracker() {},
  };
  const result = await cleanupPort(9222, {
    policy: { ...policy, ports: { "9222": { mode: "headed", anchors: [] } } },
    cdp, auditOnly: true, maintainAnchors: false,
    managedStatus: { managed: true, mode: "headed" }, now: start + 30,
  });
  assert.ok(result.actions.some((entry) => entry.action === "activity-tracker-restored"));
  const retained = state().leases[`9222:${first.targetId}`];
  assert.equal(retained.lastObservedInteractionAt, start + 20);
  assert.ok(retained.expiresAt >= start + 30 + policy.cleanup.interactive_idle_ms);
  assert.equal(closed, 1);
  const attempt = await retry(first.taskId, start + 50,
    { startedAt: start + 40, lastInteractionAt: 0 });
  assert.equal(attempt.kind, "busy");
  assert.equal(state().leases[`9222:${first.targetId}`].lastObservedInteractionAt, start + 20);
});

test("cleanup retains observed input even if the retention tracker cannot be restored", async () => {
  const first = await create("failed-tracker-with-input");
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 10 });
  const result = await cleanupPort(9222, {
    policy: { ...policy, ports: { "9222": { mode: "headed", anchors: [] } } },
    auditOnly: true, maintainAnchors: false, managedStatus: { managed: true, mode: "headed" }, now: start + 30,
    cdp: {
      async assertChrome() {},
      async listPages() { return [{ id: first.targetId, url: "https://sellercentral.amazon.com/work", webSocketDebuggerUrl: "ws://retained" }]; },
      Session: { async open() { return { close() {} }; } },
      async readLeaseActivity() { return { ok: false }; },
      async readLeaseInteraction() { return { ok: true, version: 1, startedAt: start, lastInteractionAt: start + 20 }; },
      async installLeaseActivityTracker() { throw new Error("tracker restoration failed"); },
    },
  });
  assert.equal(result.actions[0].reason, "activity-unavailable");
  assert.equal(state().leases[`9222:${first.targetId}`].lastObservedInteractionAt, start + 20);
});
