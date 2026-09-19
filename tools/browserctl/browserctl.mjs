#!/usr/bin/env node
import { spawn, spawnSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  authAttemptStatus, recordAuthAttempt, setAnchorAuthRequired,
  acquireLease, adoptUnregisteredLease, claimExpiredLease, listLeases, recordActivityProbeFailure,
  releaseLease, removeLease, restartActivityMeasurement, touchLease,
  transitionMissedHeartbeat, listTaskTabs, completeTaskTabs, detachTaskTab, regionTabState, surplusAnchorLeases,
} from "./lease-registry.mjs";
import { anchorAuthState, anchorMatchesUrl, loadBrowserPolicy, policyForPort } from "./policy.mjs";
import { sessionEnvironment } from "./session.mjs";
import { acquireSessionLock, acquireSessionLockWithWait, sessionLockHasChildren } from "./session-lock.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const CDP_MODULE = resolve(HERE, "../report-fetcher/cdp.mjs");
const LAUNCHER = resolve(HERE, "../report-fetcher/launch-chrome-debug.py");

function parseArgs(argv) {
  const positional = [];
  const options = {};
  for (let i = 0; i < argv.length; i++) {
    const value = argv[i];
    if (!value.startsWith("--")) { positional.push(value); continue; }
    const key = value.slice(2);
    if (argv[i + 1] && !argv[i + 1].startsWith("--")) options[key] = argv[++i];
    else options[key] = true;
  }
  return { positional, options };
}

function required(options, key) {
  const value = options[key];
  if (value == null || value === "") throw new Error(`ARGUMENT_REQUIRED: --${key}`);
  return value;
}

function portNumber(value) {
  const port = Number(value);
  if (![9222, 9223].includes(port)) throw new Error(`UNSUPPORTED_CDP_PORT: ${value}`);
  return port;
}

function safeOrigin(rawUrl) {
  try { return new URL(rawUrl).origin; } catch { return null; }
}

function launcherEnv(port, policy) {
  const config = policyForPort(port, policy);
  return {
    ...process.env,
    AMAZON_BROWSER_SESSION: port === 9223 ? "grimoire" : "operator",
    CDP_PORT: String(port),
    CDP_PROFILE: config.profile,
    CDP_START_URL: config.start_url,
    CDP_BROWSER_MODE: config.mode,
    ...(config.chrome_bin ? { CHROME_BIN: config.chrome_bin } : {}),
    ...(config.window_class ? { CDP_WINDOW_CLASS: config.window_class } : {}),
  };
}

function pythonCommand() {
  for (const command of [process.env.CDP_PYTHON, "python3", "python"].filter(Boolean)) {
    const probe = spawnSync(command, ["--version"], { encoding: "utf8" });
    if (!probe.error && probe.status === 0) return command;
  }
  throw new Error("No Python interpreter is available for the Chrome launcher");
}

function runLauncher(port, args, policy, extraEnv = {}) {
  const result = spawnSync(pythonCommand(), [LAUNCHER, ...args], {
    env: { ...launcherEnv(port, policy), ...extraEnv }, encoding: "utf8", timeout: 30000,
  });
  if (result.error || result.status !== 0) {
    const detail = (result.stderr || result.stdout || result.error?.message || "launcher failed").trim();
    throw new Error(detail);
  }
  return result.stdout.trim();
}

function launcherStatus(port, policy) {
  return JSON.parse(runLauncher(port, ["--mode", "status"], policy));
}

async function cdpForPort(port, policy) {
  const config = policyForPort(port, policy);
  process.env.CDP_PORT = String(port);
  process.env.AMAZON_BROWSER_SESSION = port === 9223 ? "grimoire" : "operator";
  process.env.CDP_PROFILE = config.profile;
  process.env.CDP_START_URL = config.start_url;
  process.env.CDP_BROWSER_MODE = config.mode;
  if (config.chrome_bin) process.env.CHROME_BIN = config.chrome_bin;
  else delete process.env.CHROME_BIN;
  if (config.window_class) process.env.CDP_WINDOW_CLASS = config.window_class;
  else delete process.env.CDP_WINDOW_CLASS;
  return import(`${pathToFileURL(CDP_MODULE).href}?browserctl=${port}-${Date.now()}-${Math.random()}`);
}

