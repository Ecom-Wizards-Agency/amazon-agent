# Creator Connections

This folder is the human-facing operating hub for the Creator Connections workflow.

The runnable skill lives here:

`skills/amazon-creator-connections/`

Use this folder when someone wants the simple version of what the system does, how to run it, and what the manager should check before samples are sent.

## What this system does

- Launches or prepares Creator Connections campaigns from product information and campaign rules.
- Audits campaign inboxes for new creator inquiries, replies, confirmations, posted videos, and product-switch requests.
- Keeps one clean campaign-level tracker per product or campaign.
- Scores creators before sample approval so the team does not send samples to weak or unverified candidates.
- Tracks sample fulfillment through MCF once the manager approves the final details.
- Sends structured Slack sweep updates for new changes only.
- Produces weekly client-ready Creator Connections summaries for the internal Slack channel.

## Where to start

1. Open the campaign or brand in Amazon Creator Connections.
2. Open the matching campaign tracker.
3. Ask the agent to run the Creator Connections workflow.
4. The agent should verify the brand, campaign, product, ASIN, and active tracker before acting.
5. The agent should stop before sending creator replies, launching campaigns, or placing MCF sample orders unless the operator has approved the action.

## Main files

- `OPERATING PLAYBOOK.md`: Daily workflow, launch workflow, and sample workflow.
- `TRACKER RULES.md`: Tracker columns, statuses, scoring, and product-switch rules.
- `SLACK SWEEP FORMAT.md`: Daily and weekly Slack update format.
- `../skills/amazon-creator-connections/SKILL.md`: Runtime skill entrypoint for Codex and Claude.

## Non-negotiables

- Do not send samples without a verified product match, ASIN, address, and approval.
- Do not keep duplicate active creator rows across product trackers.
- If a creator switches products, keep the active row on the final chosen product.
- If the product choice is not final, move or keep the creator in an undecided holding area.
- Always verify the creator thread before sending any message.
- Keep client and creator private data out of repo documentation.
