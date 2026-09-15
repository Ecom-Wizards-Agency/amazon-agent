import { createHash } from "node:crypto";
import { basename } from "node:path";
import * as cdpDefault from "../report-fetcher/cdp.mjs";
import * as registryDefault from "./lease-registry.mjs";
import { loadBrowserPolicy } from "./policy.mjs";
import { resolveContextScope, scopeForOrigin, assertContextCovers, isRegionalScope,
  REGION_WORKFLOW, REGION_ANCHOR_KEYS } from "./context-scopes.mjs";
import { acquireSessionLock } from "./session-lock.mjs";

const configuredPort = () => Number(process.env.CDP_PORT || 9223);
const markerUrl = (token) => `about:blank#ew-task-tab=${encodeURIComponent(token)}`;

export { REGION_WORKFLOW, REGION_ANCHOR_KEYS };

export function sellerCentralRegionTask({ marketplace, origin, claimScope } = {}) {
  if (claimScope !== undefined && claimScope !== "global") {
    throw taskError("TASK_TAB_CONTEXT_INVALID", "claimScope must be global when supplied");
  }
  const sellerCentral = { marketplace, origin };
  const scope = resolveContextScope({ exclusiveContext: true,
    sellerCentral: marketplace == null && origin == null ? undefined : sellerCentral });
  if (!isRegionalScope(scope)) {
    throw taskError("REGION_SCOPE_REQUIRED", "a mapped Seller Central region is required");
  }
  return {
    taskId: taskIdFor(REGION_WORKFLOW, scope), workflow: REGION_WORKFLOW,
    slot: "primary", exclusiveContext: true, sellerCentral, scope,
    anchorKey: REGION_ANCHOR_KEYS[scope], ...(claimScope === undefined ? {} : { claimScope }),
  };
}

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
  if (!page) return null;
  if (!page.webSocketDebuggerUrl) {
    throw taskError("TASK_TAB_TARGET_UNAVAILABLE", `retained target ${targetId} has no connection endpoint`);
  }
  const session = await cdp.Session.open(page.webSocketDebuggerUrl);
  return { page, session };
}

