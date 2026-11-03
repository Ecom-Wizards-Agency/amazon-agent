# Amazon SEO Keyword Workbook Workflow

> **Current-agent rule:** the active agent gathers MCP and browser inputs, writes SEO, builds, validates, and completes authorized internal delivery. A handoff is used only when a required capability is unavailable.
>
> **Known capture quirks** (baked into the preflight browser checklist; details in the `amazon-seo` skill): POE inputs come from the API-first downloader (`run-poe.mjs`, one command per niche; manual tab-click/CSV export is fallback only); Amazon may render EN → switch the site language preference before listing capture; clean up duplicate downloads only after canonical inputs pass validation.

## 1. Run SoldScope Keyword Research

Keyword data comes from the SoldScope MCP. A run is identified by its marketplace, its ASIN list (anchor first) and its `search_id`; there is no saved niche. The full procedure, the adapter CLI and the credit rule are in `tools/soldscope/README.md`.

SoldScope calls that spend credits need one run approval naming the ASINs, marketplace and expected credits; rank-tracker writes need exact-action approval (`tools/soldscope/README.md`).

1. **Pick the ASIN set.** The anchor first when the product is live, plus up to 9 competitors: POE top clicked products, the top 10 of `keyword_research_search_by_keyword` for the hero keyword, or the operator's list.
2. **State the credits and get the run approval.** `keyword_research_search_multi_asin` costs one credit per ASIN.
3. **Start the search.** US, CA, MX, UK, DE, ES, FR and IT: one `keyword_research_search_multi_asin` with 2 to 10 ASINs. Other marketplaces: one `kr_asin_search` per ASIN, read with `kr_get_results`; the adapter merges them (`--asin-pages`) and computes relevancy itself.
4. **Read every row.** Poll `keyword_research_get_search_progress` at most every 5 seconds (`searchStatus` 2 = done, 13 = failed). Page `keyword_research_get_multi_results` with `per_page` 1000 until every `meta.total` row is read, and save each page as `multi-<search_id>-page-NNN.json` in the run folder. Log the credits in `credits-log.tsv` there.
5. **Write the builder files.**

   ```bash
   .venv/bin/python tools/soldscope/keywords.py --pages multi-<search_id>-page-*.json \
     --out-dir <run dir> --anchor <ASIN> --asins <ASIN,ASIN,...> --marketplace <US> --search-id <id>
   ```

   It writes `roots.csv`, `core.csv` (relevancy 0.30 or more), `expanded.csv` (the complete pool, relevancy 0.01 or more), `competitors.csv`, `research.json` and `keywords-receipt.json`. Relevancy is normalized to 0-1. The run fails (exit 2) when the rows read do not equal `meta.total` or the unique, dropped and merged rows do not add up; fix the pages, never the receipt.
6. **Point the config at the run.** `roots_csv`, `master_csv`, `expanded_mkl_csv` and `competitors_csv` take the four CSVs. Copy the run fields from `research.json` and `keywords-receipt.json` into `keyword_exports` and `product_anchor.research`; never type them from memory.

**Verify that `core.csv` carries the exact anchor ASIN as a column before building.** The adapter puts the anchor first when it was in the search's ASIN set. If it is missing, the anchor was not searched; a new search costs credits and needs a new approval.

**Prelaunch products** have no anchor. Leave `product_anchor.asin` empty, search the competitors only, omit `--anchor`, and set `ranking_context.mode` to `unavailable` (see `NEW-CLIENT.md`).

Legacy DataDive configs (`datadive_niche`, `datadive_exports`) still build from their saved CSVs with DataDive labels; no new DataDive data is collected.

## 2. Gather POE/OEI Evidence

Preferred: the API-first downloader (`amazon-opportunity-explorer` skill,
`tools/opportunity-explorer/run-poe.mjs`). ONE command per niche produces every
POE contract input, locale-independent and builder-ready:

```bash
node tools/opportunity-explorer/run-poe.mjs search --query "<niche kw>" --marketplace <cc> --client <slug>   # → *_related-niches.json
node tools/opportunity-explorer/run-poe.mjs niche  --niche-id <id>     --marketplace <cc> --client <slug>   # → Products/SearchTerms CSVs, CRI (sentiment-labeled), Returns, overview JSON
```

All EU marketplaces run through the one `.de` login (`--origin
https://sellercentral.amazon.de --marketplace de|it|es|fr|…`); US via the
default `.com` origin. Map outputs to the config inputs:

| config input | run-poe output |
|---|---|
| `poe_products_csv` | `<date>_<cc>-<slug>_NicheDetailsProductsTab.csv` |
| `poe_search_terms_csv` | `<date>_<cc>-<slug>_NicheDetailsSearchTermsTab.csv` |
| `related_niches_json` | `<date>_poe_<cc>_<query>_related-niches.json` |
| `poe_reviews_json` | `<date>_poe_<cc>-<slug>_customer-review-insights.json` |
| `poe_returns_json` | `<date>_poe_<cc>-<slug>_returns.json` |
| `poe_structured_json` | `<date>_poe_<cc>-<slug>_overview.json` |

Record the POE context from the overview JSON (account, marketplace, niche,
last-updated date). A niche without returns data yields `notExposed: true`;
the builder writes its honest "not-exposed" row automatically.

Fallback (manual UI export + deprecated DOM extractor): see
`skills/amazon-opportunity-explorer/references/poe-niche-export-checklist.md`.

Never inspect cookies, local storage, session storage, tokens, or credentials.

