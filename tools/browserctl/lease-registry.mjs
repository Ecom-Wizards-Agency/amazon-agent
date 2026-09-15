import { randomUUID } from "node:crypto";
import { mkdir, readFile, rename, rm, stat, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { RUNTIME_ROOT, loadBrowserPolicy } from "./policy.mjs";
import { resolveContextScope, isRegionalScope, scopeForOrigin,
  REGION_WORKFLOW, REGION_ANCHOR_KEYS } from "./context-scopes.mjs";

export const LEASE_CLASSES = new Set([
  "anchor", "background-active", "background-success", "interactive", "inspection",
]);

const REGISTRY_PATH = join(RUNTIME_ROOT, "leases.json");
const LOCK_PATH = join(RUNTIME_ROOT, ".leases.lock");
const LOCK_STALE_MS = 30_000;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const leaseKey = (port, targetId) => `${Number(port)}:${targetId}`;

function normalizedOrigin(value) {
  if (!value) return null;
  try { return new URL(value).origin; } catch { return null; }
}

function emptyState() {
  return {
    schema_version: 1, revision: 0, leases: {}, auth_attempts: {},
    task_tabs: {}, context_claims: {}, regional_context_claims: {}, download_claims: {},
  };
}

async function readState() {
  try {
    const value = JSON.parse(await readFile(REGISTRY_PATH, "utf8"));
    if (value.schema_version !== 1 || typeof value.leases !== "object") {
      throw new Error("unsupported lease registry schema");
    }
    value.auth_attempts ||= {};
    // Additive fields keep the live schema at v1. Long-running runners loaded
    // before this deployment can therefore continue heartbeating while newer
    // processes start using keyed task tabs.
    value.task_tabs ||= {};
    value.context_claims ||= {};
    value.regional_context_claims ||= {};
    value.download_claims ||= {};
    return value;
  } catch (error) {
    if (error?.code === "ENOENT") return emptyState();
    throw error;
  }
}

async function writeState(state) {
  await mkdir(RUNTIME_ROOT, { recursive: true, mode: 0o700 });
  state.revision = Number(state.revision || 0) + 1;
  const temporary = join(RUNTIME_ROOT, `.leases.${process.pid}.${Date.now()}.tmp`);
  await writeFile(temporary, `${JSON.stringify(state, null, 2)}\n`, { mode: 0o600 });
  await rename(temporary, REGISTRY_PATH);
}

async function acquireLock(timeoutMs = 5000) {
  await mkdir(RUNTIME_ROOT, { recursive: true, mode: 0o700 });
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    try {
      await mkdir(LOCK_PATH, { mode: 0o700 });
      await writeFile(join(LOCK_PATH, "owner.json"), JSON.stringify({ pid: process.pid, at: Date.now() }), { mode: 0o600 });
      return;
    } catch (error) {
      if (error?.code !== "EEXIST") throw error;
      try {
        const metadata = await stat(LOCK_PATH);
        if (Date.now() - metadata.mtimeMs > LOCK_STALE_MS) {
          await rm(LOCK_PATH, { recursive: true, force: true });
          continue;
        }
      } catch (probeError) {
        if (probeError?.code !== "ENOENT") throw probeError;
      }
      if (Date.now() >= deadline) throw new Error("LEASE_REGISTRY_BUSY: timed out acquiring registry lock");
      await sleep(25 + Math.floor(Math.random() * 50));
    }
  }
}

async function transaction(mutator) {
  await acquireLock();
  try {
    const state = await readState();
    const result = await mutator(state);
    await writeState(state);
    return result;
  } finally {
    await rm(LOCK_PATH, { recursive: true, force: true });
  }
}

function assertLeaseInput({ port, targetId, leaseClass }) {
  if (!Number.isInteger(Number(port)) || Number(port) < 1 || Number(port) > 65535) {
    throw new Error(`LEASE_INVALID: unsupported port ${port}`);
  }
  if (!targetId || typeof targetId !== "string") throw new Error("LEASE_INVALID: targetId is required");
  if (!LEASE_CLASSES.has(leaseClass)) throw new Error(`LEASE_INVALID: unsupported class ${leaseClass}`);
}

function expiryFor(leaseClass, now, policy) {
  if (leaseClass === "background-success") return now + policy.cleanup.background_grace_ms;
  if (leaseClass === "interactive" || leaseClass === "inspection") {
    return now + policy.cleanup.interactive_idle_ms;
  }
  return null;
}

function taskSlotKey(port, taskId, slot) {
  return `${Number(port)}:${encodeURIComponent(taskId)}:${encodeURIComponent(slot)}`;
}

function assertTaskText(name, value, maxLength = 200) {
  if (typeof value !== "string" || !value.trim() || value.length > maxLength
      || /[\u0000-\u001f\u007f]/.test(value)) {
    throw new Error(`TASK_TAB_INVALID: ${name} must be a non-empty, non-control string of at most ${maxLength} characters`);
  }
  return value.trim();
}

function taskControlIsHealthy(control, now) {
  return Boolean(control && Number(control.expiresAt || 0) > now);
}

function isRegionPrimary(record) {
  return record.workflow === REGION_WORKFLOW && record.slot === "primary";
}

function regionAnchor(record, policy) {
  const anchorKey = REGION_ANCHOR_KEYS[record.regionScope ?? record.contextScope];
  return policy.ports?.[String(record.port)]?.anchors?.find((anchor) => anchor.key === anchorKey);
}

function preferredAnchor(leases, livePageIds) {
  const live = new Set(livePageIds);
  return leases.find((lease) => live.has(lease.targetId)) || leases[0];
}

function allowsAnchor(record, lease) {
  return isRegionPrimary(record) && isRegionalScope(record.regionScope ?? record.contextScope)
    && lease.anchorKey === REGION_ANCHOR_KEYS[record.regionScope ?? record.contextScope];
}

