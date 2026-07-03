---
name: amazon-creator-connections
description: Use for Amazon Creator Connections work — auditing/triaging the creator message inbox, mapping messages to products and campaign tracker tabs, drafting creator replies (operator-confirmed sends), preparing campaigns up to the publish checkpoint, creating/reconciling tracker tabs, and finding tracker gaps. Trigger on requests like go through the Creator Connections messages, run the message audit, update the creator tracker, answer the creators, prepare a Creator Connections campaign, or reconcile the creator system.
---

# Amazon Creator Connections

## Core Rule

Creator Connections lives behind the Amazon Ads login and has no MCP — all inbox, campaign, and tracker-verification work happens in the connected browser (Codex operates the browser per the repo role split). Reading messages, updating the tracker sheet, and drafting replies are normal work. **Sending any creator message and publishing any campaign are stop-before-risk actions**: each needs the operator's explicit approval of that exact action in the current chat, or a matching `_local/local-permissions.md` standing permission.

Do not process message threads whose status marks them inactive (declined/expired/closed — the "red" threads). The skip rule is client-confirmed and stored in local memory; until it is confirmed, follow the first-run discovery step below and skip nothing silently.

## Modes

Default mode is the message audit. The others are documented in `references/workflows.md`:

- `audit` — triage inbox messages, match to products, update tracker tabs, draft replies (default).
- `campaign` — prepare a new campaign from a reference campaign; stop before publish.
- `tracker` — create a campaign-level tracker tab from a live campaign.
- `gaps` — find campaigns/ASINs with no matching tracker tab.
- `reconcile` — full-system audit across campaigns, messages, samples, content, and tabs.

## Required Inputs

If needed information is missing, ask briefly:

```text
I need the client/brand, marketplace, Amazon Ads account label, the tracker Google Sheet URL, and the message scope (since the previous tracker update / last 24 hours / last 7 days / all messages) — unless a local config already covers this client.
```

Scope options (from the original builder): since the previous tracker update, the last 24 hours, the last 7 days, or all available messages. Default to "since the previous tracker update" when the tracker shows a last-updated marker; otherwise ask.

## Local Memory

Per-client settings live in `_local/creator-connections/<client>-config.json` (the `_local/` folder is gitignored — never copy real brand names, account labels, sheet URLs, creator names, or addresses into tracked files). Check it before asking for inputs; create it after the first run. Template:

```json
{
  "client": "<client name>",
  "brand": "<brand as shown in Creator Connections>",
  "advertiser": "<Amazon Ads account label>",
  "marketplace": "<e.g. United States>",
  "profiles": ["<message profile(s), if the account has more than one>"],
  "tracker_sheet_url": "<Google Sheet URL>",
  "status_filter": {
    "confirmed": false,
    "skip_statuses": [],
    "process_statuses": [],
    "notes": "Filled and operator-confirmed during the first supervised run"
  },
  "reply_policy": {
    "auto_send": false,
    "notes": "Sends stay operator-approved per batch until a matching _local/local-permissions.md entry exists"
  }
}
```

Recurring quirks (UI oddities, tracker conventions, reply-tone tweaks) go in `_local/creator-connections/local-notes.md`.

## Navigation

Use the Creator Connections route from `AGENTS.md` (Amazon Ads Account Selection): Campaign Manager → top-right account selector → `Brand content` → `Creator connections`. Never start from the direct account chooser. Run the standard connected-browser checkpoint (logged in, correct account/brand, marketplace, visible page title) before touching anything.

## Message Triage (status filter)

1. Enumerate the message threads in scope, newest first. Record thread count before filtering.
2. Read each thread's visible status indicator (pill/label/color).
3. **If `status_filter.confirmed` is false (first supervised run):** screenshot one example of every distinct status pill/color to `evidence/<client>/creator-connections/`, list which statuses look inactive (declined, expired, closed, rejected offers), propose the skip/process mapping to the operator, and only apply it after the operator confirms. Save the confirmed rule into the client config.
4. **If confirmed:** skip threads matching `skip_statuses`, process the rest. Always report skipped-vs-processed counts by status in the handoff — skipped threads are listed, never silently dropped.

## Match + Track

Match each processed inquiry in this order: exact ASIN or Amazon product URL; visible campaign reference; explicit product name. Flag ambiguous or multi-product threads for manager review — do not guess.

Update the correct campaign-level tab in the tracker sheet. Preserve the exact columns, dropdowns, formatting, and the one-row-per-creator-per-campaign rule (`references/tracker-schema.md`). Capture verified full names and addresses when present, sample status and date only when shipment is confirmed, the product, Content Posted Yes/No, verified content links, and concise evidence notes. Identify inquiries whose product has no tracker tab and flag them for `gaps` mode.

## Reply Drafting

For each processed thread that needs an answer (sample requests, creator questions, content submissions, follow-ups), draft a reply using `references/reply-playbook.md` plus the thread and tracker context. Then:

1. Present the full batch to the operator: thread/creator, thread status, the draft, and why it's needed.
2. **STOP before sending.** Send only the drafts the operator explicitly approves in the current chat, or those covered by a matching `_local/local-permissions.md` standing permission (scope must name Creator Connections replies for this client; mention in the operator note when a standing permission was used).
3. After approved sends, record the reply in the tracker Notes and re-verify each thread shows the sent message.

The intended maturity path: first runs are fully operator-approved; once the operator trusts the drafts, they add a standing-permission entry for routine reply types and sends become a routine — no new mechanism needed.

## Handoff Report

When finished, tell the operator:

- account/brand, marketplace, and scope covered
- threads found / processed / skipped (by status) / flagged for manager review
- tracker tabs and rows updated, plus products with no tracker tab
- replies drafted vs sent (and under which approval)
- evidence saved under `evidence/<client>/creator-connections/`
- anything blocked and the next exact action

Keep the report concise. If work continues in another agent, leave the standard cross-agent handoff per `AGENTS.md`.

## References

- `references/workflows.md` — the campaign / tracker / gaps / reconcile modes.
- `references/reply-playbook.md` — reply templates and tone rules.
- `references/tracker-schema.md` — tracker columns, dropdowns, and tab conventions.
