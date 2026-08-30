---
name: amazon-ads-performance-briefs
description: "Produce read-only daily or weekly Amazon Ads performance briefs from Sellerboard and AdLabs data, including trend, pacing, and data-quality flags."
---

# Amazon Ads Performance Briefs

Browser: None (read-only file and MCP inputs; local brief generation and Slack delivery).

Use this skill for daily or weekly Amazon Ads performance briefs. It observes and reports; it never changes campaigns.

## Modes

- `daily`: previous-day performance versus the prior day and trailing seven-day average.
- `weekly`: completed-week performance, week-over-week drivers, pacing, recommendations, and data confidence.

Read `references/brief-workflows.md` after selecting the mode. It contains the source priority, data-quality gates, daily and weekly flows, toolkit commands, Slack delivery contract, and hard rules.

Route interactive Ads Console work to `amazon-ads-console`, Sponsored Products bulk files to `amazon-sponsored-products-bulk-files`, audits to `amazon-audit`, and approved weekly optimization to `amazon-ppc-weekly-management`.
