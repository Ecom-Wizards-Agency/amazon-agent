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
- **`product_anchor`**: client, account, marketplace, product, **anchor ASIN** (must be a DataDive-tracked column in the master CSV), DataDive niche id, POE niche.
  - If a niche already exists but the anchor ASIN is **not** a tracked column, ADD the ASIN to that existing niche in the connected browser (Niche Tracker → add competitor) instead of running a new dive. That reuses the research, ~1 token, no duplicate niche. Only dive when no niche exists. See the "Anchor not tracked in an existing niche" rule in `skills/amazon-seo/references/keyword-research-workbook.md`.
- **`product_facts`**: physical facts from the **label/PDP**: `form`, **`blend_or_single`**, the `ingredients[]` list (names + any branded raw materials, e.g. Fibregum™), `certifications`, and `key_attributes`. These gate the **title framing** (a blend must not lead the title with one ingredient) and compliance (ingredient *names* are factual; ingredient *effects* are health claims). The builder warns if this block is missing.
- **`seo_identity`**: the consumer-facing `brand` and shortest recognizable `product_name`. Both must appear in the <=75-character title and description. Do not infer the brand from the Seller Central client/account name.
- **`related_niche_filter.keep` / `exclude_examples`**: only the genuinely relevant POE related niches; list known drift to drop (validation fails if drift survives).
- **`triage` tokens**: `brand_tokens` from the DataDive competitors; `form/claim/negative` for this product form + marketplace language. For `claim_tokens`, check `skills/amazon-seo/references/eu-compliance-matrix.md`.
- **`never_ever`**: `relevant_words` (protect real product intent), `explicit_never_words` (force-negate junk), marketplace `stop_words`.
- **`stale_data_guard.forbidden_terms`**: distinctive terms from the *template's* product so it can't leak into the new workbook (e.g. German collagen terms in an Italian fibre workbook).
- **`inputs{}`**: the paths for every source file (the contract; CLI flags still override). Leave **`handoff_note`** empty unless you need a specific location. The builder resolves it per run: the shared team vault at `<team-vault>/Clients/<Client>/Handoffs/` when that client already has a folder there, otherwise next to the workbook in `output/<client>/seo/`. Setting it overrides both. Never point it at a personal vault: client folders left the personal vault on 27.07.2026.
- **`datadive_exports`**: record Core 30% + Expanded 1% metadata **at export time** (placeholder `TO_RECORD_*` values fail validation by design).

## 2. Preflight (capability-based checklists)
```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json --preflight
```
- Preflight tags each missing input `(MCP)`, `(BROWSER)`, or `(setup)`.
- **`(MCP)` (generated locally, no browser):** roots, Core 30% MKL, and competitors come from the DataDive MCP. Call `get_niche_roots` / `get_niche_keywords` / `get_niche_competitors`, save each raw JSON, confirm `len(keywords) == numVisibleKeywords`, then run `datadive_mcp_to_csv.py` to write the three contract CSVs. (Validated identical to the UI exports; see the `datadive-mcp-vs-download` memory.)
- **`(BROWSER)`:** the **full DataDive keyword pool** (three read-only GETs merged locally, NOT a UI export and NOT a settings change: see the `amazon-seo` skill), POE Products/Search Terms CSVs, POE related-niches/reviews/returns/structured JSON, and a listing-reference JSON. Save to the contract paths, re-run preflight, and continue when READY. Hand off only a capability that the current runtime lacks.

## 3. Write the SEO content
```bash
cp <an existing seo_content.*.json> \
   tools/amazon-seo-keyword-workbook/seo_content.<client>-<market>.json
```
- Pull the **Ranking Juice** snapshot from the DataDive MCP (`get_ranking_juice` for the niche) into `ranking_juice_snapshot`. Also pull the **master keyword list** (`get_niche_keywords`) so you front-load the highest-SV **tracked** keyword in the title (not a Roots-tab term; see methodology §2).
- Write the **title / bullets / description / backend** per `references/seo-writing-methodology.md`: preserve brand and product identity, describe blends accurately, and satisfy **both** Ranking Juice and the **semantic/Alexa** layer. The semantic row must carry `poe_evidence` from both POE Search Terms and POE Reviews or Returns.
- Apply EU compliance per `references/eu-compliance-matrix.md` (names allowed, effects prohibited) and note each removed/authorized claim in the compliance column.

## 4. Build
```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json
```
All QA gates must pass (Core/Expanded row counts match CSVs; distinct source paths;
DataDive metadata not placeholder; Never-Ever one-word; POE tabs current-source;
stale-data guard clean; sheet names valid; style preserved). Fix any FAIL before delivery.

## 5. Deliver
Delivery is automatic. Set `inputs.drive_folder` in the config to the client's existing
`<Client> - Shared/<Keyword Research>/<Country>` folder (Drive folder id, Drive URL, or the
mounted path). Every build that passes all QA gates is then delivered as a **native Google
Sheet** through `tools/gdrive-deliver/deliver.py`, named after the workbook stem, with a
receipt next to the manifest. A build with any FAIL stays local. Pass `--no-deliver 1` to
build without delivering, or `--drive-folder <id>` to override the config for one run.
Before the first delivery, list the client's Shared folder and reuse the existing Keyword
Research folder; never create a spelling variant next to it.

After the first delivery, paste the receipt's `remote_id` (the build prints it as a hint)
into `inputs.drive_sheet_id`. From then on every QA-passed rebuild **updates that Sheet in
place** through `tools/gdrive-deliver/update_sheet.py` instead of creating a new Sheet:
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
