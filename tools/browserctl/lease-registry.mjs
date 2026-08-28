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
  return { schema_version: 1, revision: 0, leases: {}, auth_attempts: {} };
}

async function readState() {
  try {
    const value = JSON.parse(await readFile(REGISTRY_PATH, "utf8"));
    if (value.schema_version !== 1 || typeof value.leases !== "object") {
      throw new Error("unsupported lease registry schema");
    }
    value.auth_attempts ||= {};
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

export async function acquireLease({
  port, targetId, leaseClass = "background-active", owner = "unknown", origin = null,
  anchorKey = null, now = Date.now(), policy = loadBrowserPolicy(),
}) {
  assertLeaseInput({ port, targetId, leaseClass });
  return transaction((state) => {
    const key = leaseKey(port, targetId);
    const previous = state.leases[key];
    const lease = {
      port: Number(port), targetId, class: leaseClass, owner: String(owner),
      state: leaseClass === "background-active" ? "active" : "leased",
      origin: normalizedOrigin(origin) || previous?.origin || null,
      anchorKey: anchorKey || (leaseClass === "anchor" ? previous?.anchorKey || null : null),
      acquiredAt: previous?.acquiredAt || now,
      updatedAt: now,
      heartbeatAt: leaseClass === "background-active" ? now : previous?.heartbeatAt || null,
      lastActivityAt: previous?.lastActivityAt || now,
      expiresAt: expiryFor(leaseClass, now, policy),
      outcome: previous?.outcome || null,
    };
    state.leases[key] = lease;
    return structuredClone(lease);
  });
}

export async function touchLease({ port, targetId, kind = "activity", now = Date.now(), policy = loadBrowserPolicy() }) {
  return transaction((state) => {
    const key = leaseKey(port, targetId);
    const lease = state.leases[key];
    if (!lease) return null;
    if (kind === "heartbeat") {
      if (lease.class === "background-active") lease.heartbeatAt = now;
    } else {
      lease.lastActivityAt = Math.max(Number(lease.lastActivityAt || 0), now);
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
    if (outcome === "success") {
      lease.class = "background-success";
      lease.state = "released";
      lease.expiresAt = now + policy.cleanup.background_grace_ms;
    } else if (outcome === "interactive") {
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
    lease.updatedAt = now;
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
    lease.expiresAt = now + policy.cleanup.interactive_idle_ms;
    lease.updatedAt = now;
    return structuredClone(lease);
  });
}

export async function recordActivityProbeFailure({ port, targetId, now = Date.now() }) {
  return transaction((state) => {
    const lease = state.leases[leaseKey(port, targetId)];
    if (!lease) return null;
    lease.activityProbeFailedAt = now;
    lease.updatedAt = now;
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
    lease.lastActivityAt = now;
    lease.expiresAt = now + policy.cleanup.interactive_idle_ms;
    lease.updatedAt = now;
    delete lease.activityProbeFailedAt;
    return structuredClone(lease);
  });
}

export async function removeLease({ port, targetId }) {
  return transaction((state) => delete state.leases[leaseKey(port, targetId)]);
}

export async function listLeases() {
  const state = await readState();
  return Object.values(state.leases).map((lease) => structuredClone(lease));
}

export async function claimExpiredLease({ port, targetId, expectedUpdatedAt, now = Date.now() }) {
  return transaction((state) => {
    const lease = state.leases[leaseKey(port, targetId)];
    if (!lease || lease.class === "anchor" || lease.class === "background-active") return null;
    if (Number(lease.updatedAt) !== Number(expectedUpdatedAt) || Number(lease.expiresAt || Infinity) > now) return null;
    lease.state = "closing";
    lease.updatedAt = now;
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
