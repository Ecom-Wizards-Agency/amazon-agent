# SOP Draft: New Client FBA Disposal Prevention Gate

Date: 2026-08-03
Status: ready for review
Owner: Amazon Operations Lead
Related workflow: New client onboarding, FBA inventory controls, removals, stranded inventory, product recalls

## Purpose

Prevent avoidable destruction, liquidation, or uncontrolled removal of a new client's FBA inventory.

This is a mandatory onboarding gate. A client is not considered operationally onboarded until the operator has verified the current inventory state, configured future return settings, reviewed every active removal order, and escalated any required or recall-generated disposal order.

Important limitation: Return-to-seller settings are prospective controls. They do not automatically cancel or convert removal orders that already exist, and they may not override required or recall-generated removals.

## Preconditions

- Seller Central access is active.
- The exact seller account and marketplace are known.
- The client has approved a complete return-to-seller address and phone number.
- The client has named an emergency contact for inventory-loss decisions.
- The operator has permission to update FBA inventory settings.
- The operator understands that changing a setting is not proof that existing inventory is protected.

## Required Inputs

- Seller account name and merchant entity.
- Marketplace or marketplaces in scope.
- Approved return recipient, address lines, city, state or region, postal code, country, and phone number.
- Client decision for refurbishment, grade and resell, liquidation, return, and disposal.
- Current unfulfillable inventory quantities by ASIN, SKU, FNSKU, and disposition.
- Current stranded inventory quantities and auto-removal dates.
- Removal Order Detail data for at least the previous 90 days.
- Removal Shipment Detail data for active or recently completed returns.
- Current product-safety, recall, required-removal, and Account Health notices.

## Onboarding Go/No-Go Gate

All rows must pass before onboarding is signed off.

| Control | Pass condition | Fail condition |
| --- | --- | --- |
| Account and marketplace | Exact client account and marketplace are visibly confirmed | Account or marketplace is ambiguous |
| Unfulfillable settings | Return to seller is selected and the approved address is saved | Dispose or liquidation is enabled without written approval, or address is missing |
| Stranded settings | Return to seller is selected for both stranded-inventory categories | Either category is set to dispose, or address is missing |
| Stranded inventory | Every current row and auto-removal date is reviewed | A row is approaching removal without an owner and action |
| Unfulfillable inventory | Quantities and dispositions are captured and reconciled | Quantities are unknown or only settings were reviewed |
| Removal orders | Every pending, planning, processing, and in-process order is opened and reviewed | Only the report total was checked |
| Recall and required removals | No un-escalated disposal order or recall notice exists | A recall or required disposal exists without same-day escalation |
| Evidence | Screenshots and identifiers are stored in the onboarding evidence pack | Any required proof is missing |
| Second review | Another operator checks the evidence and totals | The same operator is the only reviewer |

Any fail condition makes onboarding status **RED**. Settings can be saved while the onboarding gate remains RED.

## Workflow

### 1. Verify the operating context

1. Open Seller Central.
2. Confirm the exact seller account.
3. Confirm the marketplace.
4. Confirm the interface language and use English when possible.
5. Capture one screenshot showing the account and marketplace.

Repeat this verification after switching marketplaces, accounts, or major Seller Central tools.

### 2. Capture the inventory baseline before changing settings

1. Open Manage unfulfillable inventory.
2. Record each ASIN, SKU, FNSKU, total unfulfillable quantity, and disposition breakdown.
3. Calculate the total unfulfillable quantity.
4. Open Fix stranded inventory.
5. Record the number of products, available units, stranded reason, date of stranded event, and auto-removal date.
6. Open Removal Order Detail and use an exact date range covering at least the previous 90 days.
7. Record every order that is Pending, Planning, Processing, or In process.
8. For each order, record:
   - Removal Order ID.
   - Amazon Order ID when available.
   - Order source.
   - Order type: Return, Disposal, or Liquidation.
   - Date submitted.
   - Requested, completed, cancelled, and pending quantities.
   - Whether the Cancel control is available.
   - ASIN, SKU, FNSKU, and item-level quantities.
9. Open Removal Shipment Detail for any active return shipment and record tracking status.
10. Review product-safety, recall, required-removal, Performance Notification, and Account Health notices that could trigger mandatory inventory action.

