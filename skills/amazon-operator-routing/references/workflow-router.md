# Workflow Router

Use this table to map user requests to local search and browser workflows.

| User intent | Search first | Good queries | Browser target | Stop before |
| --- | --- | --- | --- | --- |
| Communicate with creators | Advertising Help After Login, MAG SOPs | `creator connections`, `creator`, `message`, `campaign` | Amazon Ads Campaign Manager > top-right account selector > Brand content > Creator connections | Sending message, launching/changing campaign |
| Create FBA shipment | Amazon Seller Help, MAG SOPs | `shipment`, `send to amazon`, `FBA shipment`, `reconcile` | Seller Central > Inventory/FBA shipment flow | Confirming shipment, buying labels, submitting placement/shipping choices |
| Weekly FBA Inventory Overview / reshipment planning | `amazon-inventory-planning`, Amazon Seller Help | `FBA inventory`, `restock report`, `business report`, `inventory overview`, `reshipment` | Seller Central reports, local planner, pCloud, Slack staging | Client-facing Slack posts, final file-management batch if it touches Downloads, account-changing actions |
| Download reports | Seller Help, Ads Support, MAG SOPs | exact report name, `download report`, `report center`, `business report`, `search term report` | Seller Central reports or Ads Report Center | Download location if ambiguous; report generation if it changes account state |
| Seller Support case | Amazon Seller Help, MAG SOPs | `case`, `support`, `contact us`, issue text, error code | Seller Central > Help/Get Support/Case log | Submitting case or sending reply |
| Account health issue | Seller Help, MAG SOPs | `account health`, `policy violation`, `appeal`, `deactivation`, error text | Seller Central > Account Health/Performance | Submitting appeal, acknowledging policy action |
| Promotion or sales discount setup | Amazon Seller Help, MAG SOPs | `percentage off promotion`, `promo code`, `sale price`, `promotion`, `Pack of 3`, SKU/ASIN | Seller Central > Advertising > Promotions, or Manage Inventory sale price flow if the SOP/task calls for a sale price | Submitting the promotion, changing live prices, deleting/canceling existing promotions |
| Prepare bulk files | MAG SOPs, Ads Support, Amazon Ads Help | `bulk`, `bulk sheet`, `flat file`, `upload`, template name | Local spreadsheet first, then upload UI if requested | Uploading file, applying changes |
| Listing/catalog fix | Amazon Seller Help, MAG SOPs | error code, `variation`, `parentage`, `brand`, `attribute`, `A+ Content`, `image`, `feed processing` | Seller Central > Catalog/Manage Inventory or flat-file upload flow | Saving listing changes, deleting/relisting, uploading feeds |
| Check account health | Amazon Seller Help, MAG SOPs | `account health`, visible violation text, `policy`, `appeal`, `performance notification` | Seller Central > Account Health and Performance Notifications | Acknowledging actions, submitting appeals, contacting support |
| Ads bidding/budget change | Advertising Help After Login, MAG SOPs | `bidding`, `budget`, `bid adjustment`, `schedule rule`, campaign type | Amazon Ads > Campaign manager | Saving changes to bids/budgets/rules |
| Campaign troubleshooting | Advertising Help After Login, MAG SOPs | symptom text, `impressions`, `campaign status`, `ad status`, `budget`, `eligibility` | Amazon Ads > Campaign/ad details | Changing campaign settings |
| Ads reports | Advertising Help After Login, Amazon Ads Help, MAG SOPs | report name, `measurement`, `reports`, `download`, `sponsored products report`, `search term` | Amazon Ads > Measurement & reporting / Reports | Creating scheduled reports, changing reporting settings |
| Ads billing/payment support | Advertising Help After Login | `billing`, `invoice`, `payment failure`, `receipt`, exact warning text | Amazon Ads > Billing and payments | Changing payment method, submitting payment details |
| Ads API/SP API question | Amazon Ads Help, Seller Help | endpoint name, `API`, `reporting`, `bulk`, `Sponsored Products API` | Usually no Chrome action unless user asks | Creating credentials/API keys |

## Troubleshooting Pattern

When the user brings an error, screenshot, blocked campaign, rejected listing, missing report, or account health issue:

1. Copy exact error text or visible labels.
2. Search exact phrase first.
3. Search simplified keywords second.
4. Identify likely category: permission, eligibility, policy, data delay, file validation, campaign status, budget/bid, account setting, marketplace/account mismatch.
5. Gather evidence from UI: account, marketplace, entity ID, ASIN/SKU/campaign, dates, status, warning text.
6. For Account Health policy/compliance rows, click `Review details` when that button/link is present before summarizing the issue. Record the expanded detail text, status, impacted ASIN/SKU/listing, date, action taken, Account Health Rating impact, and next-step labels. Stop before `Submit new information`, appeals, acknowledgements, support contact, or any other account-changing action.
7. Prepare an action plan with:
   - likely root cause
   - supporting evidence
   - exact next click path
   - whether a case/appeal/file upload is needed
   - draft text if support communication is needed

## Support Case Draft Pattern

Before drafting a support case, gather:

- Account/marketplace
- ASIN/SKU/campaign/order/shipment/case ID
- Exact error/warning
- What was expected
- What already happened
- Business impact
- Clear request to Amazon

Do not submit without confirmation.

## Creator Connections Navigation Note

Use this route for Creator Connections:

1. Open `https://advertising.amazon.com/campaign-manager`.
2. Select the correct account in the top-right account selector.
3. Open `Brand content` in the left navigation.
4. Click `Creator connections`.

Do not use ~~`https://advertising.amazon.com/choose-account?destination=/bi`~~ as the starting route. That direct link can show only a partial account list and may omit accounts visible from Campaign Manager, including the account needed for Swissker/SwissKlip work.

## Operator Note Pattern

For Amazon troubleshooting, finish with:

- Source docs/SOPs used, with local paths.
- UI path taken and final page/screen.
- Screenshot/table evidence saved or transcribed.
- Root cause hypothesis, confidence level, and what would disprove it.
- Recommended next action, clearly marking anything that requires Victor confirmation.
