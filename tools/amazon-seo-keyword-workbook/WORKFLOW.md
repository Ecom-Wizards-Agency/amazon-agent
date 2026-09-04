# Amazon SEO Keyword Workbook Workflow

> **Current-agent rule:** the active agent gathers MCP and browser inputs, writes SEO, builds, validates, and completes authorized internal delivery. A handoff is used only when a required capability is unavailable.
>
> **Known capture quirks** (baked into the preflight browser checklist; details in the `amazon-seo` skill): DataDive export buttons may emit no download event → map files by rows/headers and cross-check counts against DataDive MCP; POE inputs come from the API-first downloader (`run-poe.mjs`, one command per niche; manual tab-click/CSV export is fallback only); Amazon may render EN → switch the site language preference before listing capture; clean up duplicate downloads only after canonical inputs pass validation.

## 1. Gather DataDive Exports

**MCP-first:** generate **roots**, **Core 30% MKL**, and **competitors** from the DataDive MCP via `datadive_mcp_to_csv.py`. Validated identical to the UI exports; see the `datadive-mcp-vs-download` memory and the `amazon-seo` skill. The **full keyword pool** (formerly called the "Expanded 1% MKL") needs no UI download either: merge three read-only endpoints (`/mkl/{id}?includeAsinCatalog=true`, `/outlier/{id}`, `/residue-kw-list/{id}`) and filter `relevancy` locally. Never change the niche's Min. Relevancy setting; it mutates shared state for the whole team.

- **roots CSV**: MCP `get_niche_roots` → generator (or Roots grid's leftmost **Export** tab for **Normalized Root**).
- **Core MKL CSV at `30% Min Rel.`**: MCP `get_niche_keywords` → generator (confirm `len(keywords)==numVisibleKeywords` first).
- **Complete keyword-pool CSV filtered at `1% Min Rel.`**: merge the three read-only endpoints above, verify that the partition count matches `numKeywords`, then write it to the legacy `expanded_mkl_csv` contract path. Never substitute the 30% Core file.
- **competitors CSV**: MCP `get_niche_competitors` → generator (or **Niche Tracker > Export Competitors**).

At export time, record for **both** MKLs in the config: **Min Rel., visible keyword count, visible search volume, and export timestamp** (don't backfill these later; capture them while the grid is on screen).

**Verify the Core MKL has the exact anchor ASIN as a real column BEFORE any fallback/injection logic.** Only if the anchor column is genuinely absent should you inject its ranks via DataDive MCP `get_niche_keywords` (and drop any same-brand sibling column so it can't corrupt triage). A clean export with the anchor already tracked needs no injection.

Use DataDive MCP for:

- Ranking Juice snapshot
- competitor sanity checks
- keyword distribution sanity checks
- outlier/opportunity context

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

Stop if the ASIN resolves to the wrong product family. Flag any cross-family edge case, such as live copy that clearly describes one product family while DataDive categorises the ASIN differently.

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
- The Core MKL carries the exact anchor ASIN column (and same-brand siblings are in `asin_roles.siblings`, so they don't pollute triage or duplicate the anchor row)
- DataDive metadata is complete
- Never Ever rows are one-word `Never Ever` rows only
- POE rows match current sources
- stale product/language/market terms are absent
- health-claim risk terms are not pushed into visible copy automatically
- no competitor brand tokens (`triage.brand_tokens`) in the SEO Text "New Listing" copy (title/bullets/description/backend); own brand allowed, Notes column exempt
- `1. Root Keywords` is written as `Important | Root Keyword | Frequency | Broad Search Volume | Root Score`. `Important` auto-marks roots whose DataDive score ≥ `root_importance.min_score` (default 0.10)

## 6. Deliver

Delivery runs inside the build: with `inputs.drive_folder` set in the config, a QA-passed build is delivered as a native Google Sheet through `tools/gdrive-deliver/deliver.py` (receipt saved next to the manifest, `--no-deliver 1` to skip). The destination is the client's Google Drive folder (shared drive `Ecom Wizards`, account `<your-google-account>`):

`<your-gdrive-mount>/Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/<Client> - Shared/<Keyword Research>/<Country>/`

The workbook is a client deliverable, so it goes inside `<Client> - Shared/`, the only folder the client can see. Everything else under `<Client>/` is internal; never deliver into it (see Google Drive Delivery in `AGENTS.md`).

Once the Sheet exists, set `inputs.drive_sheet_id` to its id (the build prints the id as a hint after a successful delivery; it is the receipt's `remote_id`). Every later QA-passed build then updates that Sheet in place through `tools/gdrive-deliver/update_sheet.py` instead of creating a new one: same file id, comments and links preserved, formatting kept, every workbook tab cleared and rewritten with live formulas, Sheet-only tabs left untouched and listed as `tabs_orphaned` in the receipt. A build with any FAIL never updates the Sheet, exactly as it never delivers. Preview the plan with `python3 tools/gdrive-deliver/update_sheet.py <workbook.xlsx> <sheet id> --dry-run`, which makes no write call.

Folder convention: **one Keyword Research folder per client, with a sub-folder per country**, NOT a folder per run (e.g. `Acme/Acme - Shared/Keyword Research/ES/Acme ES Collagen Keyword Research 2026-06-15 v2.xlsx`). The folder's exact name varies per client (`Keyword Research`, `02 Keyword Research`): list it and reuse the existing one rather than creating a variant. **If the client has only one country, drop the country sub-folder** and put the workbook directly in that folder. New versions of the same run replace the old `.xlsx` in place. **Google Drive is the only delivery target. Do NOT also copy to pCloud** (decided 2026-06-12; the file is converted to a Google Sheet on Drive anyway). This applies to every client. Verify a byte-identical MD5 after copying. Do NOT copy the POE/DataDive raw files or the manifest there. They are embedded in the workbook tabs / kept local working files. Keep the `.xlsx` as the canonical workbook; the native Google Sheet copy is the shareable view.

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
