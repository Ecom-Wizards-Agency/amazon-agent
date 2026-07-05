#!/usr/bin/env node
/*
 * One-command Seller Central report fetch — hands-off, no console paste.
 *
 * Runs the fetch in Chrome's REAL page main world over the DevTools Protocol (CDP),
 * using the operator's existing logged-in session. Any agent with shell access
 * (Codex @computer) can run this; no browser sandbox. Read-only.
 *
 * Copy-paste path (fill a per-client config once, then a fixed command):
 *   node run.mjs sqp      --config config.<client>.json        # every ASIN group
 *   node run.mjs business --config config.<client>.json
 *   node run.mjs scp      --config config.<client>.json
 *   node run.mjs tst      --config config.<client>.json
 *   node run.mjs all      --config config.<client>.json        # every configured report
 *   node run.mjs <any>    --config <cfg> --plan                # show the plan, touch nothing
 *
 * Explicit-flag path:
 *   node run.mjs sqp --asins B0..,B0.. --weeks 2026-06-27 --range weekly|monthly|quarterly \
 *                    --out output/<client>/reporting/sqp.csv [--split]
 *   node run.mjs business --start 2026-06-01 --end 2026-06-30 [--asins ..] [--report child|parent|sku] --out ..
 *   node run.mjs scp --weeks 2026-06-27 [--brand <id>] [--asins ..] --out ..
 *   node run.mjs tst --weeks 2026-06-27 [--brand <b>] [--search-term <t>] --out ..
 *   node run.mjs doctor          # check the debug connection + that the profile is signed in
 *
 * Options: --marketplace us · --verbose (also write <out>.raw.json + column ids) · --split (SQP)
 * Prereq: tools/report-fetcher/launch-chrome-debug.sh (debug Chrome, signed into Seller Central).
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { assertChrome, listPages, createPage, closePage, evaluate, Session } from "./cdp.mjs";
import { format } from "./format-seller-reports.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FETCH_SRC = readFileSync(join(HERE, "fetch-seller-reports.js"), "utf8");
const LEGACY = { child: "102:DetailSalesTrafficByChildItem", parent: "102:DetailSalesTrafficByParentItem",
  sku: "102:DetailSalesTrafficBySKU", date: "102:SalesTrafficTimeSeries" };

function parseArgs(argv) {
  const o = { _: argv[0] };
  for (let i = 1; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) { const k = a.slice(2); const v = argv[i + 1]; if (v && !v.startsWith("--")) { o[k] = v; i++; } else o[k] = true; }
  }
  return o;
}
function die(msg) { console.error("ERROR: " + msg); process.exit(1); }
function slug(s) { return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""); }
function ensureDir(f) { mkdirSync(dirname(f), { recursive: true }); }
function list(v) { return Array.isArray(v) ? v : (v ? String(v).split(",").map((x) => x.trim()).filter(Boolean) : []); }

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
    return await evaluate(session, `(async()=>{ ${FETCH_SRC}\n; return await ${call}; })()`);
  } finally { session.close(); await closePage(targetId); }
}

// Write one report doc to a CSV (+ optional raw json), with error/verbose handling.
function emit(doc, outPath, verbose, desc) {
  if (!doc) die("no data returned from the page (evaluate returned undefined)");
  if (verbose) {
    const rawPath = outPath.replace(/\.csv$/, "") + ".raw.json";
    ensureDir(rawPath); writeFileSync(rawPath, JSON.stringify(doc, null, 1));
    const firstRow = (doc.batches || []).flatMap((b) => b.rows || [])[0] || {};
    console.log("[verbose]", rawPath, "| column ids:", Object.keys(firstRow).join(", ") || "(none)");
  }
  if (doc.error) die(`fetch error: ${doc.error}\n  (${desc}) — tab logged out / wrong marketplace, or a payload field changed. --verbose captures the raw response.`);
  const csv = format(doc);                 // throws + lists columns if a required one is unmapped
  ensureDir(outPath); writeFileSync(outPath, csv);
  const rows = csv.split("\n").filter((l) => l.trim()).length - 1;
  console.log(`OK — ${outPath} (${rows} rows) · ${desc}`);
}

// Build the job list for a report from config and/or flags. Each job:
//   { report, pageUrl, needMetaTag, call, out, desc, split?, asins? }
function buildJobs(report, cfg, args, mp) {
  const cfgFor = (k) => (cfg && cfg[k]) || {};
  const jobs = [];

  if (report === "sqp") {
    const c = cfgFor("sqp");
    const range = (args.range || c.reporting_range || "weekly").toLowerCase();
    const weeks = list(args.weeks || args.week) .length ? list(args.weeks || args.week) : list(c.period_end_dates);
    if (!weeks.length) die("sqp needs --weeks YYYY-MM-DD (or period_end_dates in config)");
    const outDir = c.out_dir || "output/<client>/reporting/";
    const split = args.split || c.split || false;
    let groups;
    if (args.asins || args.asin) groups = { [slug(args.asins || args.asin)]: list(args.asins || args.asin) };
    else if (c.asin_groups) groups = c.asin_groups;
    else die("sqp needs --asins B0..,B0.. or asin_groups in config");
    for (const [name, asins] of Object.entries(groups)) {
      const stem = args.out ? args.out.replace(/\.csv$/, "") : join(outDir, `sqp_${slug(name)}`);
      jobs.push({ report, group: name, asins: list(asins), range, weeks, split,
        pageUrl: "/brand-analytics/dashboard/query-performance", needMetaTag: true, stem });
    }
  } else if (report === "scp" || report === "tst") {
    const c = cfgFor(report);
    const range = (args.range || c.reporting_range || "weekly").toLowerCase();
    const weeks = list(args.weeks || args.week).length ? list(args.weeks || args.week) : list(c.period_end_dates);
    if (!weeks.length) die(`${report} needs --weeks YYYY-MM-DD (or period_end_dates in config)`);
    const out = args.out || c.out || join(c.out_dir || "output/<client>/reporting/", `${report}.csv`);
    const p = { marketplace: mp, reportingRange: range, periodEndDates: weeks };
    if (args.asins || c.asins) p.asins = list(args.asins || c.asins);
    if (args.brand || c.brand) p.brand = args.brand || c.brand;
    if (report === "tst" && (args["search-term"] || c.search_term)) p.searchTerm = args["search-term"] || c.search_term;
    const fn = report === "scp" ? "fetchScp" : "fetchTst";
    jobs.push({ report, out, range, weeks, pageUrl: `/brand-analytics/dashboard/${report === "scp" ? "brand-catalog-performance" : "top-search-terms"}`,
      needMetaTag: true, call: `${fn}(${JSON.stringify(p)})`, desc: `${report.toUpperCase()} ${range} ${weeks.join(",")}` });
  } else if (report === "business") {
    const c = cfgFor("business_report");
    const start = args.start || c.start_date, end = args.end || c.end_date;
    if (!start || !end) die("business needs --start and --end (or start_date/end_date in config)");
    const legacy = LEGACY[args.report_variant || args.variant || "child"] || c.legacy_report_id || LEGACY.child;
    const asins = list(args.asins || c.asins);
    const out = args.out || c.out || join(c.out_dir || "output/<client>/reporting/", `business_${start}.csv`);
    const p = { legacyReportId: legacy, asins, startDate: start, endDate: end };
    jobs.push({ report, out, pageUrl: "/business-reports/ref=xx_sitemetric_favb_xx", needMetaTag: false,
      call: `fetchBusinessReport(${JSON.stringify(p)})`, desc: `Business ${legacy} ${start}..${end}` + (asins.length ? ` asins=${asins.join(",")}` : " (all)") });
  } else die(`unknown report: ${report}`);
  return jobs;
}

async function runSqpJob(origin, job, args) {
  const p = { asins: job.asins, marketplace: (args.marketplace || "us").toLowerCase(), reportingRange: job.range, periodEndDates: job.weeks };
  const doc = await runFetch(origin + job.pageUrl, true, `fetchSqp(${JSON.stringify(p)})`);
  if (doc && doc.error) return emit(doc, `${job.stem}.csv`, args.verbose, `SQP ${job.group}`);
  if (job.split) {
    for (const asin of job.asins) {
      const sub = { ...doc, batches: (doc.batches || []).filter((b) => b.asin === asin) };
      emit(sub, `${job.stem}_${asin}.csv`, args.verbose, `SQP ${job.group}/${asin}`);
    }
  } else {
    emit(doc, `${job.stem}.csv`, args.verbose, `SQP ${job.group} [${job.asins.join(",")}]`);
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const mp = (args.marketplace || "us").toLowerCase();
  const cfg = args.config ? JSON.parse(readFileSync(args.config, "utf8")) : null;

  if (args._ === "doctor") {
    const v = await assertChrome();
    console.log("Chrome:", v.Browser, "| debug port reachable");
    const sc = (await listPages()).filter((p) => /sellercentral\.amazon\./.test(p.url || ""));
    if (!sc.length) { console.log("Seller Central: no tab — open https://sellercentral.amazon.com in the debug window and sign in."); process.exit(1); }
    const s = await Session.open(sc[0].webSocketDebuggerUrl);
    let st;
    try {
      st = await evaluate(s, `(function(){return {signin:/signin|ap\\/signin|authportal|\\/account-picker|\\/ax\\//i.test(location.href)||/sign[- ]?in/i.test(document.title)};})()`);
    } finally { s.close(); }
    console.log(`Seller Central: ${sc.length} tab(s) → ${new URL(sc[0].url).host}`);
    if (st && !st.signin) { console.log("Login: OK — session is active. Ready to fetch."); process.exit(0); }
    console.log("Login: NOT signed in. Sign into Seller Central in the debug window, then re-run doctor.");
    process.exit(1);
  }

  const reports = args._ === "all" ? ["sqp", "business", "scp", "tst"].filter((r) => cfg && (cfg[r] || cfg[r === "business" ? "business_report" : r])) : [args._];
  if (!reports.length || !["sqp", "scp", "tst", "business"].includes(reports[0]))
    die("usage: run.mjs <sqp|scp|tst|business|all|doctor> [--config <cfg>] [flags] — see the header of run.mjs");

  const jobs = reports.flatMap((r) => buildJobs(r, cfg, args, mp));

  if (args.plan) {
    console.log("PLAN (nothing fetched):");
    for (const j of jobs) {
      if (j.report === "sqp") console.log(`  SQP  ${j.group}: ${j.asins.length} ASIN(s) × ${j.weeks.length} ${j.range} period(s) → ${j.split ? j.stem + "_<asin>.csv (split)" : j.stem + ".csv (combined)"}`);
      else console.log(`  ${j.report.toUpperCase()}  → ${j.out}   (${j.desc})`);
    }
    process.exit(0);
  }

  await assertChrome();
  const sc = (await listPages()).find((p) => /sellercentral\.amazon\./.test(p.url || ""));
  if (!sc) die("No logged-in Seller Central tab found. Run launch-chrome-debug.sh and sign in, then retry.");
  const origin = new URL(sc.url).origin;

  for (const job of jobs) {
    if (job.report === "sqp") await runSqpJob(origin, job, args);
    else { const doc = await runFetch(origin + job.pageUrl, job.needMetaTag, job.call); emit(doc, job.out, args.verbose, job.desc); }
  }
}

main().catch((e) => die(e.message));
