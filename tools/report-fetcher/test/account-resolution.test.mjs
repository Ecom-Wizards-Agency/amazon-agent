/*
 * End-to-end account-resolution runs against the fake CDP server: the real
 * CLI, the real gates. Covers the stale-snapshot regression (fresh regional
 * tab must be re-listed and its LIVE identity judged), the fail-closed
 * --expect-account mismatch, the chooser dead-end, and enforced --account.
 */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync, rmSync, readFileSync, existsSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { startFakeCdp as startCdp } from "./helpers/fake-cdp.mjs";

// Each task owns a new page in the same simulated browser session. Its
// identity reflects session state; source/anchor targets must never be driven.
async function startFakeCdp(options) {
  const current = options.targets.find((target) => target.id === "NEWEST") || options.targets[0];
  return startCdp({
    ...options,
    onCreateTarget: options.onCreateTarget || ((params) => ({
      id: `OWNED${Math.random().toString(36).slice(2)}`, url: params.url, behavior: current.behavior,
    })),
  });
}

const RUN = fileURLToPath(new URL("../run.mjs", import.meta.url));
const OUT_DIR = mkdtempSync(join(tmpdir(), "report-fetcher-test-"));
const BROWSER_RUNTIME = mkdtempSync(join(tmpdir(), "report-fetcher-browser-test-"));
const runtimes = new Map();
const ARTIFACT_STUB = join(OUT_DIR, "artifactctl-test.mjs");
writeFileSync(ARTIFACT_STUB, '#!/usr/bin/env node\nprocess.stdout.write(JSON.stringify({id:"test-artifact-run"}));\n', { mode: 0o700 });

test.after(() => {
  rmSync(OUT_DIR, { recursive: true, force: true });
  rmSync(BROWSER_RUNTIME, { recursive: true, force: true });
});

