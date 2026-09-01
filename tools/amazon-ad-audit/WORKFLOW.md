# Account Audit: End-to-End Workflow

The current agent owns this workflow end to end. The config is the input contract; nothing in the code is client-specific.

## Capability model

- **Connected/internal browser:** downloads Amazon exports to the contract paths and captures evidence and caveats.
- **DataDive MCP:** pulls the niche, competitors, and rank inputs.
- **Local build and writing:** runs the builder, writes the narrative, validates, and renders.
- **Google Drive integration:** completes authorized internal delivery.

The active agent uses every available capability and continues through the full run. If one capability is unavailable, hand off only that checklist and the exact contract paths to any capable agent.

## Steps

1. **Scope**: client, marketplace(s), product lines + ASINs, break-even ACOS (assumption vs confirmed margin), brand + competitor tokens. Scaffold `config.<client>-<market>.json` (see `NEW-CLIENT.md`).

2. **Preflight**: `build_audit.py --config <cfg> --preflight`. Emits capability-based checklists for missing inputs, or READY.

3. **Gather browser inputs** (per the emitted checklist):
   - **Ads bulk `.xlsx`**: Amazon Ads console → Bulk Operations → download a Spend/Sales report for the window (SP required; SB/SB-Multi/SD/RAS sheets included if running). Download via the Chrome extension or the CDP debug Chrome; the file lands in `~/Downloads` and is read from there.
   - **Business Report `.csv`**: Seller Central → Reports → Business Reports → Detail Page Sales & Traffic by Child ASIN, for the window. You can also fetch it without the manual download through `tools/report-fetcher/`; see the `amazon-reporting` skill.
   - **Multi-ASIN SQP `.csv`** (one per product group): Brand Analytics → Search Query Performance → multi-ASIN export, weekly, for the product line's ASINs. The multi-ASIN tool caps the query grid, so SV totals are a floor. For full data, export per single ASIN. You can also fetch one uncapped file per ASIN through `tools/report-fetcher/`.
   - **Recommended extras (optional, won't block READY):** SB campaign placement report (the bulk's SB placement rows are incomplete) and the SP Search-Term Impression-Share report (ToS headroom). **Not needed:** SB/SD search-term reports. SB is intent-split by target from the bulk itself.
   - Save each to the exact `inputs{}` path and note evidence plus any caveats.

4. **Pull DataDive**: via MCP (`get_niche_keywords`, `get_niche_competitors` on the `datadive_niche`), save to the `datadive_niche_json` / `datadive_competitors_json` paths. Re-run `--preflight` until READY and continue in the same run.

5. **Build**: `build_audit.py --config <cfg>`. Runs analyze → audit workbook → SQP workbook → master → **standard figure set** (`build_figures.py`) → narrative scaffold (which references the figures that were produced). Figures are guarded: a missing input skips the chart, never fails the build. Needs matplotlib; without it the build warns and carries on.

6. **QA**: `--validate` gates: Branded+Generic+Competitor spend reconciles to total; no ACOS ratio >1.0 colored green (the historical bug); master tab count correct; narrative numbers trace to `metrics.json`.

7. **Data completeness**: the build prints a DATA COMPLETENESS panel and `--validate` prints soft WARNINGS: intent-split coverage <90%, SQP-revenue gap >20% (with the uncovered groups), missing channels, multi-parent ad groups. These are not gate failures. They indicate thin data. For each, either download the missing report and rerun or **disclose it in the deliverable's Method Notes** (for example, "SQP genuinely absent in Brand Analytics for X. Capture figures are floors.").

8. **Narrative**: write the prose and the combined **Problems and Solutions** section into the pre-filled scaffold per `skills/amazon-audit/references/audit-workflow.md` and `writing-and-delivery.md`. Keep lean (no 30-day plan, "what can be reached", or "bottom line" unless config flags them). For an approved `evidence_hybrid` pilot, capture candidates with `capture_audit_evidence.mjs`; the selector targets 6-8, rejects SQP/workbook images, and inserts only screenshots tied to a named finding.

9. **Brand render**: the build produces a branded **A4 / Inter** DOCX intermediate (`render_branded.py`): light body, Signal-Orange accent, KPI cards from metrics, page-break hygiene, full black lockup in every content-page header, and a text-only footer with `page X of Y`. **Cover page only for first-time audits** (`branding.first_time` / `--cover` / `--no-cover`). One-time per machine: `prepare_brand_assets.py` populates the gitignored `brand/` assets; without them it falls back to plain `md_to_docx`.

10. **Deliver**: convert the master workbook to a native Google Sheet and the branded intermediate to a native Google Doc. For a deep audit, immediately apply the revision-controlled request batch from `native_doc_normalize.py`. Read the Doc back and confirm a zero-margin full-page A4 cover, no cover furniture, a next-page body section, and right-edge content headers. Inspect every page directly in the native Doc for logo proportions, page totals, clipping, overlap, and reflow. The native files are the only deliverables. Do not create a PDF unless the operator explicitly requests one. Confirm with the operator before a prospect sees it. The agent owns the Doc up to first delivery; after that a human owns it and re-rendering over it is not allowed.

## Notes

- **Break-even ACOS is an assumption** until margin is confirmed; every red/amber verdict updates on the real number (single config constant → rebuild).
- **SB double-count guard:** Sponsored Brands campaigns appear in two bulk sheets (legacy + SB-Multi); the analyzer dedupes them by Campaign ID into one SB channel. Always sanity-check total ad spend/sales against the Ads console. The spend-reconciliation gate checks internal consistency only and won't flag a double-count.
- **Branded split** is computed from the Search Term Report (what customers typed), not keyword text. A branded Broad keyword serves generic queries.
- **DataDive** is read-only via the local MCP; do not commit the API key or client config JSONs (gitignored).
- Outputs live under `output/<client-slug>/reporting/` (gitignored); deliverables go to Google Drive only.
