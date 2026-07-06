# Seller Central Report Fetcher — Business Reports + SQP

Pull **Business Reports** (Detail Page Sales & Traffic) and **Search Query Performance**
(SQP) straight from Seller Central's own report APIs, using the operator's logged-in
session — no clicking through the UI, no manual downloads.

`cdp.mjs` and `launch-chrome-debug.sh` are shared infrastructure: the Opportunity
Explorer downloader (`tools/opportunity-explorer/run-poe.mjs`) uses the same CDP client
and the same debug Chrome/login. Output CSVs drop straight into
the ad-audit pipeline (`build_sqp_workbook.py`, `analyze_audit.py`). Live-reconciled: the
fetched CSVs match the manual Seller Central export to the penny.

## Hands-off (one command, via Chrome's debug protocol)

The runner drives Chrome's REAL page main world over the DevTools Protocol (CDP), so it
uses your existing login — no console paste, no browser-evaluate sandbox. Any agent with
shell access (Codex `@computer`) can run it.

One-time setup — Chrome 136+ ignores `--remote-debugging-port` on your normal profile
(a Chrome security change), so the runner uses a dedicated debug Chrome that runs
**alongside** your normal Chrome. You sign into Seller Central **once** in that window;
the login persists in the debug profile for every future run.

```bash
tools/report-fetcher/launch-chrome-debug.sh      # opens the dedicated debug Chrome (normal Chrome untouched)
# → in that new window, sign into Seller Central once (first run only)
node tools/report-fetcher/run.mjs doctor         # confirms the connection + a logged-in tab
```

Then fetch. **Copy-paste path — fill a per-client config once, then a fixed command** (copy
`config.TEMPLATE.json` → `config.<client>.json`, gitignored, and fill ASIN groups / dates):

```bash
node tools/report-fetcher/run.mjs all --config tools/report-fetcher/config.<client>.json --plan     # show the plan
node tools/report-fetcher/run.mjs all --config tools/report-fetcher/config.<client>.json --verbose  # fetch everything
```

Or explicit flags (no config):

```bash
node tools/report-fetcher/run.mjs sqp --asins <ASIN>,<ASIN> --weeks <YYYY-MM-DD> --range weekly \
  --out output/<client>/reporting/sqp.csv [--split]
node tools/report-fetcher/run.mjs business --start <YYYY-MM-DD> --end <YYYY-MM-DD> \
  --out output/<client>/reporting/business.csv
node tools/report-fetcher/run.mjs scp --weeks <YYYY-MM-DD> --out output/<client>/reporting/scp.csv
node tools/report-fetcher/run.mjs tst --weeks <YYYY-MM-DD> --out output/<client>/reporting/tst.csv
```

Reports: `sqp` (Search Query Performance), `business` (Detail Sales & Traffic), `scp` (Brand
Catalog Performance), `tst` (Top Search Terms), `all` (every report in the config). **TST is
the whole marketplace's search-term ranking (hundreds of thousands of rows)** — unfiltered it
defaults to the top ~500 (5 pages); narrow with `--brand` / `--search-term` / `--asins`, or
raise `--max-pages`, to go deeper.
Options: `--range weekly|monthly|quarterly` (SQP/SCP/TST) · `--weeks a,b` (multiple periods) ·
`--asins a,b` · `--split` (SQP: one file per ASIN instead of one combined file per group) ·
`--report child|parent|sku` (Business) · `--marketplace us` · `--plan` (print the plan,
fetch nothing) · `--verbose` (also writes `<out>.raw.json` + column ids — troubleshoot a
first run). Each SQP ASIN is fetched with a single-ASIN call (uncapped Search Query Volume).
The runner opens its own background tab, writes the CSV, closes the tab; it never disturbs
your other tabs. The canonical copy-paste Codex prompt is in `CODEX-PROMPT.md`.

