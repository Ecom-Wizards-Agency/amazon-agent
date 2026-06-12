---
name: amazon-seo-keyword-workflow
description: Use for end-to-end Amazon SEO keyword workbook workflows from DataDive 30%/1% exports, POE/OEI evidence, Never Ever KW frequency analysis, outlier triage, semantic/Alexa SEO, health-claim QA, styled XLSX generation, Drive delivery, and Obsidian/Claude handoff.
---

# Amazon SEO Keyword Workflow

Use this when Victor asks for a full Amazon SEO keyword workbook, not only listing copy.

## Standby Command

`/seo-standby` means Victor is starting a keyword-research workbook flow but the actionable instructions are expected from Claude. Acknowledge standby, load this workflow if needed, and wait. Do not open DataDive, Seller Central, Amazon listings, run the builder, write SEO, create Drive outputs, edit listings, commit/push, or inspect browser credentials/session data until Victor provides Claude's concrete handoff.

When Claude's handoff arrives, Codex's job is to gather the requested browser/UI inputs, save the exact contract paths, report saved paths plus caveats, and stop.

## Load Order

1. Use `amazon-seo` for Amazon SEO writing, semantic/Alexa/Rufus logic, and compliance posture.
2. Use `amazon-opportunity-explorer` for POE/OEI scraping and evidence.
2a. Use `amazon-listing-capture` to capture live listing copy (title/bullets/link) for the anchor + competitors into the listing-reference JSON; the builder fills the ASINs tab from it.
3. Use the workbook builder: `tools/amazon-seo-keyword-workbook/build_keyword_workbook.py`.
4. Use DataDive references only when terminology or UI behavior matters:
   - `skills/amazon-seo/references/datadive-support/datadive-support-index.md`
   - `skills/amazon-seo/references/datadive-support/datadive-seo-workflow-article-map.md`

## Required Data Inputs

- DataDive roots CSV.
- DataDive Core MKL CSV at `30% Min Rel.`.
- DataDive Expanded MKL CSV at `1% Min Rel.`.
- DataDive competitors CSV or MCP-derived competitor export.
- Ranking Juice snapshot from DataDive MCP in the SEO content JSON.
- POE Products/Search Terms CSVs.
- POE Reviews, Returns, Related Niches, and structured overview JSON.
- Listing reference JSON with product family, ASINs, listing status, title/bullets/description, ingredients, and pack size.

Record DataDive export metadata for both Core and Expanded MKL: Min Relevancy, Min SV/Max SV if changed, visible keyword count, visible search volume, export timestamp, niche ID, marketplace, and hero keyword. **Capture these at export time, while the grid is on screen** — do not backfill later.

