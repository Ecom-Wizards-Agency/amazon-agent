import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const runtime = mkdtempSync(join(tmpdir(), "regional-context-test-"));
const statePath = join(runtime, "leases.json");
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
process.env.CDP_ENABLE_TEST_LEASES = "1";
const registry = await import("../lease-registry.mjs");
const policy = { cleanup: {
  heartbeat_interval_ms: 30_000, heartbeat_stale_ms: 90_000,
  background_grace_ms: 600_000, interactive_idle_ms: 7_200_000,
} };
const start = 1_000_000;
const origins = {
  us: "https://sellercentral.amazon.com", ca: "https://sellercentral.amazon.ca",
  mx: "https://sellercentral.amazon.com.mx", de: "https://sellercentral.amazon.de",
  uk: "https://sellercentral.amazon.co.uk", au: "https://sellercentral.amazon.com.au",
};
const scopes = { us: "sc:na", ca: "sc:na", mx: "sc:na", de: "sc:eu", uk: "sc:eu", au: "sc:au" };
const state = () => JSON.parse(readFileSync(statePath, "utf8"));
const taskRecord = (taskId) => Object.values(state().task_tabs).find((entry) => entry.taskId === taskId);
function changeState(change) {
  const value = state(); change(value); writeFileSync(statePath, JSON.stringify(value));
}
function spec(taskId, marketplace, extra = {}) {
  return {
    port: 9222, taskId, workflow: "regional-context-test", owner: "test-owner",
    exclusiveContext: true, now: start, policy,
    ...(marketplace ? { sellerCentral: { marketplace, origin: origins[marketplace] } } : {}),
    ...extra,
  };
}
async function create(taskId, marketplace, extra = {}) {
  const args = spec(taskId, marketplace, extra);
  const reservation = await registry.reserveTaskTab(args);
  assert.equal(reservation.kind, "create");
  const targetId = `${taskId}-target`;
  await registry.bindReservedTaskTab({
    ...args, targetId, reservationToken: reservation.reservationToken,
    controlToken: reservation.controlToken,
  });
  return { ...args, targetId, controlToken: reservation.controlToken,
    contextScope: taskRecord(taskId).contextScope ?? "global" };
}
async function createLegacy(taskId) {
  const handle = await create(taskId);
  changeState((value) => { delete value.task_tabs[taskRecord(taskId).key].contextScope; });
  return handle;
}
async function retry(taskId, marketplace, evidence = {}, extra = {}) {
  const args = spec(taskId, marketplace, { now: start + 30, ...extra });
  const probe = await registry.reserveTaskTab(args);
  assert.equal(probe.kind, "probe");
  return registry.reserveTaskTab({ ...args, interactionProbe: {
    ...probe.probeToken, ok: true, version: 1, startedAt: start, lastInteractionAt: 0,
    targetUrl: `${origins[marketplace]}/home`, ...evidence,
  } });
}

// Frozen compatibility excerpts from the pre-regional registry. Keep these
// literal old lookup/cleanup rules: calling the new implementation here would
// not test already-loaded old code after this change is committed.
function legacyContextDecision(value, { port, exclusiveContext, now }) {
  const contextKey = String(Number(port));
  const contextClaim = value.context_claims[contextKey];
  if (contextClaim && Number(contextClaim.expiresAt || 0) <= now) {
    delete value.context_claims[contextKey];
  } else if (exclusiveContext && contextClaim) {
    return { kind: "busy", retryAt: contextClaim.expiresAt, reason: "browser-context-busy" };
  }
  return { kind: "would-acquire" };
}
function legacyClearContextClaim(value, record, controlToken = null) {
  if (!record?.exclusiveContext) return;
  const key = String(record.port);
  const claim = value.context_claims[key];
  if (!claim || claim.taskSlotKey !== record.key) return;
  if (controlToken && claim.controlToken !== controlToken) return;
  delete value.context_claims[key];
}

test.beforeEach(() => rmSync(statePath, { force: true }));
test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("three regions own one port concurrently, while same-region marketplaces conflict", async () => {
  const handles = await Promise.all([create("north-america", "us"), create("europe", "de"), create("australia", "au")]);
  assert.deepEqual(Object.keys(state().regional_context_claims).sort(), ["9222:sc:au", "9222:sc:eu", "9222:sc:na"]);
  for (const marketplace of ["us", "ca", "mx", "de", "uk", "au"]) {
    const result = await registry.reserveTaskTab(spec(`competitor-${marketplace}`, marketplace));
    assert.equal(result.kind, "busy", marketplace);
  }
  for (const handle of handles) await registry.assertTaskTabControl({ ...handle, now: start + 1 });
});

