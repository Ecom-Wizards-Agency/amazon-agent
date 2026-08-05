---
name: amazon-creator-connections
description: Use for Amazon Creator Connections operations: campaign preparation, creator inbox audits, campaign-level Google Sheet tracking, identity-safe qualification, operator-authorized creator replies and MCF fulfillment, posted-content monitoring, product-switch reconciliation, and Slack-helper sweep reporting. Trigger on requests like run a Creator Connections sweep, check new creator messages, create/update a campaign tracker, launch a Creator Connections campaign, score sample candidates, prepare MCF sample details, update the priority sample lane, post a Slack sweep, or explain the Creator Connections system.
---

# Amazon Creator Connections

Browser: Codex interactive

Use this skill for the Creator Connections operating system across brands. It is a front-end/browser workflow, supported by a campaign-level Google Sheet tracker and Slack sweep updates. It does not require an Amazon Ads API.

Creator Connections lives behind Amazon Ads login and currently has no direct MCP/API. Use the connected browser for Amazon Ads/Creator Connections and use Google Sheets/Slack connectors where available for tracker and reporting work.

## What this system can do

- Launch or prepare Creator Connections campaigns from a reference campaign, with matching naming convention, product-specific description, dates, client-approved budget, commission, and ASIN/product details.
- Create or update campaign-level tracker tabs that can be shared with clients.
- Sweep Creator Connections messages for new inquiries, replies, address confirmations, sample requests, product switches, posted content, and follow-ups.
- Map every creator to the correct product/campaign by exact ASIN or product URL first, then visible campaign context, then explicit product name.
- Keep undecided or ambiguous creators in an `Undecided` holding tab until they confirm their final product/ASIN.
- Score creators against the qualification gate before recommending samples.
- Draft creator replies for verification, proof requests, product-switch clarification, paused-product messaging, content follow-ups, sample confirmations, and thank-you messages.
- Prepare MCF sample fulfillment details after the operator approves and the creator has passed the gate.
- Update trackers with sample decisions, MCF/order details, posted content links, notes, follow-up dates, and qualification evidence.
- Prepare daily/weekly Slack sweep updates with only new updates and material status changes, then post only through the configured helper when authorized.
- Explain the whole workflow to a manager/client in plain language.

## Core rules

1. Resolve the record before acting.
   - Every action must be tied to a Creator Record ID. Resolve it through the registry and composite identity evidence, not display name alone.
   - A blank, duplicate, or conflicting record is a stop condition. Do not send, move, update, or fulfill until it is resolved.

2. Verify before acting.
   - Verify account/brand, marketplace, campaign, creator thread, product/ASIN, and tracker tab before updating or sending.
   - Never guess a product match.
   - Always double-check the creator identity before replying or preparing sample details.

3. Use the four stop-gates.
   - Creator-message sends, campaign publishing, MCF order creation, and Slack posting are externally visible actions.
   - Each requires the operator's current approval or a matching local standing permission.
   - Slack posts must use the configured posting helper. The Slack connector is for reading or operator-requested personal drafts only.

4. Draft before sending unless explicitly approved.
   - Present drafts first unless the operator explicitly says to send that exact message/action in the current chat or a standing permission in `_local/local-permissions.md` covers it.
   - For edge cases, always draft first: ambiguous product, product switch, repeated/spammy outreach, paused-product messaging, legal/payment claims, unusual fulfillment, or anything that could create client risk.

5. Keep private data out of code and PRs.
   - Creator names, addresses, emails, phone numbers, tracker URLs, Slack links, and real client data belong in the live tracker, browser, Slack, or `_local/` only.
   - Do not put private data in tracked repo files, skill examples, tests, or PR descriptions.

6. One active row per creator per final product/campaign.
   - Update existing rows when possible.
   - If a creator swaps products, move/track them under the latest confirmed product after confirmation.
   - Do not leave redundant active rows in old product tabs.
   - If the creator has not chosen a final product/ASIN, put them in `Undecided`.

7. Tight sample gate.
   - A sample requires 10/10. Lower scores remain in verification or hold states.
   - A-tier candidates can be surfaced for review only when product match is exact, risk is low, and missing items are clearly understood.
   - Never send samples just because a creator asks.
   - Watch for ghosting risk, repeated identical messages, guaranteed-review wording, missing product match, missing proof, or recipient/content-creator mismatch.