const regionClaimKey = (port, scope) => `${Number(port)}:${scope}`;
const recordScope = (record) => record.exclusiveContext ? (record.contextScope ?? "global") : null;
const guardIdentity = (port) => `@regional-guard:${Number(port)}`;
function isCompatibilityGuard(claim, port) {
  return claim?.kind === "regional-context-guard" && claim.version === 1
    && claim.port === Number(port) && claim.taskSlotKey === guardIdentity(port)
    && claim.controlToken === guardIdentity(port);
}
function liveRegionalClaims(state, port, now) {
  return Object.entries(state.regional_context_claims || {})
    .filter(([key, claim]) => key.startsWith(`${Number(port)}:`) && taskControlIsHealthy(claim, now));
}
function ownedContextClaim(state, record) {
  const scope = recordScope(record);
  return isRegionalScope(scope)
    ? state.regional_context_claims[regionClaimKey(record.port, scope)]
    : state.context_claims[String(record.port)];
}

// Old processes only inspect context_claims[port]. This derived record keeps
// their global acquisitions excluded while newer regional owners coexist.
function refreshCompatibilityGuard(state, port, now) {
  const key = String(Number(port));
  const current = state.context_claims[key];
  if (current && !isCompatibilityGuard(current, port)) return;
  const claims = liveRegionalClaims(state, port, now).map(([, claim]) => claim);
  if (!claims.length) {
    if (isCompatibilityGuard(current, port)) delete state.context_claims[key];
    return;
  }
  state.context_claims[key] = {
    kind: "regional-context-guard", version: 1, port: Number(port),
    taskSlotKey: guardIdentity(port), controlToken: guardIdentity(port),
    owner: "regional-context-controller",
    heartbeatAt: Math.max(...claims.map((claim) => Number(claim.heartbeatAt))),
    expiresAt: Math.max(...claims.map((claim) => Number(claim.expiresAt))),
  };
}

function conflictingContext(state, port, scope, now) {
  if (!scope) return null;
  const global = state.context_claims[String(Number(port))];
  const regions = liveRegionalClaims(state, port, now);
  if (global && !isCompatibilityGuard(global, port)) {
    // Unknown projection versions and malformed records are not recoverable
    // merely because their deadline looks old.
    if (global.kind || !Number.isFinite(global.expiresAt) || global.expiresAt > now) {
      return { scope: "global", claim: global };
    }
    delete state.context_claims[String(Number(port))];
  }
  if (regions.length && (!isCompatibilityGuard(global, port)
      || !taskControlIsHealthy(global, now))) {
    return { scope: "global", claim: { expiresAt: Math.max(...regions.map(([, claim]) => claim.expiresAt)) } };
  }
  const hit = regions.find(([key]) => scope === "global" || key === regionClaimKey(port, scope));
  return hit ? { scope: hit[1].scope, claim: hit[1] } : null;
}

function requireTaskControl(state, { port, taskId, slot = "primary", controlToken,
  targetId, exclusiveContext = false, contextScope, now = Date.now() }) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  const record = state.task_tabs[key];
  const scope = record ? recordScope(record) : null;
  const claim = record ? ownedContextClaim(state, record) : null;
  const guard = state.context_claims[String(Number(port))];
  const lease = record?.targetId ? state.leases[leaseKey(port, record.targetId)] : null;
  const download = state.download_claims[String(Number(port))];
  if (!record || record.controller?.token !== controlToken
      || !taskControlIsHealthy(record.controller, now)
      || (targetId !== undefined && record.targetId !== targetId)
      || (contextScope !== undefined && scope !== contextScope)
      || (exclusiveContext && !record.exclusiveContext)
      || (record.targetId && (!lease || lease.state === "closing"
        || lease.taskBindingGeneration !== record.bindingGeneration))
      || (record.exclusiveContext && (!claim || claim.taskSlotKey !== key
        || claim.controlToken !== controlToken || !taskControlIsHealthy(claim, now)))
      || (record.controller.downloadsOwned && (!download || download.taskSlotKey !== key
        || download.controlToken !== controlToken || !taskControlIsHealthy(download, now)))
      || (isRegionalScope(scope) && (claim?.scope !== scope || claim?.port !== Number(port)
        || !isCompatibilityGuard(guard, port) || !taskControlIsHealthy(guard, now)
        || guard.expiresAt < claim.expiresAt))) {
    const error = new Error(`TASK_TAB_CONTROL_LOST: ${taskId}/${slot}`);
    error.code = "TASK_TAB_CONTROL_LOST";
    throw error;
  }
  return record;
}

// Read-only fencing for managed commands. Renewal remains one atomic write.
export async function assertTaskTabControl(spec) {
  return structuredClone(requireTaskControl(await readState(), spec));
}

function clearContextClaimFor(state, record, controlToken = null, now = Date.now()) {
  if (record) {
    const downloads = state.download_claims[String(record.port)];
    if (downloads?.taskSlotKey === record.key && (!controlToken || downloads.controlToken === controlToken)) {
      delete state.download_claims[String(record.port)];
    }
  }
  if (!record?.exclusiveContext) return;
  const regional = isRegionalScope(recordScope(record));
  const claims = regional ? state.regional_context_claims : state.context_claims;
  const key = regional ? regionClaimKey(record.port, recordScope(record)) : String(record.port);
  const claim = claims[key];
  if (!claim || claim.taskSlotKey !== record.key) return;
  if (controlToken && claim.controlToken !== controlToken) return;
  delete claims[key];
  if (regional) refreshCompatibilityGuard(state, record.port, now);
}

function activateLease(lease, { owner, now }) {
  if (lease.class !== "anchor") {
    lease.class = "background-active";
    lease.owner = String(owner);
  }
  lease.state = "active";
  lease.updatedAt = now;
  lease.heartbeatAt = now;
  lease.activityMeasurementEpochAt = now;
  lease.activityTrackerBaselineAt = now;
  lease.expiresAt = null;
  lease.outcome = null;
  lease.generation = Number(lease.generation || 0) + 1;
  delete lease.closeToken;
}

