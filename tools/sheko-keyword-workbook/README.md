# Sheko DE Kollagen — Keyword Workbook Builder

Reusable, deterministic builder for the Sheko keyword-research workbook. Turns
raw **DataDive** + **Amazon Product Opportunity Explorer (POE)** exports into a
finished `.xlsx`, preserving the Google-Sheet template's style and structure.

## What it does

| Tab | Production | Source |
|---|---|---|
| `1. Root Keywords` | **Exact paste** (never transformed) | DataDive roots CSV |
| `3.1. Master List DataDive` | **Exact paste** | DataDive master keywords CSV |
| `POE Raw - Products` | **Exact paste** | POE Products CSV |
| `POE Raw - Search Terms` | **Exact paste** | POE Search Terms CSV |
| `POE Raw - Related Niches` | **Rebuild + strict filter** | related-niches JSON |
| `Outlier - Opportunity KWs` | **Rebuild** (triage + Final Action) | master CSV |
| `4.1 SEO Text` | **Rebuild** (curated rewrite + DataDive Ranking Juice column) | `seo_content.json` |
| `POE Raw - Reviews` | **Rebuild or warning row** | POE Customer Review Insights JSON |
| `POE Raw - Returns` | **Rebuild or explicit not-exposed row** | POE Returns JSON |
| `POE Semantic Insights` | **Rebuild compact summary** | POE overview/search/reviews/returns/related niches |
| `ASINs`, `2 Never KWs`, `4.2 Competitors` | **Clear for new product/market unless current curated data is supplied** | current sources only |
| `5. Campaign Structure`, `3.2. Root Long-Tails DataDive` | **Skipped / carried blank unless requested** | template `.xlsx` |

Style preservation is by construction: the existing workbook is loaded as the
styled base, so column widths, freeze panes, tab colors, fonts, number formats,
and all non-target tabs stay structurally intact. Source-driven and
product-specific tabs are rewritten or cleared with warning rows, re-applying
captured cell styles. Never carry POE reviews, returns, ASINs, competitors, or
semantic insights from another product, language, or marketplace.

## Product anchor (locked in `config.json`)

- Client **Sheko** / account **Allmedica** / marketplace **Germany**
- Product **SHEKO Premium Kollagen Pulver 450g** — ASIN **B0D1G28XR5**
- DataDive niche `m6202AaAgV`, POE niche `collagen pulver`

## Strict related-niche filter

Only the 9 relevant related niches are written. Known POE drift (`Glow25`-driven
`glow` niches plus skincare / perfume / teeth-whitening / toys / lights /
filament) is dropped. The keep-list and exclude examples live in
`config.json → related_niche_filter`. Validation fails if any excluded example
survives or a non-keep-list niche slips in.

## Outlier triage + Final Action

Rule-based classification over the master list (rules in
`config.json → triage`). Categories: `Semantic opportunity`,
`Competitor/brand term`, `Wrong product form`, `Unsupported claim/health-risk`,
`Negative candidate`, `Ignore` (Ignore = not written; it's a normal master
term). Each outlier gets a **Final Action** from
`{Use in copy, Backend only, A+ only, PPC only, Negative, Ignore}`
(`config.json → final_action`).

> The triage is a deterministic **starting point** a human refines — token
> lists are conservative and editable in `config.json`. It does not overwrite
> the curated `2 Never KWs` negatives tab.

## POE evidence tabs

For new-market runs, configure `poe_reviews_json`, `poe_returns_json`, and
`poe_structured_json`.

The builder parses current POE Customer Review Insights into `POE Raw -
Reviews`. If the Returns route is captured but Amazon does not expose a returns
table for that niche, the builder writes an explicit `Returns not exposed for
this POE niche` row. `POE Semantic Insights` is rebuilt from current POE
overview, search terms, reviews, returns status, and related niches. Configure
`stale_data_guard` to fail validation if known terms from another product leak
into the guarded tabs.

## SEO Text rewrite + Ranking Juice

The `4.1 SEO Text` tab is rebuilt from `seo_content.json` (hand-curated title,
bullets, description, backend terms, semantic/Alexa direction, compliance
notes). It adds a **DataDive Ranking Juice** column showing each element's
current vs optimized-target score.

The Ranking Juice figures are a **manual snapshot** from the DataDive MCP
(`get_ranking_juice`, niche `m6202AaAgV`) — the builder cannot call the MCP, so
refresh `seo_content.json → ranking_juice_snapshot` and the per-row `rj` strings
when DataDive re-researches the niche. The current snapshot (2026-06-06) shows
the bullets (2,364 → 62,874) and description (0 → 85,067) as the biggest gaps;
the title is already strong. Health claims are stripped to stay within EU
Reg. 1924/2006 (no authorized collagen health claims).

## Run

```bash
# from repo root, using the project .venv (openpyxl installed)
.venv/bin/python tools/sheko-keyword-workbook/build_keyword_workbook.py
```

Defaults target the 2026-06-10 cycle. Override any path with flags
(`--template`, `--out`, `--roots-csv`, `--related-niches-json`, …; see
`--help`). Re-run next cycle by pointing the flags at the new exports and, if
curation changed, an updated template.

Exit code `0` = all validations passed, `1` = a validation failed,
`2` = a source file was missing.

## Outputs

- Workbook → `output/sheko/seo/Sheko DE Kollagen Powder Keyword Research <date> v3.xlsx`
- Manifest → `output/sheko/seo/<date>_sheko_keyword_research_v3_summary.json`
  (row counts, source paths, kept/dropped niches, triage breakdown,
  validation results, warnings)

The builder **does not write to Google Drive**. Review the local workbook, then
copy it to the Sheko Drive folder.

## Validations (all must pass)

1. Product anchor is still ASIN `B0D1G28XR5` (config + master header + ASINs tab)
2. `1. Root Keywords` row count == roots CSV
3. `3.1. Master List DataDive` row count == master CSV
4. All sheet names Excel/Google-Sheets compatible (≤31 chars, no `[]:*?/\`, unique)
5. Related-niche filter excludes the known drift examples
6. `POE Raw - Products` / `POE Raw - Search Terms` row counts == their CSVs
7. Every emitted Final Action is in the allowed enum
