#!/usr/bin/env node
/*
 * One-command Seller Central report fetch — hands-off, no console paste.
 *
 * Runs the report fetch in Chrome's REAL page main world over the DevTools
 * Protocol (CDP), so it uses the operator's existing logged-in session. Any
 * agent with shell access (Codex @computer) can run this; no browser sandbox.
 *
 *   node run.mjs sqp --asin B0GF8LG5JV --week 2026-06-27 --out out.csv
 *   node run.mjs sqp --asin B0GF8LG5JV --weeks 2026-06-20,2026-06-27 --out out.csv
 *   node run.mjs business --start 2026-06-01 --end 2026-06-30 --out out.csv
 *   node run.mjs business --start .. --end .. --asins B0..,B0.. --report parent --out out.csv
 *   node run.mjs doctor            # check the Chrome debug connection + a logged-in tab
 *
 * Options: --marketplace us (default) · --verbose (also write <out>.raw.json + print column ids)
 *
 * Prereq: Chrome running with the debug port and logged into Seller Central:
 *   tools/report-fetcher/launch-chrome-debug.sh
 * Read-only. See BRANDING-adjacent Safety Rules carve-out in AGENTS.md.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { assertChrome, listPages, createPage, closePage, evaluate, Session } from "./cdp.mjs";
import { format } from "./format-seller-reports.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FETCH_SRC = readFileSync(join(HERE, "fetch-seller-reports.js"), "utf8");
const LEGACY = { child: "102:DetailSalesTrafficByChildItem", parent: "102:DetailSalesTrafficByParentItem",
  sku: "102:DetailSalesTrafficBySKU", date: "102:SalesTrafficTimeSeries" };

function parseArgs(argv) {
  const cmd = argv[0]; const o = { _: cmd };
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) { const k = a.slice(2); const v = argv[i + 1]; if (v && !v.startsWith("--")) { o[k] = v; i++; } else o[k] = true; }
  }
  return o;
}

function die(msg) { console.error("ERROR: " + msg); process.exit(1); }

async function findSellerCentralOrigin() {
  const pages = await listPages();
  const sc = pages.find((p) => /sellercentral\.amazon\./.test(p.url || ""));
  if (!sc) die("No logged-in Seller Central tab found. Open https://sellercentral.amazon.com and sign in " +
    "(same Chrome that was launched with the debug port), then retry.");
  return new URL(sc.url).origin;
}

async function waitReady(session, needMetaTag) {
  for (let i = 0; i < 100; i++) {
    const ok = await evaluate(session,
      `(function(){return /^https?:/.test(location.href) && document.readyState==='complete' && (${needMetaTag ? "!!document.querySelector('meta[name=\\'anti-csrftoken-a2z\\']')" : "true"});})()`);
    if (ok) return;
    await new Promise((r) => setTimeout(r, 200));
  }
  throw new Error("page did not become ready" + (needMetaTag ? " (anti-csrftoken meta tag never appeared — not a Brand Analytics page / not logged in)" : ""));
}

async function runFetch(pageUrl, needMetaTag, call) {
  const { targetId, session } = await createPage(pageUrl);
  try {
    await waitReady(session, needMetaTag);
    const expr = `(async()=>{ ${FETCH_SRC}\n; return await ${call}; })()`;
    return await evaluate(session, expr);
  } finally { session.close(); await closePage(targetId); }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const mp = (args.marketplace || "us").toLowerCase();

  if (args._ === "doctor") {
    const v = await assertChrome();
    console.log("Chrome:", v.Browser, "| debug port reachable");
    const pages = await listPages();
    const sc = pages.filter((p) => /sellercentral\.amazon\./.test(p.url || ""));
    if (!sc.length) {
      console.log("Seller Central: no tab found — open https://sellercentral.amazon.com in the debug window and sign in.");
      process.exit(1);
    }
    // Actively verify the debug profile is SIGNED IN (not sitting on a login page).
    const s = await Session.open(sc[0].webSocketDebuggerUrl);
    let st;
    try {
      st = await evaluate(s, `(function(){return {url:location.href,title:document.title,` +
        `signin:/signin|ap\\/signin|authportal|\\/account-picker|\\/ax\\//i.test(location.href)||/sign[- ]?in/i.test(document.title)};})()`);
    } finally { s.close(); }
    console.log(`Seller Central: ${sc.length} tab(s) → ${new URL(sc[0].url).host}`);
    if (st && !st.signin) { console.log("Login: OK — session is active. Ready to fetch."); process.exit(0); }
    console.log("Login: NOT signed in (on a sign-in page). Sign into Seller Central in the debug window, then re-run doctor.");
    process.exit(1);
  }

  if (!args.out) die("missing --out <path.csv>");
  await assertChrome();
  const origin = await findSellerCentralOrigin();

  let doc, callDesc;
  if (args._ === "sqp") {
    const asins = (args.asin ? [args.asin] : (args.asins ? String(args.asins).split(",") : []));
    if (!asins.length) die("sqp needs --asin B0... (or --asins a,b)");
    const weeks = args.week ? [args.week] : (args.weeks ? String(args.weeks).split(",") : []);
    if (!weeks.length) die("sqp needs --week YYYY-MM-DD (week-ending Saturday; or --weeks a,b)");
    callDesc = `SQP asins=${asins.join(",")} weeks=${weeks.join(",")}`;
    const params = JSON.stringify({ asins, marketplace: mp, reportingRange: (args.range || "weekly"), periodEndDates: weeks });
    doc = await runFetch(origin + "/brand-analytics/dashboard/query-performance", true, `fetchSqp(${params})`);
  } else if (args._ === "business") {
    if (!args.start || !args.end) die("business needs --start and --end (YYYY-MM-DD)");
    const legacy = LEGACY[args.report || "child"] || args.report;
    const asins = args.asins ? String(args.asins).split(",") : [];
    callDesc = `Business ${legacy} ${args.start}..${args.end}` + (asins.length ? ` asins=${asins.join(",")}` : " (all child ASINs)");
    const params = JSON.stringify({ legacyReportId: legacy, asins, startDate: args.start, endDate: args.end });
    doc = await runFetch(origin + "/business-reports/ref=xx_sitemetric_favb_xx", false, `fetchBusinessReport(${params})`);
  } else {
    die("usage: run.mjs <sqp|business|doctor> [options] — see the header of run.mjs");
  }

  if (!doc) die("no data returned from the page (evaluate returned undefined)");
  if (args.verbose) {
    const rawPath = args.out.replace(/\.csv$/, "") + ".raw.json";
    writeFileSync(rawPath, JSON.stringify(doc, null, 1));
    const firstRow = (doc.batches || []).flatMap((b) => b.rows || [])[0] || {};
    console.log("[verbose] wrote", rawPath, "| column ids:", Object.keys(firstRow).join(", ") || "(none)");
  }
  if (doc.error) die(`fetch returned an error: ${doc.error}\n  (${callDesc}) — the tab may be logged out / wrong marketplace, or a payload field changed. Re-run with --verbose to capture the raw response.`);

  const csv = format(doc);                       // throws + lists columns if a required one is unmapped
  writeFileSync(args.out, csv);
  const rows = csv.split("\n").filter((l) => l.trim()).length - 1;
  console.log(`OK — wrote ${args.out} (${rows} rows) · ${callDesc}`);
}

main().catch((e) => die(e.message));