function runCli(port, cliArgs) {
  const runtime = mkdtempSync(join(BROWSER_RUNTIME, "run-"));
  runtimes.set(port, runtime);
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [RUN, ...cliArgs], {
      timeout: 25000,
      env: {
        ...process.env,
        CDP_HOST: "127.0.0.1", CDP_PORT: String(port), CDP_AUTOSTART: "0",
        CDP_ENABLE_TEST_LEASES: "1", AMAZON_BROWSER_RUNTIME_DIR: runtime,
        REPORT_FETCHER_SETTLE_MS: "100", AMAZON_ARTIFACTCTL: ARTIFACT_STUB,
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
function pageBehavior({ facts, identity, fetchResult = null, onFetch = null, onNavigate = null }) {
  return {
    results: {
      "Page.navigate": (params) => { onNavigate?.(params.url); return {}; },
      "Runtime.evaluate": (params) => {
        const expr = String(params.expression || "");
        if (expr.includes("return await fetch")) {
          onFetch?.();
          return { result: { value: fetchResult } };
        }
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
    assert.ok(fake.sent.every((command) => !["T1", "NEWEST", "STALE"].includes(command.targetId)), "existing targets are never attached or driven");
    const registry = JSON.parse(readFileSync(join(runtimes.get(fake.port), "leases.json"), "utf8"));
    assert.equal(registry.context_claims[String(fake.port)], undefined, "failure releases context claim");
    const task = Object.values(registry.task_tabs).find((entry) => entry.port === fake.port);
    assert.equal(task.controller, null);
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
    assert.ok(fake.sent.every((command) => !["T1", "NEWEST", "STALE"].includes(command.targetId)), "existing targets are never attached or driven");
    const registry = JSON.parse(readFileSync(join(runtimes.get(fake.port), "leases.json"), "utf8"));
    assert.equal(registry.context_claims[String(fake.port)], undefined, "failure releases context claim");
    const task = Object.values(registry.task_tabs).find((entry) => entry.port === fake.port);
    assert.equal(task.controller, null);
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
    assert.ok(fake.sent.every((command) => !["T1", "NEWEST", "STALE"].includes(command.targetId)), "existing targets are never attached or driven");
    const registry = JSON.parse(readFileSync(join(runtimes.get(fake.port), "leases.json"), "utf8"));
    assert.equal(registry.context_claims[String(fake.port)], undefined, "failure releases context claim");
    const task = Object.values(registry.task_tabs).find((entry) => entry.port === fake.port);
    assert.equal(task.controller, null);
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

test("a stale pinned tab from the previous seller does not override the newest requested-account tab", { concurrency: false }, async () => {
  const requestedFacts = { url: "https://sellercentral.amazon.com/myinventory/inventory", title: "Manage Inventory", csrfMeta: true, chooserButtonCount: 0 };
  const requestedIdentity = { displayName: "Evora Body", partnerAccountId: null, merchantId: "EVORA", marketplace: null, err: null };
  const staleFacts = { url: "https://sellercentral.amazon.com/business-reports?mons_sel_dir_mcid=ALPHA", title: "Business Reports", csrfMeta: true, chooserButtonCount: 0 };
  const staleIdentity = { displayName: "AlphaInfuse", partnerAccountId: null, merchantId: "ALPHA", marketplace: null, err: null };
  const fake = await startFakeCdp({
    targets: [
      { id: "NEWEST", url: requestedFacts.url, behavior: pageBehavior({ facts: requestedFacts, identity: requestedIdentity }) },
      { id: "STALE", url: staleFacts.url, behavior: pageBehavior({ facts: staleFacts, identity: staleIdentity }) },
    ],
  });
  try {
    const { out } = await runCli(fake.port, [
      ...BUSINESS_ARGS, "--marketplace", "us", "--account", "EVORA", "--expect-account", "Evora Body",
    ]);
    assert.match(out, /Account: Evora Body/, out);
    assert.match(out, /Account check: OK/, out);
    assert.doesNotMatch(out, /AlphaInfuse/, out);
  } finally {
    await fake.close();
  }
});

test("name-based switching does not inherit another seller's stale pinned tab", { concurrency: false }, async () => {
  const auFacts = { url: "https://sellercentral.amazon.com.au/myinventory/inventory", title: "Manage Inventory AU", csrfMeta: true, chooserButtonCount: 0 };
  const auIdentity = { displayName: "Svens Island Australia", partnerAccountId: null, merchantId: "AU", marketplace: null, err: null };
  const unknownFacts = { url: "https://sellercentral.amazon.com/business-reports", title: "Business Reports", csrfMeta: false, chooserButtonCount: 0 };
  const requestedFacts = { url: "https://sellercentral.amazon.com/myinventory/inventory", title: "Manage Inventory", csrfMeta: true, chooserButtonCount: 0 };
  const requestedIdentity = { displayName: "Simply Nootropics", partnerAccountId: "DELEGATED", merchantId: null, marketplace: null, err: null };
  const staleFacts = { url: "https://sellercentral.amazon.com/business-reports?mons_sel_dir_mcid=ALPHA", title: "Business Reports", csrfMeta: true, chooserButtonCount: 0 };
  const staleIdentity = { displayName: "AlphaInfuse", partnerAccountId: null, merchantId: "ALPHA", marketplace: null, err: null };
  const fake = await startFakeCdp({
    targets: [
      { id: "CROSSORIGIN", url: auFacts.url, behavior: pageBehavior({ facts: auFacts, identity: auIdentity }) },
      { id: "UNKNOWN", url: unknownFacts.url, behavior: pageBehavior({ facts: unknownFacts, identity: null }) },
      { id: "NEWEST", url: requestedFacts.url, behavior: pageBehavior({ facts: requestedFacts, identity: requestedIdentity }) },
      { id: "STALE", url: staleFacts.url, behavior: pageBehavior({ facts: staleFacts, identity: staleIdentity }) },
    ],
  });
  try {
    const { out } = await runCli(fake.port, [
      ...BUSINESS_ARGS, "--marketplace", "us", "--expect-account", "Simply Nootropics",
      "--account-name", "Simply Nootropics", "--marketplace-label", "United States",
    ]);
    assert.match(out, /Account check: OK/, out);
    assert.match(out, /Simply Nootropics/, out);
    assert.doesNotMatch(out, /does NOT match/, out);
  } finally {
    await fake.close();
  }
});


test("a full report batch holds one task target and releases its claim", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand", merchantId: "MERCHANT", partnerAccountId: "PARTNER", marketplace: "US" };
  const configPath = join(OUT_DIR, "batch.json");
  const firstOut = join(OUT_DIR, "scp.csv");
  const secondOut = join(OUT_DIR, "tst.csv");
  writeFileSync(configPath, JSON.stringify({
    scp: { period_end_dates: ["2026-06-27"], out: firstOut },
    tst: { period_end_dates: ["2026-06-27"], out: secondOut },
  }));
  let fetches = 0;
  const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
    behavior: pageBehavior({ facts, identity, fetchResult: { report: "file", text: "sku\nEXAMPLE\n" }, onFetch() {
      fetches++;
      const registry = JSON.parse(readFileSync(join(runtimes.get(fake.port), "leases.json"), "utf8"));
      assert.ok(registry.regional_context_claims[`${fake.port}:sc:na`], "regional context held during every fetch");
      assert.equal(Object.values(registry.task_tabs)[0].contextScope, "sc:na");
    } }),
  }] });
  try {
    const result = await runCli(fake.port, ["all", "--config", configPath, "--expect-account", "Example Brand"]);
    assert.equal(result.code, 0, result.out);
    assert.equal(fetches, 2);
    assert.ok(existsSync(firstOut) && existsSync(secondOut));
    assert.equal(fake.sent.filter((command) => command.method === "Target.createTarget").length, 1);
    assert.ok(fake.sent.every((command) => command.targetId !== "ANCHOR"));
    const registry = JSON.parse(readFileSync(join(runtimes.get(fake.port), "leases.json"), "utf8"));
    assert.equal(registry.context_claims[String(fake.port)], undefined);
  } finally { await fake.close(); }
});

for (const [report, reportPath] of [["business", "/business-reports"], ["inventory", "/listing/reports"]]) {
  test(`${report}: meta-less shell with null identity passes both fetch guards`, { concurrency: false }, async () => {
    const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
    const identity = { displayName: "Example Brand", merchantId: "MERCHANT", partnerAccountId: "PARTNER", marketplace: "US", err: null };
    const out = join(OUT_DIR, `meta-less-${report}.txt`);
    let fetches = 0;
    const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
      behavior: pageBehavior({ facts, identity, fetchResult: { report: "file", text: "sku\nVERIFIED\n" },
        onNavigate(url) {
          facts.url = url;
          if (new URL(url).pathname.startsWith(reportPath)) {
            Object.assign(facts, { csrfMeta: false, scShell: true });
            Object.assign(identity, { displayName: null, merchantId: null, partnerAccountId: null,
              marketplace: null, err: "no anti-csrftoken-a2z meta tag" });
          }
        },
        onFetch() { fetches++; },
      }),
    }] });
    try {
      const args = report === "business" ? BUSINESS_ARGS : ["inventory"];
      const result = await runCli(fake.port, [...args, "--out", out, "--account", "MERCHANT", "--expect-account", "Example Brand"]);
      assert.equal(result.code, 0, result.out);
      assert.equal(fetches, 1);
      assert.equal(readFileSync(out, "utf8"), "sku\nVERIFIED\n");
      assert.equal(identity.marketplace, null, "report navigation must reach the meta-less fixture");
      assert.equal(fake.sent.filter(command => command.method === "Target.createTarget").length, 1);
    } finally { await fake.close(); }
  });
}