function applyLeaseOutcome(lease, outcome, now, policy) {
  if (lease.class === "anchor") {
    lease.state = "leased";
    lease.expiresAt = null;
    lease.lastReleasedAt = now;
  } else if (outcome === "success") {
    lease.class = "background-success";
    lease.state = "released";
    lease.expiresAt = now + policy.cleanup.background_grace_ms;
  } else if (outcome === "interactive" || outcome === "handoff") {
    lease.class = "interactive";
    lease.state = "released";
    lease.expiresAt = now + policy.cleanup.interactive_idle_ms;
  } else {
    lease.class = "inspection";
    lease.state = "released";
    lease.expiresAt = now + policy.cleanup.interactive_idle_ms;
  }
  lease.outcome = outcome;
  lease.lastActivityAt = now;
  lease.activityMeasurementEpochAt = now;
  lease.activityTrackerBaselineAt = now;
  delete lease.activityTrackerProtectionStartedAt;
  delete lease.activityTrackerRestoredAt;
  lease.updatedAt = now;
  lease.generation = Number(lease.generation || 0) + 1;
}

export async function acquireLease({
  port, targetId, leaseClass = "background-active", owner = "unknown", origin = null,
  anchorKey = null, url = null, now = Date.now(), policy = loadBrowserPolicy(), recoverClosing = false,
}) {
  assertLeaseInput({ port, targetId, leaseClass });
  return transaction((state) => {
    const key = leaseKey(port, targetId);
    const previous = state.leases[key];
    const controlled = Object.values(state.task_tabs).find((record) =>
      record.port === Number(port) && record.targetId === targetId
      && taskControlIsHealthy(record.controller, now));
    if (controlled) {
      throw new Error(`TASK_TAB_CONTROL_REQUIRED: ${controlled.taskId}/${controlled.slot}`);
    }
    if (previous?.state === "closing" && !recoverClosing) {
      throw new Error(`LEASE_CLOSING: target ${targetId} has already been claimed for cleanup`);
    }
    const lease = {
      port: Number(port), targetId, class: leaseClass, owner: String(owner),
      state: leaseClass === "background-active" ? "active" : "leased",
      origin: normalizedOrigin(origin) || previous?.origin || null,
      anchorKey: anchorKey || (leaseClass === "anchor" ? previous?.anchorKey || null : null),
      url: url || previous?.url || (leaseClass === "anchor"
        ? policy.ports[String(Number(port))]?.anchors.find((anchor) => anchor.key === anchorKey)?.url : null) || null,
      acquiredAt: previous?.acquiredAt || now,
      updatedAt: now,
      heartbeatAt: leaseClass === "background-active" ? now : previous?.heartbeatAt || null,
      lastActivityAt: previous?.lastActivityAt || now,
      activityMeasurementEpochAt: previous?.activityMeasurementEpochAt || now,
      activityTrackerBaselineAt: previous?.activityTrackerBaselineAt || now,
      expiresAt: expiryFor(leaseClass, now, policy),
      outcome: previous?.outcome || null,
      generation: Number(previous?.generation || 0) + 1,
      taskId: previous?.taskId || null,
      taskSlot: previous?.taskSlot || null,
      taskBindingGeneration: previous?.taskBindingGeneration || null,
      interactionVersion: previous?.interactionVersion ?? null,
      lastObservedInteractionAt: previous?.lastObservedInteractionAt ?? null,
    };
    state.leases[key] = lease;
    return structuredClone(lease);
  });
}

export async function adoptUnregisteredLease({
  port, targetId, owner = "browserctl:unregistered-adoption", origin = null,
  now = Date.now(), policy = loadBrowserPolicy(),
}) {
  const leaseClass = "inspection";
  assertLeaseInput({ port, targetId, leaseClass });
  return transaction((state) => {
    const key = leaseKey(port, targetId);
    const existing = state.leases[key];
    if (existing) return { adopted: false, lease: structuredClone(existing) };
    const lease = {
      port: Number(port), targetId, class: leaseClass, owner: String(owner),
      state: "released", origin: normalizedOrigin(origin), anchorKey: null,
      acquiredAt: now, updatedAt: now, heartbeatAt: null, lastActivityAt: now,
      activityMeasurementEpochAt: now,
      activityTrackerBaselineAt: now,
      expiresAt: expiryFor(leaseClass, now, policy), outcome: "unregistered-adopted",
      generation: 1,
    };
    state.leases[key] = lease;
    return { adopted: true, lease: structuredClone(lease) };
  });
}

export async function touchLease({ port, targetId, kind = "activity", now = Date.now(), policy = loadBrowserPolicy() }) {
  return transaction((state) => {
    const key = leaseKey(port, targetId);
    const lease = state.leases[key];
    if (!lease) return null;
    if (lease.state === "closing") return structuredClone(lease);
    if (kind === "heartbeat") {
      if (lease.class === "background-active") lease.heartbeatAt = now;
    } else {
      if (kind === "interaction") {
        lease.lastObservedInteractionAt = Math.max(Number(lease.lastObservedInteractionAt || 0), now);
      }
      lease.lastActivityAt = Math.max(Number(lease.lastActivityAt || 0), now);
      lease.activityMeasurementEpochAt = lease.lastActivityAt;
      lease.activityTrackerBaselineAt = lease.lastActivityAt;
      delete lease.activityTrackerProtectionStartedAt;
      delete lease.activityTrackerRestoredAt;
      if (lease.class === "background-success" && kind === "interaction") {
        lease.class = "interactive";
        lease.state = "leased";
        lease.outcome = "manual-activity";
      }
      if (lease.class === "interactive" || lease.class === "inspection") {
        lease.expiresAt = lease.lastActivityAt + policy.cleanup.interactive_idle_ms;
      }
    }
    lease.updatedAt = now;
    lease.generation = Number(lease.generation || 0) + 1;
    return structuredClone(lease);
  });
}

export async function releaseLease({
  port, targetId, outcome = "success", now = Date.now(), policy = loadBrowserPolicy(),
}) {
  return transaction((state) => {
    const key = leaseKey(port, targetId);
    const lease = state.leases[key];
    if (!lease) return null;
    if (lease.class === "anchor") return structuredClone(lease);
    if (lease.state === "closing") return structuredClone(lease);
    const controlled = Object.values(state.task_tabs).find((record) =>
      record.port === Number(port) && record.targetId === targetId
      && taskControlIsHealthy(record.controller, now));
    if (controlled) {
      throw new Error(`TASK_TAB_CONTROL_REQUIRED: ${controlled.taskId}/${controlled.slot}`);
    }
    applyLeaseOutcome(lease, outcome, now, policy);
    return structuredClone(lease);
  });
}

