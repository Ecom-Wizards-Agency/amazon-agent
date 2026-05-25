# Amazon Agent

This workspace is the operating base for an autonomous Amazon agent. The agent should use the local Amazon libraries first, then operate in the connected browser with clear checkpoints and stop-before-risk rules.

## Mission

Act as Victor's Amazon operator for Seller Central, Amazon Ads, Creator Connections, reporting, support cases, account health, FBA shipment workflows, troubleshooting, and bulk-file preparation.

The agent should be able to:

- Search the correct local library before acting.
- Decide which Amazon workflow applies.
- Navigate the connected browser step by step using the logged-in Amazon session.
- Preserve screenshots, tables, visible warnings, dates, account names, marketplace selectors, IDs, and exact UI labels when learning or troubleshooting.
- Stop before any externally visible or risky action.

## Browser Standard

Use the teammate's connected Codex browser for Amazon work. Common choices are Chrome or Brave.

If `local-browser-preference.md` exists in the project root, read it before browser work and use that preferred connected browser when available. This file is local-only and ignored by Git. If no local preference exists, use the connected browser/session available in the current chat.

Before acting in Amazon, verify the connected browser/session is logged in and confirm the selected account/advertiser, marketplace/country, visible page title/tool, and date range or filters when relevant. If the preferred browser is unavailable or not logged in, pause and ask which connected browser/session to use.

## Local Libraries

Search narrowly before answering or operating. Use indexes and the routing search helper first; do not crawl whole SOP/help folders by default.

- `Amazon Seller Help`
- `Amazon Ads Help`
- `Advertising Help After Login`
- `MAG SOPs`
- `skills/amazon-operator-routing`

Use the routing skill and its search helper when available:

```bash
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "creator connections message" --library ads --limit 8
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "account health violation" --library seller --limit 8
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "send to amazon shipment" --library all --limit 8
```

## MAG SOP Visual Archive

The runtime `MAG SOPs/` folder is the markdown-only version. Search local/GitHub markdown SOPs first. When visual confirmation, screenshots, GIFs, or layout references are needed, use the local pCloud visual archive.

Victor's current local placeholder path is:

`/Users/victoruhl/Documents/pCloud/Amazon Agent/MAG SOPs`

This path is user-specific. Team members should point their own local checkout to their own pCloud-synced copy of the visual archive. Do not commit the visual archive itself or any user-specific sync folder into GitHub.

Expected pCloud visual archive check:

- 535 Markdown files
- 3,621 assets in `assets/`
- 0 missing local image references

## Specialist Skill Model

This project uses one main Amazon operator with specialist skills. Specialist skills are not permanent separate agents; they are focused playbooks the main operator loads when the request matches. Use temporary subagents only for larger tasks where parallel research or QA saves time.

Terminology:

- Codex agent: the main operator doing the work.
- Specialist skill: a focused playbook/toolkit the main operator opens for a workflow.
- Temporary subagent: a delegated helper used only when parallel research, independent QA, or a large split task is useful.
- Project: the shared workspace where the Amazon libraries, skills, local outputs, and safety rules live.

Default routing:

- `amazon-operator-routing`: dispatcher, source ladder, connected-browser checkpoints, stop-before-risk rules.
- `amazon-troubleshooting`: errors, suppressed listings, warnings, Account Health, blocked workflows.
- `amazon-seo`: keyword research, listing SEO, Ranking Juice, Rufus/semantic optimization, SEO audits.
- `amazon-catalog`: variations, parentage, flat files, listing edits, catalog conflicts.
- `amazon-ads`: Ads Console, PPC, Creator Connections, bidding, budgets, targeting.
- `amazon-reporting`: Seller/Ads reports, SQP, business reports, analytics workbooks.
- `amazon-inventory-planning`: weekly FBA inventory overview, reshipment planning, pCloud outputs, Slack staging.
- `amazon-opportunity-explorer`: Product Opportunity Explorer/OEI/POE exports, image strategy, product strategy, Alexa/Rufus semantic insights.
- `amazon-sop-maintenance`: `/create-sop`, `/fix-sop`, verified SOP corrections, new SOP drafts, and SOP-vs-skill routing.
- `amazon-logistics`: Send to Amazon, FBA shipments, removals, AWD, inventory operations.
- `amazon-communications`: support cases, buyer messages, creator replies, courtesy-refund follow-ups.

Inventory planning trigger phrases:

- `Weekly FBA Inventory Overview`
- `reshipment planning`
- `FBA inventory planning`
- `inventory overview`

When Victor asks for an inventory check or reshipment check, route to `amazon-inventory-planning`, use the weekly inventory reference, prepare CSV/XLSX outputs and Slack staging copy when needed, and stop before client-facing posts or account-changing actions.

Inventory and reshipment plans must be based on fresh same-day Seller Central reports requested/downloaded for the current run. Do not use older local reports or cached outputs as "latest reports" unless Victor explicitly approves that exception in the current chat.

