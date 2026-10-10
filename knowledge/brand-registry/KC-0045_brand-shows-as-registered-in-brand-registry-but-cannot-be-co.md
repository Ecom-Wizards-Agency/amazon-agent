---
id: KC-0045
title: "Brand shows as registered in Brand Registry but cannot be connected to Seller Central because its trademark sits under another brand's profile"
kind: diagnosis
topic: brand-registry
status: reviewed
skills: [amazon-catalog]
marketplaces: [US]
marketplace_inferred: true
surface: "Brand Registry > Manage intellectual property; Seller Central > Manage selling roles"
surface_verified: false
symptom_keywords: ["brand registered but not in manage selling roles", "trademark listed under wrong brand", "cannot connect brand to seller central", "trademark attached to other brand profile", "new brand missing from Brand Registry selling roles"]
error_text: []
asked_as: ["A second brand appeared to be registered in Brand Registry, but it could not be connected to the seller account and did not appear as its own brand in Manage selling roles."]
synonyms: []
resolution_status: partial
fix_source: amazon-support
evidence_location: case
confidence: high
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/227-add-additional-trademarks-to-your-brand-GQCYJTBSFZK8HGN6.md", "Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md", "Amazon Seller Help/articles/214-brand-registry-application-process-GN2GYQVPR7R4VMPB.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0045"
---

## Question

A second brand appeared to be registered in Brand Registry, but it could not be connected to the seller account and did not appear as its own brand in Manage selling roles. Its word-mark trademark was listed under the intellectual properties of the seller's other, already enrolled brand.

## Answer

If a brand looks registered but never shows up in Manage selling roles, check whether its trademark was added to another enrolled brand's profile. A trademark with a different name cannot live under another brand; ask Brand Registry support to detach it, then enroll the brand separately with that trademark. Removing it does not change the other brand's trademarks or selling roles.

## Cause

The second brand's trademark had been added to the existing brand's profile as an additional trademark instead of being enrolled as its own brand. Amazon support confirmed the association was incorrect. Brand Registry only lets you add trademarks with the same trademark name to an enrolled brand; a mark with a different name needs its own enrollment, so the brand never existed as a separate profile that selling roles could attach to.

## Fix

1. In Brand Registry, open Manage > Manage intellectual property for the existing brand and check which trademarks are listed under it.
2. If a trademark with a different name appears there, open a Brand Registry support case giving the trademark office and serial number and asking Amazon to confirm whether it was incorrectly associated (case submission needs operator approval).
3. Let Amazon remove the trademark from the wrong profile; support confirmed the existing brand's other trademarks and selling-role relationships stayed intact.
4. Submit a new Brand Registry enrollment for the second brand using that trademark, then complete identity verification (2FA and documents from the account owner).
5. After approval, assign the seller account a selling role for the new brand in Manage selling roles.

## Verify

The second brand appears as its own brand in Brand Registry and in Seller Central Manage selling roles, and the first brand's profile no longer lists the other trademark.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/227-add-additional-trademarks-to-your-brand-GQCYJTBSFZK8HGN6.md`
- First-party: `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`
- First-party: `Amazon Seller Help/articles/214-brand-registry-application-process-GN2GYQVPR7R4VMPB.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No unit or page covers a differently named trademark wrongly attached to another brand's profile, how support detaches it, and the need for a separate enrollment afterwards.
- Existing coverage: partial (`Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `knowledge/brand-registry/KC-0005_brand-visible-in-brand-registry-but-listing-creation-still-b.md`, `Amazon Seller Help/articles/238-manage-your-brands-GF79K5R2ZLCWCPJT.md`, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`, `Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`).
