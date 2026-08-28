# Creator Lifecycle and Execution Guardrails

This is the single source of truth for creator identity, lifecycle transitions, scoring, fulfillment gates, and audit controls.

## One system of record

The shared Creator Connections tracker is the only durable source of truth. Its campaign rows, `Creator Registry`, `Creator Action Log`, and `Daily Action Queue` are one connected record system.

- The daily Creator Connections bot is the sole routine executor. It opens inquiries, runs background checks, writes qualification evidence, sends safe routine replies, schedules follow-ups, verifies content, and keeps the queue current.
- `creator_control.py` is a validation gate, not a second database. At the start of a run, the bot exports the private Registry to a local run file, validates the proposed changes, writes the successful result back to the Registry and Action Log, then treats the local file as a disposable cache.
- Slack is notification and escalation only. It never becomes evidence, a status source, or a place to recover creator details.
- The live Amazon thread is the source for a new factual message. Once read and verified, the tracker becomes the source for the creator's current state and next action.

No routine task may be performed from chat memory, a separate spreadsheet, or a prior Slack post. Before each external action, the bot reads the resolved Creator Record ID and current row from the tracker, validates it through the control runner, completes the action, and writes the outcome back before selecting the next creator.

## Multi-client run isolation

Read the enabled-client roster from `_local/creator-connections/enabled-clients.json`. Process enabled clients sequentially so one browser account, tracker binding, or local cache cannot bleed into the next client.

Before each client run, hard-verify all of these bindings against that client's local config:

- advertiser/account label, brand account ID, entity ID, and marketplace
- tracker spreadsheet ID and active campaign ID
- unique creator-record prefix
- client-specific registry export and message-watermark file

If any binding differs, write nothing for that client, do not advance its watermark, and raise a PII-free exception. A completed run for one client must never satisfy or mask a failed run for another. Each client keeps a separate Creator Registry, Creator Action Log, Daily Action Queue, registry export, and message-watermark file. Daily Slack reporting also uses one parent thread per client, brand, and date.

## Durable creator identity

Issue a non-PII Creator Record ID only after the creator is resolved. Format: `CCR-{brand-code}-{YY}-{sequence}`, for example `CCR-SW-26-0001`.

- The ID is immutable. It never changes when a creator changes product, campaign, display name, or tracker row.
- The central registry is authoritative. A tracker row without an ID is a legacy/unresolved record, not a safe action target.
- Do not generate IDs with spreadsheet formulas or derive them from names, addresses, ASINs, or row numbers.
- New threads may receive an ID once the thread header, brand, and campaign context are verified and no registry conflict exists.

### Matching protocol

Before a message, row update, move, or MCF order, resolve the creator in this order:

1. Exact canonical storefront URL or stable storefront slug.
2. Exact Amazon thread identity key plus matching campaign context.
3. Two independent verified contact attributes, such as full name plus normalized email, or phone plus normalized address.
4. A verified historic registry match with no conflicting detail.

Display name alone, first name alone, or an address alone is never enough. If a candidate match has conflicting email, phone, storefront, recipient, or final ASIN, set the record lock state to `Conflict` and do not act.

The registry stores opaque fingerprints for thread, storefront, email, phone, address, and full name. Normalize email and phone before fingerprinting. Keep raw contact details and visible links solely in the campaign tracker row.

### Required control-runner checkpoint

Use `tools/creator-connections-control/creator_control.py` with a local HMAC secret for every new record, background-check score, daily queue, and MCF pre-flight. The runner is the deterministic implementation of this protocol:

- `register` resolves or issues a Creator Record ID and holds any collision.
- `score` computes the 10/10 gate from evidence rather than trusting a typed score.
- `queue` produces the dated action queue and automatic escalation at the follow-up limit.
- `preflight` rejects any unresolved identity, ASIN/SKU mismatch, missing fulfillment data, duplicate-sample risk, non-Standard shipment, fee-cap breach, validation warning, or quantity other than one.

Persist only opaque fingerprints in the local registry. The private tracker keeps the raw recipient data. A failed or held runner result is a hard stop for an external action.

## Status lifecycle

Use the sheet's live dropdown values. The standard semantic stages below map to the approved labels in the tracker.