for (const changedField of ["merchantId", "marketplace"]) {
  test(`post-fetch ${changedField} drift discards the report before emit`, { concurrency: false }, async () => {
    const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
    const identity = { displayName: "Example Brand", merchantId: "MERCHANT", partnerAccountId: "PARTNER", marketplace: "US" };
    const out = join(OUT_DIR, `drift-${changedField}.txt`);
    const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
      behavior: pageBehavior({ facts, identity, fetchResult: { report: "file", text: "sku\nWRONG\n" },
        onFetch() { identity[changedField] = "CHANGED"; } }),
    }] });
    try {
      const result = await runCli(fake.port, ["inventory", "--out", out, "--expect-account", "Example Brand", "--verbose"]);
      assert.equal(result.code, 1, result.out);
      assert.match(result.out, /changed or became unverifiable/);
      assert.equal(existsSync(out), false);
      assert.equal(existsSync(`${out}.raw.json`), false);
    } finally { await fake.close(); }
  });
}

test("unresolved identity without explicit account flags fails closed", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
  const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
    behavior: pageBehavior({ facts, identity: {} }),
  }] });
  try {
    const result = await runCli(fake.port, BUSINESS_ARGS);
    assert.equal(result.code, 1, result.out);
    assert.match(result.out, /UNRESOLVED/);
    assert.ok(!fake.sent.some((command) => command.params?.expression?.includes("return await fetch")));
  } finally { await fake.close(); }
});


