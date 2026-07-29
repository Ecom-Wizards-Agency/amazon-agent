---
name: amazon-creator-connections
description: Use for Amazon Creator Connections operations: launching Creator Connections campaigns, auditing and triaging creator inboxes, mapping creators to campaign-level Google Sheet trackers, scoring creators before sample approval, drafting/sending operator-approved creator replies, tracking sample fulfillment/MCF, monitoring posted content, posting daily/weekly Slack sweep updates, reconciling product switches, and maintaining campaign tracker tabs. Trigger on requests like run a Creator Connections sweep, check new creator messages, create/update a campaign tracker, launch a Creator Connections campaign, score sample candidates, prepare MCF sample details, update the priority sample lane, post a Slack sweep, or explain the Creator Connections system.
---

# Amazon Creator Connections

Browser: Codex interactive

Use this skill for the Creator Connections operating system across brands. It is a front-end/browser workflow, supported by a campaign-level Google Sheet tracker and Slack sweep updates. It does not require an Amazon Ads API.

Creator Connections lives behind Amazon Ads login and currently has no direct MCP/API. Use the connected browser for Amazon Ads/Creator Connections and use Google Sheets/Slack connectors where available for tracker and reporting work.

## What this system can do

- Launch or prepare Creator Connections campaigns from a reference campaign, with matching naming convention, product-specific description, dates, budget, commission, and ASIN/product details.
- Create or update campaign-level tracker tabs that can be shared with clients.
- Sweep Creator Connections messages for new inquiries, replies, address confirmations, sample requests, product switches, posted content, and follow-ups.
- Map every creator to the correct product/campaign by exact ASIN or product URL first, then visible campaign context, then explicit product name.
- Keep undecided or ambiguous creators in an `Undecided` holding tab until they confirm their final product/ASIN.
- Score creators against the qualification gate before recommending samples.
- Draft creator replies for verification, proof requests, product-switch clarification, paused-product messaging, content follow-ups, sample confirmations, and thank-you messages.
- Prepare MCF sample fulfillment details after the operator approves and the creator has passed the gate.
- Update trackers with sample decisions, MCF/order details, posted content links, notes, follow-up dates, and qualification evidence.
- Post daily/weekly Slack sweep updates with only new updates and material status changes.
- Explain the whole workflow to a manager/client in plain language.

## Core rules

1. Verify before acting.
   - Verify account/brand, marketplace, campaign, creator thread, product/ASIN, and tracker tab before updating or sending.
   - Never guess a product match.
   - Always double-check the creator identity before replying or preparing sample details.

2. Draft before sending unless explicitly approved.
   - Creator messages, campaign publishing, sample approval, and MCF order creation are stop-before-risk actions.
   - Present drafts first unless the operator explicitly says to send that exact message/action in the current chat or a standing permission in `_local/local-permissions.md` covers it.
   - For edge cases, always draft first: ambiguous product, product switch, repeated/spammy outreach, paused-product messaging, legal/payment claims, unusual fulfillment, or anything that could create client risk.

3. Keep private data out of code and PRs.
   - Creator names, addresses, emails, phone numbers, tracker URLs, Slack links, and real client data belong in the live tracker, browser, Slack, or `_local/` only.
   - Do not put private data in tracked repo files, skill examples, tests, or PR descriptions.

4. One active row per creator per final product/campaign.
   - Update existing rows when possible.
   - If a creator swaps products, move/track them under the latest confirmed product after confirmation.
   - Do not leave redundant active rows in old product tabs.
   - If the creator has not chosen a final product/ASIN, put them in `Undecided`.

5. Tight sample gate.
   - Prefer 10/10 before samples.
   - A-tier candidates can be surfaced for manager/operator review only when product match is exact, risk is low, and missing items are clearly understood.
   - Never send samples just because a creator asks.
   - Watch for ghosting risk, repeated identical messages, guaranteed-review wording, missing product match, missing proof, or recipient/content-creator mismatch.

## How to use

Use natural requests:

- “Run today’s Creator Connections sweep.”
- “Check who is ready for samples.”
- “Draft verification messages for first-base candidates.”
- “Create a tracker tab for this active campaign.”
- “Prepare sample details for this approved creator.”
- “Post the sweep to Slack.”
- “Launch a campaign for this ASIN using the reference campaign.”
- “Explain the Creator Connections workflow to my manager.”

Before starting operational work, identify:

- brand/client and marketplace
- Amazon Ads account/profile
- tracker Google Sheet
- campaign or product/ASIN scope
- message scope: new since last sweep, last 24 hours, last 7 days, or all messages

Use `_local/creator-connections/<client>-config.json` when available so the operator does not need to repeat these details.

## Modes

Default mode is `audit`. Read the relevant reference file before acting:

- `audit`: read `references/workflows.md`, `references/tracker-schema.md`, and `references/reply-playbook.md`.
- `campaign`: prepare a new campaign; read `references/workflows.md`.
- `tracker`: create/repair tracker tabs; read `references/tracker-schema.md`.
- `gaps`: find campaigns or message products missing tracker tabs; read `references/workflows.md`.
- `reconcile`: full-system audit across campaigns, messages, samples, content, and tabs; read `references/workflows.md`.
- `samples`: prepare sample/MCF lane work; read `references/sample-and-slack-ops.md`.
- `slack`: daily/weekly sweep updates; read `references/sample-and-slack-ops.md`.

## Local memory

Per-client settings live in `_local/creator-connections/<client>-config.json`. `_local/` is gitignored.

Use this shape:

```json
{
  "client": "<client name>",
  "brand": "<brand shown in Creator Connections>",
  "advertiser": "<Amazon Ads account label>",
  "marketplace": "United States",
  "profiles": ["<message profile names>"],
  "tracker_sheet_url": "<private tracker URL>",
  "slack_channel_id": "<internal Slack channel ID>",
  "status_filter": {
    "confirmed": false,
    "skip_statuses": [],
    "process_statuses": []
  },
  "reply_policy": {
    "auto_send": false,
    "notes": "Routine sends require current approval unless standing permission exists."
  }
}
```

Put recurring UI quirks, approved wording, and client-specific exceptions in `_local/creator-connections/local-notes.md`.

## Browser and navigation

Use the connected browser for Amazon Ads. Run the browser checkpoint before changing anything:

- logged in
- correct Amazon Ads account/brand
- correct marketplace
- correct campaign or Creator Connections page
- visible page title/context matches the task

Navigate through Amazon Ads where possible:

Campaign Manager → account selector → Brand content → Creator connections.

If authentication is unavailable, stop and ask the operator to log in. Do not use stale browser data for live sweeps or Slack posts.

## Matching and tracker update order

Match creator inquiry to product/campaign in this order:

1. exact ASIN or Amazon product URL in the thread
2. visible campaign context
3. explicit product name
4. manager/operator decision

If multiple products appear, or if the creator switches products, hold until final product/ASIN is confirmed. Use the `Undecided` tab for unresolved product matches.

## Handoff report

Finish with:

- account/brand, marketplace, and scope covered
- threads processed/skipped/flagged
- tracker tabs and rows updated
- replies drafted vs sent
- sample-ready priority lane and blockers
- Slack links if posted
- exact next actions

Keep reports concise and operational.

## References

- `references/workflows.md`: campaign, tracker, gaps, audit, and reconcile workflows.
- `references/tracker-schema.md`: tracker columns, statuses, qualification gate, and tab rules.
- `references/reply-playbook.md`: approved message patterns and draft/send rules.
- `references/sample-and-slack-ops.md`: sample/MCF workflow, priority lane, and Slack sweep format.