test("nonexclusive tasks and another port remain independent of all regional claims", async () => {
  await create("north-america", "us");
  await create("public-page", null, { exclusiveContext: false });
  await create("other-port", "ca", { port: 9223 });
  assert.equal(state().regional_context_claims["9223:sc:na"].taskSlotKey, taskRecord("other-port").key);
});

test("global ownership blocks each regional scope until released", async () => {
  const global = await create("global-owner");
  for (const marketplace of ["us", "de", "au"]) {
    assert.equal((await registry.reserveTaskTab(spec(`blocked-${marketplace}`, marketplace))).kind, "busy");
  }
  assert.equal(state().context_claims["9222"].controlToken, global.controlToken);
  await registry.releaseTaskTabControl({ ...global, outcome: "success", now: start + 1 });
  await create("regional-after-global", "us", { now: start + 2 });
});

test("regional ownership blocks both new and already-loaded old global acquisition", async () => {
  await create("north-america", "us");
  await create("europe", "de");
  const guard = state().context_claims["9222"];
  assert.equal(guard.kind, "regional-context-guard");
  assert.equal(guard.version, 1);
  for (const result of [
    await registry.reserveTaskTab(spec("old-style-request")),
    legacyContextDecision(state(), spec("old-style-request")),
  ]) {
    assert.equal(result.kind, "busy");
    assert.equal(result.reason, "browser-context-busy");
  }
  assert.deepEqual(state().context_claims["9222"], guard);
});

test("a live old global owner cannot be silently narrowed", async () => {
  const old = await createLegacy("old-owner");
  const before = state();
  assert.equal((await registry.reserveTaskTab(spec(old.taskId, "us"))).kind, "busy");
  assert.equal((await registry.reserveTaskTab(spec("new-europe", "de"))).kind, "busy");
  assert.deepEqual(state().task_tabs, before.task_tabs);
  assert.deepEqual(state().context_claims, before.context_claims);
});

test("renewal and release derive the guard from remaining regional deadlines", async () => {
  const na = await create("north-america", "us");
  const eu = await create("europe", "de", { now: start + 10 });
  await registry.touchTaskTabControl({ ...na, now: start + 30_000 });
  assert.equal(state().context_claims["9222"].expiresAt, start + 120_000);
  assert.equal(state().regional_context_claims["9222:sc:eu"].expiresAt, start + 90_010);
  await registry.releaseTaskTabControl({ ...na, now: start + 30_001, outcome: "success" });
  assert.equal(state().context_claims["9222"].expiresAt, start + 90_010);
  await registry.assertTaskTabControl({ ...eu, now: start + 30_002 });
  assert.equal(legacyContextDecision(state(), spec("still-blocked", null, { now: start + 30_003 })).kind, "busy");
  await registry.releaseTaskTabControl({ ...eu, now: start + 30_004, outcome: "success" });
  assert.equal(state().context_claims["9222"], undefined);
  assert.deepEqual(state().regional_context_claims, {});
});

for (const loss of ["missing-claim", "replaced-claim", "missing-guard", "replaced-guard", "malformed-guard", "expired-guard"]) {
  test(`${loss} prevents assertion and atomic renewal without touching another region`, async () => {
    const na = await create("north-america", "us");
    await create("europe", "de");
    changeState((value) => {
      if (loss === "missing-claim") delete value.regional_context_claims["9222:sc:na"];
      if (loss === "replaced-claim") value.regional_context_claims["9222:sc:na"].controlToken = "new-owner";
      if (loss === "missing-guard") delete value.context_claims["9222"];
      if (loss === "replaced-guard") value.context_claims["9222"] = { taskSlotKey: "other", controlToken: "other", expiresAt: start + 90_000 };
      if (loss === "malformed-guard") value.context_claims["9222"].version = 999;
      if (loss === "expired-guard") value.context_claims["9222"].expiresAt = start;
    });
    const before = state();
    await assert.rejects(registry.assertTaskTabControl({ ...na, now: start + 1 }), /TASK_TAB_CONTROL_LOST/);
    await assert.rejects(registry.touchTaskTabControl({ ...na, now: start + 1 }), /TASK_TAB_CONTROL_LOST/);
    assert.deepEqual(state(), before);
  });
}

