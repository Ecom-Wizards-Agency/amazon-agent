import assert from "node:assert/strict";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const runtime = mkdtempSync(join(tmpdir(), "browserctl-test-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");

const registry = await import(`../lease-registry.mjs?test=${Date.now()}`);
const controller = await import(`../browserctl.mjs?test=${Date.now()}`);
const policyModule = await import(`../policy.mjs?test=${Date.now()}`);

const policy = {
  schema_version: 1,
  cleanup: {
    mode: "audit",
    background_grace_ms: 600_000,
    interactive_idle_ms: 7_200_000,
    heartbeat_interval_ms: 30_000,
    heartbeat_stale_ms: 90_000,
    auth_retry_cooldown_ms: 300_000,
  },
  ports: {
    "9222": {
      mode: "headed", profile: "/tmp/profile-9222", start_url: "https://sellercentral.amazon.com/home",
      anchors: [
        { key: "US", url: "https://sellercentral.amazon.com/home", accepted_paths: ["/home", "/amazonsell/business"], auth_origins: ["https://www.amazon.com"] },
        { key: "DE", url: "https://sellercentral.amazon.de/home", accepted_paths: ["/home", "/amazonsell/business"], auth_origins: ["https://www.amazon.de"] },
        { key: "AUS", url: "https://sellercentral.amazon.com.au/home", accepted_paths: ["/home", "/amazonsell/business"], auth_origins: ["https://www.amazon.com.au"] },
      ],
    },
  },
};

test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("successful background leases cannot close before ten minutes", { concurrency: false }, async () => {
  await registry.acquireLease({
    port: 9222, targetId: "success", leaseClass: "background-active", owner: "test", now: 1, policy,
  });
  const released = await registry.releaseLease({ port: 9222, targetId: "success", outcome: "success", now: 1000, policy });
  assert.equal(released.class, "background-success");
  assert.equal(released.expiresAt, 601_000);
  assert.equal(await registry.claimExpiredLease({ port: 9222, targetId: "success", expectedUpdatedAt: released.updatedAt, now: 600_999 }), null);
  assert.equal((await registry.claimExpiredLease({ port: 9222, targetId: "success", expectedUpdatedAt: released.updatedAt, now: 601_000 })).state, "closing");
  await registry.removeLease({ port: 9222, targetId: "success" });
});

test("activity promotes a released background page to a two-hour interactive lease", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "active", owner: "test", now: 1, policy });
  await registry.releaseLease({ port: 9222, targetId: "active", outcome: "success", now: 1000, policy });
  const touched = await registry.touchLease({ port: 9222, targetId: "active", kind: "activity", now: 2000, policy });
  assert.equal(touched.class, "interactive");
  assert.equal(touched.expiresAt, 7_202_000);
  await registry.removeLease({ port: 9222, targetId: "active" });
});

test("a missed heartbeat becomes inspection instead of closing", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "stalled", owner: "test", now: 10, policy });
  const before = await registry.transitionMissedHeartbeat({ port: 9222, targetId: "stalled", now: 90_010, policy });
  assert.equal(before.class, "background-active");
  const after = await registry.transitionMissedHeartbeat({ port: 9222, targetId: "stalled", now: 90_011, policy });
  assert.equal(after.class, "inspection");
  assert.equal(after.outcome, "heartbeat-lost");
  assert.equal(after.expiresAt, 7_290_011);
  await registry.removeLease({ port: 9222, targetId: "stalled" });
});

test("concurrent writers retain every lease", { concurrency: false }, async () => {
  await Promise.all(Array.from({ length: 20 }, (_, index) => registry.acquireLease({
    port: 9222, targetId: `concurrent-${index}`, owner: "test", now: index + 1, policy,
  })));
  const ids = new Set((await registry.listLeases()).map((lease) => lease.targetId));
  for (let index = 0; index < 20; index++) assert.equal(ids.has(`concurrent-${index}`), true);
  await Promise.all(Array.from({ length: 20 }, (_, index) =>
    registry.removeLease({ port: 9222, targetId: `concurrent-${index}` })));
});

