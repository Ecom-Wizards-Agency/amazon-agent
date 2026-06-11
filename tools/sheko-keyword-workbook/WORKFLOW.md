# Sheko Keyword Workbook — Monthly Workflow (Operator Runbook)

End-to-end runbook for regenerating the Sheko DE Kollagen keyword workbook each
cycle. Pairs with `README.md` (what the builder does) — this file is **how to
run the whole cycle**, including what is manual (browser) vs automated.

Product anchor (locked in `config.json`): client **Sheko** · account
**Allmedica** · marketplace **Germany** · **SHEKO Premium Kollagen Pulver 450g**
· ASIN **B0D1G28XR5** · DataDive niche **m6202AaAgV** · POE niche **collagen
pulver**.

---

## The data-source split (read this first)

| Input | Source | Automated? |
|---|---|---|
| Roots / Master / Competitors | **DataDive** (MCP `get_niche_keywords` / `get_niche_competitors`, or DataDive UI CSV export) | MCP read-only |
| Ranking Juice benchmark | **DataDive MCP** `get_ranking_juice` (niche `m6202AaAgV`) | MCP read-only |
| POE Products / Search Terms / Related Niches / Reviews / Returns | **Amazon Seller Central → Product Opportunity Explorer** | **Manual / connected browser only** (no MCP) — see the POE export checklist |
| Workbook assembly + styling | `build_keyword_workbook.py` | deterministic script |
| SEO copy, triage rules | `seo_content.json` + `config.json` (curated) | human-edited, applied deterministically |

POE is the only part that needs the logged-in browser. Everything downstream is
deterministic.

---

## Two-agent flow + preflight (don't hand-translate between Codex and Claude)

Each config carries an `inputs{}` contract (the exact paths the builder needs),
so paths aren't recited on the CLI. Run **preflight** to see status and get the
auto-generated handoff — the tool composes the message, not you:

```bash
.venv/bin/python tools/sheko-keyword-workbook/build_keyword_workbook.py \
  --config tools/sheko-keyword-workbook/<config>.json --preflight
```

- **Missing browser/UI inputs** → prints a copy-ready **Codex task** (paste it to
  Codex). Codex produces the contract inputs at their paths + evidence, then
  stops. It does **not** run the builder or write SEO.
- **All inputs present** → prints **READY** + the build command. Claude writes the
  SEO content (`seo_content*.json`) and runs the build.

Loop: `preflight` → paste to Codex → Codex works → `preflight` again → READY →
Claude builds. Saved protocol:
`/Users/victoruhl/Obsidian/Victors Second Brain/Context/codex-claude-handoff-protocol.md`.

**New product/market:** product-specific tabs must be rebuilt from current
sources or blanked with an explicit warning. Configure current POE evidence
paths for Reviews, Returns, and Structured Overview so the builder can rebuild
`POE Raw - Reviews`, `POE Raw - Returns`, and `POE Semantic Insights`. Keep
`ASINs`, `Competitors`, and `Never KWs` in `tabs.carry_forward_clear` unless
current curated sources exist. Add a `stale_data_guard` for known wrong-product
terms so a new-market workbook never ships template content (e.g. German
collagen reviews in an Italian fibre workbook).

---

## Steps

### 1. Pull DataDive inputs
From DataDive (MCP or UI), export to `~/Downloads/`:
- `niche-m6202AaAgV-niche-analysis-roots.csv`
- `master list-niche-m6202AaAgV-keywords.csv`
- `niche-m6202AaAgV-competitors.csv`