test("wrong pinned scope cannot renew or assert another scope's token", async () => {
  const handle = await create("north-america", "us");
  await assert.rejects(registry.assertTaskTabControl({ ...handle, contextScope: "sc:eu", now: start + 1 }), /TASK_TAB_CONTROL_LOST/);
  await assert.rejects(registry.touchTaskTabControl({ ...handle, contextScope: "sc:eu", now: start + 1 }), /TASK_TAB_CONTROL_LOST/);
});

test("released cleanup and stale release preserve a different region's claim", async () => {
  const na = await create("north-america", "us");
  const eu = await create("europe", "de");
  await registry.releaseTaskTabControl({ ...na, outcome: "success", now: start + 10 });
  const before = state().regional_context_claims["9222:sc:eu"];
  const legacyState = state();
  legacyClearContextClaim(legacyState, taskRecord(na.taskId), na.controlToken);
  assert.deepEqual(legacyState.context_claims, state().context_claims);
  await registry.removeLease({ port: 9222, targetId: na.targetId });
  await assert.rejects(registry.releaseTaskTabControl({ ...na, outcome: "success", now: start + 11 }), /TASK_TAB_STALE_CONTROL/);
  assert.deepEqual(state().regional_context_claims["9222:sc:eu"], before);
  await registry.assertTaskTabControl({ ...eu, now: start + 12 });
  assert.equal(state().context_claims["9222"].kind, "regional-context-guard");
});

test("legacy retained task narrows only after a safe same-region probe", async () => {
  const old = await createLegacy("legacy-retry");
  await registry.releaseTaskTabControl({ ...old, outcome: "error", now: start + 10 });
  const targetId = old.targetId;
  const result = await retry(old.taskId, "us");
  assert.equal(result.kind, "reuse");
  assert.equal(result.targetId, targetId);
  assert.equal(taskRecord(old.taskId).contextScope, "sc:na");
  await create("independent-europe", "de", { now: start + 31 });
});

test("legacy retained task with unknown origin keeps global ownership without permanent narrowing", async () => {
  const old = await createLegacy("legacy-unknown");
  await registry.releaseTaskTabControl({ ...old, outcome: "error", now: start + 10 });
  const result = await retry(old.taskId, "us", { targetUrl: "about:blank" });
  assert.equal(result.kind, "reuse");
  assert.equal(taskRecord(old.taskId).contextScope, undefined);
  assert.equal(state().context_claims["9222"].controlToken, result.controlToken);
  assert.equal((await registry.reserveTaskTab(spec("europe-blocked", "de", { now: start + 31 }))).kind, "busy");
});

test("legacy foreign-region target rejects narrowing and keeps its binding", async () => {
  const old = await createLegacy("legacy-foreign");
  await registry.releaseTaskTabControl({ ...old, outcome: "error", now: start + 10 });
  await assert.rejects(retry(old.taskId, "us", { targetUrl: `${origins.de}/home` }), /TASK_TAB_SCOPE_CONFLICT/);
  assert.equal(taskRecord(old.taskId).targetId, old.targetId);
  assert.equal(taskRecord(old.taskId).contextScope, undefined);
});

test("unknown interaction cannot be bypassed to migrate a legacy region", async () => {
  const old = await createLegacy("legacy-interaction");
  await registry.releaseTaskTabControl({ ...old, outcome: "error", now: start + 10 });
  changeState((value) => { delete value.leases[`9222:${old.targetId}`].interactionVersion; });
  const result = await retry(old.taskId, "us");
  assert.equal(result.kind, "busy");
  assert.equal(result.reason, "interaction-evidence-unavailable");
  assert.equal(taskRecord(old.taskId).contextScope, undefined);
});

test("explicit regional task metadata cannot change after release", async () => {
  const handle = await create("fixed-region", "us");
  await registry.releaseTaskTabControl({ ...handle, outcome: "success", now: start + 10 });
  await assert.rejects(registry.reserveTaskTab(spec(handle.taskId, "de", { now: start + 20 })), /TASK_TAB_SCOPE_CONFLICT|TASK_TAB_CONFLICT/);
  assert.equal(taskRecord(handle.taskId).contextScope, scopes.us);
});

