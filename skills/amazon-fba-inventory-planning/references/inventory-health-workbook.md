# Optional Inventory Health Workbook

Use this reference when the operator requests a broader inventory-health workbook in addition to the standard overview and reshipment plan. It is an output layer, not a replacement calculation model.

## Source Precedence

The normal planning contract remains authoritative:

1. same-day inventory, inbound, reserved, aged, excess, and fee fields from the selected Amazon account;
2. Business Report units ordered over the last 30 days as the primary demand source;
3. FBA shipped-unit and Restock measures as context or documented fallback;
4. target, lead-time, booking-buffer, scaling, threshold, and exclusion settings from the client's shared `Amazon Ops.md` profile.

Do not introduce generic 30, 60, or 75-day planning targets when the client profile supplies the actual settings. Do not use an older export because it has more columns.

## Suggested Tabs

1. **Read Me & Data Watermark:** account, marketplace, source names, requested/generated timestamps, date windows, currency, settings source, exclusions, and known missing fields.
2. **Inventory Overview:** one row per ASIN/SKU with available, inbound, reserved, unfulfillable, aged, excess, 30-day demand, days of cover, effective coverage target, and proposed reshipment.
3. **Send Stock:** positive reshipment rows only, preserving the standard planner result.
4. **Excess, Age & Fees:** Amazon-estimated excess, age bands, storage or low-inventory-level fee indicators when present, and the evidence date. Missing fields remain blank and disclosed.
5. **Action Ledger:** issue, ASIN/SKU, evidence, proposed action, owner, urgency, approval status, and notes. This tab records recommendations only and never implies execution.
6. **Source Data:** normalized source rows and join keys sufficient to reproduce every output row.

## Rules

- Keep FBM-only and excluded products visible in the overview with zero FBA recommendation and the exclusion reason.
- Separate available, inbound, reserved, and unfulfillable units. Do not collapse them into one undocumented stock number.
- Use Amazon's provided age, excess, and fee fields as evidence. Do not recreate a fee from memory when the source supplies it.
- Do not mix inventory planning with the lightweight monthly operational-check schedule. The workbook may consume the same evidence, but `amazon-fba-inventory-planning` owns reshipment calculations.
- Reconcile source ASIN/SKU keys to workbook rows and identify every unmatched or duplicated key.
- Apply the standard client-brand and native Google delivery rules when the workbook is client-visible.
