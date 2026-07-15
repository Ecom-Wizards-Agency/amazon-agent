# New Client: Campaign Builder Onboarding

Checklist to build campaigns for a new client/brief, or to prepare an update batch for an
existing client's live campaigns. No code changes, only a new config (or change-set).

## Create mode: new campaigns

### 1. Scaffold the config

```bash
cp tools/amazon-campaign-builder/config.TEMPLATE.json \
   tools/amazon-campaign-builder/config.<client>-<market>.json
```

Never carry another client's values (the config-scaffolding rule: the anchor SKUs/ASINs are exactly what the operator gives, no leftovers).

Fill from the operator's brief:

- **`client`, `brand`, `marketplace`, `amazon_account`**: basics; `brand`+`marketplace` drive the output filename.
- **`vendor_central_mode`**: vendors advertise by ASIN (SKU column left blank); sellers by SKU.
- **`naming`**: defaults to the **EW preset** (8-slot: `Goal | Ad Type | Match Type | Trigger Words | Product Identifier | Keyword | Camp Counter | Suffix`, `naming-convention.md`). Set `naming.preset: "LEGACY"` only if the operator explicitly wants the pre-v2 6-token order. `Camp Counter` auto-appears only for Halo/Auto (nothing to configure for that). Fan-out (SKW without keyword-in-name, or `transpose_keywords`) needs a disambiguating token in `variable_order`; preflight will insist if one's missing.
- **`defaults`**: `state` stays `paused` unless the operator explicitly asks for `enabled` (preflight prints a live-on-upload note if so). `start_date` empty = today. Placement percentages are whole numbers; 0 = no Bidding Adjustment row.
- **`campaigns[]`**: one entry per campaign spec from the brief. Minimum per entry: `campaign_type`, `product_name`, `sku` (or `asin` for vendors), and `keywords[]` (or `target_asins[]` for PAT). Everything else falls back to the campaign-type defaults or `defaults{}`. Set `campaign_purpose` (`SHIELD`/`SELF_TARGETING`/`CATEGORY`) only when the campaign's intent cuts across its `campaign_type` (e.g. an own-brand SKW campaign is `campaign_type: SKW, campaign_purpose: SHIELD` and gets Down-only bidding instead of Rank SKW's Fixed bid).

Alternative to hand-filling `campaigns[]`: pass a keyword-research workbook instead.
```bash
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> --keyword-file <workbook.xlsx> --preflight
```
Set `keyword_file_defaults.product_name`/`.sku`/`.asin` in the config first (the workbook doesn't carry those). See `README.md`'s "Keyword-file input" section. This path is unvalidated against a real client workbook, so double-check the parsed `campaigns[]` (via `--preview`) before building.

### 2. Ask before assuming

If the brief doesn't say, ask the operator (one AskUserQuestion round): marketplace/account, SKUs to advertise, budget + bid, campaign types wanted, portfolio, negatives, start date, paused vs enabled.

### 3. Preflight → preview → build

```bash
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> --preflight
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg> --preview   # show the operator
python3 tools/amazon-campaign-builder/build_campaigns.py --config <cfg>             # build + QA gates
```

Present the `--preview` output (or the built `_REVIEW.md`) to the operator before treating the file as final.

### 4. Hand off and stop

The deliverable is the `.xlsx` + `_REVIEW.md` under `output/<client-slug>/ads/`. Uploading it (Campaign Manager → Bulk Operations) is the operator's action, or a separately-confirmed agent action per the stop-before-risk rule. Never upload, push via AdLabs, or enable campaigns as part of this workflow.

## Update mode: changing existing campaigns

### 1. Get a fresh bulksheets export

Ask the operator (or, if you have console/AdLabs access, do it yourself) to download a
bulksheets export of the "Sponsored Products Campaigns" tab covering the campaigns/ad
groups/keywords/targets in scope (Bulk Operations → create/download a spreadsheet). This is
the **only** valid source of real IDs for update mode. The console UI's displayed IDs are
not guaranteed to match bulksheets IDs.

### 2. Scaffold the change-set

```bash
cp tools/amazon-campaign-builder/config.UPDATE.TEMPLATE.json \
   tools/amazon-campaign-builder/config.UPDATE.<client>-<market>.json
```

Set `export_file` to the downloaded path. Fill `changes{}` from the operator's request.
Every ID (`campaign_id`, `ad_group_id`, `old_keyword_id`, etc.) must be copied verbatim from
the export, never invented or remembered from a prior session. Leave `allow_end_date_clear`
false unless the operator explicitly wants to clear an existing end date.

### 3. Preflight → preview → build

```bash
python3 tools/amazon-campaign-builder/update_campaigns.py --config <cfg> --preflight
python3 tools/amazon-campaign-builder/update_campaigns.py --config <cfg> --preview   # show the operator
python3 tools/amazon-campaign-builder/update_campaigns.py --config <cfg>             # build + QA gates
```

### 4. Hand off and stop

The deliverable is the `.xlsx` + `_REVIEW.md`. **Read the `_REVIEW.md` before uploading.**
Unlike create mode, this file changes a live account the moment it's processed; there is no
paused-by-default safety net. Uploading it is the operator's action, or a separately-
confirmed agent action per the stop-before-risk rule.
