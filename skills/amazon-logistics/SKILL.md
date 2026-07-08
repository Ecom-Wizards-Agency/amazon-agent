---
name: amazon-logistics
description: Use for executing Amazon FBA and inventory operations: Send to Amazon, FBA shipments, shipment reconciliation, AWD, removal orders, returns, inventory health, reserved inventory, seller-fulfilled shipping settings, and logistics troubleshooting. For the Weekly FBA Inventory Overview or reshipment planning use amazon-inventory-planning.
---

# Amazon Logistics

Browser: Codex interactive (Send to Amazon flows; stop before creating/confirming shipments).

## Workflow

1. Confirm account, marketplace, SKU/ASIN list, quantities, shipment IDs, destination, and dates.
2. Search Amazon Seller Help first for FBA, inventory, shipping, AWD, and return rules.
3. Search internal notes for account-specific inventory or supply-chain context.
4. Use MAG logistics/catalog SOPs for practical Seller Central steps.
5. Capture warnings, placement options, fees, labels, shipment IDs, and reconciliation states.
6. Stop before confirming shipments, buying labels, submitting placement/shipping choices, creating removal orders, or changing shipping settings.

## AWD/FBA Eligibility Precheck

Before creating or editing an AWD shipment, reconcile the intended shipment list against Seller Central data. Do not assume that a SKU in a packing list, inventory report, or AWD search result is eligible to send to AWD.

Use fresh Seller Central reports when available:

- All Listings Report.
- Inventory Report.
- Amazon-fulfilled Inventory Report.
- Planning workbook or packing list.

Compare:

- Intended shipment SKUs from the planning file.
- All Listings Report fulfillment channel, such as `DEFAULT` or `AMAZON_NA`.
- Amazon-fulfilled Inventory Report presence.
- Existing FBA/AWD-selectable SKUs visible or accepted in Seller Central.
- Alternate SKU forms, such as `BASESKU` vs `BASESKU-FBA`.

Classify each SKU before browser entry:

- `AWD/FBA ready`: appears as Amazon-fulfilled or is accepted in the AWD flow.
- `Likely FBM only`: exists in listings but fulfillment channel is merchant/default.
- `Needs FBA setup`: not accepted by AWD and not Amazon-fulfilled.
- `Mapping required`: base SKU and FBA SKU differ and carton/SKU reconciliation is needed.
- `Overlap risk`: already planned for FBA and also selected for AWD.

Build a reconciliation summary with:

- Total intended AWD SKUs.
- Count already FBA/AWD ready.
- Count likely FBM only.
- Count missing or rejected by AWD.
- Count overlapping with the FBA plan.

Hard stop: do not add AWD quantities for SKUs that overlap with the FBA shipment plan unless the operator explicitly approves sending one carton to FBA and another carton to AWD.

If most intended SKUs are `DEFAULT` or merchant fulfilled, recommend enabling or creating FBA offers before retrying AWD. Prefer converting or reusing the existing base SKU when safe; create separate `BASESKU-FBA` variants only when conversion is not possible or the account intentionally uses separate FBM/FBA SKU architecture.

If Amazon AWD only shows a subset of SKUs, treat that as an eligibility signal, not proof that the visible SKUs are the correct ones to send.

In the AWD UI, distinguish row-level actions from shipment workflow actions:

- Row-level `Ready to send` adds that SKU to Step 1's ready list after reconciliation.
- Main `Confirm and continue` advances the shipment workflow and remains a stop-before-risk action.

Known AWD UI quirk: after typing a box quantity, Amazon may not calculate units until the number field is nudged with the up/down control and returned to the intended value. Verify that units calculate before treating the row as ready.

Keep this workflow GitHub-safe. Do not commit downloaded reports, planning files, client names, shipment IDs, addresses, screenshots, or account-specific SKU lists. Use generic examples such as `BASESKU`, `BASESKU-FBA`, `DEFAULT`, and `AMAZON_NA`.