export async function ensureAnchors(port, { policy = loadBrowserPolicy(), cdp = null, now = Date.now(), auditOnly = false } = {}) {
  const config = policyForPort(port, policy);
  cdp ||= await cdpForPort(port, policy);
  const pages = await cdp.listPages();
  const pageById = new Map(pages.map((page) => [page.id, page]));
  const regions = await regionTabState(port, { now });
  const actions = [];
  const detached = new Set();
  for (const region of regions) {
    const anchor = config.anchors.find((entry) => entry.key === region.anchorKey);
    const page = pageById.get(region.targetId);
    // Login recovery keeps the permanent target even after its worker expires.
    if (anchor && page && anchorAuthState(anchor, page.url) === "auth") continue;
    if (region.boundTaskId && !region.controllerFresh) {
      if (auditOnly) {
        detached.add(region.targetId);
        actions.push({ action: "would-reclassify", targetId: region.targetId, key: region.anchorKey,
          class: "inspection", reason: "heartbeat-lost" });
      } else await transitionMissedHeartbeat({ port, targetId: region.targetId, now, policy });
    }
  }
  let leases = (await listLeases()).filter((lease) => lease.port === Number(port));
  const leasedTargetIds = new Set(leases.map((lease) => lease.targetId));
  const used = new Set();
  const kept = [];
  const created = [];
  const reclassified = [];
  const skipped = [];
  const cooldownMs = policy.cleanup.auth_retry_cooldown_ms;
  const authScope = (anchor) => ({ port, targetId: "anchor-origin", routeId: safeOrigin(anchor.url) });

  const fresh = new Set(regions.filter((region) => region.controllerFresh && pageById.has(region.targetId))
    .map((region) => region.targetId));
  const surplus = new Map((await surplusAnchorLeases(port, new Set([...pageById.keys()].filter((id) => !detached.has(id)))))
    .filter((lease) => !detached.has(lease.targetId))
    .map((lease) => [lease.targetId, lease]));
  // A controlled region wins over registry order until its controller releases.
  for (const region of regions.filter((entry) => fresh.has(entry.targetId))) {
    surplus.delete(region.targetId);
    for (const lease of leases) {
      if (lease.class === "anchor" && lease.anchorKey === region.anchorKey
          && !fresh.has(lease.targetId) && !detached.has(lease.targetId)) {
        surplus.set(lease.targetId, lease);
      }
    }
  }
  for (const lease of surplus.values()) {
    const page = pageById.get(lease.targetId);
    if (!page) {
      if (auditOnly) actions.push({ action: "would-remove", targetId: lease.targetId, reason: "target-missing" });
      else await removeLease({ port, targetId: lease.targetId });
      continue;
    }
    if (auditOnly) actions.push({ action: "would-reclassify", targetId: page.id, key: lease.anchorKey,
      class: "inspection", reason: "duplicate-anchor" });
    else await acquireLease({
      port, targetId: page.id, leaseClass: "inspection", owner: "browserctl:anchor-duplicate",
      origin: safeOrigin(page.url), anchorKey: null, now, policy,
    });
    reclassified.push({ key: lease.anchorKey, targetId: page.id, origin: safeOrigin(page.url) });
  }
  leases = (await listLeases()).filter((lease) => lease.port === Number(port)
    && !(auditOnly && (surplus.has(lease.targetId) || detached.has(lease.targetId))));

  for (const anchor of config.anchors) {
    const registered = leases.find((lease) => lease.class === "anchor" && lease.anchorKey === anchor.key);
    const page = registered && pageById.get(registered.targetId);
    if (!page) {
      if (registered) {
        if (auditOnly) actions.push({ action: "would-remove", targetId: registered.targetId, reason: "target-missing" });
        else await removeLease({ port, targetId: registered.targetId });
      }
      continue;
    }
    const authState = anchorAuthState(anchor, page.url);
    if (authState === "auth") {
      const attempt = await authAttemptStatus({ ...authScope(anchor), now, cooldownMs });
      if (!auditOnly) {
        await setAnchorAuthRequired({ port, targetId: page.id, required: true, now });
        if (attempt.allowed) await recordAuthAttempt({ ...authScope(anchor), now });
      }
      used.add(page.id);
      kept.push({ key: anchor.key, targetId: page.id, url: page.url, source: "registry", reason: "auth-required" });
      skipped.push({ key: anchor.key, reason: "auth-required", retryAt: auditOnly ? null : attempt.allowed ? now + cooldownMs : attempt.retryAt });
      continue;
    }
    if (registered.authRequired && !auditOnly) {
      await setAnchorAuthRequired({ port, targetId: page.id, required: false, now });
    }
    if (authState === "ok" || fresh.has(registered.targetId)) {
      used.add(page.id);
      kept.push({ key: anchor.key, targetId: page.id, url: page.url, source: "registry" });
      continue;
    }
    if (auditOnly) actions.push({ action: "would-reclassify", targetId: page.id, key: anchor.key,
      class: "interactive", reason: "anchor-navigation", reclassifiedAt: now });
    else await acquireLease({
      port, targetId: page.id, leaseClass: "interactive", owner: "browserctl:anchor-navigation",
      origin: safeOrigin(page.url), now, policy,
    });
    reclassified.push({ key: anchor.key, targetId: page.id, origin: safeOrigin(page.url), reclassifiedAt: now });
  }

  leases = (await listLeases()).filter((lease) => lease.port === Number(port));
  if (auditOnly) leases = leases.map((lease) => {
    const preview = reclassified.find((entry) => entry.targetId === lease.targetId && entry.reclassifiedAt != null);
    return preview ? { ...lease, class: "interactive", owner: "browserctl:anchor-navigation",
      anchorKey: null, origin: preview.origin, reclassifiedAt: preview.reclassifiedAt } : lease;
  });
  for (const anchor of config.anchors) {
    if (kept.some((entry) => entry.key === anchor.key)) continue;
    const liveAnchor = leases.find((lease) => lease.class === "anchor" && lease.anchorKey === anchor.key
      && pageById.has(lease.targetId) && !(auditOnly && (surplus.has(lease.targetId) || detached.has(lease.targetId)
        || reclassified.some((entry) => entry.targetId === lease.targetId))));
    const attempt = await authAttemptStatus({ ...authScope(anchor), now, cooldownMs });
    const recent = leases.filter((lease) =>
      (lease.owner === "browserctl:anchor-navigation" || lease.class === "inspection")
      && (lease.anchorKey === anchor.key || lease.origin === safeOrigin(anchor.url)
        || anchor.auth_origins.includes(lease.origin))
      && Number(lease.reclassifiedAt ?? lease.updatedAt) + cooldownMs > now);
    if (liveAnchor || !attempt.allowed || recent.length) {
      skipped.push({ key: anchor.key,
        reason: liveAnchor ? "live-anchor" : !attempt.allowed ? "auth-cooldown" : "inspection-cooldown",
        retryAt: liveAnchor ? null : !attempt.allowed ? attempt.retryAt
          : Math.max(...recent.map((lease) => Number(lease.reclassifiedAt ?? lease.updatedAt) + cooldownMs)) });
      continue;
    }
    const existing = pages.find((page) =>
      !used.has(page.id) && !leasedTargetIds.has(page.id) && anchorMatchesUrl(anchor, page.url));
    if (existing) {
      if (auditOnly) actions.push({ action: "would-reclassify", targetId: existing.id, key: anchor.key,
        class: "anchor", reason: "anchor-adoption" });
      else await acquireLease({
        port, targetId: existing.id, leaseClass: "anchor", owner: "browserctl:anchor",
        origin: safeOrigin(existing.url), anchorKey: anchor.key, policy,
      });
      used.add(existing.id);
      kept.push({ key: anchor.key, targetId: existing.id, url: existing.url, source: "adopted" });
      continue;
    }
    if (auditOnly) {
      actions.push({ action: "would-create", key: anchor.key, url: anchor.url });
      continue;
    }
    const opened = await cdp.createPage(anchor.url, {
      leaseClass: "anchor", owner: "browserctl:anchor", anchorKey: anchor.key,
    });
    opened.session.close();
    used.add(opened.targetId);
    created.push({ key: anchor.key, targetId: opened.targetId, url: anchor.url });
    kept.push({ key: anchor.key, targetId: opened.targetId, url: anchor.url, source: "created" });
  }

  return { port: Number(port), kept, created, reclassified, skipped, closed: [], ...(auditOnly ? { actions } : {}) };
}

