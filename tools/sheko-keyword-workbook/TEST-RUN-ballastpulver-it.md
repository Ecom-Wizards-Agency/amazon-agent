# Test Run — Sheko Ballastpulver IT (reusability check)

Validates that the keyword-workbook builder works on a **different product +
marketplace** with no code changes — only new config + data.

| | |
|---|---|
| Product | Sheko Ballastpulver (fiber/psyllium powder) |
| Marketplace | amazon.it |
| DataDive niche | `8cN8b7h9F5` (hero "fibra") |
| Anchor ASIN | `B0GXZRCHQM` (Sheko; near-empty listing, RJ 4,497 → 182,860 target) |
| Config | `config.ballastpulver-it.json` (scaffolded — SEED keep-list/tokens) |
| SEO content | `seo_content.ballastpulver-it.json` (real RJ snapshot; SEO rows = TBD) |

## Already scaffolded (this session)
- `config.ballastpulver-it.json` — anchor, niche, IT brand/form/claim tokens (brands from DataDive competitors), SEED related-niche keep-list.
- `seo_content.ballastpulver-it.json` — real Ranking Juice snapshot from DataDive MCP; placeholder SEO rows.

## Still required before the builder can run green
1. **DataDive CSV exports** for niche `8cN8b7h9F5` (the exact-paste tabs need the UI CSV format, not MCP JSON):
   - roots → `~/Downloads/niche-8cN8b7h9F5-niche-analysis-roots.csv`
   - master → `~/Downloads/master list-niche-8cN8b7h9F5-keywords.csv`
   - competitors → `~/Downloads/niche-8cN8b7h9F5-competitors.csv`
2. **POE exports** (amazon.it, connected/internal browser — confirm the Sheko IT seller account). Follow `skills/amazon-opportunity-explorer/references/poe-niche-export-checklist.md`:
   - `~/Downloads/NicheDetailsProductsTab_<date>.csv`, `~/Downloads/NicheDetailsSearchTermsTab_<date>.csv`
   - related-niches capture JSON → `output/sheko/opportunity-data/<date>_poe_fibra_related-niches_chrome.json`

   > NOTE — the variation family is by **pack size**; `B0GXZRCHQM` is the **1-pack** and is currently **OFFLINE on amazon.it** (other pack sizes are online; same product, same ingredients/copy, just different quantity). POE niche export is niche-level and unaffected. Do NOT try to open the offline 1-pack page. Instead capture the live **title + bullets + description + ingredient/composition list + pack size** from any **online pack variation** (and the parent/variation family if visible) → `evidence/sheko/opportunity-data/<date>_sheko-it-variation_listing.json`. Since all packs are the same product, any online pack gives the ingredient list needed for EU health-claim eligibility.
3. **Refine the SEED config** with the real POE related niches (`related_niche_filter.keep`) and write the Italian SEO copy in `seo_content.ballastpulver-it.json` (after master keywords + live listing text are in).
4. **Template**: reuse the collagen `…v3.xlsx` as the style base (`--template`). Curated carry-forward tabs (ASINs, Reviews, Returns, Semantic, Competitors, Campaign, Never KWs) will be collagen placeholders to replace — fine for a structure/reusability test.

## Run command (once inputs land)
```bash
cd "/Users/victoruhl/Codex Projects/Amazon Agent"
.venv/bin/python tools/sheko-keyword-workbook/build_keyword_workbook.py \
  --config   tools/sheko-keyword-workbook/config.ballastpulver-it.json \
  --seo-content tools/sheko-keyword-workbook/seo_content.ballastpulver-it.json \
  --template "output/sheko/seo/Sheko DE Kollagen Powder Keyword Research 2026-06-10 v3.xlsx" \
  --roots-csv "$HOME/Downloads/niche-8cN8b7h9F5-niche-analysis-roots.csv" \
  --master-csv "$HOME/Downloads/master list-niche-8cN8b7h9F5-keywords.csv" \
  --competitors-csv "$HOME/Downloads/niche-8cN8b7h9F5-competitors.csv" \
  --poe-products-csv "$HOME/Downloads/NicheDetailsProductsTab_<date>.csv" \
  --poe-search-terms-csv "$HOME/Downloads/NicheDetailsSearchTermsTab_<date>.csv" \
  --related-niches-json "output/sheko/opportunity-data/<date>_poe_fibra_related-niches_chrome.json" \
  --out "output/sheko/seo/Sheko IT Ballastpulver Keyword Research <date> v1.xlsx" \
  --manifest "output/sheko/seo/<date>_sheko_it_ballastpulver_v1_summary.json"
```

## Pass criteria
- Builder exits 0 with **all 8 validations PASS** (anchor `B0GXZRCHQM`; root/master/POE row counts match CSVs; related-niche filter drops drift; Final Action values valid).
- Manifest shows kept/dropped related niches and triage counts that make sense for a fiber niche.
- Then: review → deliver `.xlsx` → and (per plan) **upload tooling + docs to GitHub**.
