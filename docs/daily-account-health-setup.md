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
5. Should follow-up tasks be created? If yes, which task database/tracker, task type, default assignee, and priority rules should be used?
6. What schedule and timezone should the local automation use?
7. Should the first run be a dry run, or should it post live updates and create live tasks?

## Local Automation Template

Create the automation locally only after setup is complete. Replace every placeholder before activation.

```text
Run the lean Daily Amazon Account Health Check workflow for all active profiles in {account_profile_source} with usable {seller_central_name_field} and {marketplace_field}.

Workspace and skill context:
- Work in {workspace_path}.
- Load and follow the local amazon-account-health-check skill first.
- Use {account_profile_source} as the source of truth for account scope.
- Use only these fields for account selection/output: Profile Name, {seller_central_name_field}, {marketplace_field}, Status.
- Do not use or display Fulfillment Method.
- Skip profiles missing {seller_central_name_field} or {marketplace_field}, and list them under blockers.

Daily update destination:
- Post all daily account-health output only to {daily_update_channel}.
- Do not post to client-specific channels unless they were explicitly chosen during setup.
- Create one parent post per run:

Daily Amazon Account Health Check - {Mon D}

Accounts covered:
- {seller_central_name} {marketplace}

- Add one thread comment per checked account:

{seller_central_name} {marketplace}

Account Health
- Status: {Healthy / At risk / Issue found}
- AHR: {rating}
- Policy Compliance: {summary}

SellerSonar alerts
- {None / severity + summary}

Selling blockers
- {None / ASIN + issue}

Other action
- {No alerts or follow-up needed. / known issue update / new task created}

Daily check scope:
- Read the latest {sellersonar_alert_source} report and capture relevant marketplace alerts: search suppression, Buy Box / Featured Offer suppression or drop, new seller or possible hijacker, category/sub-category change, rating/review drop, and major price or offer change.
- Use Seller Central as the source of truth. Select the seller account by {seller_central_name_field} and country/region by {marketplace_field}.
- Verify account, marketplace, page title/tool, and date/filter context before recording.
- Check Account Health status, Account Health Rating, Policy Compliance, Performance Notifications, core performance metrics, and listing blockers.
- If a policy row exposes a safe read-only details/review view, open it before summarizing. Stop before any appeal, acknowledgement, submit, contact, or account-changing action.

Known issue handling:
- Check the current daily update thread and relevant open tasks in {follow_up_task_database} before flagging an issue as new.
- If an issue is already tracked, describe it as known/open, improved, or resolved instead of creating a duplicate.
- Create follow-up tasks only for new actionable issues or materially worsened known issues, and only if task creation is enabled for this setup.
- Use default task type {default_task_type}, default assignee {default_assignee}, Status Not Started, due next day, and the configured priority mapping.

Out of scope unless directly triggered by a visible alert or known open issue:
- Inventory, stranded inventory, FBA inbound shipments, shipment reconciliation, IPI/restock, Send to Amazon, returns, refunds, payments/reserve, coupons/promotions/deals, Seller Support case log, Amazon Ads, experiments, Creator Connections, Brand Customer Reviews, and Brand Registry alerts.

Safety:
- Never handle passwords, passkeys, OTP/MFA, CAPTCHA, cookies, local storage, session stores, payment/tax/bank details, or credentials.
- If Seller Central requires login/MFA/verification, stop and report the blocked account.
- Do not submit appeals, acknowledgements, support replies, listing edits, shipment actions, messages, uploads, bid/budget/campaign changes, or any account-changing action.

Finish with a concise summary: parent update link, checked accounts, skipped/blocker accounts, tasks created, and any login/manual action needed.
```

## Activation Checklist

- Run one manual dry run before enabling the recurring automation.
- Confirm no client/account names or private IDs are stored in GitHub.
- Confirm the configured destination receives a parent post and one account comment per checked account.
- Confirm clean accounts say exactly `No alerts or follow-up needed.`
- Confirm login/MFA pauses safely.
- Confirm no appeals, acknowledgements, support replies, listing edits, shipment actions, or account-changing actions are performed.
