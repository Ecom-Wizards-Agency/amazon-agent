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
    adopt_unregistered_tabs: false,
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

test("only interaction promotes a released background page to a two-hour interactive lease", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "active", owner: "test", now: 1, policy });
  await registry.releaseLease({ port: 9222, targetId: "active", outcome: "success", now: 1000, policy });
  const touched = await registry.touchLease({ port: 9222, targetId: "active", kind: "activity", now: 2000, policy });
  assert.equal(touched.class, "background-success");
  assert.equal(touched.expiresAt, 601_000);
  const interaction = await registry.touchLease({ port: 9222, targetId: "active", kind: "interaction", now: 2000, policy });
  assert.equal(interaction.class, "interactive");
  assert.equal(interaction.expiresAt, 7_202_000);
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

test("Evo cleanup adopts an unknown page and waits a full inspection window", { concurrency: false }, async () => {
  const adoptionPolicy = structuredClone(policy);
  adoptionPolicy.cleanup.adopt_unregistered_tabs = true;
  let trackerInstalled = false;
  const closed = [];
  const page = {
    id: "adopted", type: "page", url: "https://app.flatfile.pro/imports",
    webSocketDebuggerUrl: "ws://test/adopted",
  };
  const cdp = {
    assertChrome: async () => ({}), listPages: async () => [page],
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => trackerInstalled
      ? ({ ok: true, value: 1_000 })
      : ({ ok: false, value: null }),
    installLeaseActivityTracker: async () => { trackerInstalled = true; },
    closePageImmediately: async (targetId) => { closed.push(targetId); },
  };
  const options = {
    policy: adoptionPolicy, auditOnly: false, cdp,
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" }, maintainAnchors: false,
  };

  const adopted = await controller.cleanupPort(9222, { ...options, now: 1_000 });
  assert.equal(adopted.actions[0].action, "adopted-for-inspection");
  assert.equal(adopted.actions[0].activityTracked, true);
  assert.equal(adopted.actions[0].expiresAt, 7_201_000);
  assert.deepEqual(closed, []);

  const beforeExpiry = await controller.cleanupPort(9222, { ...options, now: 7_200_999 });
  assert.deepEqual(beforeExpiry.actions, []);
  assert.deepEqual(closed, []);

  const expired = await controller.cleanupPort(9222, { ...options, now: 7_201_000 });
  assert.equal(expired.actions[0].action, "close");
  assert.deepEqual(closed, ["adopted"]);
});

test("unregistered adoption cannot overwrite a concurrent active runner lease", { concurrency: false }, async () => {
  const targetId = "adoption-race";
  await Promise.all([
    registry.adoptUnregisteredLease({
      port: 9222, targetId, owner: "cleanup", now: 1_000, policy,
    }),
    registry.acquireLease({
      port: 9222, targetId, leaseClass: "background-active", owner: "runner",
      now: 1_001, policy,
    }),
  ]);
  const lease = (await registry.listLeases()).find((entry) => entry.targetId === targetId);
  assert.equal(lease.class, "background-active");
  assert.equal(lease.owner, "runner");
  await registry.removeLease({ port: 9222, targetId });
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
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" }, maintainAnchors: false,
  });
  assert.equal(result.actions[0].action, "preserved");
  assert.equal(result.actions[0].reason, "activity-unavailable");
  await registry.removeLease({ port: 9222, targetId: "unmeasurable" });
});

test("reinstalling a missing tracker does not keep extending an idle lease", { concurrency: false }, async () => {
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

  trackerInstalled = false;
  const restoredAgain = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 705_000, cdp, managedStatus, maintainAnchors: false,
  });
  assert.equal(restoredAgain.actions[0].action, "activity-tracker-restored");
  assert.equal(restoredAgain.actions[0].expiresAt, 7_900_000);
  assert.equal(installCount, 2);

  const expired = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 7_900_001, cdp, managedStatus, maintainAnchors: false,
  });
  assert.equal(expired.actions[0].action, "close");
  assert.deepEqual(closed, ["tracker-lost"]);
});