**Regions (US / EU).** The runner uses whichever region the debug Chrome is signed into
(auto-detected from the logged-in tab) and the `--marketplace` code for the report payload.
For EU, sign the debug Chrome into an EU Seller Central — **one `.de` login covers DE/IT/ES/FR/NL/…**
— and pass the marketplace, e.g. `--marketplace de` (or `it`/`es`/`fr`). US uses `.com` with
`--marketplace us`. If the debug Chrome has tabs from more than one region open, force the
region with `--origin https://sellercentral.amazon.de` (or the config's `origin`). Report
types and column ids are language-independent (matched by id, not the localized label).

First-run troubleshooting (an agent can do this itself): `run.mjs doctor` checks the
connection; `--verbose` captures the raw response + column ids; if the formatter can't map a
column it exits non-zero and lists the source columns it saw (a one-line map tweak in
`format-seller-reports.mjs`).

## Under the hood (also runnable by console paste)

Two parts, following the house pattern (`extract-amazon-listing-copy.js`):

1. `fetch-seller-reports.js` — runs in the page main world on a logged-in
   `sellercentral.amazon.*` tab; returns report JSON. (The runner injects it via CDP; you
   can also paste it into the DevTools console directly.)
2. `format-seller-reports.mjs` — local Node; converts that JSON to the exact CSV headers
   the builders read. `cdp.mjs` + `run.mjs` are the CDP driver + CLI.

## How it works (and why it's safe)

The fetch runs **inside the page origin** via a browser `evaluate`, so it is same-origin:
the browser attaches the existing login cookies, `Origin`, and `Referer` automatically. The
only extra header the Brand-Analytics API needs is `anti-csrftoken-a2z`, read from the
page's OWN `<meta name="anti-csrftoken-a2z">` — the same anti-forgery value the page uses
for its own requests. The script **never** reads cookies, localStorage, sessionStorage,
passwords, or bearer/refresh tokens, and never logs in. Report data is returned to the agent
and sent nowhere else.

- Connected/internal browser only — **never headless** (Amazon blocks bots).
- **Read-only**: these endpoints only read reports; nothing is written or changed.
- **~5 s spacing** between requests (mirrors real usage).
- No session / 403 / missing token → the function returns `{ error }` and the agent stops
  and asks the operator to open/refresh the Brand Analytics tab. It never fabricates data.

Original code. The Seller Central endpoints and parameters are interoperability facts; no
third-party source was copied.

## Run it

Preconditions: the connected browser is on a logged-in `sellercentral.amazon.*` tab, correct
account + marketplace confirmed (the standard browser checkpoint). For SQP, be on a Brand
Analytics page so the `anti-csrftoken-a2z` meta tag is present.

**1. Fetch (in the browser).** Pass the source string + a call (Playwright / Codex path):

```js
// SQP — one product line, two weeks
await tab.playwright.evaluate(`(function(){
  ${fetchSellerReportsSource}
  return fetchSqp({ asins:["B0XXXXXXXX"], marketplace:"US",
                    reportingRange:"weekly", periodEndDates:["2026-06-21","2026-06-28"] });
})()`)

// Business Report — child-ASIN, one month
await tab.playwright.evaluate(`(function(){
  ${fetchSellerReportsSource}
  return fetchBusinessReport({ legacyReportId:"102:DetailSalesTrafficByChildItem",
                               granularity:"MONTH", startDate:"2026-06-01", endDate:"2026-06-30" });
})()`)
```

Or, in an injected/DevTools context: `window.amazonAgentFetchSqp(params)` /
`window.amazonAgentFetchBusinessReport(params)`.

Save the returned object as `<name>.json`.

**2. Format (local).**

```bash
node tools/report-fetcher/format-seller-reports.mjs <name>.json output/<client>/reporting/<file>.csv
```

- SQP → the 12 headers `build_sqp_workbook.py` reads. One file per ASIN group; point the
  ad-audit config `inputs.sqp_csvs["<group>"]` at it.
- Business → the Detail-Page-Sales-&-Traffic headers `analyze_audit.py` reads. Point
  `inputs.business_report_csv` at it.

If a required column can't be matched, the formatter exits non-zero and prints the source
columns it saw — a one-line mapping tweak in `format-seller-reports.mjs`, never a silent
wrong file.

## Self-test

```bash
node tools/report-fetcher/format-seller-reports.mjs --self-test
```

Asserts the emitted headers equal exactly what the consumers read (SQP 12/12 + row parity,
Business headers + row parity), for both label-bearing and bare-id column shapes.

## Notes / limits

- SQP multi-ASIN caveat carries over from the pipeline: request **one ASIN per file** (loop
  `asins`) for uncapped Search-Query-Volume totals; multi-ASIN grids cap the query set.
- Period dates are period-**END** in America/Los_Angeles (weekly = week-ending date).
- Column mapping is by semantic keyword, tolerant of Amazon's exact ids/labels; the first
  live pull should be eyeballed once, then it's stable.
