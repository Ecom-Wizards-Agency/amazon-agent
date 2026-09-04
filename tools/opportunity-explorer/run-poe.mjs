#!/usr/bin/env node
/*
 * One-command POE fetch over the Chrome debug protocol, sibling of
 * tools/report-fetcher/run.mjs, sharing its cdp.mjs client and
 * dedicated debug Chrome profile, started/reused automatically and logged into
 * Seller Central once through visible recovery mode.
 *
 *   node tools/browserctl/browserctl.mjs ensure --port 9222
 *   node tools/opportunity-explorer/run-poe.mjs doctor
 *   node tools/opportunity-explorer/run-poe.mjs niche  --niche-id <id> --marketplace de --client <slug> [--verbose]
 *   node tools/opportunity-explorer/run-poe.mjs search --query "kollagen pulver" --marketplace de --client <slug>
 *   node tools/opportunity-explorer/run-poe.mjs merchant-niches --marketplace us [--client <slug>]
 *
 * --marketplace is REQUIRED for data commands and is verified against the
 * session's actual marketplace (from the page's GetUserContext). When the
 * structured account options are present, a mismatch is recovered through the
 * account picker and then revalidated before any data request.
 *
 * ACCOUNT SAFETY: POE records every niche you open in that account's
 * "recently viewed niches", so researching one client while logged into another
 * client's account LEAKS the research to that account's owner. Every data
 * command now resolves and PRINTS the active account (display name +
 * partnerAccountId). Pass the configured account name, partner account id,
 * parent account name when applicable, and marketplace label. A mismatch first
 * triggers a trusted-CDP account-picker recovery. Data fetches remain blocked
 * until the post-switch identity matches.
 *
 * Output: formatted section files via format-poe.mjs into
 *   --out-dir  (default: output/<client>/opportunity-data/)
 * --verbose additionally saves the raw envelope JSON.
 *
 * Safety: dedicated CDP Chrome in its machine-policy mode, read-only GraphQL
 * reads in the operator's session, ~5 s pacing inside fetch-poe.js, one niche
 * per invocation. On {error} → exit non-zero and tell the operator.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ensureChrome, listPages, evaluate } from "../report-fetcher/cdp.mjs";
import { acquireTaskPage, releaseTaskPage, taskIdFor } from "../browserctl/task-tabs.mjs";
import { normalizeOrigin, accountPickerUrl, accountMatches, switchAccount, readIdentity, inspectPage, waitFor } from "../report-fetcher/sc-account.mjs";
import { formatEnvelope } from "./format-poe.mjs";
import { archiveClient } from "./pcloud-archive.mjs";
import { ArtifactRun } from "../artifactctl/client.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FETCH_SRC = fs.readFileSync(path.join(HERE, "fetch-poe.js"), "utf8");
let artifactContext = null;
let artifactRun = null;

function configureArtifacts(client, marketplace) {
  artifactContext = { client, marketplace: String(marketplace || "").toUpperCase() };
}

function registerPoeArtifact(file, env) {
  if (!artifactContext) return;
  artifactRun ||= new ArtifactRun({
    owner: "poe-downloader",
    workflow: "amazon-opportunity-explorer",
    client: artifactContext.client,
  });
  const disposition = artifactContext.client ? "archive-pcloud" : "preserve";
  artifactRun.register(file, disposition, disposition === "archive-pcloud" ? {
    archive: {
      client: artifactContext.client,
      dataset: "opportunity-data",
      market: artifactContext.marketplace,
      month: String(env.capturedAt || new Date().toISOString()).slice(0, 7),
      report_type: "POE",
      scope: "CAPTURE-RUN",
    },
  } : {});
}

function completeArtifacts() {
  if (artifactRun) artifactRun.complete("success");
}

process.on("exit", () => {
  if (artifactRun?.state === "active") artifactRun.complete("failed");
});

const CC_MP = {
  us: "ATVPDKIKX0DER", de: "A1PA6795UKMFR9", it: "APJ6JRA9NG5V4",
  es: "A1RKKUPIHCS9HS", fr: "A13V1IB3VIYZZH", uk: "A1F83G8C2ARO7P",
  nl: "A1805IZSGTT6HS", se: "A2NODRKZP88ZB9", pl: "A1C3SOZRARQ6R3",
  ca: "A2EUQ1WTGCTBG2", in: "A21TJRUUN4KGV", jp: "A1VC38T7YXB528",
};

const CC_ORIGIN = {
  us: "https://sellercentral.amazon.com",
  de: "https://sellercentral.amazon.de",
  it: "https://sellercentral.amazon.it",
  es: "https://sellercentral.amazon.es",
  fr: "https://sellercentral.amazon.fr",
  uk: "https://sellercentral.amazon.co.uk",
  nl: "https://sellercentral.amazon.nl",
  se: "https://sellercentral.amazon.se",
  pl: "https://sellercentral.amazon.pl",
  ca: "https://sellercentral.amazon.ca",
  in: "https://sellercentral.amazon.in",
  jp: "https://sellercentral.amazon.co.jp",
};

const argv = process.argv.slice(2);
const cmd = argv[0];
const opt = (name, dflt) => { const i = argv.indexOf(`--${name}`); return i > -1 && argv[i + 1] ? argv[i + 1] : dflt; };
const flag = (name) => argv.includes(`--${name}`);
const requestedTaskId = opt("task-id", null);
const defaultTaskKey = JSON.stringify(argv.filter((value, index) =>
  value !== "--verbose" && argv[index - 1] !== "--task-id" && value !== "--task-id"));

function usage(code = 1) {
  console.error("usage: run-poe.mjs doctor [--origin URL]");
  console.error("       run-poe.mjs niche --niche-id <id> --marketplace <cc> [--client <slug>] [account options] [--out-dir DIR] [--origin URL] [--verbose]");
  console.error("       run-poe.mjs search --query <kw> --marketplace <cc> [--client <slug>] [account options] [--out-dir DIR] [--origin URL]");
  console.error("       run-poe.mjs batch --queries \"kw1,kw2\" --marketplace <cc> --client <slug> [account options] [--top N=10 | --all] [--niche-ids id1,id2] [--origin URL]");
  console.error("       run-poe.mjs merchant-niches --marketplace <cc> [--client <slug>] [account options] [--origin URL]");
  console.error("       run-poe.mjs archive --client <slug> [--out-dir DIR] [--dry-run]");
  console.error("       run-poe.mjs self-test");
  console.error("  account options: --account-name NAME --expected-partner-account-id ID [--parent-account-name NAME] --marketplace-label LABEL");
  console.error("  --expect-account remains a legacy alias. A mismatch switches through the account picker only when the structured account options are complete.");
  console.error("  data commands infer the Seller Central origin from --marketplace; --origin remains an explicit override.");
  console.error("  archive mirrors output/<slug>/opportunity-data/ into the pCloud client archive (POE captures cannot be re-fetched later).");
  process.exit(code);
}

function sellerCentralOrigin(url) {
  try {
    const u = new URL(url);
    return /^sellercentral\.amazon\./.test(u.hostname) ? u.origin : null;
  } catch (_) {
    return null;
  }
}

function resolveDataOrigin(ccArg, explicitOrigin = null) {
  if (explicitOrigin) return normalizeOrigin(explicitOrigin);
  const cc = String(ccArg || "").toLowerCase();
  const origin = CC_ORIGIN[cc];
  if (!origin) throw new Error(`cannot infer Seller Central origin for marketplace '${ccArg || ""}'; pass --origin URL`);
  return origin;
}

function resolveDoctorOrigins(pages, explicitOrigin = null) {
  if (explicitOrigin) return [normalizeOrigin(explicitOrigin)];
  const poe = [];
  const other = [];
  for (const page of pages) {
    const origin = sellerCentralOrigin(page.url);
    if (!origin) continue;
    (/\/opportunity-explorer(?:\/|$)/.test(new URL(page.url).pathname) ? poe : other).push(origin);
  }
  return [...new Set([...poe, ...other])];
}

async function findOrCreatePoePage(origin) {
  const wantedOrigin = normalizeOrigin(origin);
  const taskId = requestedTaskId || taskIdFor(
    "amazon-opportunity-explorer",
    cmd === "doctor" ? defaultTaskKey : `${defaultTaskKey}|${wantedOrigin}`,
  );
  const taskPage = await acquireTaskPage({
    taskId, workflow: "amazon-opportunity-explorer", initialUrl: "about:blank",
    exclusiveContext: true,
  });
  try {
    await taskPage.session.send("Page.navigate", {
      url: wantedOrigin + "/opportunity-explorer",
    });
    return taskPage;
  } catch (error) {
    await releaseTaskPage(taskPage, { outcome: "error" }).catch(() => {});
    throw error;
  }
}

function poeReadinessError({ pageKind = "unknown", authState = "ambiguous", facts = {} } = {}) {
  const url = facts.url || "(URL unavailable)";
  const details = `Observed ${pageKind}/${authState} at ${url}`;
  let message;
  let code;
  if (pageKind === "chooser") {
    code = "POE_ACCOUNT_CHOOSER";
    message = `Seller Central is authenticated but stopped at the account chooser. ${details}. Select the account and marketplace in the preserved tab, or pass the structured account options so the runner can recover it.`;
  } else if (pageKind === "sign-in") {
    code = "POE_SIGNED_OUT";
    message = `Seller Central redirected this origin to sign-in. ${details}. Complete login in recovery mode.`;
  } else if (pageKind === "challenge") {
    code = "POE_HUMAN_CHALLENGE";
    message = `Seller Central is blocked by a human authentication challenge. ${details}. Complete it in recovery mode.`;
  } else if (pageKind === "auth-failed") {
    code = "POE_AUTHORIZATION_FAILED";
    message = `Seller Central loaded an authorization-failed page instead of Opportunity Explorer. ${details}. Verify this account has Opportunity Explorer access.`;
  } else {
    code = "POE_NOT_READY";
    message = `Opportunity Explorer did not become ready within the timeout. ${details}.`;
  }
  const error = new Error(message);
  error.code = code;
  error.preservePoeTab = true;
  return error;
}

async function waitPoeReady(session, timeoutMs = 30000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const ok = await evaluate(session,
      `document.readyState === "complete" && !!document.querySelector('meta[name="anti-csrftoken-a2z"]')`).catch(() => false);
    if (ok) return;
    await new Promise((r) => setTimeout(r, 500));
  }
  const page = await inspectPage(session, { timeoutMs: 10000 }).catch(() => ({
    pageKind: "unknown",
    authState: "ambiguous",
    facts: {},
  }));
  throw poeReadinessError(page);
}

async function waitPoeEntryState(session, timeoutMs = 30000) {
  // createPage returns as soon as the CDP target exists, before navigation has
  // necessarily committed. Identity recovery must not run against that brief
  // loading/about:blank state or a valid session is misread as unknown.
  try {
    await waitFor(session, `document.readyState === "complete" && (
      !!document.querySelector('meta[name="anti-csrftoken-a2z"]')
      || document.querySelectorAll('button.full-page-account-switcher-account-details').length > 0
      || /signin|auth|login|mfa|captcha|\\/ap\\/cvf/.test(location.href)
      || !!document.querySelector('input[type="password"],input[autocomplete="one-time-code"],input[name="guess"]')
    )`, "Opportunity Explorer app, account chooser, or authentication state", timeoutMs);
  } catch {
    const page = await inspectPage(session, { timeoutMs: 10000 }).catch(() => ({
      pageKind: "unknown",
      authState: "ambiguous",
      facts: {},
    }));
    throw poeReadinessError(page);
  }
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// The account-picker mechanics (waitFor, trusted clicks, the shadow-DOM
// confirm button, auth-state classification) live in the shared
// ../report-fetcher/sc-account.mjs since the 13.08.2026 account-chooser fix.
// POE passes returnTo /opportunity-explorer so a completed switch lands back
// on a POE page ready for GraphQL reads.
async function switchSellerCentralAccount(session, origin, profile) {
  await switchAccount(session, origin, profile, { returnTo: "/opportunity-explorer" });
  await waitPoeReady(session);
}

async function withPoePage(origin, work, { requireReady = true } = {}) {
  await ensureChrome();
  const taskPage = await findOrCreatePoePage(origin);
  const { session } = taskPage;
  let outcome = "success";
  try {
    if (requireReady) await waitPoeReady(session);
    return await work(session);
  } catch (error) {
    outcome = error?.preservePoeTab ? "inspection" : "error";
    if (error?.preservePoeTab) {
      console.error(`Preserving the blocked POE tab for inspection/recovery (${error.code || "POE_BLOCKED"}).`);
    }
    throw error;
  } finally {
    await releaseTaskPage(taskPage, { outcome }).catch(() => {});
  }
}

async function runFetch(session, callExpr) {
  const expr = `(async function(){ ${FETCH_SRC}\n return await ${callExpr}; })()`;
  return evaluate(session, expr, 180000);
}

// Resolve --marketplace <cc> to the obfuscated id we REQUEST in the GraphQL
// variables. One regional login covers every marketplace in that region (house
// rule, docs/daily-account-health-setup.md): from a .de session you can fetch
// de/it/es/fr/... directly. No UI switcher is needed. US needs the .com origin.
function requestedMarketplace(ccArg) {
  const cc = (ccArg || "").toLowerCase();
  if (!cc) { console.error("--marketplace <cc> is required (e.g. --marketplace de). No silent default."); process.exit(1); }
  const mp = CC_MP[cc];
  if (!mp) { console.error(`unknown marketplace code '${cc}'. Known: ${Object.keys(CC_MP).join(", ")}`); process.exit(1); }
  return mp;
}

function assertMarketplace(env, mpExpected) {
  if (env.marketplace !== mpExpected) {
    console.error(`marketplace mismatch: response is for ${env.marketplace}, requested ${mpExpected}. Wrong origin/region session?`);
    process.exit(1);
  }
}

// Resolve the ACTIVE Seller Central account from the live POE session.
// Shared implementation: GetUserContext ids + the account-switcher display
// name (sc-account.mjs readIdentity). accountMatches also comes from there.
async function readAccount(session) {
  return readIdentity(session, { timeoutMs: 30000 });
}

function assertAccount(acct, expected) {
  const label = acct.displayName || acct.partnerAccountId || "(unknown account)";
  console.error(`Account: ${label}${acct.partnerAccountId ? ` [partnerAccountId=${acct.partnerAccountId}]` : ""}`);
  if (!expected) {
    console.error("NOTE: no --expect-account given. POE research is visible in this account's recently-viewed niches; confirm this is the sanctioned account for this client.");
    return true;
  }
  const cands = [acct.displayName, acct.partnerAccountId, acct.merchantId].filter(Boolean);
  if (!cands.length) {
    console.error(`ACCOUNT CHECK FAILED: --expect-account "${expected}" was given but the session's account identity could not be resolved${acct.err ? ` (${acct.err})` : ""}. Aborting.`);
    return false;
  }
  if (!accountMatches(acct, expected)) {
    console.error(`ACCOUNT MISMATCH: expected "${expected}" but the active session is "${label}" [partnerAccountId=${acct.partnerAccountId || "?"}].`);
    console.error("The account must be recovered and revalidated before any POE request.");
    return false;
  }
  return true;
}

// One account preflight per command, before any data fetch.
async function accountPreflight(session) {
  const expectedId = opt("expected-partner-account-id", null);
  const expected = expectedId || opt("expect-account", null) || opt("account-name", null);
  let acct = await readAccount(session);
  if (assertAccount(acct, expected)) return true;
  const accountName = opt("account-name", null);
  const marketplaceLabel = opt("marketplace-label", null);
  if (!accountName || !marketplaceLabel || !expected) {
    console.error("ACCOUNT SWITCH NOT ATTEMPTED: structured account options are incomplete. No POE data was fetched.");
    return false;
  }
  console.error(`Recovering Seller Central session through the account picker: ${accountName} / ${marketplaceLabel}`);
  try {
    await switchSellerCentralAccount(session, resolveDataOrigin(opt("marketplace", null), opt("origin", null)), {
      accountName,
      parentAccountName: opt("parent-account-name", null),
      marketplaceLabel,
    });
  } catch (error) {
    console.error(String(error.message || error));
    console.error("ACCOUNT RECOVERY FAILED. No POE data was fetched.");
    return false;
  }
  acct = await readAccount(session);
  if (!assertAccount(acct, expectedId || expected)) {
    console.error("POST-SWITCH ACCOUNT CHECK FAILED. No POE data was fetched.");
    return false;
  }
  console.error("Account recovery succeeded and the partner account identity was revalidated.");
  return true;
}

async function withAccountCheckedPoePage(origin, work) {
  const result = await withPoePage(origin, async (session) => {
    await waitPoeEntryState(session);
    if (!await accountPreflight(session)) return { accountCheckFailed: true };
    // Account recovery must be allowed to run from the authenticated chooser.
    // Requiring the POE meta tag before this point made recovery unreachable
    // and mislabeled a valid login as a login failure.
    await waitPoeReady(session);
    return { value: await work(session) };
  }, { requireReady: false });
  if (result.accountCheckFailed) process.exit(1);
  return result.value;
}

function finish(env, { outDir, verbose }) {
  if (env.error) {
    console.error("fetch returned an error:", env.error);
    console.error("→ open/refresh the Opportunity Explorer tab in the debug Chrome (logged in, right account/marketplace) and re-run. Add --verbose to inspect.");
    process.exit(1);
  }
  const files = formatEnvelope(env, { outDir });
  for (const f of files) {
    const written = path.join(outDir, f.name);
    registerPoeArtifact(written, env);
    console.log(written);
  }
  if (verbose) {
    const raw = path.join(outDir, `raw_${env.kind}_${(env.capturedAt || "").replace(/[:]/g, "-")}.json`);
    fs.writeFileSync(raw, JSON.stringify(env, null, 1));
    registerPoeArtifact(raw, env);
    console.log(raw);
  }
}

if (cmd === "self-test") {
  const checks = [
    [resolveDataOrigin("de"), "https://sellercentral.amazon.de"],
    [resolveDataOrigin("uk"), "https://sellercentral.amazon.co.uk"],
    [resolveDataOrigin("us"), "https://sellercentral.amazon.com"],
    [resolveDataOrigin("de", "https://sellercentral.amazon.fr/path"), "https://sellercentral.amazon.fr"],
    [resolveDoctorOrigins([
      { url: "https://sellercentral.amazon.com/amazonsell/business" },
      { url: "https://sellercentral.amazon.de/opportunity-explorer" },
      { url: "https://example.com/" },
    ]).join(","), "https://sellercentral.amazon.de,https://sellercentral.amazon.com"],
    [accountPickerUrl("https://sellercentral.amazon.com", "/opportunity-explorer"), "https://sellercentral.amazon.com/account-switcher/default/merchantMarketplace?returnTo=%2Fopportunity-explorer"],
    [accountMatches({ displayName: "SwissKlip United States", partnerAccountId: "A1UOCFOJBIIPMH" }, "A1UOCFOJBIIPMH"), true],
    [accountMatches({ displayName: "Other account", partnerAccountId: "OTHER" }, "A1UOCFOJBIIPMH"), false],
    [poeReadinessError({ pageKind: "chooser", authState: "authenticated", facts: { url: "https://sellercentral.amazon.de/account-switcher/default/merchantMarketplace" } }).code, "POE_ACCOUNT_CHOOSER"],
    [poeReadinessError({ pageKind: "sign-in", authState: "logged_out", facts: { url: "https://sellercentral.amazon.de/ap/signin" } }).code, "POE_SIGNED_OUT"],
  ];
  for (const [actual, expected] of checks) {
    if (actual !== expected) throw new Error(`self-test failed: expected ${expected}, got ${actual}`);
  }
  console.log(`run-poe self-test: ${checks.length}/${checks.length} passed`);
  process.exit(0);
} else if (cmd === "doctor") {
  const ver = await ensureChrome();
  console.log(`Chrome: ${ver.Browser} | debug port reachable`);
  const pages = await listPages();
  const sc = pages.filter((p) => /sellercentral\.amazon\./.test(p.url));
  console.log(`Seller Central tabs: ${sc.length}${sc.length ? " → " + sc.map((p) => p.url.replace(/^https:\/\//, "").slice(0, 60)).join(", ") : ""}`);
  if (!sc.length) { console.log("Run browserctl ensure for port 9222. If authentication is needed, use browserctl auth; reserve an explicit recovery restart for a human challenge."); process.exit(1); }
  const origins = resolveDoctorOrigins(sc, opt("origin", null));
  const results = [];
  for (const origin of origins) {
    try {
      const acct = await withPoePage(origin, (session) => readAccount(session));
      results.push({ origin, acct });
    } catch (error) {
      results.push({ origin, error });
    }
  }
  results.sort((a, b) => Number(Boolean(b.acct)) - Number(Boolean(a.acct)));
  for (const result of results) {
    const prefix = origins.length > 1 ? `Active account (${result.origin})` : "Active account";
    if (result.acct) {
      const acct = result.acct;
      console.log(`${prefix}: ${acct.displayName || acct.partnerAccountId || "(unresolved)"}${acct.partnerAccountId ? ` [partnerAccountId=${acct.partnerAccountId}]` : ""}${acct.marketplace ? ` marketplace=${acct.marketplace}` : ""}`);
    } else {
      console.log(`${prefix}: (could not resolve: ${String(result.error).slice(0, 120)})`);
    }
  }
  console.log("Client runs should pass the structured account options so a mismatch can be recovered and revalidated safely.");
  process.exit(0);
} else if (cmd === "niche") {
  const nicheId = opt("niche-id", null);
  if (!nicheId) usage();
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : null);
  if (!outDir) { console.error("--client <slug> or --out-dir required"); process.exit(1); }
  const marketplace = opt("marketplace", null);
  configureArtifacts(client, marketplace);
  const mp = requestedMarketplace(marketplace);
  const origin = resolveDataOrigin(marketplace, opt("origin", null));
  const env = await withAccountCheckedPoePage(origin, (session) =>
    runFetch(session, `fetchPoeNiche(${JSON.stringify({ nicheId, obfuscatedMarketplaceId: mp })})`));
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
  completeArtifacts();
} else if (cmd === "search") {
  const query = opt("query", null);
  if (!query) usage();
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : null);
  if (!outDir) { console.error("--client <slug> or --out-dir required"); process.exit(1); }
  const marketplace = opt("marketplace", null);
  configureArtifacts(client, marketplace);
  const mp = requestedMarketplace(marketplace);
  const origin = resolveDataOrigin(marketplace, opt("origin", null));
  const env = await withAccountCheckedPoePage(origin, (session) =>
    runFetch(session, `fetchPoeSearch(${JSON.stringify({ query, obfuscatedMarketplaceId: mp })})`));
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
  completeArtifacts();
} else if (cmd === "batch") {
  // search → union/dedupe → download every kept niche in full.
  const queries = (opt("queries", opt("query", "")) || "").split(",").map((q) => q.trim()).filter(Boolean);
  const idArg = (opt("niche-ids", "") || "").split(",").map((x) => x.trim()).filter(Boolean);
  if (!queries.length && !idArg.length) usage();
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : null);
  if (!outDir) { console.error("--client <slug> or --out-dir required"); process.exit(1); }
  const top = flag("all") ? Infinity : Number(opt("top", "15"));
  const marketplace = opt("marketplace", null);
  configureArtifacts(client, marketplace);
  const mp = requestedMarketplace(marketplace);
  const origin = resolveDataOrigin(marketplace, opt("origin", null));
  await withAccountCheckedPoePage(origin, async (session) => {
    // 1) searches (paced inside fetch-poe), union by nicheId, keep search order (UI relevance)
    const byId = new Map();
    for (const q of queries) {
      const env = await runFetch(session, `fetchPoeSearch(${JSON.stringify({ query: q, obfuscatedMarketplaceId: mp })})`);
      assertMarketplace(env, mp);
      if (env.error) { console.error(`search "${q}" failed:`, env.error); process.exit(1); }
      finish(env, { outDir, verbose: flag("verbose") }); // per-query related-niches files
      for (const n of env.niches) if (!byId.has(n.nicheId)) byId.set(n.nicheId, n.nicheTitle);
      console.error(`search "${q}": ${env.niches.length} niches (union now ${byId.size})`);
    }
    for (const id of idArg) if (!byId.has(id)) byId.set(id, null);

    const ids = [...byId.keys()].slice(0, top);
    if (byId.size > ids.length) console.error(`NOTE: downloading top ${ids.length} of ${byId.size} niches (relevance order). Use --all or --top N for more.`);

    // 2) full download per niche, sequential (fetch-poe paces each heavy call)
    let ok = 0, failed = [];
    for (const [i, id] of ids.entries()) {
      const env = await runFetch(session, `fetchPoeNiche(${JSON.stringify({ nicheId: id, obfuscatedMarketplaceId: mp })})`);
      if (env.error) { failed.push({ id, title: byId.get(id), error: env.error }); console.error(`[${i + 1}/${ids.length}] ${byId.get(id) || id} FAILED: ${env.error}`); continue; }
      assertMarketplace(env, mp);
      finish(env, { outDir, verbose: flag("verbose") });
      ok += 1;
      console.error(`[${i + 1}/${ids.length}] ${env.niche.nicheTitle} ✓`);
    }
    console.error(`batch done: ${ok}/${ids.length} niches downloaded${failed.length ? `, ${failed.length} FAILED` : ""}`);
    if (failed.length) { console.error(JSON.stringify(failed, null, 1)); process.exit(1); }
  });
  completeArtifacts();
} else if (cmd === "merchant-niches") {
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : ".");
  const marketplace = opt("marketplace", null);
  configureArtifacts(client, marketplace);
  const mp = requestedMarketplace(marketplace);
  const origin = resolveDataOrigin(marketplace, opt("origin", null));
  const env = await withAccountCheckedPoePage(origin, (session) =>
    runFetch(session, `fetchPoeMerchantNiches(${JSON.stringify({ obfuscatedMarketplaceId: mp })})`));
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
  completeArtifacts();
} else if (cmd === "archive") {
  const client = opt("client", null);
  if (!client) { console.error("--client <slug> required"); process.exit(1); }
  const dryRun = flag("dry-run");
  const res = archiveClient(client, { srcDir: opt("out-dir", null), dryRun, log: (m) => console.error(m) });
  if (res.errors.length) {
    for (const e of res.errors) console.error(`archive: ${e}`);
    process.exit(1);
  }
  console.error(`archive ${dryRun ? "(dry run) " : ""}${client}: ${res.copied} copied, ${res.skipped} already archived${res.unsorted ? `, ${res.unsorted} unparseable -> _unsorted/` : ""}`);
  console.error(`  -> ${res.target}`);
} else {
  usage(cmd ? 1 : 0);
}