test("an expired regional owner cannot release or renew its replacement", async () => {
  const old = await create("expired-na", "us");
  const eu = await create("europe", "de", { now: start + 60_000 });
  const replacement = await create("replacement-na", "ca", { now: start + 100_000 });
  const before = state();
  await assert.rejects(registry.touchTaskTabControl({ ...old, now: start + 100_001 }), /TASK_TAB_CONTROL_LOST/);
  await assert.rejects(registry.releaseTaskTabControl({ ...old, now: start + 100_001 }), /TASK_TAB_CONTROL_LOST/);
  assert.deepEqual(state(), before);
  await registry.assertTaskTabControl({ ...eu, now: start + 100_002 });
  await registry.assertTaskTabControl({ ...replacement, now: start + 100_002 });
});

test("an unknown legacy target cannot fall back to global beside a live other region", async () => {
  const old = await createLegacy("ambiguous-legacy");
  await registry.releaseTaskTabControl({ ...old, outcome: "error", now: start + 10 });
  await create("europe", "de", { now: start + 20 });
  const result = await retry(old.taskId, "us", { targetUrl: "about:blank" });
  assert.equal(result.kind, "busy");
  assert.equal(result.reason, "browser-context-busy");
  assert.equal(taskRecord(old.taskId).controller, null);
  assert.equal(taskRecord(old.taskId).contextScope, undefined);
});

test("a missing legacy target permits an explicitly scoped replacement reservation", async () => {
  const old = await createLegacy("missing-legacy");
  await registry.releaseTaskTabControl({ ...old, outcome: "error", now: start + 10 });
  const result = await retry(old.taskId, "us", { missing: true, targetUrl: null });
  assert.equal(result.kind, "reuse");
  assert.equal(taskRecord(old.taskId).contextScope, "sc:na");
  const replacement = await registry.prepareMissingTaskTabReplacement({
    ...old, controlToken: result.controlToken, now: start + 31,
  });
  assert.ok(replacement.reservationToken);
  await create("europe", "de", { now: start + 32 });
});

test("changed binding generation forces a fresh probe before regional migration", async () => {
  const old = await createLegacy("raced-legacy");
  await registry.releaseTaskTabControl({ ...old, outcome: "error", now: start + 10 });
  const args = spec(old.taskId, "us", { now: start + 30 });
  const probe = await registry.reserveTaskTab(args);
  assert.equal(probe.kind, "probe");
  changeState((value) => { value.task_tabs[taskRecord(old.taskId).key].bindingGeneration += 1; });
  const result = await registry.reserveTaskTab({ ...args, interactionProbe: {
    ...probe.probeToken, ok: true, version: 1, startedAt: start, lastInteractionAt: 0,
    targetUrl: `${origins.us}/home`,
  } });
  assert.equal(result.kind, "probe");
  assert.notEqual(result.probeToken.bindingGeneration, probe.probeToken.bindingGeneration);
  assert.equal(taskRecord(old.taskId).controller, null);
  assert.equal(taskRecord(old.taskId).contextScope, undefined);
});

test("malformed expired compatibility markers are not silently recovered by acquisition", async () => {
  await create("north-america", "us");
  changeState((value) => {
    value.context_claims["9222"].version = 999;
    value.context_claims["9222"].expiresAt = start;
  });
  const guard = state().context_claims["9222"];
  const result = await registry.reserveTaskTab(spec("europe", "de", { now: start + 100_000 }));
  assert.equal(result.kind, "busy");
  assert.deepEqual(state().context_claims["9222"], guard);
});

test("the browser download phase excludes another region without blocking its ordinary work", async () => {
  const na = await create("download-na", "us");
  const eu = await create("download-eu", "de");
  await registry.acquireTaskDownloads({ ...na, now: start + 10 });
  assert.equal(taskRecord(na.taskId).controller.downloadsOwned, true);
  assert.equal(state().download_claims["9222"].controlToken, na.controlToken);
  await registry.assertTaskTabControl({ ...eu, now: start + 11 });
  await assert.rejects(registry.acquireTaskDownloads({ ...eu, now: start + 11 }), /TASK_TAB_DOWNLOAD_BUSY/);
  await registry.releaseTaskDownloads({ ...na, now: start + 12 });
  assert.equal(Boolean(taskRecord(na.taskId).controller.downloadsOwned), false);
  await registry.acquireTaskDownloads({ ...eu, now: start + 13 });
  assert.equal(state().download_claims["9222"].controlToken, eu.controlToken);
  await registry.assertTaskTabControl({ ...na, now: start + 14 });
});

