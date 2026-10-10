---
id: KC-0160
title: "Amazon sales drop while other channels stay flat: check whether FBA went out of stock and the offer fell back to FBM without Prime"
kind: diagnosis
topic: logistics
status: reviewed
skills: [amazon-audit, amazon-fba-inventory-planning]
marketplaces: [US]
marketplace_inferred: true
surface: ""
surface_verified: false
symptom_keywords: ["Amazon sales suddenly dropping", "sales drop after FBA out of stock", "switched to FBM lost Prime badge", "sales decline FBM fallback", "Amazon down but own web shop stable"]
error_text: []
asked_as: ["The client saw Amazon sales start to decline after a period of consistent sales, while their own web shop stayed steady, and asked why."]
synonyms: []
resolution_status: diagnosis-only
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/011-increase-sales-G43381.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2025-03
review_by: 2027-10
provenance: "ledger:KC-0160"
---

## Question

The client saw Amazon sales start to decline after a period of consistent sales, while their own web shop stayed steady, and asked why.

## Answer

When Amazon sales fall while other channels hold steady, check first whether the FBA offer went out of stock and the listing is selling through FBM. FBM offers lose the Prime badge, so a sales drop after the switch is expected. Also check how dependent the listing is on branded search, since non-branded traffic cushions such drops.

## Cause

Not confirmed in the thread. The client reported that FBA stock ran out on the day the decline began, and the agency named the switch to a merchant-fulfilled offer as a likely cause: an FBM offer is not Prime eligible, which usually lowers conversion. The agency also named heavy dependence on branded search as a factor. The thread does not show sales recovering after a restock.

## Fix

1. Compare the date of the sales decline with the FBA stockout date in the inventory history.
2. Check whether the live offer is FBA (Prime) or FBM.
3. Compare the trend with other sales channels to rule out a brand-demand drop.
4. Review branded search volume week over week (for example in Search Query Performance) to see whether brand demand changed.
5. Restore FBA stock as soon as possible and keep the FBM offer as a backup only.

## Verify

Sales recover once FBA units are available again and the Prime offer is featured.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/011-increase-sales-G43381.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: Adds a diagnosis order for a sudden Amazon-only sales drop: match it to an FBA stockout and FBM fallback without Prime before blaming demand.
- Existing coverage: full (`Amazon Seller Help/articles/074-amazon-outlet-GHLYT4TPVCY2MJE3.md`, `Amazon Seller Help/articles/034-amazon-services-business-solutions-agreement-G1791.md`, `Amazon Seller Help/articles/059-prime-day-readiness-playbook-GM2ADTH3XH3A5N57.md`, `AdLabs Help/articles/004-bid-optimization-guide.md`, `Amazon Seller Help/articles/064-fba-peak-readiness-playbook-G4QH4XCRWUXRJBLY.md`).