## 3. Capture Listing Reference

Use the **local-language Amazon path** (e.g. `amazon.it/dp/<ASIN>`) and **preserve both the requested ASIN and the resolved ASIN**. Amazon may redirect a child ASIN to its canonical parent; keep a row even when title/bullets fail to capture (set `status`).

Save listing evidence as JSON:

- product family confirmation
- requested ASIN + resolved ASIN
- parent/child ASINs
- listing status
- title, bullets, description
- ingredients/composition
- serving size and pack size
- health-claim caveats

These listing facts feed the config **`product_facts`** block (form, `blend_or_single`,
`ingredients[]` incl. branded raw materials, certifications, key attributes). Fill it
before writing `seo_content`: a **blend** must not lead the title with one ingredient,
and ingredient *names* are factual while ingredient *effects* are health claims.

Stop if the ASIN resolves to the wrong product family. Flag any cross-family edge case, such as live copy that clearly describes one product family while the keyword run's competitor data (`competitors.csv` category) places the ASIN in another.

## 4. Preflight

```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/<config>.json --preflight
```

If the complete pool (`expanded_mkl_csv`) is missing, do not substitute the Core file. Re-run `tools/soldscope/keywords.py` on the saved pages; it writes both from the same run, at no credit cost.

## 5. Build And QA

Run the builder and require all validations to pass:

- Core MKL rows match `core.csv`
- Expanded MKL rows match `expanded.csv`
- Core/Expanded paths are distinct
- The Core MKL carries the exact anchor ASIN column (and same-brand siblings are in `asin_roles.siblings`, so they don't pollute triage or duplicate the anchor row)
- keyword run metadata (`keyword_exports`, legacy `datadive_exports`) is complete and not placeholder text
- Never Ever rows are one-word `Never Ever` rows only
- POE rows match current sources
- stale product/language/market terms are absent
- health-claim risk terms are not pushed into visible copy automatically
- no competitor brand tokens (`triage.brand_tokens`) in the SEO Text "New Listing" copy (title/bullets/description/backend); own brand allowed, Notes column exempt
- `1. Root Keywords` is written as `Important | Root Keyword | Frequency | Broad Search Volume | Root Score`. `Important` auto-marks roots whose Root Score (0-1) is at least `root_importance.min_score` (default 0.10)

## 6. Deliver

Delivery is the last step of the build and runs only with `--deliver 1`: with `inputs.drive_folder` set in the config, a QA-passed build run with that flag is delivered as a native Google Sheet through `tools/gdrive-deliver/deliver.py` (receipt saved next to the manifest). Without the flag the build prints the target and stops; pass it only after the operator confirms the destination. `--deliver` is never read from the config, and `--no-deliver 1` forces build-only. The destination is the client's Google Drive folder (shared drive `Ecom Wizards`, account `<your-google-account>`):

`<your-gdrive-mount>/Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/<Client> - Shared/<Keyword Research>/<Country>/`

The workbook is a client deliverable, so it goes inside `<Client> - Shared/`, the only folder the client can see. Everything else under `<Client>/` is internal; never deliver into it (see Google Drive Delivery in `AGENTS.md`).

Once the Sheet exists, set `inputs.drive_sheet_id` to its id (the build prints the id as a hint after a successful delivery; it is the receipt's `remote_id`). Every later QA-passed build run with `--deliver 1` then updates that Sheet in place through `tools/gdrive-deliver/update_sheet.py` instead of creating a new one: same file id, comments and links preserved, formatting kept, every workbook tab cleared and rewritten with live formulas, Sheet-only tabs left untouched and listed as `tabs_orphaned` in the receipt. A build with any FAIL never updates the Sheet, exactly as it never delivers. Preview the plan with `python3 tools/gdrive-deliver/update_sheet.py <workbook.xlsx> <sheet id> --dry-run`, which makes no write call.

Folder convention: **one Keyword Research folder per client, with a sub-folder per country**, NOT a folder per run (e.g. `Acme/Acme - Shared/Keyword Research/ES/Acme ES Collagen Keyword Research 2026-06-15 v2.xlsx`). The folder's exact name varies per client (`Keyword Research`, `02 Keyword Research`): list it and reuse the existing one rather than creating a variant. **If the client has only one country, drop the country sub-folder** and put the workbook directly in that folder. New versions of the same run replace the old `.xlsx` in place. **Google Drive is the only delivery target. Do NOT also copy to pCloud** (decided 2026-06-12; the file is converted to a Google Sheet on Drive anyway). This applies to every client. Verify a byte-identical MD5 after copying. Do NOT copy the POE/SoldScope raw files or the manifest there. They are embedded in the workbook tabs / kept local working files. Keep the `.xlsx` as the canonical workbook; the native Google Sheet copy is the shareable view.

The build also writes:

- manifest JSON
- optional capability handoff note (shared team vault when reachable, otherwise next to the workbook)
- copy-ready capability continuation checklist

## 7. (Optional, on explicit PPC request) Fill Campaign Structure

Fill the `5. Campaign Structure` tab from the built workbook via
`fill_campaign_structure.py` (`/fill-campaigns`): extract candidates → agent classifies per
`_local/ads-strategy/strategy.md` → dry-run → apply. Visual plan + Proposed Campaign Names block
only (no bulk files); the operator pastes into the bulk-creator webapp. Details in the
`skills/amazon-seo/references/keyword-research-workbook.md`, section "Campaign Structure Fill".
