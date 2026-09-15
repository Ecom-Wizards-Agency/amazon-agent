import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const runtime = mkdtempSync(join(tmpdir(), "task-tabs-test-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
process.env.CDP_PORT = "9222";
process.env.CDP_ENABLE_TEST_LEASES = "1";

const registry = await import(`../lease-registry.mjs?task-test=${Date.now()}`);
const taskTabs = await import(`../task-tabs.mjs?task-test=${Date.now()}`);
let fakeSequence = 0;

const policy = {
  schema_version: 1,
  cleanup: {
    mode: "audit", adopt_unregistered_tabs: false,
    background_grace_ms: 600_000, interactive_idle_ms: 7_200_000,
    heartbeat_interval_ms: 30_000, heartbeat_stale_ms: 90_000,
    auth_retry_cooldown_ms: 300_000,
  },
  ports: { "9222": { mode: "headed", profile: "/tmp/test", anchors: [
    { key: "US", url: "https://sellercentral.amazon.com/home" },
    { key: "DE", url: "https://sellercentral.amazon.de/home" },
    { key: "AUS", url: "https://sellercentral.amazon.com.au/home" },
  ] } },
};

function fakeCdp({ createDelayMs = 0 } = {}) {
  const sequence = ++fakeSequence;
  const pages = [];
  const sessions = [];
  let created = 0;
  const sessionFor = (targetId) => {
    const session = {
      targetId,
      setTaskControlGuard(guard, options) { this.guard = guard; this.guardOptions = options; },
      async assertTaskControl(options) { return this.guard(options); },
      invalidateTaskControl(error) { this.controlError = error; this.close(); },
      async send(method, params = {}) {
        if (this.controlError) throw this.controlError;
        if (this.guard) await this.assertTaskControl();
        if (method === "Page.navigate") {
          const page = pages.find((entry) => entry.id === targetId);
          if (page) page.url = params.url;
        }
        return {};
      },
      close() {
        this.closed = true;
        if (this._taskHeartbeat) clearInterval(this._taskHeartbeat);
      },
    };
    sessions.push(session);
    return session;
  };
  return {
    pages,
    sessions,
    get created() { return created; },
    ensureChrome: async () => ({}),
    listPages: async () => pages.map((entry) => ({ ...entry })),
    Session: {
      open: async (url) => sessionFor(url.split("/").pop()),
    },
    setDesktopViewport: async () => {},
    installLeaseActivityTracker: async () => {},
    readLeaseInteraction: async () => ({ ok: true, version: 1, startedAt: 1, lastInteractionAt: 0 }),
    createPage: async (url) => {
      if (createDelayMs) await new Promise((resolve) => setTimeout(resolve, createDelayMs));
      created += 1;
      const targetId = `fake-${sequence}-created-${created}`;
      pages.push({
        id: targetId, type: "page", url,
        webSocketDebuggerUrl: `ws://test/devtools/page/${targetId}`,
      });
      return { targetId, session: sessionFor(targetId) };
    },
  };
}

async function acquire(cdp, taskId, extra = {}) {
  return taskTabs.acquireTaskPage({
    port: 9222, taskId, slot: "primary", workflow: "test",
    initialUrl: "https://sellercentral.amazon.com/work",
    exclusiveContext: true, ...extra,
  }, { registry, cdp, policy });
}

test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("stable task ids are deterministic and do not expose long caller keys", () => {
  const key = "/private/client/path/report.csv?merchant=secret";
  const first = taskTabs.taskIdFor("Amazon Reporting", key);
  assert.equal(first, taskTabs.taskIdFor("Amazon Reporting", key));
  assert.match(first, /^amazon-reporting:[a-f0-9]{20}$/);
  assert.equal(first.includes("private"), false);
});

test("an error retry reuses one target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "retry-once");
  await taskTabs.releaseTaskPage(first, { outcome: "error" });
  const second = await acquire(cdp, "retry-once");
  assert.equal(second.targetId, first.targetId);
  assert.equal(second.reused, true);
  assert.equal(cdp.created, 1);
  await taskTabs.releaseTaskPage(second, { outcome: "success" });
});

test("evidence acquisition never replaces a missing owned target", async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "evidence-missing");
  await taskTabs.releaseTaskPage(first, { outcome: "handoff" });
  cdp.pages.length = 0;
  await assert.rejects(acquire(cdp, "evidence-missing", { expectedTargetId: first.targetId }), /EVIDENCE_TARGET_MISMATCH/);
  assert.equal(cdp.created, 1);
});

