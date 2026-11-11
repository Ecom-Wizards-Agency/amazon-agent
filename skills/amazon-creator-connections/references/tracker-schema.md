# Creator Connections Tracker Schema

This is the sole tracker schema. Preserve the live sheet's formatting, merges, dropdown validation, chip colors, and campaign metadata. Campaign tabs are client-shareable. Private creator contact details remain only in the live sheet and local browser context.

## Tab structure

- Rows 1 to 8: campaign metadata.
- Row 9: grouped headers.
- Row 10: column headers.
- Row 11 onward: creator records.
- One tab per campaign, plus `Undecided` for unresolved product choice and three internal control tabs: `Creator Registry`, `Creator Action Log`, and `Daily Action Queue`.

These are the standard campaign header rows, not a reason to rewrite a legacy layout. Locate the live header row and resolve its fields by name.

## Simplified reading views

`Start here` records current operator restrictions, the sample-request workflow and campaign links. `Creator overview` is a formula-driven reading view with creator, campaign/product, stage, recorded score, next step, follow-up, sample/content and source-record link. Neither tab replaces a campaign row or a control tab.

- Hidden tabs, collapsed groups and filtered-out rows remain part of the same tracker. Visibility never determines update or sweep coverage. Use spreadsheet metadata and bounded connector reads that include these records, not only mounted or visible UI rows.
- The overview's `Current work` filter is a reading convenience. Validate changed records through `All records` or the complete underlying projection, including held and closed records.
- Match each view entry to the immutable Creator Record ID and exact campaign/source reference. A source-row link is a navigation reference, not a newly issued identity. Names and overview row numbers are not keys; sorting and filters can change their positions.
- Pending intake labels without verified IDs remain unresolved. Do not issue an ID from a queue ID, name or formula, or clear an intake entry before its verified campaign row is represented.
- Show the score already recorded in the source. Supported legacy headers are `Total Qualification Score`, `Qualification Score`, and `Qualification score (not shipping clearance)`. Resolve a different header explicitly rather than treating it as blank. Blank/unverified is `Not recorded`; an actual zero is `0/10`. Preserve the distinction.
- A new score comes from `score`, with its evidence and missing checks recorded in the original row. Do not type a score into the overview or copy a different campaign's score. `10/10` is qualification, not shipping authority.
- Current operator holds and identity/order conflicts override historical approval labels, scores and due dates in the reading view. Filter or layout changes must not clear a hold.
- A storefront, product or portfolio URL in a historical `Posted Link(s)` cell is not proof of posted content. Distinguish content links from other links; independent verification remains separate.

## Required update and readback protocol

For each resolved creator-record update:

1. Read the current operator restrictions, campaign row, Registry record, Queue row and existing Action Log IDs. Capture the overview's source, row-selection and score formulas. Resolve the source coordinates again before writing; retain the full before records privately.
2. Prepare the exact changed fields from verified thread, profile, order or control-runner evidence. Check live dropdowns. Preserve untouched values, notes, formulas, identity fingerprints, locks and sample history. Recompute qualification after new research/replies; update the source score, evidence and missing checks together.
3. Write the original campaign row and a dated Notes entry preserving prior notes. Synchronize applicable Registry changes through their required controls; unchanged identity/lock fields stay unchanged. Append one uniquely identified Action Log event and update the Queue outcome, due/hold state and Last Updated. Use a held queue state while an operator hold applies.
4. Read back the affected campaign, Registry, Action Log and Queue records from the same canonical spreadsheet, even when hidden. Match the intended fields exactly and confirm no unplanned field changes. A partial write is incomplete.
5. Read the changed record in the complete overview. Verify the source link, record/campaign binding, recorded score and current hold. Verify that the captured source/row/score formulas remain intact and cover new campaign rows. Add newly created campaign tabs to the view's source mapping and check its capacity before calling that tracker setup complete.
6. Run `creator_control.py verify-tracker-update` on those private captured records. If formulas are still recalculating, re-read once. Repair a damaged view within the authorized scope or hold/escalate the discrepancy; never hide it by typing a display score. Do not resend a message, repeat an order or append a duplicate log event to repair a display failure.
7. Mark the update complete and advance its message checkpoint only after verification passes. Include the full checked `tracker_update` input on an `actioned` sweep thread; also set `tracker_updated: true` and supply it on a held/escalated thread whose tracker was changed. The checkpoint runner rechecks it against the creator, run and sweep window.

The checker validates supplied connector captures; it cannot independently attest a remote write or perform one. Ordinary human edits may refresh overview formulas, but do not automatically update the Registry, Log or Queue. Reconcile such edits through this protocol before the next agent action. Keep raw captures under `_local/`, never in code or a checkpoint sent to Arcana.

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

The authoritative identity index. It stores Creator Record ID, display name for operator navigation, opaque storefront, thread, name, and contact fingerprints, active product/campaign, record state, lock state, active MCF reservation manifest, cancellation history, and merge notes. An active reservation includes the reservation ID, campaign ID, tracker source reference, ASIN, SKU, one-unit quantity, recipient binding, state, timestamps, and evidence references. Do not copy raw address, email, phone, or storefront URL values into this tab.

### Creator Action Log

Append-only, non-PII event log. Record every sent message, status move, queue decision, fulfillment pre-flight, MCF reservation, populated-screen verification, confirmation, cancellation, reconciliation hold, content verification, or escalation with the reservation ID when applicable and an evidence reference.

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
- When the current ASIN is not MCF-fulfillable, retain it as the active ASIN while the creator is `Product Switch Pending`. Record the verified alternate and fulfillment evidence in Notes/Risk Flags, keep Sample Decision `Hold`, and do not move or rewrite the active ASIN until the creator explicitly confirms the alternate.
- Never merge or move rows from display-name similarity. Resolve the Creator Record ID first.
- Do not delete historical sample records. Mark their current state and link the same Creator Record ID when verified.
