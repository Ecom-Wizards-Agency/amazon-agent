# Sample Fulfillment and Slack Operations

Read `lifecycle-execution-guardrails.md` before acting. It owns identity, score, MCF, follow-up, and escalation rules.

## Sample lane

Classify only through the active Creator Record ID:

- **Approved for Sample:** exact score of 10/10, final ASIN, verified identity, full recipient details, low risk, no duplicate sample, and no MCF blocker.
- **Verification / hold:** any missing requirement or conflicting detail. Queue a tailored request for only the missing information.
- **Do not send:** high risk, closed, paused, unresponsive after cadence, or an unresolved identity/product conflict.

Never use a name, email fragment, address, or old tracker row alone as the MCF target.

## MCF execution

An MCF order is an external paid action. It requires the current operator instruction or matching local standing permission. For a lane handed to Arcana, that act is the operator pressing "Send 1 unit via Amazon" on the Arcana lane screen; the skill never presses it.

Hand the lane to Arcana (the normal route):

1. Resolve the live tracker headers and read the exact selected row, registry entry, and latest thread.
2. Run `preflight` with `"order_owner": "arcana"`. It applies every MCF pre-flight check in `lifecycle-execution-guardrails.md`, including the explicit FBA/AFN channel, live MCF-fulfillable quantity, inventory-check timestamp, and private evidence reference, with a cap-only fee check. Seller-fulfilled or FBM stock does not count.
3. Call `creators.preflight_result` with the output and keep its `derived_order_key` exactly as returned.
4. Run `reserve-mcf` with the same proposal and that key. Retain the reservation ID.
5. Call `creators.register_record` with the locked registry row, then tell the operator the lane is ready in Arcana for the tracker row with that Creator Record ID. If it refuses the row, keep the lock, do not tell the operator, and escalate.
6. On later runs, read `creators.sample_send_outcome` with the stored key and run `arcana-outcome` on the payload. `not_found` means no send yet. Run `record-api-order` only for `placed`, `cancel-mcf` with `amazon_rejected` and `--outcome` for `failed`, wait on `pending` or `uncertain`, and escalate an escalated or `cancelled` send.
7. After `record-api-order` passes, update the tracker to `Sample Sent` and the action log, then send the standard confirmation by hand.

Seller Central form (order owner `runner`, only when the operator names that route for the lane):

1. Run `preflight` and `creators.preflight_result`, then `reserve-mcf` with the returned `derived_order_key`. Retain its unique reservation ID.
2. Resolve the live tracker headers and read the exact selected row, registry entry, and latest thread.
3. Populate MCF from the selected row, with the stored derived key as the order ID, then capture evidence that visibly shows the recipient, selected SKU/ASIN, exactly one unit, Standard shipping, estimated fee, and order ID.
4. Run `verify-mcf` against the reservation. Submit only after it returns `PASS` for the same creator, campaign, tracker row, product, recipient, order ID, and reservation ID.
5. Re-read the confirmation screen and run `confirm-mcf` with the matching reservation ID, ASIN, SKU, one unit, order ID, and evidence.
6. Update the tracker and action log, then send the standard confirmation only after confirmed fulfillment.

On the Seller Central route, if submission definitively failed, run `cancel-mcf` with the supported reason code and evidence so the reservation can be released safely. Never hand-edit the registry. If the request timed out or the outcome is unknown, do not cancel or retry: retain the lock, mark `Reconciliation Required`, and check Amazon order history first.

If order history proves the order exists, run `reconcile-mcf` with the exact reservation, creator, campaign, tracker row, product, recipient, one-unit quantity, existing order ID, and captured order-history evidence. This records the existing order and releases its lock without submitting another order. Identical replay is safe; conflicting evidence stays held. A failed `verify-mcf` recheck revokes any earlier approval for that reservation, so a corrected form requires a fresh PASS before submission.

The order ID is the lane's `derived_order_key` (`CCS-` plus 32 lower-case hex) from `creators.preflight_result`, stored in the reservation. Never compose it by hand. A reservation made before keys were stored keeps the `CC-{BRAND}-{PRODUCTCODE}-{CREATOR}-{ASIN}-{YYMMDD}` ID it was placed under. Standard shipping is the default only when permitted by the client policy. Never use expedited shipping without an explicit rule.

If the exact ASIN cannot be added to MCF, stop. Do not substitute. Run the product-switch preflight, offer only a same-campaign alternate that is already verified as MCF-fulfillable, and wait for the creator to reply with the exact alternate ASIN before changing the row or rerunning MCF.

## Content and performance

When content is posted, open the link and verify it belongs to the resolved creator and, where visible, the selected product. Write the verified link to the campaign row and action log.

For a creator-supplied performance update, reply only when message authority is present. Thank the creator, acknowledge the update, and state that performance is being tracked on the brand side. Do not promise future work or results.

## Slack reporting

Slack is an internal audit surface, not a source of truth. The tracker and action log remain authoritative.

- Read `_local/slack-posting.md` before every Slack write.
- Slack authorship follows the actor per `_local/slack-posting.md`: scheduled or background sweeps use the guarded bot helper, an attended session posts through the supervising operator's verified identity, and neither may fall back to the other. Every post, whichever identity, goes through the house-style enforcement in the posting helper.
- Do not post if the helper is unavailable, the channel is not allowlisted, the run uses stale data, or a current instruction/standing permission is absent.
- Never include addresses, emails, phones, or private tracker links.

When permitted, use one short parent and flat thread replies for material changes only. The daily parent is a PII-free tracker-progress notification: current pipeline snapshot, today's net movement, verified posted-content links, the 10/10 priority sample lane, and genuine exceptions only. Tag the configured operator mention in the parent so the owner receives the notification. Suggested categories:

- 🆕 New / First-Base Candidates
- 🔎 Background Checked / Missing to 10
- ✅ Verification Confirmed / Ready for Review
- 📦 Priority Sample Lane / Fulfillment Updates
- 🚚 Sample Sent / Delivery Watch
- 🎥 Content Posted / Links Logged
- 📈 Performance Updates
- 🔁 Product Switch / Needs Confirmation
- ⚫ Paused Product
- 📌 Action Needed

The automated daily summary uses the local posting helper only. A weekly summary is prepared each Monday and posted only through the same helper and authority check. Create one parent post titled with the brand and prior-week date range, then post the complete client-ready summary as a reply in that parent thread. Do not create additional standalone weekly-summary posts. Never bypass the helper, and never post under an identity other than the one `_local/slack-posting.md` assigns to the actor.