function profileMismatch(port, policy) {
  return `PROFILE_MISMATCH: port ${port} is served by a browser whose profile is not ${policyForPort(port, policy).profile}`;
}

export async function ensureBrowser(port, { policy = loadBrowserPolicy(), cdp = null, getStatus = launcherStatus } = {}) {
  const status = getStatus(port, policy);
  if (status.running && status.profile_verified === false) throw new Error(profileMismatch(port, policy));
  const profileVerified = status.profile_verified ?? null;
  if (profileVerified === null) console.warn(`PROFILE_UNVERIFIED: port ${port}; listener profile could not be verified`);
  const configuredMode = policyForPort(port, policy).mode;
  if (status.running && !status.managed) {
    throw new Error(`UNMANAGED_CDP_BROWSER: port ${port} is reachable but is not owned by browserctl`);
  }
  if (status.running && status.managed && status.mode && status.mode !== configuredMode) {
    throw new Error(`MODE_CHANGE_REQUIRES_RESTART: port ${port} is ${status.mode}; configured mode is ${configuredMode}`);
  }
  cdp ||= await cdpForPort(port, policy);
  const version = await cdp.ensureChrome();
  const anchors = await ensureAnchors(port, { policy, cdp });
  return { port: Number(port), browser: version.Browser, mode: status.running ? status.mode : configuredMode, profileVerified, anchors };
}

