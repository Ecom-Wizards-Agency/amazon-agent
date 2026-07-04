# Amazon SEO Keyword Workbook Workflow

> **Cross-agent note:** Codex gathers these inputs via the internal browser while Claude writes SEO + builds. Codex waits for Claude's handoff with the **`/seo-standby`** command, then captures to the contract paths and stops.
>
> **Known capture quirks** (baked into the preflight Codex task; details in the `amazon-seo-keyword-workflow` skill): DataDive export buttons may emit no download event → manual download + Codex maps files by rows/headers, Claude cross-checks counts vs the DataDive MCP; POE tabs need an in-page click (direct URLs render header-only) and POE downloads land in `~/Downloads` even when the download event times out; Amazon may render EN → switch the site language preference before listing capture; Codex cleans up duplicate downloads only after Claude accepts the canonical files.

## 1. Gather DataDive Exports

**MCP-first:** generate **roots**, **Core 30% MKL**, and **competitors** from the DataDive MCP via `datadive_mcp_to_csv.py` — only the **Expanded 1% MKL** needs a UI download (the MCP returns only the ~visible/tracked set == the 30% view, not the 1% tail). Validated identical to the UI exports; see the `datadive-mcp-vs-download` memory and the `amazon-seo-keyword-workflow` skill.

- **roots CSV** — MCP `get_niche_roots` → generator (or Roots grid's leftmost **Export** tab for **Normalized Root**).
- **Core MKL CSV at `30% Min Rel.`** — MCP `get_niche_keywords` → generator (confirm `len(keywords)==numVisibleKeywords` first).
- **Expanded MKL CSV at `1% Min Rel.`** — **UI DOWNLOAD ONLY** (export the full grid as a real CSV — never recover by scrolling; never substitute the 30% file; NOT MCP-reproducible).
- **competitors CSV** — MCP `get_niche_competitors` → generator (or **Niche Tracker > Export Competitors**).

At export time, record for **both** MKLs in the config: **Min Rel., visible keyword count, visible search volume, and export timestamp** (don't backfill these later — capture them while the grid is on screen).

**Verify the Core MKL has the exact anchor ASIN as a real column BEFORE any fallback/injection logic.** Only if the anchor column is genuinely absent should you inject its ranks via DataDive MCP `get_niche_keywords` (and drop any same-brand sibling column so it can't corrupt triage). A clean export with the anchor already tracked needs no injection.

Use DataDive MCP for:

- Ranking Juice snapshot
- competitor sanity checks
- keyword distribution sanity checks
- outlier/opportunity context

## 2. Gather POE/OEI Evidence

Use Chrome/Seller Central and the `amazon-opportunity-explorer` skill.

Capture:

- POE Products CSV — **Niche Details route `/product`**
- POE Search Terms CSV — **Niche Details route `/search-queries`**
- Customer Review Insights JSON
- Returns JSON or not-exposed evidence
- Related Niches JSON
- structured overview JSON
- screenshots/evidence

Record the visible POE context (account, country, niche, last-updated date), e.g. `Example Brand · target account · target marketplace · niche "<niche name>" · last updated <date>`.

If **Customer Review Insights** or **Returns** routes are sparse / expose no table, still capture the visible route state as JSON **with an explicit caveat** — the builder writes an honest "not-exposed" row rather than leaving the tab stale.

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
before writing `seo_content` — a **blend** must not lead the title with one ingredient,
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
- no competitor brand tokens (`triage.brand_tokens`) in the SEO Text "New Listing" copy — title/bullets/description/backend; own brand allowed, Notes column exempt
- `1. Root Keywords` is written as `Important | Root Keyword | Frequency | Broad Search Volume | Root Score` — `Important` auto-marks roots whose DataDive score ≥ `root_importance.min_score` (default 0.10)

## 6. Deliver

Copy ONLY the QA-passed final `.xlsx` to the client's Google Drive folder (shared drive `Ecom Wizards`, account `<your-google-account>`):

`<your-gdrive-mount>/Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/Keyword Research/<Country>/`

Folder convention: **one `Keyword Research` folder per client, with a sub-folder per country** — NOT a folder per run (e.g. `Acme/Keyword Research/ES/Acme ES Collagen Keyword Research 2026-06-15 v2.xlsx`). **If the client has only one country, drop the country sub-folder** and put the workbook directly in `…/<Client>/Keyword Research/`. New versions of the same run replace the old `.xlsx` in place. **Google Drive is the only delivery target — do NOT also copy to pCloud** (decided 2026-06-12; the file is converted to a Google Sheet on Drive anyway). This applies to every client. Verify a byte-identical MD5 after copying. Do NOT copy the POE/DataDive raw files or the manifest there — they are embedded in the workbook tabs / kept local working files. Keep the `.xlsx` as the canonical workbook; the native Google Sheet copy is the shareable view.

The build also writes:

- manifest JSON
- Obsidian handoff note
- copy-ready Claude/Codex prompt

## 7. (Optional, on explicit PPC request) Fill Campaign Structure

Fill the `5. Campaign Structure` tab from the built workbook via
`fill_campaign_structure.py` (`/fill-campaigns`): extract candidates → agent classifies per
`_local/ads-strategy/strategy.md` → dry-run → apply. Visual plan + Proposed Campaign Names block
only — no bulk files; the operator pastes into the bulk-creator webapp. Details in the
`amazon-seo-keyword-workflow` skill, section "Campaign Structure Fill".
