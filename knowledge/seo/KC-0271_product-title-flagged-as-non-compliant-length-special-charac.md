---
id: KC-0271
title: "Product title flagged as non-compliant: length, special characters and word repetition"
kind: rule
topic: seo
status: reviewed
skills: [amazon-seo, amazon-catalog]
marketplaces: [DE]
marketplace_inferred: true
surface: "Product title (Item name)"
surface_verified: false
symptom_keywords: ["title not compliant", "title word repeated too often", "title character limit", "special characters in title", "competitors use same title"]
error_text: []
asked_as: ["The agency told a brand that none of its proposed title variants were compliant; the brand objected that competitors use similar titles and asked what exactly was wrong."]
synonyms: []
resolution_status: partial
fix_source: first-party-doc
evidence_location: slack
confidence: high
verification: verified
verified_on: "2026-10-10"
verified_how: first-party-capture
amazon_sources: ["Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md"]
related_sops: []
supersedes: []
contradicts: ["Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md"]
observed: 2026-04
review_by: 2027-10
provenance: "ledger:KC-0271"
---

## Question

The agency told a brand that none of its proposed title variants were compliant; the brand objected that competitors use similar titles and asked what exactly was wrong.

## Answer

Check every title variant, and the live title, against the current title requirements before testing: character limit, banned special characters, no word more than twice (brand name included), and no promotional or restricted phrases. When you report a title as non-compliant, name the rule and the variant it fails. Competitors using similar titles proves nothing: Amazon states that existing non-compliant titles may be corrected automatically or left out of search results. Put the extra detail into Item highlights.

## Cause

The agency judged the variants non-compliant and listed the title rules (length, special characters, two-instance word limit). It named only one concrete breach, the product-type noun repeated more than twice, and the brand pointed out that this breach sat in the live control version, not in the new variants. The thread never establishes a length or special-character breach. The agency quoted a 200-character limit; the current Seller Central title requirements set 75 characters for a product listed for the first time.

## Fix

1. Check the title length against the current limit in the title requirements page (75 characters including spaces in the current capture).
2. Remove the prohibited special characters: ! $ ? _ { } ^ ¬ ¦.
3. Count each word; no word, including the brand name, may appear more than twice. Prepositions, articles and conjunctions are exempt.
4. Remove promotional phrases and restricted phrases.
5. Move extra descriptive detail into Item highlights instead of the title.
6. Check the live control title and each A/B variant separately, and name the exact rule and variant that fails; the breach may sit in the current live title rather than the new variants.

## Verify

Each title variant passes the length, special-character and two-instance word checks before submission, and no policy-violating title shows in Manage All Inventory.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Records that the team quoted a 200-character title limit while the current capture says 75, and that competitor titles are no proof of compliance.
- Existing coverage: full (`Amazon Seller Help/articles/150-product-title-requirements-and-guidelines-GYTR6SYGFA5E3EQC.md`).
