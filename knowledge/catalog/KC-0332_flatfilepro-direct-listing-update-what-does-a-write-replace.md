---
id: KC-0332
title: "FlatFilePro direct listing update: what does a write replace, and how do live reads differ from the saved copy?"
kind: reference
topic: catalog
status: draft
skills: [amazon-flatfilepro, amazon-seo, amazon-catalog]
marketplaces: [all]
marketplace_inferred: false
surface: "FlatFilePro connector (update_listing_on_amazon, get_listings_item_from_amazon, get_product_type_fields, get_listings)"
surface_verified: true
symptom_keywords: ["ffp update replaces bullets", "flatfilepro direct update whole array", "image url changed after upload", "media_locator issue", "selectOptions free text", "live listing values are strings", "parentAsins in ffp listing"]
error_text: []
asked_as: ["Before the first direct write through the FlatFilePro connector we read one coat listing live and saved, plus its field definitions, to see what a write replaces and how to check it landed."]
synonyms: ["FFP MCP V2", "FlatFilePro direct write", "getListingsItem", "patchListingsItem"]
resolution_status: resolved
fix_source: agency
evidence_location: run-note
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: [skills/amazon-flatfilepro/references/direct-update-mode.md, skills/amazon-flatfilepro/references/mcp-reads.md]
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0332"
---

## Question

Before the first direct write through the FlatFilePro connector we read one coat listing live and saved, plus its field definitions, to see what a write replaces and how to check it landed.

## Answer

An update replaces the whole array of every attribute you send and leaves omitted attributes alone, so sending one new bullet without the others deletes the others. Build each payload from the current array and change only the element you mean to. A read-back never shows the URL you submitted for an image; it shows an Amazon `m.media-amazon.com` URL, so only a pixel comparison proves the right picture landed. `ACCEPTED` means accepted, not live; only `SUCCEEDED` plus a matching live read confirms.

## Cause

The write is Amazon's listings patch per top-level attribute. Amazon rehosts images and assigns its own locator. FlatFilePro's saved copy is a stored snapshot, not the live listing.

## Fix

1. Read the listing live (`get_listings_item_from_amazon`) before the write and keep it; it is the before state and the rollback source.
2. Carry every untouched element of a changed attribute from a verified export or a saved copy that agrees with the live read.
3. Compare values as text: live returns most numbers and booleans as strings (`"0.26"`, `"false"`). The saved copy has the same values and order but reorders object keys and adds a non-attribute `parentAsins` key.
4. Treat field definitions (`get_product_type_fields`) as guidance: nothing is marked required, and `selectOptions` are suggestions; free text such as `100% polyester` was accepted. The result for one product type is about 250K characters.
5. Read new issues after the write. Each carries `code`, `message` (in the marketplace language), `severity`, `attributeNames` and `categories`. Image issues name `media_locator`, not a slot, so they apply to every image slot you touched.

## Verify

A live read after the write shows the payload values on every touched attribute, a new Amazon URL on each changed image slot and unchanged URLs on every other slot, and a polled update status is `SUCCEEDED`. A new URL only proves the slot changed: for images, run `skills/amazon-flatfilepro/scripts/image_intake.py compare` on the verify file, then `verify --pixels` with its result, and count the image as landed only when verify reaches state `verified`. The route is `skills/amazon-flatfilepro/references/direct-update-mode.md`.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `skills/amazon-flatfilepro/references/mcp-reads.md`.
- Evidence: team vault ledger row for this id.

## Gaps

- Read on one listing of one product type in one marketplace; no write was made during the probe.
- The catalog read's image IDs did not match the listing's locator IDs, so the catalog read cannot confirm a slot.
- Whether a direct update refreshes FlatFilePro's saved copy is not confirmed yet.
