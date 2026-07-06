---
name: amazon-opportunity-explorer
description: Use for Amazon Product Opportunity Explorer (OEI/POE) workflows, Niche Scout exports, product opportunity analysis, image strategy from OEI data, product development strategy from OEI data, and connecting Opportunity Explorer insights to Amazon SEO, Rufus/Alexa AI semantic strategy, image text, and listing differentiation.
---

# Amazon Opportunity Explorer

Use this specialist skill when the task involves Amazon Product Opportunity Explorer, OEI/POE data, Niche Scout exports, category/niche insights, product opportunity analysis, image strategy, product development ideas, or visual/listing strategy from customer review and returns data.

## Source Order

1. Knowledge-base skill references for Ecom Wizards methodology:
   - `<your-knowledge-base>/Skills/amazon-image-strategy.md`
   - `<your-knowledge-base>/Skills/oei-product-strategy.md`
   - `<your-knowledge-base>/Skills/rufus-optimization.md`
   - `<your-knowledge-base>/Skills/amazon-seo-writer.md`
   - `<your-knowledge-base>/Skills/direct-response-copywriter.md` when image text or persuasive angles matter
2. Amazon Seller Help for current Product Opportunity Explorer access, report/export behavior, and Seller Central constraints.
3. MAG SOPs for practical Seller Central navigation and screenshots when useful.

## Extraction Tool

Use the repo-native API-first downloader (house pattern of `tools/report-fetcher/`):

- Browser-side fetcher: `tools/opportunity-explorer/fetch-poe.js` — same-origin GraphQL; ONE `fetchPoeNiche` call returns every niche-detail tab (overview, Products, Search Terms, Customer Review Insights positive+negative with snippets, Returns, Insights & Trends series); `fetchPoeSearch` returns the keyword-search / related-niches grid.
- Local formatter: `tools/opportunity-explorer/format-poe.mjs` (`--self-test`) — EN-canonical builder-ready CSVs + sentiment-labeled CRI, Returns, overview, related-niches JSON.
- One-command CDP runner: `tools/opportunity-explorer/run-poe.mjs` (shares the report-fetcher debug Chrome; `--marketplace` verified against the session).
- API contract + verification: `tools/opportunity-explorer/references/poe-endpoints.md`, `poe-gap-matrix.md`.

Default model: API-first. Codex evaluates `fetch-poe.js` in the already logged-in internal-browser Seller Central page (path A); terminal agents use `run-poe.mjs` (path B). Both produce identical files. The legacy DOM extractor (`extract-opportunity-explorer.js` + `format-opportunity-explorer-export.mjs`) is a DEPRECATED fallback only.

The Chrome extension package is not part of the intended workflow once the script is tested. Keep the pCloud extension only as historical/source reference during transition.

Original extension/source backup remains available in pCloud if needed. This is the operator's current local placeholder path, not a repo dependency:

`<your-pcloud>/Account shares/Amazon Wizards/2_Company/2.7_Tools/Chrome Extension-Opportunity Explorer Downloader`

The operator confirmed ownership and backend clearance for reusing the previous extension logic. Use the extractor only through the logged-in connected browser Seller Central session. Do not inspect cookies, session storage, local storage, tokens, or credentials.

## Workflow

1. Confirm account, marketplace, product/niche/category, and intended output: image strategy, product strategy, SEO/Alexa AI strategy, or combined opportunity brief.
2. Search local Amazon docs and MAG SOPs for the current Product Opportunity Explorer path if browser navigation is needed.
3. In the connected browser, navigate Seller Central to Product Opportunity Explorer / Opportunity Explorer and verify the selected account and marketplace.
4. Fetch the niche via `fetch-poe.js` (`fetchPoeSearch` to find the nicheId, then `fetchPoeNiche`) in the page context, or run `run-poe.mjs niche --niche-id <id> --marketplace <cc> --client <slug>` from the terminal. Do not require the user to open or click a Chrome extension.
5. Format with `tools/opportunity-explorer/format-poe.mjs` into `output/{client}/opportunity-data/` with dates in filenames, or another operator-approved destination. `{client}` is the normalized lowercase-kebab client slug from `AGENTS.md`, with marketplace in filenames, not folder names.
6. Load only the relevant knowledge-base reference:
   - `amazon-image-strategy` for image set recommendations and creative direction.
   - `oei-product-strategy` for product development, differentiation, and market entry.
   - `rufus-optimization` for Amazon AI search / semantic listing strategy.
7. Trace every recommendation to a specific OEI/POE signal: returns data, negative reviews, positive reviews, success factors, positioning opportunity, seasonal pattern, demographics, search terms, or price architecture.
8. Stop before changing listings, uploading assets, publishing copy, or making account-visible changes.

## Rufus / Alexa AI Naming

The operator noted that Amazon's Rufus AI naming is moving/has moved toward Alexa or Alexa AI. Treat `Rufus`, `Alexa AI`, `Amazon AI search`, and `semantic Amazon search` as related trigger language unless current first-party Amazon docs say otherwise for a specific workflow.

## Outputs

For image strategy, produce:

- 7-8 image recommendations when no other count is specified.
- A data citation for each image.
- Creative direction.
- Three text-angle options per image: trust/proof, emotional/benefit, and problem/solution.

For product strategy, produce:

- Product development approaches.
- Positioning angles.
- Feature innovations tied to return/review signals.
- Listing differentiation ideas.
- Entry strategy, including hero SKU, price point, launch timing, and moat.

For SEO/Alexa AI strategy, produce:

- Semantic noun-phrase themes.
- Customer-intent and question clusters.
- Listing/image/A+ angles connected to OEI evidence.
- Notes for `amazon-seo` follow-up if listing copy should be produced.
