---
name: amazon-opportunity-explorer
description: "Discover and score Amazon Product Opportunity Explorer niches, download full POE evidence packs, and turn findings into product, SEO, or creative strategy."
---

# Amazon Opportunity Explorer

Browser: CDP (`run-poe.mjs` over the shared debug Chrome). Fallback: evaluate `fetch-poe.js` in a logged-in Seller Central page.

## Account Safety

POE records viewed niches in the active Seller Central account. Verify account identity before every search, niche, batch, or merchant-niches request.

For client work, pass:

- `--account-name <exact picker label>`
- `--expected-partner-account-id <id>`
- optional `--parent-account-name <agency parent>`
- `--marketplace-label <exact picker label>`
- `--marketplace <cc>`

On mismatch, `run-poe.mjs` opens the account picker, uses trusted CDP clicks to select the configured account and marketplace, reloads POE, and re-reads `partnerAccountId`. It fetches only after the identity matches.

Stop without fetching when the configured account or marketplace is unavailable or ambiguous, the session is logged out, a human challenge appears, or the post-switch identity does not match. Never handle credentials, MFA, CAPTCHA, cookies, or browser storage.

## Extraction Tool

- `tools/opportunity-explorer/fetch-poe.js`: browser-side GraphQL reads.
- `tools/opportunity-explorer/format-poe.mjs`: canonical formatter.
- `tools/opportunity-explorer/run-poe.mjs`: CDP runner with account recovery and marketplace verification.
- `references/poe-niche-export-checklist.md`: full-pack completeness.
- `references/niche-discovery-and-scoring.md`: breadth discovery and scoring.

The legacy DOM extractor is a deprecated fallback only.

## Wide Discovery Standard

When the task asks where demand or ideas exist, do not rely on three convenient niches.

1. Read the latest relevant Google Drive keyword-research workbook and DataDive roots when available.
2. Create 8 to 12 non-branded seeds spanning head term, product form, mechanism, principal uses, and meaningful attributes.
3. Search all seeds. Union and deduplicate related niches by `nicheId` while retaining seed provenance.
4. Exclude wrong-brand, wrong-product, wrong-form, wrong-audience, and wrong-use results with explicit reasons.
5. Download 5 to 10 relevant full niche packs. If fewer than five qualify, download all and record the limitation.
6. Reuse cached POE only when it is at most 14 days old and meets the same coverage contract.
7. Mark insufficient prior captures as superseded in the run manifest without deleting raw history.

The run manifest must record sources, seed categories, related niches, exclusions, selected full packs, capture dates, cache decisions, and limitations.

## Workflow

1. Confirm intended client, account, marketplace, product or niche, and output type.
2. Apply account recovery and post-switch identity verification before any POE request.
3. Run wide discovery when the question is exploratory. Run a direct niche pull only when a specific authoritative niche ID is already in scope.
4. Format outputs into `output/<client>/opportunity-data/` with market in filenames. This is a staging location, not delivery.
5. Archive the complete evidence set and its manifest through the installed pCloud API route into the client's existing `_Data/opportunity-data/` tree. Verify every remote checksum and report the durable pCloud path. If archival is unavailable, say the local research exists but pCloud archival is blocked; never call the pack delivered.
6. Trace each recommendation to POE search terms, products, reviews, returns, trends, or price structure.
7. Stop before changing listings, uploading assets, publishing copy, or making an Amazon-visible change.

## Outputs

For creative or image strategy, provide concrete visual recommendations and data citations. For product strategy, provide positioning, feature, price, and entry implications. For SEO or Alexa AI strategy, provide semantic phrase and intent clusters tied to Amazon-native evidence. The reported output must distinguish the analysis from its evidence archive and include the checksum-verified pCloud `_Data/opportunity-data/` destination for every complete pack.
