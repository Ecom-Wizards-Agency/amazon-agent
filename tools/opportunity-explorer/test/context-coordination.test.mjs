import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import test from "node:test";
import { startFakeCdp } from "../../report-fetcher/test/helpers/fake-cdp.mjs";

const RUN = fileURLToPath(new URL("../run-poe.mjs", import.meta.url));
const MARKETPLACE = "ATVPDKIKX0DER";

async function scenario(t, drift, { marketplace = "us", origin = "https://sellercentral.amazon.com",
  requestedId = MARKETPLACE, identityMarketplace = MARKETPLACE, expectedScope = "sc:na",
  accountName = null, expectedPartnerId = null, initialDisplayName = "Example Seller",
  initialPartnerId = "PARTNER_A", switchDisplayName = "Example Seller",
  switchMarketplace = identityMarketplace, expectedFetches = null } = {}) {
  const root = mkdtempSync(join(tmpdir(), "poe-context-test-"));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const runtime = join(root, "browser-runtime");
  const registryPath = join(runtime, "leases.json");
  const outDir = join(root, "output", "test-fixture", "opportunity-data");
  const launcher = join(root, "launcher.mjs");
  const artifact = join(root, "artifactctl.mjs");
  const artifactCalls = join(root, "artifact-calls.jsonl");
  const deliveryCalls = join(root, "delivery-calls.jsonl");
  const archiveStub = join(root, "pcloud-stub.mjs");
  const loader = join(root, "loader.mjs");
  const registerLoader = join(root, "register-loader.mjs");
  // Stub the delivery boundary, not the runner: both local-artifact and pCloud
  // delivery variants exercise the same real account/context gates.
  writeFileSync(archiveStub, `import fs from "node:fs";
const record = value => fs.appendFileSync(${JSON.stringify(deliveryCalls)}, JSON.stringify(value) + "\\n");
export function archiveClient() { throw new Error("Unexpected archive command in context test"); }
export function prepareArchive(client) {
  record({ kind: "prepare", client });
  return { remote: "/test-only/" + client + "/opportunity-data" };
}
export async function publishFilesAsync(files, target) {
  record({ kind: "publish", files, target });
  return { remote_folder: target.remote, artifacts: files.map(file => ({
    name: file.name, remote_path: target.remote + "/" + file.name, verified: true,
  })) };
}
`);
  writeFileSync(loader, `export async function resolve(specifier, context, nextResolve) {
  if (specifier === "./pcloud-archive.mjs" && context.parentURL === ${JSON.stringify(pathToFileURL(RUN).href)}) {
    return { url: ${JSON.stringify(pathToFileURL(archiveStub).href)}, shortCircuit: true };
  }
  return nextResolve(specifier, context);
}
`);
  writeFileSync(registerLoader, `import { register } from "node:module";\nregister(${JSON.stringify(pathToFileURL(loader).href)});\n`);
  writeFileSync(launcher, 'process.stdout.write(JSON.stringify({managed:true,mode:"headless"}));\n');
  writeFileSync(artifact, `#!/usr/bin/env node\nimport fs from "node:fs";\nfs.appendFileSync(${JSON.stringify(artifactCalls)},JSON.stringify(process.argv.slice(2))+"\\n");\nprocess.stdout.write(JSON.stringify({id:"isolated-poe-run"}));\n`, { mode: 0o700 });
  const identity = { displayName: initialDisplayName, merchantId: "SELLER_A",
    partnerAccountId: initialPartnerId, marketplace: identityMarketplace, err: null };
  const envelope = { schemaVersion: "amazon-agent.poe.v1", kind: "search", marketplace: requestedId,
    capturedAt: "2026-09-09T00:00:00Z", query: "test query",
    niches: [{ nicheTitle: "Verified fixture niche", nicheId: "NICHE1", nicheSummary: {} }] };
  let switchClicks = 0;
  let actualOrigin = origin;
  let fetches = 0;
  let identityReads = 0;
  let identityReadsAfterFetch = 0;
  let guardHeldAtFetch = false;
  let commandCountAtFetch = 0;
  const fake = await startFakeCdp({ targets: [], onCreateTarget: ({ url }) => ({
    id: "POE_TASK", url, behavior: { results: {
      "Input.dispatchMouseEvent": ({ type }) => {
        if (type === "mouseReleased") {
          const registry = JSON.parse(readFileSync(registryPath, "utf8"));
          assert.ok(registry.regional_context_claims[`${fake.port}:${expectedScope}`], "selection holds its regional claim");
          switchClicks++;
          identity.displayName = switchDisplayName;
          identity.partnerAccountId = "PARTNER_A";
          identity.marketplace = switchMarketplace;
        }
        return {};
      },
      "Runtime.evaluate": ({ expression = "" }) => {
      if (expression.includes("return await fetchPoeSearch(")) {
        fetches++;
        commandCountAtFetch = fake.sent.length;
        const registry = JSON.parse(readFileSync(registryPath, "utf8"));
        guardHeldAtFetch = Boolean(registry.regional_context_claims[`${fake.port}:${expectedScope}`]);
        assert.equal(Object.values(registry.task_tabs)[0].contextScope, expectedScope);
        if (drift === "origin") actualOrigin = "https://sellercentral.amazon.de";
        if (drift === "missing-origin") actualOrigin = null;
        if (drift === "account") identity.merchantId = "SELLER_B";
        if (drift === "marketplace") identity.marketplace = "A1PA6795UKMFR9";
        if (drift === "ownership") {
          delete registry.regional_context_claims[`${fake.port}:${expectedScope}`];
          writeFileSync(registryPath, JSON.stringify(registry));
        }
        return { result: { value: envelope } };
      }
      if (accountName && expression.includes("getBoundingClientRect")) {
        return { result: { value: { x: 20, y: 20, count: 1, current: false } } };
      }
      if (accountName && !expression.includes("chooserButtonCount")
          && (expression.includes("full-page-account-switcher-account-details") || expression.includes("!location.pathname"))) {
        return { result: { value: true } };
      }
      if (expression === "location.href") return { result: { value: actualOrigin === null ? null : actualOrigin + "/opportunity-explorer" } };
      if (expression.includes("GetUserContext")) {
        identityReads++;
        if (drift === "baseline" && identityReads === 2) identity.partnerAccountId = "PARTNER_B";
        if (fetches) identityReadsAfterFetch++;
        return { result: { value: identity } };
      }
      if (expression.includes("readyState")) return { result: { value: true } };
      if (expression.includes("chooserButtonCount")) return { result: { value: {
        url: origin + "/opportunity-explorer", csrfMeta: true,
        chooserButtonCount: 0, title: "Opportunity Explorer",
      } } };
      return { result: { value: null } };
    } } },
  }) });
  t.after(() => fake.close());
  const result = await new Promise((resolve, reject) => {
    const child = spawn(process.execPath, ["--import", registerLoader, RUN, "search", "--query", "test query",
      "--marketplace", marketplace, "--origin", origin, "--expect-account", "PARTNER_A", "--client", "test-fixture", "--verbose",
      ...(accountName ? ["--account-name", accountName, "--marketplace-label", "United States"] : []),
      ...(expectedPartnerId ? ["--expected-partner-account-id", expectedPartnerId] : [])], {
      cwd: root, timeout: 10000,
      env: { ...process.env, CDP_HOST: "127.0.0.1", CDP_PORT: String(fake.port), CDP_AUTOSTART: "0",
        CDP_ENABLE_TEST_LEASES: "1", CDP_PYTHON: process.execPath, CDP_LAUNCHER: launcher,
        AMAZON_BROWSER_RUNTIME_DIR: runtime, AMAZON_BROWSER_POLICY: join(runtime, "policy.json"),
        AMAZON_ARTIFACTCTL: artifact },
    });
    let output = "";
    let stdout = "";
    child.stdout.on("data", (chunk) => { output += chunk; stdout += chunk; });
    child.stderr.on("data", (chunk) => { output += chunk; });
    child.on("error", reject);
    child.on("close", (code, signal) => resolve({ code, signal, output, stdout }));
  });
  assert.equal(result.signal, null, `CLI must finish within its budget: ${result.output}`);
  assert.equal(fetches, expectedFetches ?? (drift === "baseline" || switchDisplayName === "Wrong Seller" ? 0 : 1), result.output);
  if (fetches) assert.equal(guardHeldAtFetch, true, "fetch must run under an exclusive context claim");
  const registry = JSON.parse(readFileSync(registryPath, "utf8"));
  if (!["ownership", "origin", "missing-origin"].includes(drift)) assert.equal(registry.context_claims[String(fake.port)], undefined, "command releases its context claim");
  if (!["origin", "missing-origin"].includes(drift)) assert.equal(registry.regional_context_claims[`${fake.port}:${expectedScope}`], undefined, "regional claim is released or the simulated loss remains authoritative");
  const tasks = Object.values(registry.task_tabs);
  assert.equal(tasks.length, 1);
  if (!["ownership", "origin", "missing-origin"].includes(drift)) assert.equal(tasks[0].controller, null, "command releases task ownership");
  assert.equal(tasks[0].targetId, "POE_TASK", "evidence target remains registered");
  const publications = existsSync(deliveryCalls)
    ? readFileSync(deliveryCalls, "utf8").trim().split("\n").map(JSON.parse).filter(call => call.kind === "publish")
    : [];
  return { ...result, outDir, artifactCalls, publications, identityReadsAfterFetch, switchClicks,
    commandsAfterFetch: fake.sent.length - commandCountAtFetch,
    lease: registry.leases[`${fake.port}:POE_TASK`] };
}

