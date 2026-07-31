---
name: amazon-seo-keyword-workflow
description: Use for the end-to-end keyword-research workbook BUILD pipeline: DataDive 30%/1% exports plus POE/OEI evidence in; Never Ever frequency analysis, outlier triage, and validation; styled XLSX workbook out, with Google Drive delivery and the Codex-Claude handoff. For SEO writing, listing re-optimization, or compliance checks use amazon-seo.
---

# Amazon SEO Keyword Workflow

Browser: Mixed (build is local; DataDive via MCP; the full keyword pool via three read-only DataDive endpoints in the extension browser).

Use this when the operator asks for a full Amazon SEO keyword workbook, not only listing copy.

## Standby Command

`/seo-standby` means the operator is starting a keyword-research workbook flow but the actionable instructions are expected from Claude. Acknowledge standby, load this workflow if needed, and wait. Do not open DataDive, Seller Central, Amazon listings, run the builder, write SEO, create Drive outputs, edit listings, commit/push, or inspect browser credentials/session data until the operator provides Claude's concrete handoff.

When the handoff arrives, the browser half of the run is: gather the requested browser/UI inputs, save them to the exact contract paths, report saved paths plus caveats, and stop. One agent can now do both halves in a single session; the split below is a checklist, not a runtime boundary.

## Load Order

1. Use `amazon-seo` for Amazon SEO writing, semantic/Alexa/Rufus logic, and compliance posture.
2. Use `amazon-opportunity-explorer` for POE/OEI data (API-first `run-poe.mjs` downloader) and evidence.
2a. Use `amazon-listing-capture` to capture live listing copy (title/bullets/link) for the anchor + competitors into the listing-reference JSON; the builder fills the ASINs tab from it.
3. Use the workbook builder: `tools/amazon-seo-keyword-workbook/build_keyword_workbook.py`.
4. Use DataDive references only when terminology or UI behavior matters:
   - `skills/amazon-seo/references/datadive-support/datadive-support-index.md`
   - `skills/amazon-seo/references/datadive-support/datadive-seo-workflow-article-map.md`

## Required Data Inputs

- DataDive roots CSV. **(MCP-generatable; see below.)**
- DataDive Core MKL CSV at `30% Min Rel.`. **(MCP-generatable.)**
- DataDive Expanded MKL CSV at `1% Min Rel.`. **(DOWNLOAD ONLY, not MCP-reproducible.)**
- DataDive competitors CSV or MCP-derived competitor export. **(MCP-generatable.)**
- Ranking Juice snapshot from DataDive MCP in the SEO content JSON.
- POE Products/Search Terms CSVs.
- POE Reviews, Returns, Related Niches, and structured overview JSON.
- Listing reference JSON with product family, ASINs, listing status, title/bullets/description, ingredients, and pack size.

### DataDive: MCP-first, and the full pool needs no UI export at all

Generate **roots**, **Core 30% MKL**, and **competitors** from the DataDive MCP. Do NOT open the browser for them. Validated byte-for-data-identical to the UI exports on a validation run (roots 222/222, Core 257/257, 0 mismatches; a full rebuild from the generated CSVs passed all QA gates with identical Ranking-Juice coverage). See [[datadive-mcp-vs-download]].

**The old "Expanded 1% MKL" was a misnomer and its UI route is retired.** It was never a larger MKL export. The MKL is a capped, curated subset (500 on a capped niche; the frontend warns about a 600 ceiling in one inclusion flow), so lowering Min. Relevancy to 1% does not add rows once the niche is at the cap, and on a capped niche the UI simply cannot reach the tail. Changing that setting is also a `POST /niche_settings/{nicheId}/mkl_okl` that **mutates shared niche state for every teammate**. Do not do it.

Instead pull the **complete keyword pool** with three read-only GETs in the operator's logged-in DataDive session (extension browser), then filter locally:

