---
name: amazon-flatfilepro
description: "Prepare, validate, upload and map narrow FlatFilePro workbooks; execute authenticated secondary-image bulk requests through the managed-client pipeline."
---

# Amazon FlatFilePro

Browser: Mixed (preparation is local; upload and column mapping use the logged-in FlatFilePro CDP session).

Use this skill for the complete FlatFilePro workflow while keeping preparation and browser mapping as explicit modes.

## Modes

- `secondary-images`: use the existing `wizards-ai/listing_images.py` and `listing_image_jobs.py` pipeline. A concrete authenticated team request authorizes the exact batch for a current managed-ready client. Resolve eligibility from the Amazon Ops registry and verify FlatFilePro seller/marketplace bindings automatically. The image workflow contract is `wizards-ai/docs/bulk-listing-images-setup.md`. No per-account pilot, source URL allowlist or release-ledger approval is required. Preserve MAIN, swatches, unspecified slots, complete requested batch coverage, immutable revisions/assets and independent processing/publication/protected-field checks. Existing submitted operation IDs reconcile without resubmission.
- `prepare`: build a narrow SKU-keyed `.xlsx` from a FlatFilePro export or Amazon template plus label, packaging, or approved copy evidence. Read `references/prepare-mode.md` and its linked field-policy references. Use `scripts/prepare_flatfilepro_upload.py`.
- `upload-map`: upload an already prepared `.xlsx`, match by SKU, map technical headers, verify every changed value in the preview, and stop before the catalog update. Read `references/upload-map-mode.md`, `references/upload-mapping-workflow.md`, and `references/upload-failure-handling.md`.

## Shared Rules

- FlatFilePro upload artifacts are `.xlsx`; CSV is for inspection only.
- Verify the exact Seller & Marketplace before browser work.
- Never map a nearby-looking attribute when the exact technical header is unavailable.
- General workbook modes stop at the preview before `Update Listings`, `Force Update`, `Done`, `Submit`, or another applying action unless the operator approves that exact action in the current chat. The bounded secondary-image pipeline uses its authenticated request authorization above.
- Local recurring account and mapping notes live under `_local/flatfilepro/local-notes.md` and remain confidential.