test("POE accepts a response only while account, marketplace and ownership remain stable", async (t) => {
  const result = await scenario(t, null);
  assert.equal(result.code, 0, result.output);
  if (existsSync(result.outDir)) {
    assert.equal(readdirSync(result.outDir).length, 3, "formatted JSON, CSV and verbose envelope are saved");
    assert.equal(existsSync(result.artifactCalls), true);
    assert.equal(result.publications.length, 0);
  } else {
    assert.equal(existsSync(result.artifactCalls), false);
    assert.equal(result.publications.length, 1, "verified data reaches the mocked delivery boundary once");
    assert.equal(result.publications[0].files.length, 3);
    assert.ok(result.publications[0].files.some(file => file.content.includes("NICHE1")));
    const receipt = JSON.parse(result.stdout.trim());
    assert.equal(receipt.status, "archived_verified");
    assert.equal(receipt.complete, true);
    assert.equal(receipt.artifacts.length, 3);
    assert.equal(receipt.remote_folder, "/test-only/test-fixture/opportunity-data");
  }
  assert.equal(result.identityReadsAfterFetch, 1, "identity is rechecked after the fetch");
  assert.equal(result.lease.class, "background-success");
});

for (const drift of ["account", "marketplace"]) {
  test(`POE rejects ${drift} drift during fetch before saving any response`, async (t) => {
    const result = await scenario(t, drift);
    assert.equal(result.code, 1, result.output);
    assert.match(result.output, /POE_CONTEXT_CHANGED/);
    assert.equal(result.identityReadsAfterFetch, 1);
    assert.equal(existsSync(result.outDir), false, "no rejected response is formatted or saved");
    assert.equal(existsSync(result.artifactCalls), false, "rejected data never reaches artifact registration");
    assert.equal(result.publications.length, 0, "rejected data never reaches pCloud publication");
    assert.equal(result.lease.class, "inspection");
  });
}