Do not proceed from settings alone. Existing orders and notices are separate controls.

### 3. Configure unfulfillable-inventory protection

1. Open Amazon fulfillment inventory settings for Unfulfillable inventory.
2. Set the removal channel to **Return to seller**.
3. Enable refurbishment only when the client approves it and the categories are appropriate.
4. Keep Liquidation and Dispose off unless the client gives written approval for those channels.
5. Select the client-approved schedule. When no client preference exists, use the safest available interval that preserves intervention time and document the selection.
6. Enter the complete approved return address and phone number.
7. Save.
8. Reopen the page and verify the saved summary, selected channel, schedule, and address.

### 4. Configure stranded-inventory protection

1. Open Amazon fulfillment inventory settings for Stranded inventory.
2. Keep automatic relist and automatic change-to-FBA settings at the approved values.
3. For inventory stranded due to account status:
   - Select Return to seller.
   - Use the maximum approved inventory age, up to the marketplace limit.
4. For inventory stranded due to listing or inventory issues:
   - Select Return to seller.
   - Use the maximum approved inventory age, up to the marketplace limit.
5. Enter and verify the same approved return address.
6. Save.
7. Reopen the page and verify both removal channels, both ages, and the address.

Current US reference values verified in Seller Central on 2026-08-03 were 60 days maximum for account-status issues and 30 days maximum for listing or inventory issues. Re-verify limits in the live marketplace instead of assuming they are universal.

### 5. Reconcile settings against current stock

1. Sum all current unfulfillable quantities.
2. Sum quantities already tied to Return, Disposal, or Liquidation orders.
3. Calculate uncovered units:

   `current unfulfillable units - units in active removal orders = uncovered units`

4. Reconcile the difference by ASIN and FNSKU.
5. Confirm whether uncovered units are eligible for the next automatic return cycle.
6. Do not describe a schedule date as a guaranteed delivery date.
7. Do not promise a 30-day grace period for inventory already in a removal order.

### 6. Detect a recall or required-disposal emergency

Treat any of the following as a same-day stop-the-line event:

- Order type is Disposal.
- Order source includes Automated Recalled Units Removal System.
- A product-safety or recall notice requires removal.
- Cancel is disabled even though the order is Pending.
- Disposed quantity is increasing.
- A new disposal order appears after Return-to-seller settings were saved.
- The client did not authorize disposal.

When triggered:

1. Keep onboarding status RED.
2. Capture the full order-detail page and report row.
3. Record the first observed timestamp and all unit counts.
4. Notify the internal owner and client emergency contact immediately.
5. Open an urgent Seller Support case through the removal-order shipment or investigation path.
6. Ask for an immediate hold, cancellation, conversion to Return to seller, and escalation to the FBA removals or recall team.
7. Recheck the disposed and pending counts after the case is created and at each agreed monitoring interval.

Return settings may not override a required or recall-generated disposal. Never present the setting change as proof that the current order is protected.

### 6.1 Confirm a successful cancellation

Seller Support may be able to cancel an Amazon-generated recall disposal even when the Seller Central Cancel control is disabled. Do not treat the support-case status, a canceled callback, or a verbal statement alone as proof that the inventory is protected.

Use the removal-order detail page as the authoritative confirmation. A complete cancellation must show:

- Status is **Merchant Cancelled**.
- Cancelled quantity equals the full ordered quantity.
- Disposed quantity is **0**.
- Pending quantity is **0**.

If any quantity remains pending or disposed, keep onboarding RED and continue the escalation. Save the removal-order page, support case ID, timestamp, and item-level reconciliation in the approved client evidence location.

### 7. Route Seller Support correctly

Use these identifiers for an existing Amazon-generated removal order:

- Removal Order ID.
- Amazon Order ID when visible.
- ASINs, SKUs, FNSKUs, and quantities.
- Order source, type, date, and status.

Choose the support path for investigating a removal order shipment or reimbursement issue.

Do not choose **batch inventory removal request** unless the seller actually submitted a bulk removal request and Seller Central provides a numeric Batch ID. An Amazon-generated Removal Order ID is not a Batch ID and must not be altered to fit a numeric field.

Do not use catalog-only specialist categories such as Reserved Inventory when no removal-order specialist category is offered. A wrong category can delay escalation during the only intervention window.