test("account drift after report navigation blocks the fetch itself", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand", merchantId: "ORIGINAL" };
  let fetched = false;
  const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
    behavior: pageBehavior({ facts, identity,
      onNavigate(url) { if (url.includes("business-reports")) identity.merchantId = "DIFFERENT"; },
      onFetch() { fetched = true; },
    }),
  }] });
  try {
    const result = await runCli(fake.port, BUSINESS_ARGS);
    assert.equal(result.code, 1, result.out);
    assert.match(result.out, /account changed or became unverifiable/);
    assert.equal(fetched, false);
  } finally { await fake.close(); }
});

test("a claim lost during a fetch prevents accepting its result", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand", merchantId: "ORIGINAL" };
  const out = join(OUT_DIR, "claim-lost.txt");
  const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
    behavior: pageBehavior({ facts, identity, fetchResult: { report: "file", text: "sku\nUNVERIFIED\n" },
      onFetch() {
        const path = join(runtimes.get(fake.port), "leases.json");
        const registry = JSON.parse(readFileSync(path, "utf8"));
        delete registry.regional_context_claims[`${fake.port}:sc:na`];
        writeFileSync(path, JSON.stringify(registry));
      },
    }),
  }] });
  try {
    const result = await runCli(fake.port, ["inventory", "--out", out]);
    assert.equal(result.code, 1, result.out);
    assert.match(result.out, /TASK_TAB_CONTROL_LOST/);
    assert.equal(existsSync(out), false);
  } finally { await fake.close(); }
});

test("structured account fields switch a wrong resolved account on the owned page", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Wrong Brand", merchantId: "WRONG", marketplace: "ATVPDKIKX0DER" };
  const behavior = pageBehavior({ facts, identity,
    fetchResult: { report: "file", text: "sku\nVERIFIED\n" },
    onNavigate(url) { facts.url = url; },
  });
  const evaluate = behavior.results["Runtime.evaluate"];
  behavior.results["Runtime.evaluate"] = (params) => {
    const expr = params.expression || "";
    if (expr.includes("getBoundingClientRect")) return { result: { value: { x: 20, y: 20, count: 1, current: false } } };
    if (!expr.includes("chooserButtonCount") && (expr.includes("full-page-account-switcher-account-details") || expr.includes("!location.pathname"))) {
      return { result: { value: true } };
    }
    return evaluate(params);
  };
  let clicks = 0;
  behavior.results["Input.dispatchMouseEvent"] = (params) => {
    if (params.type === "mouseReleased") {
      clicks++;
      const registry = JSON.parse(readFileSync(join(runtimes.get(fake.port), "leases.json"), "utf8"));
      assert.ok(registry.regional_context_claims[`${fake.port}:sc:na`], "regional claim held through account selection");
      identity.displayName = "Requested Brand";
      identity.merchantId = "REQUESTED";
    }
    return {};
  };
  const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url, behavior }] });
  try {
    const result = await runCli(fake.port, ["inventory", "--out", join(OUT_DIR, "switched.txt"),
      "--account-name", "Requested Brand", "--marketplace-label", "United States"]);
    assert.equal(result.code, 0, result.out);
    assert.match(result.out, /Account switch: done/);
    assert.ok(clicks >= 2);
    assert.ok(fake.sent.every((command) => command.targetId !== "ANCHOR"));
  } finally { await fake.close(); }
});

