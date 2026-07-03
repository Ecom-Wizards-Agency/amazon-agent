# Seller Central Procedures

Operator-verified routes and step-by-step procedures for Seller Central workflows. Load this file before doing Brand Customer Reviews, promotions, or courtesy-refund outreach work. Global stop-before-risk rules from `AGENTS.md` always apply.

## Brand Customer Reviews

For Brand Customer Reviews workflows, use this route:

1. Open `https://sellercentral.amazon.com/brand-customer-reviews/ref=xx_crvws_dnav_xx`.
2. Verify the selected seller account, marketplace, page title, and visible review count.
3. Use the `Star rating`, `Order Type`, `Contact Status`, and `Time Period` filters as needed.
4. Stop before sending messages or issuing refunds unless the operator has explicitly approved the specific action.

Do not use ~~`https://sellercentral.amazon.com/brands/customer-reviews`~~ as the starting route. It can redirect to Customer Experience Metrics and show an unrelated `Access Required` page.

## Promotions and Sale Discounts

For Seller Central promotion workflows, verify current Amazon promotion/price rules first, then use MAG SOPs for the practical path:

1. Open Seller Central and go to `Advertising` > `Promotions`.
2. Choose the promotion type from the page: `Social Media Promo Code`, `Percentage Off`, or `Buy One Get One`.
3. Check existing running or scheduled promotions, coupons, deals, sale prices, or business discounts for overlap before creating a new promotion.
4. For a single-unit sales discount, consider whether the workflow should be a limited-time `Sale Price` instead of a percentage-off promotion.
5. Stop at the final review/submit step unless the operator has explicitly approved submitting the exact promotion or price change.

## Negative Review Outreach with Courtesy Refunds

1. Filter for the requested star ratings, usually `1 Stars` and `2 Stars`.
2. Save the original review data locally under `output/{client-or-brand}/review-management/` before outreach. Capture date, reviewer name/location, Amazon profile link, review link, original review count, original review text, `Changes` set to `NO`, and an empty `New review` field.
3. For eligible verified-purchase reviews, click `Contact Customer`.
4. Select `Courtesy refund`.
5. Review Amazon's standard courtesy-refund template, then click `Send` only when the operator has approved that specific courtesy-refund action.
6. After the courtesy refund is sent, the same review should display `View Messages`. Open that link to reach the Buyer-Seller Messaging thread.
7. Create the first custom follow-up message in that message thread using the operator's provided template, replacing variables with the actual customer name, brand/company, product, and sender name.
8. Stop before sending the custom message unless the operator explicitly confirms the exact send action.