### 8. Complete the second-person review

The reviewer must independently confirm:

- Account and marketplace.
- Unfulfillable total.
- Stranded total.
- Removal-order totals and types.
- Return settings and address.
- Stranded settings and ages.
- Recall and required-removal notices.
- Every active order's cancelability.
- Any difference between current stock and quantities already in removal orders.
- RED, AMBER, or GREEN onboarding status.

The reviewer signs the checklist with name, date, and time. A screenshot without a written reconciliation is not sufficient.

### 9. Monitor after onboarding

1. Recheck removal orders and product-safety notices daily for the first seven calendar days after account access is granted.
2. Recheck unfulfillable and stranded inventory after each setting change.
3. Continue the removal-order, stranded-inventory, and returns checks in the weekly operational review.
4. Escalate any new Disposal order on the same business day.
5. Keep the client emergency contact and approved return address current.

## Stop-Before-Risk Points

- Do not enable Dispose or Liquidation without written client approval.
- Do not clear or replace a return address without confirming the exact recipient.
- Do not create or confirm a removal order without explicit approval.
- Do not submit a cancellation, support case, or escalation until the outbound text and identifiers are reviewed by the operator.
- Do not sign off onboarding while a disposal order, recall notice, quantity mismatch, or missing address remains unresolved.
- Do not claim that Amazon will return inventory merely because Return to seller is selected.
- Do not use a placeholder Batch ID or convert an alphanumeric Removal Order ID into a number.

## Evidence And Screenshots Needed

- Seller account and marketplace header.
- Unfulfillable inventory settings summary after save.
- Stranded inventory settings after save.
- Complete return address as displayed in settings.
- Manage unfulfillable inventory totals and disposition breakdown.
- Fix stranded inventory product count and auto-removal dates.
- Removal Order Detail report for the selected date range.
- Detail page for every active removal order.
- Order type, source, status, requested, completed, disposed, cancelled, and pending quantities.
- Enabled or disabled state of the Cancel control.
- Relevant recall, required-removal, Performance Notification, and Account Health notices.
- Written reconciliation of total unfulfillable units versus units in active removal orders.
- Second-review signoff.

Do not store client identifiers, addresses, screenshots, or reports in this SOP draft. Store account-specific evidence in the approved onboarding evidence location.

## Source Docs/SOPs Used

- Current Seller Central US UI verification on 2026-08-03: unfulfillable settings, stranded settings, Fix stranded inventory, Manage unfulfillable inventory, Removal Order Detail report, and recall-generated removal-order detail.
- Amazon Seller Help: FBA inventory, `G201074410`.
- Amazon Seller Help: Required Removals, `202000820`, linked from the cancellation guidance.
- `MAG SOPs/catalog/catalog-sop-fba-removal-order.md`.
- `MAG SOPs/catalog/catalog-sop-how-to-cancel-fba-removal-order.md`.
- `MAG SOPs/catalog/logistics-sop-how-to-generate-a-removal-order-detail-report.md`.
- `MAG SOPs/catalog/troubleshooting-sop-stranded-inventory-inventory-error.md`.

The MAG procedures informed the operating steps. Current Seller Central UI evidence controls where the captured SOPs differ from the live workflow.

## Open Questions Or Assumptions

- Confirm whether the onboarding owner should be the account manager, Amazon operations lead, or a named inventory specialist.
- Confirm the default unfulfillable removal schedule when a client has not stated a preference.
- Confirm the required notification channel and service-level target for a RED disposal event.
- Confirm whether every client must name a backup return address.
- Confirm whether the first-seven-days daily check should become an automated operational-review configuration.
- Marketplace limits and UI labels must be verified live. The US 30-day and 60-day limits are not assumed to apply globally.

## Promotion Notes

After review:

1. Promote this gate into the master new-client onboarding checklist used by the team.
2. Add a required RED/AMBER/GREEN inventory-control signoff to onboarding ownership.
3. Add the first-seven-days removal-order check to the operational-review setup for new clients.
4. Train operators on the difference between Removal Order ID, Amazon Order ID, and Batch ID.
5. Review all currently managed FBA clients against this gate as a one-time remediation sweep.
6. Keep the review evidence client-specific and outside the tracked SOP source tree.