test("concurrent acquisition creates one target and one controller", { concurrency: false }, async () => {
  const cdp = fakeCdp({ createDelayMs: 30 });
  const attempts = await Promise.allSettled([
    acquire(cdp, "concurrent"),
    acquire(cdp, "concurrent"),
  ]);
  assert.equal(attempts.filter((entry) => entry.status === "fulfilled").length, 1);
  assert.equal(attempts.filter((entry) =>
    entry.status === "rejected" && entry.reason.code === "TASK_TAB_BUSY").length, 1);
  assert.equal(cdp.created, 1);
  const page = attempts.find((entry) => entry.status === "fulfilled").value;
  await taskTabs.releaseTaskPage(page, { outcome: "success" });
});

test("unspecified exclusive context keeps browser-global compatibility", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "context-first");
  await assert.rejects(
    acquire(cdp, "context-second"),
    (error) => error.code === "TASK_TAB_BUSY" && /browser-context-busy/.test(error.message),
  );
  await taskTabs.releaseTaskPage(first, { outcome: "success" });
  const second = await acquire(cdp, "context-second");
  await taskTabs.releaseTaskPage(second, { outcome: "success" });
});

test("managed pages keep independent regional ownership on the same port", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const [na, eu, au] = await Promise.all([
    acquire(cdp, "regional-na", { sellerCentral: { marketplace: "us" } }),
    acquire(cdp, "regional-eu", {
      sellerCentral: { marketplace: "de" }, initialUrl: "https://sellercentral.amazon.de/home",
    }),
    acquire(cdp, "regional-au", {
      sellerCentral: { marketplace: "au" }, initialUrl: "https://sellercentral.amazon.com.au/home",
    }),
  ]);
  try {
    assert.deepEqual([na.contextScope, eu.contextScope, au.contextScope], ["sc:na", "sc:eu", "sc:au"]);
    await assert.rejects(acquire(cdp, "regional-ca-competitor", {
      sellerCentral: { marketplace: "ca" }, initialUrl: "https://sellercentral.amazon.ca/home",
    }), (error) => error.code === "TASK_TAB_BUSY" && error.blockingScope === "sc:na");
    await assert.rejects(acquire(cdp, "regional-uk-competitor", {
      sellerCentral: { marketplace: "uk" }, initialUrl: "https://sellercentral.amazon.co.uk/home",
    }), (error) => error.code === "TASK_TAB_BUSY" && error.blockingScope === "sc:eu");
    for (const page of [na, eu, au]) await page.session.assertTaskControl({ exclusiveContext: true });
    assert.equal(cdp.created, 3);
  } finally {
    for (const page of [na, eu, au]) await taskTabs.releaseTaskPage(page, { outcome: "success" });
  }
});

test("conflicting declared region and initial URL reject before page creation", async () => {
  const cdp = fakeCdp();
  await assert.rejects(acquire(cdp, "regional-origin-conflict", {
    sellerCentral: { marketplace: "de" },
  }), /TASK_TAB_CONTEXT_MISMATCH/);
  assert.equal(cdp.created, 0);
});

test("a stale control token cannot release a reclaimed target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "stale-release");
  const staleToken = first.controlToken;
  await taskTabs.releaseTaskPage(first, { outcome: "error" });
  const second = await acquire(cdp, "stale-release");
  await assert.rejects(registry.releaseTaskTabControl({
    port: 9222, taskId: "stale-release", slot: "primary",
    controlToken: staleToken, outcome: "success", policy,
  }), /TASK_TAB_STALE_CONTROL/);
  const lease = (await registry.listLeases()).find((entry) => entry.targetId === second.targetId);
  assert.equal(lease.class, "background-active");
  await taskTabs.releaseTaskPage(second, { outcome: "success" });
});

