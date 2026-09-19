import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";
import { spawnSync } from "node:child_process";

const runtime = mkdtempSync(join(tmpdir(), "anchor-auth-"));
process.env.AMAZON_BROWSER_RUNTIME_DIR = runtime;
process.env.AMAZON_BROWSER_POLICY = join(runtime, "policy.json");
const { anchorAuthState, anchorMatchesUrl, loadBrowserPolicy } = await import("../policy.mjs");
const registry = await import("../lease-registry.mjs");
const { ensureAnchors, ensureBrowser, cleanupPort, cleanupSummary, main } = await import("../browserctl.mjs");
const policy = loadBrowserPolicy();
const anchors = policy.ports["9223"].anchors;
const path = join(runtime, "leases.json");
const noCreate = { createPage: async () => assert.fail("must not create a replacement") };
const seed = (anchor, targetId = anchor.key) => registry.acquireLease({
  port: 9223, targetId, leaseClass: "anchor", anchorKey: anchor.key,
  origin: new URL(anchor.url).origin, now: 1000, policy,
});
test.beforeEach(() => rmSync(path, { force: true }));
test.after(() => rmSync(runtime, { recursive: true, force: true }));

test("anchor states distinguish accepted paths, authentication and unrelated URLs", () => {
  for (const [url, expected] of [
    ["https://sellercentral.amazon.com/ap/signin", "auth"],
    ["https://sellercentral.amazon.com/ap/signin?clientContext=fixture", "auth"],
    ["https://sellercentral.amazon.com/performance/dashboard?ref_=xx_perf_auth", "off"],
    ["https://sellercentral.amazon.com/gp/ssof/knowledge/author/123", "off"],
    ["https://sellercentral.amazon.com/apps/authorize/consent", "off"],
    ["https://sellercentral.amazon.com/?returnTo=%2Fap%2Fsignin", "off"],
    ["https://sellercentral.amazon.com/signing", "off"],
    ["https://sellercentral.amazon.com/ap/signin-extra", "auth"],
    ["https://sellercentral.amazon.com/ap/signinfoo", "off"],
    ["https://sellercentral.amazon.com/AP/MFA", "auth"],
    ["https://www.amazon.com/?returnTo=%2Fap%2Fsignin", "auth"],
    ["https://sellercentral.amazon.com/ap/cvf?mfa=1", "auth"],
    ["https://www.amazon.com/ap/signin", "auth"],
    ["https://sellercentral.amazon.com/home", "ok"],
    ["https://sellercentral.amazon.com/account-switcher/default", "ok"],
    ["https://sellercentral.amazon.com/inventory", "off"],
    ["https://example.test/ap/signin", "off"],
    ["https://www.amazon.com/home", "off"], ["invalid", "off"],
  ]) {
    assert.equal(anchorAuthState(anchors[0], url), expected, url);
    assert.equal(anchorMatchesUrl(anchors[0], url), expected === "ok", url);
  }
});

test("signin anchors survive consecutive maintenance passes and clear auth state at home", async () => {
  for (const anchor of anchors) await seed(anchor);
  const pages = anchors.map(anchor => ({ id: anchor.key, url: new URL("/ap/signin", anchor.url).href }));
  const cdp = { ...noCreate, listPages: async () => pages };
  for (const now of [2000, 3000]) {
    const result = await ensureAnchors(9223, { policy, cdp, now });
    assert.deepEqual(result.created, []);
    assert.deepEqual(result.reclassified, []);
    assert.equal(result.kept.length, 3);
    assert.ok(result.kept.every(entry => entry.reason === "auth-required"));
    assert.equal(result.skipped.length, 3);
    assert.ok(result.skipped.every(entry => entry.retryAt === 302000));
    const leases = await registry.listLeases();
    assert.equal(leases.length, 3);
    assert.ok(leases.every(lease => lease.class === "anchor" && lease.authRequired));
  }
  pages.forEach((page, index) => { page.url = anchors[index].url; });
  await ensureAnchors(9223, { policy, cdp, now: 4000 });
  assert.ok((await registry.listLeases()).every(lease => lease.authRequired === false));
});