DataDive UI export locations (so Codex doesn't hunt for them):
- **Roots CSV** — the **Roots** grid's leftmost **Export** tab, for **Normalized Root**.
- **Competitors CSV** — **Niche Tracker > Export Competitors**. Prefer the real UI export over MCP fallback. NOTE: the genuine UI export is TRANSPOSED (attribute rows, one column per ASIN) — the builder handles both shapes.
- Core/Expanded MKL — always record Min Rel, visible keyword count, visible search volume, and export timestamp at export time.
- Before fallback or rank injection, confirm the Core MKL has the exact anchor ASIN as a real DataDive column.
- **DataDive MKL grid is capped at 500 visible rows** (`numMaxVisibleKeywords`). When the Core 30% grid already saturates the cap, lowering Min Rel to 1% does NOT yield a larger export — the "Expanded 1%" CSV comes back byte-identical to the Core file (verified DE kollagen `m6202AaAgV`, 2026-06-12; Victor confirmed in-UI). The 1% tail is then structurally unavailable from BOTH the UI and the MCP (`get_niche_keywords` returns the same visible 500, with no Outlier rows and no bid column — an equal fallback for the visible grid, never a source of the tail). In that case: do NOT zero "Outliers Max Relevancy" (Outlier-labelled rows feed `3.2 Outlier KWs` and much of Never-Ever) — re-export once with outliers visible, use that file for both MKL tabs, and record the cap as an explicit caveat in `datadive_exports.*.source` + the manifest, cross-checked against the MCP niche stats (`numKeywords` vs `numVisibleKeywords`). The Expanded-1% step only adds rows when the Core grid is under the cap (e.g. IT collagen: 312 → 500).
- **DataDive export buttons may emit no detectable download event for Codex** (confirmed 2026-06-12). Fallback: Victor clicks the exports manually; Codex maps the files in `~/Downloads` by filename/timestamp/rows/headers (Core 30% includes a `Sugg. bid & range` column; Expanded 1% has far more rows) and reports row counts + headers. Claude then cross-checks the counts against the DataDive MCP niche statistics (`get_niche_competitors` → numVisibleKeywords/totalSvOfVisibleKeywords for 30%, numKeywords/totalSvOfKeywords for 1%) before accepting.
- POE Products is the Niche Details route **`/product`**; POE Search Terms is **`/search-queries`**. Capture visible context: Seller Central account, account country, niche marketplace, niche name, and last-updated date.
- POE quirks: direct tab URLs may render only the tab header — click the in-page tab to load real content. The POE **Download** click works even when the browser download event times out — look for the new file in `~/Downloads` and rename to the contract path. The repo POE script is for JSON/visible-page captures; native CSVs come from the Download button.
- After Claude accepts the canonical inputs, Codex deletes duplicate/raw intermediate downloads (never the canonical contract paths).
- Sparse POE Review Insights or Returns routes still get a visible JSON capture plus an explicit caveat.
- Listing capture uses the local-language Amazon path and preserves both requested ASIN and resolved ASIN. Flag same-brand sibling redirects and cross-family edge cases.
- Collagen has no authorized EU health claim; flag skin, hair, nails, joints, bones, wrinkles, anti-age, and elasticity terms in live copy.

**Cross-agent:** Codex captures the browser/UI inputs while Claude writes SEO + builds. Codex waits on Claude's handoff with the **`/seo-standby`** command, then writes to the contract paths and stops.

## Delivery Rule

Keyword-research workbooks are delivered to Google Drive only. Do not copy the final workbook to pCloud. Target Drive folder pattern: `Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/<Run Folder>/`.

## Workbook Rules

- The template workbook is style only.
- No product-specific tab may be carried forward.
- Rebuild every tab from current sources or generate an explicit skipped/not-exposed row.
- Tab names/order must match the canonical `template_keyword_workbook.xlsx` (= the "(Template) Brand-Country-Product Name Keyword Research" Google Sheet). Point `--template` at that clean template, NOT a previous product workbook — mismatched scheme-2 tab names were the root cause of silently-skipped/stale tabs.
- Use `3.1 MKL DataDive 30%` for the Core `30%` MKL.
- Use `2.1 MKL DataDive 1%` for the Expanded `1%` MKL.
- Use the Expanded `1%` MKL to generate `2.2 Never KWs`.
- Keep misspellings/grammar variants out of Never Ever when they still represent relevant product intent.
- Keep competitor/brand terms as PPC/context unless Victor explicitly approves another use.
- Treat disease, cure, laxative, diagnosis, weight-loss, and unsupported health terms as compliance-risk by default.
- Carry `5. Campaign Structure` forward as the empty PPC scaffold from the canonical template (Rank/Shield SKW waves, Long-Tails, Discovery, PAT Stronger/Weaker, Sum formulas, intent legend) so keywords can be filled in there. Do NOT add it to `generated_blank` — that wipes the scaffold. Only populate the campaigns when PPC is explicitly requested.

## Builder Command

```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json
```

Use `--preflight` first. If a DataDive `1%` export or metadata is missing, stop and ask for that exact source instead of substituting the `30%` file.

## QA Gates

- Core MKL rows match the `30%` CSV.
- Expanded MKL rows match the `1%` CSV.
- Core and Expanded source paths are distinct.
- The Core MKL has the exact anchor ASIN as a real column (verify this BEFORE any fallback/injection). Same-brand sibling ASINs are listed in `asin_roles.siblings` so they are labelled `Sibling` (not `Competitor`) and excluded from opportunity triage; the anchor is never duplicated in the ASINs tab.
- DataDive export metadata is complete and not placeholder text.
- Never Ever tab contains one-word rows classified as `Never Ever`.
- Every Never Ever row includes frequency, relevancy, example keywords, and source.
- POE raw tabs match current files.
- POE Reviews/Returns/Semantic tabs are current product/market data.
- Stale terms from another product, language, or marketplace are absent.
- Health-claim risk terms are not pushed into visible copy automatically.
- No competitor brand tokens (`triage.brand_tokens`) in the SEO Text "New Listing" copy (title/bullets/description/backend). Own brand is allowed; the "Notes / Compliance" column is exempt.
- `1. Root Keywords` columns are `Important | Root Keyword | Frequency | Broad Search Volume | Root Score`; `Important` is auto-marked from the roots CSV's trailing 0–1 score at `root_importance.min_score` (default 0.10, marker ⭐), EXCEPT (a) competitor-brand/number-dominated roots are demoted (`suppress_brand_roots`, default on, derives brand words from `triage.brand_tokens` — e.g. `glow`, `25`, `glow 25`, `25 collagen` are unmarked because every non-generic token is a brand word or a number) and (b) `root_importance.exclude_terms` (explicit low-relevance roots, e.g. `peptide`). `generic_terms` (defaults to `never_ever.relevant_words` + `stop_words`) are the product words that don't count toward brand-domination, so `kollagen pulver` stays marked.
- `4. SEO Text` columns are `Section | Old Listing | New Listing | Notes / Compliance` — the section label, live/old copy, new copy, and compliance/Ranking-Juice notes are each their own column (the brand-token QA gate scans column C, the publishable copy).
- `3.2 Outlier KWs` carries the NATIVE DataDive columns for each opportunity keyword (`Search Terms | SV | Relev. | Sugg. bid & range | <per-niche tracked-ASIN rank columns…>`, dynamic per niche) followed by the triage columns (`POE Signal | Classification | Reason | Recommended Use | Source | Final Action`). The MKL/Outlier ASIN columns are never hardcoded — they come from the niche's DataDive export.
- Final workbook style is preserved.
- Manifest and Obsidian handoff note are generated.

## Handoff Note Location

Every run gets its **own** handoff/protocol note saved inside that client's Obsidian folder — never appended to one shared cross-client file. Set `inputs.handoff_note` in the config to a per-run path under `…/Projects/Clients/<client>/<date>-<product>-<market>-keyword-workbook-<vN>-handoff.md`. The builder writes the note there and points the preflight Codex block's `Protocol:` line at that same per-run note (falling back to the reusable `…/Context/codex-claude-handoff-protocol.md` only when `handoff_note` is unset).
