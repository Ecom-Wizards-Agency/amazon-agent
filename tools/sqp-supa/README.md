# SQP x PPC Weekly Monitor (SUPA-style)

Per-keyword SQP shares (search volume, click share, purchase share) joined
with PPC ad spend + ad sales, per Sunday-Saturday week, per ASIN, with
rule-based flags and an Action Plan tab. The diagnostic this exists for:
"click share fell because ad spend on that keyword quietly fell."

Validated basis: the AdLabs MCP `search_query` entity is byte-identical to
Seller Central SQP (verified 2026-07-08, US 3-way + DE 2-way, 13,248 cells,
0 mismatches). See the sqp-adlabs-sc-parity memory note.

## Workflow (per refresh)

1. **Pull weekly CSVs via the AdLabs MCP** (agent step, no script):
   - SQP: `get_entity_data(search_query)` with a DATE filter per Sunday-Saturday
     week (optionally `PRODUCT_ASIN IN (...)`), then `download_data` and save as
     `downloads/<client>/reporting/sqp_<week-start>.csv`.
   - PPC: `get_entity_data(search_term)` with the same DATE filter, then
     `group_by_column(search_term)`, then `download_data`, saved as
     `downloads/<client>/reporting/search_terms_<week-start>.csv`.
2. **Configure**: copy `config.TEMPLATE.json` to `config.<client>.json`
   (gitignored), list weeks ascending and both input maps.
3. **Build + validate**:
   ```bash
   .venv/bin/python tools/sqp-supa/build_supa_workbook.py \
     --config tools/sqp-supa/config.<client>.json --validate
   ```
4. **Deliver**: copy the XLSX from `output/<client>/reporting/` to the client
   folder on the agency Drive via the desktop mount. MD5-verify local vs Drive.
   It opens directly in Google Sheets.
5. Weekly refresh: append the newest week to `weeks`, add the two new CSVs,
   rebuild. The file name carries the focus-week Saturday.

## Tabs

Dashboard (per-ASIN weekly rollup + flag) · one tab per ASIN (per-keyword
weekly matrix) · Action Plan (ranked, rule-based) · Methods & Sources
(provenance, caps, join caveat, verbatim flag rules).

## Known limits

- SQP = top 100 queries per ASIN per week (Amazon's cap in every source).
  SV totals are floors.
- The PPC join is profile-level. Search terms are campaign-scoped, not
  ASIN-scoped. Never sum ad spend across ASIN tabs.
- Validation gates: exact tab set, week headers, raw-CSV spot checks
  (shares 1e-6, spend $0.01), no >100% ratio with a green fill, plus a soft
  cross-check against AdLabs' own comparison columns.
