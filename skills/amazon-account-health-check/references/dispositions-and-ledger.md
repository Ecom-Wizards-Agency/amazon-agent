# Findings Ledger, Dispositions, and Routing

## Findings Ledger

Maintain a private findings ledger at `{findings_ledger_path}`, stored locally next to the automation. The ledger is the automation's memory only - finding identity, history, and links to follow-up tasks - so findings are never forgotten or duplicated between runs. It is not a task system: `{follow_up_task_database}` remains the human task source of truth. Never commit the ledger to the repo or GitHub.

- Finding key: `{account}|{marketplace}|{scope}|{issue_type}`, where scope is `ASIN:<asin>` for listing-level issues, `ACCOUNT` for account-level issues (order metrics, verification, Account Health Rating), or `CASE:<id>` for case-only threads.
- Entry fields: key, account, marketplace, scope, asin, case_id, issue_type, summary, severity (critical/high/medium/low), disposition, owner, task URL, first_seen, last_verified, last_status, deadline, waiting_on, waiting_since, resolved_date.
- If an account is skipped or blocked today, carry its entries forward unchanged. Never infer resolved from a missed check.
- Set resolved_date only after Seller Central verification. Keep resolved entries 30 days for dedup, then prune.
- Write the full updated ledger exactly once, at the end of the run, including degraded runs.
- First run: seed the ledger by sweeping the open follow-up tasks in `{follow_up_task_database}` for in-scope accounts, keeping their current assignees.

## Disposition and Routing

Dispositions are the workflow's internal routing layer: they decide what happens to each finding, then map into `{follow_up_task_database}`. They never replace task-system statuses. Before the run ends, every finding - new or carried over - must have exactly one disposition:

- **No action needed**: clean, informational, or verified resolved. No task.
- **Action needed**: new actionable issue with no owner yet. Create a follow-up task in the same run (default assignee `{daily_runner}`), then report the finding as Assigned.
- **Assigned**: an open task already exists. Report owner, task age in days, and an OVERDUE flag when past due. Comment on the task when the state changed; raise priority or pull the due date earlier when it worsened.
- **Waiting**: action taken, now pending an external party (marketplace case reply, client documents, reinstatement review). Update the task with who it waits on and since when; set the task status to the closest waiting/blocked status the database offers. Owner stays `{daily_runner}`.
- **Escalate**: meets an escalation trigger. Task assigned to `{escalation_owner}` at the highest priority, plus an escalation line in the daily output mentioning `{escalation_owner}`.

Escalation triggers (exhaustive - everything else defaults to `{daily_runner}`):

- account deactivation/suspension or an explicit deactivation warning
- any decision at a stop-before-risk point (appeal, acknowledgement, support reply, document upload)
- identity, bank, tax, or verification requests
- legal, IP, or counterfeit claims
- a hard marketplace deadline within 48 hours that is not already handled
- Seller Central login/MFA blockers after both approved browsers were tried

Severity maps to default routing: Critical findings are escalation candidates; High and Medium route to `{daily_runner}`; Low is No action needed unless recurring.

Degraded run (Seller Central blocked in both approved browsers): still post the action queue built from the ledger plus the alert source, mark every Seller-Central-dependent line `not verified today`, add the login blocker itself as an escalation line, and still write the ledger under the carry-forward rule.