export async function transitionMissedHeartbeat({ port, targetId, now = Date.now(), policy = loadBrowserPolicy() }) {
  return transaction((state) => {
    const lease = state.leases[leaseKey(port, targetId)];
    if (lease?.class === "anchor") {
      const record = Object.values(state.task_tabs).find((entry) =>
        entry.port === Number(port) && entry.targetId === targetId && isRegionPrimary(entry));
      if (!record?.controller || taskControlIsHealthy(record.controller, now)) return structuredClone(lease);
      return detachBoundTaskTab(state, record, "heartbeat-lost", now, policy).lease;
    }
    if (!lease || lease.class !== "background-active") return null;
    if (now - Number(lease.heartbeatAt || lease.acquiredAt) <= policy.cleanup.heartbeat_stale_ms) {
      return structuredClone(lease);
    }
    lease.class = "inspection";
    lease.state = "released";
    lease.outcome = "heartbeat-lost";
    lease.lastActivityAt = now;
    lease.activityMeasurementEpochAt = now;
    lease.activityTrackerBaselineAt = now;
    lease.expiresAt = now + policy.cleanup.interactive_idle_ms;
    lease.updatedAt = now;
    lease.generation = Number(lease.generation || 0) + 1;
    return structuredClone(lease);
  });
}

export async function recordActivityProbeFailure({ port, targetId, now = Date.now() }) {
  return transaction((state) => {
    const lease = state.leases[leaseKey(port, targetId)];
    if (!lease) return null;
    lease.activityProbeFailedAt = now;
    lease.updatedAt = now;
    lease.generation = Number(lease.generation || 0) + 1;
    return structuredClone(lease);
  });
}

export async function restartActivityMeasurement({
  port, targetId, now = Date.now(), policy = loadBrowserPolicy(),
}) {
  return transaction((state) => {
    const lease = state.leases[leaseKey(port, targetId)];
    if (!lease || lease.class === "anchor" || lease.class === "background-active") return null;
    lease.class = "inspection";
    lease.state = "released";
    lease.outcome = "activity-measurement-restored";
    // Reinstalling a tracker is not user activity. Grant one conservative
    // two-hour inspection window when measurement is first restored, but never
    // slide it forward merely because another cleanup pass reinstalls again.
    if (!Number(lease.activityTrackerProtectionStartedAt || 0)) {
      lease.lastActivityAt = Math.max(Number(lease.lastActivityAt || 0), now);
      lease.activityMeasurementEpochAt = lease.lastActivityAt;
      lease.activityTrackerProtectionStartedAt = now;
      lease.expiresAt = lease.lastActivityAt + policy.cleanup.interactive_idle_ms;
    }
    lease.activityTrackerRestoredAt = now;
    lease.activityTrackerBaselineAt = Math.max(Number(lease.activityTrackerBaselineAt || 0), now);
    lease.updatedAt = now;
    lease.generation = Number(lease.generation || 0) + 1;
    delete lease.activityProbeFailedAt;
    return structuredClone(lease);
  });
}