```
GET https://app.datadive.tools/mkl/{nicheId}?includeAsinCatalog=true   -> data.keywords
GET https://app.datadive.tools/outlier/{nicheId}                       -> data.keywords
GET https://app.datadive.tools/residue-kw-list/{nicheId}               -> data.keywords
```

The three sets are a clean partition with zero overlap, and every row carries the same fields (`keyword`, `searchVolume`, `relevancy`, `cpr8dayGiveaways`, `asinRanks`, `sponsoredAsinRanks`, `amazonUrl`). Merge them and filter `relevancy >= 0.01` for the 1% equivalent, or any other threshold. **No settings change, no Dive tokens, no download-event problem.**

Validated 31.07.2026 on niche `rJdlqdE49c`: 500 + 127 + 2,662 = **3,289 unique keywords**, matching `get_niche_competitors.numKeywords` exactly. Cross-check that equality every run before trusting the merge. Team vault run note: `Runs/2026-07-31-runtime-consolidation-test.md`.

`Update Niche` is the separate re-dive path. It is **not** needed for the tail; treat it as quota-bearing and never trigger it for this workflow.

Procedure (Claude, before the build):
1. Call `get_niche_roots`, `get_niche_keywords`, `get_niche_competitors` for the niche; save each raw JSON response to a file.
2. **Guardrail:** confirm `len(get_niche_keywords.keywords) == get_niche_competitors.numVisibleKeywords` before trusting the Core file. If they diverge, fall back to the UI Core export.
3. Run the generator to write the three contract CSVs:
   ```bash
   .venv/bin/python tools/amazon-seo-keyword-workbook/datadive_mcp_to_csv.py --anchor <ANCHOR> \
     --roots-json <roots.json> --keywords-json <keywords.json> --competitors-json <comps.json> \
     --out-roots "<roots_csv path>" --out-core "<master_csv path>" --out-competitors "<competitors_csv path>"
   ```
Notes: the Core file's `Sugg. bid & range` column is left blank (the builder never reads it; it only matters for PPC builds). `--preflight` marks these three as `(MCP)` rather than `(BROWSER)`, so the browser task only asks for the full keyword pool + POE + listing capture.

Record DataDive export metadata for both Core and Expanded MKL: Min Relevancy, Min SV/Max SV if changed, visible keyword count, visible search volume, export timestamp, niche ID, marketplace, and hero keyword. **Capture these at export time, while the grid is on screen**; do not backfill later.

