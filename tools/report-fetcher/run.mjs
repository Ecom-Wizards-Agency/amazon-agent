#!/usr/bin/env node
/*
 * One-command Seller Central report fetch — hands-off, no console paste.
 *
 * Runs the fetch in Chrome's REAL page main world over the DevTools Protocol (CDP),
 * using the operator's existing logged-in session. Any agent with shell access
 * Any agent with shell access can run this; no browser sandbox. Read-only.
 *
 * Copy-paste path (fill a per-client config once, then a fixed command):
 *   node run.mjs sqp      --config config.<client>.json        # every ASIN group
 *   node run.mjs sqp-brand --brand <id> --proxy-asin B0.. --weeks ...
 *   node run.mjs business --config config.<client>.json
 *   node run.mjs scp      --config config.<client>.json
 *   node run.mjs tst      --config config.<client>.json
 *   node run.mjs all      --config config.<client>.json        # every configured report
 *   node run.mjs <any>    --config <cfg> --plan                # show the plan, touch nothing
 *
 * Explicit-flag path:
 *   node run.mjs sqp --asins B0..,B0.. --weeks 2026-06-27 --range weekly|monthly|quarterly \
 *                    --out output/<client>/reporting/sqp.csv [--split]
 *   node run.mjs sqp-brand --brand 123 --proxy-asin B0.. --weeks 2026-06-27 --out ...
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
import { probeTab, doctorVerdict, readIdentity, inspectPage, switchAccount, accountMatches } from "./sc-account.mjs";
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
  } else if (report === "sqp-brand") {
    const c = cfgFor("sqp_brand");
    const range = (args.range || c.reporting_range || "weekly").toLowerCase();
    const weeks = list(args.weeks || args.week).length ? list(args.weeks || args.week) : list(c.period_end_dates);
    if (!weeks.length) die("sqp-brand needs --weeks YYYY-MM-DD (or period_end_dates in config)");
    const brand = args.brand || c.brand;
    if (!brand) die("sqp-brand needs --brand <brand id>");
    const proxyAsin = args["proxy-asin"] || c.proxy_asin || "";
    const out = args.out || c.out || join(c.out_dir || "output/<client>/reporting/", "sqp_brand_proxy.csv");
    const p = { marketplace: mp, reportingRange: range, periodEndDates: weeks,
      brand: String(brand), proxyAsin };
    if (args["max-pages"] || c.max_pages) p.maxPages = Number(args["max-pages"] || c.max_pages);
    jobs.push({ report, out, range, weeks,
      pageUrl: `/brand-analytics/dashboard/query-performance?brand=${encodeURIComponent(brand)}&view-id=query-performance-brands-view`,
      needMetaTag: true, call: `fetchBrandSqp(${JSON.stringify(p)})`,
      desc: `SQP BRAND VIEW proxy ${range} ${weeks.join(",")}${proxyAsin ? " -> " + proxyAsin : ""}` });
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

// Human-readable labels for classifyPage kinds, used in operator-facing messages.
const PAGE_KIND_LABEL = {
  chooser: "the account chooser (no account selected)",
  "sign-in": "a sign-in page",
  "auth-failed": "an authorization-failed page",
  challenge: "a human challenge (captcha/OTP)",
  app: "an authenticated Seller Central page",
  unknown: "an unrecognized page",
};

/*
 * Read the tab's LIVE state: page kind + auth state via one classify probe,
 * then the account identity from the page itself when it is an authenticated
 * non-chooser page. Never throws; failures land in `err`. This replaces the
 * old URL-param + DOM-name guesswork that judged a stale /json/list snapshot.
 */
async function readLiveAccount(tab) {
  const out = { err: null, pageKind: null, authState: null, url: tab.url, identity: null };
  let s;
  try { s = await Session.open(tab.webSocketDebuggerUrl); }
  catch (e) { out.err = `could not attach to the tab (${e.message})`; return out; }
  try {
    let page;
    try { page = await inspectPage(s, { timeoutMs: 8000 }); }
    catch (e) { out.err = `could not inspect the tab (${e.message})`; return out; }
    out.pageKind = page.pageKind;
    out.authState = page.authState;
    out.url = page.facts.url;
    if (page.authState === "authenticated" && page.pageKind !== "chooser") {
      try { out.identity = await readIdentity(s, { timeoutMs: 30000 }); }
      catch (e) { out.identity = { displayName: null, partnerAccountId: null, merchantId: null, marketplace: null, err: e.message }; }
    }
    return out;
  } finally { s.close(); }
}