export async function reserveTaskTab({
  port, taskId, slot = "primary", workflow, owner = "unknown",
  exclusiveContext = false, sellerCentral, claimScope, allowOperatorActivity = false, origin = null,
  interactionProbe = null, livePageIds = [], now = null, policy = loadBrowserPolicy(),
}) {
  const normalizedTaskId = assertTaskText("taskId", taskId);
  const normalizedSlot = assertTaskText("slot", slot, 100);
  const normalizedWorkflow = assertTaskText("workflow", workflow, 100);
  const regionScope = resolveContextScope({ exclusiveContext, sellerCentral });
  if (claimScope !== undefined && (claimScope !== "global" || !exclusiveContext)) {
    throw Object.assign(new Error("TASK_TAB_CONTEXT_INVALID: claimScope requires global exclusive context"),
      { code: "TASK_TAB_CONTEXT_INVALID" });
  }
  const requestedScope = claimScope || regionScope;
  const regionPrimary = isRegionPrimary({ workflow: normalizedWorkflow, slot: normalizedSlot });
  if (regionPrimary && !isRegionalScope(regionScope)) {
    throw Object.assign(new Error("REGION_SCOPE_REQUIRED: a mapped Seller Central region is required"),
      { code: "REGION_SCOPE_REQUIRED" });
  }
  const testPortAllowed = /^(1|true|yes|on)$/i.test(
    String(process.env.CDP_ENABLE_TEST_LEASES || ""),
  );
  if (![9222, 9223].includes(Number(port)) && !testPortAllowed) {
    throw new Error(`TASK_TAB_INVALID: unsupported managed browser port ${port}`);
  }
  const key = taskSlotKey(port, normalizedTaskId, normalizedSlot);
  return transaction((state) => {
    now ??= Date.now();
    let record = state.task_tabs[key];
    if (record && (record.taskId !== normalizedTaskId || record.slot !== normalizedSlot
        || record.workflow !== normalizedWorkflow || record.port !== Number(port)
        || Boolean(record.exclusiveContext) !== Boolean(exclusiveContext))) {
      throw new Error(`TASK_TAB_CONFLICT: ${normalizedTaskId}/${normalizedSlot} metadata changed`);
    }
    if (record?.contextScope !== undefined && recordScope(record) !== requestedScope
        && !(regionPrimary && (record.regionScope ?? record.contextScope) === regionScope)) {
      throw new Error(`TASK_TAB_CONFLICT: ${normalizedTaskId}/${normalizedSlot} context scope changed`);
    }
    if (regionPrimary && record && (record.regionScope ?? record.contextScope) !== regionScope) {
      throw new Error(`TASK_TAB_CONFLICT: ${normalizedTaskId}/${normalizedSlot} region changed`);
    }
    if (record?.completedAt) {
      throw new Error(`TASK_TAB_COMPLETED: ${normalizedTaskId} has already completed`);
    }
    if (taskControlIsHealthy(record?.controller, now)) {
      return {
        kind: "busy", retryAt: record.controller.expiresAt,
        taskTab: structuredClone(record),
      };
    }
    const boundLease = record?.targetId ? state.leases[leaseKey(port, record.targetId)] : null;

    let effectiveScope = requestedScope;
    const busyFor = (scope) => {
      const conflict = conflictingContext(state, port, scope, now);
      return conflict ? {
        kind: "busy", retryAt: conflict.claim.expiresAt || null, reason: "browser-context-busy",
        blockingScope: conflict.scope, blockingTask: conflict.claim.taskSlotKey || null,
        taskTab: record ? structuredClone(record) : null,
      } : null;
    };
    const conflict = busyFor(effectiveScope);
    if (conflict) return conflict;

    if (regionPrimary && record?.controller
        && (!new Set(livePageIds).has(record.targetId) || !allowsAnchor(record, boundLease || {})
          || boundLease?.class !== "anchor")) {
      detachBoundTaskTab(state, record, "heartbeat-lost", now, policy);
    }

    if (record?.targetId) {
      if (boundLease?.class === "anchor" && !allowsAnchor(record, boundLease)) {
        throw new Error(`TASK_TAB_ANCHOR_REFUSED: ${record.targetId}`);
      }
      if (boundLease?.state === "closing") {
        return { kind: "busy", retryAt: now + 1000, reason: "lease-closing", taskTab: structuredClone(record) };
      }
      // The probe carries the exact state it observed. Heartbeats, cleanup or a
      // competing acquisition invalidate it without granting partial ownership.
      const probeToken = {
        targetId: record.targetId, bindingGeneration: record.bindingGeneration,
        leaseGeneration: boundLease?.generation ?? null, recordUpdatedAt: record.updatedAt,
        controllerToken: record.controller?.token ?? null,
      };
      if (!interactionProbe || Object.entries(probeToken).some(([field, value]) => interactionProbe[field] !== value)) {
        return { kind: "probe", targetId: record.targetId, probeToken, taskTab: structuredClone(record) };
      }
      const unattendedSince = record.releasedAt ?? record.controller?.expiresAt ?? record.unattendedSince;
      if (!interactionProbe.missing && !allowOperatorActivity) {
        const known = record.interactionVersion === 1 && boundLease?.interactionVersion === 1
          && interactionProbe.ok && interactionProbe.version === 1
          && Number.isFinite(interactionProbe.startedAt) && Number.isFinite(interactionProbe.lastInteractionAt)
          && Number.isFinite(unattendedSince) && interactionProbe.startedAt <= unattendedSince;
        if (!known) {
          return { kind: "busy", retryAt: null, reason: "interaction-evidence-unavailable", taskTab: structuredClone(record) };
        }
        const observedAt = Math.max(Number(boundLease.lastObservedInteractionAt || 0), interactionProbe.lastInteractionAt);
        if (observedAt > unattendedSince) {
          // Retain the observation even if navigation later loses the tracker.
          boundLease.lastObservedInteractionAt = observedAt;
          boundLease.lastActivityAt = Math.max(Number(boundLease.lastActivityAt || 0), observedAt);
          if (boundLease.class !== "anchor") {
            boundLease.expiresAt = Math.max(Number(boundLease.expiresAt || 0), observedAt + policy.cleanup.interactive_idle_ms);
          }
          boundLease.generation = Number(boundLease.generation || 0) + 1;
          return { kind: "busy", retryAt: null, reason: "observed-interaction", taskTab: structuredClone(record) };
        }
      }
    }
    if (record?.targetId && isRegionalScope(requestedScope) && !interactionProbe?.missing) {
      const observedScope = interactionProbe?.targetUrl ? scopeForOrigin(interactionProbe.targetUrl) : null;
      if (observedScope && observedScope !== requestedScope) {
        const error = new Error(`TASK_TAB_SCOPE_CONFLICT: retained target is ${observedScope}, requested ${requestedScope}`);
        error.code = "TASK_TAB_SCOPE_CONFLICT";
        throw error;
      }
      // Historical blank/auth pages cannot prove the region of an unscoped
      // task. Preserve global exclusion until a later compatible acquisition.
      if (record.contextScope === undefined && observedScope !== requestedScope) {
        effectiveScope = "global";
        const legacyConflict = busyFor(effectiveScope);
        if (legacyConflict) return legacyConflict;
      }
    }
    if (record?.controller) {
      clearContextClaimFor(state, record, record.controller.token, now);
      record.controller = null;
    }

    if (!record) {
      record = {
        key, port: Number(port), taskId: normalizedTaskId, slot: normalizedSlot,
        workflow: normalizedWorkflow, exclusiveContext: Boolean(exclusiveContext),
        origin: normalizedOrigin(origin), state: "unbound", targetId: null,
        reservationToken: null, reservationExpiresAt: null, controller: null,
        bindingGeneration: 0, createdAt: now, updatedAt: now,
        releasedAt: null, completedAt: null, completionOutcome: null,
        interactionVersion: 1,
      };
      state.task_tabs[key] = record;
    }

    if (!record.targetId && record.reservationToken
        && Number(record.reservationExpiresAt || 0) > now) {
      return {
        kind: "busy", retryAt: record.reservationExpiresAt,
        reason: "task-tab-reservation-busy", taskTab: structuredClone(record),
      };
    }

    if (regionPrimary) record.regionScope = regionScope;
    // Leave ambiguous legacy records unscoped so a later evidenced retry can
    // migrate them. Region primaries may widen their claim for account switching.
    if (effectiveScope === requestedScope) record.contextScope = effectiveScope;
    if (regionPrimary && !record.targetId) {
      const anchor = regionAnchor(record, policy);
      if (!anchor) {
        throw Object.assign(new Error(`REGION_ANCHOR_REQUIRED: policy has no ${REGION_ANCHOR_KEYS[regionScope]} anchor`),
          { code: "REGION_ANCHOR_REQUIRED" });
      }
      const lease = preferredAnchor(Object.values(state.leases).filter((entry) =>
        entry.port === Number(port) && entry.class === "anchor" && entry.anchorKey === anchor.key), livePageIds);
      if (lease) {
        const other = Object.values(state.task_tabs).find((entry) =>
          entry.key !== key && entry.port === Number(port) && entry.targetId === lease.targetId);
        if (other) throw new Error(`TASK_TAB_TARGET_CONFLICT: ${lease.targetId}`);
        record.targetId = lease.targetId;
        record.bindingGeneration = Number(record.bindingGeneration || 0) + 1;
        record.reservationToken = null;
        record.reservationExpiresAt = null;
        lease.url ||= anchor.url;
      }
    }
    const controlToken = randomUUID();
    record.controller = {
      token: controlToken, owner: String(owner), heartbeatAt: now,
      expiresAt: now + policy.cleanup.heartbeat_stale_ms,
    };
    record.updatedAt = now;
    record.releasedAt = null;
    record.unattendedSince = null;
    record.interactionVersion = 1;
    if (exclusiveContext) {
      const regional = isRegionalScope(effectiveScope);
      const claims = regional ? state.regional_context_claims : state.context_claims;
      const contextKey = regional ? regionClaimKey(port, effectiveScope) : String(Number(port));
      claims[contextKey] = {
        taskSlotKey: key, controlToken, owner: String(owner),
        heartbeatAt: now, expiresAt: record.controller.expiresAt,
        scope: effectiveScope, port: Number(port),
      };
      if (regional) refreshCompatibilityGuard(state, port, now);
    }

    if (record.targetId) {
      const lease = state.leases[leaseKey(port, record.targetId)];
      if (lease?.class === "anchor" && !allowsAnchor(record, lease)) {
        clearContextClaimFor(state, record, controlToken, now);
        record.controller = null;
        throw new Error(`TASK_TAB_ANCHOR_REFUSED: ${record.targetId}`);
      }
      if (lease?.state === "closing") {
        clearContextClaimFor(state, record, controlToken, now);
        record.controller = null;
        return {
          kind: "busy", retryAt: now + 1000, reason: "lease-closing",
          taskTab: structuredClone(record),
        };
      }
      const activeLease = lease || {
        port: Number(port), targetId: record.targetId, class: "background-active",
        owner: String(owner), state: "active", origin: record.origin,
        anchorKey: null, acquiredAt: now, updatedAt: now, heartbeatAt: now,
        lastActivityAt: now, activityMeasurementEpochAt: now,
        activityTrackerBaselineAt: now,
        expiresAt: null, outcome: null, generation: 0,
      };
      activateLease(activeLease, { owner, now });
      activeLease.interactionVersion = 1;
      activeLease.lastObservedInteractionAt = interactionProbe?.lastInteractionAt ?? 0;
      activeLease.taskId = normalizedTaskId;
      activeLease.taskSlot = normalizedSlot;
      activeLease.taskBindingGeneration = record.bindingGeneration;
      state.leases[leaseKey(port, record.targetId)] = activeLease;
      record.state = "bound";
      record.lastAcquiredAt = now;
      return {
        kind: "reuse", controlToken, targetId: record.targetId,
        taskTab: structuredClone(record), lease: structuredClone(activeLease),
      };
    }

    record.state = "reserving";
    record.reservationToken ||= randomUUID();
    record.reservationExpiresAt = now + policy.cleanup.heartbeat_stale_ms;
    return {
      kind: "create", controlToken, reservationToken: record.reservationToken,
      taskTab: structuredClone(record),
    };
  });
}

