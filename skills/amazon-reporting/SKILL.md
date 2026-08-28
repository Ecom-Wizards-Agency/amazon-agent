---
name: amazon-reporting
description: "Use for fetching and formatting Amazon reports (`/fetch-reports`): Seller Central Business Reports, SQP, SCP, Ads reports, search term reports, bulk downloads, period comparisons, and Excel/CSV workbook outputs. Not for audit narratives: route full ad/sales audits to `amazon-audit`."
---

# Amazon Reporting

Browser: Mixed (CDP for scripted Seller Central fetches; CDP interactive for Ads Console exports until a dedicated Ads runner is implemented).

## Source Order

1. Knowledge-base analytics skill references for workbook logic:
   - `<your-knowledge-base>/Skills/amazon-sqp-intelligence-suite.md`
   - `<your-knowledge-base>/Skills/amazon-yoy-analysis.md`

   Note: these knowledge-base skill files are a user-specific local reference and may not exist at the `Code/knowledge-base` path. The operator's current local copies live in an Obsidian vault: `<your-vault>/Skills/` (e.g. `amazon-sqp-intelligence-suite.md`, `amazon-yoy-analysis.md`). This path is user-specific; team members should point to their own local knowledge-base/Obsidian copy. Do not commit the vault to GitHub. This is a reference source only, not a "check Obsidian for everything" rule.
2. Amazon Seller Help or Advertising Help After Login for current report definitions, locations, filters, and download behavior.
3. MAG SOPs for practical report generation steps.

## Workflow

1. Confirm account, marketplace, report type, date range, entity level, and destination folder.
2. Search official docs for report definitions/current UI.
3. Use internal analytics references for workbook generation and interpretation.
4. Save deliverables under `output/{client}/reporting/` with dates in filenames unless the user specifies pCloud/Drive. `{client}` is the normalized lowercase-kebab client slug from `AGENTS.md`, with marketplace in filenames, not folder names.
5. Stop before creating scheduled reports, changing report settings, or downloading sensitive reports to an unclear destination.

## Amazon Ads Console exports

For Ads bulk files, Sponsored Products Search Term Impression Share, Sponsored Brands
Campaign Placement, or another report created in the Ads Console, read
`references/ads-console-downloads.md` before acting.

Before creating Ads exports, set the Campaign Manager to the SQP-aligned analysis window
and compare `Total cost` for `All but archived` against `Enabled`. Use that comparison to
decide whether to create a second, smaller Enabled-only bulk file. Keep the broader
Enabled-and-Paused file as the coverage source.

Queue every required Sponsored Ads report near the beginning of the reporting workflow.
Submit the bulk jobs immediately after the cost comparison, then continue other report
work while Amazon generates the files. Refresh and check both report locations every five
minutes until the requested files are ready.

A campaign bulk file is ready only when its Bulk Operations row shows `Success` and
exposes a row-level download link. For a Sponsored Ads report, open the exact report
definition and download the matching `Completed` run from its history. The report list
alone is not completion evidence.

After a bulk download completes, replace Amazon's opaque alphanumeric filename segment
with the verified advertiser name and preserve the original start and end dates. An exact
destination filename supplied by the task takes precedence. Record the original filename
in the evidence note when its job identifier may be useful for traceability.

The 2026-07-30 live feasibility check proved that the shared CDP debug Chrome can:

- open the authenticated Ads Console and verify the visible account and country;
- list existing report definitions and bulk-operation jobs;
- resolve completed authenticated download links;
- save both report and bulk `.xlsx` files without the Chrome extension.

This is feasibility evidence, not a production runner. Until a dedicated Ads CDP runner
is implemented and validated, drive the Ads console interactively over the CDP debug
Chrome for operational Ads report and bulk-export work. Downloads are captured with
`Browser.setDownloadBehavior`, or read from `~/Downloads` after the click.

## Fetch reports without manual download (Business Reports + SQP)