async function probeActivity(cdp, page) {
  let session;
  let interaction = null;
  let stage = "connect";
  try {
    session = await cdp.Session.open(page.webSocketDebuggerUrl);
    stage = "read-activity";
    const initial = await cdp.readLeaseActivity(session);
    if (initial.error) return { ...initial, interaction, stage };
    interaction = cdp.readLeaseInteraction ? await cdp.readLeaseInteraction(session) : null;
    if (initial.ok) return { ...initial, interaction, measurementRestored: false };

    // A tracker installed through a short-lived CDP session survives in the
    // current document, but Chrome removes the new-document registration when
    // that session disconnects. Navigation can therefore leave a healthy tab
    // temporarily unmeasurable. Reinstall in the current document and treat
    // this moment as the start of a fresh, conservative inspection window.
    // A missing tracker can be restored. An inaccessible renderer is not
    // evidence of a missing tracker; preserve its original failure instead.
    stage = "install-tracker";
    await cdp.installLeaseActivityTracker(session);
    stage = "read-restored-activity";
    const restored = await cdp.readLeaseActivity(session);
    if (!restored.ok) return { ...restored, interaction, stage };
    return { ...restored, interaction, measurementRestored: true };
  } catch (error) {
    return { ok: false, value: null, interaction, stage, error: error.message };
  } finally {
    session?.close();
  }
}