export async function bindReservedTaskTab({
  port, taskId, slot = "primary", targetId, reservationToken, controlToken,
  owner = "unknown", origin = null, now = null, policy = loadBrowserPolicy(),
}) {
  assertLeaseInput({ port, targetId, leaseClass: "background-active" });
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    now ??= Date.now();
    const record = state.task_tabs[key];
    if (!record || record.state !== "reserving"
        || record.reservationToken !== reservationToken
        || record.controller?.token !== controlToken) {
      throw new Error(`TASK_TAB_STALE_RESERVATION: ${taskId}/${slot}`);
    }
    requireTaskControl(state, { port, taskId, slot, controlToken, now });
    const conflicting = Object.values(state.task_tabs).find((entry) =>
      entry.key !== key && entry.targetId === targetId);
    if (conflicting) throw new Error(`TASK_TAB_TARGET_CONFLICT: ${targetId}`);
    const existingLease = state.leases[leaseKey(port, targetId)];
    if (existingLease?.class === "anchor" && !allowsAnchor(record, existingLease)) {
      throw new Error(`TASK_TAB_ANCHOR_REFUSED: ${targetId}`);
    }
    if (existingLease?.state === "closing") {
      throw new Error(`LEASE_CLOSING: target ${targetId} has already been claimed for cleanup`);
    }
    const anchor = isRegionPrimary(record) ? regionAnchor(record, policy) : null;
    if (isRegionPrimary(record)) {
      if (!anchor) throw new Error("REGION_ANCHOR_REQUIRED: policy has no region anchor");
      // Anchor maintenance can win after reservation. Without a live-page
      // snapshot here, refuse any other anchor and let acquisition retry.
      const existingAnchor = Object.values(state.leases).find((entry) =>
        entry.port === Number(port) && entry.class === "anchor"
        && entry.anchorKey === anchor.key && entry.targetId !== targetId);
      if (existingAnchor) {
        throw Object.assign(new Error(`REGION_ANCHOR_CONFLICT: retry acquisition for ${anchor.key}`),
          { code: "REGION_ANCHOR_CONFLICT", retryable: true });
      }
    }
    record.state = "bound";
    record.targetId = targetId;
    record.origin = normalizedOrigin(origin) || record.origin;
    record.reservationToken = null;
    record.reservationExpiresAt = null;
    record.bindingGeneration = Number(record.bindingGeneration || 0) + 1;
    record.lastAcquiredAt = now;
    record.updatedAt = now;
    const lease = existingLease || {
      port: Number(port), targetId, class: "background-active", owner: String(owner),
      state: "active", origin: record.origin, anchorKey: null, acquiredAt: now,
      updatedAt: now, heartbeatAt: now, lastActivityAt: now,
      activityMeasurementEpochAt: now, activityTrackerBaselineAt: now,
      expiresAt: null, outcome: null, generation: 0,
    };
    if (anchor) {
      lease.class = "anchor";
      lease.owner = "browserctl:anchor";
      lease.anchorKey = anchor.key;
      lease.url = anchor.url;
    }
    activateLease(lease, { owner, now });
    lease.interactionVersion = 1;
    lease.lastObservedInteractionAt = 0;
    lease.origin = record.origin || lease.origin || null;
    lease.taskId = record.taskId;
    lease.taskSlot = record.slot;
    lease.taskBindingGeneration = record.bindingGeneration;
    state.leases[leaseKey(port, targetId)] = lease;
    return { taskTab: structuredClone(record), lease: structuredClone(lease) };
  });
}

