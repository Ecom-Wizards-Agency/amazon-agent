---
name: amazon-operator-routing
description: Route Amazon Seller Central, Amazon Ads, Amazon Creator Connections, reports, support cases, account health, shipments, inventory planning, SEO, catalog, communications, and bulk-file tasks through the right specialist skill and local Amazon libraries before taking browser action. Use when Codex must answer, troubleshoot, prepare, or operate inside Amazon Seller Central or Amazon Ads, especially with browser navigation, screenshots, tables, support-case drafts, report downloads, shipment creation, creator communication, campaign setup, bidding/budget work, bulk files, or account-health issues.
---

# Amazon Operator Routing

## Core Rule

Search the local Amazon libraries before answering or touching the connected browser. Use the search results to decide the workflow, then navigate the connected browser with explicit checkpoints and stop before risky actions.

Use this skill as the dispatcher. After classifying the request, load the relevant specialist skill when the task matches: `amazon-troubleshooting`, `amazon-account-health-check`, `amazon-seo`, `amazon-catalog`, `amazon-ads`, `amazon-reporting`, `amazon-inventory-planning`, `amazon-opportunity-explorer`, `amazon-sop-maintenance`, `amazon-logistics`, or `amazon-communications`.

## Browser Standard

Use the teammate's connected Codex browser for Amazon Seller Central, Amazon Ads, MAG SOP, and logged-in Amazon help workflows. Common choices are Chrome or Brave.

If `local-browser-preference.md` exists in the project root, read it before browser work and use that preferred connected browser when available. If no local preference exists, use the connected browser/session available in the current chat.

Before acting in Amazon, verify the connected browser/session is logged in and confirm the selected account/advertiser, marketplace/country, visible page title/tool, and date range or filters when relevant. If the preferred browser is unavailable or not logged in, pause and ask which connected browser/session to use.

## Amazon Ads Account Selection

For Amazon Ads workflows, open `https://advertising.amazon.com/campaign-manager` first, then use the account selector in the top-right of Campaign Manager to choose the correct account/brand/country. After the correct account is selected, use the left navigation to reach the target tool.

Creator Connections route:

1. Open `https://advertising.amazon.com/campaign-manager`.
2. Select the correct account in the top-right account selector.
3. In the left navigation, open `Brand content`.
4. Click `Creator connections`.

Do not start Creator Connections from ~~`https://advertising.amazon.com/choose-account?destination=/bi`~~. That direct link can hide many accounts and only show a partial account chooser, so it is unreliable for selecting a specific client account.

## Local Libraries

Read `references/library-map.md` and `references/specialist-routing.md` when choosing where to search. Main folders:

- `<repo-root>/MAG SOPs`
- `<repo-root>/sop-drafts`
- `<repo-root>/Amazon Seller Help`
- `<repo-root>/Amazon Ads Help`
- `<repo-root>/Advertising Help After Login`

Use `scripts/search_amazon_libraries.py` for quick local search:

```bash
python3 "<repo-root>/skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "create shipment"
python3 "<repo-root>/skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "bid adjustment" --library ads --limit 8
python3 "<repo-root>/skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "account health appeal" --library seller --limit 8
```

## Routing Workflow

1. **Classify the user request.**
   Decide whether it is Seller Central, Amazon Ads Console, Amazon Ads API/docs, MAG SOP, or cross-functional.

2. **Choose the specialist skill.**
   Use `references/specialist-routing.md`. Most tasks should use a specialist skill internally. Spawn temporary subagents only for parallel research, independent QA, or large multi-part work.