test("the same handle cannot nest browser download phases", async () => {
  const handle = await create("download-nesting", "us");
  await registry.acquireTaskDownloads({ ...handle, now: start + 10 });
  const claim = state().download_claims["9222"];
  await assert.rejects(registry.acquireTaskDownloads({ ...handle, now: start + 11 }), /TASK_TAB_DOWNLOAD_BUSY/);
  assert.deepEqual(state().download_claims["9222"], claim);
});

test("downloads remain independent between browser ports", async () => {
  const first = await create("download-main", "us");
  const other = await create("download-other", "de", { port: 9223 });
  await registry.acquireTaskDownloads({ ...first, now: start + 10 });
  await registry.acquireTaskDownloads({ ...other, now: start + 10 });
  assert.equal(state().download_claims["9222"].controlToken, first.controlToken);
  assert.equal(state().download_claims["9223"].controlToken, other.controlToken);
});

test("atomic task renewal also renews its browser download ownership", async () => {
  const handle = await create("download-renewal", "us");
  await registry.acquireTaskDownloads({ ...handle, now: start + 10 });
  await registry.touchTaskTabControl({ ...handle, now: start + 30_000 });
  const value = state();
  assert.equal(value.download_claims["9222"].expiresAt, taskRecord(handle.taskId).controller.expiresAt);
  assert.equal(value.download_claims["9222"].heartbeatAt, start + 30_000);
  assert.equal(value.regional_context_claims["9222:sc:na"].expiresAt, value.download_claims["9222"].expiresAt);
});

for (const loss of ["missing", "replaced", "expired"]) {
  test(`${loss} download ownership fences the entire handle without partial renewal`, async () => {
    const handle = await create(`download-${loss}`, "us");
    const independent = await create("independent-europe", "de");
    await registry.acquireTaskDownloads({ ...handle, now: start + 10 });
    changeState((value) => {
      if (loss === "missing") delete value.download_claims["9222"];
      if (loss === "replaced") value.download_claims["9222"].controlToken = "replacement-download-owner";
      if (loss === "expired") value.download_claims["9222"].expiresAt = start + 10;
    });
    const before = state();
    await assert.rejects(registry.assertTaskTabControl({ ...handle, now: start + 11 }), /TASK_TAB_CONTROL_LOST/);
    await assert.rejects(registry.touchTaskTabControl({ ...handle, now: start + 11 }), /TASK_TAB_CONTROL_LOST/);
    assert.deepEqual(state(), before);
    await registry.assertTaskTabControl({ ...independent, now: start + 12 });
  });
}

test("stale download release cannot clear another region's later download claim", async () => {
  const first = await create("download-first", "us");
  const second = await create("download-second", "de");
  await registry.acquireTaskDownloads({ ...first, now: start + 10 });
  await registry.releaseTaskDownloads({ ...first, now: start + 11 });
  await registry.acquireTaskDownloads({ ...second, now: start + 12 });
  const claim = state().download_claims["9222"];
  await registry.releaseTaskDownloads({ ...first, now: start + 13 }).catch(() => {});
  assert.deepEqual(state().download_claims["9222"], claim);
  await registry.assertTaskTabControl({ ...second, now: start + 14 });
});

test("releasing the task releases its download phase and preserves another region", async () => {
  const first = await create("download-task-release", "us");
  const second = await create("download-waiting", "de");
  await registry.acquireTaskDownloads({ ...first, now: start + 10 });
  await registry.releaseTaskTabControl({ ...first, outcome: "error", now: start + 11 });
  assert.equal(state().download_claims["9222"], undefined);
  await registry.acquireTaskDownloads({ ...second, now: start + 12 });
  assert.equal(state().download_claims["9222"].controlToken, second.controlToken);
});

test("abandoning a task clears only its own browser download phase", async () => {
  const first = await create("download-abandoned", "us");
  const second = await create("download-next", "de");
  await registry.acquireTaskDownloads({ ...first, now: start + 10 });
  await registry.abandonTaskTabReservation({ ...first, now: start + 11 });
  assert.equal(state().download_claims["9222"], undefined);
  await registry.acquireTaskDownloads({ ...second, now: start + 12 });
  const claim = state().download_claims["9222"];
  await registry.abandonTaskTabReservation({ ...first, now: start + 13 });
  assert.deepEqual(state().download_claims["9222"], claim);
});
