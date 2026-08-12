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
8. Read the precomputed Keepa findings from the configured market-signals state file for everything observed since the previous successful weekly run. Four issue types belong to this check: `fba_fee_changed`, `referral_fee_changed`, `package_dimensions_changed`, `package_weight_changed`. Never fetch market data yourself in this check.
   - Confirmation source for a fee change is Amazon's own Referral Fee Preview report (`sc_vla_referral_fee_preview_report_0313`). Fetch it headlessly with `tools/report-fetcher/run.mjs` (`--report inventory --report-type sc_vla_referral_fee_preview_report_0313`). Keepa is the daily tripwire; that report is what settles it.
   - Use Sellerboard only as a confirmation-only second opinion on a specific finding when needed. It never originates a finding.
   - Do not perform a manual Seller Central Fee Preview sample.
   - Coverage limit, state it rather than hide it: Keepa only sees ASINs registered in a profile's `monitoring` block. As of 12.08.2026 that covers 13 of 15 active profiles and 856 ASINs. The two large clothing catalogues (Kabooki DE and JBS DE) are monitored at parent level rather than per variant, so a change on a child variant alone is not seen. An unregistered ASIN is a coverage gap, not a clean account. Report it as a gap.
9. Match every actionable item to an open task using account, marketplace, issue type, and ASIN, shipment ID, or review URL. Update the existing task when matched.

## Completion

Post one compact internal summary with:

- Accounts checked and skipped.
- Clean checks.
- New and updated stock, stranded, shipment, variation, review, fee, package dimension, and package weight findings.
- Accounts or ASINs outside market-signal coverage, named as gaps rather than counted as clean.
- Review rows appended or changed.
- Tasks created or updated.
- Reshipment-planning triggers.
- Shipment-exception tasks and reconciliation eligibility.
- Blockers and stop points.

Never run `amazon-inventory-planning` or submit a shipment reconciliation request as part of this check.
