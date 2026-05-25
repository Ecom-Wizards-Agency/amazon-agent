---
name: amazon-inventory-planning
description: Use for Amazon FBA inventory planning and reshipment planning, especially the Weekly FBA Inventory Overview workflow: downloading Seller Central inventory/business/restock reports, applying the local FBA reshipment planner calculations, creating CSV/XLSX inventory overview outputs, organizing pCloud raw reports, and preparing Slack staging summaries.
---

# Amazon Inventory Planning

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

`/Users/victoruhl/Documents/New project/fba-reshipment-planner`

Important planner files:

- `src/utils/parsers.ts`
- `src/utils/calculations.ts`
- `src/types.ts`

## Core Rules

- Always download fresh Seller Central reports for the current run before planning. "Latest reports" means reports requested/generated today for the selected account and marketplace; do not base a new reshipment plan on older local files, cached output, or previously downloaded reports unless Victor explicitly approves that exception in the current chat.
- Verify every input report belongs to the selected account/marketplace and today's run before calculation. If a report page only offers an older report, request a new report and wait/download it; if Amazon cannot provide a same-day report, pause and report the blocker instead of silently using older data.
- Business Report units ordered for the last 30 days are the primary demand source.
- FBA Inventory 7-day and 30-day shipped units are context/trend fields.
- Restock sold30 is fallback/supporting signal only where the planner uses it.
- Save final deliverables outside SOP/help folders, normally under `output/{client-or-brand}/inventory/` with dates in filenames.
- Stop before client-facing Slack sends, destructive Downloads cleanup, or any account-changing Seller Central action.
- The former automation does not need to be reactivated to run this workflow; use this skill and reference file as the source of truth.

## Output

For each brand-market, produce:

- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].csv`
- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].xlsx`
- Raw report files moved to the account's pCloud raw report folder after final approval when needed, with dates in filenames.
- Slack staging copy for internal `#amazon` when actionable items exist.