test("authentication retries obey the configured cooldown", { concurrency: false }, async () => {
  const before = await registry.authAttemptStatus({
    port: 9222, targetId: "auth-target", routeId: "flatfilepro",
    now: 1000, cooldownMs: 300_000,
  });
  assert.equal(before.allowed, true);
  await registry.recordAuthAttempt({
    port: 9222, targetId: "auth-target", routeId: "flatfilepro", now: 1000,
  });
  const during = await registry.authAttemptStatus({
    port: 9222, targetId: "auth-target", routeId: "flatfilepro",
    now: 300_999, cooldownMs: 300_000,
  });
  assert.equal(during.allowed, false);
  assert.equal(during.retryAt, 301_000);
  const after = await registry.authAttemptStatus({
    port: 9222, targetId: "auth-target", routeId: "flatfilepro",
    now: 301_000, cooldownMs: 300_000,
  });
  assert.equal(after.allowed, true);
});

test("anchor ensure creates only missing anchors and preserves unknown pages", { concurrency: false }, async () => {
  const pages = [
    { id: "us", type: "page", url: "https://sellercentral.amazon.com/amazonsell/business?ref=home" },
    { id: "flatfile", type: "page", url: "https://app.flatfile.pro/login" },
  ];
  const created = [];
  const cdp = {
    listPages: async () => pages,
    createPage: async (url, options) => {
      const targetId = `created-${created.length + 1}`;
      pages.push({ id: targetId, type: "page", url });
      created.push({ targetId, url, options });
      await registry.acquireLease({ port: 9222, targetId, leaseClass: options.leaseClass, owner: options.owner, anchorKey: options.anchorKey, now: 1, policy });
      return { targetId, session: { close() {} } };
    },
  };
  const result = await controller.ensureAnchors(9222, { policy, cdp });
  assert.deepEqual(result.created.map((entry) => entry.key), ["DE", "AUS"]);
  assert.equal(pages.some((page) => page.id === "flatfile"), true);
  assert.deepEqual(result.closed, []);
  for (const lease of (await registry.listLeases()).filter((entry) => ["us", "created-1", "created-2"].includes(entry.targetId))) {
    await registry.removeLease({ port: 9222, targetId: lease.targetId });
  }
});

test("a navigated anchor is reclassified and replaced without navigation", { concurrency: false }, async () => {
  const oneAnchorPolicy = structuredClone(policy);
  oneAnchorPolicy.ports["9222"].anchors = [policy.ports["9222"].anchors[0]];
  await registry.acquireLease({
    port: 9222, targetId: "moved-anchor", leaseClass: "anchor", owner: "test",
    anchorKey: "US", origin: "https://sellercentral.amazon.com", now: 1, policy: oneAnchorPolicy,
  });
  const pages = [{ id: "moved-anchor", type: "page", url: "https://app.flatfile.pro/imports" }];
  const cdp = {
    listPages: async () => pages,
    createPage: async (url, options) => {
      pages.push({ id: "replacement", type: "page", url });
      await registry.acquireLease({ port: 9222, targetId: "replacement", leaseClass: options.leaseClass, owner: options.owner, anchorKey: options.anchorKey, now: 2, policy: oneAnchorPolicy });
      return { targetId: "replacement", session: { close() {} } };
    },
  };
  const result = await controller.ensureAnchors(9222, { policy: oneAnchorPolicy, cdp });
  assert.equal(result.reclassified[0].targetId, "moved-anchor");
  assert.equal(result.created[0].targetId, "replacement");
  const leases = await registry.listLeases();
  assert.equal(leases.find((lease) => lease.targetId === "moved-anchor").class, "interactive");
  await registry.removeLease({ port: 9222, targetId: "moved-anchor" });
  await registry.removeLease({ port: 9222, targetId: "replacement" });
});