export async function cleanupPort(port, {
  policy = loadBrowserPolicy(), auditOnly = policy.cleanup.mode !== "active", now = Date.now(),
  cdp = null, managedStatus = null, maintainAnchors = true,
} = {}) {
  try {
    managedStatus ||= launcherStatus(port, policy);
  } catch (error) {
    return { port: Number(port), reachable: false, auditOnly, actions: [], error: error.message };
  }
  const profileVerified = managedStatus.profile_verified ?? null;
  if (profileVerified === null) console.warn(`PROFILE_UNVERIFIED: port ${port}; listener profile could not be verified`);
  if (managedStatus.running && managedStatus.profile_verified === false) {
    return { port: Number(port), profileVerified, reachable: true, auditOnly, actions: [], anchorMaintenance: null,
      error: profileMismatch(port, policy) };
  }
  const configuredMode = policyForPort(port, policy).mode;
  if (!managedStatus.managed || managedStatus.mode !== configuredMode) {
    return {
      port: Number(port), profileVerified, reachable: Boolean(managedStatus.running), auditOnly, actions: [],
      error: !managedStatus.managed
        ? "UNMANAGED_CDP_BROWSER"
        : `MODE_CHANGE_REQUIRES_RESTART: running ${managedStatus.mode}; configured ${configuredMode}`,
    };
  }
  cdp ||= await cdpForPort(port, policy);
  let pages;
  let anchorMaintenance = null;
  try {
    await cdp.assertChrome();
    if (maintainAnchors) {
      try {
        const maintained = await ensureAnchors(port, { policy, cdp, now, auditOnly });
        anchorMaintenance = {
          kept: maintained.kept.length,
          created: maintained.created.length,
          reclassified: maintained.reclassified.length,
          skipped: maintained.skipped,
          ...(auditOnly ? { actions: maintained.actions } : {}),
        };
      } catch (error) { anchorMaintenance = { error: error.message }; }
    }
    pages = await cdp.listPages();
  } catch (error) {
    return { port: Number(port), profileVerified, reachable: false, auditOnly, actions: [], error: error.message };
  }
  const pageById = new Map(pages.map((page) => [page.id, page]));
  const actions = [];
  let leases = (await listLeases()).filter((lease) => lease.port === Number(port));
  const adoptedTargetIds = new Set();

  if (policy.cleanup.adopt_unregistered_tabs) {
    const registeredTargetIds = new Set(leases.map((lease) => lease.targetId));
    for (const page of pages) {
      if (registeredTargetIds.has(page.id)) continue;
      if (auditOnly) {
        const activity = await probeActivity(cdp, page);
        actions.push({ port: Number(port), action: "would-adopt", targetId: page.id,
          class: "inspection", origin: safeOrigin(page.url), reason: "unregistered-target-observed",
          activityTracked: activity.ok,
          ...(activity.ok ? {} : { probe: publicProbeFailure(activity) }),
        });
        continue;
      }
      const adoption = await adoptUnregisteredLease({
        port, targetId: page.id, origin: safeOrigin(page.url), now, policy,
      });
      if (!adoption.adopted) continue;
      adoptedTargetIds.add(page.id);
      leases.push(adoption.lease);
      const activity = await probeActivity(cdp, page);
      if (!activity.ok) {
        await recordActivityProbeFailure({ port, targetId: page.id, now });
      }
      actions.push({
        port: Number(port), action: "adopted-for-inspection", targetId: page.id,
        class: adoption.lease.class, origin: safeOrigin(page.url),
        reason: "unregistered-target-observed", expiresAt: adoption.lease.expiresAt,
        activityTracked: activity.ok,
        ...(activity.ok ? {} : { probe: publicProbeFailure(activity) }),
      });
    }
  }

  for (let lease of leases) {
    if (adoptedTargetIds.has(lease.targetId)) continue;
    const page = pageById.get(lease.targetId);
    if (!page) {
      if (!auditOnly) await removeLease({
        port, targetId: lease.targetId, expectedCloseToken: lease.closeToken || null,
      });
      actions.push({
        port: Number(port), action: auditOnly ? "would-remove" : "removed-stale-lease", targetId: lease.targetId,
        class: lease.class, origin: lease.origin || null, reason: "target-missing",
        expiresAt: lease.expiresAt || null,
      });
      continue;
    }
    if (lease.class === "anchor") continue;
    if (lease.class === "background-active") {
      const transitioned = await transitionMissedHeartbeat({ port, targetId: lease.targetId, now, policy });
      if (transitioned?.class === "inspection") {
        actions.push({
          port: Number(port), action: "promoted-to-inspection", targetId: lease.targetId,
          class: transitioned.class,
          origin: safeOrigin(page.url), reason: "heartbeat-lost", expiresAt: transitioned.expiresAt,
        });
      }
      continue;
    }

    const activity = await probeActivity(cdp, page);
    if (activity.interaction?.ok && activity.interaction.lastInteractionAt > Number(lease.lastObservedInteractionAt || 0)) {
      lease = await touchLease({ port, targetId: lease.targetId, kind: "interaction",
        now: activity.interaction.lastInteractionAt, policy });
      if (!lease) continue;
    }
    if (!activity.ok) {
      const busy = String(activity.error || "").startsWith("BROWSER_SESSION_BUSY:");
      if (!busy) await recordActivityProbeFailure({ port, targetId: lease.targetId, now });
      actions.push({
        port: Number(port), action: "preserved", targetId: lease.targetId, class: lease.class,
        origin: safeOrigin(page.url), reason: busy ? "session-busy" : "activity-unavailable", expiresAt: lease.expiresAt,
        probe: publicProbeFailure(activity),
      });
      continue;
    }
    if (activity.measurementRestored) {
      lease = await restartActivityMeasurement({
        port, targetId: lease.targetId, now: Math.max(now, Number(activity.value)), policy,
      });
      // Another controller may have reacquired or removed the target while
      // this cleanup pass was probing it.
      if (!lease) continue;
      actions.push({
        port: Number(port), action: "activity-tracker-restored", targetId: lease.targetId,
        class: lease.class, origin: safeOrigin(page.url), reason: "measurement-restarted",
        expiresAt: lease.expiresAt,
      });
      continue;
    }
    // Focus and visibility events verify measurement, but do not extend retention.
    if (!lease?.expiresAt || Number(lease.expiresAt) > now) continue;

    const candidate = {
      port: Number(port), action: auditOnly ? "would-close" : "close", targetId: lease.targetId,
      class: lease.class, origin: safeOrigin(page.url), reason: "lease-expired",
      expiresAt: lease.expiresAt,
    };
    if (auditOnly) {
      actions.push(candidate);
      continue;
    }
    const claim = await claimExpiredLease({
      port, targetId: lease.targetId, expectedUpdatedAt: lease.updatedAt,
      expectedGeneration: lease.generation, now,
    });
    if (!claim) {
      actions.push({ ...candidate, action: "preserved", reason: "lease-changed-before-close" });
      continue;
    }
    try {
      await cdp.closePageImmediately(lease.targetId, {
        explicit: true, reason: `expired ${lease.class} lease`,
      });
      await removeLease({ port, targetId: lease.targetId, expectedCloseToken: claim.closeToken });
      actions.push(candidate);
    } catch (error) {
      await acquireLease({
        port, targetId: lease.targetId, leaseClass: "inspection", owner: "browserctl:close-failed",
        origin: safeOrigin(page.url), policy, recoverClosing: true,
      });
      actions.push({ ...candidate, action: "preserved", reason: "close-failed" });
    }
  }
  const incomplete = actions.some(action => action.reason === "activity-unavailable"
    || action.reason === "session-busy" || action.reason === "close-failed" || action.activityTracked === false);
  return { port: Number(port), profileVerified, reachable: true, auditOnly, complete: !incomplete, anchorMaintenance, actions };
}

