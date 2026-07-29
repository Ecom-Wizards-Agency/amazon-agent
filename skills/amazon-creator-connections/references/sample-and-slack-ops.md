# Sample Fulfillment and Slack Operations

Use this reference for priority sample lane, MCF preparation, and Slack sweep updates.

## Priority sample lane

Separate creators into clear lanes:

### Ready for sample

Creator can be prepared for MCF only when:

- exact product/ASIN is confirmed
- sample decision is `Send` or operator says to proceed
- full name is present
- complete address is present
- phone/email are present when needed for MCF
- proof/revenue/recent content gate is passed or operator approved exception
- no unresolved recipient mismatch
- no major spam/review-manipulation risk

### Awaiting final confirmation

Use for strong candidates with one final blocker, such as:

- missing phone
- recipient/content creator mismatch
- final ASIN confirmation needed
- proof accepted but shipment details incomplete

Keep `Sample Decision = Hold` until confirmed.

### Not ready

Use for:

- no exact ASIN
- unclear product match
- weak/no proof
- incomplete details
- repeated spammy outreach
- guaranteed 5-star-review wording
- high risk

## MCF preparation

Preparing an MCF order is allowed after the operator approves the creator/sample. Creating the order is a stop-before-risk action unless the operator explicitly says to create it.

Before MCF:

1. Verify creator row and latest thread.
2. Verify exact ASIN/SKU and unit count.
3. Verify full name, street, city, state/province, ZIP/postal code, phone, and email.
4. Confirm sample quantity, usually 1 unit unless operator says otherwise.
5. Use a structured custom order ID:
   - `CC-{BRAND}-{PRODUCTCODE}-{CREATOR}-{ASIN}-{YYMMDD}`
6. Stop for final visual check before clicking Create order unless operator has explicitly approved.

After MCF order confirmation:

- Update tracker:
  - Status: `Sample Sent`
  - Fulfillment Method: `MCF`
  - Address Confirmed Date
  - Sample Approved By
  - Sample Sent Date
  - MCF Order ID
  - Delivery Status
  - Follow-up Date
  - Notes
- Send the standard sample confirmation message only after the order is confirmed.

## Fees

MCF can create fulfillment/shipping fees charged to the seller/account. If the operator asks, confirm estimated fees on the MCF page before order creation.

## Posted content tracking

When a creator posts content:

1. Open and verify the link.
2. Confirm the product/ASIN shown/tagged when visible.
3. Update:
   - Content Posted = Yes
   - Posted Link(s)
   - Status = Content Posted
   - Notes
4. Send thank-you message if approved.
5. Track performance later from campaign reporting when available.

## Daily Slack sweep

Post to the internal Creator Connections Slack channel only when there are new updates or material status changes.

Use one parent message:

```text
{Brand} Creator Connections Sweep: {Month Day, Weekday}
```

Put details inside the thread as a reply.

Keep Slack PII-free:

- no addresses
- no phone numbers
- no emails
- no private tracker URLs unless approved

Use clear categories:

- 🆕 New / First-Base Candidates
- ✅ Verification Confirmed / Ready for Review
- 📦 Priority Sample Lane / Fulfillment Updates
- 🎥 Content Posted / Links Logged
- 🔄 Product Switch / Needs Review
- ⚫ Paused Product
- 🚫 Filtered Out / Not Sample Candidate
- 📌 Action Needed

Only include new updates or changed statuses. Do not repeat unchanged items.

## Weekly Slack summary

Every Monday, create a client-facing-ready internal summary for the prior Monday–Sunday period.

Include:

- short overview
- key movement this week
- sample/fulfillment highlights
- content posted/performance updates
- follow-ups/next actions

Do not include the tracker link unless explicitly requested.

## Common guardrails

- Do not post Slack updates based on stale data if Amazon login is unavailable.
- Do not include sensitive creator contact details in Slack.
- Do not mark someone sample-ready while waiting for final ASIN, phone, recipient confirmation, or proof.
- Keep product switches and undecided creators out of product tabs until confirmed.