test("cleanup closes only an expired registered lease and ignores an unknown page", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "expired", owner: "test", now: 1, policy });
  await registry.releaseLease({ port: 9222, targetId: "expired", outcome: "success", now: 1000, policy });
  const pages = [
    { id: "expired", type: "page", url: "https://example.test/work", webSocketDebuggerUrl: "ws://test/expired" },
    { id: "unknown", type: "page", url: "https://app.flatfile.pro/imports", webSocketDebuggerUrl: "ws://test/unknown" },
  ];
  const closed = [];
  const cdp = {
    assertChrome: async () => ({}), listPages: async () => pages,
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => ({ ok: true, value: 1000 }),
    closePageImmediately: async (targetId) => { closed.push(targetId); },
  };
  const managedStatus = { managed: true, running: true, mode: "headed" };
  const audit = await controller.cleanupPort(9222, {
    policy, auditOnly: true, now: 601_001, cdp, managedStatus, maintainAnchors: false,
  });
  assert.equal(audit.actions.some((action) => action.action === "would-close" && action.targetId === "expired"), true);
  assert.deepEqual(closed, []);
  const active = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 601_001, cdp, managedStatus, maintainAnchors: false,
  });
  assert.equal(active.actions.some((action) => action.action === "close" && action.targetId === "expired"), true);
  assert.deepEqual(closed, ["expired"]);
  assert.equal(active.actions.some((action) => action.targetId === "unknown"), false);
  const repeated = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 601_002, cdp, managedStatus, maintainAnchors: false,
  });
  assert.deepEqual(repeated.actions, []);
  assert.deepEqual(closed, ["expired"]);
});

test("cleanup preserves a tab when activity cannot be measured", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "unmeasurable", owner: "test", now: 1, policy });
  await registry.releaseLease({ port: 9222, targetId: "unmeasurable", outcome: "success", now: 1000, policy });
  const cdp = {
    assertChrome: async () => ({}),
    listPages: async () => [{ id: "unmeasurable", type: "page", url: "https://example.test", webSocketDebuggerUrl: "ws://test" }],
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => ({ ok: false, value: null }),
    installLeaseActivityTracker: async () => { throw new Error("tracker unavailable"); },
    closePageImmediately: async () => { throw new Error("must not close"); },
  };
  const result = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 700_000, cdp,
    managedStatus: { managed: true, running: true, mode: "headed" }, maintainAnchors: false,
  });
  assert.equal(result.actions[0].action, "preserved");
  assert.equal(result.actions[0].reason, "activity-unavailable");
  await registry.removeLease({ port: 9222, targetId: "unmeasurable" });
});

test("cleanup restores a missing tracker and closes only after a fresh inspection window", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "tracker-lost", owner: "test", now: 1, policy });
  await registry.releaseLease({ port: 9222, targetId: "tracker-lost", outcome: "success", now: 1000, policy });
  let trackerInstalled = false;
  let installCount = 0;
  const closed = [];
  const cdp = {
    assertChrome: async () => ({}),
    listPages: async () => [{
      id: "tracker-lost", type: "page", url: "https://example.test/work",
      webSocketDebuggerUrl: "ws://test/tracker-lost",
    }],
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => trackerInstalled
      ? ({ ok: true, value: 700_000 })
      : ({ ok: false, value: null }),
    installLeaseActivityTracker: async () => { trackerInstalled = true; installCount += 1; },
    closePageImmediately: async (targetId) => { closed.push(targetId); },
  };
  const managedStatus = { managed: true, running: true, mode: "headed" };

  const restored = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 700_000, cdp, managedStatus, maintainAnchors: false,
  });
  assert.equal(restored.actions[0].action, "activity-tracker-restored");
  assert.equal(restored.actions[0].class, "inspection");
  assert.equal(restored.actions[0].expiresAt, 7_900_000);
  assert.equal(installCount, 1);
  assert.deepEqual(closed, []);

  const expired = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 7_900_001, cdp, managedStatus, maintainAnchors: false,
  });
  assert.equal(expired.actions[0].action, "close");
  assert.deepEqual(closed, ["tracker-lost"]);
});

test("overlapping cleanup passes atomically close an expired target once", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "overlap", owner: "test", now: 1, policy });
  await registry.releaseLease({ port: 9222, targetId: "overlap", outcome: "success", now: 1000, policy });
  const page = { id: "overlap", type: "page", url: "https://example.test/work", webSocketDebuggerUrl: "ws://test/overlap" };
  const closed = [];
  const cdp = {
    assertChrome: async () => ({}),
    listPages: async () => [page],
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => ({ ok: true, value: 1000 }),
    closePageImmediately: async (targetId) => { closed.push(targetId); },
  };
  const options = {
    policy, auditOnly: false, now: 601_001, cdp,
    managedStatus: { managed: true, running: true, mode: "headed" }, maintainAnchors: false,
  };
  const results = await Promise.all([
    controller.cleanupPort(9222, options),
    controller.cleanupPort(9222, options),
  ]);
  assert.deepEqual(closed, ["overlap"]);
  assert.equal(results.flatMap((result) => result.actions).filter((action) => action.action === "close").length, 1);
});

