#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  acquireLease, claimExpiredLease, listLeases, recordActivityProbeFailure,
  releaseLease, removeLease, restartActivityMeasurement, touchLease,
  transitionMissedHeartbeat,
} from "./lease-registry.mjs";
import { anchorMatchesUrl, loadBrowserPolicy, policyForPort } from "./policy.mjs";

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
  process.env.CDP_PROFILE = config.profile;
  process.env.CDP_START_URL = config.start_url;
  process.env.CDP_BROWSER_MODE = config.mode;
  if (config.chrome_bin) process.env.CHROME_BIN = config.chrome_bin;
  else delete process.env.CHROME_BIN;
  if (config.window_class) process.env.CDP_WINDOW_CLASS = config.window_class;
  else delete process.env.CDP_WINDOW_CLASS;
  return import(`${pathToFileURL(CDP_MODULE).href}?browserctl=${port}-${Date.now()}-${Math.random()}`);
}

export async function ensureAnchors(port, { policy = loadBrowserPolicy(), cdp = null } = {}) {
  const config = policyForPort(port, policy);
  cdp ||= await cdpForPort(port, policy);
  const pages = await cdp.listPages();
  const pageById = new Map(pages.map((page) => [page.id, page]));
  const leases = (await listLeases()).filter((lease) => lease.port === Number(port));
  const used = new Set();
  const kept = [];
  const created = [];
  const reclassified = [];

  for (const anchor of config.anchors) {
    const registered = leases.find((lease) => lease.class === "anchor" && lease.anchorKey === anchor.key);
    const page = registered && pageById.get(registered.targetId);
    if (!page) continue;
    if (anchorMatchesUrl(anchor, page.url)) {
      used.add(page.id);
      kept.push({ key: anchor.key, targetId: page.id, url: page.url, source: "registry" });
      continue;
    }
    await acquireLease({
      port, targetId: page.id, leaseClass: "interactive", owner: "browserctl:anchor-navigation",
      origin: safeOrigin(page.url), policy,
    });
    reclassified.push({ key: anchor.key, targetId: page.id, origin: safeOrigin(page.url) });
  }

  for (const anchor of config.anchors) {
    if (kept.some((entry) => entry.key === anchor.key)) continue;
    const existing = pages.find((page) => !used.has(page.id) && anchorMatchesUrl(anchor, page.url));
    if (existing) {
      await acquireLease({
        port, targetId: existing.id, leaseClass: "anchor", owner: "browserctl:anchor",
        origin: safeOrigin(existing.url), anchorKey: anchor.key, policy,
      });
      used.add(existing.id);
      kept.push({ key: anchor.key, targetId: existing.id, url: existing.url, source: "adopted" });
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

  return { port: Number(port), kept, created, reclassified, closed: [] };
}

export async function ensureBrowser(port, { policy = loadBrowserPolicy() } = {}) {
  const cdp = await cdpForPort(port, policy);
  const version = await cdp.ensureChrome();
  const status = launcherStatus(port, policy);
  const configuredMode = policyForPort(port, policy).mode;
  if (!status.managed) {
    throw new Error(`UNMANAGED_CDP_BROWSER: port ${port} is reachable but is not owned by browserctl`);
  }
  if (status.managed && status.mode && status.mode !== configuredMode) {
    throw new Error(`MODE_CHANGE_REQUIRES_RESTART: port ${port} is ${status.mode}; configured mode is ${configuredMode}`);
  }
  const anchors = await ensureAnchors(port, { policy, cdp });
  return { port: Number(port), browser: version.Browser, mode: status.mode, anchors };
}

async function probeActivity(cdp, page) {
  let session;
  try {
    session = await cdp.Session.open(page.webSocketDebuggerUrl);
    const initial = await cdp.readLeaseActivity(session);
    if (initial.ok) return { ...initial, measurementRestored: false };

    // A tracker installed through a short-lived CDP session survives in the
    // current document, but Chrome removes the new-document registration when
    // that session disconnects. Navigation can therefore leave a healthy tab
    // temporarily unmeasurable. Reinstall in the current document and treat
    // this moment as the start of a fresh, conservative inspection window.
    await cdp.installLeaseActivityTracker(session);
    const restored = await cdp.readLeaseActivity(session);
    if (!restored.ok) return restored;
    return { ...restored, measurementRestored: true };
  } catch (error) {
    return { ok: false, value: null, error: error.message };
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
  const configuredMode = policyForPort(port, policy).mode;
  if (!managedStatus.managed || managedStatus.mode !== configuredMode) {
    return {
      port: Number(port), reachable: Boolean(managedStatus.running), auditOnly, actions: [],
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
      const maintained = await ensureAnchors(port, { policy, cdp });
      anchorMaintenance = {
        kept: maintained.kept.length,
        created: maintained.created.length,
        reclassified: maintained.reclassified.length,
      };
    }
    pages = await cdp.listPages();
  } catch (error) {
    return { port: Number(port), reachable: false, auditOnly, actions: [], error: error.message };
  }
  const pageById = new Map(pages.map((page) => [page.id, page]));
  const actions = [];
  let leases = (await listLeases()).filter((lease) => lease.port === Number(port));

  for (let lease of leases) {
    const page = pageById.get(lease.targetId);
    if (!page) {
      await removeLease({ port, targetId: lease.targetId });
      actions.push({
        port: Number(port), action: "removed-stale-lease", targetId: lease.targetId,
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
    if (!activity.ok) {
      await recordActivityProbeFailure({ port, targetId: lease.targetId, now });
      actions.push({
        port: Number(port), action: "preserved", targetId: lease.targetId, class: lease.class,
        origin: safeOrigin(page.url), reason: "activity-unavailable", expiresAt: lease.expiresAt,
      });
      continue;
    }
    if (activity.measurementRestored) {
      lease = await restartActivityMeasurement({
        port, targetId: lease.targetId, now: Math.max(now, Number(activity.value)), policy,
      });
      actions.push({
        port: Number(port), action: "activity-tracker-restored", targetId: lease.targetId,
        class: lease.class, origin: safeOrigin(page.url), reason: "measurement-restarted",
        expiresAt: lease.expiresAt,
      });
      continue;
    }
    if (activity.value > Number(lease.lastActivityAt || 0)) {
      lease = await touchLease({ port, targetId: lease.targetId, kind: "activity", now: activity.value, policy });
    }
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
      port, targetId: lease.targetId, expectedUpdatedAt: lease.updatedAt, now,
    });
    if (!claim) {
      actions.push({ ...candidate, action: "preserved", reason: "lease-changed-before-close" });
      continue;
    }
    try {
      await cdp.closePageImmediately(lease.targetId, {
        explicit: true, reason: `expired ${lease.class} lease`,
      });
      await removeLease({ port, targetId: lease.targetId });
      actions.push(candidate);
    } catch (error) {
      await acquireLease({
        port, targetId: lease.targetId, leaseClass: "inspection", owner: "browserctl:close-failed",
        origin: safeOrigin(page.url), policy,
      });
      actions.push({ ...candidate, action: "preserved", reason: "close-failed" });
    }
  }
  return { port: Number(port), reachable: true, auditOnly, anchorMaintenance, actions };
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

async function main() {
  const { positional, options } = parseArgs(process.argv.slice(2));
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
    runLauncher(port, ["--mode", "stop"], policy, restartEnv);
    runLauncher(port, ["--mode", mode], policy, restartEnv);
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
  if (command === "cleanup") {
    const ports = options.port ? [portNumber(options.port)] : [9222, 9223];
    const results = [];
    for (const port of ports) results.push(await cleanupPort(port, { policy, auditOnly: options["audit-only"] === true || policy.cleanup.mode !== "active" }));
    console.log(JSON.stringify({ ok: true, mode: options["audit-only"] === true || policy.cleanup.mode !== "active" ? "audit" : "active", results }));
    return;
  }
  if (command === "auth") {
    const port = portNumber(required(options, "port"));
    const targetId = required(options, "target");
    console.log(JSON.stringify({ ok: true, ...(await authCommand(port, targetId, policy)) }));
    return;
  }
  throw new Error("USAGE: browserctl ensure|status|restart|lease|cleanup|auth");
}

if (process.argv[1] && realpathSync(resolve(process.argv[1])) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.log(JSON.stringify({ ok: false, error: error.message }));
    process.exitCode = 1;
  });
}