export async function prepareMissingTaskTabReplacement({
  port, taskId, slot = "primary", targetId, controlToken,
  now = null, policy = loadBrowserPolicy(),
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    now ??= Date.now();
    const record = state.task_tabs[key];
    if (!record || record.targetId !== targetId || record.controller?.token !== controlToken) {
      throw new Error(`TASK_TAB_STALE_CONTROL: ${taskId}/${slot}`);
    }
    requireTaskControl(state, { port, taskId, slot, controlToken, targetId, now });
    delete state.leases[leaseKey(port, targetId)];
    record.targetId = null;
    record.state = "reserving";
    record.reservationToken = randomUUID();
    record.reservationExpiresAt = now + policy.cleanup.heartbeat_stale_ms;
    record.bindingGeneration = Number(record.bindingGeneration || 0) + 1;
    record.updatedAt = now;
    return {
      controlToken, reservationToken: record.reservationToken,
      taskTab: structuredClone(record),
    };
  });
}

export async function touchTaskTabControl({
  port, taskId, slot = "primary", controlToken, targetId, contextScope, now = null, policy = loadBrowserPolicy(),
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    now ??= Date.now();
    const record = requireTaskControl(state, { port, taskId, slot, controlToken, targetId, contextScope, now });
    record.controller.heartbeatAt = now;
    record.controller.expiresAt = now + policy.cleanup.heartbeat_stale_ms;
    record.updatedAt = now;
    if (record.exclusiveContext) {
      const claim = ownedContextClaim(state, record);
      claim.heartbeatAt = now;
      claim.expiresAt = record.controller.expiresAt;
      if (isRegionalScope(recordScope(record))) refreshCompatibilityGuard(state, port, now);
    }
    if (record.controller.downloadsOwned) {
      const download = state.download_claims[String(Number(port))];
      download.heartbeatAt = now;
      download.expiresAt = record.controller.expiresAt;
    }
    const lease = record.targetId ? state.leases[leaseKey(port, record.targetId)] : null;
    if (lease) {
      lease.heartbeatAt = now;
      lease.updatedAt = now;
      lease.generation = Number(lease.generation || 0) + 1;
    }
    return structuredClone(record);
  });
}

/** Protect the browser-wide download directory only while a task downloads. */
export async function acquireTaskDownloads({ port, taskId, slot = "primary", controlToken,
  targetId, contextScope, now = null }) {
  return transaction((state) => {
    now ??= Date.now();
    const record = requireTaskControl(state, { port, taskId, slot, controlToken,
      targetId, contextScope, exclusiveContext: true, now });
    const current = state.download_claims[String(Number(port))];
    if (current && (!Number.isFinite(current.expiresAt) || current.expiresAt > now)) {
      const error = new Error(`TASK_TAB_DOWNLOAD_BUSY: browser downloads on port ${port} are in use`);
      error.code = "TASK_TAB_DOWNLOAD_BUSY";
      throw error;
    }
    const claim = {
      taskSlotKey: record.key, controlToken, heartbeatAt: now,
      expiresAt: record.controller.expiresAt,
    };
    record.controller.downloadsOwned = true;
    state.download_claims[String(Number(port))] = claim;
    return structuredClone(claim);
  });
}

export async function releaseTaskDownloads({ port, taskId, slot = "primary", controlToken,
  targetId, contextScope, now = null }) {
  return transaction((state) => {
    now ??= Date.now();
    const record = requireTaskControl(state, { port, taskId, slot, controlToken,
      targetId, contextScope, exclusiveContext: true, now });
    if (!record.controller.downloadsOwned) throw new Error("TASK_TAB_CONTROL_LOST: no download ownership");
    delete state.download_claims[String(Number(port))];
    delete record.controller.downloadsOwned;
    return structuredClone(record);
  });
}

function detachBoundTaskTab(state, record, outcome, now, policy) {
  const lease = record.targetId ? state.leases[leaseKey(record.port, record.targetId)] : null;
  if (lease) {
    lease.class = "inspection";
    applyLeaseOutcome(lease, "inspection", now, policy);
    lease.outcome = outcome;
    lease.lastReleasedAt = now;
    delete lease.anchorKey;
    delete lease.taskId;
    delete lease.taskSlot;
    delete lease.taskBindingGeneration;
  }
  clearContextClaimFor(state, record, record.controller?.token, now);
  record.targetId = null;
  record.controller = null;
  record.reservationToken = null;
  record.reservationExpiresAt = null;
  record.state = "unbound";
  record.bindingGeneration = Number(record.bindingGeneration || 0) + 1;
  record.releasedAt = now;
  record.updatedAt = now;
  return { taskTab: structuredClone(record), lease: lease ? structuredClone(lease) : null };
}

export async function detachTaskTab({
  port, taskId, slot = "primary", controlToken, contextScope, outcome = "inspection",
  now = null, policy = loadBrowserPolicy(),
}) {
  return transaction((state) => {
    now ??= Date.now();
    const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
    const record = state.task_tabs[key];
    if (!record || record.controller?.token !== controlToken) {
      throw new Error(`TASK_TAB_STALE_CONTROL: ${taskId}/${slot}`);
    }
    requireTaskControl(state, { port, taskId, slot, controlToken, contextScope, now });
    return detachBoundTaskTab(state, record, outcome, now, policy);
  });
}

export async function releaseTaskTabControl({
  port, taskId, slot = "primary", controlToken, contextScope, outcome = "handoff",
  now = null, policy = loadBrowserPolicy(),
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    now ??= Date.now();
    const record = state.task_tabs[key];
    if (!record || record.controller?.token !== controlToken) {
      throw new Error(`TASK_TAB_STALE_CONTROL: ${taskId}/${slot}`);
    }
    requireTaskControl(state, { port, taskId, slot, controlToken, contextScope, now });
    if (isRegionPrimary(record) && !["success", "handoff"].includes(outcome)) {
      return detachBoundTaskTab(state, record, outcome, now, policy);
    }
    const lease = record.targetId ? state.leases[leaseKey(port, record.targetId)] : null;
    if (lease && lease.state !== "closing") applyLeaseOutcome(lease, outcome, now, policy);
    clearContextClaimFor(state, record, controlToken, now);
    record.controller = null;
    record.state = record.targetId ? "bound" : "unbound";
    record.releasedAt = now;
    record.updatedAt = now;
    return {
      taskTab: structuredClone(record), lease: lease ? structuredClone(lease) : null,
    };
  });
}