test("cleanup refuses an unmanaged browser before reading or closing targets", { concurrency: false }, async () => {
  const cdp = {
    assertChrome: async () => { throw new Error("must not probe unmanaged browser"); },
    closePageImmediately: async () => { throw new Error("must not close unmanaged browser"); },
  };
  const result = await controller.cleanupPort(9222, {
    policy, auditOnly: false, cdp,
    managedStatus: { managed: false, running: true, mode: "headed" }, maintainAnchors: false,
  });
  assert.equal(result.error, "UNMANAGED_CDP_BROWSER");
  assert.deepEqual(result.actions, []);
});

test("scheduled cleanup additively recreates a missing anchor", { concurrency: false }, async () => {
  const oneAnchorPolicy = structuredClone(policy);
  oneAnchorPolicy.ports["9222"].anchors = [policy.ports["9222"].anchors[0]];
  const pages = [{
    id: "unknown", type: "page", url: "https://app.flatfile.pro/imports",
    webSocketDebuggerUrl: "ws://test/unknown",
  }];
  const created = [];
  const cdp = {
    assertChrome: async () => ({}),
    listPages: async () => pages,
    createPage: async (url, options) => {
      const targetId = "replacement-anchor";
      pages.push({ id: targetId, type: "page", url, webSocketDebuggerUrl: "ws://test/anchor" });
      created.push(targetId);
      await registry.acquireLease({
        port: 9222, targetId, leaseClass: options.leaseClass, owner: options.owner,
        anchorKey: options.anchorKey, origin: url, now: 1, policy: oneAnchorPolicy,
      });
      return { targetId, session: { close() {} } };
    },
  };
  const result = await controller.cleanupPort(9222, {
    policy: oneAnchorPolicy, auditOnly: false, now: 2, cdp,
    managedStatus: { managed: true, running: true, mode: "headed" },
  });
  assert.deepEqual(created, ["replacement-anchor"]);
  assert.deepEqual(result.anchorMaintenance, { kept: 1, created: 1, reclassified: 0 });
  assert.equal(pages.some((page) => page.id === "unknown"), true);
  await registry.removeLease({ port: 9222, targetId: "replacement-anchor" });
});

test("CLI-acquired targets are instrumented for interaction activity", { concurrency: false }, async () => {
  let closed = false;
  let instrumented = false;
  const cdp = {
    listPages: async () => [{
      id: "python-runner", type: "page", url: "https://www.amazon.com/dp/B0X",
      webSocketDebuggerUrl: "ws://test/python-runner",
    }],
    Session: { open: async () => ({ close() { closed = true; } }) },
    installLeaseActivityTracker: async () => { instrumented = true; },
  };
  const result = await controller.acquireTargetLease({
    port: 9222, targetId: "python-runner", leaseClass: "background-active",
    owner: "test", policy, cdp,
  });
  assert.equal(result.activityTracked, true);
  assert.equal(result.lease.origin, "https://www.amazon.com");
  assert.equal(instrumented, true);
  assert.equal(closed, true);
  await registry.removeLease({ port: 9222, targetId: "python-runner" });
});

test("machine policy rejects silent in-app browser fallback", { concurrency: false }, () => {
  writeFileSync(process.env.AMAZON_BROWSER_POLICY, JSON.stringify({
    schema_version: 1,
    routing: {
      default_cdp_port: 9222,
      wizards_ai_cdp_port: 9223,
      in_app_browser_priority: "first",
      allow_silent_in_app_fallback: true,
    },
  }));
  assert.throws(() => policyModule.loadBrowserPolicy(), /disable silent in-app fallback/);
  rmSync(process.env.AMAZON_BROWSER_POLICY, { force: true });
});