// Everything observed about the live account, for gate decisions and messages.
// The URL's own mons_sel_dir_mcid is OBSERVED state (it reflects the tab's real
// selection); the value the caller forces via --account never lands here.
function observedOf(live) {
  const id = (live && live.identity) || {};
  let urlMcid = null;
  try { urlMcid = new URL(live.url).searchParams.get("mons_sel_dir_mcid"); } catch {}
  return {
    displayName: id.displayName || null,
    partnerAccountId: id.partnerAccountId || null,
    merchantId: id.merchantId || urlMcid || null,
    urlMcid,
  };
}

function describeLive(live) {
  const parts = [];
  if (live.url) parts.push(`tab: ${live.url}`);
  if (live.pageKind) parts.push(`page: ${PAGE_KIND_LABEL[live.pageKind] || live.pageKind}`);
  const obs = observedOf(live);
  if (obs.displayName) parts.push(`account: ${obs.displayName}`);
  if (obs.merchantId || obs.partnerAccountId) parts.push(`id: ${obs.merchantId || obs.partnerAccountId}`);
  if (live.err) parts.push(live.err);
  else if (live.identity && live.identity.err && !obs.displayName) parts.push(live.identity.err);
  return parts.join(" · ") || "(nothing observable)";
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

/*
 * Connection + login health check. Every Seller Central tab is probed LIVE and
 * in parallel with hard budgets (probeTab), so the output reflects the state
 * at probe time, not a stale /json/list snapshot, and a hung tab costs 20 s,
 * not 125 s. Three-state verdict: OK (exit 0), signed out / human challenge
 * (exit 1), INDETERMINATE with a retry instruction (exit 2). A tab that cannot
 * be probed is never reported as signed out; conflating the two is what
 * produced the false "NOT signed in" verdict of 13.08.2026.
 */
async function doctor() {
  const v = await ensureChrome();
  console.log("Chrome:", v.Browser, "| debug port reachable");
  const sc = (await listPages()).filter((p) => /sellercentral\.amazon\./.test(p.url || ""));
  if (!sc.length) {
    console.log("Seller Central: no tab open. Run tools/report-fetcher/launch-chrome-debug.sh --mode recovery, sign in, then return it to headless mode with tools/report-fetcher/launch-chrome-debug.sh.");
    process.exit(1);
  }
  console.log(`Seller Central: ${sc.length} tab(s), probed live at ${new Date().toISOString()}`);
  const results = await Promise.all(sc.map((p) => probeTab(p)));
  for (const r of results) {
    let host = "?";
    try { host = new URL(r.url).host; } catch {}
    const serves = Object.entries(MARKET_HOSTS).filter(([, hs]) => hs[0] === host).map(([m]) => m.toUpperCase());
    let label;
    if (r.state === "signed-in" && r.pageKind === "chooser") label = "account chooser open, NO account selected";
    else if (r.state === "signed-in" && r.pageKind === "auth-failed") label = "authorization-failed page (authenticated, but this account cannot open that URL)";
    else if (r.state === "signed-in") {
      const id = r.identity || {};
      label = `${id.displayName || "(name unresolved)"} · ${id.merchantId || id.partnerAccountId || (id.err ? `ids unavailable (${id.err})` : "no id")}`;
    } else if (r.state === "signed-out") label = "sign-in page (logged out)";
    else if (r.state === "challenge") label = "human challenge (captcha/OTP)";
    else label = `indeterminate: ${r.reason}`;
    console.log(`  - ${host}${serves.length ? ` (${serves.join("/")})` : ""}${r.stale ? " [stale url from snapshot]" : ""} → ${label}`);
  }
  if (sc.length > 1) console.log("  Note: more than one region/account is open. The runner picks the tab matching --marketplace; pass --account <merchant-id> to pin the seller.");
  const verdict = doctorVerdict(results);
  console.log(verdict.text);
  process.exit(verdict.exitCode);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const mp = (args.marketplace || "us").toLowerCase();
  const cfg = args.config ? JSON.parse(readFileSync(args.config, "utf8")) : null;

  if (args._ === "doctor") return doctor();

  const reports = args._ === "all" ? ["sqp", "business", "scp", "tst", "inventory"].filter((r) => cfg && (cfg[r] || cfg[r === "business" ? "business_report" : r])) : [args._];
  if (!reports.length || !["sqp", "sqp-brand", "scp", "tst", "business", "inventory"].includes(reports[0]))
    die("usage: run.mjs <sqp|sqp-brand|scp|tst|business|inventory|all|doctor> [--config <cfg>] [flags]. See the header of run.mjs");

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
    let match = wanted.map((h) => scTabs.find((p) => hostOf(p) === h)).find(Boolean);
    // No tab on this region yet: open the preferred host ourselves rather than
    // failing. One Seller Central login covers every region the seller is
    // registered in, so a signed-in .com session reaches .de and .com.au too --
    // the tab just has to exist, because host routing above picks by tab.
    // Without this an unattended run dies on any non-US marketplace, which is
    // exactly what happened to JBS DE and Svens Island AU on 11.08.2026.
    if (!match) {
      const host = wanted[0];
      console.log(`Region: no tab serves --marketplace ${mp}; opening https://${host}/home`);
      const opened = await createPage(`https://${host}/home`);
      // Give the fresh tab time to land + settle. Env override exists for tests.
      await new Promise((r) => setTimeout(r, Number(process.env.REPORT_FETCHER_SETTLE_MS || 14000)));
      match = (await listPages()).find((p) => hostOf(p) === host) || opened;
      // A fresh regional tab can land on sign-in if the session does not extend
      // there. Say so plainly instead of fetching an empty report. On failure,
      // close the tab we just created: a leaked sign-in tab becomes another
      // doctor run's first probe target and poisons its verdict.
      const closeOwned = async () => { try { await closePage(opened.targetId); } catch {} };
      const probe = await (async () => {
        let s = null;
        try {
          s = await Session.open(match.webSocketDebuggerUrl);
          return JSON.parse(await evaluate(s, `JSON.stringify({p: !!document.querySelector("input[type=password]"), h: location.host})`, 25000));
        } catch { return null; } finally { if (s) try { s.close(); } catch {} }
      })();
      if (probe && probe.p) { await closeOwned(); die(`Opened https://${host}/home but it shows a sign-in page. Run tools/report-fetcher/launch-chrome-debug.sh --mode recovery, sign in to that region, then return to headless mode.`); }
      if (!match || hostOf(match) !== host) { await closeOwned(); die(`Could not open a Seller Central tab on ${host} for --marketplace ${mp}.`); }
    }
    origin = new URL(match.url).origin;
    const others = [...new Set(scTabs.map(hostOf))].filter((h) => h !== hostOf(match));
    console.log(`Region: ${new URL(origin).host} for --marketplace ${mp}${others.length ? ` (ignoring other open host(s): ${others.join(", ")})` : ""}`);
  }

  // ----- Account resolution: judge the LIVE page, enforce the gates. -----
  // Re-list pages first. The regional branch above may have just opened the
  // tab, and the pre-resolution snapshot cannot contain it; filtering the old
  // snapshot made --expect-account fail with "(unknown)" on every fresh
  // regional tab, and let the chooser page hide behind silent nulls.
  const livePages = await listPages();
  const onOrigin = livePages.filter((p) => (p.url || "").startsWith(origin));
  if (!onOrigin.length) die(`No tab on ${origin} after region resolution. Retry; if it persists, restart the debug Chrome (launch-chrome-debug.sh).`);
  const acctTab = onOrigin.find((p) => /[?&]mons_sel_dir_mcid=/.test(p.url || "")) || onOrigin[0];

  const forcedAcct = args.account || (cfg && cfg.account) || null;
  const accountName = args["account-name"] || (cfg && cfg.account_name) || null;
  const marketplaceLabel = args["marketplace-label"] || (cfg && cfg.marketplace_label) || null;
  const parentAccountName = args["parent-account-name"] || (cfg && cfg.parent_account_name) || null;
  const expect = args["expect-account"] || (cfg && cfg.expect_account) || null;
  const canSwitch = Boolean(accountName && marketplaceLabel);
  const guarded = Boolean(forcedAcct || expect);

  let live = await readLiveAccount(acctTab);
  let switchAttempted = false;
  const attemptSwitch = async () => {
    switchAttempted = true;
    console.log(`Account switch: driving the Seller Central account picker to "${accountName}" / "${marketplaceLabel}"`);
    const s = await Session.open(acctTab.webSocketDebuggerUrl);
    try { await switchAccount(s, origin, { accountName, marketplaceLabel, parentAccountName }); }
    finally { s.close(); }
    live = await readLiveAccount(acctTab);
    console.log(`Account switch: done, the tab now shows ${describeLive(live)}`);
  };

  // Pages that cannot carry a seller context are explicit branches, never silent nulls.
  if (live.pageKind === "sign-in") die(`The ${origin} tab shows a sign-in page. Run tools/report-fetcher/launch-chrome-debug.sh --mode recovery, sign in, return it to headless mode, and re-run. Nothing fetched.`);
  if (live.pageKind === "challenge") die(`The ${origin} tab is blocked by a human challenge (captcha/OTP). Run launch-chrome-debug.sh --mode recovery and complete it. Nothing fetched.`);
  if (live.pageKind === "chooser") {
    if (canSwitch) await attemptSwitch();
    else die(`The ${origin} session sits on the account chooser: NO account is selected, so any fetch would silently use the session default. Pick the account in the debug window, or pass --account-name and --marketplace-label (config: account_name/marketplace_label) so the runner selects it. Nothing fetched. Observed ${describeLive(live)}`);
  }
  if (live.err || live.authState !== "authenticated" || live.pageKind === "chooser") {
    const msg = `Account resolution on ${origin} is not conclusive. Observed ${describeLive(live)}`;
    if (guarded) die(`${msg}. Nothing fetched (fail-closed because --account/--expect-account was requested). Fix the session, or pass account_name/marketplace_label to let the runner switch, then re-run.`);
    console.log(`WARNING: ${msg}. Proceeding because no account guard was requested; the fetch will use whatever seller this session resolves to.`);
  }

  let observed = observedOf(live);

  // --account is ENFORCED. The old behavior treated it as a URL hint, warned on
  // a visible mismatch (and said nothing at all when the tab carried no account
  // param), then proceeded on the session default seller. That silent fallback
  // is how a wrong-account pull happens; it is gone.
  if (forcedAcct) {
    let verifiedBy = null;
    if (accountMatches(observed, forcedAcct)) verifiedBy = `--account ${forcedAcct}`;
    if (!verifiedBy && canSwitch && !switchAttempted) {
      await attemptSwitch();
      observed = observedOf(live);
      if (accountMatches(observed, forcedAcct)) verifiedBy = `--account ${forcedAcct}`;
    }
    // A completed switch is itself verification: switchAccount clicked exactly
    // one account button whose text equals account_name and confirmed leaving
    // the picker, and the re-read display name agrees.
    if (!verifiedBy && switchAttempted && accountName && accountMatches(observed, accountName)) {
      verifiedBy = `the post-switch account name "${accountName}"`;
    }
    // Generic Seller Central pages often cannot serve the merchant id (see
    // readIdentity); a name match against --expect-account still proves the
    // right account is active, and the id keeps riding on the URL as a hint.
    if (!verifiedBy && expect && accountMatches(observed, expect)) {
      verifiedBy = `--expect-account "${expect}" (name match; the --account id itself is not readable on this page)`;
    }
    if (!verifiedBy) {
      die(`--account ${forcedAcct} could not be verified against the live session. Observed ${describeLive(live)}. Nothing fetched. Remedies: pass --account-name and --marketplace-label (config: account_name/marketplace_label) so the runner drives the account switcher; or switch the account in the debug window and re-run; or verify by name with --expect-account.`);
    }
    console.log(`Account: ${observed.displayName || "(name unresolved)"} · ${observed.merchantId || observed.partnerAccountId || forcedAcct} (verified via ${verifiedBy})`);
  } else {
    const label = [observed.displayName, observed.merchantId || observed.partnerAccountId].filter(Boolean).join(" · ");
    if (label) console.log(`Account: ${label} (inherited from the live tab)`);
    else console.log(`Account: UNRESOLVED on an authenticated page. The fetch will use the session DEFAULT seller; if this login holds several sellers the numbers may be another client's. Pass --expect-account "<name or merchant-id>" to make this fail closed (see: run.mjs doctor).`);
  }

  // --expect-account stays fail-closed and judges ONLY observed identity (live
  // page reads + the tab URL's own account param), never a caller-supplied value.
  if (expect) {
    const cands = [observed.displayName, observed.partnerAccountId, observed.merchantId].filter(Boolean);
    if (!cands.length) die(`--expect-account "${expect}" cannot be verified: no account identity was observable. Observed ${describeLive(live)}. Nothing fetched (fail-closed by design). Fix the session and re-run, or run doctor for a live view.`);
    if (!accountMatches(observed, expect)) die(`--expect-account "${expect}" does NOT match the signed-in account. Observed ${describeLive(live)}. Nothing fetched. Switch the account (in the debug window, or via --account-name/--marketplace-label) and re-run. Note --account alone cannot satisfy this check, by design.`);
    console.log(`Account check: OK, the signed-in account matches --expect-account "${expect}"`);
  }

  // URL account params: forced id first, else whatever the live tab carries.
  // This stays a HINT on the report URLs; every judgement above used live reads.
  const acct = accountParamsFrom(live.url || acctTab.url || "");
  if (forcedAcct) acct.set("mons_sel_dir_mcid", forcedAcct);

  for (const job of jobs) {
    if (job.report === "sqp") await runSqpJob(origin, job, args, acct);
    else { const doc = await runFetch(withAccount(origin + job.pageUrl, acct), job.needMetaTag, job.call); emit(doc, job.out, args.verbose, job.desc); }
  }
}

main().catch((e) => die(e.message));
