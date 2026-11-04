# New Client / Product / Market: Setup Checklist

This builder is **client-agnostic**. Nothing is client- or product-specific. Every run
is driven by a config. Adding a new client/product/market = one config + one SEO
content file. No code changes.

## 1. Create the config
```bash
cp tools/amazon-seo-keyword-workbook/config.TEMPLATE.json \
   tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json
```
Fill every `<...>` and `TO_RECORD_*`:
- **`keyword_source`**: `"SoldScope"` (the template default). It sets the client-visible source labels and goes with `tabs.template_renames`, which renames the template's two MKL tabs to `3.1 MKL SoldScope 30%` and `2.1 MKL SoldScope 1%`. Keep the template's other tab names as they are.
- **`product_anchor`**: client, account, marketplace, product, **anchor ASIN** (must be an ASIN column in `core.csv`; the adapter puts the anchor first when it was in the search), POE niche, and **`research`**: the run identity (`asins` with the anchor first, `marketplace`, `search_id`, `date_from`, `date_to`) copied from `research.json`. Legacy configs keep `datadive_niche` instead; the builder still reads it.
  - If the anchor is missing from `core.csv`, it was not in the search's ASIN set. Re-running the adapter cannot add it; a new SoldScope search costs credits and needs a new run approval.
- **Prelaunch/untracked research**: search the competitors only, leave `product_anchor.asin` empty and run the adapter without `--anchor`. When no own ranking observation exists, set `ranking_context` to `{ "mode": "unavailable", "reason": "...", "evidence_file": "..." }`. Evidence JSON must contain matching `asin`, `marketplace`, `status` (`prelaunch` or `inactive-untracked`), `verified_at`, and existing `evidence_files` paths. Use an empty ASIN only for a product awaiting catalog creation. Disable `triage.semantic_opportunity.include_if_anchor_not_ranking`. This mode visibly marks rankings unavailable; it never substitutes a competitor or invents an own-ASIN column. All other QA gates remain required.
- **`product_facts`**: physical facts from the **label/PDP**: `form`, **`blend_or_single`**, the `ingredients[]` list (names + any branded raw materials, e.g. Fibregum™), `certifications`, and `key_attributes`. These gate the **title framing** (a blend must not lead the title with one ingredient) and compliance (ingredient *names* are factual; ingredient *effects* are health claims). The builder warns if this block is missing.
- **`seo_identity`**: the consumer-facing `brand` and shortest recognizable `product_name`. Both must appear in the <=75-character title and description. Do not infer the brand from the Seller Central client/account name.
- **`related_niche_filter.keep` / `exclude_examples`**: only the genuinely relevant POE related niches; list known drift to drop (validation fails if drift survives).
- **`triage` tokens**: `brand_tokens` from the brands in `competitors.csv`; `form/claim/negative` for this product form + marketplace language. For `claim_tokens`, check `skills/amazon-seo/references/eu-compliance-matrix.md`.
- **`never_ever`**: `relevant_words` (protect real product intent), `explicit_never_words` (force-negate junk), marketplace `stop_words`. Its relevancy thresholds, like `triage.semantic_opportunity.min_relevancy`, are normalized relevancy (0-1); the adapter divides SoldScope's 0-100 score by 100, so the old values still apply.
- **`root_importance`**: recalibrate for SoldScope. The adapter's Root Score is a root's Broad Search Volume divided by the top root's, so `min_score` 0.10 marks roots with at least a tenth of the top root's Broad SV. DataDive scored roots differently, so thresholds tuned on DataDive workbooks can mark too many or too few roots. After the first SoldScope build, check how many roots carry the marker and the ad marker in `1. Root Keywords`, and adjust `min_score`, `ad_min_score` and `ad_min_sv` for the client.
- **`stale_data_guard.forbidden_terms`**: distinctive terms from the *template's* product so it can't leak into the new workbook (e.g. German collagen terms in an Italian fibre workbook).
- **`inputs{}`**: the paths for every source file (the contract; CLI flags still override). Leave **`handoff_note`** empty unless you need a specific location. The builder resolves it per run: the shared team vault at `<team-vault>/Clients/<Client>/Handoffs/` when that client already has a folder there, otherwise next to the workbook in `output/<client>/seo/`. Setting it overrides both. Never point it at a personal vault: client folders left the personal vault on 27.07.2026.
- **`keyword_exports`**: the run metadata for Core (`core_mkl`) and the pool (`expanded_mkl`): `search_id`, `asins`, `marketplace`, `date_from`, `date_to`, `raw_rows`, `kept_rows`, `core_min`, `pool_min` and `relevancy_mode`, copied from `research.json` and `keywords-receipt.json` (placeholder `TO_RECORD_*` values fail validation by design). Legacy configs keep `datadive_exports`; the builder still reads it.

