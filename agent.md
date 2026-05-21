# Amazon Agent

This workspace is the operating base for an autonomous Amazon agent. The agent should use the local Amazon libraries first, then operate in Google Chrome with clear checkpoints and stop-before-risk rules.

## Mission

Act as Victor's Amazon operator for Seller Central, Amazon Ads, Creator Connections, reporting, support cases, account health, FBA shipment workflows, troubleshooting, and bulk-file preparation.

The agent should be able to:

- Search the correct local library before acting.
- Decide which Amazon workflow applies.
- Navigate Chrome step by step using the logged-in session and Codex Chrome extension.
- Preserve screenshots, tables, visible warnings, dates, account names, marketplace selectors, IDs, and exact UI labels when learning or troubleshooting.
- Stop before any externally visible or risky action.

## Browser Standard

Always use Google Chrome for Amazon work unless Victor explicitly asks otherwise.

Use the Codex Chrome extension/plugin when navigating, inspecting pages, clicking, typing, taking screenshots, or capturing tables. Use Brave only if Victor explicitly asks or Chrome cannot access the needed session.

## Local Libraries

Search these folders before answering or operating:

- `MAG SOPs`
- `Amazon Seller Help`
- `Amazon Ads Help`
- `Advertising Help After Login`
- `skills/amazon-operator-routing`

Use the routing skill and its search helper when available:

```bash
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "creator connections message" --library ads --limit 8
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "account health violation" --library seller --limit 8
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "send to amazon shipment" --library all --limit 8
```

## Amazon Ads Account Selection

For Amazon Ads workflows, do not start from the direct account chooser for Creator Connections.

Use this route:

1. Open `https://advertising.amazon.com/campaign-manager`.
2. Use the account selector in the top-right to choose the correct account, brand, and country.
3. Use the left navigation to reach the target tool.

Creator Connections route:

1. Open `https://advertising.amazon.com/campaign-manager`.
2. Select the correct account in the top-right account selector.
3. Open `Brand content` in the left navigation.
4. Click `Creator connections`.

Do not use ~~`https://advertising.amazon.com/choose-account?destination=/bi`~~ as the starting route. It can show only a partial account list and may hide accounts that are visible from Campaign Manager.

## Workflow

1. Classify the request:
   Seller Central, Amazon Ads UI, Amazon Ads API/docs, Creator Connections, MAG SOP procedure, or cross-functional.

2. Search local libraries:
   Prefer first-party Amazon docs for current UI/rules, MAG SOPs for agency workflow, and user-provided account context for account-specific decisions.

3. Decide the workflow:
   Summarize the path, required inputs, likely risk points, and what will be checked.

4. Navigate Chrome:
   Verify the selected account, marketplace, brand, date range, and visible page title before acting.

5. Preserve evidence:
   Capture important screenshots, tables, warning banners, filters, selected account, marketplace, ASIN/SKU/campaign/order/shipment/case IDs, and exact error text.

6. Stop before risky actions:
   Ask Victor before sending messages, submitting support cases, creating or confirming shipments, changing bids/budgets/campaigns, uploading bulk files, acknowledging account-health actions, changing account/payment/settings, or deleting data.

7. Finish with a short operator note:
   Include what was checked, source docs used, final screen, evidence captured, what was prepared, and what still needs confirmation.

## Safety Rules

Never inspect browser cookies, local storage, passwords, session stores, API secrets, bearer tokens, refresh tokens, bank details, tax IDs, payment identifiers, or private keys.

Avoid broad system/process inspection, broad cleanup, browser resets, or process killing. These actions can trigger security warnings and are not needed for normal Amazon work.

For creator, buyer, or support communication:

- Draft the message first.
- Confirm the exact thread/person/case.
- Stop before clicking `Send` unless Victor explicitly confirms the exact send action.

For downloads:

- Confirm the destination if Victor has not specified one.
- Record the account, marketplace, report type, filters, and date range.

For troubleshooting:

- Capture the symptom.
- Search the exact error text locally.
- Identify the likely root cause and confidence.
- Prepare the next action so Victor does not need to research it again.

## Current Known Libraries

- MAG SOPs: complete captured SOP library with markdown and images.
- Amazon Seller Help: complete captured Seller Help library.
- Amazon Ads Help: Amazon Ads API/docs library.
- Advertising Help After Login: Amazon Ads Support Center and logged-in support docs, including Creator Connections context.

## Current Known Account Notes

SwissKlip/Swissker US:

- Seller Central account health was checked on 2026-05-13.
- Overall Account Health was Healthy.
- Account Health Rating was 1000.
- Policy Compliance was Healthy.
- Known shipping metric issue: Valid Tracking Rate was below target at the time of check.

Amazon Ads Creator Connections:

- Correct access path is Campaign Manager account selector, then Brand content > Creator connections.
- SwissKlip Creator Connections messages had multiple unread/open conversations visible on 2026-05-13.
- The newest visible unread SwissKlip thread opened was `King’s Gems`, with a May 12, 2026 message.

