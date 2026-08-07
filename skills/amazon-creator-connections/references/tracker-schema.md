# Creator Connections Tracker Schema

This is the sole tracker schema. Preserve the live sheet's formatting, merges, dropdown validation, chip colors, and campaign metadata. Campaign tabs are client-shareable. Private creator contact details remain only in the live sheet and local browser context.

## Tab structure

- Rows 1 to 8: campaign metadata.
- Row 9: grouped headers.
- Row 10: column headers.
- Row 11 onward: creator records.
- One tab per campaign, plus `Undecided` for unresolved product choice and three internal control tabs: `Creator Registry`, `Creator Action Log`, and `Daily Action Queue`.

## Campaign tab columns

The live header order is authoritative. Resolve columns by header name at runtime. Do not hard-code letters or prior positions.

### Record control

1. Creator Record ID

### Creator and campaign activity

2. Creator Name
3. Status
4. Full Name
5. Address
6. Email
7. Phone
8. Date Sent
9. Product
10. Content Posted
11. Posted Link(s)
12. Notes

### Sample fulfillment / MCF tracking

13. Fulfillment Method
14. Address Confirmed Date
15. Sample Approved By
16. Sample Sent Date
17. MCF Order ID
18. Tracking Number
19. Delivery Status
20. Follow-up Date

### Creator qualification gate

21. Amazon Storefront Link
22. Portfolio / Media Kit Link
23. Requested ASIN
24. Product Match Status
25. Recent Posting Verified?
26. Last Visible Post Date
27. Content Quality Rating
28. Category Fit
29. Performance Evidence Available?
30. Earns Revenue Badge?
31. Revenue Badge Source
32. Revenue Threshold Met?
33. Specific ASIN Mentioned?
34. Spam Risk
35. Risk Flags
36. Total Qualification Score
37. Qualification Tier
38. Sample Decision
39. Qualification Notes

## Control tabs

### Creator Registry

The authoritative identity index. It stores Creator Record ID, display name for operator navigation, opaque storefront, thread, name, and contact fingerprints, active product/campaign, record state, lock state, and merge notes. Do not copy raw address, email, phone, or storefront URL values into this tab.

### Creator Action Log

Append-only, non-PII event log. Record every sent message, status move, queue decision, fulfillment pre-flight, MCF result, content verification, or escalation with an evidence reference.

### Daily Action Queue

The bot's daily worklist. It should show the Creator Record ID, current status, action type, due date, required inputs, gate result, queue state, escalation reason, evidence reference, and last update.

`PENDING_APPROVAL` is the only valid gate result for a queued creator-message send unless a matching local standing permission has already been verified by the executor. `PASS` from a qualification or MCF pre-flight never authorizes a message send, campaign publish, MCF creation, or Slack post.

## Status and decision rules

Use the status dropdown that exists on the target sheet. Do not invent values. The standard labels are:

- New Inquiry
- First-Base Pass
- Verification Sent
- Verification Confirmed
- Proof Requested
- Address Verification
- Approved for Sample
- Sample Sent
- Delivered / Awaiting Content
- Content Posted
- Performance Update
- Follow Up
- Manager Review
- Product Switch Pending
- On Hold
- Unqualified
- Ghosted
- Declined / Closed
- `<Product> Pause`

Use the existing chip color when a label already exists. New client-specific labels require a coordinated color and a recorded local note. The fulfillment decision is separate: `Send`, `Hold`, or `Do Not Send`.

`Send` requires the exact 10/10 gate in `lifecycle-execution-guardrails.md`; it is not inferred from a status alone.

## Product and duplicate rules

- One active creator row per Creator Record ID and final product/ASIN.
- A creator who has not confirmed the final product remains in `Undecided`.
- On a verified product switch, make the final-product row active and retain the old row as historical only. Never leave two active sample paths.
- Never merge or move rows from display-name similarity. Resolve the Creator Record ID first.
- Do not delete historical sample records. Mark their current state and link the same Creator Record ID when verified.
