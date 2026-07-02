---
name: amazon-campaign-builder
description: Use to create Amazon Sponsored Products campaigns from a plain-text brief — parses the brief into a per-client config and builds a bulk-upload .xlsx (SKW/Halo/BMM/Phrase/Auto/PAT, EW naming convention, paused by default). File-only output; uploading or any AdLabs push stays a separate operator-confirmed action.
---

# Amazon Campaign Builder (SP campaigns from text)

Use this when the operator asks to create/build/set up Sponsored Products campaigns ("create SKW campaigns for these keywords", "build me an auto + PAT set for this SKU", "make the launch campaigns as a bulk file"). It ports the Ecom Wizards Amazon Ads Bulk Creator app's generation logic into a repo-native, config-driven builder.

## Source of truth

1. **Toolkit:** `tools/amazon-campaign-builder/` — `campaign_model.py` (pure logic) + `build_campaigns.py` (CLI). See its `README.md`, `NEW-CLIENT.md`, `WORKFLOW.md`.
2. **Bulksheet format:** the toolkit emits Amazon's documented bulksheets-2.0 vocabulary (sheet `Sponsored Products Campaigns`, `Dynamic bids - down only`, `negativeExact`, `asin-expanded=`, …) — the README's "Format fixes" table records where it deliberately deviates from the web app.

## The config contract

Copy `tools/amazon-campaign-builder/config.TEMPLATE.json` → `config.<client>-<market>.json` (gitignored). Required per campaign spec: `campaign_type` (SKW/Halo/BMM/Phrase/Auto/PAT), `product_name`, `sku[]` (sellers) or `asin[]` (vendors), and `keywords[]` (or `target_asins[]` for PAT). Naming defaults to `Goal | SP | MatchType | ProductName | TargetDescriptor | EW`; add `Counter` when a spec fans out into several campaigns.

## Flow

1. **Parse the brief.** Extract client, marketplace, SKUs/ASINs, campaign types, keywords/target ASINs, budgets, bids, negatives, portfolio, start date, state.
2. **Ask once for what's missing** (AskUserQuestion): marketplace/account, SKUs, budget + bid, paused vs enabled, portfolio, negatives. Never carry another client's values.
3. **Scaffold the config** and run `build_campaigns.py --config <cfg> --preflight` until READY.
4. **Preview** (`--preview`) and show the operator the planned campaigns + combined daily budget. Adjust until it matches intent.
5. **Build** (`--config <cfg>`) → `output/<client-slug>/ads/<date>_<Brand>_<Market>_SP_bulk_campaigns.xlsx` + `_REVIEW.md`; the QA gates must PASS.
6. **Hand off the file + review and stop.** Upload is the operator's move.

## Rules

- **File-only output.** The toolkit never uploads or touches live campaigns. Uploading the bulk file, enabling campaigns, changing live bids/budgets, or any AdLabs `create_entities` push is stop-before-risk: it needs the operator's explicit instruction for that specific action in the current chat, or a matching `_local/local-permissions.md` standing permission.
- **Paused by default.** `state: enabled` only when the operator explicitly asks; preflight flags it (campaigns go live the moment Amazon processes the upload).
- **AdLabs push variant:** for AdLabs-managed accounts the operator may ask to push instead of upload — that follows the `amazon-adlabs-audit` write policy verbatim (explicit per-write lift in the current chat, batch-by-batch what-will-change summary, tags). Build the file first anyway; it is the reviewable artifact.
- **Never hand-edit the builders per client** — everything client-specific lives in the config. If the code can't express something, extend the toolkit, not a fork.
- SP only in v1. SB/SD requests: say so and fall back to the `amazon-ads` skill / manual console flow (the row builders are channel-keyed for a later SB/SD port).
