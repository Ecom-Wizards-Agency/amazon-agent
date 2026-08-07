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
 *          --account <merchant-id> (pin the SELLER when the login holds several; default is
 *                                   inherited from your Seller Central tab, NOT the session default)
 *          --origin https://sellercentral.amazon.<tld> (force the region; normally derived from
 *                                   --marketplace via MARKET_HOSTS)
 * The runner starts/reuses the dedicated headless Chrome automatically. The
 * operator signs in once through launch-chrome-debug.sh --mode recovery.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { ensureChrome, listPages, createPage, closePage, evaluate, Session } from "./cdp.mjs";
import { format } from "./format-seller-reports.mjs";

const HERE = dirname(fileURLToPath(import.meta.url));
const FETCH_SRC = readFileSync(join(HERE, "fetch-seller-reports.js"), "utf8");
const LEGACY = { child: "102:DetailSalesTrafficByChildItem", parent: "102:DetailSalesTrafficByParentItem",
  sku: "102:DetailSalesTrafficBySKU", date: "102:SalesTrafficTimeSeries" };

// Which Seller Central host serves each marketplace, in preference order. A seller signs into
// ONE host per region and reaches every marketplace in it, so the fallbacks are the regional
// siblings: one .de login covers DE/IT/ES/FR/NL/SE/PL/BE/IE/TR/UK, one .com login covers
// US/CA/MX/BR. AU, JP, SG, IN, AE, SA, EG, ZA are their own logins with no sibling.
// Used to pick the RIGHT tab when the debug Chrome has several regions open. Without this the
// runner took whichever Seller Central tab came first, so `--marketplace au` could fetch from
// the US origin (or vice versa) and label the file with the wrong country.
const EU = ["sellercentral.amazon.de", "sellercentral.amazon.co.uk", "sellercentral.amazon.fr",
  "sellercentral.amazon.it", "sellercentral.amazon.es", "sellercentral.amazon.nl",
  "sellercentral.amazon.se", "sellercentral.amazon.pl", "sellercentral.amazon.com.be",
  "sellercentral.amazon.ie", "sellercentral.amazon.com.tr"];
const NA = ["sellercentral.amazon.com", "sellercentral.amazon.ca", "sellercentral.amazon.com.mx",
  "sellercentral.amazon.com.br"];