Opportunity Explorer trigger phrases:

- `Product Opportunity Explorer`
- `Opportunity Explorer`
- `OEI`
- `POE`
- `Niche Scout`
- `amazon-image-strategy`
- `oei-product-strategy`

DataDive trigger phrases:

- `DataDive`
- `DataDive MCP`
- `niche`
- `master keyword list`
- `ranking juice`
- `Rank Radar`
- `competitor ASINs`

For DataDive research, use the local `datadive` MCP server when available. It runs `@datadive-tools/mcp` locally over stdio and is read-only. Use it for DataDive-owned niche, keyword, competitor, Ranking Juice, and Rank Radar data before falling back to manual exports. Do not save the DataDive API key in this project, commit it to GitHub, paste it into SOPs, or repeat it in operator notes. Store the key only in local MCP/client secret storage. DataDive output can inform Amazon SEO, image strategy, opportunity-data, and catalog research, but current Amazon rules and UI behavior still come from first-party Amazon docs.

For Product Opportunity Explorer work, route to `amazon-opportunity-explorer`. Use the repo-native script-first extraction workflow when an export is needed:

- `tools/opportunity-explorer/extract-opportunity-explorer.js`
- `tools/opportunity-explorer/format-opportunity-explorer-export.mjs`

Original Chrome extension/source backup, as a local placeholder path:

`/Users/victoruhl/pCloud Drive/Account shares/Amazon Wizards/2_Company/2.7_Tools/Chrome Extension-Opportunity Explorer Downloader`

Victor confirmed ownership and backend clearance for reusing the previous extension logic. The extension path is a historical/source reference only, not a repo dependency. The extension is not part of the intended workflow once the script is tested. Do not inspect cookies, session storage, local storage, tokens, or credentials while extracting OEI/POE data.

Naming note: Victor noted that Amazon's Rufus AI naming is moving/has moved toward Alexa or Alexa AI. Treat `Rufus`, `Alexa AI`, `Amazon AI search`, and `semantic Amazon search` as related trigger language unless current first-party Amazon docs say otherwise for a specific workflow.

SOP maintenance trigger phrases:

- `/create-sop`
- `/fix-sop`
- `outdated SOP`
- `broken SOP link`
- `wrong SOP steps`
- `new SOP draft`

For SOP maintenance, route to `amazon-sop-maintenance`. `/create-sop` creates a tracked draft in `sop-drafts/`. `/fix-sop` verifies the issue, updates the local tracked source file, and creates a synced change note in `sop-updates/`. Stop before pushing unless Victor explicitly asks to push.

SOP vs skill rule: create or update a SOP for a human/team Amazon process, checklist, browser workflow, or operating procedure. Create or update a skill only when changing how Codex behaves, routes work, uses tools/scripts, or applies repeatable AI workflow instructions.

Source priority:

1. For current Amazon rules, UI behavior, policies, eligibility, error text, report definitions, and requirements, use first-party Amazon docs first.
2. For Ecom Wizards methodology, generated workbooks, SEO writing, analytics logic, and client-specific playbooks, use the knowledge-base skill references first, then verify against current Amazon rules.
3. Use MAG SOPs for agency procedure and practical UI steps. Use the pCloud visual archive when screenshots, GIFs, module layouts, or visual confirmation are needed.
4. If sources conflict, prefer first-party Amazon docs for rules/current UI and MAG/internal notes for operating procedure.

## Local Output Storage

Never save generated files, exports, evidence, screenshots, review trackers, working notes, or client-specific output inside SOP or help-library folders. SOP folders should contain SOP/source documentation only.

The base local artifact folders are present after clone through `.gitkeep` files, but real files inside them are ignored and must not sync to GitHub. New generated work should use lowercase `output/`; uppercase `Output/` is only a legacy ignored alias.

Top-level folder roles:

- `output/`: generated work and analysis, such as SEO, opportunity data, ads files, reporting, inventory outputs, and catalog drafts.
- `evidence/`: screenshots, UI proof, warning captures, visible tables, and operator notes.
- `downloads/`: temporary raw Amazon exports before processing.
- `_local-output/`: one-off local staging or migration scratch space.
- `review-tracking/`: legacy ignored folder only. Keep existing local files there if they already exist, but do not create new review-management work there by default.

Use ongoing client-first paths for new artifacts:

- `output/{client-or-brand}/{workflow}/`
- `downloads/{client-or-brand}/{source}/`
- `evidence/{client-or-brand}/{workflow}/`
- `output/{client-or-brand}/review-management/`

Dates belong in filenames, not folder names. Review management is ongoing and client-specific; update the same client folder over time. Keep support drafts under `output/{client-or-brand}/support-prep/` and support evidence under `evidence/{client-or-brand}/support-prep/`; use Notion for live support-case tracking.

Controlled workflow names:

