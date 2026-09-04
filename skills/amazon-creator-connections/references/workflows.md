# Creator Connections Workflows

Every workflow inherits the main skill rules: verify account/brand/product first, protect private data, preserve the tracker, resolve the Creator Record ID, and stop before risky actions unless approved.

## `audit`: daily or ad hoc message sweep

Use for: “run a sweep,” “check new messages,” “who replied,” “who posted,” “who confirmed,” “who is ready for samples.”

1. Open the correct brand’s Creator Connections messages.
2. Use the requested scope. Default to new/updated threads since the last tracker or Slack sweep.
3. For each thread, verify and resolve:
   - creator display name
   - Creator Record ID or a safe new-record decision
   - campaign context
   - exact ASIN/product, if present
   - latest creator message
   - whether we already replied
   - whether the creator provided full details, proof, or content links
4. Run the creator background check before requesting proof or fulfillment details:
   - Amazon storefront or creator profile link
   - visible recent shoppable videos/posts
   - Earns Revenue badge, if visible
   - attached product cards and relevance to the campaign product
   - media kit, portfolio, or public social links when available
   - basic spam/ghosting risk signals
5. Populate the tracker qualification columns from the background check. If the creator passes the visible fit check, request only the basic fulfillment details still missing: full name, complete shipping address, email, phone, and final ASIN/product confirmation.
6. Classify the update:
   - new inquiry
   - verification sent
   - verification confirmed
   - proof requested
   - manager review
   - product switch
   - sample ready
   - sample sent/delivered
   - awaiting content
   - content posted
   - paused product
   - unqualified/ghosted/declined
7. Update the tracker row or create one in the correct tab. Append an audit-log entry and add any due work to the daily action queue.
8. Draft any needed creator replies, but do not send unless approved in the current chat or covered by standing permission.
9. If Slack reporting is requested or automated, use only the configured posting helper and post only new updates/material status changes.

## `campaign`: prepare or launch a campaign

Use for: “launch Creator Connections for this ASIN,” “copy the reference campaign,” “create a July–December campaign.”

Inputs: brand/account, product ASIN, reference campaign, campaign dates, budget, commission, and desired folder/profile.

1. Verify the live Amazon listing:
   - title
   - ASIN
   - availability
   - current product claims
   - main selling points
2. Use the reference campaign’s naming convention and structure.
3. Create a product-specific campaign description based only on the listing and approved product info.
4. Use the client-provided commission and budget. Do not assume a default range or number.
5. Create or confirm the campaign-level tracker tab.
6. Prepare campaign fields in Creator Connections.
7. Stop before publish and show the operator the campaign setup for final approval.

## `tracker`: create or repair a tracker tab

Use for: “create a tracker for this campaign,” “make this tab match the approved tracker,” “add a tab for active campaign.”

1. Read the live campaign:
   - campaign name
   - product title + ASIN
   - start/end date
   - commission
   - campaign status
   - campaign ID/type
   - accepted creators
   - submitted content
   - budget/remaining budget/spend
   - orders/sales/clicks
   - campaign link/product page
2. Duplicate the approved tracker format.
3. Preserve:
   - first 10 header/info rows
   - merged category headers
   - dropdowns and chip colors
   - formulas and validation
   - column order
4. Create rows only from verified campaign/message evidence.
5. If product is unclear, use the `Undecided` tab.

## `gaps`: find missing trackers

Use for: “which active campaigns don’t have trackers,” “which products are not running/tracked yet.”

1. Inventory active Creator Connections campaigns.
2. Inventory tracker tabs.
3. Compare by campaign name, ASIN, and product title.
4. Report missing or ambiguous trackers with:
   - campaign name
   - product/ASIN
   - campaign link
   - status
   - message count/content count, when visible
   - recommended tab name
5. Create tabs only after product/campaign matching is verified.

## `reconcile`: full-system audit

Use for: “audit everything,” “make sure all campaigns and trackers are clean,” “retrace messages.”

1. Inventory campaigns.
2. Inventory tracker tabs.
3. Read message threads in scope.
4. Reconcile:
   - duplicate creator rows
   - product switches
   - missing details
   - sample status
   - posted content links
   - stale follow-ups
   - unanswered inquiries
   - creators in the wrong product tab
5. Move unresolved product matches to `Undecided`.
6. For an MCF-blocked exact ASIN, verify the original blocker and a same-campaign FBA/MCF-fulfillable alternative before sending a switch request. Keep the original ASIN active and Sample Decision `Hold` until the creator explicitly replies with the alternate ASIN.
7. Move confirmed product switches to the final product tab only after `preflight-switch --phase confirm` passes.
8. Preserve historical notes without keeping duplicate active sample rows.
9. Report manager decisions needed and exact next steps.

## `explain`: explain the system

Use for: “what can this repo/skill do,” “explain this to my manager/client.”

Summarize in plain language:

- The system launches Creator Connections campaigns from the front end.
- It tracks every creator in campaign-level Google Sheet tabs.
- It uses a background-check and qualification gate before sample approval.
- It asks for basic fulfillment details only after visible creator fit is strong enough, and asks for proof only when the background check cannot verify enough.
- It prepares MCF sample details only after approval.
- It tracks sample sent, delivery, posted content, links, and follow-ups.
- It posts clean Slack sweep updates for internal visibility.
