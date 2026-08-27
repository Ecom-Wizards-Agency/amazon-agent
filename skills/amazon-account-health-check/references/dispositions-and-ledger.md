# Findings Ledger, Dispositions, and Routing

## Findings Ledger

Maintain a private findings ledger at `{findings_ledger_path}`, stored locally next to the automation. The ledger is the automation's memory only - finding identity, history, and links to follow-up tasks - so findings are never forgotten or duplicated between runs. It is not a task system: `{follow_up_task_database}` remains the human task source of truth. Never commit the ledger to the repo or GitHub.

- Finding key: `{account}|{marketplace}|{scope}|{issue_type}`, where scope is `ASIN:<asin>` for listing-level issues, `ACCOUNT` for account-level issues (order metrics, verification, Account Health Rating), or `CASE:<id>` for case-only threads.
- Entry fields: key, account, marketplace, scope, asin, case_id, issue_type, summary, severity (critical/high/medium/low), disposition, owner, task URL, first_seen, last_verified, last_status, last_movement, last_reported, deadline, waiting_on, waiting_since, resolved_date, impact, current_state, next_step.
- If an account is skipped or blocked today, carry its entries forward unchanged. Never infer resolved from a missed check.
- Set resolved_date only after Seller Central verification. Keep resolved entries 30 days for dedup, then prune.
- Write the full updated ledger exactly once, at the end of the run, including degraded runs.
- First run: seed the ledger by sweeping the open follow-up tasks in `{follow_up_task_database}` for in-scope accounts, keeping their current assignees.

## Fields The Digest Depends On

The run posts nothing, so the digest is only as honest as what the ledger says. Three of these fields are not optional.

- `last_movement`: the date the finding's observed state actually CHANGED. Not the date you looked at it. `last_seen` and `last_verified` cannot tell "checked again, unchanged" apart from "got worse today", and that difference is what the digest uses to choose between staying silent and printing a line. Set it only when something moved: a new deadline, a status change, a worse severity, a resolution. Leave it alone on an unchanged re-check.
- `impact`, `current_state`, `next_step`: the three narrative fields behind the digest's approved card layout (`• *Issue:* / *Impact:* / *Current state:* / *Next step:*`; `summary` is the Issue). `impact` says why it matters in money or risk terms. `current_state` says exactly what the page showed THIS run, dated — refresh it on every run that verifies the finding. `next_step` is the single concrete action with a named owner (`<@slack-id> — do X by date`); touch `impact` and `next_step` only when they actually change. A finding without these fields renders as a compact one-liner instead of a card, so writing them is what upgrades the finding's visibility.
- `last_reported`: the date the finding last appeared in a digest or in an immediate escalation. Set it yourself when you post an immediate escalation; the digest pass maintains it otherwise. It re-arms the stall timer, so a stuck item nags on a cadence instead of repeating itself every single morning until the reader stops reading.
- `coverage[YYYY-MM-DD][<region>]`: a TOP-LEVEL ledger key, not a field on a finding. Each region run writes one object with `checked`, `in_scope` and `skipped` (a list of `Account MKT (reason)` strings). Write it even when the run failed, with `checked: 0`, because this entry is also the run's claim: `guard.py` reads exactly this key to decide whether the region already ran today, and a missing entry gets the run retried into a loop. A region with no entry is reported as **pending** and is never folded into the checked count. Do not skip the write to keep the numbers tidy. On 12.08.2026 a run that read zero of nine accounts still produced a post that implied full coverage, which is the failure this field exists to make impossible.

## Disposition and Routing

Dispositions are the workflow's internal routing layer: they decide what happens to each finding, then map into `{follow_up_task_database}`. They never replace task-system statuses. Before the run ends, every finding - new or carried over - must have exactly one disposition:

- **No action needed**: clean, informational, or verified resolved. No task.
- **Action needed**: new actionable issue with no owner yet. Create a follow-up task in the same run (default assignee `{daily_runner}`), then report the finding as Assigned.
- **Assigned**: an open task already exists. Report owner, task age in days, and an OVERDUE flag when past due. Comment on the task when the state changed; raise priority or pull the due date earlier when it worsened.
- **Waiting**: action taken, now pending an external party (marketplace case reply, client documents, reinstatement review). Update the task with who it waits on and since when; set the task status to the closest waiting/blocked status the database offers. Owner stays `{daily_runner}`.
- **Escalate**: meets an escalation trigger. Task assigned to `{escalation_owner}` at the highest priority. The digest picks the finding up from the ledger and carries it, so no post is needed from the run. Post an immediate one-line escalation only when it cannot wait for the digest (deactivation warning, policy deadline inside 3 days, high-severity finding with no owner), and then set `last_reported` so the digest does not repeat it. Format in `output-and-tasks.md`.

Escalation triggers (exhaustive - everything else defaults to `{daily_runner}`):

- account deactivation/suspension or an explicit deactivation warning
- any decision at a stop-before-risk point (appeal, acknowledgement, support reply, document upload)
- identity, bank, tax, or verification requests
- legal, IP, or counterfeit claims
- a hard marketplace deadline within 48 hours that is not already handled
- Seller Central login/MFA blockers after both approved browsers were tried

Severity maps to default routing: Critical findings are escalation candidates; High and Medium route to `{daily_runner}`; Low is No action needed unless recurring.

Degraded run (Seller Central blocked in both approved browsers): write the ledger under the carry-forward rule and write the coverage entry for the region with `checked: 0` and the blocked accounts in `skipped`. Carry every unverified finding forward untouched: never re-dispose it, never mark it resolved, and never restate it as verified today. Report the login blocker in the finish note, and post nothing beyond an immediate escalation if the blocker itself meets that bar. There is no queue post to fall back on, so a degraded run is visible through its coverage entry and the digest's pending count, not through a post.
