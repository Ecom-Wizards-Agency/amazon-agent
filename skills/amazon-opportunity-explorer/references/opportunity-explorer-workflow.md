# Opportunity Explorer Workflow

Use this reference for Product Opportunity Explorer / OEI / POE workflows that feed image strategy, product strategy, Amazon SEO, and Amazon AI search strategy.

## Extraction Tool

Use the repo-native API-first downloader when an export is needed: one `getNiche` call returns every niche-detail tab (overview, Products, Search Terms, Customer Review Insights positive+negative with snippets, Returns, trends); the keyword search returns the related-niches grid:

- `tools/opportunity-explorer/fetch-poe.js` (browser-side, same-origin GraphQL; window.amazonAgentFetchPoe*)
- `tools/opportunity-explorer/format-poe.mjs` (local formatter, `--self-test`)
- `tools/opportunity-explorer/run-poe.mjs` (one-command CDP runner; shares the report-fetcher debug Chrome)
- Contract + verification: `tools/opportunity-explorer/references/poe-endpoints.md`, `poe-gap-matrix.md`
- Deprecated DOM-scraping fallback: `extract-opportunity-explorer.js` + `format-opportunity-explorer-export.mjs`

Original Chrome extension/source backup, as a local placeholder path:

`<your-pcloud>/Account shares/Amazon Wizards/2_Company/2.7_Tools/Chrome Extension-Opportunity Explorer Downloader`

The operator confirmed ownership and backend clearance for reusing the previous extension logic. The extension path is a historical/source reference only, not a repo dependency. The extension is not part of the intended workflow once the script is tested. Do not inspect cookies, session storage, local storage, tokens, or credentials while extracting OEI/POE data.

## Script-First Operating Model

The normal workflow should not require a Chrome extension or manual extension clicks.

The current agent should:

1. Confirm the logged-in Seller Central session shows the requested account and marketplace.
2. Run `tools/opportunity-explorer/run-poe.mjs` (`search` to find the niche, then `niche --niche-id <id>`) with `--marketplace` and `--client`. It verifies the account, fetches through the same-origin API and formats the result.
3. Without shell access to the CDP runner, evaluate `tools/opportunity-explorer/fetch-poe.js` in a Product Opportunity Explorer page and pass the returned JSON from memory to `tools/opportunity-explorer/format-poe.mjs --stdin --client <slug>`.
4. Use the deprecated DOM extractor (`extract-opportunity-explorer.js` + `format-opportunity-explorer-export.mjs`) only when both API paths fail, and say so in the operator note.

Keep the original Chrome extension only as historical/source reference. The API-first downloader replaces it.

## Setup Note For Team Members

Team members should clone the GitHub `amazon-agent` repo. No browser extension install is required for the AI workflow.

When an OEI/POE export is needed, the current agent should:

1. Open Product Opportunity Explorer in the connected browser.
2. Run `tools/opportunity-explorer/run-poe.mjs` for the niche, or evaluate `tools/opportunity-explorer/fetch-poe.js` in the page context when the CDP runner is unavailable.
3. Format evaluated `fetch-poe.js` output with `tools/opportunity-explorer/format-poe.mjs --stdin --client <slug>`; `run-poe.mjs` formats its own output.
4. Fall back to the deprecated `tools/opportunity-explorer/extract-opportunity-explorer.js` and `tools/opportunity-explorer/format-opportunity-explorer-export.mjs` only when the API path fails.

## Data To Capture

When extracting OEI/POE data, preserve:

- Account and marketplace.
- Niche title and URL.
- Export date.
- Search volume and growth.
- Brand/product concentration.
- Pricing and price architecture.
- Products and top ASINs when available.
- Search terms.
- Customer review insights.
- Returns data.
- Success factors and positioning opportunities.
- Seasonal patterns.
- Demographics.

## Analysis Routing

Use the exported data with:

- `amazon-listing-images` for Amazon gallery planning, exact copy, and visual direction from supplied product and POE evidence. `amazon-image-strategy` remains a trigger phrase, not a second skill.
- `oei-product-strategy` for product concepts and differentiation.
- `rufus-optimization` for Rufus/Alexa AI semantic search strategy.
- `amazon-seo-writer` when the OEI insights should become listing copy.
- `conversion-offers-and-copy` when image text or Bildtexte need stronger persuasion.

## Stop Points

Stop before:

- Saving or publishing live listing changes.
- Uploading product images or A+ content.
- Changing catalog data.
- Sharing client-facing recommendations without the operator approval when the analysis is speculative.
- Modifying the extractor scripts unless the operator explicitly approves that work for the specific change.
