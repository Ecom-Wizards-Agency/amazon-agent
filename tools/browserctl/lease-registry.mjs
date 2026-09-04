import { randomUUID } from "node:crypto";
import { mkdir, readFile, rename, rm, stat, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { RUNTIME_ROOT, loadBrowserPolicy } from "./policy.mjs";

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
    task_tabs: {}, context_claims: {},
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

function clearContextClaimFor(state, record, controlToken = null) {
  if (!record?.exclusiveContext) return;
  const key = String(record.port);
  const claim = state.context_claims[key];
  if (!claim || claim.taskSlotKey !== record.key) return;
  if (controlToken && claim.controlToken !== controlToken) return;
  delete state.context_claims[key];
}

function activateLease(lease, { owner, now }) {
  lease.class = "background-active";
  lease.owner = String(owner);
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
  if (lease.class === "anchor") return;
  if (outcome === "success") {
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
  anchorKey = null, now = Date.now(), policy = loadBrowserPolicy(), recoverClosing = false,
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
      lease.lastActivityAt = Math.max(Number(lease.lastActivityAt || 0), now);
      lease.activityMeasurementEpochAt = lease.lastActivityAt;
      lease.activityTrackerBaselineAt = lease.lastActivityAt;
      delete lease.activityTrackerProtectionStartedAt;
      delete lease.activityTrackerRestoredAt;
      if (lease.class === "background-success") {
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
  exclusiveContext = false, allowOperatorActivity = false, origin = null,
  now = Date.now(), policy = loadBrowserPolicy(),
}) {
  const normalizedTaskId = assertTaskText("taskId", taskId);
  const normalizedSlot = assertTaskText("slot", slot, 100);
  const normalizedWorkflow = assertTaskText("workflow", workflow, 100);
  const testPortAllowed = /^(1|true|yes|on)$/i.test(
    String(process.env.CDP_ENABLE_TEST_LEASES || ""),
  );
  if (![9222, 9223].includes(Number(port)) && !testPortAllowed) {
    throw new Error(`TASK_TAB_INVALID: unsupported managed browser port ${port}`);
  }
  const key = taskSlotKey(port, normalizedTaskId, normalizedSlot);
  return transaction((state) => {
    let record = state.task_tabs[key];
    if (record && (record.taskId !== normalizedTaskId || record.slot !== normalizedSlot
        || record.workflow !== normalizedWorkflow || record.port !== Number(port)
        || Boolean(record.exclusiveContext) !== Boolean(exclusiveContext))) {
      throw new Error(`TASK_TAB_CONFLICT: ${normalizedTaskId}/${normalizedSlot} metadata changed`);
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
    if (record?.controller) {
      clearContextClaimFor(state, record, record.controller.token);
      record.controller = null;
    }
    const boundLease = record?.targetId ? state.leases[leaseKey(port, record.targetId)] : null;
    if (!allowOperatorActivity && record?.releasedAt
        && Number(boundLease?.lastActivityAt || 0) > Number(record.releasedAt)
        && ["interactive", "inspection"].includes(boundLease?.class)) {
      return {
        kind: "busy", retryAt: null, reason: "operator-activity-observed",
        taskTab: structuredClone(record),
      };
    }

    const contextKey = String(Number(port));
    const contextClaim = state.context_claims[contextKey];
    if (contextClaim && Number(contextClaim.expiresAt || 0) <= now) {
      delete state.context_claims[contextKey];
    } else if (exclusiveContext && contextClaim && contextClaim.taskSlotKey !== key) {
      return {
        kind: "busy", retryAt: contextClaim.expiresAt, reason: "browser-context-busy",
        taskTab: record ? structuredClone(record) : null,
      };
    }

    if (!record) {
      record = {
        key, port: Number(port), taskId: normalizedTaskId, slot: normalizedSlot,
        workflow: normalizedWorkflow, exclusiveContext: Boolean(exclusiveContext),
        origin: normalizedOrigin(origin), state: "unbound", targetId: null,
        reservationToken: null, reservationExpiresAt: null, controller: null,
        bindingGeneration: 0, createdAt: now, updatedAt: now,
        releasedAt: null, completedAt: null, completionOutcome: null,
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

    const controlToken = randomUUID();
    record.controller = {
      token: controlToken, owner: String(owner), heartbeatAt: now,
      expiresAt: now + policy.cleanup.heartbeat_stale_ms,
    };
    record.updatedAt = now;
    if (exclusiveContext) {
      state.context_claims[contextKey] = {
        taskSlotKey: key, controlToken, owner: String(owner),
        heartbeatAt: now, expiresAt: record.controller.expiresAt,
      };
    }

    if (record.targetId) {
      const lease = state.leases[leaseKey(port, record.targetId)];
      if (lease?.class === "anchor") {
        clearContextClaimFor(state, record, controlToken);
        record.controller = null;
        throw new Error(`TASK_TAB_ANCHOR_REFUSED: ${record.targetId}`);
      }
      if (lease?.state === "closing") {
        clearContextClaimFor(state, record, controlToken);
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
  owner = "unknown", origin = null, now = Date.now(), policy = loadBrowserPolicy(),
}) {
  assertLeaseInput({ port, targetId, leaseClass: "background-active" });
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    const record = state.task_tabs[key];
    if (!record || record.state !== "reserving"
        || record.reservationToken !== reservationToken
        || record.controller?.token !== controlToken) {
      throw new Error(`TASK_TAB_STALE_RESERVATION: ${taskId}/${slot}`);
    }
    const conflicting = Object.values(state.task_tabs).find((entry) =>
      entry.key !== key && entry.targetId === targetId);
    if (conflicting) throw new Error(`TASK_TAB_TARGET_CONFLICT: ${targetId}`);
    const existingLease = state.leases[leaseKey(port, targetId)];
    if (existingLease?.class === "anchor") {
      throw new Error(`TASK_TAB_ANCHOR_REFUSED: ${targetId}`);
    }
    if (existingLease?.state === "closing") {
      throw new Error(`LEASE_CLOSING: target ${targetId} has already been claimed for cleanup`);
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
    activateLease(lease, { owner, now });
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
  now = Date.now(), policy = loadBrowserPolicy(),
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    const record = state.task_tabs[key];
    if (!record || record.targetId !== targetId || record.controller?.token !== controlToken) {
      throw new Error(`TASK_TAB_STALE_CONTROL: ${taskId}/${slot}`);
    }
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
  port, taskId, slot = "primary", controlToken, now = Date.now(), policy = loadBrowserPolicy(),
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    const record = state.task_tabs[key];
    if (!record || record.controller?.token !== controlToken) return null;
    record.controller.heartbeatAt = now;
    record.controller.expiresAt = now + policy.cleanup.heartbeat_stale_ms;
    record.updatedAt = now;
    if (record.exclusiveContext) {
      const claim = state.context_claims[String(Number(port))];
      if (!claim || claim.taskSlotKey !== key || claim.controlToken !== controlToken) return null;
      claim.heartbeatAt = now;
      claim.expiresAt = record.controller.expiresAt;
    }
    return structuredClone(record);
  });
}

export async function releaseTaskTabControl({
  port, taskId, slot = "primary", controlToken, outcome = "handoff",
  now = Date.now(), policy = loadBrowserPolicy(),
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    const record = state.task_tabs[key];
    if (!record || record.controller?.token !== controlToken) {
      throw new Error(`TASK_TAB_STALE_CONTROL: ${taskId}/${slot}`);
    }
    const lease = record.targetId ? state.leases[leaseKey(port, record.targetId)] : null;
    if (lease && lease.state !== "closing") applyLeaseOutcome(lease, outcome, now, policy);
    clearContextClaimFor(state, record, controlToken);
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
  port, taskId, slot = "primary", controlToken, now = Date.now(),
}) {
  const key = taskSlotKey(port, assertTaskText("taskId", taskId), assertTaskText("slot", slot, 100));
  return transaction((state) => {
    const record = state.task_tabs[key];
    if (!record || record.controller?.token !== controlToken) return null;
    clearContextClaimFor(state, record, controlToken);
    record.controller = null;
    record.reservationExpiresAt = Math.min(Number(record.reservationExpiresAt || now), now);
    record.updatedAt = now;
    return structuredClone(record);
  });
}

export async function completeTaskTabs({
  port, taskId, outcome = "success", now = Date.now(), policy = loadBrowserPolicy(),
}) {
  const normalizedTaskId = assertTaskText("taskId", taskId);
  return transaction((state) => {
    const records = Object.values(state.task_tabs).filter((entry) =>
      entry.port === Number(port) && entry.taskId === normalizedTaskId && !entry.completedAt);
    const busy = records.find((entry) => taskControlIsHealthy(entry.controller, now));
    if (busy) throw new Error(`TASK_TAB_BUSY: ${normalizedTaskId}/${busy.slot}`);
    const released = [];
    for (const record of records) {
      if (record.controller) clearContextClaimFor(state, record, record.controller.token);
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
