# Ad/Sales Audit — End-to-End Workflow

Two-agent flow (Codex gathers browser downloads; Claude pulls DataDive, builds, writes). The config is the input contract; nothing in the code is client-specific.

## Roles

- **Codex** (connected/internal browser): downloads the Amazon exports to the contract paths, captures evidence + caveats, then stops. Does NOT run the builder, write the narrative, or edit listings.
- **Claude**: pulls DataDive via MCP, runs the builder, writes the narrative per the playbook, delivers.

## Steps

1. **Scope** — client, marketplace(s), product lines + ASINs, break-even ACOS (assumption vs confirmed margin), brand + competitor tokens. Scaffold `config.<client>-<market>.json` (see `NEW-CLIENT.md`).

2. **Preflight** — `build_audit.py --config <cfg> --preflight`. Emits a copy-ready Codex download task for missing inputs, or READY.

3. **Codex gathers** (per the emitted task):
   - **Ads bulk `.xlsx`** — Amazon Ads console → Bulk Operations → download a Spend/Sales report for the window (SP required; SB/SB-Multi/SD/RAS sheets included if running). File downloads use the @Chrome extension (US VPN) per the Codex download rule.
   - **Business Report `.csv`** — Seller Central → Reports → Business Reports → Detail Page Sales & Traffic by Child ASIN, for the window. (Or fetch it without the manual download: `tools/report-fetcher/` — see the `amazon-reporting` skill.)
   - **Multi-ASIN SQP `.csv`** (one per product group) — Brand Analytics → Search Query Performance → multi-ASIN export, weekly, for the product line's ASINs. (Caveat: the multi-ASIN tool caps the query grid; SV totals are a floor. For full data, export per single ASIN.) (Or fetch via `tools/report-fetcher/` — one ASIN per file gives uncapped SV.)
   - **Recommended extras (optional, won't block READY):** SB campaign placement report (the bulk's SB placement rows are incomplete) and the SP Search-Term Impression-Share report (ToS headroom). **Not needed:** SB/SD search-term reports — SB is intent-split by target from the bulk itself.
   - Save each to the exact `inputs{}` path; note evidence + any caveats; stop.

4. **Claude pulls DataDive** — via MCP (`get_niche_keywords`, `get_niche_competitors` on the `datadive_niche`), save to the `datadive_niche_json` / `datadive_competitors_json` paths. Re-run `--preflight` → READY.

5. **Build** — `build_audit.py --config <cfg>`. Runs analyze → audit workbook → SQP workbook → master → narrative scaffold.

6. **QA** — `--validate` gates: Branded+Generic+Competitor spend reconciles to total; no ACOS ratio >1.0 colored green (the historical bug); master tab count correct; narrative numbers trace to `metrics.json`.

7. **Data completeness** — the build prints a DATA COMPLETENESS panel and `--validate` prints soft WARNINGS: intent-split coverage <90%, SQP-revenue gap >20% (with the uncovered groups), missing channels, multi-parent ad groups. These aren't gate failures — they're thin data. For each: either download the missing report (re-run) or **disclose it in the deliverable's Method Notes** (e.g. "SQP genuinely absent in Brand Analytics for X — capture figures are floors").

8. **Narrative** — write the prose/Problems/Levers into the pre-filled scaffold per `docs/amazon-ad-audit-playbook.md`. Keep lean (no 30-day plan / "what can be reached" / "bottom line" unless config flags them). Reference screenshots inline as `![caption](file.png)`.

9. **Brand render** — the build produces a branded **A4 / Inter** `.docx` + `.pdf` (`render_branded.py`): light body, Signal-Orange accent, KPI cards from metrics, page-break hygiene. **Cover page only for first-time audits** (`branding.first_time` / `--cover` / `--no-cover`). One-time per machine: `prepare_brand_assets.py` populates the gitignored `brand/` assets; without them it falls back to plain `md_to_docx`.

10. **Deliver** — master `.xlsx` + branded `.docx` **+ `.pdf`** to `delivery.drive_folder`. The A4 `.docx` edits in Google Docs (don't convert to a native gdoc — it breaks the cover/cards). Confirm with the operator before a prospect sees it.

## Notes

- **Break-even ACOS is an assumption** until margin is confirmed; every red/amber verdict updates on the real number (single config constant → rebuild).
- **SB double-count guard:** Sponsored Brands campaigns appear in two bulk sheets (legacy + SB-Multi); the analyzer dedupes them by Campaign ID into one SB channel. Always sanity-check total ad spend/sales against the Ads console — the spend-reconciliation gate checks internal consistency only and won't flag a double-count.
- **Branded split** is computed from the Search Term Report (what customers typed), not keyword text — a branded Broad keyword serves generic queries.
- **DataDive** is read-only via the local MCP; do not commit the API key or client config JSONs (gitignored).
- Outputs live under `output/<client-slug>/reporting/` (gitignored); deliverables go to Google Drive only.
