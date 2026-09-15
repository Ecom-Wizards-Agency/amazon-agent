import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const runtime = mkdtempSync(join(tmpdir(), "lease-registry-test-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
const registry = await import(`../lease-registry.mjs?lease-test=${Date.now()}`);
const { loadBrowserPolicy } = await import("../policy.mjs");
const { sellerCentralRegionTask } = await import("../task-tabs.mjs");
const policy = loadBrowserPolicy();
test.beforeEach(() => rmSync(join(runtime, "leases.json"), { force: true }));
test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("activity preserves a released success lease; interaction still promotes it", async () => {
  const spec = { port: 9223, targetId: "activity-success", policy };
  await registry.acquireLease({ ...spec, now: 100 });
  await registry.releaseLease({ ...spec, now: 1000 });
  const activity = await registry.touchLease({ ...spec, kind: "activity", now: 2000 });
  assert.equal(activity.class, "background-success");
  assert.equal(activity.state, "released");
  assert.equal(activity.outcome, "success");
  assert.equal(activity.expiresAt, 601000);
  assert.equal(activity.lastActivityAt, 2000);
  assert.equal(activity.lastObservedInteractionAt, null);
  const interaction = await registry.touchLease({ ...spec, kind: "interaction", now: 3000 });
  assert.equal(interaction.class, "interactive");
  assert.equal(interaction.state, "leased");
  assert.equal(interaction.outcome, "manual-activity");
  assert.equal(interaction.expiresAt, 7203000);
  assert.equal(interaction.lastObservedInteractionAt, 3000);
});

test("activity slides existing interactive and inspection windows without changing their release state", async () => {
  for (const outcome of ["handoff", "error"]) {
    const spec = { port: 9223, targetId: `activity-${outcome}`, policy };
    await registry.acquireLease({ ...spec, now: 100 });
    const released = await registry.releaseLease({ ...spec, outcome, now: 1000 });
    const touched = await registry.touchLease({ ...spec, kind: "activity", now: 2000 });
    assert.equal(touched.class, released.class);
    assert.equal(touched.state, "released");
    assert.equal(touched.outcome, outcome);
    assert.equal(touched.expiresAt, 7202000);
  }
});

test("region state reports controller freshness and surplus selection prefers a live target per port", async () => {
  for (const [port, targetId, anchorKey] of [
    [9223, "missing-us", "US"], [9223, "healthy-us", "US"], [9223, "extra-us", "US"],
    [9223, "missing-de", "DE"], [9223, "extra-de", "DE"], [9222, "other-port-us", "US"],
  ]) {
    await registry.acquireLease({ port, targetId, leaseClass: "anchor", anchorKey, now: 100, policy });
  }
  const spec = { ...sellerCentralRegionTask({ marketplace: "us" }), port: 9223, policy };
  const reserved = await registry.reserveTaskTab({ ...spec, livePageIds: ["healthy-us", "extra-us"], now: 1000 });
  assert.equal(reserved.kind, "reuse");
  assert.equal(reserved.targetId, "healthy-us");
  const fresh = (await registry.regionTabState(9223, { now: 2000 })).find((entry) => entry.targetId === "healthy-us");
  assert.deepEqual(fresh, {
    leaseId: "9223:healthy-us", anchorKey: "US", targetId: "healthy-us",
    url: "https://sellercentral.amazon.com/home", boundTaskId: spec.taskId, boundSlot: "primary", controllerFresh: true,
  });
  const stale = (await registry.regionTabState(9223, { now: 91000 })).find((entry) => entry.targetId === "healthy-us");
  assert.equal(stale.controllerFresh, false);
  const otherPort = await registry.regionTabState(9222, { now: 2000 });
  assert.equal(otherPort.length, 1);
  assert.equal(otherPort[0].boundTaskId, null);
  assert.equal(otherPort[0].boundSlot, null);
  assert.equal(otherPort[0].controllerFresh, false);
  assert.deepEqual((await registry.surplusAnchorLeases(9223, new Set(["healthy-us", "extra-us"])))
    .map((lease) => lease.targetId), ["missing-us", "extra-us", "extra-de"]);
  await registry.releaseTaskTabControl({ ...spec, controlToken: reserved.controlToken, outcome: "success", now: 3000 });
  const released = (await registry.regionTabState(9223, { now: 4000 })).find((entry) => entry.targetId === "healthy-us");
  assert.equal(released.controllerFresh, false);
});

test("registry release detaches region errors and rejects stale detach control", async () => {
  const spec = { ...sellerCentralRegionTask({ marketplace: "au" }), port: 9223, policy };
  for (const outcome of ["error", "inspection", "blocked", "auth-required", "operation-failed", "interactive"]) {
    const reserved = await registry.reserveTaskTab({ ...spec, now: 10000 });
    assert.equal(reserved.kind, "create");
    const targetId = `region-${outcome}`;
    await registry.bindReservedTaskTab({ ...spec, targetId,
      reservationToken: reserved.reservationToken, controlToken: reserved.controlToken, now: 11000 });
    await assert.rejects(registry.detachTaskTab({ ...spec, controlToken: "wrong", now: 12000 }), /TASK_TAB_STALE_CONTROL/);
    const released = await registry.releaseTaskTabControl({ ...spec, controlToken: reserved.controlToken, outcome, now: 12000 });
    assert.equal(released.lease.class, "inspection");
    assert.equal(released.lease.outcome, outcome);
    assert.equal(released.lease.expiresAt, 7212000);
    assert.equal("anchorKey" in released.lease, false);
    assert.equal(released.taskTab.targetId, null);
    assert.equal(released.taskTab.controller, null);
    assert.equal(released.taskTab.reservationToken, null);
    assert.equal(released.taskTab.reservationExpiresAt, null);
  }
});

test("ordinary workflow reuse still refuses a target reclassified as an anchor", async () => {
  const spec = { port: 9222, taskId: "ordinary-anchor-reuse", workflow: "test", policy };
  const reserved = await registry.reserveTaskTab({ ...spec, now: 1000 });
  await registry.bindReservedTaskTab({ ...spec, targetId: "ordinary-anchor-reuse",
    reservationToken: reserved.reservationToken, controlToken: reserved.controlToken, now: 2000 });
  await registry.releaseTaskTabControl({ ...spec, controlToken: reserved.controlToken, outcome: "success", now: 3000 });
  await registry.acquireLease({ port: 9222, targetId: "ordinary-anchor-reuse", leaseClass: "anchor", anchorKey: "AUS", now: 4000, policy });
  await assert.rejects(registry.reserveTaskTab({ ...spec, now: 5000 }), /TASK_TAB_ANCHOR_REFUSED/);
});

test("a stale region controller detaches on heartbeat cleanup or acquisition of a missing target", async () => {
  for (const cleanup of [true, false]) {
    const port = cleanup ? 9223 : 9222;
    const spec = { ...sellerCentralRegionTask({ marketplace: cleanup ? "au" : "de" }), port, policy };
    const reserved = await registry.reserveTaskTab({ ...spec, now: 100000 });
    const targetId = `stale-region-${port}`;
    await registry.bindReservedTaskTab({ ...spec, targetId,
      reservationToken: reserved.reservationToken, controlToken: reserved.controlToken, now: 100001 });
    const healthy = await registry.transitionMissedHeartbeat({ port, targetId, now: 100002, policy });
    assert.equal(healthy.class, "anchor");
    if (cleanup) {
      const stale = await registry.transitionMissedHeartbeat({ port, targetId, now: 190000, policy });
      assert.equal(stale.class, "inspection");
    }
    const replacement = await registry.reserveTaskTab({ ...spec, livePageIds: cleanup ? [targetId] : [], now: 190001 });
    assert.equal(replacement.kind, "create");
    const lease = (await registry.listLeases()).find((entry) => entry.targetId === targetId);
    assert.equal(lease.class, "inspection");
    assert.equal(lease.outcome, "heartbeat-lost");
    assert.equal("anchorKey" in lease, false);
    await registry.abandonTaskTabReservation({ ...spec, controlToken: replacement.controlToken, now: 190002 });
  }
});

test("a busy acquisition preserves a stale region binding and later reuses the live anchor", async () => {
  const spec = { ...sellerCentralRegionTask({ marketplace: "de" }), port: 9223, policy };
  const targetId = "recover-live-region";
  const reserved = await registry.reserveTaskTab({ ...spec, now: 100000 });
  await registry.bindReservedTaskTab({ ...spec, targetId,
    reservationToken: reserved.reservationToken, controlToken: reserved.controlToken, now: 100001 });
  const blockerSpec = { port: 9223, taskId: "global-blocker", workflow: "test", exclusiveContext: true, policy };
  const blocker = await registry.reserveTaskTab({ ...blockerSpec, now: 190001 });
  const beforeTabs = await registry.listTaskTabs();
  const beforeLeases = await registry.listLeases();
  const busy = await registry.reserveTaskTab({ ...spec, livePageIds: [targetId], now: 190002 });
  assert.equal(busy.reason, "browser-context-busy");
  assert.deepEqual(await registry.listTaskTabs(), beforeTabs);
  assert.deepEqual(await registry.listLeases(), beforeLeases);
  await registry.abandonTaskTabReservation({ ...blockerSpec, controlToken: blocker.controlToken, now: 190003 });
  const probe = await registry.reserveTaskTab({ ...spec, livePageIds: [targetId], now: 190004 });
  assert.equal(probe.kind, "probe");
  const recovered = await registry.reserveTaskTab({ ...spec, livePageIds: [targetId], now: 190005,
    interactionProbe: { ...probe.probeToken, ok: true, version: 1, startedAt: 100001,
      lastInteractionAt: 0, targetUrl: "https://sellercentral.amazon.de/inventory" } });
  assert.equal(recovered.kind, "reuse");
  assert.equal(recovered.targetId, targetId);
  assert.notEqual(recovered.controlToken, reserved.controlToken);
  assert.equal(recovered.lease.class, "anchor");
  assert.equal(recovered.lease.expiresAt, null);
  assert.equal(recovered.taskTab.bindingGeneration, reserved.taskTab.bindingGeneration + 1);
  await registry.releaseTaskTabControl({ ...spec, controlToken: recovered.controlToken, outcome: "success", now: 190006 });
});

test("region binding refuses an anchor created by maintenance after reservation", async () => {
  const spec = { ...sellerCentralRegionTask({ marketplace: "us" }), port: 9223, policy };
  const reserved = await registry.reserveTaskTab({ ...spec, now: 1000 });
  await registry.acquireLease({ port: 9223, targetId: "maintenance-anchor", leaseClass: "anchor",
    anchorKey: "US", now: 1001, policy });
  const before = await registry.listTaskTabs();
  await assert.rejects(registry.bindReservedTaskTab({ ...spec, targetId: "reserved-target",
    reservationToken: reserved.reservationToken, controlToken: reserved.controlToken, now: 1002 }),
  { code: "REGION_ANCHOR_CONFLICT", retryable: true });
  assert.deepEqual(await registry.listTaskTabs(), before);
  assert.deepEqual((await registry.listLeases()).filter((lease) => lease.class === "anchor")
    .map((lease) => lease.targetId), ["maintenance-anchor"]);
  await registry.abandonTaskTabReservation({ ...spec, controlToken: reserved.controlToken, now: 1003 });
  const retried = await registry.reserveTaskTab({ ...spec, livePageIds: ["maintenance-anchor", "reserved-target"], now: 1004 });
  assert.equal(retried.kind, "reuse");
  assert.equal(retried.targetId, "maintenance-anchor");
});

test("region state normalizes an absent anchor key to null", async () => {
  await registry.acquireLease({ port: 9223, targetId: "unkeyed-anchor", leaseClass: "anchor", policy });
  const path = join(runtime, "leases.json");
  const raw = JSON.parse(readFileSync(path, "utf8"));
  delete raw.leases["9223:unkeyed-anchor"].anchorKey;
  writeFileSync(path, JSON.stringify(raw));
  const [state] = await registry.regionTabState(9223);
  assert.equal(state.anchorKey, null);
});


test("global regional reservations create and detach the region anchor without changing its task id", async () => {
  const spec = { ...sellerCentralRegionTask({ marketplace: "de", claimScope: "global" }), port: 9223, policy };
  const reservation = await registry.reserveTaskTab({ ...spec, now: 1000 });
  assert.equal(reservation.taskTab.contextScope, "global");
  assert.equal(reservation.taskTab.regionScope, "sc:eu");
  await registry.bindReservedTaskTab({ ...spec, targetId: "global-de", reservationToken: reservation.reservationToken,
    controlToken: reservation.controlToken, now: 2000 });
  const lease = (await registry.listLeases()).find(entry => entry.targetId === "global-de");
  assert.equal(lease.class, "anchor");
  assert.equal(lease.anchorKey, "DE");
  const conflict = await registry.reserveTaskTab({ ...sellerCentralRegionTask({ marketplace: "us" }),
    port: 9223, now: 3000, policy });
  assert.equal(conflict.kind, "busy");
  assert.equal(conflict.blockingScope, "global");
  const detached = await registry.detachTaskTab({ ...spec, controlToken: reservation.controlToken,
    contextScope: "global", now: 4000 });
  assert.equal(detached.lease.class, "inspection");
  assert.equal(detached.lease.expiresAt, 7204000);
  assert.equal("anchorKey" in detached.lease, false);
  assert.equal(detached.taskTab.targetId, null);
  const regional = await registry.reserveTaskTab({ ...sellerCentralRegionTask({ marketplace: "de" }),
    port: 9223, now: 5000, policy });
  assert.equal(regional.kind, "create");
  assert.equal(regional.taskTab.contextScope, "sc:eu");
  assert.equal(regional.taskTab.taskId, spec.taskId);
});

for (const detached of [false, true]) {
  test(`closeReleasedTaskTab removes ${detached ? "detached" : "released"} records atomically`, async () => {
    const spec = { port: 9223, taskId: "close-registry", workflow: "test", policy };
    const reserved = await registry.reserveTaskTab(spec);
    const bound = { ...spec, targetId: "close-target", reservationToken: reserved.reservationToken,
      controlToken: reserved.controlToken };
    await registry.bindReservedTaskTab(bound);
    assert.equal(await registry.closeReleasedTaskTab(bound), false);
    await registry[detached ? "detachTaskTab" : "releaseTaskTabControl"]({ ...bound, outcome: "success" });
    assert.equal(await registry.closeReleasedTaskTab(bound), true);
    assert.deepEqual(await registry.listLeases(), []);
    assert.deepEqual(await registry.listTaskTabs(), []);
    assert.equal(await registry.closeReleasedTaskTab(bound), false);
    assert.equal((await registry.reserveTaskTab(spec)).kind, "create");
  });
}

test("closeReleasedTaskTab refuses region anchors and replacement bindings", async () => {
  const spec = { port: 9223, ...sellerCentralRegionTask({ marketplace: "us" }), policy };
  const reserved = await registry.reserveTaskTab(spec);
  const bound = { ...spec, targetId: "region-close-refused", reservationToken: reserved.reservationToken,
    controlToken: reserved.controlToken };
  await registry.bindReservedTaskTab(bound);
  await registry.releaseTaskTabControl({ ...bound, outcome: "success" });
  assert.equal(await registry.closeReleasedTaskTab(bound), false);
  assert.equal((await registry.listLeases())[0].class, "anchor");
  const task = { port: 9223, taskId: "replacement", workflow: "test", policy };
  const reservation = await registry.reserveTaskTab(task);
  const binding = { ...task, targetId: "new-target", reservationToken: reservation.reservationToken,
    controlToken: reservation.controlToken };
  await registry.bindReservedTaskTab(binding);
  await registry.releaseTaskTabControl({ ...binding, outcome: "success" });
  assert.equal(await registry.closeReleasedTaskTab({ ...binding, targetId: "old-target" }), false);
  assert.equal((await registry.listTaskTabs()).find((entry) => entry.taskId === task.taskId).targetId, "new-target");
});