test("POE rejects an in-flight response after context ownership is lost", async (t) => {
  const result = await scenario(t, "ownership");
  assert.equal(result.code, 1, result.output);
  assert.match(result.output, /TASK_TAB_CONTROL_LOST/);
  assert.equal(result.identityReadsAfterFetch, 0, "lost ownership blocks subsequent browser reads");
  assert.equal(result.commandsAfterFetch, 0, "no CDP command is issued after ownership loss");
  assert.equal(existsSync(result.outDir), false);
  assert.equal(existsSync(result.artifactCalls), false);
  assert.equal(result.publications.length, 0);
  assert.ok(result.lease, "target is preserved for ordinary stale-heartbeat recovery");
});

test("POE revalidates the requested account when establishing its baseline", async (t) => {
  const result = await scenario(t, "baseline");
  assert.equal(result.code, 1, result.output);
  assert.match(result.output, /POE_CONTEXT_(?:CHANGED|UNVERIFIED)|ACCOUNT MISMATCH/);
  assert.equal(existsSync(result.outDir), false);
  assert.equal(existsSync(result.artifactCalls), false);
  assert.equal(result.publications.length, 0);
  assert.equal(result.lease.class, "inspection");
});


test("POE keeps an EU claim when reading France through a Germany UI session", async (t) => {
  const result = await scenario(t, null, { marketplace: "fr", origin: "https://sellercentral.amazon.de",
    requestedId: "A13V1IB3VIYZZH", identityMarketplace: "A1PA6795UKMFR9", expectedScope: "sc:eu" });
  assert.equal(result.code, 0, result.output);
  assert.equal(result.publications.length, 1);
});