test("missing anchors respect origin cooldown across target IDs and resume after expiry", async () => {
  const one = structuredClone(policy);
  one.ports["9223"].anchors = [anchors[0]];
  await seed(anchors[0]);
  await ensureAnchors(9223, { policy: one, now: 2000,
    cdp: { ...noCreate, listPages: async () => [{ id: "US", url: "https://sellercentral.amazon.com/ap/signin" }] } });
  for (const now of [3000, 4000]) {
    const result = await ensureAnchors(9223, { policy: one, now, cdp: { ...noCreate, listPages: async () => [] } });
    assert.deepEqual(result.created, []);
    assert.deepEqual(result.skipped, [{ key: "US", reason: "auth-cooldown", retryAt: 302000 }]);
  }
  let created = 0;
  await ensureAnchors(9223, { policy: one, now: 302000, cdp: {
    listPages: async () => [], createPage: async () => {
      created++;
      return { targetId: "new", session: { close() {} } };
    },
  } });
  assert.equal(created, 1);
});

test("recent navigation and inspection leases suppress creation for their origin", async () => {
  const one = structuredClone(policy);
  one.ports["9223"].anchors = [anchors[0]];
  for (const leaseClass of ["interactive", "inspection"]) {
    await registry.acquireLease({ port: 9223, targetId: "prior", leaseClass,
      owner: leaseClass === "interactive" ? "browserctl:anchor-navigation" : "worker",
      origin: "https://sellercentral.amazon.com", now: 1000, policy });
    for (const now of [2000, 3000]) {
      const result = await ensureAnchors(9223, { policy: one, now,
        cdp: { ...noCreate, listPages: async () => [{ id: "prior", url: "https://sellercentral.amazon.com/ap/signin" }] } });
      assert.deepEqual(result.created, []);
      assert.deepEqual(result.skipped, [{ key: "US", reason: "inspection-cooldown", retryAt: 301000 }]);
    }
    await registry.removeLease({ port: 9223, targetId: "prior" });
  }
});

test("profile mismatch stops ensure and cleanup before CDP or registry mutation", async () => {
  await seed(anchors[0]);
  const before = readFileSync(path);
  const status = { running: true, managed: true, mode: policy.ports["9223"].mode, profile_verified: false };
  const cdp = { ensureChrome: async () => assert.fail("must not ensure Chrome"),
    assertChrome: async () => assert.fail("must not contact Chrome"), ...noCreate };
  const result = await cleanupPort(9223, { policy, managedStatus: status, cdp, auditOnly: false });
  assert.equal(result.error, `PROFILE_MISMATCH: port 9223 is served by a browser whose profile is not ${policy.ports["9223"].profile}`);
  assert.equal(result.anchorMaintenance, null);
  assert.equal(cleanupSummary([result], "active").status, "incomplete");
  assert.equal(cleanupSummary([result], "active").ok, false);
  const originalExitCode = process.exitCode;
  const originalLog = console.log;
  let summary;
  console.log = value => { summary = JSON.parse(value); };
  try {
    await main(["cleanup", "--port", "9223"], { cleanup: async () => result });
    assert.equal(summary.status, "incomplete");
    assert.equal(process.exitCode, 1);
  } finally {
    process.exitCode = originalExitCode;
    console.log = originalLog;
  }
  assert.deepEqual(result.actions, []);
  await assert.rejects(ensureBrowser(9223, { policy, cdp, getStatus: () => status }), /PROFILE_MISMATCH/);
  assert.deepEqual(readFileSync(path), before);
});

test("23 historical navigation leases and three signin anchors do not grow", async () => {
  const pages = [];
  for (let index = 0; index < 23; index++) {
    const anchor = anchors[index % 3];
    const targetId = `historical-${index}`;
    await registry.acquireLease({ port: 9223, targetId, leaseClass: "interactive",
      owner: "browserctl:anchor-navigation", origin: new URL(anchor.url).origin, now: 1, policy });
    pages.push({ id: targetId, url: new URL("/ap/signin", anchor.url).href });
  }
  for (const anchor of anchors) {
    await seed(anchor);
    pages.push({ id: anchor.key, url: new URL("/ap/signin", anchor.url).href });
  }
  const result = await ensureAnchors(9223, { policy, now: 1_000_000, cdp: { ...noCreate, listPages: async () => pages } });
  assert.equal(result.kept.length, 3);
  assert.deepEqual(result.created, []);
  assert.equal((await registry.listLeases()).length, 26);
});

test("audit previews auth retention without changing lease bytes; cleanup reports skipped", async () => {
  for (const anchor of anchors) await seed(anchor);
  const before = readFileSync(path);
  const pages = anchors.map(anchor => ({ id: anchor.key, url: new URL("/ap/signin", anchor.url).href }));
  const cdp = { ...noCreate, assertChrome: async () => ({}), listPages: async () => pages };
  const result = await cleanupPort(9223, { policy, cdp, now: 2000, auditOnly: true,
    managedStatus: { running: true, managed: true, profile_verified: true, mode: policy.ports["9223"].mode } });
  assert.equal(result.anchorMaintenance.skipped.length, 3);
  assert.ok(result.anchorMaintenance.skipped.every(entry => entry.retryAt === null));
  assert.equal(result.anchorMaintenance.created, 0);
  assert.deepEqual(readFileSync(path), before);
});


