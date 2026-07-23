# Weekly Operational Check

Run accounts in the configured stable regional order. Re-check open weekly findings before discovering new ones.

## Per-Account Sequence

1. Verify login, Seller Central account label, marketplace, page, and current filters.
2. Check Inventory Dashboard low-stock alerts. Open Restock Recommendations only to validate or add context to the same stock exception. Do not create two findings for the same ASIN.
3. Create or update a `reshipment-planning` task when Amazon shows a current low-stock or positive restock recommendation. Record ASIN, SKU, available, inbound, reserved, days of supply, and Amazon recommendation when visible. Do not download the full planning report set or calculate shipment quantities.
4. Check Stranded Inventory and update one finding per account-marketplace and ASIN.
5. Follow `shipment-exceptions.md` to check open, recently received, and reconciliation-eligible FBA shipments. Review exceptions only; do not reconcile every healthy shipment.
6. Review only new variation alerts, suppressed or inactive children, and known open variation findings. Do not inspect every healthy family. Route repairs to `amazon-catalog`.
7. Follow `review-tracking.md` for new 1- and 2-star reviews.
8. Read SellerSonar fee, dimension, and weight alerts since the previous successful weekly run. Use Sellerboard only to confirm a specific alert when needed. Do not perform a manual Fee Preview sample.
9. Match every actionable item to an open task using account, marketplace, issue type, and ASIN, shipment ID, or review URL. Update the existing task when matched.

## Completion

Post one compact internal summary with:

- Accounts checked and skipped.
- Clean checks.
- New and updated stock, stranded, shipment, variation, review, and fee findings.
- Review rows appended or changed.
- Tasks created or updated.
- Reshipment-planning triggers.
- Shipment-exception tasks and reconciliation eligibility.
- Blockers and stop points.

Never run `amazon-inventory-planning` or submit a shipment reconciliation request as part of this check.
