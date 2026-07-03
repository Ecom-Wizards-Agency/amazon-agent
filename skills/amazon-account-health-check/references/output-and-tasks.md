# Slack Output, Notion Follow-Up Defaults, and Finish Note

## Slack Output

Use one parent post per daily run in `{daily_update_channel}`. Do not post this workflow to client-specific channels unless setup explicitly chooses that destination. The parent post is the action queue - the daily runner's to-do list - not just a coverage list.

Parent format:

```text
Daily Amazon Account Health Check - {Mon D}

Action queue {@daily_runner}
1. :red_circle: ESCALATE {@escalation_owner} - {account} {marketplace} - {issue + deadline} - {task link}
2. :large_orange_circle: ACTION - {account} {marketplace} - {scope} {issue} - {next step} by {date} - {task link}
3. :large_yellow_circle: ASSIGNED - {account} {marketplace} - {issue} - {owner}, open {N}d{, OVERDUE} - {task link}
4. :hourglass_flowing_sand: WAITING - {account} {marketplace} - {issue} - waiting on {target}, day {N}{, deadline {date}} - {task link}

Clean: {N} of {M} accounts - no action needed
Skipped/blocked: {none / account + reason}
```

Order the queue: escalations first, then action items, then assigned-overdue, then assigned, then waiting. If the queue is empty, write exactly `Action queue: empty` - a missing parent post means the run failed, not that everything was clean. Mention `{escalation_owner}` only on escalation lines.

Thread comment per account:

```text
{{seller_central_name}} {{marketplace}}

Account Health
- Status: {Healthy / At risk / Issue found}
- AHR: {rating}
- Policy Compliance: {summary}

SellerSonar alerts
- {None / severity + alert summary / alert source stale ({date})}

Findings
- [{NO ACTION / ACTION / ASSIGNED / WAITING / ESCALATE}] {scope} - {issue} - owner {name} - {task link / deadline / waiting on}
```

Keep comments short and human-readable. Do not include raw tables unless an issue needs the detail.
If an account is fully clean, the Findings section is exactly: `No action needed.`

When a `{supervisor}` is configured, add one extra thread comment on the last run of the week starting with `Weekly digest {@supervisor}`: findings per account this week, new vs resolved counts, escalations raised, overdue count, and recurring or systemic patterns from ledger history. Strategic summary, not a task list.

## Notion Follow-Up Defaults

Follow-up tasks are how dispositions land in the human task system. Create or update tasks only when `{follow_up_task_database}` is configured. Do not create tasks during setup or dry runs unless the operator explicitly approves live task creation. Resolve the database and its schema at runtime; do not hardcode IDs.

Disposition mapping (update-don't-duplicate, matched by ledger key):

- No action needed: nothing.
- Action needed: create a task, then report the finding as Assigned.
- Assigned: comment on the existing task when the state changed; raise `Priority` or pull `Due` earlier when it worsened; reassign to `{escalation_owner}` only when it newly meets an escalation trigger.
- Waiting: update/comment the existing task with who it waits on and since when; set the closest waiting/blocked status the database offers; owner stays `{daily_runner}`.
- Escalate: task assigned to `{escalation_owner}` at the highest priority.

Never set a completed/done status and never close an escalation task - only the escalation owner resolves those. When a finding is verified resolved in Seller Central, comment `verified resolved {date}` and report it in the queue for the owner to close.

Default fields on creation:

- `Task Type`: `{default_task_type}`
- `Assignee`: `{daily_runner}`, or `{escalation_owner}` for escalations
- `Assigned Employee`: same person, when that relation exists
- `Due`: the earlier of the next business day or (marketplace deadline minus 2 days)
- `Status`: `Not Started`
- `Brand` or account relation: match from the configured account profile source, when available

Priority mapping:

- Critical account deactivation risk, suspension, active policy violation, urgent deadline: `Urgent`
- New seller/hijacker risk, search suppression, important Featured Offer issue, shipment defect above threshold: `High`
- Rating/category/pricing issue without immediate account risk: `Normal`
- Informational or resolved issue: do not create a task unless requested

Task body must include:

- Context
- Evidence
- Objective
- Acceptance criteria, including posting a done-note in the daily update thread
- Stop-before-risk note
- Link to the day's account thread comment and the ledger key

## Finish Note

Report:

- Slack parent link and account comment link.
- Queue counts by disposition, overdue count, and escalations raised.
- Notion task titles and URLs created or updated.
- Accounts checked or skipped.
- Ledger written yes/no, and which browser was used (preferred or fallback).
- Any blockers, login needs, or actions requiring the operator approval.
