---
id: KC-0329
title: "FlatFilePro connector read versus the FlatFilePro item-detail read: are the listing values the same, and what does the connector leave out?"
kind: reference
topic: catalog
status: draft
skills: [amazon-flatfilepro, amazon-seo]
marketplaces: [all]
marketplace_inferred: false
surface: "FlatFilePro connector (get_listings, listings export) and FlatFilePro item-detail read"
surface_verified: true
symptom_keywords: ["flatfilepro mcp same as export", "ffp connector archived sku", "get_listings archived", "ffp export header spelling", "unit_count type_value header", "can I build an upload from the ffp connector"]
error_text: []
asked_as: ["Before switching the FlatFilePro workflows to the new connector, we compared its read of one supplement SKU with the browser item-detail read to see whether the values match."]
synonyms: ["FFP MCP", "Flatfile Pro connector", "FlatFilePro export"]
resolution_status: resolved
fix_source: agency
evidence_location: run-note
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: []
related_sops: [skills/amazon-flatfilepro/references/mcp-reads.md, skills/amazon-flatfilepro/references/direct-update-mode.md]
supersedes: []
contradicts: []
observed: 2026-10
review_by: 2027-10
provenance: "ledger:KC-0329"
---

## Question

Before switching the FlatFilePro workflows to the new connector, we compared its read of one supplement SKU with the browser item-detail read to see whether the values match.

## Answer

They match. The connector's listings export and the item-detail read for the same SKU had the same `versionId` and the same 168 flattened attribute keys and values. The differences are in what each read carries, not in the values: the connector has no Amazon catalog title (`itemName`) and no relationships record, and `get_listings` returns archived SKUs without saying they are archived. Build upload values from the verified export, not from a saved `get_listings` result.

Since 29 Oct 2026 the connector also writes listings directly and reads live Amazon (`get_listings_item_from_amazon`, `get_catalog_item_from_amazon`); the attended route is `skills/amazon-flatfilepro/references/direct-update-mode.md`, and KC-0332 covers what a write replaces and how live reads differ from the saved copy. The comparison below still holds for the saved-copy reads.

## Cause

Both reads come from FlatFilePro's saved copy of the listing. The item-detail read's `itemName` is Amazon's catalog display title, which can differ from the saved `item_name` value, so it cannot be derived from `item_name`. The flattening that turned item-detail reads into rows used to drop nested objects such as `unit_count[0].type` and `item_dimensions[0].width`; the connector tooling flattens them.

## Fix

1. Read current values through `node tools/amazon-operations/ffp-mcp.mjs` on a verified export (`fetch-export`, then `resolve` and `grid`), as `skills/amazon-flatfilepro/references/mcp-reads.md` describes.
2. Treat a saved `get_listings` result as a planning read only, and check archive status in the export before trusting a SKU list from it.
3. Author changes against the export's header spelling. Occurrence `i` becomes `__{i+1}__` (`item_name__1__value`), nested object keys join with one underscore (`unit_count__1__type_value`, `item_dimensions__1__height_unit`), nested arrays add `__{j+1}__` (`outer__1__material__2__value`), and an array of strings ends with an empty key (`color__1__standardized_values__1__`).
4. Allow for export time: a catalog of 6 listings exported in about 1 s. A catalog of 2,557 listings failed twice with `RETRY_EXHAUSTED` after about eight minutes each; for a catalog that size, build the workbook source from the FlatFilePro XLSX export.

## Verify

The export's receipt shows the SHA-256 and record count matched, `resolve` lists any archived SKUs it excluded, and the grid's headers use the `__N__` spelling.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: none captured yet.
- Also in: `skills/amazon-flatfilepro/references/mcp-reads.md`.
- Evidence: team vault ledger row for this id.

## Gaps

- Compared on one SKU in one marketplace; other product types may carry nested shapes not seen here.
- `get_listings` and the export cannot show live Amazon state. For that, use the connector's live listing read, which returns Amazon's attributes and issues, or the listing issue, Category Listings Report and detail page.
