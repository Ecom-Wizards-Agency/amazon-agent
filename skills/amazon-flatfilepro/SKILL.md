---
name: amazon-flatfilepro
description: "Update existing Amazon listings directly through the FlatFilePro connector (copy, attributes, MAIN and PT images); prepare, upload and map narrow FlatFilePro workbooks for what it cannot write; run authenticated secondary-image bulk requests."
---

# Amazon FlatFilePro

Browser: Mixed (direct update, connector reads and preparation need no browser; workbook upload, column mapping and image baselines use the logged-in FlatFilePro CDP session).

Use this skill for the complete FlatFilePro workflow while keeping preparation and browser mapping as explicit modes.

## Modes

- `secondary-images`: the Grimoire and Slack route. Use the existing `wizards-ai/listing_images.py` and `listing_image_jobs.py` pipeline. A concrete authenticated team request authorizes the exact batch for a current managed-ready client. Resolve eligibility from the Amazon Ops registry and verify FlatFilePro seller/marketplace bindings automatically. The image workflow contract is `wizards-ai/docs/bulk-listing-images-setup.md`. No per-account pilot, source URL allowlist or release-ledger approval is required. Preserve MAIN, swatches, unspecified slots, complete requested batch coverage, immutable revisions/assets and independent processing/publication/protected-field checks. Existing submitted operation IDs reconcile without resubmission.
- `direct-update`: the attended default for any edit the connector's `flatfilepro_update_listing_on_amazon` can express on an existing listing, at any number of SKUs: copy, backend terms, structured attributes, MAIN and PT01 to PT09 images. Live Amazon read before and after every write, a hashed batch the operator approves, one recorded write per SKU, and verify. Read `references/direct-update-mode.md`; it lists what stays on the workbook route.
- `prepare`: build a narrow SKU-keyed `.xlsx` from current values plus label, packaging, or approved copy evidence. In an attended session the current values come from the FlatFilePro connector's verified export grid (`references/mcp-reads.md`); a FlatFilePro XLSX export or Amazon template is the fallback. Read `references/prepare-mode.md` and its linked field-policy references. Use `scripts/prepare_flatfilepro_upload.py`; `scripts/selftest_prepare.py` checks it.
- `attended-images`: an operator in an attended chat supplies finished images, MAIN included; intake and hosting, then the direct-update write with a pixel check. The workbook `attended_gallery` plan is the fallback without the connector. Read `references/attended-images-mode.md`.
- `upload-map`: upload an already prepared `.xlsx`, match by SKU, map technical headers, verify every changed value in the preview, and stop before the catalog update. Read `references/upload-map-mode.md`, `references/upload-mapping-workflow.md`, and `references/upload-failure-handling.md`.

## Shared Rules

- FlatFilePro upload artifacts are `.xlsx`; CSV is for inspection only.
- Verify the exact Seller & Marketplace before browser work. When the connector resolved the IDs, the selector's seller and marketplace must equal them.
- `get_listings` and the export show FlatFilePro's saved copy, not live Amazon. A saved `get_listings` result is planning input only; workbook values come from a byte-verified export or the CDP read (`references/mcp-reads.md`). Live Amazon reads are part of the direct-update route; elsewhere run them only when the operator asks.
- A direct write needs the operator's approval of the exact batch (`review.md` and its SHA-256) in the current chat, plus the MAIN image review when the batch changes MAIN. An approval expires after 12 hours, and every write starts with a fresh live read of the SKU. Never resubmit a recorded write.
- Never map a nearby-looking attribute when the exact technical header is unavailable.
- Workbook modes stop at the preview before `Update Listings`, `Force Update`, `Done`, `Submit`, or another applying action unless the operator approves that exact action in the current chat. The bounded secondary-image pipeline uses its authenticated request authorization above.
- Local recurring account and mapping notes live under `_local/flatfilepro/local-notes.md` and remain confidential.