test("legacy lease mutation cannot override a controlled task target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const page = await acquire(cdp, "legacy-release-guard");
  await assert.rejects(registry.releaseLease({
    port: 9222, targetId: page.targetId, outcome: "success", policy,
  }), /TASK_TAB_CONTROL_REQUIRED/);
  await assert.rejects(registry.acquireLease({
    port: 9222, targetId: page.targetId, leaseClass: "inspection",
    owner: "legacy", policy,
  }), /TASK_TAB_CONTROL_REQUIRED/);
  await taskTabs.releaseTaskPage(page, { outcome: "success" });
});

test("an explicit second slot is the only way to create a second task target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const primary = await acquire(cdp, "two-slots");
  await taskTabs.releaseTaskPage(primary, { outcome: "handoff" });
  const evidence = await acquire(cdp, "two-slots", {
    slot: "evidence-step-1", exclusiveContext: false,
  });
  assert.notEqual(evidence.targetId, primary.targetId);
  assert.equal(cdp.created, 2);
  await taskTabs.releaseTaskPage(evidence, { outcome: "success" });
});

test("a missing bound target produces exactly one replacement", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "missing-target");
  await taskTabs.releaseTaskPage(first, { outcome: "error" });
  cdp.pages.splice(0, cdp.pages.length);
  const replacement = await acquire(cdp, "missing-target");
  assert.notEqual(replacement.targetId, first.targetId);
  assert.equal(cdp.created, 2);
  await taskTabs.releaseTaskPage(replacement, { outcome: "success" });
});

test("success keeps the task target for the configured grace period", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const page = await acquire(cdp, "success-grace");
  const before = Date.now();
  await taskTabs.releaseTaskPage(page);
  const lease = (await registry.listLeases()).find((entry) => entry.targetId === page.targetId);
  assert.equal(lease.class, "background-success");
  assert.ok(lease.expiresAt >= before + policy.cleanup.background_grace_ms);
});

test("regional task descriptors share stable ids within each mapped region", () => {
  assert.equal(taskTabs.REGION_WORKFLOW, "seller-central-region");
  assert.deepEqual(taskTabs.REGION_ANCHOR_KEYS, { "sc:na": "US", "sc:eu": "DE", "sc:au": "AUS" });
  for (const [marketplace, scope, anchorKey] of [
    ["us", "sc:na", "US"], ["ca", "sc:na", "US"], ["mx", "sc:na", "US"],
    ["de", "sc:eu", "DE"], ["uk", "sc:eu", "DE"], ["au", "sc:au", "AUS"],
  ]) {
    assert.deepEqual(taskTabs.sellerCentralRegionTask({ marketplace }), {
      taskId: taskTabs.taskIdFor(taskTabs.REGION_WORKFLOW, scope),
      workflow: taskTabs.REGION_WORKFLOW, slot: "primary", exclusiveContext: true,
      sellerCentral: { marketplace, origin: undefined }, scope, anchorKey,
    });
  }
  assert.equal(taskTabs.sellerCentralRegionTask({ origin: "https://sellercentral.amazon.de/home" }).scope, "sc:eu");
  for (const descriptor of [{}, { marketplace: "jp" }, { origin: "https://sellercentral.amazon.co.jp" }]) {
    assert.throws(() => taskTabs.sellerCentralRegionTask(descriptor), { code: "REGION_SCOPE_REQUIRED" });
  }
  assert.throws(() => taskTabs.sellerCentralRegionTask({ marketplace: "us", origin: "https://sellercentral.amazon.de" }),
    { code: "TASK_TAB_CONTEXT_MISMATCH" });
});