| Stage | Typical status | Automatic action | Transition evidence |
| --- | --- | --- | --- |
| Campaign available | Campaign Launched / Inquiry Sent | Read campaign metadata and create or verify its tracker tab. | Campaign, ASIN, dates, and tracker header agree. |
| New contact | New Inquiry | Resolve identity, capture message facts, queue background check. | Thread header and current message are logged. |
| Qualification research | First-Base Pass / Manager Review | Check storefront, recent visible shoppable content, fit, revenue signal, and risk. Write evidence and missing-to-10 items. | Background-check evidence is recorded. |
| Verification loop | Verification Sent / Proof Requested / Address Verification | Send only the tailored request for missing fields. Set due date to two days later. | Message send is visible in the correct thread and logged. |
| Verified | Verification Confirmed | Reconcile latest reply against the Creator Record ID and recalculate score. | Required information matches the same resolved record. |
| Sample eligible | Approved for Sample | Run the full MCF pre-flight. Do not create an order yet unless that action is permitted. | Score is exactly 10/10 and every fulfillment gate passes. |
| Fulfilled | Sample Sent | Record order ID, one unit, fee, shipment and estimated delivery. Send confirmation only after order confirmation. | MCF confirmation screen and order ID match the record. |
| Delivery/content follow-up | Delivered / Awaiting Content / Follow Up | Start a kind follow-up at delivery plus three days, then every two days. | Due date and sent-message audit entry exist. |
| Content/performance | Content Posted / Performance Update | Verify the link, write it to the campaign row, thank the creator when permitted. | Link opens and record/product match is visible or stated. |
| Stop state | On Hold / Unqualified / Ghosted / Declined / Closed / Product Pause | Stop routine action, retain history, and log the reason. | Pause, risk, refusal, or cadence threshold is recorded. |

## Scoring and cadence

- A sample requires exactly 10/10. Scores below 10/10 remain in verification or hold states.
- Always background-check first. Ask for shoppable links only if the storefront cannot be verified from the available view.
- Missing details, ASIN confirmation, or proof: follow up every two days, at most three attempts.
- Recipient mismatch: every two days, at most two attempts.
- Product pause acknowledgement: every two days, at most two attempts; the desired final reply is acknowledgement.
- Awaiting content: begin three days after expected delivery, then every two days, at most three attempts.

## MCF pre-flight

All checks must pass in the same run immediately before order creation:

1. Creator Record ID resolves without conflict and exactly one active record is selected.
2. Status is `Approved for Sample`, Sample Decision is `Send`, and score is `10/10`.
3. The final requested ASIN, tracker product, MCF SKU, and selected MCF product match exactly.
4. Full name, street address, city, state/province, ZIP/postal code, phone, and email are present in the selected creator row.
5. No prior sample exists for the same Creator Record ID and final product/ASIN. The synchronized registry's `sample_history` is authoritative for the deterministic gate; reconcile it against the tracker and MCF order history before pre-flight. Caller-supplied proposal history may add evidence but can never hide registry history.
6. Quantity equals exactly `1`. Standard shipping is selected. The visible fee is within the client-approved cap.
7. There are no page validation errors, recipient mismatches, or field truncations.

Capture the pre-flight evidence reference before creating the order. If any check fails, lock the record and escalate. Never make a corrective second order to compensate for an uncertain first order.

## Audit records

For every state-changing action, append one non-PII entry to `Creator Action Log` and update the row's dated Notes entry. The log records Creator Record ID, timestamp, source, action, verification result, record version, outcome, and evidence reference.

Each daily run writes one row per actionable creator to `Daily Action Queue`. Queue items must include status, due date, required inputs, gate result, current action, and escalation reason when blocked.

The runner's JSON result is the evidence reference for the queue and action log. Do not rely on a free-form chat summary as proof that an identity or MCF pre-flight passed.

## Escalations

Escalate only when the bot cannot safely resolve or complete a task:

- identity conflict, duplicate active row, or duplicate sample risk
- final product/ASIN conflict or unresolved product switch
- missing or conflicting recipient details
- creator remains below 10/10 or unresponsive after the configured cadence
- MCF pre-flight, quantity, fee, page-validation, or confirmation failure
- message, tracker, or verified content-link failure
- paused product, legal/review-manipulation, payment, or off-platform request

Use this PII-free Slack structure through the configured posting helper:

```text
📌 Action Needed: Creator Connections

Creator: {display name}
Record ID: {creator record ID}
Brand/Product: {brand} / {product}
ASIN: {asin or Unclear}
Stage: {status}
Issue: {specific mismatch or failure}
Bot action: {held, queued, or safe clarification sent}
Next step: {specific human decision}
Tracker: {tab and row only}
```
