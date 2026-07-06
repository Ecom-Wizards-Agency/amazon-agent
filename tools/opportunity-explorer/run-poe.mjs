#!/usr/bin/env node
/*
 * One-command POE fetch over the Chrome debug protocol — sibling of
 * tools/report-fetcher/run.mjs, sharing its cdp.mjs client and
 * launch-chrome-debug.sh prerequisite (dedicated debug Chrome profile,
 * logged into Seller Central once).
 *
 *   tools/report-fetcher/launch-chrome-debug.sh            # once; sign in
 *   node tools/opportunity-explorer/run-poe.mjs doctor
 *   node tools/opportunity-explorer/run-poe.mjs niche  --niche-id <id> --marketplace us --client <slug> [--verbose]
 *   node tools/opportunity-explorer/run-poe.mjs search --query "manuka honey" --marketplace us --client <slug>
 *   node tools/opportunity-explorer/run-poe.mjs merchant-niches --marketplace us [--client <slug>]
 *
 * --marketplace is REQUIRED for data commands and is verified against the
 * session's actual marketplace (from the page's GetUserContext) — a mismatch
 * aborts instead of silently pulling another country's data.
 * Output: formatted section files via format-poe.mjs into
 *   --out-dir  (default: output/<client>/opportunity-data/)
 * --verbose additionally saves the raw envelope JSON.
 *
 * Safety: connected debug Chrome only (never headless), read-only GraphQL
 * reads in the operator's session, ~5 s pacing inside fetch-poe.js, one niche
 * per invocation. On {error} → exit non-zero and tell the operator.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { assertChrome, listPages, createPage, closePage, evaluate } from "../report-fetcher/cdp.mjs";
import { formatEnvelope } from "./format-poe.mjs";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FETCH_SRC = fs.readFileSync(path.join(HERE, "fetch-poe.js"), "utf8");

const CC_MP = {
  us: "ATVPDKIKX0DER", de: "A1PA6795UKMFR9", it: "APJ6JRA9NG5V4",
  es: "A1RKKUPIHCS9HS", fr: "A13V1IB3VIYZZH", uk: "A1F83G8C2ARO7P",
  nl: "A1805IZSGTT6HS", se: "A2NODRKZP88ZB9", pl: "A1C3SOZRARQ6R3",
  ca: "A2EUQ1WTGCTBG2", in: "A21TJRUUN4KGV", jp: "A1VC38T7YXB528",
};

const argv = process.argv.slice(2);
const cmd = argv[0];
const opt = (name, dflt) => { const i = argv.indexOf(`--${name}`); return i > -1 && argv[i + 1] ? argv[i + 1] : dflt; };
const flag = (name) => argv.includes(`--${name}`);

function usage(code = 1) {
  console.error("usage: run-poe.mjs doctor | niche --niche-id <id> --marketplace <cc> [--client <slug>] [--out-dir DIR] [--origin URL] [--verbose]");
  console.error("       run-poe.mjs search --query <kw> --marketplace <cc> [--client <slug>] [--out-dir DIR]");
  console.error("       run-poe.mjs batch --queries \"kw1,kw2\" --marketplace <cc> --client <slug> [--top N=15 | --all] [--niche-ids id1,id2]");
  console.error("       run-poe.mjs merchant-niches --marketplace <cc> [--client <slug>]");
  process.exit(code);
}

async function findOrCreatePoePage(origin) {
  // reuse an existing POE tab if the operator has one open; else a temp tab
  const pages = await listPages();
  const existing = pages.find((p) => /sellercentral\.amazon\..*\/opportunity-explorer/.test(p.url));
  if (existing) {
    const { Session } = await import("../report-fetcher/cdp.mjs");
    return { targetId: null, session: await Session.open(existing.webSocketDebuggerUrl), temp: false };
  }
  const { targetId, session } = await createPage(origin + "/opportunity-explorer/explore");
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

async function runFetch(callExpr, origin) {
  await assertChrome();
  const { targetId, session, temp } = await findOrCreatePoePage(origin);
  try {
    await waitPoeReady(session);
    const expr = `(async function(){ ${FETCH_SRC}\n return await ${callExpr}; })()`;
    return await evaluate(session, expr, 180000);
  } finally {
    session.close();
    if (temp && targetId) await closePage(targetId);
  }
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

const origin = opt("origin", "https://sellercentral.amazon.com");

if (cmd === "doctor") {
  const ver = await assertChrome();
  console.log(`Chrome: ${ver.Browser} | debug port reachable`);
  const pages = await listPages();
  const sc = pages.filter((p) => /sellercentral\.amazon\./.test(p.url));
  console.log(`Seller Central tabs: ${sc.length}${sc.length ? " → " + sc.map((p) => p.url.replace(/^https:\/\//, "").slice(0, 60)).join(", ") : ""}`);
  if (!sc.length) console.log("Open Seller Central in the debug Chrome and log in, then re-run.");
  process.exit(0);
} else if (cmd === "niche") {
  const nicheId = opt("niche-id", null);
  if (!nicheId) usage();
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : null);
  if (!outDir) { console.error("--client <slug> or --out-dir required"); process.exit(1); }
  const mp = requestedMarketplace(opt("marketplace", null));
  const env = await runFetch(`fetchPoeNiche(${JSON.stringify({ nicheId, obfuscatedMarketplaceId: mp })})`, origin);
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
} else if (cmd === "search") {
  const query = opt("query", null);
  if (!query) usage();
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : null);
  if (!outDir) { console.error("--client <slug> or --out-dir required"); process.exit(1); }
  const mp = requestedMarketplace(opt("marketplace", null));
  const env = await runFetch(`fetchPoeSearch(${JSON.stringify({ query, obfuscatedMarketplaceId: mp })})`, origin);
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
  const mp = requestedMarketplace(opt("marketplace", null));

  // 1) searches (paced inside fetch-poe), union by nicheId, keep search order (UI relevance)
  const byId = new Map();
  for (const q of queries) {
    const env = await runFetch(`fetchPoeSearch(${JSON.stringify({ query: q, obfuscatedMarketplaceId: mp })})`, origin);
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
    const env = await runFetch(`fetchPoeNiche(${JSON.stringify({ nicheId: id, obfuscatedMarketplaceId: mp })})`, origin);
    if (env.error) { failed.push({ id, title: byId.get(id), error: env.error }); console.error(`[${i + 1}/${ids.length}] ${byId.get(id) || id} FAILED: ${env.error}`); continue; }
    assertMarketplace(env, mp);
    finish(env, { outDir, verbose: flag("verbose") });
    ok += 1;
    console.error(`[${i + 1}/${ids.length}] ${env.niche.nicheTitle} ✓`);
  }
  console.error(`batch done: ${ok}/${ids.length} niches downloaded${failed.length ? `, ${failed.length} FAILED` : ""}`);
  if (failed.length) { console.error(JSON.stringify(failed, null, 1)); process.exit(1); }
} else if (cmd === "merchant-niches") {
  const client = opt("client", null);
  const outDir = opt("out-dir", client ? `output/${client}/opportunity-data` : ".");
  const mp = requestedMarketplace(opt("marketplace", null));
  const env = await runFetch(`fetchPoeMerchantNiches(${JSON.stringify({ obfuscatedMarketplaceId: mp })})`, origin);
  assertMarketplace(env, mp);
  finish(env, { outDir, verbose: flag("verbose") });
} else {
  usage(cmd ? 1 : 0);
}
