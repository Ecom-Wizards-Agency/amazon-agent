# Weekly FBA Inventory Overview

This reference replaces the long paused automation prompt for `weekly-fba-reshipment-planner` / "Weekly FBA Inventory Overview".

## Scope

Default account order:

1. Acme US
2. Initech FR
3. Example Brand DE
4. Hooli DE

Do not include Globex, Umbrella, or Stark unless the operator explicitly expands the scope. Hooli DE is expected to need custom adjustments; if its override rules are unknown, process files but ask the operator before finalizing or posting Hooli output.

## Channel Rules

Post only in the internal Slack `#amazon-check` channel for review:

- Channel id: `<slack-channel-id>` (the real id lives in the local reshipment config, not in this file)
- Send through `~/Automations/wizards-ai/slack.sh` as Wizards AI. Do not use a personal Slack identity or the Slack connector for posting.
- Do not post to client channels unless the operator explicitly approves a client-channel send after reviewing the staging output.

## Browser And Login Rules

Use the connected Amazon MCP/SP-API as the default source for reshipment planning. The browser is a fallback for fields the MCP does not provide, account/login verification when needed, and narrow historical investigations such as tracing a specific receipt or shipment. Do not open or switch Seller Central accounts merely to repeat data already available through MCP.

Never interact with 1Password, password managers, credential vaults, passkeys, OTP/2FA fields, CAPTCHA, or credential autofill prompts. If login, password, passkey, OTP, CAPTCHA, or 1Password action is required, pause and ask the operator to complete it manually.

Keep the connected browser set to auto-download into Downloads. Do not rename files inside browser Save dialogs. Let files land in Downloads, classify each download by headers/content, and do final file management after reports are downloaded, calculations are done, and Slack text is ready.

## Planner Source Of Truth

Use the local planner whenever possible:

`<your-projects>/fba-reshipment-planner`

Prefer planner behavior over prompt formulas and over any hosted website. Key files:

- `src/utils/parsers.ts`
- `src/utils/calculations.ts`
- `src/types.ts` for `DEFAULT_SETTINGS`

## Demand Source Rule

Follow the GitHub/local planner rule:

- Business Report units ordered for the last 30 days are the main demand source for 30-day velocity and reshipment calculations.
- FBA Inventory 7-day and 30-day shipped units are used for trend ratio and inventory-context fields.
- Restock sold30 is only a fallback/supporting signal where the planner uses it for missing FBA detail.
- If Business Report units and FBA/Restock sold30 differ, prefer Business Report units for demand.

## Shared Planning Settings

Resolve every account's team-vault `Amazon Ops.md` profile before calculation. The profile supplies target stock days, lead time, Amazon booking buffer, scaling multiplier, minimum monthly FBA threshold, and any FBM-only exclusions. Effective coverage days are derived by the lookup tool as target + lead time + booking buffer.

Do not use a generic local default when the profile is missing, incomplete, or disabled. Stop that account and report the exact missing setting. `reportDays` remains a run input, normally 30; group mode remains child ASIN.

## Account-Specific FBA Eligibility

- Read `agent_safety_notes`, `recurring_workflow_notes`, and the structured reshipment fields from the shared team-vault profile before calculation.
- Apply product-level FBM-only exclusions before calculating or posting FBA reshipment quantities.
- Some accounts keep bundles and multipacks, including 2-pack, 3-pack, and 4-pack offers, on FBM by policy. Where the shared profile says so, never recommend, include, or send those offers to FBA.
- Report titles can omit pack-count wording, so title text alone is not sufficient. Apply the structured `fba_exclude_patterns` plus `fba_exclude_asins` from the shared profile. Exact ASIN exclusions take precedence over report text.
- Do not duplicate either exclusion list in the local run config.
- Excluded products remain visible in the full inventory workbook with `FBA Eligibility` labeled `FBM only - bundle/multipack` and zero FBA reshipment units.

## Seller Central Reports

For each account, switch Seller Central account via `/account-switcher/default/merchantMarketplace` and select the correct account/container and marketplace.

Fresh-data requirement:

- Start every run with a fresh same-day MCP/SP-API pull for the selected Ops Manager account and marketplace. Record the source freshness timestamp. Do not use archived local reports, cached planner outputs, previous Downloads files, or an older "latest available" result unless the operator explicitly approves that exception in the current chat.
- Use Seller Central reports only for required fields that are missing or stale in MCP. Match any fallback report's requested/generated date to the run date and verify the browser account/marketplace before downloading and calculating.
- When using `tools/report-fetcher/run.mjs`, always pass the requested `--marketplace` and the exact Ops Manager `Seller Central Name` through `--expect-account`. The command must abort before fetching if either the regional host or seller account is wrong.
- If neither MCP nor Seller Central can provide a required same-day field, pause and summarize the blocker for that account instead of substituting older data.
- For US/EU timezone differences, use the Seller Central visible requested/generated date plus the local download timestamp as evidence. If the marketplace date appears one day behind because of Amazon timezone behavior, note that explicitly in the operator summary and keep the newly requested/downloaded file isolated from older files.