test("cleanup retains the original probe error and reports incomplete work", { concurrency: false }, async () => {
  await registry.acquireLease({ port: 9222, targetId: "probe-timeout", owner: "test", now: 1, policy });
  await registry.releaseLease({ port: 9222, targetId: "probe-timeout", outcome: "success", now: 1000, policy });
  const cdp = {
    assertChrome: async () => ({}),
    listPages: async () => [{ id: "probe-timeout", type: "page", url: "https://example.test/work", webSocketDebuggerUrl: "ws://test/tab" }],
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => ({ ok: false, error: "CDP Runtime.evaluate timed out after 10000 ms" }),
    installLeaseActivityTracker: async () => { throw new Error("must not overwrite the timeout with a tracker install failure"); },
    closePageImmediately: async () => { throw new Error("must preserve"); },
  };
  const result = await controller.cleanupPort(9222, {
    policy, auditOnly: false, now: 700_000, cdp,
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" }, maintainAnchors: false,
  });
  assert.equal(result.complete, false);
  assert.equal(result.actions[0].probe.stage, "read-activity");
  assert.equal(result.actions[0].probe.error, "CDP Runtime.evaluate timed out after 10000 ms");
  assert.equal(controller.cleanupSummary([result], "active").ok, false);
  assert.equal(controller.cleanupSummary([{ reachable: false }], "active").complete, false);
  const deferred = controller.cleanupSummary([{
    reachable: true, complete: false, actions: [{ reason: "session-busy", probe: { stage: "connect" } }],
  }], "active");
  assert.equal(deferred.complete, false);
  assert.equal(deferred.ok, true);
  assert.equal(deferred.status, "deferred");
  await registry.removeLease({ port: 9222, targetId: "probe-timeout" });
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
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" }, maintainAnchors: false,
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
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" },
  });
  assert.deepEqual(created, ["replacement-anchor"]);
  assert.deepEqual(result.anchorMaintenance, { kept: 1, created: 1, reclassified: 0, skipped: [] });
  assert.equal(pages.some((page) => page.id === "unknown"), true);
  await registry.removeLease({ port: 9222, targetId: "replacement-anchor" });
});

test("the account switcher counts as a signed-in anchor, not a navigated one", { concurrency: false }, () => {
  const [us] = policy.ports["9222"].anchors;
  const switcher = "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace?returnTo=%2Fhome";
  assert.equal(policyModule.anchorMatchesUrl(us, switcher), true);
  assert.equal(policyModule.anchorMatchesUrl(us, "https://sellercentral.amazon.com/account-switcher"), true);
  assert.equal(policyModule.anchorMatchesUrl(us, "https://sellercentral.amazon.com/home"), true);
  assert.equal(policyModule.anchorMatchesUrl(us, "https://sellercentral.amazon.com/inventory"), false);
  assert.equal(policyModule.anchorMatchesUrl(us, "https://sellercentral.amazon.com/account-switcheroo"), false);
  assert.equal(policyModule.anchorMatchesUrl(us, "https://sellercentral.amazon.de/account-switcher/default"), false);
});

