---
name: amazon-campaign-builder
description: Use to create Amazon Sponsored Products campaigns from a plain-text brief or a keyword-research workbook, or to update/pause/archive existing SP campaigns from a downloaded bulksheets export. Trigger on requests like create SKW campaigns for these keywords, build campaigns from this brief, build campaigns from this keyword workbook, pause these keywords, raise this campaign's budget, archive this campaign, or `/create-campaigns`. Create mode builds a bulk-upload .xlsx (paused by default); update mode builds a real-ID Update/Archive/Create .xlsx against an existing account. File-only output; uploading or any AdLabs push stays a separate operator-confirmed action.
---

# Amazon Campaign Builder (v2: SP create + update)

Browser: None (file-only build; any upload is a separate operator-confirmed Codex interactive action).

Use this when the operator asks to create/build/set up Sponsored Products campaigns ("create SKW campaigns for these keywords", "build me an auto + PAT set for this SKU", "make the launch campaigns as a bulk file", "build campaigns from this keyword workbook"), **or** to change existing live campaigns ("pause these keywords", "raise this campaign's budget to $30", "archive this old campaign", "add these negatives to this ad group"). It ports the Ecom Wizards Amazon Ads Bulk Creator app's generation logic into a repo-native, config-driven builder, plus a new update-mode with no web-app equivalent.

## Source of truth

1. **Toolkit:** `tools/amazon-campaign-builder/`: `campaign_model.py` + `build_campaigns.py` (create), `keyword_workbook.py` (keyword-file input), `update_model.py` + `update_campaigns.py` (update). See its `README.md`, `NEW-CLIENT.md`, `WORKFLOW.md`.
2. **Bulksheet format:** the toolkit emits Amazon's documented bulksheets-2.0 vocabulary (sheet `Sponsored Products Campaigns`, `Dynamic bids - down only`, `negativeExact`, `asin-expanded=`, …). The README's "Format fixes" table records where it deliberately deviates from the web app. `references/bulksheets-2.0-reference.md` is the authority for Update-row semantics (blank-means-unchanged exceptions, immutable fields, archive cascades).
3. **Naming:** `_local/ads-strategy/naming-convention.md` (LOCAL ONLY): the EW 8-slot naming convention and per-purpose bidding table, ported into `campaign_model.py`'s EW preset and `CAMPAIGN_PURPOSE_BIDDING`.

## Create mode: the config contract

Copy `tools/amazon-campaign-builder/config.TEMPLATE.json` → `config.<client>-<market>.json` (gitignored). Required per campaign spec: `campaign_type` (SKW/Halo/BMM/Phrase/Auto/PAT), `product_name`, `sku[]` (sellers) or `asin[]` (vendors), and `keywords[]` (or `target_asins[]` for PAT). Set `campaign_purpose` (`SHIELD`/`SELF_TARGETING`/`CATEGORY`) only when intent cuts across the type (e.g. an own-brand SKW campaign). Naming defaults to the **EW preset** (`Goal | Ad Type | Match Type | Trigger Words | Product Identifier | Keyword | Camp Counter | Suffix`); set `naming.preset: "LEGACY"` for the pre-v2 order. Alternative to hand-filling `campaigns[]`: `--keyword-file <workbook.xlsx>` sources it from a keyword-research workbook's "5. Campaign Structure" tab (or a generic flat sheet). Unvalidated against a real client workbook: double-check via `--preview`.

### Create flow

1. **Parse the brief (or note the keyword workbook path).** Extract client, marketplace, SKUs/ASINs, campaign types, keywords/target ASINs, budgets, bids, negatives, portfolio, start date, state.
2. **Ask once for what's missing**, in a single scoping message: marketplace/account, SKUs, budget + bid, paused vs enabled, portfolio, negatives. Never carry another client's values.
3. **Scaffold the config** and run `build_campaigns.py --config <cfg> [--keyword-file <wb>] --preflight` until READY.
4. **Preview** (`--preview`) and show the operator the planned campaigns + combined daily budget. Adjust until it matches intent.
5. **Build** (`--config <cfg>`) → `output/<client-slug>/ads/<date>_<Brand>_<Market>_SP_bulk_campaigns.xlsx` + `_REVIEW.md`; the QA gates must PASS.
6. **Hand off the file + review and stop.** Upload is the operator's move.

## Update mode: the change-set contract

Copy `tools/amazon-campaign-builder/config.UPDATE.TEMPLATE.json` → `config.UPDATE.<client>-<market>.json`. Requires `export_file` (a bulksheets download of the "Sponsored Products Campaigns" tab: the **only** valid source of real IDs, never the console UI or a remembered ID) and a `changes{}` block describing the intended edits. Every ID in `changes{}` must be copied verbatim from that export.

### Update flow

1. **Get a fresh export** from the operator (or download one yourself if you have access). It must cover every campaign/ad group/keyword/target in scope.
2. **Scaffold the change-set** from the operator's request, sourcing every ID from the export.
3. **Preflight** (`update_campaigns.py --config <cfg> --preflight`) until READY. Catches unresolved IDs, invalid enums, disallowed end-date clears.
4. **Preview** (`--preview`): a plain-English line per planned change (and per skip); show the operator.
5. **Build** (`--config <cfg>`) → `..._SP_bulk_UPDATE.xlsx` + `_REVIEW.md`; QA gates must PASS.
6. **Hand off and stop.** Remind the operator: **read the `_REVIEW.md` before uploading**. Update-mode rows act on real, currently-serving entities; there's no paused-by-default safety net like create mode. A fresh export is needed before any subsequent update batch.

## Rules

- **File-only output.** The toolkit never uploads or touches live campaigns. Uploading the bulk file, enabling campaigns, changing live bids/budgets, or any AdLabs `create_entities`/update push is stop-before-risk: it needs the operator's explicit instruction for that specific action in the current chat, or a matching `_local/local-permissions.md` standing permission.
- **Paused by default (create mode only).** `state: enabled` only when the operator explicitly asks; preflight flags it (campaigns go live the moment Amazon processes the upload). Update mode has no equivalent default: its rows already act on live entities, so the `_REVIEW.md` is the safety mechanism instead.
- **AdLabs push variant:** for AdLabs-managed accounts the operator may ask to push instead of upload. That follows the `amazon-adlabs-audit` write policy verbatim (explicit per-write lift in the current chat, batch-by-batch what-will-change summary, tags). Build the file first anyway; it is the reviewable artifact.
- **Never hand-edit the builders per client.** Everything client-specific lives in the config/change-set. If the code can't express something, extend the toolkit, not a fork.
- **Keyword/Match-Type/Product-Targeting-Expression are immutable** in update mode: "changing" one is always Archive-old + Create-new, never an Update to the text. Negatives can only be archived, never paused.
- SP only. SB/SD requests: say so and fall back to the `amazon-ads` skill / manual console flow (the row builders are channel-keyed for a later SB/SD port).
- Run `python3 tools/amazon-campaign-builder/selftest.py` after any code change to the toolkit: it must stay green.
