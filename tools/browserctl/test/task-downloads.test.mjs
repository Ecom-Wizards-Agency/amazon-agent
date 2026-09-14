import assert from "node:assert/strict";
import test from "node:test";
import { withTaskDownloads } from "../task-downloads.mjs";

function task({ busy = false, loseAfterOperation = false, releaseFails = false } = {}) {
  const events = [];
  const handle = { port: 9222, taskId: "labels", slot: "primary", targetId: "target", controlToken: "token", contextScope: "sc:eu" };
  let checks = 0;
  handle.session = {
    async assertTaskControl() {
      events.push("assert");
      if (++checks === 3 && loseAfterOperation) throw this.invalidateTaskControl(new Error("expired"));
    },
    invalidateTaskControl(cause) {
      events.push("invalidate");
      return Object.assign(new Error(cause.message), { code: "TASK_TAB_CONTROL_LOST" });
    },
  };
  handle._registry = {
    async acquireTaskDownloads(spec) {
      events.push("acquire");
      assert.equal(spec.controlToken, handle.controlToken);
      assert.equal(spec.contextScope, "sc:eu");
      if (busy) throw Object.assign(new Error("other download"), { code: "TASK_TAB_DOWNLOAD_BUSY" });
      return { controlToken: handle.controlToken };
    },
    async releaseTaskDownloads() {
      events.push("release");
      if (releaseFails) throw new Error("claim replaced");
    },
  };
  return { handle, events };
}

test("download claim covers the whole operation and result verification", async () => {
  const { handle, events } = task();
  assert.equal(await withTaskDownloads(handle, async () => { events.push("download+verify"); return "verified"; }), "verified");
  assert.deepEqual(events, ["assert", "acquire", "assert", "download+verify", "assert", "release"]);
});

test("busy download routing never starts or retries the operation", async () => {
  const { handle, events } = task({ busy: true });
  await assert.rejects(withTaskDownloads(handle, async () => events.push("must not run")), { code: "TASK_TAB_DOWNLOAD_BUSY" });
  assert.deepEqual(events, ["assert", "acquire"]);
});

test("operation failure releases routing and does not reacquire the claim", async () => {
  const { handle, events } = task();
  await assert.rejects(withTaskDownloads(handle, async () => { throw new Error("PDF identity mismatch"); }), /PDF identity mismatch/);
  assert.deepEqual(events, ["assert", "acquire", "assert", "release"]);
});

test("lost ownership or replacement at release rejects the completed result", async () => {
  for (const options of [{ loseAfterOperation: true }, { releaseFails: true }]) {
    const { handle, events } = task(options);
    await assert.rejects(withTaskDownloads(handle, async () => "do not return"), { code: "TASK_TAB_CONTROL_LOST" });
    assert.ok(events.includes("invalidate"));
    assert.equal(events.filter((event) => event === "acquire").length, 1);
    assert.equal(events.filter((event) => event === "release").length, 1);
  }
});
