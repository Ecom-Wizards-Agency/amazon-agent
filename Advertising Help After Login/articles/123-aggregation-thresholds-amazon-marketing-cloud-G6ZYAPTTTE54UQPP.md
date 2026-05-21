---
title: "Aggregation thresholds"
source_url: "https://advertising.amazon.com/help/G6ZYAPTTTE54UQPP"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-05-13"
status: "captured"
---

# Aggregation Thresholds in Amazon Marketing Cloud

This article explains AMC aggregation thresholds and how they affect query outputs.

## Key Points

- AMC uses aggregation thresholds so outputs are sufficiently aggregated before analysis.
- Some columns have high or very high thresholds and may not be allowed in final outputs.
- `user_id` is treated as highly sensitive and cannot be selected in final SQL outputs.
- Threshold classification affects whether columns can appear in output workflows.

## Threshold Classes

| Class | Meaning |
| --- | --- |
| NONE | No aggregation threshold. |
| LOW | Lower aggregation restriction. |
| MEDIUM | Medium aggregation restriction. |
| HIGH | Higher aggregation restriction. |
| VERY_HIGH | Strong restriction; sensitive columns may not be output. |
| INTERNAL | Internal-use threshold behavior. |

## Workflow

1. Understand column threshold classifications.
2. Use the AMC Query Editor option to append aggregation threshold columns when troubleshooting.
3. Review query output for NULL values caused by thresholds.
4. Adjust query granularity and time windows if needed.

## Checkpoints

- Stop before exporting or sharing AMC query outputs.
- Check NULL rates in critical metrics before discarding data.
- Expand time windows or use less granular grouping to reduce threshold-driven NULLs.
- Keep privacy thresholds intact; do not try to expose user-level data.

## Routing Use

Use this page when the user asks why AMC query output has NULL values, missing fields, or aggregation/privacy restrictions.
