/*
 * End-to-end account-resolution runs against the fake CDP server: the real
 * CLI, the real gates. Covers the stale-snapshot regression (fresh regional
 * tab must be re-listed and its LIVE identity judged), the fail-closed
 * --expect-account mismatch, the chooser dead-end, and enforced --account.
 */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { startFakeCdp } from "./helpers/fake-cdp.mjs";

const RUN = fileURLToPath(new URL("../run.mjs", import.meta.url));
const OUT_DIR = mkdtempSync(join(tmpdir(), "report-fetcher-test-"));

function runCli(port, cliArgs) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [RUN, ...cliArgs], {
      env: {
        ...process.env,
        CDP_HOST: "127.0.0.1", CDP_PORT: String(port), CDP_AUTOSTART: "0",
        REPORT_FETCHER_SETTLE_MS: "100",
      },
    });
    let out = "";
    child.stdout.on("data", (c) => { out += c; });
    child.stderr.on("data", (c) => { out += c; });
    child.on("close", (code) => resolve({ code, out }));
  });
}

// Script a page target: identity for GetUserContext, live facts for the
// classify probe, plus canned replies for the runner's readiness/sign-in probes.
function pageBehavior({ facts, identity }) {
  return {
    results: {
      "Runtime.evaluate": (params) => {
        const expr = String(params.expression || "");
        if (expr.includes("GetUserContext")) return { result: { value: identity } };
        if (expr.includes("chooserButtonCount")) return { result: { value: facts } };
        if (expr.includes("input[type=password]")) {
          return { result: { value: JSON.stringify({ p: false, h: new URL(facts.url).host }) } };
        }
        if (expr.includes("readyState")) return { result: { value: true } };
        return { result: { value: null } };
      },
    },
  };
}

const BUSINESS_ARGS = ["business", "--start", "2026-06-01", "--end", "2026-06-30", "--out", join(OUT_DIR, "br.csv")];

test("fresh regional tab: gate judges the re-listed LIVE tab (stale-snapshot regression)", { concurrency: false }, async () => {
  const comFacts = { url: "https://sellercentral.amazon.com/home", title: "Seller Central", csrfMeta: true, chooserButtonCount: 0 };
  const comIdentity = { displayName: "Example Brand / United States", partnerAccountId: "A1US", merchantId: null, marketplace: null, err: null };
  const deFacts = { url: "https://sellercentral.amazon.de/home", title: "Seller Central", csrfMeta: true, chooserButtonCount: 0 };
  const deIdentity = { displayName: "Example Brand Deutschland", partnerAccountId: "A1DE", merchantId: null, marketplace: null, err: null };
  const fake = await startFakeCdp({
    targets: [{ id: "COM1", url: comFacts.url, behavior: pageBehavior({ facts: comFacts, identity: comIdentity }) }],
    onCreateTarget: (params) => ({ id: `NEW${Math.random().toString(36).slice(2, 8)}`, url: params.url, behavior: pageBehavior({ facts: deFacts, identity: deIdentity }) }),
  });
  try {
    const { code, out } = await runCli(fake.port, [...BUSINESS_ARGS, "--marketplace", "de", "--expect-account", "Example Brand Deutschland"]);
    // Pre-fix this died with "(unknown)": the fresh .de tab was filtered out of
    // the pre-resolution snapshot, so no identity was ever observed.
    assert.match(out, /Account check: OK/, out);
    assert.match(out, /Example Brand Deutschland/, out);
    assert.doesNotMatch(out, /does NOT match/, out);
    // The fetch itself fails on the fake (no report data); only the gate is under test.
    assert.notEqual(code, null);
  } finally {
    await fake.close();
  }
});

test("--expect-account mismatch dies fail-closed naming the observed account", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", title: "Seller Central", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "SomeOther Brand", partnerAccountId: "A1XX", merchantId: null, marketplace: null, err: null };
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: facts.url, behavior: pageBehavior({ facts, identity }) }],
  });
  try {
    const { code, out } = await runCli(fake.port, [...BUSINESS_ARGS, "--marketplace", "us", "--expect-account", "Example Brand"]);
    assert.equal(code, 1, out);
    assert.match(out, /does NOT match/);
    assert.match(out, /SomeOther Brand/);
    assert.match(out, /Nothing fetched/);
  } finally {
    await fake.close();
  }
});

test("account chooser without structured fields dies actionably, never session-default", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace", title: "Select account", csrfMeta: false, chooserButtonCount: 4 };
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: facts.url, behavior: pageBehavior({ facts, identity: null }) }],
  });
  try {
    const { code, out } = await runCli(fake.port, [...BUSINESS_ARGS, "--marketplace", "us"]);
    assert.equal(code, 1, out);
    assert.match(out, /account chooser/);
    assert.match(out, /NO account is selected/);
    assert.match(out, /Nothing fetched/);
  } finally {
    await fake.close();
  }
});

test("--account is enforced: unverifiable id without structured fields dies with remedies", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", title: "Seller Central", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand / United States", partnerAccountId: null, merchantId: null, marketplace: null, err: "GetUserContext not authorized (403) on this page" };
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: facts.url, behavior: pageBehavior({ facts, identity }) }],
  });
  try {
    const { code, out } = await runCli(fake.port, [...BUSINESS_ARGS, "--marketplace", "us", "--account", "amzn1.merchant.o.NOTONPAGE"]);
    assert.equal(code, 1, out);
    assert.match(out, /--account amzn1\.merchant\.o\.NOTONPAGE could not be verified/);
    assert.match(out, /account-name/);
    assert.match(out, /Nothing fetched/);
  } finally {
    await fake.close();
  }
});

test("--account verified via matching --expect-account name proceeds with the hint note", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", title: "Seller Central", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand / United States", partnerAccountId: null, merchantId: null, marketplace: null, err: "GetUserContext not authorized (403) on this page" };
  const fake = await startFakeCdp({
    targets: [{ id: "T1", url: facts.url, behavior: pageBehavior({ facts, identity }) }],
  });
  try {
    const { out } = await runCli(fake.port, [...BUSINESS_ARGS, "--marketplace", "us", "--account", "amzn1.merchant.o.SOMEID", "--expect-account", "Example Brand"]);
    assert.match(out, /verified via --expect-account "Example Brand"/, out);
    assert.match(out, /Account check: OK/, out);
  } finally {
    await fake.close();
  }
});
