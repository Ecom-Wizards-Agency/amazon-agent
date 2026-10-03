// Non-secret facts about the controller that holds a busy Seller Central context.
// No imports: seller-assistant.mjs shares these without loading a browser module.

/** The busy answer for a Seller Central context another controller holds:
 * reserveTaskTab returns browser-context-busy with the blocking scope, which
 * acquireTaskPage throws as TASK_TAB_BUSY. Other busy answers (the same task in
 * another process, input on the task's own tab) carry no blocking scope. */
export function regionBusy(error) {
  return error?.code === "TASK_TAB_BUSY" && typeof error.blockingScope === "string" && error.blockingScope !== "";
}

/** Facts from the task record the registry lists for the blocking claim. The
 * control token is never copied. */
export async function regionHolder(registry, error, now = Date.now()) {
  const facts = { blocking_scope: error.blockingScope, owner: null, workflow: null, task_id: null, heartbeat_age_s: null };
  let record = null;
  if (error.blockingTask) {
    try { record = (await registry.listTaskTabs()).find((entry) => entry.key === error.blockingTask) || null; } catch { /* facts stay unknown */ }
  }
  if (!record) return facts;
  const heartbeatAt = Number(record.controller?.heartbeatAt);
  return { ...facts, owner: record.controller?.owner ?? null, workflow: record.workflow ?? null, task_id: record.taskId ?? null,
    heartbeat_age_s: Number.isFinite(heartbeatAt) ? Math.max(0, Math.round((now - heartbeatAt) / 1000)) : null };
}

/** "Seller Central sc:na is held by step.mjs:4242 (seller-central-region)". */
export function describeRegionHolder(facts) {
  return `Seller Central ${facts.blocking_scope} is held by ${facts.owner || "another controller"}${facts.workflow ? ` (${facts.workflow})` : ""}`;
}
