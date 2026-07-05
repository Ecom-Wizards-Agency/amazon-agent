# Seller Central Report Fetcher — Business Reports + SQP

Pull **Business Reports** (Detail Page Sales & Traffic) and **Search Query Performance**
(SQP) straight from Seller Central's own report APIs, using the operator's logged-in
session — no clicking through the UI, no manual downloads. Output CSVs drop straight into
the ad-audit pipeline (`build_sqp_workbook.py`, `analyze_audit.py`). Live-reconciled: the
fetched CSVs match the manual Seller Central export to the penny.

## Hands-off (one command, via Chrome's debug protocol)

The runner drives Chrome's REAL page main world over the DevTools Protocol (CDP), so it
uses your existing login — no console paste, no browser-evaluate sandbox. Any agent with
shell access (Codex `@computer`) can run it.

One-time setup — launch Chrome with the debug port (uses your normal profile, so the
Seller Central login carries over):

```bash
tools/report-fetcher/launch-chrome-debug.sh     # quit Chrome fully first
node tools/report-fetcher/run.mjs doctor         # confirms the connection + a logged-in tab
```

Then fetch:

```bash
node tools/report-fetcher/run.mjs sqp --asin B0GF8LG5JV --week 2026-06-27 \
  --out output/<client>/reporting/sqp_<asin>.csv
node tools/report-fetcher/run.mjs business --start 2026-06-01 --end 2026-06-30 \
  --out output/<client>/reporting/business.csv
```

Options: `--weeks a,b` (multiple SQP weeks) · `--asins a,b` · `--report child|parent|sku`
(Business) · `--marketplace us` · `--verbose` (also writes `<out>.raw.json` and prints the
column ids — use this to troubleshoot a first run). The runner opens its own temporary tab,
runs the fetch, writes the CSV, and closes the tab; it never disturbs your other tabs.

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
