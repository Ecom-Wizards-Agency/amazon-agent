# Negative Review Tracking

Use the shared Google Sheet `Review Management`:

`https://docs.google.com/spreadsheets/d/18otgJNjAKRlpDyTQkcCzhHAqKTxMJc6EgxrQBj8TG_A/edit`

Use one configured tab per client-market. Preserve these columns in order:

1. `Date`
2. `Name and address`
3. `Link to their Amazon profile`
4. `Link to the review`
5. `Original review count`
6. `Original review text`
7. `Changes (YES / NO)`
8. `New review`

## Weekly Procedure

1. Load `docs/seller-central-procedures.md` before opening Brand Customer Reviews.
2. Verify the seller account, marketplace, page title, and filters.
3. Filter for new 1- and 2-star reviews since the previous successful weekly run.
4. Read the configured tab before writing. Treat the canonical review URL or Amazon review ID as the unique key.
5. Append a row only when no matching review exists.
6. For a new row, save the original date, reviewer, profile URL, review URL, star count, and text. Set `Changes (YES / NO)` to `NO` and leave `New review` empty.
7. When a matched review's star count or text changed, keep the original fields, set `Changes (YES / NO)` to `YES`, and write the current star count and text into `New review` with the observation date.
8. Do not append a duplicate when nothing changed.
9. Create or update a task only when Seller Central offers an actionable path such as eligible outreach, refund review, or escalation. Tracking alone does not require a task.

Never contact the customer or issue a refund during the weekly check. Route approved follow-up to `amazon-communications`.

## Acceptance Examples

- New URL: append one row.
- Existing URL with identical rating and text: no write and no task.
- Existing URL with changed rating or text: update the existing row; do not append.
- New negative review with no available action: append the row and report it; do not create a task.
- Missing configured tab: stop for that client unless activation already approved copying the configured empty template tab.
