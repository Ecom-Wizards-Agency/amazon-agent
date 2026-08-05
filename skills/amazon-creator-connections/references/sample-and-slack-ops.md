# Sample Fulfillment and Slack Operations

Read `lifecycle-execution-guardrails.md` before acting. It owns identity, score, MCF, follow-up, and escalation rules.

## Sample lane

Classify only through the active Creator Record ID:

- **Approved for Sample:** exact score of 10/10, final ASIN, verified identity, full recipient details, low risk, no duplicate sample, and no MCF blocker.
- **Verification / hold:** any missing requirement or conflicting detail. Queue a tailored request for only the missing information.
- **Do not send:** high risk, closed, paused, unresponsive after cadence, or an unresolved identity/product conflict.

Never use a name, email fragment, address, or old tracker row alone as the MCF target.

## MCF execution

An MCF order is an external paid action. It requires the current operator instruction or matching local standing permission.

1. Lock the Creator Record ID for the pre-flight so another queue item cannot target the same creator/product.
2. Resolve the live tracker headers and read the exact selected row, registry entry, and latest thread.
3. Apply every MCF pre-flight check in `lifecycle-execution-guardrails.md`.
4. Capture a pre-flight screenshot/evidence reference that visibly shows the recipient, selected SKU/ASIN, exactly one unit, shipping selection, and estimated fee.
5. Create the order only after all controls pass. Re-read the confirmation screen and match order ID, recipient, product, quantity, and dates to the locked record.
6. Update the tracker and action log, then send the standard confirmation only after confirmed fulfillment.

The order ID is `CC-{BRAND}-{PRODUCTCODE}-{CREATOR}-{ASIN}-{YYMMDD}`. Standard shipping is the default only when permitted by the client policy. Never use expedited shipping without an explicit rule.

## Content and performance

When content is posted, open the link and verify it belongs to the resolved creator and, where visible, the selected product. Write the verified link to the campaign row and action log.

For a creator-supplied performance update, reply only when message authority is present. Thank the creator, acknowledge the update, and state that performance is being tracked on the brand side. Do not promise future work or results.

## Slack reporting

Slack is an internal audit surface, not a source of truth. The tracker and action log remain authoritative.

- Read `_local/slack-posting.md` before every Slack write.
- Agent-authored posts must use the configured posting helper and bot identity. The Slack connector is read-only or for personal drafts requested by the operator.
- Do not post if the helper is unavailable, the channel is not allowlisted, the run uses stale data, or a current instruction/standing permission is absent.
- Never include addresses, emails, phones, or private tracker links.

When permitted, use one short parent and flat thread replies for material changes only. Suggested categories:

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

The automated daily summary uses the local posting helper only. A weekly summary is prepared each Monday but is posted only through the same helper and authority check. Never bypass the helper or impersonate the operator through the Slack connector.