test("POE rejects an unannounced cross-region redirect before publishing a response", async (t) => {
  const result = await scenario(t, "origin");
  assert.equal(result.code, 1, result.output);
  assert.match(result.output, /TASK_TAB_CONTROL_LOST|TASK_TAB_CONTEXT_MISMATCH/);
  assert.equal(result.publications.length, 0);
  assert.equal(existsSync(result.outDir), false);
});


test("POE protects a fetched response when its current origin cannot be observed", async (t) => {
  const result = await scenario(t, "missing-origin");
  assert.equal(result.code, 1, result.output);
  assert.match(result.output, /TASK_TAB_CONTROL_LOST|TASK_TAB_CONTEXT_INVALID/);
  assert.equal(result.publications.length, 0);
});


test("structured POE name forces exact managed selection when a similar seller is active", async (t) => {
  const result = await scenario(t, null, { accountName: "Example Seller", initialDisplayName: "Example Seller Plus" });
  assert.equal(result.code, 0, result.output);
  assert.ok(result.switchClicks >= 2, "similar display name cannot bypass the account picker");
  assert.equal(result.publications.length, 1);
});

test("structured POE expected partner ID requires equality before skipping selection", async (t) => {
  const result = await scenario(t, null, { accountName: "Example Seller", expectedPartnerId: "PARTNER_A",
    initialPartnerId: "PARTNER_A_MORE" });
  assert.equal(result.code, 0, result.output);
  assert.ok(result.switchClicks >= 2, "a prefix match is not verified identity");
});

test("structured POE rejects a different observed seller after picker completion", async (t) => {
  const result = await scenario(t, null, { accountName: "Example Seller", initialDisplayName: "Example Seller Plus",
    switchDisplayName: "Wrong Seller" });
  assert.equal(result.code, 1, result.output);
  assert.match(result.output, /POST-SWITCH ACCOUNT CHECK FAILED/);
  assert.equal(result.publications.length, 0);
});

test("Allfemme United States verifies without an unnecessary account switch", async (t) => {
  const result = await scenario(t, null, { accountName: "Allfemme", initialDisplayName: "Allfemme United States",
    identityMarketplace: null });
  assert.equal(result.code, 0, result.output);
  assert.equal(result.switchClicks, 0);
  assert.equal(result.publications.length, 1);
});

test("structured POE recovers the requested marketplace before the first fetch", async (t) => {
  const result = await scenario(t, null, { accountName: "Allfemme", initialDisplayName: "Allfemme Canada",
    identityMarketplace: "A2EUQ1WTGCTBG2", switchDisplayName: "Allfemme United States", switchMarketplace: MARKETPLACE });
  assert.equal(result.code, 0, result.output);
  assert.ok(result.switchClicks >= 2);
});

test("a wrong marketplace after picker completion blocks POE and publication", async (t) => {
  const result = await scenario(t, null, { accountName: "Allfemme", initialDisplayName: "Allfemme United States",
    identityMarketplace: "A2EUQ1WTGCTBG2", switchDisplayName: "Allfemme United States", expectedFetches: 0 });
  assert.equal(result.code, 1, result.output);
  assert.match(result.output, /POST-SWITCH ACCOUNT CHECK FAILED/);
  assert.equal(result.publications.length, 0);
});
