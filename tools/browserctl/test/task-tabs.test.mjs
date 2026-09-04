import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

const runtime = mkdtempSync(join(tmpdir(), "task-tabs-test-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
process.env.CDP_PORT = "9222";
process.env.CDP_ENABLE_TEST_LEASES = "1";

const registry = await import(`../lease-registry.mjs?task-test=${Date.now()}`);
const taskTabs = await import(`../task-tabs.mjs?task-test=${Date.now()}`);
let fakeSequence = 0;

const policy = {
  schema_version: 1,
  cleanup: {
    mode: "audit", adopt_unregistered_tabs: false,
    background_grace_ms: 600_000, interactive_idle_ms: 7_200_000,
    heartbeat_interval_ms: 30_000, heartbeat_stale_ms: 90_000,
    auth_retry_cooldown_ms: 300_000,
  },
  ports: { "9222": { mode: "headed", profile: "/tmp/test", anchors: [] } },
};

function fakeCdp({ createDelayMs = 0 } = {}) {
  const sequence = ++fakeSequence;
  const pages = [];
  let created = 0;
  const sessionFor = (targetId) => ({
    targetId,
    async send(method, params = {}) {
      if (method === "Page.navigate") {
        const page = pages.find((entry) => entry.id === targetId);
        if (page) page.url = params.url;
      }
      return {};
    },
    close() {
      if (this._taskHeartbeat) clearInterval(this._taskHeartbeat);
    },
  });
  return {
    pages,
    get created() { return created; },
    ensureChrome: async () => ({}),
    listPages: async () => pages.map((entry) => ({ ...entry })),
    Session: {
      open: async (url) => sessionFor(url.split("/").pop()),
    },
    setDesktopViewport: async () => {},
    installLeaseActivityTracker: async () => {},
    createPage: async (url) => {
      if (createDelayMs) await new Promise((resolve) => setTimeout(resolve, createDelayMs));
      created += 1;
      const targetId = `fake-${sequence}-created-${created}`;
      pages.push({
        id: targetId, type: "page", url,
        webSocketDebuggerUrl: `ws://test/devtools/page/${targetId}`,
      });
      return { targetId, session: sessionFor(targetId) };
    },
  };
}

async function acquire(cdp, taskId, extra = {}) {
  return taskTabs.acquireTaskPage({
    port: 9222, taskId, slot: "primary", workflow: "test",
    initialUrl: "https://sellercentral.amazon.com/work",
    exclusiveContext: true, ...extra,
  }, { registry, cdp, policy });
}

test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("stable task ids are deterministic and do not expose long caller keys", () => {
  const key = "/private/client/path/report.csv?merchant=secret";
  const first = taskTabs.taskIdFor("Amazon Reporting", key);
  assert.equal(first, taskTabs.taskIdFor("Amazon Reporting", key));
  assert.match(first, /^amazon-reporting:[a-f0-9]{20}$/);
  assert.equal(first.includes("private"), false);
});

test("an error retry reuses one target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "retry-once");
  await taskTabs.releaseTaskPage(first, { outcome: "error" });
  const second = await acquire(cdp, "retry-once");
  assert.equal(second.targetId, first.targetId);
  assert.equal(second.reused, true);
  assert.equal(cdp.created, 1);
  await taskTabs.releaseTaskPage(second, { outcome: "success" });
});

test("concurrent acquisition creates one target and one controller", { concurrency: false }, async () => {
  const cdp = fakeCdp({ createDelayMs: 30 });
  const attempts = await Promise.allSettled([
    acquire(cdp, "concurrent"),
    acquire(cdp, "concurrent"),
  ]);
  assert.equal(attempts.filter((entry) => entry.status === "fulfilled").length, 1);
  assert.equal(attempts.filter((entry) =>
    entry.status === "rejected" && entry.reason.code === "TASK_TAB_BUSY").length, 1);
  assert.equal(cdp.created, 1);
  const page = attempts.find((entry) => entry.status === "fulfilled").value;
  await taskTabs.releaseTaskPage(page, { outcome: "success" });
});

test("browser-global Seller Central context is exclusive per port", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "context-first");
  await assert.rejects(
    acquire(cdp, "context-second"),
    (error) => error.code === "TASK_TAB_BUSY" && /browser-context-busy/.test(error.message),
  );
  await taskTabs.releaseTaskPage(first, { outcome: "success" });
  const second = await acquire(cdp, "context-second");
  await taskTabs.releaseTaskPage(second, { outcome: "success" });
});

test("a stale control token cannot release a reclaimed target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "stale-release");
  const staleToken = first.controlToken;
  await taskTabs.releaseTaskPage(first, { outcome: "error" });
  const second = await acquire(cdp, "stale-release");
  await assert.rejects(registry.releaseTaskTabControl({
    port: 9222, taskId: "stale-release", slot: "primary",
    controlToken: staleToken, outcome: "success", policy,
  }), /TASK_TAB_STALE_CONTROL/);
  const lease = (await registry.listLeases()).find((entry) => entry.targetId === second.targetId);
  assert.equal(lease.class, "background-active");
  await taskTabs.releaseTaskPage(second, { outcome: "success" });
});

test("legacy lease mutation cannot override a controlled task target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const page = await acquire(cdp, "legacy-release-guard");
  await assert.rejects(registry.releaseLease({
    port: 9222, targetId: page.targetId, outcome: "success", policy,
  }), /TASK_TAB_CONTROL_REQUIRED/);
  await assert.rejects(registry.acquireLease({
    port: 9222, targetId: page.targetId, leaseClass: "inspection",
    owner: "legacy", policy,
  }), /TASK_TAB_CONTROL_REQUIRED/);
  await taskTabs.releaseTaskPage(page, { outcome: "success" });
});

test("an explicit second slot is the only way to create a second task target", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const primary = await acquire(cdp, "two-slots");
  await taskTabs.releaseTaskPage(primary, { outcome: "handoff" });
  const evidence = await acquire(cdp, "two-slots", {
    slot: "evidence-step-1", exclusiveContext: false,
  });
  assert.notEqual(evidence.targetId, primary.targetId);
  assert.equal(cdp.created, 2);
  await taskTabs.releaseTaskPage(evidence, { outcome: "success" });
});

test("a missing bound target produces exactly one replacement", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const first = await acquire(cdp, "missing-target");
  await taskTabs.releaseTaskPage(first, { outcome: "error" });
  cdp.pages.splice(0, cdp.pages.length);
  const replacement = await acquire(cdp, "missing-target");
  assert.notEqual(replacement.targetId, first.targetId);
  assert.equal(cdp.created, 2);
  await taskTabs.releaseTaskPage(replacement, { outcome: "success" });
});

test("success keeps the task target for the configured grace period", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const page = await acquire(cdp, "success-grace");
  const before = Date.now();
  await taskTabs.releaseTaskPage(page, { outcome: "success" });
  const lease = (await registry.listLeases()).find((entry) => entry.targetId === page.targetId);
  assert.equal(lease.class, "background-success");
  assert.ok(lease.expiresAt >= before + policy.cleanup.background_grace_ms);
});

test("removing a closed target also removes its task binding", { concurrency: false }, async () => {
  const cdp = fakeCdp();
  const page = await acquire(cdp, "binding-cleanup");
  await taskTabs.releaseTaskPage(page, { outcome: "success" });
  await registry.removeLease({ port: 9222, targetId: page.targetId });
  assert.equal((await registry.listTaskTabs()).some((entry) =>
    entry.taskId === "binding-cleanup"), false);
});
