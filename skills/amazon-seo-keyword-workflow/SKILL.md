---
name: amazon-seo-keyword-workflow
description: Use for the end-to-end keyword-research workbook BUILD pipeline: DataDive 30%/1% exports plus POE/OEI evidence in; Never Ever frequency analysis, outlier triage, and validation; styled XLSX workbook out, with Google Drive delivery and the Codex-Claude handoff. For SEO writing, listing re-optimization, or compliance checks use amazon-seo.
---

# Amazon SEO Keyword Workflow

Use this when the operator asks for a full Amazon SEO keyword workbook, not only listing copy.

## Standby Command

`/seo-standby` means the operator is starting a keyword-research workbook flow but the actionable instructions are expected from Claude. Acknowledge standby, load this workflow if needed, and wait. Do not open DataDive, Seller Central, Amazon listings, run the builder, write SEO, create Drive outputs, edit listings, commit/push, or inspect browser credentials/session data until the operator provides Claude's concrete handoff.

When Claude's handoff arrives, Codex's job is to gather the requested browser/UI inputs, save the exact contract paths, report saved paths plus caveats, and stop.

## Load Order

1. Use `amazon-seo` for Amazon SEO writing, semantic/Alexa/Rufus logic, and compliance posture.
2. Use `amazon-opportunity-explorer` for POE/OEI data (API-first `run-poe.mjs` downloader) and evidence.
2a. Use `amazon-listing-capture` to capture live listing copy (title/bullets/link) for the anchor + competitors into the listing-reference JSON; the builder fills the ASINs tab from it.
3. Use the workbook builder: `tools/amazon-seo-keyword-workbook/build_keyword_workbook.py`.
4. Use DataDive references only when terminology or UI behavior matters:
   - `skills/amazon-seo/references/datadive-support/datadive-support-index.md`
   - `skills/amazon-seo/references/datadive-support/datadive-seo-workflow-article-map.md`

## Required Data Inputs

- DataDive roots CSV. **(MCP-generatable — see below.)**
- DataDive Core MKL CSV at `30% Min Rel.`. **(MCP-generatable.)**
- DataDive Expanded MKL CSV at `1% Min Rel.`. **(DOWNLOAD ONLY — not MCP-reproducible.)**
- DataDive competitors CSV or MCP-derived competitor export. **(MCP-generatable.)**
- Ranking Juice snapshot from DataDive MCP in the SEO content JSON.
- POE Products/Search Terms CSVs.
- POE Reviews, Returns, Related Niches, and structured overview JSON.
- Listing reference JSON with product family, ASINs, listing status, title/bullets/description, ingredients, and pack size.

### DataDive: MCP-first (only ONE file needs the browser download)

Generate **roots**, **Core 30% MKL**, and **competitors** from the DataDive MCP — do NOT send Codex to the browser for them. Only the **Expanded 1% MKL** still requires the UI download, because the MCP returns only the ~visible/tracked set (== the 30% view), not the 1% expansion tail. Validated byte-for-data-identical to the UI exports on a validation run (roots 222/222, Core 257/257, 0 mismatches; a full rebuild from the generated CSVs passed all QA gates with identical Ranking-Juice coverage). See [[datadive-mcp-vs-download]].

Procedure (Claude, before the build):
1. Call `get_niche_roots`, `get_niche_keywords`, `get_niche_competitors` for the niche; save each raw JSON response to a file.
2. **Guardrail:** confirm `len(get_niche_keywords.keywords) == get_niche_competitors.numVisibleKeywords` before trusting the Core file. If they diverge, fall back to the UI Core export.
3. Run the generator to write the three contract CSVs:
   ```bash
   .venv/bin/python tools/amazon-seo-keyword-workbook/datadive_mcp_to_csv.py --anchor <ANCHOR> \
     --roots-json <roots.json> --keywords-json <keywords.json> --competitors-json <comps.json> \
     --out-roots "<roots_csv path>" --out-core "<master_csv path>" --out-competitors "<competitors_csv path>"
   ```
