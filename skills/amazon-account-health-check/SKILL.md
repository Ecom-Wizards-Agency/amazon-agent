---
name: amazon-account-health-check
description: Use for daily Amazon account health checks across Seller Central accounts: reading #sellersonar, checking Seller Central Account Health, posting a #amazon parent thread with one account comment per account, and creating Notion troubleshooting follow-up tasks for actionable account-health issues.
---

# Amazon Account Health Check

Use this skill for recurring or ad hoc daily account health checks.

Trigger phrases include `daily account health check`, `account health sweep`, `run account health`, `check account health for accounts`, and requests to post a daily `#amazon` account-health thread.

## Source Order

1. Local client profile cache or Notion ops profile for account labels and marketplace.
2. Slack `#sellersonar` for the first alert pass.
3. Seller Central in the internal browser as the source of truth.
4. SellerSonar dashboard only when Slack is grouped, truncated, incomplete, or needs filtering.

## Browser Rules

- Use the internal browser for Seller Central.
- If Seller Central shows login or verification, stop and ask Victor to complete it.
- Verify account, marketplace, page title/tool, and date/filter context before recording.
- Repeat verification after account/marketplace switches, tool switches, or session timeouts.
- Stop before appeals, acknowledgements, support contact, listing edits, shipment actions, messages, uploads, or account-changing actions.

## Check Sequence

For each account-marketplace:

1. Read the latest `#sellersonar` daily report.
2. Record relevant alerts:
   - search suppression
   - Buy Box / Featured Offer suppression or drop
   - new seller or possible hijacker
   - category/sub-category change
   - rating/review drop
   - major price, offer, or fulfillment change
3. Open Seller Central and verify account/marketplace.
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

## Slack Output

Use one parent post per daily run in `#amazon`.

Parent format:

```text
Daily Amazon Account Health Check - {Mon D}

Accounts covered:
- {Account Marketplace}
```

Thread comment per account:

```text
{Account Marketplace}

Policy Compliance
- {status}
- AHR: {rating}
- {open issue count} open policy issues

SellerSonar alerts
- {severity}: {alert summary}

Featured Offer
- Featured Offer: {value/status}
- `{ASIN}` is {listing status}
- SKU: `{SKU}`
- {brand} price: {price}
- Inventory: {inventory}

Other action
- {action summary or "None"}
```

Keep comments short and human-readable. Do not include raw tables unless an issue needs the detail.

## Notion Follow-Up Defaults

Create follow-up tasks only for actionable issues, not for clean checks.

Route client-specific follow-ups to `Client Tasks - Overview`.

Default fields:

- `Task Type`: `Troubleshooting`
- `Assignee`: Alain
- `Assigned Employee`: Alain, when the relation can be resolved
- `Due`: next day
- `Status`: `Not Started`
- `Brand`: matching Partner Success brand

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
