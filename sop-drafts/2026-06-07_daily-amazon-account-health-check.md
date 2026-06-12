# SOP Draft: Daily Amazon Account Health Check

Date: 2026-06-07
Status: ready for review
Owner: Amazon operations
Related workflow: Daily account health monitoring, SellerSonar alert triage, Seller Central account checks

## Purpose

Create a fast daily routine for checking each Amazon account, using `#sellersonar` as the first alert pass and Seller Central in the internal browser as the source of truth. A clean account should take about 3-6 minutes. Accounts with alerts or warnings take longer only for evidence capture and issue triage.

## Preconditions

- The operator has access to the internal Codex browser and the relevant Seller Central sessions.
- If a Seller Central page shows a login screen, the operator stops and asks the operator to log in. The operator must not handle passwords, one-time codes, authenticator prompts, cookies, local storage, session stores, or other credentials.
- The account list for the day is known from the current task, Notion ops profiles, or `_local/client-profiles/profiles.json`.
- The operator can read the Slack channel `#sellersonar`.
- The operator knows where to record the daily result. Default is a concise operator note in the current chat unless the operator names a Slack, Notion, or other destination.
- Local evidence and output folders exist or can be created under:
  - `evidence/{client-or-brand}/account-check/`
  - `output/{client-or-brand}/account-check/`

## Required Inputs

- Account or brand name.
- Marketplace or country.
- Seller Central account label, when available.
- Fulfillment exposure: FBA-only, MFN, Seller-Fulfilled Prime, or mixed.
- Any known high-risk ASINs, SKUs, open cases, recent policy issues, or active launch/promo periods.
- Last check date or prior operator note, when available.

## Workflow

### 1. Start With SellerSonar In Slack

1. Read the latest daily report in `#sellersonar`.
2. Ignore `#sellersonar-now`; it is out of scope for this routine.
3. Identify alerts for the account, brand, ASINs, or marketplace being checked.
4. Prioritize these alert types:
   - `Search suppressed`
   - `Buy Box suppressed`
   - new seller or suspected hijacker
   - category or sub-category change
   - rating/review drop
   - major price, offer, or fulfillment change
5. Open SellerSonar dashboard only when Slack is incomplete, grouped, truncated, or needs filtering by account/brand.
6. Download or use the linked `Notifications.csv` only when the Slack report contains meaningful alerts, grouped `+N notifications`, or missing detail needed for triage.
7. Record the alert count and alert types in the operator note. Do not treat SellerSonar as final proof of account health.

### 2. Verify Seller Central Context

1. Open Seller Central in the internal browser.
2. Confirm the visible account, marketplace/country, page title/tool, and relevant date or filter context before recording anything.
3. If switching accounts, marketplaces, tools, or returning after a timeout, repeat the confirmation.
4. If the account or marketplace does not match the requested check, stop and correct the selector before continuing.

### 3. Check Account Health

1. Open `Performance > Account Health` or the direct Account Health dashboard.
2. Record the overall Account Health status and Account Health Rating, if visible.
3. Inspect all visible Policy Compliance categories.
4. Use `View All` where available to expose every complaint or violation category.
5. Look for any visible labels such as:
   - `Action Required`
   - `Under Review`
   - `Suspended`
   - account deactivation warning
   - listing deactivation warning
   - policy violation
   - product compliance request
6. For every nonzero Account Health issue row, open `Review details` when present before summarizing.
7. Capture or transcribe:
   - status
   - impacted ASIN, SKU, listing, order, or case ID
   - issue type and exact Amazon wording
   - visible date or deadline
   - Account Health Rating impact
   - next-step labels or buttons
8. Stop before appeals, acknowledgements, submitting new information, calling Account Health Support, opening support contact flows, or changing listings.

### 4. Check Performance Notifications

1. Open Performance Notifications for the account.
2. Review notifications since the last check.
3. Flag messages related to:
   - account health
   - policy compliance
   - product compliance
   - listing removals or suppressions
   - verification or document requests
   - claims, chargebacks, or order performance
   - shipping performance
4. Record notification titles, dates, and deadlines. Open details only as needed to understand the issue.
5. Stop before replying, acknowledging, appealing, uploading documents, or contacting support.

### 5. Check Order And Shipping Performance

1. Review the Account Health performance metrics visible for the account:
   - Order Defect Rate
   - A-to-z Guarantee claims
   - chargebacks
   - cancellation rate
   - late shipment rate
   - Valid Tracking Rate
2. For MFN, Seller-Fulfilled Prime, or mixed accounts, pay extra attention to:
   - pending orders
   - unshipped orders
   - late shipment warnings
   - tracking defects
   - buyer message response SLA
