---
id: KC-0050
title: "Brand Store will not submit for publishing and still shows an outdated brand logo"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [DE]
marketplace_inferred: false
surface: "Amazon Ads > Stores > Store builder (Submit for publishing, Store settings)"
surface_verified: false
symptom_keywords: ["brand store cannot publish", "store builder errors in red", "store missing image link warning", "change brand logo in brand store", "old logo on brand store"]
error_text: []
asked_as: ["After the agency built a Brand Store, the brand owner tried to publish it but the builder flagged issues that had to be fixed first."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Advertising Help After Login/articles/179-stores-builder-GGYZFGR2ZP8444PB.md", "Advertising Help After Login/articles/230-create-your-store-GXYQWXYUW67LPVVF.md", "Advertising Help After Login/articles/141-stores-moderation-GAEG64S8CFJH5Z7R.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2024-11
review_by: 2027-10
provenance: "ledger:KC-0050"
---

## Question

After the agency built a Brand Store, the brand owner tried to publish it but the builder flagged issues that had to be fixed first. The store also showed an old brand logo the brand no longer uses.

## Answer

When a Brand Store will not submit, resolve every issue the builder marks in red first; in this case, tiles with missing image links did not block publishing and could be removed. The store logo lives in the builder's Store settings, so update it there when the brand changes its logo. Then submit for publishing and wait for moderation to show the store as Live.

## Cause

The Store builder blocks Submit for publishing while issues it flags in red are unresolved. In this thread, other flagged items were tiles with missing image links, which the brand owner judged unnecessary and which did not stop publishing. The logo comes from the store's own settings, not the listings, so it stays outdated until someone replaces it there.

## Fix

1. Open the store in the Store builder and review every flagged issue before submitting.
2. Fix all issues shown in red; the store cannot be submitted until they are resolved.
3. For tiles flagged only for a missing image link, either add the link or remove the tile if it is not needed.
4. Replace the brand logo in the Store settings section of the builder.
5. Click Submit for publishing and wait for moderation; the store goes live once approved.

## Verify

The store's moderation status shows Live, the public store URL opens on the marketplace, and the header shows the current logo.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Advertising Help After Login/articles/179-stores-builder-GGYZFGR2ZP8444PB.md`
- First-party: `Advertising Help After Login/articles/230-create-your-store-GXYQWXYUW67LPVVF.md`
- First-party: `Advertising Help After Login/articles/141-stores-moderation-GAEG64S8CFJH5Z7R.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Store SOPs cover building and rejection fixes but not the pre-submit split between blocking red issues and non-blocking missing-image-link flags.
- Existing coverage: partial (`MAG SOPs/catalog/brand-registry-sop-fix-brand-store-byline.md`).