function publicProbeFailure(activity) {
  const message = String(activity.error || "Activity tracker returned no valid measurement");
  // CDP timeout/connection errors are useful; exclude URLs and multiline page
  // exception contents from persistent cleanup diagnostics.
  return { stage: activity.stage || "read-activity",
    error: message.split("\n")[0].replace(/(?:https?|wss?):\/\/\S+/g, "[endpoint]").slice(0, 240) };
}

export async function cleanupPortWithLock(port, {
  lockWaitMs = 120_000, ...options
} = {}, {
  acquire = acquireSessionLock, cleanup = cleanupPort, clock = Date.now,
  sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
} = {}) {
  if (!Number.isSafeInteger(lockWaitMs) || lockWaitMs < 0) throw new Error("INVALID_LOCK_WAIT_MS");
  let unlock;
  try {
    unlock = await acquireSessionLockWithWait(port, "browserctl:cleanup", {
      lockWaitMs, retryIntervalMs: 5000,
    }, { acquire, clock, sleep });
  } catch (error) {
    if (String(error.message).startsWith("BROWSER_SESSION_BUSY")) {
      return { port: Number(port), status: "deferred", reason: "session-busy",
        waitMs: error.waitMs, auditOnly: options.auditOnly, complete: false, actions: [] };
    }
    return { port: Number(port), complete: false, actions: [], error: error.message };
  }
  try {
    return await cleanup(port, options);
  } finally { unlock(); }
}

export function cleanupSummary(results, mode) {
  const complete = results.every(result => result.reachable && !result.error && result.complete !== false);
  const deferred = !complete && results.every(result =>
    (result.status === "deferred" && result.reason === "session-busy" && !result.error)
    || (result.reachable && !result.error
    && (result.complete !== false || (result.actions?.some(action => action.reason === "session-busy")
      && result.actions.every(action => action.reason === "session-busy"
        || (!action.probe && action.activityTracked !== false
          && !["activity-unavailable", "close-failed"].includes(action.reason)))))));
  return { ok: complete || deferred, complete, status: complete ? "complete" : deferred ? "deferred" : "incomplete", mode, results };
}

async function statusCommand(port, policy) {
  const status = launcherStatus(port, policy);
  const leases = (await listLeases()).filter((lease) => lease.port === Number(port));
  return {
    ...status,
    configured_mode: policyForPort(port, policy).mode,
    routing: policy.routing,
    lease_counts: Object.fromEntries([...new Set(leases.map((lease) => lease.class))]
      .map((kind) => [kind, leases.filter((lease) => lease.class === kind).length])),
  };
}

async function authCommand(port, targetId, policy) {
  const module = await import("./auth-broker.mjs");
  return module.authenticateTarget({ port, targetId, policy });
}

