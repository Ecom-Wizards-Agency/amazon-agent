# Amazon SEO Keyword Workbook Workflow

## 1. Gather DataDive Exports

From the DataDive UI, export:

- roots CSV
- Core MKL CSV at `30% Min Rel.`
- Expanded MKL CSV at `1% Min Rel.`
- competitors CSV, or create a MCP-derived competitor CSV fallback

Record export metadata in the config for both MKLs before building.

Use DataDive MCP for:

- Ranking Juice snapshot
- competitor sanity checks
- keyword distribution sanity checks
- outlier/opportunity context

## 2. Gather POE/OEI Evidence

Use Chrome/Seller Central and the `amazon-opportunity-explorer` skill.

Capture:

- POE Products CSV
- POE Search Terms CSV
- Customer Review Insights JSON
- Returns JSON or not-exposed evidence
- Related Niches JSON
- structured overview JSON
- screenshots/evidence

Never inspect cookies, local storage, session storage, tokens, or credentials.

## 3. Capture Listing Reference

Save listing evidence as JSON:

- product family confirmation
- parent/child ASINs
- listing status
- title, bullets, description
- ingredients/composition
- serving size and pack size
- health-claim caveats

Stop if the ASIN resolves to the wrong product family.

## 4. Preflight

```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/<config>.json --preflight
```

If the `1%` Expanded MKL is missing, do not substitute the `30%` file. Export the `1%` file from DataDive.

## 5. Build And QA

Run the builder and require all validations to pass:

- Core MKL rows match the `30%` CSV
- Expanded MKL rows match the `1%` CSV
- Core/Expanded paths are distinct
- DataDive metadata is complete
- Never Ever rows are one-word `Never Ever` rows only
- POE rows match current sources
- stale product/language/market terms are absent
- health-claim risk terms are not pushed into visible copy automatically

## 6. Deliver

Copy the QA-passed `.xlsx` to the client Drive folder. Keep the `.xlsx` as the canonical workbook. Native Google Sheets copies are shareable views only.

The build also writes:

- manifest JSON
- Obsidian handoff note
- copy-ready Claude/Codex prompt