const first = (host, siblings) => [host, ...siblings.filter((h) => h !== host)];
const MARKET_HOSTS = {
  us: first("sellercentral.amazon.com", NA), ca: first("sellercentral.amazon.ca", NA),
  mx: first("sellercentral.amazon.com.mx", NA), br: first("sellercentral.amazon.com.br", NA),
  uk: first("sellercentral.amazon.co.uk", EU), gb: first("sellercentral.amazon.co.uk", EU),
  de: first("sellercentral.amazon.de", EU), fr: first("sellercentral.amazon.fr", EU),
  it: first("sellercentral.amazon.it", EU), es: first("sellercentral.amazon.es", EU),
  nl: first("sellercentral.amazon.nl", EU), se: first("sellercentral.amazon.se", EU),
  pl: first("sellercentral.amazon.pl", EU), be: first("sellercentral.amazon.com.be", EU),
  ie: first("sellercentral.amazon.ie", EU), tr: first("sellercentral.amazon.com.tr", EU),
  au: ["sellercentral.amazon.com.au"], jp: ["sellercentral.amazon.co.jp"],
  sg: ["sellercentral.amazon.sg"], in: ["sellercentral.amazon.in"],
  ae: ["sellercentral.amazon.ae"], sa: ["sellercentral.amazon.sa"],
  eg: ["sellercentral.amazon.eg"], za: ["sellercentral.amazon.co.za"],
};

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
  if (doc.report === "file") {             // inventory/listing report: raw file, no reformatting
    ensureDir(outPath); writeFileSync(outPath, doc.text || "");
    const lines = (doc.text || "").split("\n").filter((l) => l.trim()).length;
    console.log(`OK — ${outPath} (${Math.max(0, lines - 1)} rows) · ${desc} · ${doc.filename || ""}`);
    return;
  }
  const csv = format(doc);                 // throws + lists columns if a required one is unmapped
  ensureDir(outPath); writeFileSync(outPath, csv);
  const rows = csv.split("\n").filter((l) => l.trim()).length - 1;
  console.log(`OK — ${outPath} (${rows} rows) · ${desc}`);
  if (doc.truncated) console.log(`   NOTE: ${doc.note}`);
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
    if (args["max-pages"] || c.max_pages) p.maxPages = Number(args["max-pages"] || c.max_pages);
    const fn = report === "scp" ? "fetchScp" : "fetchTst";
    jobs.push({ report, out, range, weeks, pageUrl: `/brand-analytics/dashboard/${report === "scp" ? "brand-catalog-performance" : "top-search-terms"}`,
      needMetaTag: true, call: `${fn}(${JSON.stringify(p)})`, desc: `${report.toUpperCase()} ${range} ${weeks.join(",")}` });
  } else if (report === "inventory") {
    const c = cfgFor("inventory");
    const rtype = args["report-type"] || c.report_type || "";
    const ext = args.out && /\.\w+$/.test(args.out) ? "" : ".txt";
    const out = args.out || c.out || join(c.out_dir || "output/<client>/reporting/", `inventory${ext}`);
    const p = rtype ? { reportType: rtype } : {};
    jobs.push({ report, out, pageUrl: "/listing/reports/ref=xx_invreport_favb_xx", needMetaTag: false,
      call: `fetchInventoryReport(${JSON.stringify(p)})`, desc: `Inventory report${rtype ? " " + rtype : ""}` });
  } else if (report === "business") {
    const c = cfgFor("business_report");
    const start = args.start || c.start_date, end = args.end || c.end_date;
    if (!start || !end) die("business needs --start and --end (or start_date/end_date in config)");
    // `--report child|parent|sku` is the documented flag; report_variant/variant are older
    // aliases. Before this, `--report parent` was read by none of them and silently fell back
    // to the CHILD report, so a "parent" pull returned child rows under a parent filename.
    const variant = args.report || args.report_variant || args.variant || c.report_variant || "child";
    if (!LEGACY[variant]) die(`unknown --report "${variant}" — expected one of: ${Object.keys(LEGACY).join(", ")}`);
    const legacy = LEGACY[variant] || c.legacy_report_id || LEGACY.child;
    const asins = list(args.asins || c.asins);
    const out = args.out || c.out || join(c.out_dir || "output/<client>/reporting/", `business_${start}.csv`);
    const p = { legacyReportId: legacy, asins, startDate: start, endDate: end };
    jobs.push({ report, out, pageUrl: "/business-reports/ref=xx_sitemetric_favb_xx", needMetaTag: false,
      call: `fetchBusinessReport(${JSON.stringify(p)})`, desc: `Business ${legacy} ${start}..${end}` + (asins.length ? ` asins=${asins.join(",")}` : " (all)") });
  } else die(`unknown report: ${report}`);
  return jobs;
}

// Seller Central carries the SELECTED SELLER ACCOUNT in `mons_sel_*` query params, not in
// the origin. The runner opens its own tab, so without these it lands on whatever account is
// the session default — silently returning another client's numbers. Inherit them from the
// operator's logged-in tab (or force one with --account <merchant-id>).
// Carry the SELLER identity only (`mons_sel_dir_*`). Deliberately NOT `mons_sel_mkid`: which
// marketplace's data comes back is already set by the `marketplace` field in the report payload,
// and inheriting a tab's mkid would silently override it (a .de tab left on DE would return DE
// numbers for a `--marketplace it` run). Host routing picks the region; the payload picks the
// marketplace; these params only pick the account.
function accountParamsFrom(url) {
  const out = new URLSearchParams();
  try {
    for (const [k, v] of new URL(url).searchParams) if (k.startsWith("mons_sel_dir_")) out.set(k, v);
  } catch {}
  return out;
}

// Best-effort read of the seller display name from a Seller Central tab, so the operator (or
// Codex) can eyeball WHICH CLIENT a pull belongs to instead of decoding a merchant id. Mirrors
// the account-safety pattern in ../opportunity-explorer/run-poe.mjs.
const ACCT_NAME_JS = `(function(){
  var sels = ['[data-test="current-account"]','.dropdown-account-switcher-header',
              '[data-testid*="account-switcher" i]','[id*="account-switcher" i]',
              '[class*="partner-switcher" i]','[data-testid*="partner-switcher" i]',
              '#sc-mkt-picker-switcher-select','[aria-label*="account" i][role="button"]'];
  for (var i=0;i<sels.length;i++){
    var el=document.querySelector(sels[i]);
    var t=el&&(el.innerText||el.textContent||'').trim();
    if(t) return t.split('\\n').map(function(x){return x.trim();}).filter(Boolean).slice(0,2).join(' / ');
  }
  return null;
})()`;

async function readAccountName(page) {
  if (!page || !page.webSocketDebuggerUrl) return null;
  let s;
  try { s = await Session.open(page.webSocketDebuggerUrl); return await evaluate(s, ACCT_NAME_JS); }
  catch { return null; }
  finally { if (s) s.close(); }
}

