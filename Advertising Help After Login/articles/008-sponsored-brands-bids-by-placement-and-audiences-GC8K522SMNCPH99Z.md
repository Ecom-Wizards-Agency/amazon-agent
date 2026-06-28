---
title: "Sponsored Brands bids by placement and audiences"
source_url: "https://advertising.amazon.com/help/GC8K522SMNCPH99Z"
downloaded_at: "2026-05-12"
source: "Amazon Ads Support Center"
---

# Sponsored Brands bids by placement and audiences

Bid adjustments let you automatically increase or decrease bids when ads appear in specific placements or target certain audience segments.

You can adjust bids by placement or audience to be more strategic with budget by increasing the bid when the ad is eligible to appear in certain locations or to certain groups of advertisers.

You can do this when creating a campaign on the **Campaign Bid Adjustments** card, or once a campaign is live in campaign manager.

## Bids by placement

**Tip:** Adjusting bids by placement is best for advertisers who have observed that certain placements have led to conversions, sales, or other desired activities in the past. You can view placement metrics for existing campaigns within campaign manager on the bid adjustment tab.

Enter a percentage amount to increase your bid when your ad is eligible to compete for one or all of these placements:

- Top of search (first page): the top row of first-page search results.
- Rest of search: the middle or bottom of shopping results and the second page of shopping results and beyond.

To adjust bids by placement within campaign manager, click the **Placements** tab on the **Campaign Bid Adjustments** card and enter the desired percent in the box next to **Placements other than top of search**.

Example:

If you bid `$1` for a keyword and set a `50%` bid adjustment decrease, then your bid for placements other than top of search may decrease to `$0.50`.

Formula:

`$1 original bid - ($1 x .50 rest of search bid adjustment)`

## Bids by audience

**Note:** You can adjust bids for only one audience per campaign. You can choose either an Amazon-built audience or an Amazon Marketing Cloud audience, but not both.

You can adjust bids by audience to help drive discovery and sales for specific groups of shoppers. You choose an audience and a percentage to increase bids by when a user from that audience searches for products.

There are two types of audiences:

- **Amazon built audiences:** prebuilt audience segments informed by first-party shopping and streaming signals, including in-market, lifestyle, interests, and life events. These are available to all sponsored ads advertisers.
- **Amazon Marketing Cloud custom audiences:** AMC users can apply bid adjustments to AMC custom audiences in Sponsored Product campaigns. Use engagement signals such as impressions, clicks, and conversions across Amazon Ads media investments to capture high-intent audiences during the shopping journey.

Example:

If you bid `$2` for a keyword and set a `50%` increase for a custom audience, your bid adjusts to `$3`.

Formula:

`$2 original bid + ($2 x .50 custom audience adjustment)`

**Tip:** Audiences created in AMC are available in the sponsored ads account during campaign creation and campaign management. Performance reports are available in Ads Console and through Amazon Marketing Cloud reporting features.

## Combine bids by placement with bids by audience

You can combine bid adjustments by placement and audience for the same campaign.

You can enter up to a `900%` increase, or `10x`, to the base bid. If both placement and audience bid percentages are applied and both conditions are met, these bid adjustments are applied together to determine the final bid.

Example:

You bid `$1` for a keyword and set:

- `50%` bid adjustment increase for placements other than top of search
- `100%` bid adjustment for a custom audience

The bid for placements other than top of search for that audience may increase to `$3`.

Calculation:

- a: `$1` original bid + `50%` rest of search adjustment = `$1.50`
- b: `$1.50` + `100%` custom audience adjustment = `$3.00`

## Combine cost controls with bids by placement or audience

**Note:** Because cost control is a target average cost and not a max cost, average CPC may be higher than the amount entered. You can only use cost control if the campaign goal is Drive page visits.

You can combine bid adjustments with cost controls to specify where to adjust bids and for whom while still controlling campaign cost.

Cost control automatically adjusts bids based on the specified cost per click, which can be chosen on the Cost control card.

When cost control is on and bids by placement or audience are adjusted, expected target CPC adjusts accordingly. This means the highest possible CPC will exceed the target cost-control CPC.

## Related topics

- Understand bid adjustments in Sponsored ads
- Understand bid adjustments on Amazon DSP
- Adjust Sponsored Products bids
- Apply bid adjustments on Amazon DSP