8. Background-check first.
   - Before asking a creator for proof or fulfillment details, check what is visible from the creator profile, Amazon storefront, recent shoppable videos, Earns Revenue badge, attached product cards, media kit, and public social/portfolio links.
   - Populate the tracker qualification gate from verifiable public/visible evidence first.
   - If the creator qualifies from the background check, ask only for the basic fulfillment details needed to send the sample: full name, complete shipping address, email, phone, and final product/ASIN confirmation.
   - Ask for extra proof only when the visible background check cannot verify enough activity, fit, or performance to make a sample decision.

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

- `audit`: read `references/workflows.md`, `references/lifecycle-execution-guardrails.md`, `references/tracker-schema.md`, and `references/reply-playbook.md`.
- `campaign`: prepare a new campaign; read `references/workflows.md`.
- `tracker`: create/repair tracker tabs; read `references/tracker-schema.md`.
- `gaps`: find campaigns or message products missing tracker tabs; read `references/workflows.md`.
- `reconcile`: full-system audit across campaigns, messages, samples, content, and tabs; read `references/workflows.md`.
- `samples`: prepare or execute permitted sample/MCF lane work; read `references/lifecycle-execution-guardrails.md` and `references/sample-and-slack-ops.md`.
- `slack`: prepare or post permitted daily/weekly sweep updates; read `references/sample-and-slack-ops.md`.
- `explain`: explain the operating model to a manager/client; read `references/workflows.md`.

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

## Deterministic control runner

Before a state-changing action, use `tools/creator-connections-control/creator_control.py` with local, private run files. It is the required guardrail for record resolution, the computed 10/10 gate, daily queue generation, and MCF pre-flight.

- Issue or resolve the immutable Creator Record ID with `register`. Never assign an ID from a name, row number, or spreadsheet formula.
- Run `score` after every background check or creator reply. Do not overwrite the score with a manually typed value when its visible evidence no longer supports it.
- Build the dated machine-readable queue with `queue` before the daily sweep. Sync its results to `Daily Action Queue` and `Creator Action Log` only after the record ID is resolved.
- Run `preflight` immediately before any MCF order. A `HOLD` result means no order and an escalation. Until SP-API access is authorized, MCF creation remains a controlled browser/operator action after a passing pre-flight.

See `tools/creator-connections-control/README.md` for the input format and local HMAC-secret setup. Never commit run files, the registry, screenshots, raw addresses, or the HMAC secret.

The shared tracker is the sole durable system of record. The daily bot is the sole routine executor. The local runner is disposable validation state and Slack is reporting only. Read the current tracker row and resolved Creator Record ID before every external action, then write the result back before moving to another creator.

## Status filter and evidence

Creator Connections does not provide a reliable native status filter. The configured filter is the team's own classification after the thread is read.

- On the first supervised run, when `status_filter.confirmed` is false, capture one example of each visible inactive or active status signal to `evidence/<client>/creator-connections/`.
- Propose the process/skip mapping to the operator, then save the approved mapping in the local client configuration.
- Once confirmed, list processed and skipped counts by status. Never silently skip an inactive thread.
- Keep screenshots, campaign warnings, product-selection evidence, and MCF pre-flight evidence in the same local evidence path. Do not commit this folder.

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

When work changes agent or session, create the standard cross-agent handoff using `docs/handoff-template.md`. Include the Creator Record ID, current lock/gate state, selected row/tab, evidence reference, and the exact no-go condition. Never put private contact details in the handoff.

## References

- `references/workflows.md`: campaign, tracker, gaps, audit, and reconcile workflows.
- `references/tracker-schema.md`: tracker columns, statuses, qualification gate, and tab rules.
- `references/lifecycle-execution-guardrails.md`: record identity, lifecycle transitions, MCF gates, cadence, audit records, and escalation rules.
- `references/reply-playbook.md`: approved message patterns and draft/send rules.
- `references/sample-and-slack-ops.md`: sample/MCF workflow, priority lane, and Slack sweep format.
