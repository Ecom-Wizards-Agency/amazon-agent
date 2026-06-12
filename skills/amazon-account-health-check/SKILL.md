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

- Use the internal browser for Seller Central.
- If Seller Central shows login or verification, stop and ask Victor to complete it.
- Verify account, marketplace, page title/tool, and date/filter context before recording.
- Repeat verification after account/marketplace switches, tool switches, or session timeouts.
- Stop before appeals, acknowledgements, support contact, listing edits, shipment actions, messages, uploads, or account-changing actions.

## Check Sequence

For each account-marketplace:

1. Read the latest report from `{sellersonar_alert_source}`.
2. Record relevant alerts:
   - search suppression
   - Buy Box / Featured Offer suppression or drop
   - new seller or possible hijacker
   - category/sub-category change
   - rating/review drop
   - major price or offer change
3. Open Seller Central and verify the account by `{seller_central_name_field}` and the country/region by `{marketplace_field}`.
4. Check Account Health:
   - overall status and Account Health Rating
   - Policy Compliance categories and `View all`
   - `Review details` for any nonzero policy row when present
5. Check Performance Notifications since the last run.
6. Check order/shipping metrics:
   - ODR, A-to-z, chargebacks
   - cancellation, late shipment, valid tracking, on-time delivery
7. Check homepage action indicators and product/listing health:
   - Actions tab
   - Product Performance status
   - Featured Offer %
   - active/suppressed/inactive/pricing issue states

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
- Any blockers, login needs, or actions requiring Victor approval.
