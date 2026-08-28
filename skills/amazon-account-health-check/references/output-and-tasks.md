# Digest Contract, Notion Follow-Up Defaults, and Finish Note

## What The Run Posts

The run posts nothing. It reads, disposes every finding into the ledger, writes its coverage entry, and returns its structured result. A separate deterministic pass reads that ledger once a day and posts the single digest in `{daily_update_channel}`, covering every region together. That is why the run stays quiet: three region runs each posting a parent plus one comment per account produced roughly 1,900 words a day across three threads, including comments for accounts nobody had read. The reader wants one overview of what matters today.

The one exception is an **immediate escalation**, and only for something that cannot wait for the digest:

- an Amazon deactivation warning
- a policy deadline inside 3 days
- a high-severity finding with no owner

Post it the moment you find it. One line, in `{daily_update_channel}`, no thread, no parent post to hang it under. Then set `last_reported` on that finding so the digest does not repeat what the reader already saw.

Escalation line format:

```text
:red_circle: ESCALATE {@escalation_owner} - {account} {marketplace} - {issue}{, deadline DD.MM.YYYY} - {task link or task proposal}
```

Mention `{escalation_owner}` on escalation lines only, never anywhere else. Do not post this workflow to client-specific channels unless setup explicitly chooses that destination.

Dates in prose and in any posted line are `DD.MM.YYYY`. ISO `YYYY-MM-DD` is only for ledger day keys such as `coverage[YYYY-MM-DD]`. A `Mon D` stamp is not allowed anywhere: it is neither format, and the run is claimed by its coverage entry rather than by a post title, so a stamp like that reads as a date nobody can match.

## Severity Vocabulary

Four labels, exactly these, wherever a finding is labelled: the ledger, the digest, and an escalation line.

```text
ESCALATE
ACTION
ASSIGNED
WAITING
```

Do not invent a fifth. `CLEAN`, `WATCH` and `BLOCKED` are not labels in this workflow. A clean finding is disposed `No action needed` and simply does not appear. A blocker is not a finding label either: it goes in the finish note, and a browser blocker that stopped the run reading anything is posted by the runner's preflight before this check ever starts.

## What The Run Writes To The Ledger

The digest can only be as honest as the ledger, so per finding:

- disposition, severity, owner, task link, deadline, and the account, marketplace and scope that identify it
- `last_movement`: the date the observed state actually changed
- `last_reported`: set it when you post an immediate escalation, so the stall timer re-arms
- `impact`, `current_state`, `next_step`: the digest's card fields (summary is the Issue). Impact in money/risk terms; current_state is what the page showed this run, dated and refreshed every verifying run; next_step is one concrete action with a named owner. A finding without them renders as a one-line fallback instead of a card

And once per run, at the top level of the ledger:

- `coverage[YYYY-MM-DD][<region>]` with `checked`, `in_scope` and `skipped`, written even when the run failed, with `checked: 0`

Field semantics and the reasons behind them are in `dispositions-and-ledger.md`.

When a `{supervisor}` is configured, the weekly digest is built from ledger history by the same digest pass on the last run of the week: findings per account, new vs resolved counts, escalations raised, overdue count, and recurring or systemic patterns. Strategic summary, not a task list. The check itself still posts nothing.

## Notion Follow-Up Defaults

Follow-up tasks are how dispositions land in the human task system. Create or update tasks only when `{follow_up_task_database}` is configured. Do not create tasks during setup or dry runs unless the operator explicitly approves live task creation. Resolve the database and its schema at runtime; do not hardcode IDs.

Disposition mapping (update-don't-duplicate, matched by ledger key):

- No action needed: nothing.
- Action needed: create a task, then report the finding as Assigned.
- Assigned: comment on the existing task when the state changed; raise `Priority` or pull `Due` earlier when it worsened; reassign to `{escalation_owner}` only when it newly meets an escalation trigger.
- Waiting: update/comment the existing task with who it waits on and since when; set the closest waiting/blocked status the database offers; owner stays `{daily_runner}`.
- Escalate: task assigned to `{escalation_owner}` at the highest priority.

Never set a completed/done status and never close an escalation task - only the escalation owner resolves those. When a finding is verified resolved in Seller Central, comment `verified resolved {DD.MM.YYYY}`, set the ledger entry's `resolved_date` and `last_movement`, and leave the task open for the owner to close.

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
- Acceptance criteria, including a done-note on the task itself
- Stop-before-risk note
- The ledger key of the finding, and the date the state last moved

## Finish Note

The finish note is the run's structured JSON result. It is never posted to Slack: the digest pass owns the daily post, and duplicating the note there is exactly the noise the digest replaced.

Report:

- Counts by disposition, overdue count, and escalations raised.
- Any immediate escalation posted, with its finding key, so it is clear why the digest will not repeat it.
- The coverage entry written for this run: region, `checked`, `in_scope`, and the `skipped` list.
- Notion task titles and URLs created or updated, or the task proposals when the stage forbids live writes.
- Accounts checked or skipped.
- Ledger written yes/no, and which browser was used (preferred or fallback).
- Any blockers, including a missing or stale market-signal state file, login needs, or actions requiring the operator's approval.
