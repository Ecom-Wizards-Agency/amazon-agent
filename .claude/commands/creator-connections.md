---
description: Run a Creator Connections workflow: inbox audit, tracker update, reply drafts, campaign preparation, sample lane, Slack-ready report, gap check, reconciliation, or explanation. Status-filtered with four externally visible stop-gates.
argument-hint: "[client + marketplace + mode: audit|campaign|tracker|gaps|reconcile|samples|slack|explain (default audit) + scope/details]"
---

# Creator Connections

Route Creator Connections work through the `amazon-creator-connections` skill. It is the source of truth.

The user's target is: **$ARGUMENTS**

1. Load the skill and read the client-local configuration and notes before requesting missing inputs.
2. Confirm brand, marketplace, Ads account label, tracker, and scope. Run the connected-browser checkpoint.
3. Apply the confirmed status-filter mapping. If it is not configured, perform the first-run status discovery and ask for mapping confirmation.
4. Resolve a Creator Record ID before any message, tracker edit, product move, or sample action. A blank, duplicate, or conflicting ID is an escalation, not an assumption.
5. Run the requested mode. Match product in the order ASIN/product URL, campaign context, explicit product name. Update the tracker, append the non-PII action log, and refresh the daily action queue.
6. Apply four stop-gates: creator-message sends, campaign publishing, MCF order creation, and Slack posts need a current operator instruction or matching local standing permission. Slack authorship follows the actor per `_local/slack-posting.md` (bot helper for background sweeps, the supervising operator's own identity in attended sessions).
7. Finish with a concise handoff: processed/skipped/flagged counts, tracker and queue changes, draft versus sent actions, evidence location, and remaining blocker.
