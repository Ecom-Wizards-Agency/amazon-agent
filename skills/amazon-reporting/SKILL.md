---
name: amazon-reporting
description: Use for fetching and formatting Amazon reports (`/fetch-reports`): Seller Central Business Reports, SQP, SCP, Ads reports, search term reports, bulk downloads, period comparisons, and Excel/CSV workbook outputs. Not for audit narratives: route full ad/sales audits to `amazon-ad-audit` or `amazon-adlabs-audit`.
---

# Amazon Reporting

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

## Fetch reports without manual download (Business Reports + SQP)

`tools/report-fetcher/` pulls Business Reports (Detail Page Sales & Traffic) and Search Query Performance straight from Seller Central's own report APIs in the connected/internal browser: no clicking through the UI, no manual CSV download. The output CSVs match the exact headers `build_sqp_workbook.py` and `analyze_audit.py` read, so they satisfy the ad-audit preflight's Business-Report + SQP CODEX tasks directly.

Preconditions: connected/internal browser (never headless) on a logged-in `sellercentral.amazon.*` tab; correct account + marketplace confirmed via the browser checkpoint; for SQP, a Brand Analytics page (so the `anti-csrftoken-a2z` meta tag is present).

Reports: `sqp` (Search Query Performance), `business` (Detail Sales & Traffic), `scp` (Brand Catalog Performance), `tst` (Top Search Terms), `all`. Slash command: `/fetch-reports`. Canonical copy-paste prompt: `tools/report-fetcher/CODEX-PROMPT.md`.

Hands-off (preferred; needs Chrome on the debug port; an agent with shell/`@computer` runs and troubleshoots it). Copy-paste path: fill a per-client config once (`config.TEMPLATE.json` → `config.<client>.json`, gitignored), then a fixed command:

```bash
tools/report-fetcher/launch-chrome-debug.sh        # one-time; dedicated debug Chrome; log into Seller Central in it
node tools/report-fetcher/run.mjs doctor           # verify connection + that the profile is signed in
node tools/report-fetcher/run.mjs all --config tools/report-fetcher/config.<client>.json --plan
node tools/report-fetcher/run.mjs all --config tools/report-fetcher/config.<client>.json --verbose
```

Or explicit flags: `run.mjs sqp --asins B0..,B0.. --weeks YYYY-MM-DD --range weekly|monthly|quarterly --out ... [--split]`; `business --start .. --end .. --out ...`; `scp`/`tst --weeks .. --out ...`. SQP fetches one ASIN per call (uncapped SV) and writes one combined file per group (or `--split` per ASIN). `--verbose` captures `<out>.raw.json` + column ids for troubleshooting; `--plan` prints the plan without fetching. Full options in `tools/report-fetcher/README.md`.

Manual fallback (no debug port): `evaluate` the source of `fetch-seller-reports.js` in a logged-in tab, call `fetchSqp`/`fetchBusinessReport`/`fetchScp`/`fetchTst`, save the JSON, then `node tools/report-fetcher/format-seller-reports.mjs <json> <out.csv>`.

Then point the consumer config at the CSV: SQP → `inputs.sqp_csvs["<group>"]` (one file per ASIN group; one ASIN per file for uncapped SV); Business → `inputs.business_report_csv`.

Rules: read-only (report reads only); reads only the page's own anti-CSRF meta tag, never cookies/passwords/session storage/tokens (see the Safety Rules carve-out in `AGENTS.md`); ~5 s between requests. If there is no active session or the evaluate can't fire, land nothing and ask the operator to open/refresh the tab. Never fabricate rows. Runs under whichever agent drives the browser (Codex internal browser or Claude connected Chrome).
