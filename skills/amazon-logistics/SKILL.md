---
name: amazon-logistics
description: "Execute and troubleshoot FBA logistics, including Send to Amazon, shipment reconciliation, AWD, removals, returns, and reserved inventory."
---

# Amazon Logistics

Browser: CDP (Send to Amazon flows; exact approval is required before each shipment commitment).

## Workflow

1. Confirm account, marketplace, SKU/ASIN list, quantities, shipment IDs, destination, and dates.
2. Search Amazon Seller Help first for FBA, inventory, shipping, AWD, and return rules.
3. Search internal notes for account-specific inventory or supply-chain context.
4. Use MAG logistics/catalog SOPs for practical Seller Central steps.
5. Capture warnings, placement options, fees, labels, shipment IDs, and reconciliation states.
6. Before confirming shipments, buying labels, submitting placement or shipping choices,
   creating removal orders, or changing shipping settings, obtain the operator's explicit
   approval for that exact action and reviewed payload in the current chat, or verify a
   matching scoped permission in `_local/local-permissions.md`.
7. Immediately before the approved action, re-verify the account, marketplace, SKUs,
   carton and unit counts, ship-from address, expiration dates, fees, placement, ship
   mode, and carrier. If the final screen introduces or changes a material term, stop for
   new approval. After acting, capture the resulting workflow or shipment identifier and
   status.

## Send to Amazon (FBA) Shipment Creation

Verified against the live UI on 01.09.2026. Order matters: check the freight setting before
entering quantities, and check the placement lever before confirming Step 1.

**Start from the client's carton registry, not from unit counts.** The shared team-vault
`Amazon Ops.md` reshipment block carries `carton_units` (ASIN → units per carton),
`carton_specs` (SKU, dims, weight, which saved packing template to use), and `short_names`.
Plan and communicate in whole boxes ("send 10 boxes"), convert to units only for entry
fields that need it, and round shipment quantities up to full cartons. When the registry is
missing for an account, recover it from Amazon before asking the client: a past shipment's
**Carrier updates tab shows per-box weight and dimensions** (carrier-measured), and
units-per-box = the shipment's contents units ÷ its box count. Write newly confirmed carton
data back to the vault profile in a supervised session.

**Never trust a saved packing template's units-per-box blindly.** Templates are
operator-entered and can contradict the physical cartons (on 01.09.2026 the MM3.5OZ
template said 100/box while the real carton holds 60, proven by carrier-measured boxes).
Cross-check the template against the vault registry or a past shipment before committing a
row; prefer creating a correctly named new template over reusing a wrong one.

**Expiration dates default to the SKU's most recent shipment.** Read them from the prior
Send to Amazon workflow (shipment page → "Send to Amazon (view)" → Step 1's View shows
per-SKU `Expiration date`). Reuse those values unless the operator or client states a new
batch; exceptions are possible, so name the source ("reused from FBA…") in the operator
note. Some SKUs track no expiration; their rows commit without one.

**A fresh workflow arrives with "I want to ship with Amazon Global Logistics" already
checked.** Uncheck it for any shipment moving on the client's own carrier, before entering
quantities. Left checked, it routes the freight through Amazon instead of the forwarder.

**The quantity column is Boxes, not units.** Amazon computes units from the packing
template. Read the computed units back before continuing: entering a unit count here
silently multiplies it by the units-per-box.

**Step 1 does not count a SKU until its row is committed.** Fill boxes and the expiration
date where required, then click that row's `Ready to send`. `SKUs ready to send` stays at 0
and `Confirm and continue` stays disabled until every intended row is committed. The
checkbox at the left of the row is a bulk-apply control, not the gate. This mirrors the AWD
row-level behaviour described below.

**Read the barcode type from Send to Amazon, not from Manage Inventory.** The row shows
either `Manufacturer barcode` or `Unit labels required`. An FNSKU that matches the ASIN in
Manage Inventory is not proof of manufacturer barcode, and getting this wrong sends the
warehouse a split labeling instruction for part of one shipment.

**Packing template error `Provide prep category information`** usually means the template's
`Who labels units?` is unset. Setting it clears the error and unlocks the row's Boxes field.

**Placement fees: check the 5-carton rule before confirming Step 1.** Amazon-optimized and
Partial shipment splits require at least five cartons of *every* item in the plan. If any
format falls below five cartons the plan drops to Minimal Splits and pays the placement
fee. Rebalancing so each format has five or more cartons can hold total cartons and total
bottles constant while moving the placement fee to zero. On a roughly 50-carton shipment
this has been worth several hundred dollars. Compare the options before confirming, and
raise the rebalance with the operator when a format sits just below five.

**Carrier and ship mode are set at Step 2 and are painful to change afterwards.**

- For a freight forwarder that is not in Amazon's carrier list, choose `Other`.
- Amazon requires one carrier across all small-parcel shipments in a plan, so the choice
  applies to every destination at once.
- Small parcel needs a tracking ID per box. LTL needs one document per shipment. Confirm
  which the forwarder can actually supply before choosing, because a plan with many boxes
  can mean dozens of tracking numbers.
- Keep the carrier consistent across legs of the same consignment.

**Box labels.** Set the label format per shipment, then anchor the print action on the
shipment ID rather than on proximity to the format dropdown: proximity matching downloads
the same shipment repeatedly while reporting success. Verify every PDF's page count against
that shipment's box count before delivering, and check the page size matches the requested
label stock. Thermal 4×6 UPS SPD labels run 2 pages per box (FBA box label + UPS shipping
label), so pages = 2 × boxes; the house stock is thermal 4×6 unless the operator says
otherwise.

**Archive labels + packing plan in pCloud after creation** (client convention, e.g. Evora
Body and Svens Island): `1_Delivery/1.1_Clients/<Client>/_Data/inventory/` with one label
PDF per shipment named
`YYYY-MM-DD_<Client>_<Market>_FBA-Box-Labels_<Mode>_<n>-<FC>_<ShipmentID>_Thermal-4x6_v1.pdf`
plus one `YYYY-MM-DD_<Client>_<Market>_Carton-Packing-Plan_<Mode>_v1.xlsx`. The packing
plan workbook carries: header block (ship-from, carrier, ship date, delivery window),
destinations table with per-SKU carton counts per shipment (verified against each
shipment's contents page; whole cartons only), a carton breakdown (SKU, ASIN, EAN,
units/carton, size, weight, expiration), and warehouse packing instructions (one SKU per
carton, 2 label pages per numbered box, barcodes uncovered, prepaid handoff).

**Multi-destination splits.** When the per-destination SKU table will not render, the split
can be derived from each destination's carton count and unit count, since units per carton
differ per format. Only use the result when each destination has exactly one integer
solution and the totals reconcile to the known per-format carton counts. Label it as
derived rather than read from Amazon.

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