Gather:

- FBA Inventory: `/reportcentral/MANAGE_INVENTORY_HEALTH/1`, reportId `19600`
- Restock Report: `/reportcentral/RestockReport/1`, reportId `94300`
- Inventory Report: `/listing/reports/ref=xx_invreport_favb_xx` or `/listing/api/status/inventory-reports`
- Business Report: `/business-reports/ref=xx_sitemetric_dnav_xx#/report?id=102:DetailSalesTrafficByChildItem`, last 30 days

If Amazon blocks programmatic Business Report download, pause and ask the operator or the teammate to click Download, then use the newest `BusinessReport-MM-DD-YY.csv` or completed temporary browser CSV from Downloads for the current account.

## Deliverables

Generate one CSV and one XLSX per brand-market with:

- Full Inventory Overview sheet.
- Reshipment / Send Stock Only sheet.
- Excess Inventory / Plan Sales sheet if supported by downloaded reports, using Amazon estimated excess quantity, aged inventory, and/or high days-of-cover indicators.

Save final files as:

- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].csv`
- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].xlsx`

Save in the account's pCloud Inventory Planning folder.

## Raw Download Cleanup

After CSV/XLSX files are generated and Slack text is ready, move raw report downloads for each run out of Downloads into the account's raw report folder:

`Inventory Planning/Raw Reports/`

Rename raw files in the final file-management batch:

`YYYY-MM-DD_[Brand]_[Market]_[Report Type].[csv/txt]`

Keep duplicate downloads only when they clearly belong to the run and label with suffixes like `_duplicate 1` or `_duplicate 2`. Do not touch unrelated Downloads files.

## Slack Staging Format

Use one inventory overview parent thread per brand-market in `#amazon-check`. This is preferred over one combined all-client thread because each account remains easy to scan, copy, link, and share. Parent title:

`BRAND Inventory Overview - Country`

Examples:

- `Acme Inventory Overview - US`
- `Example Brand Inventory Overview - Germany`

Create an individual brand-market thread only when it has at least one positive reshipment quantity. Do not create an individual thread for an account with zero reshipment units, even if it has excess inventory.

The thread contains separate flat replies in this exact order:

1. `*How it was calculated*`: state the same-day sources and the formula. Demand is Business Report units ordered over 30 days. Required units = `(30d demand ÷ 30) × scaling multiplier × effective coverage days`. Reshipment = round up `max(0, required units - available - inbound - reserved)`. State that FBA 7d/30d and Restock data are validation/fallback context.
2. `*Reshipment*`: the copy-ready list. Include only ASINs with a positive reshipment quantity. Each line starts with the ASIN in backticks, then a short product name, then `- X units needed | Available: A | Inbound: I | Reserved: R`.
3. Show the 10 highest-quantity reshipment rows. If more exist, add `Plus N more low-volume rows in the workbook.` Then add `Total: X units`.
4. `*Excess Inventory / Plan Sales*`: always a separate reply when actionable. Never combine excess units with the reshipment reply. Show the 6 highest excess rows, note the remaining count, and add the total.

Do not replace the account threads with aggregate replies such as `Run status`, `Send stock`, `Completed safely`, or cross-account totals. Slack is for the per-account copyable list. Put blockers, scope summaries, and login notes in the Codex task unless they directly qualify an account's source line.

After the individual reshipment threads, create one short channel parent for all included accounts with zero positive reshipment quantities:

```text
*No reshipment needed for:*
• Brand 1 Market
• Brand 2 Market
```

Use real Slack line breaks, not escaped `\n` text. Post this parent through `tools/reshipment/post_slack_no_reshipment.py` so formatting is preserved.

Do not include blocked, incomplete, excluded, or unverified accounts in this list. They belong in the Codex task summary.

Client-channel delivery is v2 and is not active. Until Victor explicitly approves v2, post only to `#amazon-check`.

Shorten product names aggressively so the differentiator is visible in Slack.

If Slack file upload is available, attach the XLSX to the parent thread. If file upload is not available, skip the attachment rather than blocking the run.

## Finish Summary

Finish with:

- Files saved.
- Raw Downloads files moved to pCloud and renamed.
- `#amazon` staging threads posted or skipped.
- Any skipped attachment.
- Any accounts skipped.
- Any channel confirmations needed.
- Any manual actions still needed.
