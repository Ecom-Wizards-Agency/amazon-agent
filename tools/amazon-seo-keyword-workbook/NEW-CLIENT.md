# New Client / Product / Market — Setup Checklist

This builder is **client-agnostic**. Nothing is Sheko/collagen-specific — every run
is driven by a config. Adding a new client/product/market = one config + one SEO
content file. No code changes.

## 1. Create the config
```bash
cp tools/amazon-seo-keyword-workbook/config.TEMPLATE.json \
   tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json
```
Fill every `<...>` and `TO_RECORD_*`:
- **`product_anchor`** — client, account, marketplace, product, **anchor ASIN** (must be a DataDive-tracked column in the master CSV), DataDive niche id, POE niche.
- **`related_niche_filter.keep` / `exclude_examples`** — only the genuinely relevant POE related niches; list known drift to drop (validation fails if drift survives).
- **`triage` tokens** — `brand_tokens` from the DataDive competitors; `form/claim/negative` for this product form + marketplace language. For `claim_tokens`, check `skills/amazon-seo/references/eu-compliance-matrix.md`.
- **`never_ever`** — `relevant_words` (protect real product intent), `explicit_never_words` (force-negate junk), marketplace `stop_words`.
- **`stale_data_guard.forbidden_terms`** — distinctive terms from the *template's* product so it can't leak into the new workbook (e.g. German collagen terms in an Italian fibre workbook).
- **`inputs{}`** — the paths for every source file (the contract; CLI flags still override).
- **`datadive_exports`** — record Core 30% + Expanded 1% metadata **at export time** (placeholder `TO_RECORD_*` values fail validation by design).

## 2. Preflight (auto-generates the Codex handoff)
```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json --preflight
```
- Missing browser/UI inputs → it prints a **copy-ready Codex task**. Paste to Codex.
- Codex (connected browser): DataDive UI CSVs (roots, Core 30% MKL, **Expanded 1% MKL**, competitors), POE Products/Search Terms CSVs, POE related-niches/reviews/returns/structured JSON, and a listing-reference JSON. Then it stops and reports paths.

## 3. Write the SEO content
```bash
cp <an existing seo_content.*.json> \
   tools/amazon-seo-keyword-workbook/seo_content.<client>-<market>.json
```
- Pull the **Ranking Juice** snapshot from the DataDive MCP (`get_ranking_juice` for the niche) into `ranking_juice_snapshot`.
- Write the **title / bullets / description / backend** per `references/seo-writing-methodology.md`.
- Apply EU compliance per `references/eu-compliance-matrix.md` and note each removed/authorized claim in the compliance column.

## 4. Build
```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json
```
All QA gates must pass (Core/Expanded row counts match CSVs; distinct source paths;
DataDive metadata not placeholder; Never-Ever one-word; POE tabs current-source;
stale-data guard clean; sheet names valid; style preserved). Fix any FAIL before delivery.

## 5. Deliver
Review the `.xlsx`, then copy to the client's Drive folder (or use `--drive-dir`).
Optionally **File → Save as Google Sheets** for a shareable native copy.

---
**Worked example:** `config.sheko-ballastpulver-it.json` + `seo_content.sheko-ballastpulver-it.json`
(Sheko fibre, amazon.it). Sheko is just an example client here — not the tool's identity.