3. For FBA-only accounts, still check for A-to-z claims, chargebacks, product complaints, and product compliance issues.
4. Record any metric below target, trending warning, or visible performance issue.

### 6. Check Homepage Action Indicators

1. Return to the Seller Central homepage or dashboard.
2. Review the action indicator bar and account widgets for:
   - pending orders to ship
   - shipment issues
   - listing issues
   - account health warnings
   - deactivation risk
   - recommended actions that affect account health
3. Use the Account Health widget as a quick cross-marketplace signal, but verify material issues on the actual Account Health dashboard.

### 7. Check Listing Health Signals

1. Check listing health areas that are relevant to the account or SellerSonar alerts:
   - suppressed listings
   - inactive listings
   - search-suppressed listings
   - pricing-health issues
   - Buy Box suppression or featured-offer issues
2. If SellerSonar reported an ASIN-level issue, verify the same ASIN in Seller Central or the relevant listing/pricing page.
3. Record impacted ASINs/SKUs and whether Seller Central confirms, contradicts, or does not show the SellerSonar alert.

### 8. Finish With The Operator Note

Use this concise format:

```text
Daily account health check - {Account / Marketplace}
Date checked: {YYYY-MM-DD}
Seller Central context: {account label}, {marketplace}, {page/tool verified}
SellerSonar: {0 alerts / alert count + types}
Account Health: {status}, AHR {score if visible}
Policy/Compliance issues: {none / summary with ASIN/SKU/status/deadline}
Performance notifications: {none / summary}
Order/shipping metrics: {healthy / issue summary}
Listing health: {healthy / issue summary}
Evidence captured: {none / evidence path}
Recommended next action: {none / owner + urgency + next step}
Stop points remaining: {appeal/support/send/change action needing approval}
```

## Severity Rules

- Critical: account deactivation risk, suspended account/listing, Account Health warning, unresolved policy violation, required response deadline, A-to-z or chargeback spike.
- High: search suppression, Buy Box suppression on key ASINs, new unauthorized seller, major Valid Tracking Rate, late shipment, or cancellation issue.
- Medium: rating drop, category change, pricing-health issue, inactive listing, stranded inventory, or repeated warning without immediate deadline.
- Low: positive rating movement, informational SellerSonar changes, resolved alerts, or minor dashboard recommendations.

## Stop-Before-Risk Points

- Stop before submitting appeals, acknowledgements, documents, support cases, support replies, chat messages, listing edits, shipment changes, bulk uploads, pricing changes, account setting changes, or any externally visible action.
- Stop if the browser shows a login screen, session timeout, account selector mismatch, marketplace mismatch, or page that asks for credentials or verification.
- Stop before downloading sensitive reports into an unclear folder.
- Stop before posting client-facing updates to Slack or Notion unless the operator explicitly requested that destination in the current chat or a matching local standing permission exists.

## Evidence And Screenshots Needed

- Capture screenshots or precise transcriptions for:
  - Account Health status/AHR when unhealthy or changed
  - policy issue rows and expanded `Review details`
  - warning banners, deadlines, or deactivation-risk messages
  - Performance Notifications requiring action
  - SellerSonar alerts that are confirmed in Seller Central
  - listing/search/Buy Box suppression evidence
- Store screenshots under `evidence/{client-or-brand}/account-check/`.
- Store downloaded SellerSonar CSVs or working notes under `output/{client-or-brand}/account-check/`.
- Dates belong in filenames, for example `2026-06-07_swissker-us-account-health-note.md`.
- Do not save evidence inside `MAG SOPs/`, Amazon help-library folders, or other source-document folders.

## Source Docs/SOPs Used

- `skills/amazon-operator-routing/SKILL.md`
- `skills/amazon-troubleshooting/SKILL.md`
- `MAG SOPs/catalog/catalog-sop-amazon-policy-violations-check.md`
- `MAG SOPs/general/supplemental-article-amazon-seller-central-home-page-basic-navigation.md`
- Recent `#sellersonar` daily report structure observed in Slack

## Open Questions Or Assumptions

- Seller Central in the internal browser is the source of truth for account health.
- `#sellersonar` is the fastest first pass for alert discovery.
- SellerSonar dashboard is a drill-down tool and is not mandatory for every clean account.
- `#sellersonar-now` is intentionally out of scope.
- Daily output defaults to the current chat/operator note unless the operator names a Slack, Notion, or other destination.
- Client-specific owner, recurring schedule, and live follow-up status should live in Notion or the active task system, not in this SOP draft.

## Promotion Notes

After review, promote this routine into the durable MAG/internal SOP library or link it from the Amazon Agent account-check workflow. If promoted, keep the process generic and put client-specific account lists, owners, schedules, and escalations in Notion ops profiles.
