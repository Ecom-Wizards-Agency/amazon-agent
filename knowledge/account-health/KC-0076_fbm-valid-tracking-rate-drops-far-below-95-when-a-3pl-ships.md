---
id: KC-0076
title: "FBM Valid Tracking Rate drops far below 95% when a 3PL ships with an unrecognized carrier mapping"
kind: diagnosis
topic: account-health
status: reviewed
skills: [amazon-account-health-check, amazon-troubleshooting]
marketplaces: [US]
marketplace_inferred: true
surface: "Seller Central > Performance > Account Health > Shipping performance > Valid Tracking Rate"
surface_verified: false
symptom_keywords: ["valid tracking rate low", "VTR below 95 percent", "invalid tracking FBM 3PL", "3PL shipping method mapping wrong", "FBM at risk of deactivation tracking"]
error_text: ["Valid Tracking Rate"]
asked_as: ["The account manager flagged a 30-day FBM Valid Tracking Rate under half of the target and asked for immediate action, warning it could shut down FBM."]
synonyms: []
resolution_status: partial
fix_source: agency
evidence_location: slack
confidence: medium
verification: unverified
verified_on: ""
verified_how: ""
amazon_sources: ["Amazon Seller Help/articles/049-manage-orders-faq-G69124.md", "Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md"]
related_sops: []
supersedes: []
contradicts: []
observed: 2026-05
review_by: 2027-10
provenance: "ledger:KC-0076"
---

## Question

The account manager flagged a 30-day FBM Valid Tracking Rate under half of the target and asked for immediate action, warning it could shut down FBM. The 3PL had been working on the issue for weeks.

## Answer

A sudden FBM Valid Tracking Rate collapse while orders still ship usually means the ship confirmations name a carrier Amazon cannot match, often from a 3PL shipping-method mapping. Fix the carrier mapping first, then expect the 30-day rate to recover gradually as new orders fill the window, slowing as it nears the target. The same mapping fault can hit other sales channels the 3PL fulfils.

## Cause

The 3PL's shipping-method mapping did not pass a carrier Amazon recognized, so ship confirmations carried tracking Amazon counted as invalid. After the mapping was fixed and orders shipped with carriers Amazon recognizes, the 30-day rate began climbing; it had not yet returned above 95% when the thread ended.

## Fix

1. Open the Valid Tracking Rate detail in Account Health and confirm which orders have invalid tracking and which carrier name they show.
2. Have the 3PL or shipping integration correct its shipping-method-to-carrier mapping so ship confirmations name a carrier Amazon recognizes (in this case Amazon Shipping, UPS and a regional carrier).
3. Keep FBM live while fixing if possible; turning FBM off was proposed as an emergency stop but the brand owner rejected it.
4. Track the 30-day VTR at each check; it climbs gradually as new valid-tracking orders replace old ones in the window.
5. If FBM offers are suspended for VTR, prepare a plan of action for the VTR appeals route in the MAG SOP. Operator approval required before submitting.

## Verify

New FBM orders show valid carrier tracking in Manage Orders, and the 30-day Valid Tracking Rate rises toward and above 95%.

## Stop before

Stop before any submission, appeal, case send, refund, price change or listing change unless the operator approved that exact action.

## Sources

- First-party: `Amazon Seller Help/articles/049-manage-orders-faq-G69124.md`
- First-party: `Amazon Seller Help/articles/177-prepare-for-the-holiday-season-G8ZDWEJB9Z9YPFQ8.md`
- Also in: none.
- Evidence: team vault ledger row for this id.

## Gaps

- Net new versus existing sources: No unit ties a sudden FBM Valid Tracking Rate collapse to a 3PL shipping-method carrier mapping and shows the gradual 30-day recovery after the fix.
- Existing coverage: partial (`knowledge/catalog/KC-0006_variation-children-vanish-from-a-family-check-fbm-offer-deac.md`, `knowledge/account-health/KC-0012_fbm-offer-not-selling-because-the-account-is-in-vacation-mod.md`).