function startHeartbeats(handle, { registry, policy }) {
  const interval = policy.cleanup.heartbeat_interval_ms;
  let renewing = false;
  handle.session._taskHeartbeat = setInterval(async () => {
    if (renewing || handle._released) return;
    renewing = true;
    try {
      const renewed = await registry.touchTaskTabControl({
        port: handle.port, taskId: handle.taskId, slot: handle.slot,
        targetId: handle.targetId, controlToken: handle.controlToken, contextScope: handle.contextScope, policy,
      });
      if (!renewed) throw taskError("TASK_TAB_CONTROL_LOST", "task renewal did not confirm ownership");
    } catch (error) {
      handle.session.invalidateTaskControl(error);
    } finally { renewing = false; }
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
    return { targetId, session, source: recovered ? "recovered" : "created" };
  } catch (error) {
    session.close();
    await registry.abandonTaskTabReservation({
      port, taskId, slot, controlToken,
    }).catch(() => {});
    throw error;
  }
}

async function acquireTaskPageInner({
  port = configuredPort(), taskId, slot = "primary", workflow,
  initialUrl = "about:blank", exclusiveContext = false, sellerCentral, claimScope,
  allowOperatorActivity = false, owner = ownerName(), expectedTargetId = null,
} = {}, {
  registry = registryDefault, cdp = cdpDefault, policy = loadBrowserPolicy(),
} = {}) {
  assertPort(port);
  const regionScope = resolveContextScope({ exclusiveContext, sellerCentral });
  if (claimScope !== undefined && (claimScope !== "global" || !exclusiveContext)) {
    throw taskError("TASK_TAB_CONTEXT_INVALID", "claimScope requires global exclusive context");
  }
  const requestedScope = claimScope || regionScope;
  if (workflow === REGION_WORKFLOW && slot === "primary" && initialUrl === "about:blank") {
    initialUrl = policy.ports?.[String(port)]?.anchors
      ?.find((anchor) => anchor.key === REGION_ANCHOR_KEYS[regionScope])?.url || initialUrl;
  }
  if (requestedScope && initialUrl && scopeForOrigin(initialUrl)) {
    assertContextCovers(requestedScope, { origin: initialUrl });
  }
  await cdp.ensureChrome();
  let livePageIds = [];
  if (workflow === REGION_WORKFLOW && slot === "primary") {
    try { livePageIds = (await cdp.listPages()).map((page) => page.id); }
    catch (error) { throw taskError("TASK_TAB_TARGET_UNAVAILABLE", error.message); }
  }
  const spec = {
    port, taskId, slot, workflow, owner, exclusiveContext, sellerCentral, claimScope,
    allowOperatorActivity, origin: originOf(initialUrl), policy,
    livePageIds,
  };
  let reservation = await registry.reserveTaskTab(spec);
  let opened = null;
  try {
    for (let attempt = 0; reservation.kind === "probe" && attempt < 3; attempt++) {
      opened?.session.close();
      opened = null;
      let observation;
      try {
        opened = await openExistingPage(cdp, reservation.targetId);
        observation = opened ? await cdp.readLeaseInteraction(opened.session) : { missing: true };
        if (opened && observation.targetUrl === undefined) observation.targetUrl = opened.page.url;
        if (opened && observation.targetUrl) opened.page.url = observation.targetUrl;
      } catch (error) {
        // Only absence from a successful target listing permits replacement.
        // An explicit interaction override cannot turn a connection failure
        // into permission to create a duplicate page.
        if (!opened) throw taskError("TASK_TAB_TARGET_UNAVAILABLE", error.message);
        observation = { ok: false };
      }
      reservation = await registry.reserveTaskTab({
        ...spec, interactionProbe: { ...reservation.probeToken, ...observation },
      });
    }
  } catch (error) {
    opened?.session.close();
    throw error;
  }
  if (reservation.kind === "probe") {
    opened?.session.close();
    throw taskError("TASK_TAB_BUSY", "task binding changed during interaction check", { retryAt: null });
  }
  if (reservation.kind === "busy") {
    opened?.session.close();
    throw taskError(
      reservation.reason === "interaction-evidence-unavailable" ? "TASK_TAB_INTERACTION_UNKNOWN" : "TASK_TAB_BUSY",
      reservation.blockingScope
        ? `${reservation.reason}: ${reservation.blockingScope} on port ${port}`
        : reservation.reason || `${taskId}/${slot} is controlled by another process`,
      { retryAt: reservation.retryAt || null, blockingScope: reservation.blockingScope || null,
        blockingTask: reservation.blockingTask || null },
    );
  }

  const controlToken = reservation.controlToken;
  if (expectedTargetId && (reservation.kind !== "reuse" || reservation.targetId !== expectedTargetId || !opened)) {
    opened?.session.close();
    await registry.abandonTaskTabReservation({ port, taskId, slot, controlToken }).catch(() => {});
    throw taskError("EVIDENCE_TARGET_MISMATCH", "capture requires the existing exact task target");
  }
  const contextScope = reservation.taskTab?.contextScope ?? (exclusiveContext ? "global" : null);
  try {
    if (reservation.kind !== "reuse") {
      opened?.session.close();
      opened = null;
    }
    if (reservation.kind === "reuse") {
      // An existing probe connection has not navigated or changed the viewport.
      // A vanished target is replaced only after obtaining its task reservation.
      if (opened && opened.page.id !== reservation.targetId) {
        opened.session.close();
        opened = null;
      }
      if (!opened) opened = await openExistingPage(cdp, reservation.targetId);
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
  } catch (error) {
    opened?.session.close();
    await registry.abandonTaskTabReservation({ port, taskId, slot, controlToken }).catch(() => {});
    throw error;
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
    port: Number(port), taskId, slot, workflow, controlToken, contextScope, regionScope,
    targetId: page.targetId, session: page.session, source: page.source,
    reused: page.source === "reused", contextVerificationRequired: true,
    _registry: registry, _policy: policy, _released: false,
  };
  try {
    // createPage has a legacy heartbeat until the target is bound. From this
    // point onward only the token-checked atomic task renewal owns liveness.
    if (handle.session._leaseHeartbeat) clearInterval(handle.session._leaseHeartbeat);
    handle.session.setTaskControlGuard(({ exclusiveContext: requireExclusive } = {}) =>
      registry.assertTaskTabControl({ port, taskId, slot, controlToken, contextScope,
        targetId: handle.targetId, exclusiveContext: requireExclusive }), {
          exclusiveContext, contextScope,
          initialUrl: opened?.page.url || markerUrl(reservation.reservationToken || "bound"),
        });
    startHeartbeats(handle, { registry, policy });
    await cdp.setDesktopViewport(handle.session);
    await cdp.installLeaseActivityTracker(handle.session);
    if (!handle.reused && initialUrl) {
      await handle.session.send("Page.navigate", { url: initialUrl }, { timeoutMs: 15000 });
    }
    await handle.session.assertTaskControl();
    return handle;
  } catch (error) {
    let keepAnchor = false;
    if (workflow === REGION_WORKFLOW && slot === "primary") {
      try {
        const livePage = (await cdp.listPages()).find((entry) => entry.id === handle.targetId);
        keepAnchor = Boolean(livePage && scopeForOrigin(livePage.url) === regionScope);
      } catch { /* A failed target probe cannot establish safe reuse. */ }
    }
    // Setup has not handed control to the workflow. Preserve a live region
    // target on its origin so transient setup failures do not multiply tabs.
    await (keepAnchor
      ? finishTaskPage(handle, "abandonTaskTabReservation")
      : releaseTaskPage(handle, { outcome: "error" })).catch(() => {});
    throw error;
  }
}

export async function acquireTaskPage(spec = {}, dependencies = {}) {
  const unlock = dependencies.cdp && dependencies.cdp !== cdpDefault ? () => {}
    : acquireSessionLock(spec.port ?? configuredPort(), spec.taskId);
  try {
    const handle = await acquireTaskPageInner(spec, dependencies);
    handle._unlockSession = unlock;
    return handle;
  } catch (error) { unlock(); throw error; }
}

/**
 * Release successfully by default. Pass "handoff" deliberately for an explicit operator handover.
 * A failed regional home navigation detaches the target and may throw REGION_PARK_FAILED.
 */
export async function releaseTaskPage(handle, { outcome = "success" } = {}) {
  if (!handle || handle._released) return null;
  if (handle.workflow === REGION_WORKFLOW && handle.slot === "primary") {
    if (!["success", "handoff"].includes(outcome)) return detachTaskPage(handle, { outcome });
    if (outcome === "success") {
      try {
        const anchorKey = REGION_ANCHOR_KEYS[handle.regionScope ?? handle.contextScope];
        const anchor = handle._policy.ports?.[String(handle.port)]?.anchors?.find((entry) => entry.key === anchorKey);
        if (!anchor) throw taskError("REGION_ANCHOR_REQUIRED", `policy has no ${anchorKey} anchor`);
        const navigation = await handle.session.send("Page.navigate", { url: anchor.url }, { timeoutMs: 15000 });
        if (navigation.errorText) throw new Error(`REGION_PARK_FAILED: ${navigation.errorText}`);
      } catch (error) {
        await detachTaskPage(handle, { outcome: "error" });
        throw error;
      }
    }
  }
  return finishTaskPage(handle, "releaseTaskTabControl", outcome);
}

export async function detachTaskPage(handle, { outcome = "inspection" } = {}) {
  return finishTaskPage(handle, "detachTaskTab", outcome);
}

async function finishTaskPage(handle, method, outcome) {
  if (!handle || handle._released) return null;
  handle._released = true;
  if (handle.session?._taskHeartbeat) clearInterval(handle.session._taskHeartbeat);
  handle.session?.close();
  try { return await handle._registry[method]({
    port: handle.port, taskId: handle.taskId, slot: handle.slot,
    controlToken: handle.controlToken, contextScope: handle.contextScope, outcome, policy: handle._policy,
  }); } finally { handle._unlockSession?.(); }
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
