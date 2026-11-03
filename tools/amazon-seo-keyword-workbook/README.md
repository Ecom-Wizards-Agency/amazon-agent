# Amazon SEO Keyword Workbook Builder

Reusable builder for Amazon SEO keyword workbooks from SoldScope keyword research and Amazon Product Opportunity Explorer sources. Configs and CSVs from earlier DataDive runs still build.

**Client-agnostic.** Nothing is product-specific. Every run is driven by a per-client config. To start a new client/product/market, copy `config.TEMPLATE.json` and follow `NEW-CLIENT.md`. Any local `config.<client>.json` files are just worked examples (gitignored), not the tool's identity.

The workbook template is used only as a style source. Every product-specific tab is rebuilt from current files or generated as an explicit skipped/not-exposed tab.

## Required Sources

- Keyword CSVs from `tools/soldscope/keywords.py`: `roots.csv`, `core.csv` (Core, relevancy 0.30 or more), `expanded.csv` (the complete pool, relevancy 0.01 or more, at the `expanded_mkl_csv` contract path) and `competitors.csv`. Relevancy is normalized to 0-1.
- `research.json` and `keywords-receipt.json` from the same run, for the run metadata.
- Optional per-row keyword ranking score notes (`rj`) in the SEO content JSON.
- POE Products and Search Terms CSVs.
- POE Reviews, Returns, Related Niches, and structured overview JSON.
- Listing reference JSON with ASINs, product family, listing status, pack size, ingredients, and current copy.

## Tab Production

| Tab | Production |
|---|---|
| `ASINs` | Rebuilt from product anchor, listing reference, and competitors |
| `1. Root Keywords` | Exact paste from the roots CSV |
| `2.1 MKL SoldScope 1%` | Exact paste from the complete pool (`expanded.csv`) |
| `2.2 Never KWs` | Generated from the pool's single-word frequency |
| `3.1 MKL SoldScope 30%` | Exact paste from Core (`core.csv`) |
| `3.2 Outlier KWs` | Rebuilt from Core, competitor gaps, POE signals, and triage rules |
| `4. SEO Text` | Rebuilt from SEO content JSON, plus the calculated keyword ranking score row |
| `4.2 Competitors` | Exact paste from current competitors CSV |
| `POE Raw - Products` | Exact paste from POE Products CSV |
| `POE Raw - Search Terms` | Exact paste from POE Search Terms CSV |
| `POE Raw - Reviews` | Parsed from current POE Review Insights JSON |
| `POE Raw - Returns` | Parsed from POE Returns JSON or explicit not-exposed row |
| `POE Raw - Related Niches` | Rebuilt from related-niches JSON with keep/drop filter |
| `POE Semantic Insights` | Rebuilt from POE overview, search terms, reviews, returns, and related niches |
| `5. Campaign Structure` | Carried forward as the empty PPC scaffold; filled only on a PPC request |

The template names its two MKL tabs `3.1 MKL DataDive 30%` and `2.1 MKL DataDive 1%`. `tabs.template_renames` in `config.TEMPLATE.json` renames them to the SoldScope names before the build, and every other tab key in the config uses the template's own sheet names, so no stray tab is created. Legacy DataDive configs have no renames and keep the DataDive tab names and labels (`keyword_source` defaults to `DataDive`). The builder also accepts the older names `2 Never KWs`, `Outlier - Opportunity KWs` and `4.1 SEO Text`; Excel does not allow `/` in sheet names, so `Outlier - Opportunity KWs` is the workbook-safe version of `Outlier / Opportunity KWs`.

## Run

Make the keyword CSVs first. Save every `keyword_research_get_multi_results` page of the SoldScope search, then run `tools/soldscope/keywords.py --pages <pages> --out-dir <run dir> --anchor <ASIN> --asins <ASIN,...> --marketplace <US> --search-id <id>`; the full procedure and the CLI are in `tools/soldscope/README.md`. SoldScope calls that spend credits need one run approval naming the ASINs, marketplace and expected credits; rank-tracker writes need exact-action approval (`tools/soldscope/README.md`).

```bash
cd "<repo-root>"
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>.json
```

Use `--preflight` first. Missing inputs are reported with exact expected paths.

