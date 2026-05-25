# Weekly FBA Inventory Overview

This reference replaces the long paused automation prompt for `weekly-fba-reshipment-planner` / "Weekly FBA Inventory Overview".

## Scope

Default account order:

1. Swissker US
2. Ilapharm FR
3. Piercing XXL DE
4. JBS DE

Do not include Sondur, Goda, or AlphaInfuse unless Victor explicitly expands the scope. JBS DE is expected to need custom adjustments; if its override rules are unknown, process files but ask Victor before finalizing or posting JBS output.

## Channel Rules

Post only in the internal Slack `#amazon` staging channel for review:

- Channel id: `C0AR1699WMQ`
- Do not post to client channels unless Victor explicitly approves a client-channel send after reviewing the staging output.
- If a future run is client-facing and the client channel is unknown, skip that brand and ask Victor at the end.

## Browser And Login Rules

For this workflow, use the teammate's preferred connected browser with an existing Seller Central session unless Victor says otherwise. If desktop-control tools are available, use them to operate the connected browser. If browser automation is unavailable, pause and ask which connected browser/session to use.

Never interact with 1Password, password managers, credential vaults, passkeys, OTP/2FA fields, CAPTCHA, or credential autofill prompts. If login, password, passkey, OTP, CAPTCHA, or 1Password action is required, pause and ask Victor to complete it manually.

Keep the connected browser set to auto-download into Downloads. Do not rename files inside browser Save dialogs. Let files land in Downloads, classify each download by headers/content, and do final file management after reports are downloaded, calculations are done, and Slack text is ready.

## Planner Source Of Truth

Use the local planner whenever possible:

`/Users/victoruhl/Documents/New project/fba-reshipment-planner`

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

## Default Planning Settings

Use unless Victor gives account-specific overrides:

| Setting | Value |
| --- | --- |
| `targetDaysOfStock` | 45 |
| `productionDays` | 0 |
| `transitDays` | 7 |
| `amazonBookingDays` | 14 |
| `scalingMultiplier` | 1.0 |
| `reportDays` | 30 |
| `minimumMonthlyThreshold` | 100 |
| `groupMode` | child ASIN |

## Seller Central Reports

For each account, switch Seller Central account via `/account-switcher/default/merchantMarketplace` and select the correct account/container and marketplace.

Fresh-report requirement:

- Start every run by requesting/downloading new reports for the selected account and marketplace. Do not use archived local reports, cached planner outputs, previous Downloads files, or any older "latest available" report as the basis for a new reshipment plan unless Victor explicitly approves that exception in the current chat.
- Treat "latest reports" as same-day reports from the current run. Match the report requested/generated date to the run date and verify the browser header account/marketplace before downloading and before calculation.
- If Seller Central shows only older reports, request a new report in the UI and wait until it is ready. If Amazon cannot generate a same-day report, pause and summarize the blocker for that account instead of substituting older data.
- For US/EU timezone differences, use the Seller Central visible requested/generated date plus the local download timestamp as evidence. If the marketplace date appears one day behind because of Amazon timezone behavior, note that explicitly in the operator summary and keep the newly requested/downloaded file isolated from older files.

Gather:

- FBA Inventory: `/reportcentral/MANAGE_INVENTORY_HEALTH/1`, reportId `19600`
- Restock Report: `/reportcentral/RestockReport/1`, reportId `94300`
- Inventory Report: `/listing/reports/ref=xx_invreport_favb_xx` or `/listing/api/status/inventory-reports`
- Business Report: `/business-reports/ref=xx_sitemetric_dnav_xx#/report?id=102:DetailSalesTrafficByChildItem`, last 30 days

If Amazon blocks programmatic Business Report download, pause and ask Victor or the teammate to click Download, then use the newest `BusinessReport-MM-DD-YY.csv` or completed temporary browser CSV from Downloads for the current account.

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

Use one inventory overview parent thread per brand-market in `#amazon`. Parent title:

`BRAND Inventory Overview - Country`

Examples:

- `Swissker Inventory Overview - US`
- `Piercing XXL Inventory Overview - Germany`

Only create a Slack thread if at least one section has actionable items. If there are no send-stock items and no excess-inventory items, skip Slack.

Thread replies:

1. `Reshipment`: only ASINs whose status is send-stock and reshipment quantity is greater than zero. Each line starts with the ASIN in backticks, then a short product name, then `- X units needed | Available: A | Inbound: I | Reserved: R`. Final line is the total.
2. `Excess Inventory / Plan Sales`: products needing sales planning, including available/excess/aged stock and days of cover where available.

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
