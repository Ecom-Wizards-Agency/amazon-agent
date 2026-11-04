---
description: Run the weekly PPC loop for a SYNQ client (stock and budget gates, runner review, proposals, approved SYNQ web-app changes); the AdLabs carve-out account keeps its AdLabs loop
argument-hint: "<client/profile> [week-end date]"
---

# Weekly PPC Management

Load and follow the `amazon-ppc-weekly-management` skill as the source of truth.

The requested target is: **$ARGUMENTS**

If no client/brand is given in the arguments, FIRST ask the operator which brand and
marketplace(s) to run (one question, before any data pull). Same for the week-end date if
missing: dates are operator-supplied, never defaulted.

Rules that always hold, whatever the arguments:

- Doctrine and thresholds come from `_local/ads-strategy/strategy.md` v3 and `strategy.json` `management`; never guess them.
- SYNQ reads start with `list_clients` (skip demo clients), a `get_catalog` SKU or title check, then `get_sync_status`.
- Every change is a proposal -> explicit operator approval of that exact action -> `batches.py snapshot` -> the change in the SYNQ web app on the operator browser -> readback with the SYNQ change tools. No approval, no change. Grimoire never writes.
- A SYNQ runner and any other bid writer never share a campaign. Before any one-off bid or budget push, read the SYNQ Bid Optimizer page read-only to confirm the campaign is in no runner or is excluded from it; the change log is supporting evidence only.
- Rank campaigns are never cut for pacing reasons without an explicit operator decision.
- The AdLabs carve-out account (US and CA, identified in `docs/synq-mcp.md`) follows `skills/amazon-ppc-weekly-management/references/adlabs-carve-out.md` (AdLabs loop and dayparting schedules).