export async function acquireTargetLease({
  port, targetId, leaseClass, owner, origin = null, anchorKey = null,
  policy = loadBrowserPolicy(), cdp = null,
}) {
  cdp ||= await cdpForPort(port, policy);
  const page = (await cdp.listPages()).find((entry) => entry.id === targetId);
  if (!page) throw new Error(`CDP_TARGET_NOT_FOUND: ${targetId}`);
  const lease = await acquireLease({
    port, targetId, leaseClass, owner,
    origin: origin || safeOrigin(page.url), anchorKey, policy,
  });
  let session;
  try {
    session = await cdp.Session.open(page.webSocketDebuggerUrl);
    await cdp.installLeaseActivityTracker(session);
    return { lease, activityTracked: true };
  } catch {
    await recordActivityProbeFailure({ port, targetId });
    return { lease, activityTracked: false };
  } finally {
    session?.close();
  }
}

export async function main(raw = process.argv.slice(2), { cleanup = cleanupPortWithLock, fetch = globalThis.fetch } = {}) {
  if (raw.includes("--help")) {
    console.log("Usage: browserctl ensure|status|restart|lease|task|region|cleanup|auth");
    return;
  }
  const separator = raw.indexOf("--");
  if (["run", "session"].includes(raw[0])) {
    const { options } = parseArgs(separator < 0 ? raw : raw.slice(0, separator));
    const env = { ...process.env, ...sessionEnvironment(options.session) };
    if (raw[0] === "session") {
      console.log(JSON.stringify(sessionEnvironment(options.session)));
      return;
    }
    const command = separator < 0 ? [] : raw.slice(separator + 1);
    if (!command.length) throw new Error("USAGE: browserctl run --session grimoire -- command [args]");
    const lockWaitMs = options["lock-wait-ms"] === undefined ? 120_000 : Number(options["lock-wait-ms"]);
    if (options["lock-wait-ms"] === true) throw new Error("INVALID_LOCK_WAIT_MS");
    let unlock = await acquireSessionLockWithWait(Number(env.CDP_PORT), "browserctl:run", { lockWaitMs });
    env.AMAZON_BROWSER_LOCK_TOKEN = process.env.AMAZON_BROWSER_LOCK_TOKEN || "";
    env.AMAZON_BROWSER_LOCK_CHAIN = process.env.AMAZON_BROWSER_LOCK_CHAIN || "[]";
    env.AMAZON_BROWSER_LAUNCHER_CONTROL = "sigusr1-v1";
    env.AMAZON_BROWSER_LAUNCHER_PID = String(process.pid);
    env.AMAZON_BROWSER_LOCK_WAIT_MS = String(lockWaitMs);
    try {
      const child = spawn(command[0], command.slice(1), { env, stdio: "inherit" });
      const releaseEarly = () => {
        if (!unlock || sessionLockHasChildren(Number(env.CDP_PORT))) return;
        unlock(); unlock = null;
      };
      process.on("SIGUSR1", releaseEarly);
      const forwardTerm = () => child.kill("SIGTERM");
      const forwardInt = () => child.kill("SIGINT");
      process.on("SIGTERM", forwardTerm); process.on("SIGINT", forwardInt);
      try {
        process.exitCode = await new Promise((resolve, reject) => {
          child.once("error", reject);
          child.once("exit", (code, signal) => resolve(code ?? (signal === "SIGINT" ? 130 : 143)));
        });
      } finally { process.off("SIGUSR1", releaseEarly); process.off("SIGTERM", forwardTerm); process.off("SIGINT", forwardInt); }
    } finally { unlock?.(); }
    return;
  }
  const { positional, options } = parseArgs(raw);
  const [command, subcommand] = positional;
  const policy = loadBrowserPolicy();
  if (command === "ensure") {
    console.log(JSON.stringify({ ok: true, ...(await ensureBrowser(portNumber(required(options, "port")), { policy })) }));
    return;
  }
  if (command === "status") {
    console.log(JSON.stringify({ ok: true, ...(await statusCommand(portNumber(required(options, "port")), policy)) }));
    return;
  }
  if (command === "restart") {
    const port = portNumber(required(options, "port"));
    const mode = required(options, "mode");
    const reason = String(required(options, "reason")).trim();
    if (!new Set(["headed", "headless", "recovery"]).has(mode)) throw new Error(`UNSUPPORTED_BROWSER_MODE: ${mode}`);
    if (!reason) throw new Error("ARGUMENT_REQUIRED: --reason");
    const restartEnv = {
      CDP_BROWSERCTL_RESTART: "1",
      CDP_EXPLICIT_RESTART_REASON: reason,
    };
    const unlock = acquireSessionLock(port, "browserctl:restart");
    try {
      const active = (await listTaskTabs()).filter(task => task.port === port && task.controller?.expiresAt > Date.now());
      if (active.length) throw new Error("BROWSER_RESTART_BUSY: wait for active workflow controllers to release");
      runLauncher(port, ["--mode", "stop"], policy, restartEnv);
      runLauncher(port, ["--mode", mode], policy, restartEnv);
    } finally { unlock(); }
    console.log(JSON.stringify({ ok: true, port, mode, restarted: true, reason }));
    return;
  }
  if (command === "lease") {
    const port = portNumber(required(options, "port"));
    const targetId = required(options, "target");
    let result;
    let metadata = {};
    if (subcommand === "acquire") {
      const acquired = await acquireTargetLease({
        port, targetId, leaseClass: required(options, "class"), owner: required(options, "owner"),
        origin: options.origin || null, anchorKey: options.anchor || null, policy,
      });
      result = acquired.lease;
      metadata = { activity_tracked: acquired.activityTracked };
    } else if (subcommand === "touch") {
      result = await touchLease({ port, targetId, kind: options.kind || "activity", policy });
    } else if (subcommand === "release") {
      result = await releaseLease({ port, targetId, outcome: options.outcome || "success", policy });
    } else throw new Error("USAGE: browserctl lease acquire|touch|release");
    console.log(JSON.stringify({ ok: true, lease: result, ...metadata }));
    return;
  }
  if (command === "task") {
    const port = portNumber(required(options, "port"));
    const taskId = required(options, "task-id");
    const outcome = options.outcome || (subcommand === "detach" ? "inspection" : "success");
    if (!["success", "error", "inspection"].includes(outcome)) throw new Error(`UNSUPPORTED_TASK_OUTCOME: ${outcome}`);
    let result;
    if (subcommand === "complete") {
      policyForPort(port, policy);
      result = await completeTaskTabs({ port, taskId, outcome, policy });
    } else if (subcommand === "detach") {
      result = await detachTaskTab({ port, taskId, slot: required(options, "slot"),
        controlToken: required(options, "control-token"), outcome, policy });
    } else throw new Error("USAGE: browserctl task complete|detach");
    console.log(JSON.stringify({ ok: true, result }));
    return;
  }
  if (command === "region" && subcommand === "state") {
    const port = portNumber(required(options, "port"));
    const regions = await regionTabState(port);
    let pages = [];
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`, { signal: AbortSignal.timeout(2000) });
      if (response.ok) {
        const targets = await response.json();
        if (Array.isArray(targets)) pages = targets.filter(page => page?.type === "page");
      }
    } catch { /* An offline browser still has useful stored region state. */ }
    const pageById = new Map(pages.map(page => [page.id, page]));
    console.log(JSON.stringify({ ok: true, port, regions: regions.map(region => ({
      ...region, liveUrl: pageById.get(region.targetId)?.url ?? null,
      title: pageById.get(region.targetId)?.title ?? null,
    })) }));
    return;
  }
  if (command === "cleanup") {
    const ports = options.port ? [portNumber(options.port)] : [9222, 9223];
    const results = [];
    const lockWaitMs = options["lock-wait-ms"] === undefined ? 120_000 : Number(options["lock-wait-ms"]);
    if (options["lock-wait-ms"] === true || !Number.isSafeInteger(lockWaitMs) || lockWaitMs < 0) throw new Error("INVALID_LOCK_WAIT_MS");
    for (const port of ports) results.push(await cleanup(port, { policy, lockWaitMs, auditOnly: options["audit-only"] === true || policy.cleanup.mode !== "active" }));
    const summary = cleanupSummary(results, options["audit-only"] === true || policy.cleanup.mode !== "active" ? "audit" : "active");
    console.log(JSON.stringify(summary));
    if (summary.status === "incomplete") process.exitCode = 1;
    return;
  }
  if (command === "auth") {
    const port = portNumber(required(options, "port"));
    const targetId = required(options, "target");
    console.log(JSON.stringify({ ok: true, ...(await authCommand(port, targetId, policy)) }));
    return;
  }
  throw new Error("USAGE: browserctl ensure|status|restart|lease|task|region|cleanup|auth");
}

if (process.argv[1] && realpathSync(resolve(process.argv[1])) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.log(JSON.stringify({ ok: false, error: error.message }));
    process.exitCode = 1;
  });
}
