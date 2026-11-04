---
name: amazon-ads-performance-briefs
description: "Produce read-only daily or weekly Amazon Ads performance briefs from Sellerboard and SYNQ data, including trend, pacing, and data-quality flags."
---

# Amazon Ads Performance Briefs

Browser: None (read-only file and MCP inputs; local brief generation and Slack delivery).

Use this skill for daily or weekly Amazon Ads performance briefs. It observes and reports; it never changes campaigns.

## Modes

- `daily`: previous-day performance versus the prior day and trailing seven-day average.
- `weekly`: completed-week performance, week-over-week drivers, pacing, recommendations, and data confidence.

Read `references/brief-workflows.md` after selecting the mode. It contains the source priority, data-quality gates, daily and weekly flows, toolkit commands, Slack delivery contract, and hard rules.

Sellerboard is the account P&L source; SYNQ supplies campaign and target detail and the cross-check through its read-only MCP. Read [references/runtime-caveats.md](references/runtime-caveats.md) before trusting a same-day figure, a SYNQ list that may be row-capped, a total-sales figure inside the 2 to 3 day Sales and Traffic lag, or a missing scheduled brief. The AdLabs carve-out account (US and CA) still pulls from AdLabs; follow the "AdLabs carve-out only" section of `references/brief-workflows.md` for them.

Route interactive Ads Console work to `amazon-ads-console`, Sponsored Products bulk files to `amazon-sponsored-products-bulk-files`, audits to `amazon-audit`, and approved weekly optimization to `amazon-ppc-weekly-management`.