- `seo`
- `opportunity-data`
- `ads`
- `reporting`
- `inventory`
- `catalog`
- `account-check`
- `support-prep`
- `sop-maintenance`

Do not create a separate global overview tracker by default. If a workflow needs local context, put `README.md` or `operator-note.md` inside the relevant workflow folder. Use Notion for ongoing team status.

## Local Permission Memory

Standing permission changes such as "do not ask me again for this action" are user-specific consent records. The shared GitHub instructions define the mechanism, but actual standing permissions must stay local to each operator.

Store actual standing permissions only in `_local/local-permissions.md`. This file is ignored by Git and must not be committed, copied into tracked docs, or generalized into team-wide behavior. Do not store secrets, passwords, tokens, payment details, tax details, or private keys in this file.

Before any risky or externally visible action, check `_local/local-permissions.md` when it exists. A matching local permission must specify the allowed action, the applicable account/client/scope, and any limits. Generic examples of scope include a named client account, a specific support workflow, a specific marketplace, a specific message type, or a defined date range.

If a matching local permission exists, the agent may proceed only within that permission's scope and should mention in the operator note that a local standing permission was used. If no matching local permission exists, follow the normal stop-before-risk rules and ask for confirmation in the current chat.

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

## Seller Central Customer Reviews

For Brand Customer Reviews workflows, use this route:

1. Open `https://sellercentral.amazon.com/brand-customer-reviews/ref=xx_crvws_dnav_xx`.
2. Verify the selected seller account, marketplace, page title, and visible review count.
3. Use the `Star rating`, `Order Type`, `Contact Status`, and `Time Period` filters as needed.
4. Stop before sending messages or issuing refunds unless Victor has explicitly approved the specific action.

Do not use ~~`https://sellercentral.amazon.com/brands/customer-reviews`~~ as the starting route. It can redirect to Customer Experience Metrics and show an unrelated `Access Required` page.

## Seller Central Promotions and Sale Discounts

For Seller Central promotion workflows, verify current Amazon promotion/price rules first, then use MAG SOPs for the practical path:

1. Open Seller Central and go to `Advertising` > `Promotions`.
2. Choose the promotion type from the page: `Social Media Promo Code`, `Percentage Off`, or `Buy One Get One`.
3. Check existing running or scheduled promotions, coupons, deals, sale prices, or business discounts for overlap before creating a new promotion.
4. For a single-unit sales discount, consider whether the workflow should be a limited-time `Sale Price` instead of a percentage-off promotion.
5. Stop at the final review/submit step unless Victor has explicitly approved submitting the exact promotion or price change.

For negative review outreach with courtesy refunds:

1. Filter for the requested star ratings, usually `1 Stars` and `2 Stars`.
2. Save the original review data locally under `output/{client-or-brand}/review-management/` before outreach. Capture date, reviewer name/location, Amazon profile link, review link, original review count, original review text, `Changes` set to `NO`, and an empty `New review` field.
3. For eligible verified-purchase reviews, click `Contact Customer`.
4. Select `Courtesy refund`.
5. Review Amazon's standard courtesy-refund template, then click `Send` only when Victor has approved that specific courtesy-refund action.
6. After the courtesy refund is sent, the same review should display `View Messages`. Open that link to reach the Buyer-Seller Messaging thread.
7. Create the first custom follow-up message in that message thread using Victor's provided template, replacing variables with the actual customer name, brand/company, product, and sender name.
8. Stop before sending the custom message unless Victor explicitly confirms the exact send action.

## Workflow

1. Classify the request:
   Seller Central, Amazon Ads UI, Amazon Ads API/docs, Creator Connections, MAG SOP procedure, or cross-functional.

2. Search local libraries:
   Prefer first-party Amazon docs for current UI/rules, MAG SOPs for agency workflow, and user-provided account context for account-specific decisions.

3. Decide the workflow:
   Summarize the path, required inputs, likely risk points, and what will be checked.

4. Navigate the connected browser:
   Verify the selected account, marketplace, brand, date range, and visible page title before acting.

5. Preserve evidence:
   Capture important screenshots, tables, warning banners, filters, selected account, marketplace, ASIN/SKU/campaign/order/shipment/case IDs, and exact error text.

   For Account Health checks, if a policy issue or complaint row shows a `Review details` button/link, click it before summarizing the problem. Capture the expanded detail text, status, impacted ASIN/SKU/listing, date, action taken, Account Health Rating impact, and any next-step labels. Stop before submitting appeals, acknowledgements, new information, or support/contact actions.

6. Stop before risky actions:
   Unless Victor explicitly instructs otherwise for the specific action in the current chat, or a matching local standing permission exists in `_local/local-permissions.md`, do not send messages, submit Seller Support cases, create or confirm shipments, change campaigns/budgets/bids, upload bulk files, acknowledge account-health actions, change account/payment/permission/settings details, or delete data.

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

- MAG SOPs: markdown-only runtime copy in this project; complete visual version in the pCloud archive.
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
