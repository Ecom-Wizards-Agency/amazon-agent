---
name: amazon-fba-inventory-planning
description: "Build fresh FBA inventory overviews and reshipment plans from same-day Seller Central data; use Amazon Logistics to execute shipments or removals."
---

# Amazon FBA Inventory Planning

Browser: Mixed (connected Amazon MCP/SP-API is the default data path; use CDP only for missing MCP fields, login/account verification, or historical UI investigation).

Use this skill for recurring or ad hoc FBA inventory overview and reshipment planning. It owns the former "Weekly FBA Inventory Overview" automation workflow.

## When To Use

- Weekly FBA Inventory Overview.
- Reshipment / send-stock planning.
- Inventory overview CSV/XLSX generation.
- Excess inventory / plan-sales identification.
- FBA Inventory, Restock, Inventory Report, and Business Report collection for planning.

Trigger phrases include `Weekly FBA Inventory Overview`, `reshipment planning`, `FBA inventory planning`, `inventory overview`, and plain requests for an inventory check or reshipment check.

## Required Reference

Read `references/weekly-fba-inventory-overview.md` before running the weekly workflow or recreating its instructions.

Use the local planner as the source of truth for parsing and calculations when available:

`<your-projects>/fba-reshipment-planner`

Important planner files:

- `src/utils/parsers.ts`
- `src/utils/calculations.ts`
- `src/types.ts`

## Core Rules

- Resolve each brand-market's shared team-vault `Amazon Ops.md` profile before calculating. Use its reshipment settings and product exclusions through `tools/client-profiles/find-client-profile.mjs`; never copy stable target, lead-time, booking-buffer, scaling, threshold, or FBM-exclusion values into a local run config.
- Use the connected Amazon MCP/SP-API as the default source for reshipment planning when it provides the required same-day inventory, inbound, reserved, aged/excess, and 30-day demand fields. Do not open Seller Central merely to repeat data already available through MCP.
- Verify every MCP result belongs to the Ops Manager account and marketplace selected for the run and record its freshness timestamp. If a required field is unavailable or stale, use the narrowest Seller Central report/browser fallback for that field only. Never substitute older local files, cached output, or a previous run unless the operator explicitly approves the exception in the current chat.
- For any CDP report-fetcher fallback, pass both `--marketplace <code>` and `--expect-account "<Seller Central Name>"`. Abort on a mismatch before fetching. Never rely on the session-default seller when the login contains multiple accounts.
- Business Report units ordered for the last 30 days are the primary demand source.
- FBA Inventory 7-day and 30-day shipped units are context/trend fields.
- Restock sold30 is fallback/supporting signal only where the planner uses it.
- Save final deliverables outside SOP/help folders, normally under `output/{client}/inventory/` with dates in filenames. `{client}` is the normalized lowercase-kebab client slug from `AGENTS.md`, with marketplace in filenames, not folder names.
- Stop before client-facing Slack sends, destructive Downloads cleanup, or any account-changing Seller Central action.
- If the shared profile is missing, incomplete, or not enabled for reshipment planning, stop for that account instead of falling back to generic local defaults.
- The former automation does not need to be reactivated to run this workflow; use this skill and reference file as the source of truth.

## Output

For each brand-market, produce:

- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].csv`
- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].xlsx`
- Raw report files moved to the account's pCloud raw report folder after final approval when needed, with dates in filenames.
- Slack staging copy for internal `#amazon` when actionable items exist.
