---
name: amazon-seo-keyword-workflow
description: Use for end-to-end Amazon SEO keyword workbook workflows from DataDive 30%/1% exports, POE/OEI evidence, Never Ever KW frequency analysis, outlier triage, semantic/Alexa SEO, health-claim QA, styled XLSX generation, Drive delivery, and Obsidian/Claude handoff.
---

# Amazon SEO Keyword Workflow

Use this when Victor asks for a full Amazon SEO keyword workbook, not only listing copy.

## Load Order

1. Use `amazon-seo` for Amazon SEO writing, semantic/Alexa/Rufus logic, and compliance posture.
2. Use `amazon-opportunity-explorer` for POE/OEI scraping and evidence.
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

Record DataDive export metadata for both Core and Expanded MKL: Min Relevancy, Min SV/Max SV if changed, visible keyword count, visible search volume, export timestamp, niche ID, marketplace, and hero keyword.

## Workbook Rules

- The template workbook is style only.
- No product-specific tab may be carried forward.
- Rebuild every tab from current sources or generate an explicit skipped/not-exposed row.
- Use `3.1. Master List DataDive` for the Core `30%` MKL.
- Use `3.2. Expanded MKL 1%` for the Expanded `1%` MKL.
- Use the Expanded `1%` MKL to generate `2 Never KWs`.
- Keep misspellings/grammar variants out of Never Ever when they still represent relevant product intent.
- Keep competitor/brand terms as PPC/context unless Victor explicitly approves another use.
- Treat disease, cure, laxative, diagnosis, weight-loss, and unsupported health terms as compliance-risk by default.
- Keep `5. Campaign Structure` skipped unless PPC is requested.

## Builder Command

```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.sheko-ballastpulver-it.json
```

Use `--preflight` first. If a DataDive `1%` export or metadata is missing, stop and ask for that exact source instead of substituting the `30%` file.

## QA Gates

- Core MKL rows match the `30%` CSV.
- Expanded MKL rows match the `1%` CSV.
- Core and Expanded source paths are distinct.
- DataDive export metadata is complete and not placeholder text.
- Never Ever tab contains one-word rows classified as `Never Ever`.
- Every Never Ever row includes frequency, relevancy, example keywords, and source.
- POE raw tabs match current files.
- POE Reviews/Returns/Semantic tabs are current product/market data.
- Stale terms from another product, language, or marketplace are absent.
- Health-claim risk terms are not pushed into visible copy automatically.
- Final workbook style is preserved.
- Manifest and Obsidian handoff note are generated.
