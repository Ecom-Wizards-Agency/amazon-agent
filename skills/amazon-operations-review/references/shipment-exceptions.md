# FBA Shipment Exceptions

Use this as a lightweight weekly monitor. `amazon-logistics` owns investigation, reconciliation, support cases, and shipment changes.

## Scope

In the Shipping Queue, review:

- Open and inbound FBA shipments.
- Recently delivered, checked-in, receiving, or closed shipments that changed since the previous successful weekly run.
- Known open shipment findings and reconciliation cases.

Amazon normally moves shipments through `In transit`, `Delivered`, `Checked in`, `Receiving`, and `Closed`. Do not flag one of these statuses merely because it exists.

## Actionable Exceptions

Create or update one `shipment-exception` task when at least one condition is visible:

- Amazon displays `Action required`, an error, a warning, or investigation eligibility.
- The carrier and Seller Central conflict, such as carrier-delivered while Amazon still shows an earlier state after Amazon's displayed receiving or delivery window has passed.
- A ship-by date, delivery estimate, appointment, or other Amazon-displayed deadline has passed without the expected progress.
- Tracking is missing, inactive, rejected, or otherwise flagged by Amazon.
- Expected and received units differ after the shipment is closed or Amazon marks the contents eligible for reconciliation.
- Units marked damaged or defective are not included in Amazon's credited received quantity, produce a discrepancy, or carry an actionable warning or investigation option.
- Amazon or an open reconciliation case requests documents, clarification, or a reply.

Do not invent a fixed delay threshold. Use Amazon's displayed dates, warnings, and eligibility state. Treat normal receiving within Amazon's displayed window as clean.

## Damaged Or Defective Units

Check damaged or defective indicators when they are visible in shipment contents, but use the received count as the decision rule:

- If Amazon still counts the affected units as `Received` and shows no `Action required`, discrepancy, investigation eligibility, or other actionable warning, record the shipment as clean. Do not create a task merely because a damaged or defective label is visible.
- If the condition reduces the credited received quantity or produces an actionable discrepancy, create or update the shipment-exception task.
- Do not treat recurring product-quality complaints as a shipment discrepancy. Those belong in the monthly returns and Voice of the Customer review.

## Finding Contract

Record only visible, decision-relevant fields:

- Account and marketplace.
- Shipment name and shipment ID.
- Current Seller Central status and last visible update.
- Carrier status and tracking reference when shown.
- Shipped, expected, and received units when relevant.
- Damaged or defective units and whether Amazon still included them in the received count.
- Amazon-displayed deadline, receiving window, warning, discrepancy, or eligibility state.
- Existing case ID and latest requested action when present.
- Recommended next step and required evidence.

Deduplicate using account, marketplace, shipment ID, and issue type. Update the open task when status, discrepancy, deadline, or requested evidence changes.

## Stop Point

The weekly check may open shipment details and the Contents tab read-only. Stop before:

- Selecting discrepancy classifications.
- Uploading invoices, packing slips, proof of delivery, or other documents.
- Previewing or submitting a research request.
- Replying to or opening a support case.
- Changing, canceling, or confirming a shipment.

Route approved follow-up to `amazon-logistics`. Use first-party Amazon shipment status and reconciliation guidance first, then the MAG FBA shipment-reconciliation SOP for practical steps.
