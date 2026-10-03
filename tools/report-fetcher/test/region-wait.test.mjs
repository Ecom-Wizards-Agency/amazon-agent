/*
 * run.mjs on a port without a session lock takes turns on a busy Seller Central
 * region: the real CLI against the fake CDP server, with the holder's claim
 * seeded in a temporary lease registry the child shares.
 */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { startFakeCdp } from "./helpers/fake-cdp.mjs";

const ROOT = mkdtempSync(join(tmpdir(), "report-fetcher-region-wait-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = join(ROOT, "runtime");
process.env.AMAZON_BROWSER_POLICY = join(ROOT, "runtime", "policy.json");
process.env.AMAZON_BROWSER_LOCK_DIR = join(ROOT, "locks");
process.env.CDP_ENABLE_TEST_LEASES = "1";
delete process.env.WIZARDS_AI_MODE;
const registry = await import("../../browserctl/lease-registry.mjs");

const RUN = fileURLToPath(new URL("../run.mjs", import.meta.url));
const ARTIFACT_STUB = join(ROOT, "artifactctl-test.mjs");
writeFileSync(ARTIFACT_STUB, '#!/usr/bin/env node\nprocess.stdout.write(JSON.stringify({id:"test-artifact-run"}));\n', { mode: 0o700 });
// The launcher's managed-status probe, so the child never reads the HOME profile.
const LAUNCHER_STUB = join(ROOT, "launcher.mjs");
writeFileSync(LAUNCHER_STUB, 'process.stdout.write(JSON.stringify({managed:true,mode:"headless"}));\n');
const HOLDER_OWNER = "region-step.mjs:4242";
const ARGS = ["business", "--start", "2026-06-01", "--end", "2026-06-30", "--out", join(ROOT, "br.csv"), "--marketplace", "us"];

test.after(() => rmSync(ROOT, { recursive: true, force: true }));

function pageBehavior() {
  const facts = { url: "https://sellercentral.amazon.com/home", title: "Seller Central", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand / United States", partnerAccountId: "A1US", merchantId: null, marketplace: null, err: null };
  return { results: { "Runtime.evaluate": (params) => {
    const expr = String(params.expression || "");
    if (expr.includes("return await fetch")) return { result: { value: null } };
    if (expr.includes("GetUserContext")) return { result: { value: identity } };
    if (expr.includes("chooserButtonCount")) return { result: { value: facts } };
    if (expr.includes("input[type=password]")) return { result: { value: JSON.stringify({ p: false, h: "sellercentral.amazon.com" }) } };
    if (expr.includes("readyState")) return { result: { value: true } };
    return { result: { value: null } };
  } } };
}

/** Another attended session holds sc:na on this port. */
async function holdRegion(port, taskId) {
  const held = await registry.reserveTaskTab({ port, taskId, workflow: "amazon-catalog", owner: HOLDER_OWNER,
    exclusiveContext: true, sellerCentral: { marketplace: "us" } });
  assert.equal(held.kind, "create");
  return () => registry.abandonTaskTabReservation({ port, taskId, controlToken: held.controlToken });
}

function runCli(port, waitMs, onStderr = () => {}) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [RUN, ...ARGS], {
      timeout: 25000,
      env: {
        ...process.env, CDP_HOST: "127.0.0.1", CDP_PORT: String(port), CDP_AUTOSTART: "0",
        REPORT_FETCHER_SETTLE_MS: "100", AMAZON_ARTIFACTCTL: ARTIFACT_STUB,
        CDP_PYTHON: process.execPath, CDP_LAUNCHER: LAUNCHER_STUB,
        AMAZON_BROWSER_REGION_WAIT_MS: String(waitMs),
      },
    });
    let out = "", err = "";
    child.stdout.on("data", (chunk) => { out += chunk; });
    child.stderr.on("data", (chunk) => { err += chunk; onStderr(err); });
    child.on("close", (code) => resolve({ code, out, err }));
  });
}

test("run.mjs waits for a held region, says so once on stderr, and continues once it is free", { concurrency: false }, async () => {
  const fake = await startFakeCdp({ targets: [], onCreateTarget: (params) => ({ id: `OWNED${Math.random().toString(36).slice(2, 8)}`, url: params.url, behavior: pageBehavior() }) });
  try {
    const release = await holdRegion(fake.port, "holder-then-free");
    let released = false;
    const { out, err } = await runCli(fake.port, 20000, (stderr) => {
      if (!released && /waiting up to 20 s/.test(stderr)) { released = true; release(); }
    });
    assert.equal(released, true, err);
    const waitLines = err.split("\n").filter((line) => line.includes("waiting up to"));
    assert.equal(waitLines.length, 1, err);
    assert.match(waitLines[0], /^Seller Central sc:na is held by region-step\.mjs:4242 \(amazon-catalog\), heartbeat \d+ s ago; waiting up to 20 s for it$/);
    assert.doesNotMatch(out + err, /TASK_TAB_BUSY/);
    assert.match(out, /Account: Example Brand /, out + err);
    assert.ok(fake.sent.some((command) => command.method === "Target.createTarget"), "the task page was acquired after the wait");
  } finally {
    await fake.close();
  }
});

test("run.mjs fails with TASK_TAB_BUSY and the holder facts once the bound passes", { concurrency: false }, async () => {
  const fake = await startFakeCdp({ targets: [] });
  try {
    const release = await holdRegion(fake.port, "holder-bound");
    try {
      const started = Date.now();
      const { code, out, err } = await runCli(fake.port, 400);
      assert.equal(code, 1, out + err);
      assert.ok(Date.now() - started >= 400);
      assert.match(err, /ERROR: TASK_TAB_BUSY: browser-context-busy: sc:na on port \d+; Seller Central sc:na is held by region-step\.mjs:4242 \(amazon-catalog\), heartbeat \d+ s ago; waited \d+ s/);
      assert.equal(fake.sent.some((command) => command.method === "Target.createTarget"), false, "no page was created");
      const record = (await registry.listTaskTabs()).find((entry) => entry.taskId === "holder-bound");
      assert.equal(JSON.stringify(out + err).includes(record.controller.token), false, "the holder token is never printed");
    } finally { await release(); }
  } finally {
    await fake.close();
  }
});
