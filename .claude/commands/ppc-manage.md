---
description: Run the weekly PPC management loop for an AdLabs-managed client (stock gate, pacing, Rank Radar, optimizer preview -> approval -> apply)
argument-hint: "<client/profile> [week-end date]"
---

# Weekly PPC Management

Load and follow the `amazon-ppc-management` skill as the source of truth.

The requested target is: **$ARGUMENTS**

If no client/brand is given in the arguments, FIRST ask the operator which brand and
marketplace(s) to run (one question, before any data pull). Same for the week-end date if
missing: dates are operator-supplied, never defaulted.

Rules that always hold, whatever the arguments:

- Doctrine and thresholds come from `_local/ads-strategy/strategy.md` v3 and `strategy.json` `management`; never guess them.
- Dates for `preview_optimization` / `preview_harvest` are operator-supplied, never defaulted.
- Every write is preview -> explicit operator approval of that batch -> apply with a meaningful note. No approval, no apply.
- Rank campaigns are never cut for pacing reasons without an explicit operator decision.