3. **Search the correct library first.**
   Use obvious terms and Amazon UI labels. Search synonyms too:
   - shipment: `shipment`, `FBA`, `send to Amazon`, `reconcile`
   - reports: `report`, report name, `download`, `business report`, `search term`, `bulk`
   - cases: `case`, `support`, `ticket`, `appeal`, `contact us`
   - account health: `account health`, `violation`, `policy`, `appeal`, `performance`
   - creators: `creator`, `creator connections`, `campaign`, `message`
   - ads: `campaign`, `bidding`, `budget`, `targeting`, `bulk`, `Sponsored Products`, `Sponsored Brands`, `DSP`
   - opportunity explorer: `Product Opportunity Explorer`, `Opportunity Explorer`, `OEI`, `POE`, `Niche Scout`, `image strategy`, `product strategy`
   - Amazon AI search: `Rufus`, `Alexa AI`, `Amazon AI search`, `semantic search`

   If the request may involve both agency procedure and current Amazon UI behavior, search one first-party library, MAG, and relevant `sop-drafts/` before deciding.

4. **Decide the workflow.**
   Read `references/workflow-router.md` for common tasks. If several sources conflict, prefer:
   - Current Amazon first-party docs for current UI/rules.
   - Knowledge-base skills/client notes for Ecom Wizards methodology, generated workbooks, SEO writing, analytics logic, and account-specific context.
   - MAG SOPs for agency procedure and practical operator steps.
   - `sop-drafts/` for recent but not-final workflow learnings.

5. **Prepare before browser action.**
   Summarize the intended path and required inputs. Identify risky steps before they happen.

6. **Navigate the connected browser step-by-step.**
   Follow `references/chrome-checkpoints.md`. Capture/inspect visible state at each major screen. Preserve tables, visible warnings, values, dates, report filters, selected accounts, marketplaces, and IDs.

7. **Stop before risky actions.**
   Ask for confirmation before sending messages, submitting support cases, creating shipments, changing campaigns/budgets/bids, uploading bulk files, deleting data, or making externally visible changes.

8. **Finish with an operator note.**
   Include what was done, what source(s) were used, open risks, exact files downloaded/prepared, and next action needed from the operator if any.

## Visual and Table Preservation

When the task involves UI learning, troubleshooting, or documentation:

- Preserve table values in markdown tables.
- Save screenshots when they show an important UI state, error, warning, or workflow step.
- Record exact page names, tab names, button/menu labels, filters, marketplace/account selectors, report types, and date ranges.
- For troubleshooting, capture the symptom, likely root cause, evidence, and next recommended action so the operator does not need to research it again.

## Safety Rules

Avoid local actions that have triggered cybersecurity warnings:

- Do not inspect broad system processes.
- Do not kill broad processes.
- Do not use broad cleanup commands.
- Do not reset browser automation unless necessary and explicitly safe.
- Do not copy, store, or repeat credentials, API secrets, bearer tokens, refresh tokens, payment identifiers, bank details, tax IDs, or private keys.
- Summarize credential-heavy Amazon documentation examples instead of saving runnable secret-handling snippets.

Browser stop points:

- Do not send creator messages without confirmation.
- Do not submit Seller Support cases without confirmation.
- For Seller Support follow-ups or escalations, reply inside the existing case when one exists. Do not open a duplicate case for the same issue unless the operator explicitly asks for a new case or Seller Central blocks replies.
- Before live Seller Support chat, support-case submission, or email-style case replies, check `_local/local-permissions.md` for the locally configured operator full name. Use that full name for traceability when Amazon asks for a sender name or when signing a message. If no full name is stored locally, pause and ask the operator before sending. Never commit the actual local identity to GitHub.
- In Seller Support chat, wait for the associate's first message before sending substantive details. Send one focused message at a time and wait for the next associate reply. If the associate says they are still checking, reply politely that the named operator is still waiting.
- Do not create or confirm shipments without confirmation.
- Do not upload bulk files without confirmation.
- Do not change bids, budgets, campaigns, account settings, permissions, or payment details without confirmation.
- Do not download sensitive reports into an unclear folder; confirm destination if not already specified.

## Response Pattern

For operational tasks, keep the user updated:

1. “I found the relevant SOP/docs: …”
2. “The workflow is: …”
3. “I’m at this screen/checkpoint: …”
4. “This is the risky action; confirm before I continue: …”
5. “Done; saved/downloaded/prepared: …”

If blocked, explain the exact blocker and the next useful retry, not a generic failure.
