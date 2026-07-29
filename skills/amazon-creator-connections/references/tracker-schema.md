# Creator Connections Tracker Schema

The tracker is a client-shareable Google Sheet with one tab per campaign plus an `Undecided` tab for unconfirmed product matches.

Preserve the sheet structure exactly. Do not restyle or reorder columns unless the operator asks.

## Header structure

Rows 1–8 contain campaign or tab metadata.

Rows 9–10 contain merged category headers and column headers.

Do not include dropdowns in rows 1–10 unless the existing sheet already does. Data rows start at row 11.

## Core tabs

- Campaign tabs: one tab per campaign/product/date range.
- `Undecided`: creators who have not confirmed final product/ASIN.
- Brand-level dashboards are optional and should not replace campaign-level tabs.

## Column groups

Use the approved column order:

### Creator + campaign activity

1. Creator Name
2. Status
3. Full Name
4. Address
5. Email
6. Phone
7. Date Sent
8. Product
9. Content Posted
10. Posted Link(s)
11. Notes

### Sample fulfillment / MCF tracking

12. Fulfillment Method
13. Address Confirmed Date
14. Sample Approved By
15. Sample Sent Date
16. MCF Order ID
17. Tracking Number
18. Delivery Status
19. Follow-up Date

### Creator qualification gate

20. Amazon Storefront Link
21. Portfolio / Media Kit Link
22. Requested ASIN
23. Product Match Status
24. Recent Posting Verified?
25. Last Visible Post Date
26. Content Quality Rating
27. Category Fit
28. Performance Evidence Available?
29. Earns Revenue Badge?
30. Revenue Badge Source
31. Revenue Threshold Met?
32. Specific ASIN Mentioned?
33. Spam Risk
34. Risk Flags
35. Total Qualification Score
36. Qualification Tier
37. Sample Decision
38. Qualification Notes

## Status dropdowns

Use the existing sheet dropdown values and chip colors. Common values include:

- New Inquiry
- First-Base Pass
- Verification Sent
- Verification Confirmed
- Proof Requested
- Manager Review
- Approved for Sample
- Sample Sent
- Delivered / Awaiting Content
- Content Posted
- Follow Up
- <Product> Pause
- On Hold
- Unqualified
- Ghosted
- Declined / Closed
- Address Verification
- Inquiry Sent

When adding or changing a status, keep a matching color. Do not leave new statuses white/unformatted. For client-specific product pauses, use a clear status such as `<Product> Pause` and document the exact wording in local notes.

## Qualification gate

Use a 10-point score as a decision aid, not an automatic approval.

Suggested scoring:

- Recent active posting: 0–2
- Content quality: 0–2
- Category/product fit: 0–2
- Performance/revenue proof: 0–1
- Specific ASIN mentioned: 0–1
- Storefront or portfolio available: 0–1
- Responsiveness/complete details: 0–1

Tiers:

- 8–10: `A - Send`, only if product match is exact and risk is low.
- 5–7: `B - Review`, ask for missing proof/details or manager approval.
- 0–4: `C - Do Not Send`, hold or reject until proof improves.

Prefer 10/10 before sample sending. Surface 8–9 candidates only with clear missing items and operator decision.

## Sample decision

Allowed sample decisions:

- Send
- Hold
- Do Not Send

Do not set `Send` unless:

- product/ASIN is confirmed
- creator passed the qualification gate or operator approved an exception
- full shipping/contact details are complete
- no major risk flag remains

## Product switch rules

- If a creator changes desired product, confirm the final product/ASIN before moving rows.
- Once confirmed, move the active row to the final product tab.
- Leave the old product row only if needed as historical context, and mark it `On Hold` / `Do Not Send`; do not keep multiple active sample-ready rows.
- Do not move undecided creators until they confirm.

## Undecided tab

Use `Undecided` when:

- no ASIN was provided
- product name is vague
- multiple products were requested without final choice
- the creator asks for “any product”
- the message appears under one campaign but the creator’s actual desired product is unclear

Sample decision must stay `Hold` or `Do Not Send` until the creator confirms exact product/ASIN.

## Notes rules

Notes should be concise evidence logs:

- message date
- what the creator provided
- what we asked
- proof/status found
- sample decision and blocker
- reply sent date

Do not write private data into repo files or Slack. Keep addresses, emails, and phone numbers in the tracker only.