Notes: the Core file's `Sugg. bid & range` column is left blank (the builder never reads it; it only matters for PPC builds). `--preflight` marks these three as `(MCP)` rather than `(CODEX)`, so the Codex task only asks for the Expanded 1% MKL + POE + listing capture.

Record DataDive export metadata for both Core and Expanded MKL: Min Relevancy, Min SV/Max SV if changed, visible keyword count, visible search volume, export timestamp, niche ID, marketplace, and hero keyword. **Capture these at export time, while the grid is on screen** — do not backfill later.

DataDive UI export locations (so Codex doesn't hunt for them):
- **Roots CSV** — the **Roots** grid's leftmost **Export** tab, for **Normalized Root**.
- **Competitors CSV** — **Niche Tracker > Export Competitors**. Prefer the real UI export over MCP fallback. NOTE: the genuine UI export is TRANSPOSED (attribute rows, one column per ASIN) — the builder handles both shapes.
- Core/Expanded MKL — always record Min Rel, visible keyword count, visible search volume, and export timestamp at export time.
- Before fallback or rank injection, confirm the Core MKL has the exact anchor ASIN as a real DataDive column.
- **DataDive export buttons may emit no detectable download event for Codex** (confirmed 2026-06-12). Fallback: the operator clicks the exports manually; Codex maps the files in `~/Downloads` by filename/timestamp/rows/headers (Core 30% includes a `Sugg. bid & range` column; Expanded 1% has far more rows) and reports row counts + headers. Claude then cross-checks the counts against the DataDive MCP niche statistics (`get_niche_competitors` → numVisibleKeywords/totalSvOfVisibleKeywords for 30%, numKeywords/totalSvOfKeywords for 1%) before accepting.
- POE inputs come from the API-first downloader: `tools/opportunity-explorer/run-poe.mjs` (`search` → related-niches JSON; `niche` → Products/SearchTerms CSVs + sentiment-labeled CRI + Returns + overview JSON, all builder-ready and locale-independent). One `.de` login covers every EU marketplace (`--origin https://sellercentral.amazon.de --marketplace de|it|es|fr|…`); US uses the `.com` origin. Whoever has the debug Chrome (Claude via CDP, or Codex via internal-browser evaluate of `fetch-poe.js`) can produce these — no manual tab clicking. Capture context (account, marketplace, niche, last-updated) comes from the overview JSON.
- POE fallback quirks (manual export only): direct tab URLs render header-only — click the in-page tab; the Download click works even when the download event times out — check `~/Downloads` and rename to the contract path.
- After Claude accepts the canonical inputs, Codex deletes duplicate/raw intermediate downloads (never the canonical contract paths).
- Sparse POE Review Insights or Returns routes still get a visible JSON capture plus an explicit caveat.
- Listing capture uses the local-language Amazon path and preserves both requested ASIN and resolved ASIN. Flag same-brand sibling redirects and cross-family edge cases.
- Collagen has no authorized EU health claim; flag skin, hair, nails, joints, bones, wrinkles, anti-age, and elasticity terms in live copy.

**Cross-agent:** Codex captures the browser/UI inputs while Claude writes SEO + builds. Codex waits on Claude's handoff with the **`/seo-standby`** command, then writes to the contract paths and stops.

## Delivery Rule

Keyword-research workbooks are delivered to Google Drive only. Do not copy the final workbook to pCloud. Target Drive folder pattern: `Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/Keyword Research/<Country>/` — one `Keyword Research` folder per client, a sub-folder per country, NOT a folder per run. If the client has only one country, the workbook goes directly in `…/<Client>/Keyword Research/`. New versions replace the old `.xlsx` in place.

## Workbook Rules

- The template workbook is style only.
- No product-specific tab may be carried forward.
- Rebuild every tab from current sources or generate an explicit skipped/not-exposed row.
- Tab names/order must match the canonical `template_keyword_workbook.xlsx` (= the "(Template) Brand-Country-Product Name Keyword Research" Google Sheet). Point `--template` at that clean template, NOT a previous product workbook — mismatched scheme-2 tab names were the root cause of silently-skipped/stale tabs.
- Use `3.1 MKL DataDive 30%` for the Core `30%` MKL.
- Use `2.1 MKL DataDive 1%` for the Expanded `1%` MKL.
- Use the Expanded `1%` MKL to generate `2.2 Never KWs` — a sectioned audit tab: Never-Ever single-word negatives (negative-phrase on the root word), competitor brands (campaign-dependent), claim-risk words, a review-manually near-miss band, and phrase-level negative candidates. Every row carries Category, Why, max SV, max relevancy, and example phrases so a human can justify each negative.
- Keep misspellings/grammar variants out of Never Ever when they still represent relevant product intent.
- Keep competitor/brand terms as PPC/context unless the operator explicitly approves another use — in the Never-KWs tab they live in their own section: negative in rank/SKW campaigns, TARGET in PAT/conquest, never blanket negatives.
- Treat disease, cure, laxative, diagnosis, weight-loss, and unsupported health terms as compliance-risk by default.
- Carry `5. Campaign Structure` forward as the empty PPC scaffold from the canonical template (Rank/Shield SKW waves, Long-Tails, Discovery, PAT Stronger/Weaker, Sum formulas, intent legend) so keywords can be filled in there. Do NOT add it to `generated_blank` — that wipes the scaffold. Only populate the campaigns when PPC is explicitly requested — via `fill_campaign_structure.py` (see Campaign Structure Fill below).

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
- Never KWs tab is sectioned (Never Ever / brands / claim risk / review band / phrase candidates); word rows are single words; every data row has Category + Why populated (validated).
- Every Never Ever row includes frequency, max SV, max relevancy, and example phrases as written columns.
- POE raw tabs match current files.
- POE Reviews/Returns/Semantic tabs are current product/market data.
- Stale terms from another product, language, or marketplace are absent.
- Health-claim risk terms are not pushed into visible copy automatically.
- No competitor brand tokens (`triage.brand_tokens`) in the SEO Text "New Listing" copy (title/bullets/description/backend). Own brand is allowed; the "Notes / Compliance" column is exempt.
- The SEO Text tab carries the post-2026-07-27 title structure: a `Title (≤75 char — required from 2026-07-27)` row (≤75 chars incl. spaces) **and** an `Item Highlights (≤125 char — from 2026-07-27)` row (≤125 chars, searchable), in addition to the current-rules title kept live until 2026-07-27. Notes live in the separate "Notes / Compliance" column (Col D), never mixed into the copy column. See [[amazon-title-75char-2026]].
- `product_facts` block present in config (ingredients + `blend_or_single` + certifications); the builder warns if it is missing and checks completeness when present.
- The ≤75 title **leads with a tracked MKL keyword, not a root** — the title covers at least one Master-List keyword and its lead (non-brand) token exists in the MKL vocabulary. See [[seo-title-ranking-juice-rules]].
- **Ranking-Juice coverage is computed and reported** (covered SV / total + addressable %) in the validation/manifest output — covered SV must be > 0; a warning fires below 60% addressable. No new workbook tab; the human-facing RJ stays in the SEO-content `rj`/compliance columns.
- **Semantic / Alexa AI direction row present and non-empty** — keeps the semantic layer alive alongside Ranking Juice (the dual objective).
- **Compliance tax reported** when `triage.claim_tokens` exist — claim-gated SV vs addressable SV is a validation row, so the RJ cost of compliance is visible instead of silently deflating the addressable %; recover it via the rewrite ladder in `skills/amazon-seo/references/health-claims-compliance.md`.
- **Regulated-category check reminder**: with `compliance.category_tier: "regulated"` and `compliance.checked` false, the builder warns to run `/health-claims-check` before delivery; `compliance.claims_audit` verdict=`prohibited` terms auto-merge into `triage.claim_tokens`.
- Blend guard: if `product_facts.blend_or_single == "blend"`, the title must not lead with a single ingredient name (warning).
- `1. Root Keywords` columns are `Important | Root Keyword | Frequency | Broad Search Volume | Root Score | Category`. The Important column is the AD-TARGETING signal (operator priority): in tiered mode (`root_importance.ad_min_sv`/`ad_min_score` set) roots get ⭐⭐ when score ≥ ad_min_score AND Broad SV ≥ ad_min_sv AND Category is not Brand/Claim/Form/Off-niche — these seed the SKW/rank campaigns; ⭐ marks relevant-but-below-SV-floor roots. Category uses the same triage tokens + core/POE vocabulary as the Never-Ever ladder. Legacy configs (only `min_score`) keep the old binary ⭐.
- Final workbook style is preserved.
- Manifest and Obsidian handoff note are generated.

## Handoff Note Location

Every run gets its **own** handoff/protocol note saved inside that client's Obsidian folder — never appended to one shared cross-client file. Set `inputs.handoff_note` in the config to a per-run path under `…/Projects/Clients/<client>/<date>-<product>-<market>-keyword-workbook-<vN>-handoff.md`. The builder writes the note there and points the preflight Codex block's `Protocol:` line at that same per-run note (falling back to the reusable `…/Context/codex-claude-handoff-protocol.md` only when `handoff_note` is unset).

## Campaign Structure Fill (on request)

Fill the workbook's `5. Campaign Structure` tab from the built workbook's own data. **VISUAL PLAN
ONLY** — the output is the filled tab plus a Proposed Campaign Names block; pasting into the
bulk-creator webapp is the operator's manual step. Never emit campaign bulk files from this flow.

Preconditions: a built, QA-passed workbook; `_local/ads-strategy/strategy.json` + `strategy.md`
present with no `<placeholders>` (copy from `tools/amazon-seo-keyword-workbook/ads-strategy.TEMPLATE.*`).
The strategy files are proprietary and local-only. Claude refreshes them from the Notion playbooks
listed in the strategy.md header when stale; Codex uses them as-is and asks the operator if missing.
Set `campaign_structure.own_brand_tokens` and `product_name_for_naming` in the client config.

Three phases:

```bash
# 1. mechanical extraction (SV bands, brand/never/claim flags, roots, PAT revenue)
.venv/bin/python tools/amazon-seo-keyword-workbook/fill_campaign_structure.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>.json \
  --extract output/<client>/ads/<date>_campaign_candidates.json

# 2. agent judgment (no script): read candidates.json + _local/ads-strategy/strategy.md; assign
#    keywords/ASINs to scaffold slots per the judgment rules (intent tiers/waves, discovery root
#    specificity, halo theming, PAT strength); write classification.json
#    (schema amazon-agent.campaign-classification.v1)

# 3. validate + write (always dry-run first, show the operator, then apply)
.venv/bin/python tools/amazon-seo-keyword-workbook/fill_campaign_structure.py \
  --config ... --workbook <xlsx> --apply <classification.json> --dry-run
.venv/bin/python tools/amazon-seo-keyword-workbook/fill_campaign_structure.py \
  --config ... --workbook <xlsx> --apply <classification.json>   # writes a .bak first
```

Judgment split: the script enforces SV bands, caps, never/claim/form/brand exclusions, same-root
halo, one-root discovery, dedupe, capacity, and generates campaign names from the local naming
template. The agent decides intent tiers (Wave 1/2/3), which roots are specific enough for
Discovery, halo grouping, PAT Stronger/Weaker when revenue is missing, and review-band promotions —
each with a short "why". A FAIL blocks the save; fix the classification, don't fight the validator.
