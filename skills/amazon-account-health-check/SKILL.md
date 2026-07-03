---
name: amazon-account-health-check
description: Use for daily Amazon account health checks across Seller Central accounts: re-checking open findings from a local findings ledger, reading an alert source such as SellerSonar, checking Seller Central Account Health, disposing every finding (no action / action needed / assigned / waiting / escalate), posting a daily action-queue thread with one account comment per account, and creating or updating follow-up tasks for actionable account-health issues.
---

# Amazon Account Health Check

Use this skill for recurring or ad hoc daily account health checks.

Trigger phrases include `daily account health check`, `account health sweep`, `run account health`, `check account health for accounts`, and requests to post a daily account-health thread.

## First-Run Setup

Before creating or running a recurring automation, ask for and record local configuration. Do not commit this configuration to GitHub.

Required setup values:

- `{account_profile_source}`: where active account profiles live, such as Notion, a local CSV, or a local JSON cache.
- `{seller_central_name_field}`: the profile field used to select the Seller Central account. Recommended field name: `Seller Central Name`.
- `{marketplace_field}`: the profile field used to select the country/marketplace. Recommended field name: `Marketplace`.
- `{daily_update_channel}`: the Slack channel or other destination for parent posts and account comments.
- `{sellersonar_alert_source}`: the Slack channel, dashboard, CSV, or other alert source used for first-pass alert triage.
- `{follow_up_task_database}`: optional task database or tracker for follow-up work.
- `{default_task_type}`: optional task type for follow-ups, such as `Troubleshooting`.
- `{daily_runner}`: the person who works the daily action queue and is the default owner of every follow-up task. Record their chat member ID and task-system person ID so mentions and assignments resolve correctly.
- `{escalation_owner}`: the person who receives true escalations only. Record their chat member ID and task-system person ID. Mention them only on escalation lines, never on clean runs.
- `{supervisor}`: optional strategic supervisor who receives a weekly digest instead of daily output. Record their chat member ID.
- `{findings_ledger_path}`: local path of the private findings ledger JSON, stored next to the automation, never in the repo or GitHub.
- `{preferred_browser}`: the operator's locally saved browser preference for all live runs - the built-in in-app browser, or a Chromium browser connected through the browser extension (such as Chrome or Brave). The non-preferred approved browser is the fallback.
- `{schedule}` and `{timezone}`: optional local recurring automation schedule.

Ask which accounts and marketplaces should run before creating a local automation. Account names, marketplace lists, channel IDs, Notion IDs, assignees, schedules, and local paths are runtime configuration, not source-controlled skill content.

## Source Order

1. `{account_profile_source}` for active profiles, `{seller_central_name_field}`, and `{marketplace_field}`.
2. `{sellersonar_alert_source}` for the first alert pass.
3. Seller Central in the internal browser as the source of truth.
4. SellerSonar dashboard only when the alert source is grouped, truncated, incomplete, or needs filtering.

## Browser Rules