## 2. Preflight (capability-based checklists)
```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json --preflight
```
- Preflight tags each missing input `(MCP)`, `(BROWSER)`, or `(setup)`.
- **`(MCP)` (generated locally, no browser):** roots, Core, the complete pool and competitors come from one SoldScope keyword search. Get the run approval, save every result page, then run `tools/soldscope/keywords.py` to write all four CSVs (steps in `WORKFLOW.md` section 1 and `tools/soldscope/README.md`). SoldScope calls that spend credits need one run approval naming the ASINs, marketplace and expected credits; rank-tracker writes need exact-action approval (`tools/soldscope/README.md`).
- **`(BROWSER)`:** POE Products/Search Terms CSVs, POE related-niches/reviews/returns/structured JSON, and a listing-reference JSON. Save to the contract paths, re-run preflight, and continue when READY. Hand off only a capability that the current runtime lacks.

## 3. Write the SEO content
```bash
cp <an existing seo_content.*.json> \
   tools/amazon-seo-keyword-workbook/seo_content.<client>-<market>.json
```
- Score the draft with the **keyword ranking score** (`ranking_score.py --keywords <core.csv> --seo-content <seo_content.json>`); the build appends the same score to the SEO Text tab. Front-load the highest-SV **tracked** keyword from `core.csv` in the title (not a Roots-tab term; see methodology §2). An optional per-row `rj` note shows in the Notes column as "Keyword ranking score note".
- Write the **title / bullets / description / backend** per `references/seo-writing-methodology.md`: preserve brand and product identity, describe blends accurately, and satisfy **both** the keyword ranking score and the **semantic/Alexa** layer. The semantic row must carry `poe_evidence` from both POE Search Terms and POE Reviews or Returns.
- Apply EU compliance per `references/eu-compliance-matrix.md` (names allowed, effects prohibited) and note each removed/authorized claim in the compliance column.

## 4. Build
```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json
```
All QA gates must pass (Core/Expanded row counts match CSVs; distinct source paths;
keyword run metadata not placeholder; Never-Ever one-word; POE tabs current-source;
stale-data guard clean; sheet names valid; style preserved). Fix any FAIL before delivery.

## 5. Deliver
Delivery needs confirmation. Set `inputs.drive_folder` in the config to the client's existing
`<Client> - Shared/<Keyword Research>/<Country>` folder (Drive folder id, Drive URL, or the
mounted path). A build that passes all QA gates and is run with `--deliver 1`, after the
operator confirms the folder, is delivered as a **native Google Sheet** through
`tools/gdrive-deliver/deliver.py`, named after the workbook stem, with a receipt next to
the manifest. Without `--deliver 1` the build prints the target and stops; the flag is
read from the command line only, never from the config. A build with any FAIL stays local.
Pass `--no-deliver 1` to build without delivering, or `--drive-folder <id>` to override the
config for one run.
Before the first delivery, list the client's Shared folder and reuse the existing Keyword
Research folder; never create a spelling variant next to it.

After the first delivery, paste the receipt's `remote_id` (the build prints it as a hint)
into `inputs.drive_sheet_id`. From then on every QA-passed rebuild run with `--deliver 1`
**updates that Sheet in place** through `tools/gdrive-deliver/update_sheet.py` instead of
creating a new Sheet:
same file id, comments and links preserved, cell formatting kept, every workbook tab
cleared and rewritten with live formulas, tabs that exist only in the Sheet left untouched
and listed as `tabs_orphaned` in the receipt. The FAIL rule is unchanged: a build with any
FAIL never updates the Sheet. `--drive-sheet-id <id>` overrides the config for one run,
`--no-deliver 1` skips both routes, and
`python3 tools/gdrive-deliver/update_sheet.py <workbook.xlsx> <sheet id> --dry-run` prints
the tab plan without writing anything.

---
**Client configs are LOCAL ONLY.** Real `config.<client>-*.json` / `seo_content.<client>-*.json`
files contain client data and are gitignored. Never commit them to GitHub. Only
`config.TEMPLATE.json` lives in the repo. Worked examples are your local `config.*.json`
files from previous runs; any such client config is just a worked example, not
the tool's identity.
