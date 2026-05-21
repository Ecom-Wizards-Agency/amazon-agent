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

## Required Reference

Read `references/weekly-fba-inventory-overview.md` before running the weekly workflow or recreating its instructions.

Use the local planner as the source of truth for parsing and calculations when available:

`/Users/victoruhl/Documents/New project/fba-reshipment-planner`

Important planner files:

- `src/utils/parsers.ts`
- `src/utils/calculations.ts`
- `src/types.ts`

## Core Rules

- Business Report units ordered for the last 30 days are the primary demand source.
- FBA Inventory 7-day and 30-day shipped units are context/trend fields.
- Restock sold30 is fallback/supporting signal only where the planner uses it.
- Save final deliverables outside SOP/help folders.
- Stop before client-facing Slack sends, destructive Downloads cleanup, or any account-changing Seller Central action.

## Output

For each brand-market, produce:

- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].csv`
- `YYYY-MM-DD_Inventory Overview_[Brand]_[Market].xlsx`
- Raw report files moved to the account's dated pCloud raw report folder after final approval when needed.
- Slack staging copy for internal `#amazon` when actionable items exist.
