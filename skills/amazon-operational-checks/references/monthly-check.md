# Monthly Operational Check

Run accounts in the configured stable regional order. Do not repeat weekly review, stranded-inventory, variation, or fee checks.

## Per-Account Sequence

1. Verify login, Seller Central account label, marketplace, page, and a trailing 30-day date range.
2. Review returns and refunds by ASIN. Create or update a finding only when both conditions are true:
   - Return rate is greater than 10%.
   - Returned units are at least 3.
3. Record orders, returned units, return rate, top reason, and comparison context when visible. Do not treat a low-volume percentage alone as actionable.
4. Review Voice of the Customer. Summarize useful positive signals. Create or update tasks only for actionable negative patterns, such as poor customer-experience status or repeated product complaints.
5. Check for a completed full reshipment plan for the same account-marketplace within the preceding seven calendar days. If it contains an excess-inventory section, reuse that section and record its run date instead of repeating the overstock check.
6. Otherwise review excess, aged, and high-days-of-cover inventory. Create a promotion-planning task only when action is warranted. Do not create or submit a promotion.
7. Match findings to open tasks using account, marketplace, issue type, and ASIN. Update matched tasks instead of duplicating them.

## Completion

Post one compact internal summary with:

- Accounts checked and skipped.
- Return exceptions and Voice of the Customer signals.
- Overstock findings or reused reshipment evidence.
- Tasks created or updated.
- Clean checks, blockers, and stop points.

Do not perform fee sampling or run a full reshipment plan.
