/** Hold browser-wide download routing for one bounded operation on an owned tab. */
export async function withTaskDownloads(handle, operation) {
  if (typeof operation !== "function") throw new TypeError("download operation must be a function");
  const session = handle?.session;
  if (!session || !handle._registry) {
    throw Object.assign(new Error("TASK_TAB_CONTROL_LOST: downloads require a managed task page"),
      { code: "TASK_TAB_CONTROL_LOST" });
  }
  const spec = {
    port: handle.port, taskId: handle.taskId, slot: handle.slot,
    controlToken: handle.controlToken, targetId: handle.targetId,
    contextScope: handle.contextScope, policy: handle._policy,
  };
  await session.assertTaskControl();
  let acquired = false;
  try {
    try {
      const claim = await handle._registry.acquireTaskDownloads(spec);
      if (!claim) throw new Error("download acquisition did not confirm ownership");
      acquired = true;
    } catch (error) {
      if (error.code === "TASK_TAB_DOWNLOAD_BUSY") throw error;
      throw session.invalidateTaskControl(error);
    }
    await session.assertTaskControl();
    const result = await operation();
    await session.assertTaskControl();
    return result;
  } finally {
    if (acquired) {
      try { await handle._registry.releaseTaskDownloads(spec); }
      catch (error) { throw session.invalidateTaskControl(error); }
    }
  }
}
