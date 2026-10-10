---
id: KC-0202
title: "Variation child is search suppressed and shows only a packshot: check whether its main image carries a text label, badge or tag"
kind: diagnosis
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [DE]
marketplace_inferred: false
surface: "Seller Central > Inventory > Manage All Inventory (Search Suppressed status); product detail page"
surface_verified: false
symptom_keywords: ["[\"child ASIN search suppressed main image\", \"main image label not allowed\", \"badge on main image not going live\", \"supply badge main image rejected\", \"child shows only packshot not optimized images\", \"main image hangtag search suppressed\"]"]
error_text: ["Search Suppressed"]
asked_as: ["A client opened the single-pack child of a variation family and saw only a plain packshot instead of the optimized gallery, while a multi-pack sibling with the same style of main image displayed corre"]
synonyms: []
resolution_status: partial
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/153-product-image-guide-G1881.md"]
related_sops: ["MAG SOPs/catalog/troubleshooting-sop-how-to-fix-search-suppressed.md"]
supersedes: []
contradicts: []
observed: 2024-11
review_by: 2027-10
provenance: "ledger:KC-0202"
---

## Question

A client opened the single-pack child of a variation family and saw only a plain packshot instead of the optimized gallery, while a multi-pack sibling with the same style of main image displayed correctly. The child turned out to be search suppressed, and the client suspected the label added to the main image. In a separate account the team also could not get main images carrying "N-month supply" badges to reflect and removed the badges.

## Answer

When a variation child shows only a packshot or drops out of search, check whether it is search suppressed and read the stated reason. If the main image carries a label, badge, supply callout or readable tag, it likely breaks the main image rule: only the product on a white background, with no text or graphics. Amazon may suppress the listing until a compliant main image is uploaded. Replace the main image with a clean version and move the callout to a secondary image. Do not rely on a sibling ASIN that was accepted with the same label.

## Cause

Not confirmed in the thread: nobody read or quoted the suppression reason. The likely mechanism is the main image rule. Amazon main images allow no text, logos, borders, color blocks, watermarks or other graphics on the product or in the background, and Amazon may suppress a listing from search until a compliant main image is provided. The client suspected the label on this child's main image. A sibling ASIN with a similar label was accepted, so enforcement looked uneven and one accepted child does not prove compliance.

## Fix

1. In Manage All Inventory, filter for Search Suppressed listings and open the affected child to read the stated reason.
2. Compare the live main image with the main image requirements in the Product image guide; look for text, badges, quantity or supply callouts, borders or color blocks.
3. Upload a clean main image (product only, pure white background, no text or badges) to the affected child, and move any quantity or supply message into a secondary image.
4. Ask the brand owner to forward Amazon suppression emails so image rejections are caught early.
5. Recheck the child after the image refresh window and confirm the suppression is cleared and the full gallery shows.

## Verify

The child no longer appears under Search Suppressed in Manage All Inventory, and its detail page shows the full image gallery with the new main image.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/153-product-image-guide-G1881.md`
- Also in: `MAG SOPs/catalog/troubleshooting-sop-how-to-fix-search-suppressed.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Ties a search-suppressed variation child showing only a packshot to a text label or supply badge on its main image, and warns that an accepted sibling with the same label does not prove compliance.
- Existing coverage: full (`MAG SOPs/catalog/catalog-sop-a-b-test-main-image.md`, `Amazon Seller Help/articles/153-product-image-guide-G1881.md`).
