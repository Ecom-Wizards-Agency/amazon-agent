---
title: "Understand automatic budget allocation in Display, Video, and Audio campaigns"
source_url: "https://advertising.amazon.com/help/GB8PANYRYQY4F4X3"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Understand automatic budget allocation in Display, Video, and Audio campaigns

Prioritize spending on better performing ad groups with automated budget allocation.

If you're participating in the DVA+ beta, these features can only be manually adjusted in DVA+ with Advanced settings.

## What is automatic budget allocation?

Use automated budget allocation to prioritize spending on better performing ad groups according to your selected KPI, and also rollover unused budget to your next flight. It works at the ad group level along with any pacing profile (even, pace ahead, ASAP) and.

- alleviates the manual process of considering factors like historic performance insights and delivery to determine how to distribute budget.
- reduces wasted impressions on lower performing lines.
- increases campaign performance through dynamic budget allocations.

**Tip**: Use the same pacing profile for all ad groups in a campaign.

## How it works

You opt in to automated budget allocation during campaign setup and it begins right away (running 7 days a week). It detects slow spending ad groups ($5 a day) and shifts the remaining budget to higher spending ad groups within the campaign. If the projected spend of all ad groups sums to an amount less than your budget, then the campaign may underdeliver.

Usually automatic budget allocation is set up by default, but check your campaign and ad group settings to modify it.

When you create a new campaign, you'll choose a goal and KPI. Once you do so, the optimization strategy section will appear. Usually automatic budget allocation is selected by default. To make changes:

1. Click **Change**.
2. Select **Automate budget allocation**.
3. Click **Done**.

## Best practices

- Set a budget of at least $5 a day for each ad group.
- If you don't want to include all ad groups in automatic budget allocation, you can exclude them by adding a manual budget on the ad group setting page.
- Use projected spend to identify important tactics that are likely to underdeliver. To address this, increase the maximum average CPM (cost per 1000 impressions).

## Budget allocation status

| Status | Color | What it means | Action required |
| --- | --- | --- | --- |
| Optimizing | Green | Budget optimization is running normally. | No action is required. You can hover over the budget optimization icon to see the most recent budget change made. |
| Optimized out | Yellow | This ad group isn't delivering due to budget optimization reallocations. | Increase the campaign budget such that the updated budget is equal to or greater than $5 per ad group per each remaining flight day. |
| Ended | Gray | The ad group's flight dates have passed. | Rebook the line item. |
| Not enrolled | No icon | The ad group is opted out of budget optimization and the projected spend is equal to the ad group budget you've manually set. | Opt the ad group in to budget optimization by selecting Automatically optimize budget in the budget section of the ad group settings page. |
