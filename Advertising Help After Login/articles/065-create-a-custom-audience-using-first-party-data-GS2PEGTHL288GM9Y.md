---
title: "Create a custom audience using first-party data"
source_url: "https://advertising.amazon.com/help/GS2PEGTHL288GM9Y"
library: "Amazon Ads Support Center"
downloaded_at: "2026-05-12"
status: "captured"
---

# Create a custom audience using first-party data

Use Amazon first-party shopping and streaming signals to create custom audience segments.

Amazon DSP organizes first-party audience types into three main categories: media, retail, and remarketing audiences.

## Audience definitions and lookback windows

| Category | Audience type | Audience definition | Lookback window |
| --- | --- | --- | --- |
| Media | Prime Video | Audiences who streamed specified movies, TV series, genres, or titles with specified actors or directors. | 1-180 days |
| Media | IMDb | Audiences who visited specified people or title pages on IMDb.com. | 1-365 days |
| Media | Twitch | Audiences who streamed specified categories, games, streamers, or genres on Twitch.tv. | 1-30 days |
| Media | Kindle Books | Audiences who opened specified Kindle book titles. | 1-365 days |
| Retail | Amazon Stores | Customers who viewed specified Amazon Stores or Store pages. | 1-90 days |
| Retail | Whole Foods Market | Customers who purchased specified ASINs from a Whole Foods Market store. | 1-365 days |
| Retail | Product | Shoppers who engage with products on Amazon. | Variable |
| Retail | Brand | People who engage with brands on Amazon. | Variable |
| Remarketing | Streaming TV campaigns | Audiences exposed to selected Streaming TV and Prime Video orders or line items. | Unadjustable |
| Remarketing | Audio ads | Audiences exposed to selected audio ads orders or line items. | Unadjustable |
| Remarketing | Twitch ads | Audiences exposed to selected Twitch.tv ads orders or line items. | Unadjustable |
| Remarketing | Display and Online Video ads | Audiences exposed to selected orders or line items on other supply sources. | Unadjustable |
| Remarketing | OLV ads with completion rate | Audiences who watched a selected percentage of selected OLV orders or line items. | Unadjustable |

## How to create an audience

1. In the navigation side menu, click **Campaigns**.
2. Click **Audiences** in the side navigation.
3. Click **New audience**.
4. Click **Next** on the tile for the audience type: media, retail, or remarketing.
5. Follow the flow for the selected audience type.

## Media audience setup

1. Enter audience settings:
   - **Name:** descriptive name identifying purpose.
   - **Description:** visible to other Amazon DSP users in the entity.
2. Select attributes:
   - Select a lookback window.
   - Select an attribute from the dropdown.
   - Click **choose**.
   - Search for the value.
   - Click **add** next to values to include, up to 10.
   - Click **Done**.
   - Add another attribute if needed.
   - Click **Save**.

Up to three different attributes can be combined in one audience, and up to 10 values per attribute can be selected. Attributes and values are connected with OR statements.

## Twitch attribute types

- **Streamer:** audience based on views of a specific Twitch streamer or event.
- **Category/Game:** audience based on views of a game or activity.
- **Genre:** audience based on views of a game type.

In the [Twitch directory](https://www.twitch.tv/directory), popular streamers and categories/games can be viewed by sorting by viewers.

Twitch audiences do not permit third-party tagging. If third-party tags are included on ad lines with these audiences, and the same ad is used on other ad groups, the ad will be paused.

## Audience status

Within 24 hours, audiences show a status in Campaign manager. Only Active audiences can be applied to Amazon Ads campaigns.

| Status | Meaning |
| --- | --- |
| Pending | Collecting data or waiting for review. |
| Processing | Audience is being built and will become available later. |
| Active | Ready to use in the line item settings page. |
| Failed | Cannot be built because of audience size or policy violation. |

If an audience fails, it may violate policy or be too small. Add values or extend the lookback window to increase size.

## Related topics

- [Understand audiences on Amazon](https://advertising.amazon.com/help/GKSQZKMHW95GJDB7)
- [Amazon Marketing Cloud](https://advertising.amazon.com/help/G9H78BXVT5NCEGUM)
- [Create a custom audience using third-party data](https://advertising.amazon.com/help/GWU447PKLV5MHGYF)
