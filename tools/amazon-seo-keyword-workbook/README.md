# Amazon SEO Keyword Workbook Builder

Reusable builder for Amazon SEO keyword workbooks from DataDive and Amazon Product Opportunity Explorer sources.

**Client-agnostic.** Nothing is product-specific — every run is driven by a per-client config. To start a new client/product/market, copy `config.TEMPLATE.json` and follow `NEW-CLIENT.md`. Any local `config.<client>.json` files are just worked examples (gitignored), not the tool's identity.

The workbook template is used only as a style source. Every product-specific tab is rebuilt from current files or generated as an explicit skipped/not-exposed tab.

## Required Sources

- DataDive roots CSV.
- DataDive Core MKL CSV at `30% Min Rel.`.
- DataDive Expanded MKL CSV at `1% Min Rel.`.
- DataDive competitors CSV or MCP-derived competitor CSV.
- DataDive Ranking Juice snapshot in the SEO content JSON.
- POE Products and Search Terms CSVs.
- POE Reviews, Returns, Related Niches, and structured overview JSON.
- Listing reference JSON with ASINs, product family, listing status, pack size, ingredients, and current copy.

## Tab Production

| Tab | Production |
|---|---|
| `ASINs` | Rebuilt from product anchor, listing reference, and competitors |
| `1. Root Keywords` | Exact paste from DataDive roots CSV |
| `2 Never KWs` | Generated from Expanded MKL `1%` single-word frequency |
| `3.1. Master List DataDive` | Exact paste from Core MKL `30%` |
| `3.2. Expanded MKL 1%` | Exact paste from Expanded MKL `1%` |
| `4.1 SEO Text` | Rebuilt from SEO content JSON and Ranking Juice snapshot |
| `4.2 Competitors` | Exact paste from current competitors CSV |
| `POE Raw - Products` | Exact paste from POE Products CSV |
| `POE Raw - Search Terms` | Exact paste from POE Search Terms CSV |
| `POE Raw - Reviews` | Parsed from current POE Review Insights JSON |
| `POE Raw - Returns` | Parsed from POE Returns JSON or explicit not-exposed row |
| `POE Raw - Related Niches` | Rebuilt from related-niches JSON with keep/drop filter |
| `POE Semantic Insights` | Rebuilt from POE overview, search terms, reviews, returns, and related niches |
| `Outlier - Opportunity KWs` | Rebuilt from Core MKL, competitor gaps, POE signals, and triage rules |
| `5. Campaign Structure` | Generated blank/skipped unless PPC is requested |

Excel does not allow `/` in sheet names, so `Outlier - Opportunity KWs` is the workbook-safe version of `Outlier / Opportunity KWs`.

## Run

```bash
cd "<repo-root>"
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>.json
```

Use `--preflight` first. Missing inputs are reported with exact expected paths.

## DataDive Metadata

Each config must record both Core and Expanded MKL export metadata:

- Min Relevancy
- Min SV / Max SV if changed
- visible keyword count
- visible search volume
- export timestamp
- DataDive niche ID
- marketplace
- hero keyword

Placeholder values such as `TO_RECORD_FROM_DATADIVE_UI` fail validation.

## Never Ever Logic

The `2 Never KWs` tab is generated from the `1%` Expanded MKL.

The builder tokenizes keywords into single words, calculates frequency, and adds context:

- example keywords
- max search volume
- average/max relevancy
- whether the word appears in Core MKL
- whether it appears in POE terms
- whether it appears in product/listing/ingredient language

Only one-word rows classified as `Never Ever` are written to the final tab. Misspellings and grammar variants stay out of Never Ever when they still represent relevant product intent.

## Outputs

- Styled workbook `.xlsx`
- Manifest JSON
- Optional Drive copy via `--drive-dir`
- Obsidian handoff note when `handoff_note` is configured