export async function abandonTaskTabReservation({
  port, taskId, slot = "primary", controlToken, now = null,
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    now ??= Date.now();
    const record = state.task_tabs[key];
    if (!record || record.controller?.token !== controlToken) return null;
    clearContextClaimFor(state, record, controlToken, now);
    record.controller = null;
    record.reservationExpiresAt = Math.min(Number(record.reservationExpiresAt || now), now);
    record.unattendedSince = now;
    record.updatedAt = now;
    return structuredClone(record);
  });
}

export async function completeTaskTabs({
  port, taskId, outcome = "success", now = null, policy = loadBrowserPolicy(),
}) {
  const normalizedTaskId = assertTaskText("taskId", taskId);
  return transaction((state) => {
    now ??= Date.now();
    const records = Object.values(state.task_tabs).filter((entry) =>
      entry.port === Number(port) && entry.taskId === normalizedTaskId && !entry.completedAt);
    const busy = records.find((entry) => taskControlIsHealthy(entry.controller, now));
    if (busy) throw new Error(`TASK_TAB_BUSY: ${normalizedTaskId}/${busy.slot}`);
    const released = [];
    for (const record of records) {
      if (record.controller) clearContextClaimFor(state, record, record.controller.token, now);
      record.controller = null;
      record.completedAt = now;
      record.completionOutcome = outcome;
      record.updatedAt = now;
      const lease = record.targetId ? state.leases[leaseKey(port, record.targetId)] : null;
      if (lease && lease.state !== "closing") {
        applyLeaseOutcome(lease, outcome === "success" ? "success" : outcome, now, policy);
      }
      released.push({ taskTab: structuredClone(record), lease: lease ? structuredClone(lease) : null });
    }
    return released;
  });
}

export async function listTaskTabs() {
  const state = await readState();
  return Object.values(state.task_tabs).map((record) => structuredClone(record));
}

export async function removeLease({ port, targetId, expectedCloseToken = null }) {
  return transaction((state) => {
    const key = leaseKey(port, targetId);
    const lease = state.leases[key];
    if (!lease) return false;
    if (lease.state === "closing" && lease.closeToken
        && lease.closeToken !== expectedCloseToken) return false;
    delete state.leases[key];
    for (const [recordKey, record] of Object.entries(state.task_tabs)) {
      if (record.port !== Number(port) || record.targetId !== targetId) continue;
      clearContextClaimFor(state, record, record.controller?.token || null);
      // Once the exact target is gone there is no useful binding to retain.
      // A later retry can reserve a clean record under the same stable task ID.
      delete state.task_tabs[recordKey];
    }
    return true;
  });
}

export async function listLeases() {
  const state = await readState();
  return Object.values(state.leases).map((lease) => structuredClone(lease));
}

export async function regionTabState(port, { now = Date.now() } = {}) {
  const state = await readState();
  return Object.entries(state.leases)
    .filter(([, lease]) => lease.port === Number(port) && lease.class === "anchor")
    .map(([leaseId, lease]) => {
      const record = Object.values(state.task_tabs).find((entry) =>
        entry.port === Number(port) && entry.targetId === lease.targetId);
      return {
        leaseId, anchorKey: lease.anchorKey ?? null, targetId: lease.targetId, url: lease.url || null,
        boundTaskId: record?.taskId || null, boundSlot: record?.slot || null,
        controllerFresh: taskControlIsHealthy(record?.controller, now),
      };
    });
}

export async function surplusAnchorLeases(port, livePageIds) {
  const groups = new Map();
  for (const lease of await listLeases()) {
    if (lease.port !== Number(port) || lease.class !== "anchor") continue;
    if (!groups.has(lease.anchorKey)) groups.set(lease.anchorKey, []);
    groups.get(lease.anchorKey).push(lease);
  }
  return [...groups.values()].flatMap((leases) => {
    const kept = preferredAnchor(leases, livePageIds);
    return leases.filter((lease) => lease !== kept);
  });
}

export async function claimExpiredLease({
  port, targetId, expectedUpdatedAt, expectedGeneration = null, now = Date.now(),
}) {
  return transaction((state) => {
    const lease = state.leases[leaseKey(port, targetId)];
    if (!lease || lease.class === "anchor" || lease.class === "background-active") return null;
    const controlled = Object.values(state.task_tabs).find((record) =>
      record.port === Number(port) && record.targetId === targetId
      && taskControlIsHealthy(record.controller, now));
    if (controlled) return null;
    if (expectedGeneration != null
        ? Number(lease.generation || 0) !== Number(expectedGeneration)
        : Number(lease.updatedAt) !== Number(expectedUpdatedAt)) return null;
    if (Number(lease.expiresAt || Infinity) > now) return null;
    lease.state = "closing";
    lease.closeToken = randomUUID();
    lease.updatedAt = now;
    lease.generation = Number(lease.generation || 0) + 1;
    return structuredClone(lease);
  });
}

export async function authAttemptStatus({ port, targetId, routeId, now = Date.now(), cooldownMs }) {
  const state = await readState();
  const key = `${Number(port)}:${targetId}:${routeId}`;
  const last = Number(state.auth_attempts[key] || 0);
  return { allowed: !last || now - last >= cooldownMs, retryAt: last ? last + cooldownMs : null };
}

export async function recordAuthAttempt({ port, targetId, routeId, now = Date.now() }) {
  return transaction((state) => {
    const key = `${Number(port)}:${targetId}:${routeId}`;
    state.auth_attempts[key] = now;
    return { recorded: true, at: now };
  });
}

export function defaultLeaseOwner() {
  return `${basename(process.argv[1] || "node")}:${process.pid}`;
}