`tools/report-fetcher/` pulls Business Reports (Detail Page Sales & Traffic) and Search Query Performance straight from Seller Central's own report APIs in the connected/internal browser: no clicking through the UI, no manual CSV download. The output CSVs match the exact headers `build_sqp_workbook.py` and `analyze_audit.py` read, so they satisfy the ad-audit preflight's Business-Report and SQP browser inputs directly.

Preconditions: the policy-configured CDP browser on a logged-in `sellercentral.amazon.*` tab; correct account + marketplace confirmed via the browser checkpoint; for SQP, a Brand Analytics page (so the `anti-csrftoken-a2z` meta tag is present). Use the allowlisted broker for login and an explicit attended recovery restart only for a human challenge.

Reports: `sqp` (Search Query Performance), `business` (Detail Sales & Traffic), `scp` (Brand Catalog Performance), `tst` (Top Search Terms), `all`. Slash command: `/fetch-reports`. Canonical copy-paste prompt: `tools/report-fetcher/BROWSER-PROMPT.md`.

Hands-off (preferred; needs Chrome on the debug port; an agent with shell/`@computer` runs and troubleshoots it). Copy-paste path: fill a per-client config once (`config.TEMPLATE.json` → `config.<client>.json`, gitignored), then a fixed command:

```bash
node tools/browserctl/browserctl.mjs ensure --port 9222
node tools/browserctl/browserctl.mjs auth --port 9222 --target <target-id>
node tools/report-fetcher/run.mjs doctor           # connection + login + WHICH SELLER each tab is on
node tools/report-fetcher/run.mjs all --config tools/report-fetcher/config.<client>.json --plan
node tools/report-fetcher/run.mjs all --config tools/report-fetcher/config.<client>.json \
  --expect-account "<Client Name>" --verbose
```

**Account gate (mandatory).** One login can hold several sellers and the debug Chrome can have several
regions open. `doctor` probes every tab live (exit 0 signed in, 1 signed out, 2 INDETERMINATE: retry,
never treat as logged out); confirm the client before trusting a number, and pass
`--expect-account "<Client Name>"` so a wrong-seller pull aborts instead of producing a
correct-looking file. `--account <merchant-id>` is enforced, not a hint: the run dies rather than
falling back to the session default, and with config `account_name` + `marketplace_label` the runner
drives Seller Central's own account picker to the right seller itself. Region is derived from `--marketplace`
(US `.com`, EU `.de` + siblings, AU `.com.au`, ...), not from whichever tab is first. This class of bug is
silent: the file has the right dates, shape and headers, and the wrong company's numbers.

Or explicit flags: `run.mjs sqp --asins B0..,B0.. --weeks YYYY-MM-DD --range weekly|monthly|quarterly --out ... [--split]`; `business --start .. --end .. [--report child|parent|sku] --out ...`; `scp`/`tst --weeks .. --out ...`. **`--weeks` takes the period-END date (weekly = the Saturday).** SQP fetches one ASIN per call (uncapped SV) and writes one combined file per group (or `--split` per ASIN). `--verbose` captures `<out>.raw.json` + column ids for troubleshooting; `--plan` prints the plan without fetching. Full options in `tools/report-fetcher/README.md`.

Manual fallback (no debug port): `evaluate` the source of `fetch-seller-reports.js` in a logged-in tab, call `fetchSqp`/`fetchBusinessReport`/`fetchScp`/`fetchTst`, save the JSON, then `node tools/report-fetcher/format-seller-reports.mjs <json> <out.csv>`.

Then point the consumer config at the CSV: SQP → `inputs.sqp_csvs["<group>"]` (one file per ASIN group; one ASIN per file for uncapped SV); Business → `inputs.business_report_csv`.

Rules: read-only (report reads only); reads only the page's own anti-CSRF meta tag, never cookies/passwords/session storage/tokens (see the Safety Rules carve-out in `AGENTS.md`); ~5 s between requests. If there is no active session or the evaluate can't fire, land nothing and ask the operator to open/refresh the tab. Never fabricate rows. The CDP runner is the default for both agents; the manual evaluate fallback runs under whichever agent drives the browser.
