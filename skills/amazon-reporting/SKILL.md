---
name: amazon-reporting
description: Use for Amazon reporting and analytics: Seller Central reports, Amazon Ads reports, SQP, SCP, business reports, search term reports, bulk downloads, period comparisons, dashboards, and Excel/CSV workbook outputs.
---

# Amazon Reporting

## Source Order

1. Knowledge-base analytics skill references for workbook logic:
   - `<your-knowledge-base>/Skills/amazon-sqp-intelligence-suite.md`
   - `<your-knowledge-base>/Skills/amazon-yoy-analysis.md`

   Note: these knowledge-base skill files are a user-specific local reference and may not exist at the `Code/knowledge-base` path. The operator's current local copies live in an Obsidian vault: `<your-vault>/Skills/` (e.g. `amazon-sqp-intelligence-suite.md`, `amazon-yoy-analysis.md`). This path is user-specific — team members should point to their own local knowledge-base/Obsidian copy. Do not commit the vault to GitHub. This is a reference source only, not a "check Obsidian for everything" rule.
2. Amazon Seller Help or Advertising Help After Login for current report definitions, locations, filters, and download behavior.
3. MAG SOPs for practical report generation steps.

## Workflow

1. Confirm account, marketplace, report type, date range, entity level, and destination folder.
2. Search official docs for report definitions/current UI.
3. Use internal analytics references for workbook generation and interpretation.
4. Save deliverables under `output/{client}/reporting/` with dates in filenames unless the user specifies pCloud/Drive. `{client}` is the normalized lowercase-kebab client slug from `AGENTS.md`, with marketplace in filenames, not folder names.
5. Stop before creating scheduled reports, changing report settings, or downloading sensitive reports to an unclear destination.

## Fetch reports without manual download (Business Reports + SQP)

`tools/report-fetcher/` pulls Business Reports (Detail Page Sales & Traffic) and Search Query Performance straight from Seller Central's own report APIs in the connected/internal browser — no clicking through the UI, no manual CSV download. The output CSVs match the exact headers `build_sqp_workbook.py` and `analyze_audit.py` read, so they satisfy the ad-audit preflight's Business-Report + SQP CODEX tasks directly.

Preconditions: connected/internal browser (never headless) on a logged-in `sellercentral.amazon.*` tab; correct account + marketplace confirmed via the browser checkpoint; for SQP, a Brand Analytics page (so the `anti-csrftoken-a2z` meta tag is present).

Sequence (details + params in `tools/report-fetcher/README.md`):

1. `evaluate` the source of `tools/report-fetcher/fetch-seller-reports.js`, then call `fetchSqp({asins, marketplace, reportingRange, periodEndDates})` or `fetchBusinessReport({legacyReportId, granularity, startDate, endDate, asins?})`. Save the returned JSON.
2. `node tools/report-fetcher/format-seller-reports.mjs <json> output/{client}/reporting/<file>.csv`.
3. Point the consumer config at it: SQP → `inputs.sqp_csvs["<group>"]` (one file per ASIN group; one ASIN per file for uncapped SV); Business → `inputs.business_report_csv`.

Rules: read-only (report reads only); reads only the page's own anti-CSRF meta tag, never cookies/passwords/session storage/tokens (see the Safety Rules carve-out in `AGENTS.md`); ~5 s between requests. If there is no active session or the evaluate can't fire, land nothing and ask the operator to open/refresh the tab — never fabricate rows. Runs under whichever agent drives the browser (Codex internal browser or Claude connected Chrome).
