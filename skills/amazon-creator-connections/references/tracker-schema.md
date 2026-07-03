# Creator Tracker Schema

The tracker is a shared Google Sheet with one tab per campaign (campaign-level model, client-shareable). The sheet URL is per-client (`_local/creator-connections/<client>-config.json`).

## Columns (preserve exactly, in this order)

| Column | Rules |
| --- | --- |
| Creator Name | Creator's display name from the thread/campaign. |
| Status | Approved dropdown values only — do not invent new statuses. Covers the sample/collaboration lifecycle (e.g. inquiry, sample requested, sample sent, ghosted, unqualified, content submitted). Read the existing dropdown from the sheet; record the client's actual value set in local notes on first contact. |
| Full Name | Verified full name, only when the creator provided it. |
| Address | Verified shipping address, only when present. Never copy addresses into tracked repo files or reports — sheet only. |
| Date Sent | Sample ship date, only when shipment is confirmed. |
| Product | The matched product (per the SKILL.md matching order). |
| Content Posted | Yes/No validation only. |
| Posted Link(s) | Verified content links (opened and checked, not just claimed). |
| Notes | Concise evidence notes: thread date, what was agreed, replies sent, follow-up needed. |

## Rules

- **One row per creator per campaign.** Update the existing row; never duplicate.
- Preserve the tab's existing formatting, dropdown validations, and metadata header when editing.
- New tabs duplicate the client's approved styling and carry a metadata header read from the live campaign: campaign name, product title, ASIN, schedule, commission, status, campaign ID, campaign type, budget/remaining/spend, orders, sales, clicks, campaign link, product link.
- Tab naming: product + date range (e.g. `Product Jan 26-27`), matching the client's existing convention when one exists.
- Creator personal data (full names, addresses) stays in the sheet and `_local/` only.