test("region primary binds a live anchor, parks it, and reuses it without creating a tab", async () => {
  const cdp = fakeCdp();
  const spec = taskTabs.sellerCentralRegionTask({ marketplace: "us" });
  await registry.acquireLease({ port: 9222, targetId: "missing-us-anchor", leaseClass: "anchor", anchorKey: "US", policy });
  const targetId = "live-us-anchor";
  cdp.pages.push({ id: targetId, url: policy.ports["9222"].anchors[0].url,
    webSocketDebuggerUrl: `ws://test/devtools/page/${targetId}` });
  await registry.acquireLease({ port: 9222, targetId, leaseClass: "anchor", anchorKey: "US", policy });
  const first = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
  assert.equal(first.targetId, targetId);
  await assert.rejects(taskTabs.acquireTaskPage(spec, { registry, cdp, policy }), { code: "TASK_TAB_BUSY" });
  await registry.touchTaskTabControl({ ...spec, port: 9222, targetId,
    controlToken: first.controlToken, contextScope: first.contextScope, policy });
  await assert.rejects(registry.acquireLease({ port: 9222, targetId,
    leaseClass: "interactive", owner: "anchor-maintenance", policy }), /TASK_TAB_CONTROL_REQUIRED/);
  let lease = (await registry.listLeases()).find((entry) => entry.targetId === targetId);
  assert.equal(lease.class, "anchor");
  assert.equal(lease.expiresAt, null);
  await first.session.send("Page.navigate", { url: "https://sellercentral.amazon.com/inventory" });
  const state = (await registry.regionTabState(9222)).find((entry) => entry.targetId === targetId);
  assert.equal(state.controllerFresh, true);
  assert.equal(state.boundTaskId, spec.taskId);
  const result = await taskTabs.releaseTaskPage(first);
  assert.equal(result.taskTab.controller, null);
  assert.equal(result.lease.class, "anchor");
  assert.equal(result.lease.expiresAt, null);
  assert.ok(result.lease.lastReleasedAt);
  assert.equal(cdp.pages[0].url, policy.ports["9222"].anchors[0].url);
  const second = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
  assert.equal(second.targetId, targetId);
  assert.equal(cdp.created, 0);
  const before = Date.now();
  const detached = await taskTabs.detachTaskPage(second, { outcome: "blocked" });
  assert.equal(detached.lease.class, "inspection");
  assert.equal(detached.lease.outcome, "blocked");
  assert.equal("anchorKey" in detached.lease, false);
  assert.equal("taskId" in detached.lease, false);
  assert.equal(detached.taskTab.targetId, null);
  assert.equal(detached.taskTab.controller, null);
  assert.ok(detached.lease.expiresAt >= before + policy.cleanup.interactive_idle_ms);
  await assert.rejects(registry.detachTaskTab({ ...spec, port: 9222, controlToken: second.controlToken, policy }),
    /TASK_TAB_STALE_CONTROL/);
  await registry.removeLease({ port: 9222, targetId: "missing-us-anchor" });
  const third = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
  assert.notEqual(third.targetId, targetId);
  assert.equal(cdp.created, 1);
  lease = (await registry.listLeases()).find((entry) => entry.targetId === third.targetId);
  assert.equal(lease.class, "anchor");
  assert.equal(lease.owner, "browserctl:anchor");
  assert.equal(lease.anchorKey, "US");
  assert.equal(lease.url, policy.ports["9222"].anchors[0].url);
  await taskTabs.releaseTaskPage(third);
});

test("region failures detach automatically and additional slots remain ordinary task tabs", async () => {
  const cdp = fakeCdp();
  const spec = taskTabs.sellerCentralRegionTask({ marketplace: "de" });
  for (const outcome of ["error", "inspection", "blocked", "auth-required", "operation-failed"]) {
    const page = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
    let unlocked = false;
    page._unlockSession = () => { unlocked = true; };
    const released = await taskTabs.releaseTaskPage(page, { outcome });
    assert.equal(released.lease.class, "inspection");
    assert.equal(released.lease.outcome, outcome);
    assert.equal(released.taskTab.targetId, null);
    assert.equal(unlocked, true);
    assert.equal(page._released, true);
  }
  assert.equal(cdp.created, 5);
  const extra = await taskTabs.acquireTaskPage({ ...spec, slot: "evidence" }, { registry, cdp, policy });
  const released = await taskTabs.releaseTaskPage(extra);
  assert.equal(released.lease.class, "background-success");
});

