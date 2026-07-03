# SOP Draft: Daily Amazon Account Health Check

Date: 2026-06-07
Status: ready for review
Owner: Amazon operations
Related workflow: Daily account health monitoring, SellerSonar alert triage, Seller Central account checks

## Purpose

Create a fast daily routine for checking each Amazon account, using `#sellersonar` as the first alert pass and Seller Central in the internal browser as the source of truth. A clean account should take about 3-6 minutes. Accounts with alerts or warnings take longer only for evidence capture and issue triage.

## Preconditions

- The operator has a locally saved preferred browser for live runs: either the built-in Codex in-app browser or a Chromium browser connected through the Chrome extension (Chrome, Brave; the extension typically requires the US VPN). The preferred browser is used for every browser step; the other approved browser is the fallback.
- Step 1 of every live run is opening the preferred browser and confirming Seller Central is logged in before any account checks begin. If the preferred browser is logged out, try the fallback browser before declaring the run blocked.
- Parallel tabs are allowed only across regions (for example one US Seller Central tab plus one Europe tab); never two tabs within the same regional Seller Central domain, because they share one session and account selector.
- One regional login covers every marketplace in that region: stay on the active session's Seller Central domain (whichever regional domain the operator logged in on, such as DE, UK, or IT) and switch country/account only through the in-app marketplace/account switcher. Never switch country by changing the Seller Central URL/domain - a domain change forces a new login. Open deep links such as `/cu/case-lobby` on the active session's domain.
- If a Seller Central page shows a login screen in both approved browsers, the run is blocked: the assistant stops and asks the operator to log in. The assistant must not handle passwords, one-time codes, authenticator prompts, cookies, local storage, session stores, or other credentials.
- The local findings ledger (`findings.json` next to the automation) is readable; it carries open findings, their dispositions, and links to their follow-up tasks between runs. It is private automation memory, never committed to GitHub; the task system remains the human source of truth.
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

Run accounts by region in this order:

1. Europe accounts first.
2. US accounts second.
3. Any remaining non-Europe, non-US marketplaces last unless the operator gives a different priority.

### 0. Re-Check Open Findings First

1. Load the findings ledger and the open follow-up tasks it links for in-scope accounts.
2. The run starts by answering: "What was still open yesterday, and what is its status today?" - not by looking for new issues.
3. During each account's check, verify every open finding's current state in Seller Central, then re-dispose it in step 9: still open and owned (Assigned, with age and an OVERDUE flag when past due), pending an external party (Waiting, with who and since when), or verified resolved (record the resolved date, comment on the task, and report it for the owner to close - never close it yourself).
4. If an account cannot be checked today, carry its ledger entries forward unchanged; never infer resolved from a missed check.

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
8. Freshness guard: if the latest daily report is older than the previous business day, never record `0 alerts` - record `alert source stale ({report date})` and treat SellerSonar-dependent checks as not performed.

### 2. Verify Seller Central Context

1. Open the built-in Codex browser and confirm Seller Central is logged in.
2. Open Seller Central in the built-in browser.
3. Confirm the visible account, marketplace/country, page title/tool, and relevant date or filter context before recording anything.
4. If switching accounts, marketplaces, tools, or returning after a timeout, repeat the confirmation.
5. If the account or marketplace does not match the requested check, stop and correct the selector before continuing.

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
8. For new or materially changed policy issues, run an ASIN-focused support-case deep dive before deciding whether a follow-up task or operator action is needed:
   - investigate one affected ASIN at a time
   - search Manage Support Cases / Case Log for the ASIN, starting with the policy issue date, one day before, and one day after, then extending through today for unresolved issues
   - read the full matching case history, including paginated older messages
   - identify the original policy/suppression case and the most specific operational follow-up case
   - summarize only decision-relevant facts, not every duplicate case
   - call out missing information such as batch IDs, upload proof, affected SKUs, label/PDF evidence, unanswered Amazon requests, or conflicting Amazon instructions