test("observable marketplace ID mismatch stops before fetching", { concurrency: false }, async () => {
  const facts = { url: "https://sellercentral.amazon.com/home", csrfMeta: true, chooserButtonCount: 0 };
  const identity = { displayName: "Example Brand", merchantId: "MERCHANT", marketplace: "A1PA6795UKMFR9" };
  let fetched = false;
  const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
    behavior: pageBehavior({ facts, identity, onFetch() { fetched = true; } }),
  }] });
  try {
    const result = await runCli(fake.port, BUSINESS_ARGS);
    assert.equal(result.code, 1, result.out);
    assert.match(result.out, /Requested marketplace us could not be verified/);
    assert.equal(fetched, false);
  } finally { await fake.close(); }
});


for (const [marketplace, sourceOrigin, wantedOrigin, scope] of [
  ["us", "https://sellercentral.amazon.com.br", "https://sellercentral.amazon.com", "sc:na"],
  ["de", "https://sellercentral.amazon.com.tr", "https://sellercentral.amazon.de", "sc:eu"],
  ["br", "https://sellercentral.amazon.com", "https://sellercentral.amazon.com.br", "global"],
  ["tr", "https://sellercentral.amazon.de", "https://sellercentral.amazon.com.tr", "global"],
  ["ca", "https://sellercentral.amazon.com", "https://sellercentral.amazon.com", "sc:na"],
]) {
  test(`report ${marketplace} routes within its declared group and acquires ${scope}`, async () => {
    const facts = { url: wantedOrigin + "/home", csrfMeta: true, chooserButtonCount: 0 };
    const identity = { displayName: "Routing Seller", merchantId: "MERCHANT", marketplace: marketplace.toUpperCase() };
    let heldScope;
    const behavior = pageBehavior({ facts, identity, fetchResult: { report: "file", text: "sku\nVERIFIED\n" },
      onNavigate(url) { facts.url = url; },
      onFetch() {
        const registry = JSON.parse(readFileSync(join(runtimes.get(fake.port), "leases.json"), "utf8"));
        const task = Object.values(registry.task_tabs)[0];
        heldScope = task.contextScope;
        const claim = scope === "global" ? registry.context_claims[String(fake.port)]
          : registry.regional_context_claims[`${fake.port}:${scope}`];
        assert.equal(claim.controlToken, task.controller.token);
      },
    });
    const fake = await startFakeCdp({ targets: [{ id: "ROUTING_ANCHOR", url: sourceOrigin + "/home", behavior }] });
    try {
      const result = await runCli(fake.port, ["inventory", "--marketplace", marketplace,
        "--expect-account", "Routing Seller", "--out", join(OUT_DIR, `route-${marketplace}.txt`)]);
      assert.equal(result.code, 0, result.out);
      assert.equal(heldScope, scope);
      const navigations = fake.sent.filter(command => command.method === "Page.navigate" && command.params.url !== "about:blank");
      assert.ok(navigations.length);
      assert.ok(navigations.every(command => new URL(command.params.url).origin === wantedOrigin));
      assert.ok(fake.sent.every(command => command.targetId !== "ROUTING_ANCHOR"));
    } finally { await fake.close(); }
  });
}

test("report rejects contradictory requested marketplace and origin before acquiring or selecting", async () => {
  const facts = { url: "https://sellercentral.amazon.de/home", csrfMeta: true, chooserButtonCount: 0 };
  const fake = await startFakeCdp({ targets: [{ id: "ANCHOR", url: facts.url,
    behavior: pageBehavior({ facts, identity: { displayName: "Seller", marketplace: "DE" } }) }] });
  try {
    const result = await runCli(fake.port, [...BUSINESS_ARGS, "--marketplace", "us", "--origin", "https://sellercentral.amazon.de"]);
    assert.equal(result.code, 1, result.out);
    assert.match(result.out, /TASK_TAB_CONTEXT_MISMATCH/);
    assert.equal(fake.sent.filter(command => command.method === "Target.createTarget").length, 0);
    assert.equal(fake.sent.filter(command => command.method === "Input.dispatchMouseEvent").length, 0);
  } finally { await fake.close(); }
});
