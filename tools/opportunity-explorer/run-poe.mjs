#!/usr/bin/env node
/*
 * One-command POE fetch over the Chrome debug protocol — sibling of
 * tools/report-fetcher/run.mjs, sharing its cdp.mjs client and
 * launch-chrome-debug.sh prerequisite (dedicated debug Chrome profile,
 * logged into Seller Central once).
 *
 *   tools/report-fetcher/launch-chrome-debug.sh --mode recovery  # visible only for login/recovery
 *   tools/report-fetcher/launch-chrome-debug.sh            # normal headless mode
 *   node tools/opportunity-explorer/run-poe.mjs doctor
 *   node tools/opportunity-explorer/run-poe.mjs niche  --niche-id <id> --marketplace de --client <slug> [--verbose]
 *   node tools/opportunity-explorer/run-poe.mjs search --query "kollagen pulver" --marketplace de --client <slug>
 *   node tools/opportunity-explorer/run-poe.mjs merchant-niches --marketplace us [--client <slug>]
 *
 * --marketplace is REQUIRED for data commands and is verified against the
 * session's actual marketplace (from the page's GetUserContext) — a mismatch
 * aborts instead of silently pulling another country's data.
 *
 * ACCOUNT SAFETY: POE records every niche you open in that account's
 * "recently viewed niches", so researching one client while logged into another
 * client's account LEAKS the research to that account's owner. Every data
 * command now resolves and PRINTS the active account (display name +
 * partnerAccountId). Pass --expect-account "<name|partnerAccountId>" to HARD
 * ABORT on a mismatch before any niche is opened. See the POE skill's "Account
 * Safety" section and memory poe-account-identity-leak-rule.
 *
 * Output: formatted section files via format-poe.mjs into
 *   --out-dir  (default: output/<client>/opportunity-data/)
 * --verbose additionally saves the raw envelope JSON.
 *
 * Safety: dedicated CDP Chrome in its normal headless mode, read-only GraphQL
 * reads in the operator's session, ~5 s pacing inside fetch-poe.js, one niche
 * per invocation. On {error} → exit non-zero and tell the operator.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { assertChrome, listPages, createPage, closePage, evaluate } from "../report-fetcher/cdp.mjs";
import { formatEnvelope } from "./format-poe.mjs";
import { archiveClient } from "./pcloud-archive.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FETCH_SRC = fs.readFileSync(path.join(HERE, "fetch-poe.js"), "utf8");

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

function usage(code = 1) {
  console.error("usage: run-poe.mjs doctor [--origin URL]");
  console.error("       run-poe.mjs niche --niche-id <id> --marketplace <cc> [--client <slug>] [--expect-account NAME] [--out-dir DIR] [--origin URL] [--verbose]");
  console.error("       run-poe.mjs search --query <kw> --marketplace <cc> [--client <slug>] [--expect-account NAME] [--out-dir DIR] [--origin URL]");
  console.error("       run-poe.mjs batch --queries \"kw1,kw2\" --marketplace <cc> --client <slug> [--expect-account NAME] [--top N=15 | --all] [--niche-ids id1,id2] [--origin URL]");
  console.error("       run-poe.mjs merchant-niches --marketplace <cc> [--client <slug>] [--expect-account NAME] [--origin URL]");
  console.error("       run-poe.mjs archive --client <slug> [--out-dir DIR] [--dry-run]");
  console.error("       run-poe.mjs self-test");
  console.error("  --expect-account matches the active SC account (display name substring, or exact partnerAccountId/merchantId); mismatch ABORTS before any niche is opened.");
  console.error("  data commands infer the Seller Central origin from --marketplace; --origin remains an explicit override.");
  console.error("  archive mirrors output/<slug>/opportunity-data/ into the pCloud client archive (POE captures cannot be re-fetched later).");
  process.exit(code);
}

function normalizeOrigin(value) {
  try { return new URL(value).origin; }
  catch (_) { throw new Error(`invalid Seller Central origin: ${value}`); }
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
  // Reuse only a POE tab on the requested Seller Central origin. Reusing a
  // different region silently reads the wrong session and defeats the account
  // preflight.
  const wantedOrigin = normalizeOrigin(origin);
  const pages = await listPages();
  const existing = pages.find((p) =>
    sellerCentralOrigin(p.url) === wantedOrigin &&
    /\/opportunity-explorer(?:\/|$)/.test(new URL(p.url).pathname));
  if (existing) {
    const { Session } = await import("../report-fetcher/cdp.mjs");
    return { targetId: null, session: await Session.open(existing.webSocketDebuggerUrl), temp: false };
  }
  const { targetId, session } = await createPage(wantedOrigin + "/opportunity-explorer");
  return { targetId, session, temp: true };
}

async function waitPoeReady(session, timeoutMs = 30000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeoutMs) {
    const ok = await evaluate(session,
      `document.readyState === "complete" && !!document.querySelector('meta[name="anti-csrftoken-a2z"]')`);
    if (ok) return;
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error("POE page never became ready (readyState/meta tag) — is the session logged in?");
}

async function withPoePage(origin, work) {
  await assertChrome();
  const { targetId, session, temp } = await findOrCreatePoePage(origin);
  try {
    await waitPoeReady(session);
    return await work(session);
  } finally {
    session.close();
    if (temp && targetId) await closePage(targetId);
  }
}

async function runFetch(session, callExpr) {
  const expr = `(async function(){ ${FETCH_SRC}\n return await ${callExpr}; })()`;
  return evaluate(session, expr, 180000);
}

// Resolve --marketplace <cc> to the obfuscated id we REQUEST in the GraphQL
// variables. One regional login covers every marketplace in that region (house
// rule, docs/daily-account-health-setup.md): from a .de session you can fetch
// de/it/es/fr/... directly — no UI switcher needed. US needs the .com origin.
function requestedMarketplace(ccArg) {
  const cc = (ccArg || "").toLowerCase();
  if (!cc) { console.error("--marketplace <cc> is required (e.g. --marketplace de). No silent default."); process.exit(1); }
  const mp = CC_MP[cc];
  if (!mp) { console.error(`unknown marketplace code '${cc}' — known: ${Object.keys(CC_MP).join(", ")}`); process.exit(1); }
  return mp;
}

function assertMarketplace(env, mpExpected) {
  if (env.marketplace !== mpExpected) {
    console.error(`marketplace mismatch: response is for ${env.marketplace}, requested ${mpExpected}. Wrong origin/region session?`);
    process.exit(1);
  }
}

// Resolve the ACTIVE Seller Central account from the live POE session: ids from
// GetUserContext (partnerAccountId/merchantId) plus the account-switcher display
// name from the DOM. Returns { displayName, partnerAccountId, merchantId, marketplace, err }.
async function readAccount(session) {
  const expr = `(async function(){ ${FETCH_SRC}
    var out = { displayName: null, partnerAccountId: null, merchantId: null, marketplace: null, err: null };
    try {
      var c = await fetchPoeContext();
      var u = (c && c.userContext) || {};
      out.partnerAccountId = u.partnerAccountId || null;
      out.merchantId = u.merchantId || null;
      out.marketplace = (c && c.marketplace) || u.marketplaceSelection || null;
      if (c && c.error) out.err = c.error;
    } catch (e) { out.err = String(e); }
    var el = document.querySelector('[class*="AccountSwitcher" i]')
          || document.querySelector('[data-testid*="account-switcher" i]')
          || document.querySelector('[id*="account-switcher" i]');
    if (el) out.displayName = (el.textContent || "").replace(/\\s+/g, " ").trim().slice(0, 80);
    return out;
  })()`;
  return evaluate(session, expr, 30000);
}

// Print the active account for the audit trail, and hard-abort on an
// --expect-account mismatch BEFORE any niche is opened (so nothing leaks).
function assertAccount(acct, expected) {
  const label = acct.displayName || acct.partnerAccountId || "(unknown account)";
  console.error(`Account: ${label}${acct.partnerAccountId ? ` [partnerAccountId=${acct.partnerAccountId}]` : ""}`);
  if (!expected) {
    console.error("NOTE: no --expect-account given. POE research is visible in this account's recently-viewed niches; confirm this is the sanctioned account for this client.");
    return true;
  }
  const norm = (s) => String(s || "").toLowerCase().replace(/\s+/g, " ").trim();
  const want = norm(expected);
  const cands = [acct.displayName, acct.partnerAccountId, acct.merchantId].map(norm).filter(Boolean);
  if (!cands.length) {
    console.error(`ACCOUNT CHECK FAILED: --expect-account "${expected}" was given but the session's account identity could not be resolved${acct.err ? ` (${acct.err})` : ""}. Aborting.`);
    return false;
  }
  const hit = cands.some((c) => c === want || c.includes(want) || want.includes(c));
  if (!hit) {
    console.error(`ACCOUNT MISMATCH: expected "${expected}" but the active session is "${label}" [partnerAccountId=${acct.partnerAccountId || "?"}].`);
    console.error("Aborting to avoid leaking this client's POE research into the wrong account. Switch the debug Chrome to the correct Seller Central account and re-run.");
    return false;
  }
  return true;
}

// One account preflight per command, before any data fetch.
async function accountPreflight(session) {
  const acct = await readAccount(session);
  return assertAccount(acct, opt("expect-account", null));
}

async function withAccountCheckedPoePage(origin, work) {
  const result = await withPoePage(origin, async (session) => {
    if (!await accountPreflight(session)) return { accountCheckFailed: true };
    return { value: await work(session) };
  });
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
  for (const f of files) console.log(path.join(outDir, f.name));
  if (verbose) {
    const raw = path.join(outDir, `raw_${env.kind}_${(env.capturedAt || "").replace(/[:]/g, "-")}.json`);
    fs.writeFileSync(raw, JSON.stringify(env, null, 1));
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
  ];
  for (const [actual, expected] of checks) {
    if (actual !== expected) throw new Error(`self-test failed: expected ${expected}, got ${actual}`);
  }
  console.log(`run-poe self-test: ${checks.length}/${checks.length} passed`);
  process.exit(0);
} else if (cmd === "doctor") {
  const ver = await assertChrome();
  console.log(`Chrome: ${ver.Browser} | debug port reachable`);
  const pages = await listPages();
  const sc = pages.filter((p) => /sellercentral\.amazon\./.test(p.url));
  console.log(`Seller Central tabs: ${sc.length}${sc.length ? " → " + sc.map((p) => p.url.replace(/^https:\/\//, "").slice(0, 60)).join(", ") : ""}`);
  if (!sc.length) { console.log("Open Seller Central in the debug Chrome and log in, then re-run."); process.exit(0); }
  const origins = resolveDoctorOrigins(sc, opt("origin", null));
  const results = await Promise.all(origins.map(async (origin) => {
    try {
      const acct = await withPoePage(origin, (session) => readAccount(session));
      return { origin, acct };
    } catch (error) {
      return { origin, error };
    }
  }));
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
  console.log("Before pulling POE for a client, confirm this is the sanctioned account and pass --expect-account to enforce it.");
  process.exit(0);
} else if (cmd === "niche") {
  const nicheId = opt("niche-id", null);
  if (!nicheId) usage();
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : null);
  if (!outDir) { console.error("--client <slug> or --out-dir required"); process.exit(1); }
  const marketplace = opt("marketplace", null);
  const mp = requestedMarketplace(marketplace);
  const origin = resolveDataOrigin(marketplace, opt("origin", null));
  const env = await withAccountCheckedPoePage(origin, (session) =>
    runFetch(session, `fetchPoeNiche(${JSON.stringify({ nicheId, obfuscatedMarketplaceId: mp })})`));
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
} else if (cmd === "search") {
  const query = opt("query", null);
  if (!query) usage();
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : null);
  if (!outDir) { console.error("--client <slug> or --out-dir required"); process.exit(1); }
  const marketplace = opt("marketplace", null);
  const mp = requestedMarketplace(marketplace);
  const origin = resolveDataOrigin(marketplace, opt("origin", null));
  const env = await withAccountCheckedPoePage(origin, (session) =>
    runFetch(session, `fetchPoeSearch(${JSON.stringify({ query, obfuscatedMarketplaceId: mp })})`));
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
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
} else if (cmd === "merchant-niches") {
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : ".");
  const marketplace = opt("marketplace", null);
  const mp = requestedMarketplace(marketplace);
  const origin = resolveDataOrigin(marketplace, opt("origin", null));
  const env = await withAccountCheckedPoePage(origin, (session) =>
    runFetch(session, `fetchPoeMerchantNiches(${JSON.stringify({ obfuscatedMarketplaceId: mp })})`));
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
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
