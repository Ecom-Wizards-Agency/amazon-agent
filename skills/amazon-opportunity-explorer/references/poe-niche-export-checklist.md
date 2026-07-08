# POE Niche Export Checklist (connected browser)

What the operator/agent must do **in the connected, logged-in Amazon Seller
Central browser** to produce the Product Opportunity Explorer (POE) inputs that
the keyword-workbook builder consumes. POE is behind Seller-Central auth. There
is **no MCP** for it, so this step is always browser-driven.

> Safety (per `AGENTS.md`): never inspect cookies, local storage, session
> storage, tokens, or credentials during extraction. Verify the selected
> **account, marketplace, and niche/page title** before exporting.

This checklist is product-agnostic: substitute the client, niche, ASIN, and
marketplace for the job at hand. A DE collagen powder (`collagen pulver`,
`B0XXXXXXXX`, amazon.de) is the worked example.

---

## A. Per-niche "Niche Details" CSV exports (canonical builder inputs)

**Preferred (API-first, no clicking):** fetch the niche via the downloader.
One call captures Products, Search Terms, CRI (positive+negative), Returns and
overview, and writes builder-ready EN-canonical CSVs regardless of UI locale:

```bash
node tools/opportunity-explorer/run-poe.mjs search --query "<niche keyword>" --marketplace <cc> --client <slug>
node tools/opportunity-explorer/run-poe.mjs niche --niche-id <id> --marketplace <cc> --client <slug>
```

(or via internal-browser evaluate of `tools/opportunity-explorer/fetch-poe.js`
+ `format-poe.mjs`; see that tool's README; API contract in
`tools/opportunity-explorer/references/poe-endpoints.md`.)

**Fallback (manual UI export)**. Do this for the **main niche** and **each
related niche you intend to keep**:

1. Open POE → search/open the niche → **Niche Details**.
2. **Products tab** → export CSV.
3. **Search Terms tab** → export CSV.

Destination + naming the builder expects:

| Niche | Products CSV | Search Terms CSV |
|---|---|---|
| Main | `~/Downloads/NicheDetailsProductsTab_<date>.csv` | `~/Downloads/NicheDetailsSearchTermsTab_<date>.csv` |
| Related (each) | `downloads/{client}/opportunity-data/related-niches-<date>/<##>-<niche-slug>_products_NicheDetailsProductsTab_<date>.csv` | `…_search-terms_NicheDetailsSearchTermsTab_<date>.csv` |

(The main-niche CSVs are passed to the builder via `--poe-products-csv` /
`--poe-search-terms-csv`. The per-niche related CSVs are archived for evidence;
the builder currently derives the related-niches **tab** from the grid capture
in step B; see the optional enhancement in the builder README.)

## B. Related-niches grid + Reviews / Returns / Insights (JSON capture)

**Preferred:** already covered by the downloader in step A. `run-poe.mjs
search` writes the related-niches v1 JSON (builder-compatible `cells` rows) and
`run-poe.mjs niche` writes sentiment-labeled CRI + Returns JSON/CSV.

**Fallback (deprecated DOM extractor):** in the connected browser, on the
relevant POE page, run the repo extractor in page context:

```js
await window.amazonAgentExtractOpportunityExplorer()
```
(loaded from `tools/opportunity-explorer/extract-opportunity-explorer.js`, DEPRECATED)

- Save the returned object as JSON under
  `output/{client}/opportunity-data/<date>_poe_<niche-slug>_*.json`. The builder
  reads the **related-niches** capture (e.g.
  `<date>_poe_collagen-pulver_related-niches_chrome.json`) and uses its
  `tables[0]` (headers + rows) as the related-niches grid.
- Optionally format to JSON + Markdown:
  ```bash
  node tools/opportunity-explorer/format-opportunity-explorer-export.mjs \
    <input.json> output/{client}/opportunity-data
  ```
- The extractor also captures Insights & Trends, Products, Search Terms,
  Customer Review Insights, and Returns tab text/tables. Use these to curate
  the `POE Raw - Reviews`, `POE Raw - Returns`, and `POE Semantic Insights` tabs.

## C. Evidence

Save screenshots / tab snapshots under `evidence/{client}/opportunity-data/`
(e.g. `<date>_poe_<niche>_products.png`, `…_returns.png`, `…_search-terms.png`).

---

## D. Relevance is the builder's job, not the export's

Export whatever niches you need to inspect, **including drift**. The builder
applies the strict keep-list filter (`<your config>.json →
related_niche_filter`) and drops unrelated niches (e.g. `glow`-drift, skincare,
perfume, teeth-whitening, toys, lights, filament). Keep the keep-list in the
config in sync with the niches you actually want in the workbook.

## E. Handoff to the deterministic pipeline

Once A–C exist on disk, the rest is automated and browser-free: run
`tools/amazon-seo-keyword-workbook/build_keyword_workbook.py --config <your config>`
(see that tool's `WORKFLOW.md` / `NEW-CLIENT.md`). Validation fails loudly if a
POE CSV row count doesn't match its sheet, so a bad/partial export is caught
before delivery.