test("a failed home navigation detaches the region tab", async () => {
  const cdp = fakeCdp();
  const spec = taskTabs.sellerCentralRegionTask({ marketplace: "au" });
  const page = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
  page.session.send = async () => ({ errorText: "net::ERR_FAILED" });
  await assert.rejects(taskTabs.releaseTaskPage(page), /REGION_PARK_FAILED/);
  const lease = (await registry.listLeases()).find((entry) => entry.targetId === page.targetId);
  assert.equal(lease.class, "inspection");
  assert.equal(lease.outcome, "error");
});

test("transient region setup failures preserve the live anchor across retries", async () => {
  const cdp = fakeCdp();
  const spec = taskTabs.sellerCentralRegionTask({ marketplace: "au" });
  const first = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
  await taskTabs.releaseTaskPage(first);
  for (const step of ["viewport", "tracker", "control"]) {
    cdp.setDesktopViewport = async () => {
      if (step === "viewport") throw new Error("transient setup");
    };
    cdp.installLeaseActivityTracker = async (session) => {
      if (step === "tracker") throw new Error("transient setup");
      session.assertTaskControl = async () => { throw new Error("transient setup"); };
    };
    await assert.rejects(taskTabs.acquireTaskPage(spec, { registry, cdp, policy }), /transient setup/);
    const record = (await registry.listTaskTabs()).find((entry) => entry.taskId === spec.taskId);
    const lease = (await registry.listLeases()).find((entry) => entry.targetId === first.targetId);
    assert.equal(record.targetId, first.targetId);
    assert.equal(record.controller, null);
    assert.equal(lease.class, "anchor");
    assert.equal(lease.expiresAt, null);
    assert.equal(cdp.sessions.at(-1).closed, true);
    assert.equal(cdp.sessions.at(-1)._taskHeartbeat._destroyed, true);
  }
  cdp.setDesktopViewport = async () => {};
  cdp.installLeaseActivityTracker = async () => {};
  const retried = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
  assert.equal(retried.targetId, first.targetId);
  assert.equal(cdp.created, 1);
  await taskTabs.releaseTaskPage(retried);
});

test("a timed-out initial region navigation preserves a target that reached its region", async () => {
  const cdp = fakeCdp();
  const spec = taskTabs.sellerCentralRegionTask({ marketplace: "de" });
  cdp.installLeaseActivityTracker = async (session) => {
    const send = session.send.bind(session);
    session.send = async (...args) => {
      await send(...args);
      throw new Error("navigation timeout");
    };
  };
  await assert.rejects(taskTabs.acquireTaskPage(spec, { registry, cdp, policy }), /navigation timeout/);
  const targetId = cdp.pages[0].id;
  const lease = (await registry.listLeases()).find((entry) => entry.targetId === targetId);
  assert.equal(lease.class, "anchor");
  cdp.installLeaseActivityTracker = async () => {};
  const retried = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
  assert.equal(retried.targetId, targetId);
  assert.equal(cdp.created, 1);
  await taskTabs.releaseTaskPage(retried);
});

test("missing region parking configuration still releases every handle resource", async () => {
  for (const ports of [{}, { "9222": {} }]) {
    const cdp = fakeCdp();
    const spec = taskTabs.sellerCentralRegionTask({ marketplace: "au" });
    const page = await taskTabs.acquireTaskPage(spec, { registry, cdp, policy });
    let unlocked = 0;
    page._unlockSession = () => { unlocked++; };
    page._policy = { ...policy, ports };
    await assert.rejects(taskTabs.releaseTaskPage(page), { code: "REGION_ANCHOR_REQUIRED" });
    assert.equal(page._released, true);
    assert.equal(page.session.closed, true);
    assert.equal(page.session._taskHeartbeat._destroyed, true);
    assert.equal(unlocked, 1);
    assert.equal(await taskTabs.releaseTaskPage(page), null);
    const record = (await registry.listTaskTabs()).find((entry) => entry.taskId === spec.taskId);
    assert.equal(record.controller, null);
    assert.equal(record.targetId, null);
    const lease = (await registry.listLeases()).find((entry) => entry.targetId === page.targetId);
    assert.equal(lease.class, "inspection");
  }
});

