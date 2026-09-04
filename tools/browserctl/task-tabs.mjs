import { createHash } from "node:crypto";
import { basename } from "node:path";
import * as cdpDefault from "../report-fetcher/cdp.mjs";
import * as registryDefault from "./lease-registry.mjs";
import { loadBrowserPolicy } from "./policy.mjs";

const configuredPort = () => Number(process.env.CDP_PORT || 9222);
const markerUrl = (token) => `about:blank#ew-task-tab=${encodeURIComponent(token)}`;

export function taskIdFor(workflow, stableKey) {
  const label = String(workflow || "task").toLowerCase()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 60) || "task";
  const digest = createHash("sha256").update(String(stableKey)).digest("hex").slice(0, 20);
  return `${label}:${digest}`;
}

function ownerName() {
  return `${basename(process.argv[1] || "node")}:${process.pid}`;
}

function originOf(value) {
  if (!value) return null;
  try { return new URL(value).origin; } catch { return null; }
}

function taskError(code, message, details = {}) {
  const error = new Error(`${code}: ${message}`);
  error.code = code;
  Object.assign(error, details);
  return error;
}

function assertPort(port) {
  const actual = configuredPort();
  if (Number(port) !== actual) {
    throw taskError(
      "TASK_TAB_PORT_MISMATCH",
      `requested port ${port}, but the loaded CDP module is configured for ${actual}`,
    );
  }
}

async function openExistingPage(cdp, targetId) {
  const page = (await cdp.listPages()).find((entry) => entry.id === targetId);
  if (!page?.webSocketDebuggerUrl) return null;
  const session = await cdp.Session.open(page.webSocketDebuggerUrl);
  await cdp.setDesktopViewport(session);
  await cdp.installLeaseActivityTracker(session).catch(() => {});
  return { page, session };
}

function startHeartbeats(handle, { registry, policy }) {
  const interval = policy.cleanup.heartbeat_interval_ms;
  handle.session._taskHeartbeat = setInterval(() => {
    Promise.all([
      registry.touchLease({
        port: handle.port, targetId: handle.targetId, kind: "heartbeat", policy,
      }),
      registry.touchTaskTabControl({
        port: handle.port, taskId: handle.taskId, slot: handle.slot,
        controlToken: handle.controlToken, policy,
      }),
    ]).catch(() => {});
  }, interval);
  handle.session._taskHeartbeat.unref?.();
}

async function createOrRecoverReservedPage({
  reservationToken, controlToken, port, taskId, slot, owner, initialUrl,
  registry, cdp, policy,
}) {
  const marker = markerUrl(reservationToken);
  let matches = (await cdp.listPages()).filter((entry) => entry.url === marker);
  if (matches.length > 1) {
    await registry.abandonTaskTabReservation({ port, taskId, slot, controlToken });
    throw taskError(
      "TASK_TAB_RESERVATION_CONFLICT",
      `multiple targets exist for ${taskId}/${slot}; preserving all of them`,
    );
  }

  let targetId;
  let session;
  let recovered = false;
  if (matches.length === 1) {
    recovered = true;
    targetId = matches[0].id;
    session = (await openExistingPage(cdp, targetId))?.session || null;
    if (!session) {
      await registry.abandonTaskTabReservation({ port, taskId, slot, controlToken });
      throw taskError("TASK_TAB_TARGET_UNAVAILABLE", `reserved target ${targetId} is unavailable`);
    }
  } else {
    const created = await cdp.createPage(marker, {
      owner,
      freshPageReason: `reserved task tab ${taskId}/${slot}`,
    });
    targetId = created.targetId;
    session = created.session;
  }

  try {
    await registry.bindReservedTaskTab({
      port, taskId, slot, targetId, reservationToken, controlToken,
      owner, origin: originOf(initialUrl), policy,
    });
    if (initialUrl) {
      await session.send("Page.navigate", { url: initialUrl }, { timeoutMs: 15000 });
    }
    return { targetId, session, source: recovered ? "recovered" : "created" };
  } catch (error) {
    session.close();
    await registry.abandonTaskTabReservation({
      port, taskId, slot, controlToken,
    }).catch(() => {});
    throw error;
  }
}

export async function acquireTaskPage({
  port = configuredPort(), taskId, slot = "primary", workflow,
  initialUrl = "about:blank", exclusiveContext = false,
  allowOperatorActivity = false, owner = ownerName(),
} = {}, {
  registry = registryDefault, cdp = cdpDefault, policy = loadBrowserPolicy(),
} = {}) {
  assertPort(port);
  await cdp.ensureChrome();
  let reservation = await registry.reserveTaskTab({
    port, taskId, slot, workflow, owner, exclusiveContext,
    allowOperatorActivity, origin: originOf(initialUrl), policy,
  });
  if (reservation.kind === "busy") {
    throw taskError(
      "TASK_TAB_BUSY",
      reservation.reason || `${taskId}/${slot} is controlled by another process`,
      { retryAt: reservation.retryAt || null },
    );
  }

  const controlToken = reservation.controlToken;
  let opened;
  if (reservation.kind === "reuse") {
    opened = await openExistingPage(cdp, reservation.targetId);
    if (!opened) {
      const replacement = await registry.prepareMissingTaskTabReplacement({
        port, taskId, slot, targetId: reservation.targetId, controlToken, policy,
      });
      reservation = {
        kind: "create", controlToken,
        reservationToken: replacement.reservationToken,
      };
    }
  }

  let page;
  try {
    page = reservation.kind === "reuse"
      ? { targetId: reservation.targetId, session: opened.session, source: "reused" }
      : await createOrRecoverReservedPage({
        reservationToken: reservation.reservationToken, controlToken,
        port, taskId, slot, owner, initialUrl, registry, cdp, policy,
      });
  } catch (error) {
    await registry.abandonTaskTabReservation({
      port, taskId, slot, controlToken,
    }).catch(() => {});
    throw error;
  }

  const handle = {
    port: Number(port), taskId, slot, workflow, controlToken,
    targetId: page.targetId, session: page.session, source: page.source,
    reused: page.source === "reused", contextVerificationRequired: true,
    _registry: registry, _policy: policy, _released: false,
  };
  startHeartbeats(handle, { registry, policy });
  return handle;
}

export async function releaseTaskPage(handle, { outcome = "handoff" } = {}) {
  if (!handle || handle._released) return null;
  handle._released = true;
  if (handle.session?._taskHeartbeat) clearInterval(handle.session._taskHeartbeat);
  handle.session?.close();
  return handle._registry.releaseTaskTabControl({
    port: handle.port, taskId: handle.taskId, slot: handle.slot,
    controlToken: handle.controlToken, outcome, policy: handle._policy,
  });
}

export async function completeBrowserTask({
  port = configuredPort(), taskId, outcome = "success",
} = {}, { registry = registryDefault, policy = loadBrowserPolicy() } = {}) {
  assertPort(port);
  return registry.completeTaskTabs({ port, taskId, outcome, policy });
}

export async function withTaskPage(spec, work, {
  successOutcome = "success", registry = registryDefault,
  cdp = cdpDefault, policy = loadBrowserPolicy(),
} = {}) {
  const page = await acquireTaskPage(spec, { registry, cdp, policy });
  try {
    const result = await work(page);
    await releaseTaskPage(page, { outcome: successOutcome });
    return result;
  } catch (error) {
    await releaseTaskPage(page, { outcome: "error" }).catch(() => {});
    throw error;
  }
}