- Use `{preferred_browser}` for all live runs. Two browsers are approved for this workflow: the built-in in-app browser, and a Chromium browser connected through the browser extension (such as Chrome or Brave; typically requires the operator's US VPN). Whichever the operator saved as preferred is the default for every browser step; the other approved browser is the fallback.
- Step 1 of every live run is opening `{preferred_browser}` and confirming Seller Central is logged in before any account checks begin.
- If Seller Central is not logged in or shows login or verification in the preferred browser, try the fallback browser before declaring the run blocked, and note the fallback in the finish report. If both are blocked, run the degraded-run procedure (see Disposition and Routing) and escalate the login blocker.
- Parallel tabs are allowed only across regions (for example one US Seller Central tab plus one Europe tab), because regions are separate Seller Central sessions. Never open two tabs within the same regional Seller Central domain - they share one session and account selector, and switching account in one tab silently switches the other.
- Verify account, marketplace, page title/tool, and date/filter context before recording.
- Repeat verification after account/marketplace switches, tool switches, or session timeouts.
- Never click `Submit appeal` during an account-health check unless the operator is present and has explicitly approved that exact action.
- Stop before appeals, acknowledgements, support contact, support replies, listing edits, shipment actions, messages, uploads, or account-changing actions.

## Check Sequence

Step 0 of every run, before any new checks: re-check open findings. Load `{findings_ledger_path}` and the open follow-up tasks it links for in-scope accounts. Every open finding gets re-verified in Seller Central during its account's check and re-disposed (see Disposition and Routing) - the run starts by answering "what was still open yesterday, and what is its status today?", not by looking for new issues.

Process account-marketplaces by region in this order:

1. Europe accounts first.
2. US accounts second.
3. Any remaining non-Europe, non-US marketplaces last, unless the operator gives a different order.

Within each region, keep a stable marketplace/account order for the run so Slack output is easy to scan.

For each account-marketplace:

1. Open `{preferred_browser}` and confirm Seller Central is logged in.
2. Read the latest report from `{sellersonar_alert_source}`. Freshness guard: if the latest report is older than the previous business day, never report `No alerts` - report `alert source stale ({report date})` and treat alert-source checks as not performed.
3. Record relevant alerts:
   - search suppression
   - Buy Box / Featured Offer suppression or drop
   - new seller or possible hijacker
   - category/sub-category change
   - rating/review drop
   - major price or offer change
4. Open Seller Central and verify the account by `{seller_central_name_field}` and the country/region by `{marketplace_field}`.
5. Check Account Health:
   - overall status and Account Health Rating
   - Policy Compliance categories and `View all`
   - `Review details` for any nonzero policy row when present
   - affected ASIN/SKU, reason, date, status, deadline, Account Health Rating impact, and next-step labels
6. Check Performance Notifications since the last run.
7. Check order/shipping metrics:
   - ODR, A-to-z, chargebacks
   - cancellation, late shipment, valid tracking, on-time delivery
8. Check homepage action indicators and product/listing health:
   - Actions tab
   - Product Performance status
   - Featured Offer %
   - active/suppressed/inactive/pricing issue states

## Policy Issue Deep Dive

When a new or materially changed Account Health policy issue appears, gather context without taking action:

1. Focus the investigation on one affected ASIN at a time. Copy the affected ASIN, related SKUs, policy issue date, policy type, status, and exact Amazon wording from Account Health.
2. Open Manage Support Cases / Case Log. In Seller Central, the known working route is `/cu/case-lobby` when older case-log URLs fail.
3. Search or scan for cases containing the affected ASIN in the subject or visible case text. Start with cases created on the policy issue date, one day before, and one day after, then extend through today when the issue is still open or when newer follow-up cases reference the same ASIN.
4. Prefer the original policy/suppression case and the most specific operational follow-up case over a broad list of duplicates. Do not list every matching case unless it adds a decision-relevant fact.
5. Open matching support cases read-only. Read the full thread history, including older pages of messages when the case is paginated. Capture:
   - case ID, subject, status, created date, latest Amazon reply date
   - Amazon's root-cause wording and customer-feedback wording, if provided
   - all affected ASINs/variations listed in the case
   - requested documents, images, deadlines, and reply/appeal instructions
   - seller/operator replies already sent and whether they actually answer Amazon's latest request
   - unresolved decision gaps, such as missing batch IDs, missing proof of upload, unclear affected SKUs, missing label images/PDFs, or conflicting Amazon instructions
6. Check Performance Notifications for the same date window if the case log is missing or incomplete.
7. Use exact Amazon wording from the case or policy row to search first-party Seller Help and local SOPs.
8. Summarize the deep dive as an operator decision brief, not a case dump:
   - what Amazon says the problem is
   - which case is the primary thread to continue
   - which secondary case adds a material fact
   - what information is still missing before the operator/operator can decide
   - recommended next action and where to take it, if safe and approved

Do not reply to the case, email Amazon, click `Submit appeal`, acknowledge warnings, upload documents, or edit listings during this check. The goal is to make the issue clear for the operator and prepare the next action, not to resolve it live.

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

## Account Source

For automation runs, fetch active profiles from `{account_profile_source}`.

Required profile fields:

- `Profile Name`
- `{seller_central_name_field}`; recommended: `Seller Central Name`
- `{marketplace_field}`; recommended: `Marketplace`
- `Status`

Rules:

- Use `{seller_central_name_field}` as the canonical Seller Central account selector.
- Use `{marketplace_field}` as the canonical country/region selector.
- Group and run profiles by region with Europe first, then US, then any remaining marketplaces.
- Show the country/region in all Slack parent and account-comment output.
- Do not use or display `Fulfillment Method` in the daily account-health workflow.
- Skip profiles missing `{seller_central_name_field}` or `{marketplace_field}` and list them under blockers.

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