### 2. Pull POE inputs (connected browser)
Follow `skills/amazon-opportunity-explorer/references/poe-niche-export-checklist.md`.
Produces:
- `~/Downloads/NicheDetailsProductsTab_<date>.csv`, `~/Downloads/NicheDetailsSearchTermsTab_<date>.csv` (main niche)
- related-niches grid capture → `output/sheko/opportunity-data/<date>_poe_collagen-pulver_related-niches_chrome.json`
- customer-review-insights capture → `output/sheko/opportunity-data/<date>_poe_<keyword>_customer-review-insights.json`
- returns capture or not-exposed evidence → `output/sheko/opportunity-data/<date>_poe_<keyword>_returns.json`
- structured overview capture → `output/sheko/opportunity-data/<date>_poe_<keyword>_visible-structured.json`
- per-niche CSVs → `downloads/sheko/opportunity-data/related-niches-<date>/`
- evidence (screenshots/snapshots) → `evidence/sheko/opportunity-data/`

### 3. Refresh the Ranking Juice snapshot
The builder cannot call the MCP, so update the snapshot by hand:
- Call DataDive MCP `get_ranking_juice` with `nicheId: m6202AaAgV`.
- Update `tools/sheko-keyword-workbook/seo_content.json → ranking_juice_snapshot`
  (total/title/bullets/description current vs target) and the per-row `rj`
  strings. Also check `list_indexing_issue_alerts` (marketplace `de`) — note any
  ASIN that lost indexing.

### 4. Run the builder
```bash
cd "/Users/victoruhl/Codex Projects/Amazon Agent"
.venv/bin/python tools/sheko-keyword-workbook/build_keyword_workbook.py \
  --out "output/sheko/seo/Sheko DE Kollagen Powder Keyword Research <date> v<N>.xlsx" \
  --manifest "output/sheko/seo/<date>_sheko_keyword_research_v<N>_summary.json"
```
Override `--roots-csv`, `--master-csv`, `--poe-products-csv`,
`--poe-search-terms-csv`, `--related-niches-json` if the new files use different
names/paths. `--template` defaults to the prior version's `.xlsx` (the style
base) — point it at the latest reviewed workbook.

### 5. Review
- All 8 validations must print **PASS** (exit code 0). Fix any FAIL before delivery.
- Skim the manifest: `dropped` related niches (drift gone), `outlier_triage`
  counts, `seo_text.ranking_juice_snapshot`.
- The triage and SEO copy are a **starting point** — refine `config.json` tokens
  / `seo_content.json` and re-run if needed. Curated tabs (Reviews, Returns,
  Semantic Insights) carry forward from the template; refresh them when the POE
  data materially changes.

### 6. Deliver (see below)

---

## Delivery

The builder produces a **styled `.xlsx`** — that is the source of truth (it
preserves the template's column widths, freeze panes, tab colors, and
formatting). Native Google-Sheet copies made via CSV/text conversion lose that
formatting, so we deliver the `.xlsx` and convert with one click.

1. **Copy to Drive.** The Google Drive connector and the local Drive Desktop
   mount are both `victor@ecomwizards.agency`. Either works:
   - Filesystem: `cp` the `.xlsx` into
     `…/GoogleDrive-victor@ecomwizards.agency/Geteilte Ablagen/Ecom Wizards/01_Client Sheets/Partners/Sheko/`
   - or the builder's `--drive-dir "<that folder>"` flag to copy on build.
2. **Native copy (optional):** in Drive, open the `.xlsx` → **File → Save as
   Google Sheets**. Keep the `.xlsx` as the canonical version; treat the native
   Sheet as a shareable view.
3. Confirm the new version sits alongside (not overwriting) prior versions.

---

## Cycle checklist

- [ ] DataDive roots/master/competitors CSVs in `~/Downloads/`
- [ ] POE Products/Search Terms CSVs + related-niches JSON + evidence captured
- [ ] Ranking Juice snapshot refreshed in `seo_content.json`
- [ ] Builder run → 8/8 validations PASS
- [ ] Manifest reviewed (drift dropped, triage/action counts sane)
- [ ] `.xlsx` copied to the Sheko Drive folder (new version, no overwrite)
- [ ] Native Google-Sheet copy made if a shareable link is needed
