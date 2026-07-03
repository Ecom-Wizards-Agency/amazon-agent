# Daily Amazon Account Health Setup

This guide explains how to configure the reusable daily Amazon account-health workflow without storing private account data in GitHub.

## What Belongs In GitHub

- The generic account-health skill and workflow instructions.
- Setup questions and placeholder-based templates.
- Stop-before-risk rules and output formats.

## What Must Stay Local

Do not commit:

- Seller account names, client names, account lists, marketplaces tied to clients, or test-run results.
- Slack channel IDs, Notion database IDs, user IDs, assignee names, local workspace paths, or local automation files.
- Credentials, MFA data, cookies, browser session data, payment details, tax details, or downloaded reports.
- Generated profile caches such as `_local/client-profiles/profiles.json`.

## First-Run Questions

Before creating a recurring automation, ask the operator:

1. Which Seller Central accounts and marketplaces should be checked?
2. Where is the account profile source, and which fields contain `Seller Central Name`, `Marketplace`, and `Status`?
3. Where should daily updates be posted?
4. Which alert source should be checked first, such as a SellerSonar Slack channel, dashboard, or CSV?
5. Should follow-up tasks be created? If yes, which task database/tracker, task type, and priority rules should be used?
6. Who is the daily runner (works the action queue, default task owner), who is the escalation owner (true escalations only), and is there a strategic supervisor for a weekly digest? Record chat member IDs and task-system person IDs locally.
7. Which browser does the operator prefer for live runs: the built-in in-app browser, or a Chromium browser connected through the browser extension (Chrome, Brave)? The preference is saved locally and used for all runs; the other approved browser is the fallback.
8. Where should the private findings ledger live? Default: `findings.json` next to the local automation, never in the repo or GitHub.
9. What schedule and timezone should the local automation use?
10. Should the first run be a dry run, or should it post live updates and create live tasks?

## Local Automation Template

Create the automation locally only after setup is complete. Replace every placeholder before activation.