9. Stop before appeals, acknowledgements, submitting new information, calling Account Health Support, opening support contact flows, replying to cases, uploading files, or changing listings.

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
SellerSonar: {0 alerts / alert count + types / alert source stale ({date})}
Account Health: {status}, AHR {score if visible}
Policy/Compliance issues: {none / summary with ASIN/SKU/status/deadline}
Performance notifications: {none / summary}
Order/shipping metrics: {healthy / issue summary}
Listing health: {healthy / issue summary}
Evidence captured: {none / evidence path}
Findings: {per finding: Disposition | Owner | Task link | Deadline}
Stop points remaining: {appeal/support/send/change action needing approval}
```

### 9. Dispose Every Finding

Before the run ends, every finding - new or carried over from the ledger - must get exactly one disposition. Dispositions are the workflow's internal routing layer that decides what happens in the task system; they never replace task statuses.

1. **No action needed** - clean, informational, or verified resolved. No task.
2. **Action needed** - new actionable issue with no owner yet. Create a follow-up task in the same run (default assignee: the daily runner), then report the finding as Assigned.
3. **Assigned** - an open task already exists. Report owner, age in days, and OVERDUE when past due; comment on the task when the state changed; raise priority or pull the due date earlier when it worsened.
4. **Waiting** - action taken, pending an external party (Amazon case reply, client documents, reinstatement review). Update the task with who it waits on and since when; set the closest waiting/blocked status the task system offers; the daily runner keeps ownership and chases it.
5. **Escalate** - meets an escalation trigger: deactivation/suspension or explicit warning, a stop-before-risk decision, identity/bank/tax/verification requests, legal/IP/counterfeit claims, an unhandled hard deadline within 48 hours, or a login blocker after both approved browsers were tried. Task assigned to the escalation owner at the highest priority, mentioned only on escalation lines.

Update the findings ledger once at the end of the run with every finding's key, disposition, owner, task link, dates, and deadline.

## Severity Rules

- Critical: account deactivation risk, suspended account/listing, Account Health warning, unresolved policy violation, required response deadline, A-to-z or chargeback spike.
- High: search suppression, Buy Box suppression on key ASINs, new unauthorized seller, major Valid Tracking Rate, late shipment, or cancellation issue.
- Medium: rating drop, category change, pricing-health issue, inactive listing, stranded inventory, or repeated warning without immediate deadline.
- Low: positive rating movement, informational SellerSonar changes, resolved alerts, or minor dashboard recommendations.

Severity maps to default routing: Critical findings are escalation candidates; High and Medium route to the daily runner; Low is No action needed unless recurring.

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
- Dates belong in filenames, for example `2026-06-07_acme-us-account-health-note.md`.
- Do not save evidence inside `MAG SOPs/`, Amazon help-library folders, or other source-document folders.

## Source Docs/SOPs Used

- `skills/amazon-operator-routing/SKILL.md`
- `skills/amazon-troubleshooting/SKILL.md`
- `MAG SOPs/catalog/catalog-sop-amazon-policy-violations-check.md`
- `MAG SOPs/general/supplemental-article-amazon-seller-central-home-page-basic-navigation.md`
- Recent `#sellersonar` daily report structure observed in Slack

## Open Questions Or Assumptions

- Seller Central in the internal browser is the source of truth for account health.
- The operator's locally saved preferred browser (built-in Codex browser, or Chrome/Brave via the Chrome extension with US VPN) is used for all runs; the other approved browser is the fallback.
- `#sellersonar` is the fastest first pass for alert discovery.
- SellerSonar dashboard is a drill-down tool and is not mandatory for every clean account.
- `#sellersonar-now` is intentionally out of scope.
- Daily output defaults to the current chat/operator note unless the operator names a Slack, Notion, or other destination.
- Client-specific owner, recurring schedule, and live follow-up status should live in Notion or the active task system, not in this SOP draft.

## Promotion Notes

After review, promote this routine into the durable MAG/internal SOP library or link it from the Amazon Agent account-check workflow. If promoted, keep the process generic and put client-specific account lists, owners, schedules, and escalations in Notion ops profiles.
