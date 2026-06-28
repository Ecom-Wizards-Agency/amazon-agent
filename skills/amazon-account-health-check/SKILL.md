---
name: amazon-account-health-check
description: Use for daily Amazon account health checks across Seller Central accounts: reading an alert source such as SellerSonar, checking Seller Central Account Health, posting a configured daily update thread with one account comment per account, and optionally creating troubleshooting follow-up tasks for actionable account-health issues.
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
- `{default_assignee}`: optional default owner for follow-up tasks.
- `{schedule}` and `{timezone}`: optional local recurring automation schedule.

Ask which accounts and marketplaces should run before creating a local automation. Account names, marketplace lists, channel IDs, Notion IDs, assignees, schedules, and local paths are runtime configuration, not source-controlled skill content.

## Source Order

1. `{account_profile_source}` for active profiles, `{seller_central_name_field}`, and `{marketplace_field}`.
2. `{sellersonar_alert_source}` for the first alert pass.
3. Seller Central in the internal browser as the source of truth.
4. SellerSonar dashboard only when the alert source is grouped, truncated, incomplete, or needs filtering.

## Browser Rules

- Use the built-in Codex in-app browser for Seller Central. Do not use another browser for this workflow unless the operator explicitly says otherwise.
- Step 1 of every live run is opening the built-in browser and confirming Seller Central is logged in before any account checks begin.
- If Seller Central is not logged in or shows login or verification, stop and ask the operator to complete it in the built-in browser.
- Verify account, marketplace, page title/tool, and date/filter context before recording.
- Repeat verification after account/marketplace switches, tool switches, or session timeouts.
- Never click `Submit appeal` during an account-health check unless the operator is present and has explicitly approved that exact action.
- Stop before appeals, acknowledgements, support contact, support replies, listing edits, shipment actions, messages, uploads, or account-changing actions.

## Check Sequence

Process account-marketplaces by region in this order:

1. Europe accounts first.
2. US accounts second.
3. Any remaining non-Europe, non-US marketplaces last, unless the operator gives a different order.

Within each region, keep a stable marketplace/account order for the run so Slack output is easy to scan.

For each account-marketplace:

1. Open the built-in Codex browser and confirm Seller Central is logged in.
2. Read the latest report from `{sellersonar_alert_source}`.
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

Use one parent post per daily run in `{daily_update_channel}`. Do not post this workflow to client-specific channels unless setup explicitly chooses that destination.

Parent format:

```text
Daily Amazon Account Health Check - {Mon D}

Accounts covered:
- {{seller_central_name}} {{marketplace}}
```

Order the `Accounts covered` list by the same region-first run order: Europe, then US, then any remaining marketplaces.

Thread comment per account:

```text
{{seller_central_name}} {{marketplace}}

Account Health
- Status: {Healthy / At risk / Issue found}
- AHR: {rating}
- Policy Compliance: {summary}

SellerSonar alerts
- {None / severity + alert summary}

Selling blockers
- {None / ASIN + issue}

Other action
- {No alerts or follow-up needed. / known issue update / new task created}
```

Keep comments short and human-readable. Do not include raw tables unless an issue needs the detail.
If no alerts, blockers, or follow-up actions are found, write exactly: `No alerts or follow-up needed.`

## Notion Follow-Up Defaults

Create follow-up tasks only for actionable issues, not for clean checks.

Create follow-up tasks only when `{follow_up_task_database}` is configured. Do not create tasks during setup or dry runs unless the operator explicitly approves live task creation.

Default fields:

- `Task Type`: `{default_task_type}`
- `Assignee`: `{default_assignee}`
- `Assigned Employee`: `{default_assignee}`, when that relation exists
- `Due`: next day
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
- Acceptance criteria
- Stop-before-risk note

## Finish Note

Report:

- Slack parent link and account comment link.
- Notion task titles and URLs created.
- Accounts checked or skipped.
- Any blockers, login needs, or actions requiring the operator approval.