```text
Run the Daily Amazon Account Health Check as an action-queue workflow for all active profiles in {account_profile_source} with usable {seller_central_name_field} and {marketplace_field}.

Workspace and skill context:
- Work in {workspace_path}.
- Load and follow the local amazon-account-health-check skill first.
- Use {account_profile_source} as the source of truth for account scope.
- Use only these fields for account selection/output: Profile Name, {seller_central_name_field}, {marketplace_field}, Status.
- Do not use or display Fulfillment Method.
- Skip profiles missing {seller_central_name_field} or {marketplace_field}, and list them under blockers.

Roles:
- {daily_runner} is the daily runner and default owner of every follow-up task.
- {escalation_owner} receives true escalations only; mention them only on escalation lines.
- {supervisor} supervises via the weekly digest only; never assign them tasks or mention them outside the digest.

Findings ledger (private memory):
- Path: {findings_ledger_path}. Private automation memory only: finding identity/history plus task links. {follow_up_task_database} remains the human task source of truth. Never commit the ledger to the repo.
- Finding key: account|marketplace|scope|issue_type, where scope is ASIN:<asin>, ACCOUNT, or CASE:<id>.
- Carry entries forward unchanged when an account is skipped/blocked; set resolved dates only after Seller Central verification; keep resolved entries 30 days for dedup; write the full ledger once, at the end of the run, including degraded runs.

Step 0 - Re-check open findings first:
- Load the ledger and the open tasks it links; for every open finding, verify current state in Seller Central during that account's check, then re-dispose it: assigned (owner, days open, OVERDUE when past due), waiting (waiting on whom, since when, deadline), or verified resolved (record it, comment on the task, report it for the owner to close - never close tasks yourself).

Browser rules:
- Use the operator's locally saved preferred browser for all runs: the built-in in-app browser, or a Chromium browser connected through the browser extension. Use the other approved browser as fallback before declaring the run blocked.
- Parallel tabs only across regions (separate Seller Central sessions); never two tabs within the same regional Seller Central domain.
- One regional login covers every marketplace in that region: stay on the active session's Seller Central domain and switch country/account only via the in-app marketplace switcher; never by changing the URL/domain (that forces a re-login). Open deep links such as /cu/case-lobby on the active session's domain.

Daily update destination:
- Post all daily account-health output only to {daily_update_channel}.
- Do not post to client-specific channels unless they were explicitly chosen during setup.
- Create one parent post per run (the action queue, ordered: escalations, actions, assigned-overdue, assigned, waiting):

Daily Amazon Account Health Check - {Mon D}

Action queue {@daily_runner}
1. ESCALATE {@escalation_owner} - {account} {marketplace} - {issue + deadline} - {task link}
2. ACTION - {account} {marketplace} - {scope} {issue} - {next step} by {date} - {task link}
3. ASSIGNED - {account} {marketplace} - {issue} - {owner}, open {N}d{, OVERDUE} - {task link}
4. WAITING - {account} {marketplace} - {issue} - waiting on {target}, day {N} - {task link}

Clean: {N} of {M} accounts - no action needed
Skipped/blocked: {none / account + reason}

- If the queue is empty, write exactly: Action queue: empty. A missing parent post means the run failed.
- Add one thread comment per checked account:

{seller_central_name} {marketplace}

Account Health
- Status: {Healthy / At risk / Issue found}
- AHR: {rating}
- Policy Compliance: {summary}

SellerSonar alerts
- {None / severity + summary / alert source stale ({date})}

Findings
- [{NO ACTION / ACTION / ASSIGNED / WAITING / ESCALATE}] {scope} - {issue} - owner {name} - {task link / deadline / waiting on}

- If an account is fully clean, the Findings section is exactly: No action needed.
- On the last run of the week, add a Weekly digest {@supervisor} comment: findings per account, new vs resolved, escalations raised, overdue count, recurring patterns.

Daily check scope:
- Read the latest {sellersonar_alert_source} report and capture relevant marketplace alerts: search suppression, Buy Box / Featured Offer suppression or drop, new seller or possible hijacker, category/sub-category change, rating/review drop, and major price or offer change.
- Use Seller Central as the source of truth. Select the seller account by {seller_central_name_field} and country/region by {marketplace_field}.
- Verify account, marketplace, page title/tool, and date/filter context before recording.
- Check Account Health status, Account Health Rating, Policy Compliance, Performance Notifications, core performance metrics, and listing blockers.
- If a policy row exposes a safe read-only details/review view, open it before summarizing. Stop before any appeal, acknowledgement, submit, contact, or account-changing action.
- For new or materially changed policy issues, investigate one affected ASIN at a time. Copy the affected ASIN/SKU, policy issue date, status, and exact Amazon wording, then check Manage Support Cases / Case Log for matching ASIN cases. Start with cases created on the same day, one day before, and one day after; extend through today when newer cases reference the same unresolved issue. Use `/cu/case-lobby` when older case-log URLs fail. Open matching cases read-only, read the full thread history including paginated older messages, and capture only decision-relevant facts: Amazon's root-cause wording, customer feedback, affected variations/SKUs, requested documents, deadlines, case ID, seller replies already sent, and unresolved gaps such as missing batch IDs, missing upload proof, unclear affected SKUs, missing label images/PDFs, or conflicting Amazon instructions. Summarize as an operator decision brief with the primary case to continue, secondary cases that add material facts, missing information, and the recommended safe next action.

Dispositions (routing layer):
- Every finding - new or carried over - gets exactly one disposition before the run ends: no action needed, action needed, assigned, waiting, or escalate. Dispositions decide what happens in {follow_up_task_database}; they never replace its statuses.
- Action needed: create a task (task type {default_task_type}, assignee {daily_runner}, Status Not Started, Due = earlier of next business day or deadline minus 2 days, configured priority mapping), then report as assigned.
- Assigned: comment on the existing task when the state changed; raise priority or pull the due date earlier when it worsened.
- Waiting: update the task with who it waits on and since when; set the closest waiting/blocked status the database offers.
- Escalate (deactivation/suspension/warning, stop-before-risk decisions, identity/bank/tax/verification, legal/IP claims, unhandled deadline under 48h, login blocked in both browsers): task assigned to {escalation_owner} at the highest priority.
- Update-don't-duplicate, matched by ledger key. Never set a completed status; never close an escalation task.
- SellerSonar freshness guard: if the latest alert report is older than the previous business day, report "alert source stale" instead of "No alerts".
- Degraded run (login blocked in both browsers): still post the queue from ledger + alert source, mark lines "not verified today", escalate the login blocker, still write the ledger.

Out of scope unless directly triggered by a visible alert or known open issue:
- Inventory, stranded inventory, FBA inbound shipments, shipment reconciliation, IPI/restock, Send to Amazon, returns, refunds, payments/reserve, coupons/promotions/deals, Seller Support case log, Amazon Ads, experiments, Creator Connections, Brand Customer Reviews, and Brand Registry alerts.

Safety:
- Never handle passwords, passkeys, OTP/MFA, CAPTCHA, cookies, local storage, session stores, payment/tax/bank details, or credentials.
- If Seller Central requires login/MFA/verification, stop and report the blocked account.
- Never click Submit appeal during an account-health check unless the operator is present and has explicitly approved that exact action.
- Do not submit appeals, acknowledgements, support replies, listing edits, shipment actions, messages, uploads, bid/budget/campaign changes, or any account-changing action.

Finish with a concise summary: parent update link, queue counts by disposition, overdue count, escalations raised, checked accounts, skipped/blocker accounts, tasks created/updated, ledger written yes/no, browser used, and any login/manual action needed.
```

## Activation Checklist

- Run 2-3 supervised manual runs before enabling the recurring automation.
- Confirm no client/account names, person IDs, or the findings ledger are stored in GitHub.
- Confirm the configured destination receives an action-queue parent post and one account comment per checked account, with the escalation owner mentioned only on escalation lines.
- Confirm clean accounts say exactly `No action needed.` and an empty queue says exactly `Action queue: empty`.
- Confirm every finding carries a disposition, tasks are created/updated without duplicates (matched by ledger key), and the ledger is written once at the end of the run.
- Confirm login/MFA pauses safely and the degraded-run path posts the queue with an escalated login blocker.
- Confirm no appeals, acknowledgements, support replies, listing edits, shipment actions, or account-changing actions are performed.
