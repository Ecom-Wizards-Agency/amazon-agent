---
id: KC-0001
title: "FBA hazmat review blocks a battery-powered kit with a cosmetic liquid: battery exemption sheet plus SDS, and an SDS declaration form when the SDS brand does not match"
kind: diagnosis
topic: compliance
status: draft
skills: [amazon-regulated-product-appeals]
marketplaces: [US]
marketplace_inferred: false
surface: "Seller Central > FBA Compliance Dashboard (dangerous goods classification, SDS and exemption sheet upload); Send to Amazon; Seller Support case"
surface_verified: false
symptom_keywords: ["hazmat review battery kit", "FBA_INB_0008 batteries", "SDS brand does not match detail page", "battery exemption sheet upload", "cannot send battery product to FBA"]
error_text: [FBA_INB_0008, "Additional information about the batteries is required in order to complete the Hazmat review process.", "The product brand in the SDS on file does not match the product brand on the detail page", FBA_INB_0181]
asked_as: ["A new battery-powered beauty device sold as a kit with a cosmetic liquid could not be sent to FBA."]
synonyms: ["Gefahrgut", "dangerous goods review", "hazmat"]
resolution_status: resolved
fix_source: amazon-support
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: ["MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md"]
supersedes: []
contradicts: []
observed: 2026-02
review_by: 2027-10
provenance: "ledger:KC-0001"
---

## Question

A new battery-powered beauty device sold as a kit with a cosmetic liquid could not be sent to FBA. Shipment creation through a 3PL returned FBA_INB_0008 ('Additional information about the batteries is required in order to complete the Hazmat review process.'). The client asked whether to sell FBM in the meantime.

## Answer

A battery-powered device sold with a personal-care liquid will go through a dangerous-goods review before FBA accepts it. Upload a signed and dated battery exemption sheet (watt-hours, voltage) and an SDS for the liquid through the FBA Compliance Dashboard. The SDS brand must match the detail-page brand exactly; if the manufacturer's SDS shows another brand, submit Amazon's SDS declaration form instead of the same SDS again. Keep six-sided packaging photos ready, budget hazmat storage fees, check expiry dates against the 105-day FBA minimum, and keep FBM as the fallback while classification is pending.

## Cause

The ASIN went into dangerous-goods (hazmat) review because it combines a battery-powered device with a personal-care liquid. Amazon needed battery information through the battery exemption sheet and an SDS for the liquid. The first SDS was rejected because the brand on the SDS did not match the brand on the detail page.

## Fix

1. Open a Seller Support case. Amazon's answer points to the FBA Compliance Dashboard (sellercentral.amazon.com/fba/compliance-dashboard).
2. Download the region-specific battery exemption sheet from the dashboard. Fill in watt-hours and voltage from the battery or packaging, plus the mandatory Date and 'Prepared by' fields. Upload it against the ASIN. Amazon states a review time of 2 business days.
3. If the ASIN is not selectable in the dashboard yet, upload the sheet manually and tie it to the ASIN. Keep the sheet in Excel: its dropdowns are lost when it is imported into Google Sheets.
4. Answer Amazon's follow-up request with six-sided product photos (hazard statements, pictograms, ingredient list, barcode) and an SDS for the liquid component.
5. If the SDS is rejected with 'The product brand in the SDS on file does not match the product brand on the detail page', submit Amazon's SDS declaration form instead. Prepare one declaration for the liquid alone and one for the kit as a whole. Submission needs operator approval.
6. After acceptance, expect hazmat storage fees slightly above standard-size. Before creating the shipment, check the batch expiry date against FBA_INB_0181 (expiration date at least 105 days out). Keep FBM as the fallback for a short-dated batch.

## Verify

The SDS declaration was accepted and the product could be sent to FBA. The batch on hand then failed the 105-day expiry rule and was sold FBM.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: The SDS declaration form as the fallback for a brand mismatch, the FBA_INB_0008 text, the six-sided photo follow-up and the 105-day expiry interaction are not in the existing SOP.
- Existing coverage: partial (`MAG SOPs/catalog/troubleshooting-sop-sds-upload-hazmat-issues.md`).
- Confidence is medium, not high: the fix comes from one thread, no first-party capture is cited, and the MAG SOP matches only part of the mechanism (SDS and exemption-sheet upload, the SDS matching the listing).
