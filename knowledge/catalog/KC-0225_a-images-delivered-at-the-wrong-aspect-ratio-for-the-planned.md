---
id: KC-0225
title: "A+ images delivered at the wrong aspect ratio for the planned modules: brief module sizes before design"
kind: procedure
topic: catalog
status: reviewed
skills: [amazon-catalog, amazon-flatfilepro]
marketplaces: [all]
marketplace_inferred: true
surface: "Seller Central > Advertising > A+ Content Manager"
surface_verified: false
symptom_keywords: ["A+ images wrong size", "rescale A+ images", "A+ module dimensions", "A+ framework image sizes", "A+ banner aspect ratio"]
error_text: []
asked_as: ["A designer delivered a numbered set of A+ graphics."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: screenshot
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/156-a-content-guide-GLG4RQK2Y2RJADU4.md"]
related_sops: ["MAG SOPs/design/design-sop-creating-a-content-and-brand-story-modules.md"]
supersedes: []
contradicts: []
observed: 2025-06
review_by: 2027-10
provenance: "ledger:KC-0225"
---

## Question

A designer delivered a numbered set of A+ graphics. The team building the A+ content sent them back because the images did not match the recommended module sizes in their A+ framework. The designer first said they were to scale, then re-exported them at the module aspect ratios.

## Answer

Brief A+ designers on the module layout, each module's minimum pixel size and its aspect ratio before they start. A+ Content Manager resizes larger images and lets you crop, so a wrong-ratio image still uploads but loses part of the design when cropped. Check delivered files against the framework before the A+ build and return mismatched images for re-export.

## Cause

The thread does not establish why the graphics missed the sizes. The designer said they were to scale, and the team building the A+ project asked for a re-export at the sizes in its A+ layout framework. Each A+ module states a minimum image size, for example 970 x 300 or 970 x 600 for basic image modules and 1464 x 600 (desktop) for premium full-width images. Amazon resizes images larger than the template and lets you crop and scale in the tool. An image at a different aspect ratio still uploads, but it gets cropped or scaled, which can cut off text and design elements.

## Fix

1. Decide the A+ layout (basic or premium, and which module per section) before design starts.
2. Give the designer a framework listing each section's module, its minimum pixel size and its aspect ratio.
3. Check every delivered file's dimensions and ratio against the framework before handing it to the person who builds the A+ project.
4. Send back any file whose ratio does not match and ask for a re-export at the module ratio.
5. Build the A+ project in A+ Content Manager once all images match; submitting it needs operator approval.

## Verify

Each image meets its module's minimum pixel size and matches the module's aspect ratio, so it places in A+ Content Manager without cropping away text or design elements.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/156-a-content-guide-GLG4RQK2Y2RJADU4.md`
- Also in: `MAG SOPs/design/design-sop-creating-a-content-and-brand-story-modules.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Module sizes are documented, but no local source gives the handoff check of validating designer files against the A+ framework before building the project.
- Existing coverage: partial (`MAG SOPs/design/design-sop-creating-a-content-and-brand-story-modules.md`, `Amazon Seller Help/articles/156-a-content-guide-GLG4RQK2Y2RJADU4.md`, `MAG SOPs/catalog/logistics-sop-send-to-amazon-how-to-create-fba-shipment.md`, `Amazon Seller Help/articles/154-shoppable-video-guide-GUZBYWTTVULY6C9Y.md`, `Advertising Help After Login/articles/148-content-tiles-on-stores-GBX4ZFVHAKXKA5WM.md`).