test("an expired regional controller cannot detach a signin anchor", async () => {
  const { sellerCentralRegionTask } = await import("../task-tabs.mjs");
  await seed(anchors[0]);
  await registry.reserveTaskTab({ ...sellerCentralRegionTask({ marketplace: "us" }),
    port: 9223, policy, livePageIds: ["US"], now: 1000 });
  const one = structuredClone(policy);
  one.ports["9223"].anchors = [anchors[0]];
  const result = await ensureAnchors(9223, { policy: one, now: 92000,
    cdp: { ...noCreate, listPages: async () => [{ id: "US", url: "https://sellercentral.amazon.com/ap/signin" }] } });
  assert.deepEqual(result.created, []);
  assert.deepEqual(result.reclassified, []);
  assert.equal(result.kept[0].reason, "auth-required");
  assert.equal((await registry.listLeases())[0].class, "anchor");
});

test("six-hour-old anchor starts cooldown at reclassification in active and audit passes", async () => {
  const one = structuredClone(policy);
  one.ports["9223"].anchors = [anchors[0]];
  const now = 1000 + 6 * 3600_000;
  await seed(anchors[0]);
  const before = readFileSync(path);
  const pages = [{ id: "US", url: "https://sellercentral.amazon.com/performance/dashboard?ref_=xx_perf_auth" }];
  const cdp = { ...noCreate, listPages: async () => pages };
  const preview = await ensureAnchors(9223, { policy: one, cdp, now, auditOnly: true });
  assert.equal(preview.actions.some(action => action.action === "would-create"), false);
  assert.equal(preview.actions[0].reclassifiedAt, now);
  assert.deepEqual(readFileSync(path), before);
  const active = await ensureAnchors(9223, { policy: one, cdp, now });
  assert.deepEqual(active.skipped, preview.skipped);
  const [lease] = await registry.listLeases();
  assert.equal(lease.acquiredAt, 1000);
  assert.equal(lease.reclassifiedAt, now);
  const next = await ensureAnchors(9223, { policy: one, cdp, now: now + 1 });
  assert.equal(next.skipped[0].reason, "inspection-cooldown");
  let created = 0;
  const expired = await ensureAnchors(9223, { policy: one, now: now + policy.cleanup.auth_retry_cooldown_ms,
    cdp: { listPages: async () => pages, createPage: async () => {
      created++;
      return { targetId: "replacement", session: { close() {} } };
    } } });
  assert.equal(created, 1);
  assert.equal(expired.created.length, 1);
});

test("ensure and cleanup consume the Python status contract with one probe and tri-state evidence", async () => {
  const fixture = spawnSync("python3", ["-B", new URL("./fixtures/launcher-profile.py", import.meta.url).pathname, "--json"], { encoding: "utf8" });
  assert.equal(fixture.status, 0, fixture.stderr);
  const statuses = JSON.parse(fixture.stdout);
  const one = structuredClone(policy);
  one.ports["9223"].mode = "headed";
  one.ports["9223"].anchors = [];
  const cdp = { ensureChrome: async () => ({ Browser: "fixture" }), assertChrome: async () => ({}), listPages: async () => [] };
  for (const original of [...statuses, { ...statuses[0], profile_verified: undefined },
    { ...statuses[0], running: false, managed: false, mode: null }]) {
    const status = { ...original, port: 9223 };
    let calls = 0;
    const warnings = [];
    const warn = console.warn;
    console.warn = message => warnings.push(message);
    try {
      const options = { policy: one, cdp, getStatus: () => { calls++; return status; } };
      if (status.profile_verified === false) {
        await assert.rejects(ensureBrowser(9223, options), /PROFILE_MISMATCH/);
      } else {
        const result = await ensureBrowser(9223, options);
        assert.equal(result.profileVerified, status.profile_verified ?? null);
        assert.equal(result.mode, "headed");
        assert.equal(warnings.length, status.profile_verified == null ? 1 : 0);
      }
      assert.equal(calls, 1);
      warnings.length = 0;
      const result = await cleanupPort(9223, { policy: one, cdp, managedStatus: status });
      assert.equal(result.profileVerified, status.profile_verified ?? null);
      assert.equal(warnings.length, status.profile_verified == null ? 1 : 0);
      if (status.profile_verified === false) assert.equal(cleanupSummary([result], "audit").status, "incomplete");
    } finally { console.warn = warn; }
  }
});