test("ordinary workflows and additional region slots cannot bind anchors", async () => {
  for (const [taskId, workflow, slot] of [
    ["anchor-refusal", "test", "primary"],
    ["anchor-refusal-slot", taskTabs.REGION_WORKFLOW, "evidence"],
  ]) {
    const spec = { port: 9222, taskId, workflow, slot, policy };
    const reservation = await registry.reserveTaskTab(spec);
    await registry.acquireLease({ port: 9222, targetId: taskId, leaseClass: "anchor", anchorKey: "DE", policy });
    await assert.rejects(registry.bindReservedTaskTab({ ...spec, targetId: taskId,
      reservationToken: reservation.reservationToken, controlToken: reservation.controlToken }), /TASK_TAB_ANCHOR_REFUSED/);
    await registry.abandonTaskTabReservation({ ...spec, controlToken: reservation.controlToken });
  }
});

test("removing a closed target also removes its task binding", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const page = await acquire(cdp, "binding-cleanup");
  await taskTabs.releaseTaskPage(page, { outcome: "success" });
  await registry.removeLease({ port: 9222, targetId: page.targetId });
  assert.equal((await registry.listTaskTabs()).some((entry) =>
    entry.taskId === "binding-cleanup"), false);
});


test("global region claims keep the anchor through switcher navigation and regional reacquisition", async () => {
  const { Session } = await import("../../report-fetcher/cdp.mjs");
  for (const lease of await registry.listLeases()) {
    await registry.removeLease({ port: lease.port, targetId: lease.targetId });
  }
  for (const [marketplace, anchorKey, home] of [
    ["de", "DE", "https://sellercentral.amazon.de/home"],
    ["au", "AUS", "https://sellercentral.amazon.com.au/home"],
  ]) {
    const cdp = fakeCdp();
    const regional = taskTabs.sellerCentralRegionTask({ marketplace });
    const global = taskTabs.sellerCentralRegionTask({ marketplace, claimScope: "global" });
    assert.equal(global.taskId, regional.taskId);
    assert.equal(global.anchorKey, anchorKey);
    const targetId = `global-${marketplace}-anchor`;
    cdp.pages.push({ id: targetId, url: home, webSocketDebuggerUrl: `ws://test/devtools/page/${targetId}` });
    await registry.acquireLease({ port: 9222, targetId, leaseClass: "anchor", anchorKey, policy });
    cdp.readLeaseInteraction = async () => ({ ok: false });
    for (const spec of [regional, global, regional, global]) {
      const handle = await taskTabs.acquireTaskPage({ ...spec, allowOperatorActivity: true,
        ...(spec.claimScope ? { initialUrl: "https://sellercentral.amazon.com/account-switcher" } : {}),
      }, { registry, cdp, policy });
      try {
        assert.equal(handle.targetId, targetId);
        assert.equal(handle.contextScope, spec.claimScope || regional.scope);
        assert.equal(handle.session.guardOptions.contextScope, handle.contextScope);
        assert.equal(handle.session.guardOptions.exclusiveContext, true);
        if (spec.claimScope) {
          const switcher = "https://sellercentral.amazon.com/account-switcher";
          const guard = Object.create(Session.prototype);
          guard.invalidateTaskControl = error => { throw error; };
          guard.setTaskControlGuard(async () => {}, handle.session.guardOptions);
          assert.doesNotThrow(() => guard._assertTaskNavigation(switcher));
          await handle.session.send("Page.navigate", { url: switcher });
          await handle.session.assertTaskControl();
          await assert.rejects(acquire(cdp, `global-blocked-${marketplace}`, {
            sellerCentral: { marketplace: "us" },
          }), { code: "TASK_TAB_BUSY" });
        }
      } finally {
        const result = await taskTabs.releaseTaskPage(handle);
        assert.equal(result.lease.class, "anchor");
        assert.equal(result.lease.anchorKey, anchorKey);
      }
      assert.equal(cdp.pages[0].url, home);
    }
    assert.equal(cdp.created, 0);
  }
});