function withAccount(url, params) {
  if (!params || [...params.keys()].length === 0) return url;
  const u = new URL(url);
  for (const [k, v] of params) if (!u.searchParams.has(k)) u.searchParams.set(k, v);
  return u.toString();
}

async function runSqpJob(origin, job, args, acct) {
  const p = { asins: job.asins, marketplace: (args.marketplace || "us").toLowerCase(), reportingRange: job.range, periodEndDates: job.weeks };
  const doc = await runFetch(withAccount(origin + job.pageUrl, acct), true, `fetchSqp(${JSON.stringify(p)})`);
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
    const v = await ensureChrome();
    console.log("Chrome:", v.Browser, "| debug port reachable");
    const sc = (await listPages()).filter((p) => /sellercentral\.amazon\./.test(p.url || ""));
    if (!sc.length) { console.log("Seller Central: no logged-in tab. Run tools/report-fetcher/launch-chrome-debug.sh --mode recovery, sign in, then return it to headless mode with tools/report-fetcher/launch-chrome-debug.sh."); process.exit(1); }
    const s = await Session.open(sc[0].webSocketDebuggerUrl);
    let st;
    try {
      st = await evaluate(s, `(function(){return {signin:/signin|ap\\/signin|authportal|\\/account-picker|\\/ax\\//i.test(location.href)||/sign[- ]?in/i.test(document.title)};})()`);
    } finally { s.close(); }
    console.log(`Seller Central: ${sc.length} tab(s)`);
    for (const p of sc) {
      let host = "?", mcid = null;
      try { const u = new URL(p.url); host = u.host; mcid = u.searchParams.get("mons_sel_dir_mcid"); } catch {}
      const serves = Object.entries(MARKET_HOSTS).filter(([, hs]) => hs[0] === host).map(([m]) => m.toUpperCase());
      const name = await readAccountName(p);
      console.log(`  - ${host}${serves.length ? ` (${serves.join("/")})` : ""} → ${name || "(name unresolved)"} · ${mcid || "NO account param (session default)"}`);
    }
    if (sc.length > 1) console.log("  Note: more than one region/account is open. The runner picks the tab matching --marketplace; pass --account <merchant-id> to pin the seller.");
    if (st && !st.signin) { console.log("Login: OK — session is active. Ready to fetch."); process.exit(0); }
    console.log("Login: NOT signed in. Sign into Seller Central in the debug window, then re-run doctor.");
    process.exit(1);
  }

  const reports = args._ === "all" ? ["sqp", "business", "scp", "tst", "inventory"].filter((r) => cfg && (cfg[r] || cfg[r === "business" ? "business_report" : r])) : [args._];
  if (!reports.length || !["sqp", "scp", "tst", "business", "inventory"].includes(reports[0]))
    die("usage: run.mjs <sqp|scp|tst|business|inventory|all|doctor> [--config <cfg>] [flags] — see the header of run.mjs");

  const jobs = reports.flatMap((r) => buildJobs(r, cfg, args, mp));

  if (args.plan) {
    console.log("PLAN (nothing fetched):");
    for (const j of jobs) {
      if (j.report === "sqp") console.log(`  SQP  ${j.group}: ${j.asins.length} ASIN(s) × ${j.weeks.length} ${j.range} period(s) → ${j.split ? j.stem + "_<asin>.csv (split)" : j.stem + ".csv (combined)"}`);
      else console.log(`  ${j.report.toUpperCase()}  → ${j.out}   (${j.desc})`);
    }
    process.exit(0);
  }

  await ensureChrome();
  // Region: pass --origin (e.g. https://sellercentral.amazon.de) to force it — needed
  // when the debug Chrome has tabs from more than one region (US .com vs EU .de). One
  // EU login (.de) covers DE/IT/ES/FR/NL/... via --marketplace; US uses .com.
  const forced = args.origin || (cfg && cfg.origin);
  const pages = await listPages();
  const hostOf = (p) => { try { return new URL(p.url).host; } catch { return ""; } };
  let origin;
  if (forced) {
    origin = new URL(forced).origin;
    if (!pages.some((p) => (p.url || "").startsWith(origin))) die(`No debug-Chrome tab on ${origin}. Open Seller Central there (signed in) and retry.`);
  } else {
    const scTabs = pages.filter((p) => /sellercentral\.amazon\./.test(p.url || ""));
    if (!scTabs.length) die("No logged-in Seller Central tab found. Run tools/report-fetcher/launch-chrome-debug.sh --mode recovery, sign in, then return it to headless mode with tools/report-fetcher/launch-chrome-debug.sh.");
    // Pick the tab whose HOST actually serves the requested marketplace, in preference order.
    // Never just take the first Seller Central tab: with .com and .com.au both open that is a
    // coin flip, and the wrong one returns another country's (or another seller's) numbers.
    const wanted = MARKET_HOSTS[mp];
    if (!wanted) die(`Unknown --marketplace "${mp}". Known: ${Object.keys(MARKET_HOSTS).join(", ")}. Or force the region with --origin https://sellercentral.amazon.<tld>`);
    const match = wanted.map((h) => scTabs.find((p) => hostOf(p) === h)).find(Boolean);
    if (!match) die(`No debug-Chrome tab serves --marketplace ${mp}. Expected one of: ${wanted.join(", ")}. Open Seller Central on that host (signed in) and retry.\n  Tabs currently open: ${[...new Set(scTabs.map(hostOf))].join(", ")}`);
    origin = new URL(match.url).origin;
    const others = [...new Set(scTabs.map(hostOf))].filter((h) => h !== hostOf(match));
    console.log(`Region: ${new URL(origin).host} for --marketplace ${mp}${others.length ? ` (ignoring other open host(s): ${others.join(", ")})` : ""}`);
  }

  // Account context. Prefer a tab on this origin that actually carries a selected account;
  // otherwise we would inherit the session default and quietly audit the wrong seller.
  const onOrigin = pages.filter((p) => (p.url || "").startsWith(origin));
  const acct = accountParamsFrom((onOrigin.find((p) => /[?&]mons_sel_dir_mcid=/.test(p.url || "")) || onOrigin[0] || {}).url || "");
  // OBSERVED identity = what the operator's tab actually is, read BEFORE we force anything.
  // The gate below must judge against this, never against a value we supplied ourselves.
  const observedMcid = acct.get("mons_sel_dir_mcid") || null;
  const forcedAcct = args.account || (cfg && cfg.account);
  if (forcedAcct) acct.set("mons_sel_dir_mcid", forcedAcct);
  const mcid = acct.get("mons_sel_dir_mcid");
  const acctName = await readAccountName(onOrigin.find((p) => /[?&]mons_sel_dir_mcid=/.test(p.url || "")) || onOrigin[0]);
  const acctLabel = [acctName, mcid].filter(Boolean).join(" · ") || "(unresolved)";
  if (mcid) console.log(`Account: ${acctLabel}${forcedAcct ? " (forced via --account)" : " (inherited from your Seller Central tab)"}`);
  else console.log(`Account: ${acctLabel} — NO account param detected, falling back to the session DEFAULT seller. If this login holds several sellers the numbers may be another client's. Pass --account <merchant-id> (see: run.mjs doctor).`);

  // Hard gate, same contract as run-poe.mjs --expect-account: abort BEFORE any fetch if the
  // resolved account does not match what the caller expected. Matches the merchant id exactly
  // or the display name case-insensitively as a substring.
  // --account is a HINT, not a guaranteed switch. Seller Central resolves the account
  // server-side; supplying mons_sel_dir_mcid for a seller the session is not already on does
  // NOT reliably switch it, and the returned report can still be the tab's seller. So warn
  // loudly whenever the forced id disagrees with what the tab actually shows.
  if (forcedAcct && observedMcid && forcedAcct !== observedMcid) {
    console.log(`WARNING: --account ${forcedAcct} does not match the account your tab is on (${observedMcid}${acctName ? " / " + acctName : ""}). ` +
      `Seller Central may ignore the override and return the TAB's seller instead. Switch the account in the debug Chrome and re-run rather than trusting this file.`);
  }

  const expect = args["expect-account"] || (cfg && cfg.expect_account);
  if (expect) {
    // Judge ONLY against independently observed identity. Matching against `mcid` would be
    // circular when --account is set: the caller supplies the value and then it validates itself.
    const hit = (observedMcid && (observedMcid === expect || observedMcid.endsWith(expect))) ||
      (acctName && acctName.toLowerCase().includes(String(expect).toLowerCase()));
    if (!hit) die(`--expect-account "${expect}" does NOT match the account actually signed in (${acctName || "unknown"}${observedMcid ? " · " + observedMcid : ""}). Nothing fetched. Switch the account in the debug Chrome and re-run. Note --account alone cannot satisfy this check, by design.`);
    console.log(`Account check: OK — the signed-in account matches --expect-account "${expect}"`);
  }

  for (const job of jobs) {
    if (job.report === "sqp") await runSqpJob(origin, job, args, acct);
    else { const doc = await runFetch(withAccount(origin + job.pageUrl, acct), job.needMetaTag, job.call); emit(doc, job.out, args.verbose, job.desc); }
  }
}

main().catch((e) => die(e.message));