test("an anchor resting on the account switcher is never replaced", { concurrency: false }, async () => {
  const oneAnchorPolicy = structuredClone(policy);
  oneAnchorPolicy.ports["9222"].anchors = [policy.ports["9222"].anchors[0]];
  const pages = [{
    id: "us-anchor", type: "page",
    url: "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace?returnTo=%2Fhome",
    webSocketDebuggerUrl: "ws://test/us-anchor",
  }];
  await registry.acquireLease({
    port: 9222, targetId: "us-anchor", leaseClass: "anchor", owner: "browserctl:anchor",
    anchorKey: "US", origin: "https://sellercentral.amazon.com", now: 1, policy: oneAnchorPolicy,
  });
  const cdp = {
    assertChrome: async () => ({}),
    listPages: async () => pages,
    createPage: async () => { throw new Error("must not open a replacement anchor"); },
  };
  const result = await controller.ensureAnchors(9222, { policy: oneAnchorPolicy, cdp });
  assert.deepEqual(result.created, []);
  assert.deepEqual(result.reclassified, []);
  assert.equal(result.kept.length, 1);
  assert.equal(result.kept[0].source, "registry");
  assert.equal(pages.length, 1);
  await registry.removeLease({ port: 9222, targetId: "us-anchor" });
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

test("duplicate anchors become inspection leases and missing duplicates are dropped", async () => {
  const oneAnchorPolicy = structuredClone(policy);
  oneAnchorPolicy.ports["9222"].anchors = [policy.ports["9222"].anchors[0]];
  for (const targetId of ["gone-anchor", "healthy-anchor", "duplicate-anchor"]) {
    await registry.acquireLease({ port: 9222, targetId, leaseClass: "anchor", anchorKey: "US", now: 1, policy });
  }
  const pages = ["healthy-anchor", "duplicate-anchor"].map((id) => ({
    id, url: "https://sellercentral.amazon.com/home", webSocketDebuggerUrl: "ws://test/" + id,
  }));
  const closed = [];
  const cdp = {
    assertChrome: async () => ({}), listPages: async () => pages,
    createPage: async () => { throw new Error("must keep the first live anchor"); },
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => ({ ok: true, value: 1000 }),
    closePageImmediately: async (id) => { closed.push(id); },
  };
  const options = { policy: oneAnchorPolicy, cdp, auditOnly: false,
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" } };
  const result = await controller.cleanupPort(9222, { ...options, now: 1000 });
  assert.deepEqual(result.anchorMaintenance, { kept: 1, created: 0, reclassified: 1, skipped: [] });
  const leases = await registry.listLeases();
  assert.equal(leases.some((lease) => lease.targetId === "gone-anchor"), false);
  const duplicate = leases.find((lease) => lease.targetId === "duplicate-anchor");
  assert.equal(duplicate.class, "inspection");
  assert.equal(duplicate.owner, "browserctl:anchor-duplicate");
  assert.equal(duplicate.anchorKey, null);
  assert.equal(duplicate.expiresAt, 7_201_000);
  assert.deepEqual(closed, []);
  await controller.cleanupPort(9222, { ...options, now: 7_201_001 });
  assert.deepEqual(closed, ["duplicate-anchor"]);
  await registry.removeLease({ port: 9222, targetId: "healthy-anchor" });
});

test("task completion leaves the browser environment untouched without importing CDP", async () => {
  const taskId = "registry-only:0123456789abcdef0123";
  const spec = { port: 9222, taskId, workflow: "registry-only", policy };
  const reserved = await registry.reserveTaskTab(spec);
  await registry.bindReservedTaskTab({ ...spec, ...reserved, targetId: "registry-only" });
  await registry.releaseTaskTabControl({ ...spec, controlToken: reserved.controlToken, outcome: "handoff" });
  const previous = { ...process.env };
  try {
    // A CDP import would reject this invalid session before completion.
    process.env.AMAZON_BROWSER_SESSION = "invalid-registry-only-session";
    process.env.CDP_PORT = "12345";
    const expected = { ...process.env };
    const result = await runCli(["task", "complete", "--port", "9222", "--task-id", taskId]);
    assert.equal(result.lines[0].result[0].taskTab.completionOutcome, "success");
    assert.deepEqual({ ...process.env }, expected);
  } finally {
    for (const key of Object.keys(process.env)) if (!(key in previous)) delete process.env[key];
    Object.assign(process.env, previous);
    await registry.removeLease({ port: 9222, targetId: "registry-only" });
  }
});

test("anchor creation failure still expires leases and reports only expiry failures as incomplete", async () => {
  const closed = [];
  const cdp = {
    assertChrome: async () => ({}),
    listPages: async () => [{ id: "expiry-after-anchor-failure", url: "https://example.test/work" }],
    createPage: async () => { throw new Error("anchor creation failed"); },
    Session: { open: async () => ({ close() {} }) },
    readLeaseActivity: async () => ({ ok: true, value: 1000 }),
    closePageImmediately: async (id) => { closed.push(id); },
  };
  const options = { policy, auditOnly: false, cdp, now: 601_001,
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" } };
  for (const closeFails of [false, true]) {
    await registry.acquireLease({ port: 9222, targetId: "expiry-after-anchor-failure", now: 1, policy });
    await registry.releaseLease({ port: 9222, targetId: "expiry-after-anchor-failure", outcome: "success", now: 1000, policy });
    if (closeFails) cdp.closePageImmediately = async () => { throw new Error("close failed"); };
    const result = await controller.cleanupPort(9222, options);
    assert.equal(result.anchorMaintenance.error, "anchor creation failed");
    assert.equal(result.reachable, true);
    assert.equal(result.complete, !closeFails);
    assert.equal(result.actions[0].reason, closeFails ? "close-failed" : "lease-expired");
    const cli = await runCli(["cleanup", "--port", "9222"], { cleanup: async () => result });
    assert.equal(cli.exitCode, closeFails ? 1 : 0);
    await registry.removeLease({ port: 9222, targetId: "expiry-after-anchor-failure" });
  }
  assert.deepEqual(closed, ["expiry-after-anchor-failure"]);
});

test("fresh regional controllers protect foreign URLs and win over older duplicate anchors", async () => {
  const { sellerCentralRegionTask, REGION_ANCHOR_KEYS } = await import("../task-tabs.mjs");
  const spec = { ...sellerCentralRegionTask({ marketplace: "us" }), port: 9222, policy };
  assert.equal(spec.anchorKey, REGION_ANCHOR_KEYS["sc:na"]);
  const oneAnchorPolicy = structuredClone(policy);
  oneAnchorPolicy.ports["9222"].anchors = [policy.ports["9222"].anchors[0]];
  for (const targetId of ["older-anchor", "controlled-anchor"]) {
    await registry.acquireLease({ port: 9222, targetId, leaseClass: "anchor", anchorKey: spec.anchorKey, now: 1, policy });
  }
  await registry.reserveTaskTab({ ...spec, livePageIds: ["controlled-anchor"], now: 1000 });
  const pages = [
    { id: "older-anchor", url: "https://sellercentral.amazon.com/home" },
    { id: "controlled-anchor", url: "https://app.flatfile.pro/imports" },
  ];
  const result = await controller.ensureAnchors(9222, {
    policy: oneAnchorPolicy, now: 2000, cdp: {
      listPages: async () => pages,
      createPage: async () => { throw new Error("must not replace a controlled region"); },
    },
  });
  assert.deepEqual(result.created, []);
  assert.deepEqual(result.closed, []);
  assert.deepEqual(result.kept.map((entry) => entry.targetId), ["controlled-anchor"]);
  assert.deepEqual(result.reclassified.map((entry) => entry.targetId), ["older-anchor"]);
  assert.equal((await registry.regionTabState(9222, { now: 2000 }))[0].controllerFresh, true);
  for (const targetId of ["older-anchor", "controlled-anchor"]) await registry.removeLease({ port: 9222, targetId });
});

test("a missing target with a fresh regional controller gets one live replacement", async () => {
  const { sellerCentralRegionTask } = await import("../task-tabs.mjs");
  const spec = { ...sellerCentralRegionTask({ marketplace: "us" }), port: 9222, policy };
  await registry.acquireLease({ port: 9222, targetId: "missing-controlled", leaseClass: "anchor", anchorKey: "US", now: 1, policy });
  await registry.reserveTaskTab({ ...spec, livePageIds: ["missing-controlled"], now: 1000 });
  const oneAnchorPolicy = structuredClone(policy);
  oneAnchorPolicy.ports["9222"].anchors = [policy.ports["9222"].anchors[0]];
  const pages = [];
  const cdp = {
    listPages: async () => pages,
    createPage: async (url, options) => {
      pages.push({ id: "live-replacement", url });
      await registry.acquireLease({ port: 9222, targetId: "live-replacement",
        leaseClass: options.leaseClass, anchorKey: options.anchorKey, now: 2000, policy });
      return { targetId: "live-replacement", session: { close() {} } };
    },
  };
  const before = await registry.listTaskTabs();
  const audit = await controller.ensureAnchors(9222, { policy: oneAnchorPolicy, cdp, now: 2000, auditOnly: true });
  assert.deepEqual(audit.kept, []);
  assert.deepEqual(audit.actions.map((action) => action.action), ["would-remove", "would-create"]);
  assert.deepEqual(await registry.listTaskTabs(), before);
  assert.deepEqual(pages, []);
  const first = await controller.ensureAnchors(9222, { policy: oneAnchorPolicy, cdp, now: 2000 });
  assert.deepEqual(first.kept.map((entry) => entry.targetId), ["live-replacement"]);
  assert.equal(first.created.length, 1);
  assert.equal((await registry.listLeases()).some((lease) => lease.targetId === "missing-controlled"), false);
  assert.equal((await registry.listTaskTabs()).some((task) => task.targetId === "missing-controlled"), false);
  const second = await controller.ensureAnchors(9222, { policy: oneAnchorPolicy, cdp, now: 2001 });
  assert.equal(second.created.length, 0);
  await registry.removeLease({ port: 9222, targetId: "live-replacement" });
});

test("audit-only previews mutations while recording observed activity and heartbeat transitions", async () => {
  const { sellerCentralRegionTask } = await import("../task-tabs.mjs");
  const auditPolicy = structuredClone(policy);
  auditPolicy.cleanup.adopt_unregistered_tabs = true;
  const spec = { ...sellerCentralRegionTask({ marketplace: "us" }), port: 9222, policy: auditPolicy };
  for (const [targetId, anchorKey] of [["audit-stale", "US"], ["audit-gone", "DE"], ["audit-live", "DE"], ["audit-duplicate", "DE"], ["audit-moved", "AUS"]]) {
    await registry.acquireLease({ port: 9222, targetId, leaseClass: "anchor", anchorKey, now: 1, policy: auditPolicy });
  }
  await registry.reserveTaskTab({ ...spec, livePageIds: ["audit-stale"], now: 1000 });
  for (const targetId of ["audit-expired", "audit-input", "audit-untracked", "audit-probe-error", "audit-missing-lease", "audit-heartbeat"]) {
    await registry.acquireLease({ port: 9222, targetId, now: 1, policy: auditPolicy });
    if (targetId !== "audit-heartbeat") await registry.releaseLease({ port: 9222, targetId, outcome: "success", now: 1000, policy: auditPolicy });
  }
  await registry.acquireLease({ port: 9222, targetId: "audit-fresh-heartbeat", now: 601_000, policy: auditPolicy });
  const beforeLeases = await registry.listLeases();
  const beforeTasks = await registry.listTaskTabs();
  const pages = beforeLeases.filter((lease) => lease.targetId.startsWith("audit-")
    && !["audit-gone", "audit-missing-lease"].includes(lease.targetId)).map((lease) => ({
    id: lease.targetId, url: ["audit-live", "audit-duplicate"].includes(lease.targetId)
      ? "https://sellercentral.amazon.de/home" : "https://example.test/work",
    webSocketDebuggerUrl: lease.targetId,
  }));
  for (const targetId of ["audit-unknown", "audit-unknown-error"]) {
    pages.push({ id: targetId, url: "https://example.test/unknown", webSocketDebuggerUrl: targetId });
  }
  const installed = new Set();
  const cdp = {
    assertChrome: async () => ({}), listPages: async () => pages,
    createPage: async () => { assert.fail("audit must not create targets"); },
    closePageImmediately: async () => { assert.fail("audit must not close targets"); },
    installLeaseActivityTracker: async (session) => { installed.add(session.id); },
    Session: { open: async (id) => ({ id, close() {} }) },
    readLeaseActivity: async (session) => ["audit-probe-error", "audit-unknown-error"].includes(session.id)
      ? { ok: false, error: "probe failed" }
      : { ok: !["audit-untracked", "audit-unknown"].includes(session.id) || installed.has(session.id), value: 1000 },
    readLeaseInteraction: async (session) => ({ ok: true, lastInteractionAt: session.id === "audit-input" ? 601_000 : 0 }),
  };
  const result = await controller.cleanupPort(9222, { policy: auditPolicy, auditOnly: true, cdp, now: 601_001,
    managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" } });
  const anchorActions = result.anchorMaintenance.actions;
  for (const targetId of ["audit-stale", "audit-duplicate", "audit-moved"]) {
    assert.ok(anchorActions.some((action) => action.action === "would-reclassify" && action.targetId === targetId));
  }
  assert.ok(anchorActions.some((action) => action.action === "would-remove" && action.targetId === "audit-gone"));
  assert.deepEqual(anchorActions.filter((action) => action.action === "would-create").map((action) => action.key), ["US", "AUS"]);
  for (const [targetId, expected] of [["audit-expired", "would-close"], ["audit-untracked", "activity-tracker-restored"],
    ["audit-missing-lease", "would-remove"], ["audit-heartbeat", "promoted-to-inspection"], ["audit-unknown", "would-adopt"]]) {
    assert.ok(result.actions.some((action) => action.targetId === targetId && action.action === expected));
  }
  const afterLeases = await registry.listLeases();
  assert.equal(afterLeases.length, beforeLeases.length);
  const observedIds = new Set(["audit-input", "audit-untracked", "audit-probe-error", "audit-heartbeat"]);
  assert.deepEqual(afterLeases.filter((lease) => !observedIds.has(lease.targetId)),
    beforeLeases.filter((lease) => !observedIds.has(lease.targetId)));
  const input = afterLeases.find((lease) => lease.targetId === "audit-input");
  assert.equal(input.lastObservedInteractionAt, 601_000);
  assert.equal(input.class, "interactive");
  assert.equal(input.expiresAt, 7_801_000);
  const restored = afterLeases.find((lease) => lease.targetId === "audit-untracked");
  assert.equal(restored.activityTrackerRestoredAt, 601_001);
  assert.equal(restored.class, "inspection");
  assert.equal(restored.expiresAt, 7_801_001);
  assert.equal(afterLeases.find((lease) => lease.targetId === "audit-probe-error").activityProbeFailedAt, 601_001);
  const heartbeat = afterLeases.find((lease) => lease.targetId === "audit-heartbeat");
  assert.equal(heartbeat.class, "inspection");
  assert.equal(heartbeat.outcome, "heartbeat-lost");
  assert.equal(heartbeat.expiresAt, 7_801_001);
  assert.deepEqual([...installed].sort(), ["audit-unknown", "audit-untracked"]);
  assert.equal(result.actions.find((action) => action.targetId === "audit-unknown").activityTracked, true);
  const unknownError = result.actions.find((action) => action.targetId === "audit-unknown-error");
  assert.equal(unknownError.action, "would-adopt");
  assert.equal(unknownError.activityTracked, false);
  assert.deepEqual(unknownError.probe, { stage: "read-activity", error: "probe failed" });
  assert.equal(result.complete, false);
  assert.deepEqual(await registry.listTaskTabs(), beforeTasks);
  for (const lease of beforeLeases.filter((entry) => entry.targetId.startsWith("audit-"))) {
    await registry.removeLease({ port: 9222, targetId: lease.targetId });
  }
});

test("anchor maintenance detaches expired regional controllers before creating one replacement", async () => {
  const { sellerCentralRegionTask } = await import("../task-tabs.mjs");
  const spec = { ...sellerCentralRegionTask({ marketplace: "us" }), port: 9222, policy };
  await registry.acquireLease({ port: 9222, targetId: "stale-region", leaseClass: "anchor", anchorKey: "US", now: 1, policy });
  await registry.reserveTaskTab({ ...spec, livePageIds: ["stale-region"], now: 1000 });
  const oneAnchorPolicy = structuredClone(policy);
  oneAnchorPolicy.ports["9222"].anchors = [policy.ports["9222"].anchors[0]];
  const pages = [{ id: "stale-region", url: "https://sellercentral.amazon.com/inventory" }];
  const cdp = {
    listPages: async () => pages,
    createPage: async (url, options) => {
      pages.push({ id: "fresh-region", url });
      await registry.acquireLease({ port: 9222, targetId: "fresh-region",
        leaseClass: options.leaseClass, anchorKey: options.anchorKey, now: 92_000, policy });
      return { targetId: "fresh-region", session: { close() {} } };
    },
  };
  const first = await controller.ensureAnchors(9222, { policy: oneAnchorPolicy, cdp, now: 92_000 });
  assert.equal(first.created.length, 1);
  const stale = (await registry.listLeases()).find((lease) => lease.targetId === "stale-region");
  assert.equal(stale.class, "inspection");
  assert.equal(stale.outcome, "heartbeat-lost");
  assert.equal(stale.taskId, undefined);
  assert.equal(stale.expiresAt, 7_292_000);
  const second = await controller.ensureAnchors(9222, { policy: oneAnchorPolicy, cdp, now: 93_000 });
  assert.equal(second.created.length, 0);
  for (const targetId of ["stale-region", "fresh-region"]) await registry.removeLease({ port: 9222, targetId });
});

test("cleanup ignores focus activity but extends inspection for interaction", async () => {
  for (const interacted of [false, true]) {
    await registry.acquireLease({ port: 9222, targetId: "inspection-input", leaseClass: "inspection", now: 1000, policy });
    const closed = [];
    const cdp = {
      assertChrome: async () => ({}),
      listPages: async () => [{ id: "inspection-input", url: "https://example.test", webSocketDebuggerUrl: "ws://test/input" }],
      Session: { open: async () => ({ close() {} }) },
      readLeaseActivity: async () => ({ ok: true, value: 7_201_001 }),
      readLeaseInteraction: async () => ({ ok: true, lastInteractionAt: interacted ? 7_201_000 : 0 }),
      closePageImmediately: async (id) => { closed.push(id); },
    };
    await controller.cleanupPort(9222, { policy, cdp, auditOnly: false, now: 7_201_001,
      managedStatus: { managed: true, running: true, profile_verified: true, mode: "headed" }, maintainAnchors: false });
    assert.deepEqual(closed, interacted ? [] : ["inspection-input"]);
    if (interacted) {
      assert.equal((await registry.listLeases()).find((lease) => lease.targetId === "inspection-input").expiresAt, 14_401_000);
      await registry.removeLease({ port: 9222, targetId: "inspection-input" });
    }
  }
});

async function runCli(args, dependencies) {
  const lines = [];
  const log = console.log;
  const exitCode = process.exitCode;
  process.exitCode = 0;
  console.log = (line) => lines.push(JSON.parse(line));
  try {
    await controller.main(args, dependencies);
    return { lines, exitCode: process.exitCode };
  } finally {
    console.log = log;
    process.exitCode = exitCode;
  }
}

test("cleanup CLI defers a busy lock at the deadline with exit zero and preserves audit mode", async () => {
  let now = 1000;
  const sleeps = [];
  let attempts = 0;
  const result = await runCli(["cleanup", "--port", "9223", "--lock-wait-ms", "12000", "--audit-only"], {
    cleanup: (port, options) => controller.cleanupPortWithLock(port, options, {
      acquire: (requestedPort, owner) => {
        assert.equal(requestedPort, 9223);
        assert.equal(owner, "browserctl:cleanup");
        attempts++;
        throw new Error("BROWSER_SESSION_BUSY: fixture");
      },
      clock: () => now,
      sleep: async (ms) => { sleeps.push(ms); now += ms; },
      cleanup: async () => { throw new Error("must not run a busy port pass"); },
    }),
  });
  assert.deepEqual(sleeps, [5000, 5000, 2000]);
  assert.equal(attempts, 3);
  assert.equal(result.exitCode, 0);
  const summary = result.lines[0];
  assert.equal(summary.ok, true);
  assert.equal(summary.complete, false);
  assert.equal(summary.status, "deferred");
  assert.equal(summary.mode, "audit");
  assert.equal(summary.results[0].reason, "session-busy");
  assert.equal(summary.results[0].waitMs, 12000);
  assert.equal(summary.results[0].auditOnly, true);
  assert.equal(controller.cleanupSummary([...summary.results, { reachable: true, complete: true }], "active").status, "deferred");
  assert.equal(controller.cleanupSummary([...summary.results, { reachable: false, error: "probe failed" }], "active").status, "incomplete");
  const failed = await runCli(["cleanup", "--port", "9223"], {
    cleanup: async () => ({ reachable: true, complete: false, actions: [{ reason: "close-failed" }] }),
  });
  assert.equal(failed.exitCode, 1);
  assert.equal(failed.lines[0].ok, false);
  for (const actions of [[], [{ reason: "session-busy" }, { activityTracked: false }],
    [{ reason: "session-busy" }, { reason: "activity-unavailable" }]]) {
    const incomplete = controller.cleanupSummary([{ reachable: true, complete: false, actions }], "active");
    assert.equal(incomplete.ok, false);
    assert.equal(incomplete.status, "incomplete");
  }
});

test("cleanup retries then holds one lock across the port pass and always releases it", async () => {
  let now = 0;
  let attempts = 0;
  let held = false;
  let releases = 0;
  const dependencies = {
    acquire: () => {
      if (++attempts === 1) throw new Error("BROWSER_SESSION_BUSY: fixture");
      held = true;
      return () => { held = false; releases++; };
    },
    clock: () => now, sleep: async (ms) => { now += ms; },
    cleanup: async (port, options) => {
      assert.equal(held, true);
      assert.equal(options.auditOnly, true);
      return { port, reachable: true, complete: true, actions: [] };
    },
  };
  const result = await controller.cleanupPortWithLock(9223, { auditOnly: true }, dependencies);
  assert.equal(result.complete, true);
  assert.equal(now, 5000);
  assert.equal(releases, 1);
  assert.equal(held, false);
  await assert.rejects(controller.cleanupPortWithLock(9223, {}, {
    ...dependencies, cleanup: async () => { throw new Error("port failed"); },
  }), /port failed/);
  assert.equal(releases, 2);
  const failure = await controller.cleanupPortWithLock(9223, {}, {
    ...dependencies, acquire: () => { throw new Error("permission denied"); },
  });
  assert.equal(failure.error, "permission denied");
  assert.equal(controller.cleanupSummary([failure], "active").status, "incomplete");
  for (const value of ["-1", "bad", "1.5"]) {
    await assert.rejects(runCli(["cleanup", "--lock-wait-ms", value]), /INVALID_LOCK_WAIT_MS/);
  }
});

test("cleanup port probes can borrow its real in-process session lock", async () => {
  const { acquireSessionLock, assertSessionLock } = await import("../session-lock.mjs");
  const previous = process.env.AMAZON_BROWSER_LOCK_DIR;
  process.env.AMAZON_BROWSER_LOCK_DIR = join(runtime, "locks");
  try {
    await controller.cleanupPortWithLock(9223, {}, {
      cleanup: async () => {
        const releaseProbe = acquireSessionLock(9223, "probe");
        assertSessionLock(9223);
        releaseProbe();
        assertSessionLock(9223);
        return { reachable: true, complete: true, actions: [] };
      },
    });
    assert.throws(() => assertSessionLock(9223), /LOCK_LOST/);
  } finally {
    if (previous === undefined) delete process.env.AMAZON_BROWSER_LOCK_DIR;
    else process.env.AMAZON_BROWSER_LOCK_DIR = previous;
  }
});

test("task complete CLI completes all slots with the selected outcome on either port", async () => {
  for (const [port, outcome] of [[9222, "success"], [9223, "error"], [9223, "inspection"]]) {
    const taskId = "cli-complete-" + port + "-" + outcome;
    for (const slot of ["primary", "evidence"]) {
      const spec = { port, taskId, slot, workflow: "test", policy };
      const reserved = await registry.reserveTaskTab(spec);
      await registry.bindReservedTaskTab({ ...spec, ...reserved, targetId: taskId + "-" + slot });
      await registry.releaseTaskTabControl({ ...spec, controlToken: reserved.controlToken, outcome: "handoff" });
    }
    const args = ["task", "complete", "--port", String(port), "--task-id", taskId];
    if (outcome !== "success") args.push("--outcome", outcome);
    const { lines } = await runCli(args);
    assert.equal(lines[0].ok, true);
    assert.equal(lines[0].result.length, 2);
    for (const { taskTab, lease } of lines[0].result) {
      assert.equal(taskTab.completionOutcome, outcome);
      assert.ok(taskTab.completedAt);
      assert.equal(lease.class, outcome === "success" ? "background-success" : "inspection");
      await registry.removeLease({ port, targetId: lease.targetId });
    }
  }
  await assert.rejects(runCli(["task", "complete", "--port", "9223", "--task-id", "bad", "--outcome", "handoff"]), /UNSUPPORTED_TASK_OUTCOME/);
});

test("task detach CLI fences control and region state reports the binding", async () => {
  const { sellerCentralRegionTask } = await import("../task-tabs.mjs");
  const spec = { ...sellerCentralRegionTask({ marketplace: "us" }), port: 9222, policy };
  await registry.acquireLease({ port: 9222, targetId: "cli-region", leaseClass: "anchor", anchorKey: "US", policy });
  const reserved = await registry.reserveTaskTab({ ...spec, livePageIds: ["cli-region"] });
  const state = await runCli(["region", "state", "--port", "9222"]);
  assert.equal(state.lines[0].regions[0].boundTaskId, spec.taskId);
  assert.equal(state.lines[0].regions[0].controllerFresh, true);
  const args = ["task", "detach", "--port", "9222", "--task-id", spec.taskId, "--slot", "primary"];
  await assert.rejects(runCli([...args, "--control-token", "wrong"]), /TASK_TAB_STALE_CONTROL/);
  const { lines } = await runCli([...args, "--control-token", reserved.controlToken]);
  assert.equal(lines[0].result.taskTab.targetId, null);
  assert.equal(lines[0].result.lease.class, "inspection");
  assert.equal(lines[0].result.lease.anchorKey, undefined);
  assert.equal(lines[0].result.lease.outcome, "inspection");
  assert.deepEqual((await runCli(["region", "state", "--port", "9222"])).lines[0].regions, []);
  await registry.removeLease({ port: 9222, targetId: "cli-region" });
});

test("region state joins live page URL and title by target ID without changing stored state", async () => {
  await registry.acquireLease({ port: 9222, targetId: "live-region", leaseClass: "anchor", anchorKey: "US", policy });
  const before = await registry.regionTabState(9222);
  let liveUrl = "https://sellercentral.amazon.com/inventory";
  try {
    const fetch = async (url, options) => {
      assert.equal(url, "http://127.0.0.1:9222/json/list");
      assert.ok(options.signal instanceof AbortSignal);
      return { ok: true, json: async () => [
        { id: "other-region", type: "page", url: "https://example.test/wrong", title: "Wrong page" },
        { id: "live-region", type: "page", url: liveUrl, title: "Inventory" },
      ] };
    };
    for (const url of [liveUrl, "https://sellercentral.amazon.com/reports"]) {
      liveUrl = url;
      const result = await runCli(["region", "state", "--port", "9222"], { fetch });
      assert.equal(result.exitCode, 0);
      assert.deepEqual(result.lines[0].regions, before.map(region => ({ ...region, liveUrl, title: "Inventory" })));
    }
    assert.deepEqual(await registry.regionTabState(9222), before);
  } finally { await registry.removeLease({ port: 9222, targetId: "live-region" }); }
});

test("region state preserves stored URL with null live fields for unavailable or missing targets", async () => {
  const { sellerCentralRegionTask } = await import("../task-tabs.mjs");
  const regionPolicy = { ...policy, ports: { ...policy.ports, "9223": policy.ports["9222"] } };
  const spec = { ...sellerCentralRegionTask({ marketplace: "de" }), port: 9223, policy: regionPolicy };
  await registry.acquireLease({ port: 9223, targetId: "offline-region", leaseClass: "anchor", anchorKey: "DE", policy });
  const reserved = await registry.reserveTaskTab({ ...spec, livePageIds: ["offline-region"] });
  await registry.releaseTaskTabControl({ ...spec, controlToken: reserved.controlToken,
    outcome: "success" });
  const before = await registry.regionTabState(9223);
  assert.equal(before[0].url, "https://sellercentral.amazon.de/home");
  try {
    for (const response of [null, { ok: false }, { ok: true, json: async () => { throw new Error("invalid JSON"); } },
      { ok: true, json: async () => ({}) }, { ok: true, json: async () => [] }]) {
      const result = await runCli(["region", "state", "--port", "9223"], { fetch: async url => {
        assert.equal(url, "http://127.0.0.1:9223/json/list");
        if (!response) throw new Error("ECONNREFUSED");
        return response;
      } });
      assert.equal(result.exitCode, 0);
      assert.equal(result.lines[0].ok, true);
      assert.deepEqual(result.lines[0].regions, before.map(region => ({ ...region, liveUrl: null, title: null })));
    }
    assert.deepEqual(await registry.regionTabState(9223), before);
  } finally { await registry.removeLease({ port: 9223, targetId: "offline-region" }); }
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
