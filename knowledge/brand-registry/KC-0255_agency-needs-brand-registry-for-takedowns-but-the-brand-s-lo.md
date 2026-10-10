---
id: KC-0255
title: "Agency needs Brand Registry for takedowns but the brand's logins disagree: find the login that submitted the Brand Registry application and get invited from it"
kind: procedure
topic: brand-registry
status: reviewed
skills: [amazon-catalog, amazon-client-onboarding]
marketplaces: [US]
marketplace_inferred: true
surface: "brandregistry.amazon.com > User permissions; Service Provider Central client invitation link"
surface_verified: false
symptom_keywords: ["need Brand Registry access for takedown", "Brand Registry login redirects to Seller Central", "duplicate Brand Registry account", "which login owns the brand in Brand Registry", "service provider invite did not give Brand Registry access"]
error_text: []
asked_as: ["To report a copycat seller, the agency needed to act through the brand's Brand Registry administrator account."]
synonyms: []
resolution_status: resolved
fix_source: client
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md"]
related_sops: ["MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md"]
supersedes: []
contradicts: []
observed: 2026-07
review_by: 2027-10
provenance: "ledger:KC-0255"
---

## Question

To report a copycat seller, the agency needed to act through the brand's Brand Registry administrator account. The client first generated a Service Provider invitation link, which only showed the agency already had Seller Central access. The client's own Brand Registry login kept sending them back to Seller Central, and the team was unsure which login owned the approved brands, suspecting a duplicate Brand Registry account.

## Answer

Seller Central access does not give you Brand Registry: for takedowns, ask the brand's Brand Registry administrator to invite you by email through User permissions. Before asking for anyone's credentials, confirm which login submitted the Brand Registry application, because that account holds the approved brands. Check that the invite covers every brand you need to protect.

## Cause

Seller Central user access and Brand Registry user access are separate grants; only a brand Administrator can invite users through User Permissions. Two logins had been used around the brand setup, and the approved brands sat under the login that submitted the Brand Registry application, which Amazon makes the brand's Administrator and Rights Owner. A service-provider invitation link the client generated only showed the agency's existing access and did not give it Brand Registry. The thread did not establish why, or why the client's Brand Registry login redirected to Seller Central.

## Fix

1. Identify which login submitted the Brand Registry application; Amazon makes that user the Administrator and Rights Owner, so that account holds the approved brands.
2. Have that Administrator open Brand Registry, click the gear icon, select User Permissions > Invite a user to your brand, and invite each agency user by the email of their Brand Registry account with a role that includes Report a Violation (Rights Owner, or Registered Agent for a third party).
3. Make sure the invitation covers every brand the agency must protect; update permissions per brand if needed.
4. Each invitee accepts the invitation and completes Amazon's verification.
5. File takedowns through Report a violation from the Brand Registry account; each report needs operator approval and genuine IP-violation evidence.

## Verify

After accepting, the agency user sees all the brands in Brand Registry and can open Report a violation for them.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`
- Also in: `MAG SOPs/catalog/catalog-sop-remove-unauthorized-sellers-hijackers.md`
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Role pages explain who assigns roles, but nothing local says a service-provider Seller Central invite does not reach Brand Registry or to find the login that submitted the application first.
- Existing coverage: full (`Amazon Seller Help/articles/212-brand-registry-glossary-GBR82EG272SZJDFS.md`, `Amazon Seller Help/articles/221-brand-registry-selling-roles-GJ84K745AL3R5N3Q.md`, `Amazon Seller Help/articles/220-brand-registry-protection-roles-GCF9UE9VGKGA2W5F.md`).
