---
name: amazon-listing-capture
description: Use to capture current Amazon listing copy (title, bullet points, canonical link) for an anchor ASIN and its siblings/competitors in the local marketplace language, into the listing-reference JSON the keyword-workbook builder ingests. Deterministic Codex connected-browser port of the legacy ZeroWork scrape; feeds the ASINs tab.
---

# Amazon Listing Capture

Capture live listing copy (title + bullets + link) for a set of ASINs and write it to the
listing-reference JSON that `tools/amazon-seo-keyword-workbook/build_keyword_workbook.py`
(`build_asins`) ingests to fill the **ASINs tab** (`title`, `bullet_points`, `link`).

This replaces the legacy ZeroWork workflow #45716 (reverse-engineered in
`tools/listing-capture/zerowork-45716-workflow-spec.md`). It is **Codex's job** via the
connected/internal browser — Amazon blocks headless scraping and `agent.md` mandates the
connected browser. Never inspect cookies, storage, tokens, or credentials.

## Inputs
- The **ASINs tab `link` column** (anchor + siblings + competitors) is the input link list —
  already in the clean `amazon.<tld>/dp/<ASIN>` form the scrape expects. Or pass an ASIN list +
  marketplace.
- Competitor ASINs also come from DataDive MCP (`get_niche_competitors`) / `competitors_csv`.

## Routine (per ASIN)
1. **Force local language.** Navigate to the locale path `https://www.amazon.<tld>/-/<lang>/dp/<ASIN>`
   (e.g. `amazon.it/-/it/dp/<ASIN>`) — plain `/dp/<ASIN>` can render the EN UI. Marketplace→lang:
   it→it, de→de, es→es, fr→fr, co.uk→en, com→en. After capture, verify the title/bullets read in the
   local language; if they came back English, retry via the locale path. **If the locale path STILL
   renders English** (confirmed on amazon.it, 2026-06-12): switch the Amazon site language preference
   itself (the language switcher in the nav/footer, e.g. "italiano - IT"), then re-run the capture for
   all affected ASINs.
2. **Run the extractor** `tools/listing-capture/extract-amazon-listing-copy.js` — one
   self-contained function. **Proven runner** (Codex connected browser): evaluate a STRING that
   defines the function and calls it — passing the function *object* is blocked there
   ("Code generation from strings disallowed"):
   ```js
   await tab.playwright.evaluate(
     `(function(){\n${extractorSource}\nreturn extractAmazonListingCopy("B0F2HZVJMB");\n})()`
   )
   ```
   (`extractorSource` = the file contents; the trailing `window.…` assignment is now try/caught so
   the whole file is safe to include.) DevTools / injected path: `window.amazonAgentExtractListingCopy("<requestedAsin>")`.
   **Always pass the requested ASIN** — variation listings redirect (e.g. `B0F2HZVJMB` → `B0GGCBQLND`),
   so the extractor sets `asin` = the requested ASIN (the key the builder uses) and records the
   page's `resolvedAsin` separately. It returns `{ asin, resolvedAsin, title, bullets[], link, capturedAt, status }`:
   - title from `#productTitle`.
   - bullets in order: (1) `#feature-bullets ul`, then (2) fallback
     `#productFactsDesktopExpander > div:first-child ul` — the fallback is **required** (the
     primary is often empty; confirmed by the spec's selector test).
   - link = clean canonical `amazon.<tld>/dp/<ASIN>`.
3. Keep the row even if title/bullets fail; record `status: "empty"|"error"`.

## Output
Assemble one file per the schema `tools/listing-capture/listing-reference.schema.v1.json`:

```json
{ "schemaVersion": "amazon-agent.listing-reference.v1", "marketplace": "amazon.<tld>",
  "listings": [ { "asin": "...", "role": "Anchor|Sibling|Competitor", "title": "...",
                  "bullets": ["...","..."], "link": "https://www.amazon.<tld>/dp/<ASIN>",
                  "capturedAt": "...", "status": "ok" } ] }
```

Save to the run's contract path (e.g. `evidence/<client>/opportunity-data/<date>_<market>_listings_anchor+competitors.json`)
and set it as the config `inputs.listing_reference_json`. The builder then fills the ASINs tab
keyed by ASIN; missing copy stays blank (never fabricated).

## Guardrails
- Connected/internal browser only; do not run the legacy ZeroWork workflow.
- No cookies/storage/credentials/tokens.
- Flag any unauthorized EU health claims seen in the live copy (joint/skin/hair/nail/anti-age)
  so the SEO step can strip them; see `skills/amazon-seo` and `references/eu-compliance-matrix.md`.