DataDive UI export locations (so Codex doesn't hunt for them):
- **Roots CSV**: the **Roots** grid's leftmost **Export** tab, for **Normalized Root**.
- **Competitors CSV**: **Niche Tracker > Export Competitors**. Prefer the real UI export over MCP fallback. NOTE: the genuine UI export is TRANSPOSED (attribute rows, one column per ASIN); the builder handles both shapes.
- Core/Expanded MKL: always record Min Rel, visible keyword count, visible search volume, and export timestamp at export time.
- Before fallback or rank injection, confirm the Core MKL has the exact anchor ASIN as a real DataDive column.
- **Anchor not tracked in an existing niche: ADD the ASIN, do NOT re-dive.** When a niche already exists for the product's market but our anchor ASIN is not one of its tracked columns (the usual case for a niche someone dived around competitors), do not spend a full `create_niche_dive`. Instead add just our ASIN to that existing niche so it gains a rank column and the existing roots/MKL/competitor research is reused (≈1 dive token vs ~10, and one niche instead of a duplicate). The DataDive **MCP has no add-ASIN action**, so this is a Codex UI step: DataDive → Niche Tracker → add competitor ASIN → let it re-research; the ASIN then appears in `get_niche_keywords.asinRanks`. Only `create_niche_dive` (spending a full dive, ideally seeded on OUR ASIN) when **no** niche exists for the product yet. Verify with `get_niche_competitors`/`get_niche_keywords` that the anchor is a tracked column after the add, before rank injection. See [[keyword-research-config-scaffolding]].
- **If you do fall back to a UI export, do not trust the download event.** DataDive's export buttons emit no detectable download event in some browser runtimes (confirmed 2026-06-12, still true for Codex on 31.07.2026; the Chrome extension handled it cleanly). Robust pattern: snapshot `~/Downloads`, click Export, then poll for a new `niche-{id}-data*.zip` and validate it by timestamp, size, ZIP members, headers, and row counts. Cross-check against `get_niche_competitors` (`numVisibleKeywords`/`totalSvOfVisibleKeywords` for the visible set, `numKeywords`/`totalSvOfKeywords` for the full pool) before accepting. Prefer the three read-only endpoints above, which avoid this entirely.
- POE inputs come from the API-first downloader: `tools/opportunity-explorer/run-poe.mjs` (`search` → related-niches JSON; `niche` → Products/SearchTerms CSVs + sentiment-labeled CRI + Returns + overview JSON, all builder-ready and locale-independent). One `.de` login covers every EU marketplace (`--origin https://sellercentral.amazon.de --marketplace de|it|es|fr|…`); US uses the `.com` origin. Whoever has the debug Chrome (Claude via CDP, or Codex via internal-browser evaluate of `fetch-poe.js`) can produce these; no manual tab clicking. Capture context (account, marketplace, niche, last-updated) comes from the overview JSON.
- **⚠️ ALWAYS pass `--origin https://sellercentral.amazon.de` for any EU client, on `doctor` too.** `origin` DEFAULTS to `https://sellercentral.amazon.com`, so a bare `run-poe.mjs doctor` reads the account context from the `.com` page and reports whatever account is active there (typically an unrelated US account) even when a `.de` tab is open and the EU client is the selected merchant. It looks like the "wrong account", and the account-safety abort will misfire. The debug Chrome is a **separate profile** from your normal Chrome: switching accounts in your everyday Chrome does nothing; switch the merchant in the port-9222 debug Chrome's account picker, then `doctor --origin https://sellercentral.amazon.de` should report the expected EU merchant, e.g. `<Merchant Name> [partnerAccountId=<partner-account-id>] marketplace=A1PA6795UKMFR9`. Confirmed 2026-07-21. (Note: EU cross-market still uses the `.de` login origin with a different `--marketplace`; do NOT derive origin from the marketplace domain.) POE also requires the account to actually have Opportunity Explorer / Brand Analytics access. If `search`/`niche` hang with an "unsettled top-level await" while `readAccount` succeeds, the account likely lacks OEI access for that marketplace.
- **POE niche selection: Codex picks and pulls, no pause for Claude.** (Operator 2026-07-26.) Once the correct Seller Central account is selected, Codex runs the POE keyword search, takes the closest matching niche itself, and downloads the full set in the same session. Do NOT stop to have Claude choose the niche ID. The account check is the only gate that still blocks; niche choice is not. Report the chosen niche (id + label + T90 SV) and any close runners-up in the handback so Claude can re-pull if the pick was wrong, which is cheaper than a round-trip on every run. If the search returns no plausible niche at all, say so and stop.
- **Saving POE so it actually reaches the workbook.** The POE files only become tabs if they land on the exact `inputs{}` contract paths that `--preflight` prints. Nothing else is read. Six files, six destinations: `poe_products_csv` and `poe_search_terms_csv` are EXACT-PASTE into `POE Raw - Products` / `POE Raw - Search Terms`, so their raw column layout must survive untouched (no reordering, no de-duping, no header edits). `poe_reviews_json`, `poe_returns_json`, `related_niches_json` and `poe_structured_json` are REBUILT into `POE Raw - Reviews`, `POE Raw - Returns`, `POE Raw - Related Niches` and `POE Semantic Insights`. Rename downloads to the contract paths rather than pointing the config at `~/Downloads`. After the files land, re-run `--preflight` and require every POE line to flip to PRESENT before building; a path typo shows up as a silently skipped or placeholder tab, not as an error. Then let the QA gates confirm it: `required_current_tabs`, the POE-tabs-match-current-files gate, and the `stale_data_guard` forbidden-terms sweep together prove the tabs hold this product's data and not the template lineage's.
- POE fallback quirks (manual export only): direct tab URLs render header-only, so click the in-page tab; the Download click works even when the download event times out; check `~/Downloads` and rename to the contract path.
- After Claude accepts the canonical inputs, Codex deletes duplicate/raw intermediate downloads (never the canonical contract paths).
- Sparse POE Review Insights or Returns routes still get a visible JSON capture plus an explicit caveat.
- Listing capture uses the local-language Amazon path and preserves both requested ASIN and resolved ASIN. Flag same-brand sibling redirects and cross-family edge cases.
- Collagen has no authorized EU health claim; flag skin, hair, nails, joints, bones, wrinkles, anti-age, and elasticity terms in live copy.

**Cross-agent:** Codex captures the browser/UI inputs while Claude writes SEO + builds. Codex waits on Claude's handoff with the **`/seo-standby`** command, then writes to the contract paths and stops.

## Delivery Rule

Keyword-research workbooks are delivered to Google Drive only. Do not copy the final workbook to pCloud. Target Drive folder pattern: `Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/<Client> - Shared/<Keyword Research>/<Country>/`. The workbook is a client deliverable, so it belongs inside `<Client> - Shared/`, the one folder the client has access to. Everything outside it is internal (see Google Drive Delivery in `AGENTS.md`). The Keyword Research folder's exact name varies per client (`Keyword Research`, `02 Keyword Research`): list the folder and reuse the existing one, never create a variant. One Keyword Research folder per client, a sub-folder per country, NOT a folder per run. If the client has only one country, the workbook goes directly in that folder. New versions replace the old `.xlsx` in place.

## Workbook Rules

- The template workbook is style only.
- No product-specific tab may be carried forward.
- Rebuild every tab from current sources or generate an explicit skipped/not-exposed row.
- Tab names/order must match the canonical `template_keyword_workbook.xlsx` (= the "(Template) Brand-Country-Product Name Keyword Research" Google Sheet). Point `--template` at that clean template, NOT a previous product workbook. Mismatched scheme-2 tab names were the root cause of silently-skipped/stale tabs.
- Use `3.1 MKL DataDive 30%` for the Core `30%` MKL.
- Use `2.1 MKL DataDive 1%` for the Expanded `1%` MKL.
- Use the Expanded `1%` MKL to generate `2.2 Never KWs`, a sectioned audit tab: Never-Ever single-word negatives (negative-phrase on the root word), competitor brands (campaign-dependent), claim-risk words, a review-manually near-miss band, and phrase-level negative candidates. Every row carries Category, Why, max SV, max relevancy, and example phrases so a human can justify each negative.
- Keep misspellings/grammar variants out of Never Ever when they still represent relevant product intent.
- Keep competitor/brand terms as PPC/context unless the operator explicitly approves another use. In the Never-KWs tab they live in their own section: negative in rank/SKW campaigns, TARGET in PAT/conquest, never blanket negatives.
- Treat disease, cure, laxative, diagnosis, weight-loss, and unsupported health terms as compliance-risk by default.
- Carry `5. Campaign Structure` forward as the empty PPC scaffold from the canonical template (Rank/Shield SKW waves, Long-Tails, Discovery, PAT Stronger/Weaker, Sum formulas, intent legend) so keywords can be filled in there. Do NOT add it to `generated_blank`; that wipes the scaffold. Only populate the campaigns when PPC is explicitly requested, via `fill_campaign_structure.py` (see Campaign Structure Fill below).

## Builder Command

```bash
.venv/bin/python tools/amazon-seo-keyword-workbook/build_keyword_workbook.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>-<product>-<market>.json
```

Use `--preflight` first. If a DataDive `1%` export or metadata is missing, stop and ask for that exact source instead of substituting the `30%` file.

## QA Gates

- Core MKL rows match the `30%` CSV.
- Expanded MKL rows match the `1%` CSV.
- Core and Expanded source paths are distinct.
- The Core MKL has the exact anchor ASIN as a real column (verify this BEFORE any fallback/injection). Same-brand sibling ASINs are listed in `asin_roles.siblings` so they are labelled `Sibling` (not `Competitor`) and excluded from opportunity triage; the anchor is never duplicated in the ASINs tab.
- DataDive export metadata is complete and not placeholder text.
- Never KWs tab is sectioned (Never Ever / brands / claim risk / review band / phrase candidates); word rows are single words; every data row has Category + Why populated (validated).
- Every Never Ever row includes frequency, max SV, max relevancy, and example phrases as written columns.
- POE raw tabs match current files.
- POE Reviews/Returns/Semantic tabs are current product/market data.
- Stale terms from another product, language, or marketplace are absent.
- Health-claim risk terms are not pushed into visible copy automatically.
- No competitor brand tokens (`triage.brand_tokens`) in the SEO Text "New Listing" copy (title/bullets/description/backend). Own brand is allowed; the "Notes / Compliance" column is exempt.
- The SEO Text tab carries the post-2026-07-27 title structure: a `Title (≤75 char — required from 2026-07-27)` row (≤75 chars incl. spaces) **and** an `Item Highlights (≤125 char — from 2026-07-27)` row (≤125 chars, searchable), in addition to the current-rules title kept live until 2026-07-27. Notes live in the separate "Notes / Compliance" column (Col D), never mixed into the copy column. See [[amazon-title-75char-2026]].
- **Item Highlights separator + chip order are gated.** The title takes the spaced en-dash ` – `, the highlights take the spaced middot ` · ` (revised 2026-07-26 from comma); a dash or pipe in the highlights FAILS the build, and a comma inside a chip is allowed. The field is also gated on its ≤125 cap and on adding **incremental** SV over the other searchable fields. Chip 1 is the only chip mobile search reliably shows, so order chips by strength, not by keyword volume. Rules in `skills/amazon-seo/SKILL.md`, reasoning in `skills/amazon-seo/references/seo-writing-methodology.md`.
- `product_facts` block present in config (ingredients + `blend_or_single` + certifications); the builder warns if it is missing and checks completeness when present.
- The ≤75 title **leads with a tracked MKL keyword, not a root**: the title covers at least one Master-List keyword and its lead (non-brand) token exists in the MKL vocabulary. See [[seo-title-ranking-juice-rules]].
- **Ranking-Juice coverage is computed and reported** (covered SV / total + addressable %) in the validation/manifest output. Covered SV must be > 0; a warning fires below 60% addressable. No new workbook tab; the human-facing RJ stays in the SEO-content `rj`/compliance columns.
- **Semantic / Alexa AI direction row present and non-empty**: keeps the semantic layer alive alongside Ranking Juice (the dual objective).
- **Compliance tax reported** when `triage.claim_tokens` exist: claim-gated SV vs addressable SV is a validation row, so the RJ cost of compliance is visible instead of silently deflating the addressable %; recover it via the rewrite ladder in `skills/amazon-seo/references/health-claims-compliance.md`.
- **Regulated-category check reminder**: with `compliance.category_tier: "regulated"` and `compliance.checked` false, the builder warns to run `/health-claims-check` before delivery; `compliance.claims_audit` verdict=`prohibited` terms auto-merge into `triage.claim_tokens`.
- Blend guard: if `product_facts.blend_or_single == "blend"`, the title must not lead with a single ingredient name (warning).
- `1. Root Keywords` columns are `Important | Root Keyword | Frequency | Broad Search Volume | Root Score | Category`. The Important column is the AD-TARGETING signal (operator priority): in tiered mode (`root_importance.ad_min_sv`/`ad_min_score` set) roots get ⭐⭐ when score ≥ ad_min_score AND Broad SV ≥ ad_min_sv AND Category is not Brand/Claim/Form/Off-niche. These seed the SKW/rank campaigns; ⭐ marks relevant-but-below-SV-floor roots. Category uses the same triage tokens + core/POE vocabulary as the Never-Ever ladder. Legacy configs (only `min_score`) keep the old binary ⭐.
- Final workbook style is preserved.
- Manifest and cross-agent handoff note are generated (see Handoff Note Location for where the note lands).

## Handoff Note Location

Every run gets its **own** handoff/protocol note, never appended to one shared cross-client file. You do not have to configure the path: the builder resolves it, preferring the shared team vault so teammates and their agents see the run.

| Condition | Where the note lands |
|---|---|
| `inputs.handoff_note` is set | exactly there (explicit override always wins) |
| Shared vault reachable **and** the client already has a folder | `<team-vault>/Clients/<Client>/Handoffs/<workbook name> Handoff.md` |
| Otherwise | next to the workbook, in the gitignored `output/<client>/seo/` |

The vault root comes from the `AMAZON_AGENT_TEAM_VAULT` env var or `_local/team-vault-path.txt`, and only counts when it actually contains a `Clients/` folder. The note filename inherits the workbook filename, so the version carries over on its own.

The builder never creates a client folder in the shared vault. That vault syncs to every teammate, so a folder invented by a script, or a near-miss spelling next to the real one, is worse than no note. An unmatched client falls back to `output/` and the run warns you to create the client's hub note in the vault first.

The preflight Codex block's `Protocol:` line points at whatever path this resolves to, falling back to the reusable `…/Context/codex-claude-handoff-protocol.md` only when nothing resolves.

## Campaign Structure Fill (on request)

Fill the workbook's `5. Campaign Structure` tab from the built workbook's own data. **VISUAL PLAN
ONLY**: the output is the filled tab plus a Proposed Campaign Names block; pasting into the
bulk-creator webapp is the operator's manual step. Never emit campaign bulk files from this flow.

Preconditions: a built, QA-passed workbook; `_local/ads-strategy/strategy.json` + `strategy.md`
present with no `<placeholders>` (copy from `tools/amazon-seo-keyword-workbook/ads-strategy.TEMPLATE.*`).
The strategy files are proprietary and local-only. Claude refreshes them from the Notion playbooks
listed in the strategy.md header when stale; Codex uses them as-is and asks the operator if missing.
Set `campaign_structure.own_brand_tokens` and `product_name_for_naming` in the client config.

Three phases:

```bash
# 1. mechanical extraction (SV bands, brand/never/claim flags, roots, PAT revenue)
.venv/bin/python tools/amazon-seo-keyword-workbook/fill_campaign_structure.py \
  --config tools/amazon-seo-keyword-workbook/config.<client>.json \
  --extract output/<client>/ads/<date>_campaign_candidates.json

# 2. agent judgment (no script): read candidates.json + _local/ads-strategy/strategy.md; assign
#    keywords/ASINs to scaffold slots per the judgment rules (intent tiers/waves, discovery root
#    specificity, halo theming, PAT strength); write classification.json
#    (schema amazon-agent.campaign-classification.v1)

# 3. validate + write (always dry-run first, show the operator, then apply)
.venv/bin/python tools/amazon-seo-keyword-workbook/fill_campaign_structure.py \
  --config ... --workbook <xlsx> --apply <classification.json> --dry-run
.venv/bin/python tools/amazon-seo-keyword-workbook/fill_campaign_structure.py \
  --config ... --workbook <xlsx> --apply <classification.json>   # writes a .bak first
```

Judgment split: the script enforces SV bands, caps, never/claim/form/brand exclusions, same-root
halo, one-root discovery, dedupe, capacity, and generates campaign names from the local naming
template. The agent decides intent tiers (Wave 1/2/3), which roots are specific enough for
Discovery, halo grouping, PAT Stronger/Weaker when revenue is missing, and review-band promotions,
each with a short "why". A FAIL blocks the save; fix the classification, don't fight the validator.