## Keyword Run Metadata

Each config records the run for both Core (`keyword_exports.core_mkl`) and the pool (`keyword_exports.expanded_mkl`), copied from `research.json` and `keywords-receipt.json`:

- `search_id`, `asins`, `marketplace`
- `date_from`, `date_to`
- `raw_rows`, `kept_rows`
- `core_min`, `pool_min` (normalized relevancy, 0-1)
- `relevancy_mode`

The run identity also goes in `product_anchor.research` (`asins`, `marketplace`, `search_id`, `date_from`, `date_to`).

Legacy configs keep `datadive_exports` with the DataDive UI fields (Min Relevancy, visible keyword count, visible search volume, export timestamp, niche ID, marketplace, hero keyword) and `product_anchor.datadive_niche`; the builder reads both. A group passes when every field of either set is filled. Placeholder values such as `TO_RECORD_*` or `<...>` fail validation.

## Never Ever Logic

The `2.2 Never KWs` tab is generated from the complete pool (`expanded.csv`).

The builder tokenizes keywords into single words, calculates frequency, and adds context:

- example keywords
- max search volume
- average/max relevancy
- whether the word appears in Core MKL
- whether it appears in POE terms
- whether it appears in product/listing/ingredient language

Only one-word rows classified as `Never Ever` are written to the final tab. Misspellings and grammar variants stay out of Never Ever when they still represent relevant product intent.

## Keyword Ranking Score

`ranking_score.py` calculates our local equivalent of DataDive's Ranking Juice (title x3 + bullets x2 + description x1, incremental credit per field, tiered phrase matching) from any keyword list with search volume. Client-visible cells call it the keyword ranking score, never Ranking Juice. Method and calibration: `skills/amazon-seo/references/seo-writing-methodology.md` section 2.

```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/ranking_score.py \
  --keywords <core.csv | legacy get_niche_keywords.json> \
  [--listing <listing-reference.json>] [--seo-content <seo_content.json>] \
  [--compare-datadive <get_ranking_juice.json>] [--weights '{"title":3,"bullets":2,"description":1}'] \
  [--highlights-field title|bullets|description|none] [--json]
```

- `--keywords`: a Core MKL CSV in the builder format, such as `core.csv` from `tools/soldscope/keywords.py` (optional blank leading column; `Search Terms` and `SV` columns found by name, falling back to columns 2 and 3 like the builder), or a saved legacy DataDive `get_niche_keywords` JSON. Every row is scored with its own SV, including variants that tokenize identically.
- `--listing`: listing-reference or listing-capture JSON (`{"listings": [{"asin", "title", "bullets", "description"}]}`); one row per ASIN.
- `--seo-content`: scores the New Listing copy as `Draft` (Title + Item Highlights + Bullet 1-5 + Description, first line of each cell).
- `--compare-datadive` (legacy): prints ours vs a saved DataDive `get_ranking_juice` JSON per ASIN with the title and total ratios and both rank orders. Use it only to re-check the calibration on old DataDive files.

The builder runs the same score after the SEO Text tab is written. It appends one `Keyword Ranking Score (calculated)` row (draft total, per-field breakdown and % of max, then competitor totals from `listing_reference_json`, highest first, anchor excluded), records draft and competitor scores under `ranking_score` in the manifest, adds the informational validation row `Keyword ranking score computed` (it never fails the build; it shows why when no score was computed), and warns when the draft total is below the competitor median. The keyword list is the Core MKL (`master_csv`). Config, all keys optional:

```json
"ranking_score": {
  "enabled": true,
  "weights": {"title": 3, "bullets": 2, "description": 1},
  "item_highlights_field": "title"
}
```

With `"enabled": false` the build output is unchanged from a build without the feature.

## Outputs

- Styled workbook `.xlsx`
- Manifest JSON
- Optional Drive copy via `--drive-dir`
- Cross-agent handoff note, always. It goes to the shared team vault's `Clients/<Client>/Handoffs/` when that vault is reachable and the client has a folder there, otherwise next to the workbook. Set `inputs.handoff_note` to override. Point the builder at the vault with the `AMAZON_AGENT_TEAM_VAULT` env var or a `_local/team-vault-path.txt` holding the vault root.
