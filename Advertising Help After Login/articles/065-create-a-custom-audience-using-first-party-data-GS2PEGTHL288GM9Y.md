---
title: "Create a custom audience using first-party data"
source_url: "https://advertising.amazon.com/help/GS2PEGTHL288GM9Y"
library: "Amazon Ads Support Center"
downloaded_at: "2026-10-07"
status: "captured"
---

# Create a custom audience using first-party data

Use Amazon first-party shopping and streaming signals to create custom audience segments.

Updated on Jul 22, 2026

**Good to know**

- Audiences can take up to 24 hours to process. A "Failed" status usually means the audience is too small or policy-restricted. Add more values or extend the lookback window.
- Twitch audiences don't allow third-party tags. Adding third-party tags to ad groups with Twitch audiences can pause your ads, including on other ad groups using the same ad.
- Retail audiences are limited to brands tied to your account. Private label ASINs, policy-restricted products, and brands or Stores with fewer than 2,000 unique visitors can't be included.

You can create several types of audiences based on Amazon 1st party data. Each audience type offers unique attributes and lookback windows to help you reach customers with relevant entertainment interests. Amazon DSP organizes them into 3 main categories: media, retail, and remarketing audiences.

| Category | Audience type | Audience definition | Lookback window |
| --- | --- | --- | --- |
| Media | Prime Video | Reach audiences who have streamed the specified movies, TV series, genres, or titles with the specified actors or directors. | 1-180 days |
| IMDb | Reach audiences who have visited the specified people or title pages on IMDb.com. | 1-365 days |
| Twitch | Reach audiences who have streamed the specified categories, games, streamers, or genres on Twitch.tv. | 1-30 days |
| Kindle Books | Reach audiences who have opened any of the specified Kindle book titles. | 1-365 days |
| Retail | Amazon Stores | Customers who have viewed the specified Amazon Stores, or Amazon Stores pages. | 1-90 days |
| Whole Foods Market | Customers who purchased the specified ASINs from a Whole Foods Market store within a defined time frame. | 1-365 days |
| Product | Shoppers who engage with products on Amazon | variable |
| Brand | People who engage with brands on Amazon | variable |
| Remarketing | Streaming TV campaigns | Reach audiences who have been exposed to selected Streaming TV and Prime Video orders or line items that you have run. | unadjustable |
| Audio ads | Reach audiences who have been exposed to selected audio ads orders or line items that you have run. | unadjustable |
| Twitch ads | Reach audiences who have been exposed to selected Twitch.tv ads orders or line items that you have run. | unadjustable |
| Display and Online Video (OLV) ads | Reach audiences who have been exposed to selected orders or line items that you have run on other supply sources. | unadjustable |
| Online Video (OLV) ads with completion rate | Reach audiences who have been watched a selected percentage of selected OLV orders or line items that you have run. Example: only engage customers who've watched 75% of the ad. | unadjustable |

## How to create an audience

Create an audience:

1. In the navigation side menu, click **Campaigns**
2. Click **Audiences** in the side navigation.
3. Click **New audience**.
4. Click **Next** on the tile for the audience type you want to create (media, retail, or remarketing).
5. Follow the steps below according to your chosen audience type.

**1. Enter Audience settings**

- **Name**: choose a descriptive name that identifies the audience purpose
- **Description**: viewable to other Amazon DSP users in your entity

**2. Select attributes**

- Select a lookback window.
- Select an attribute from the drop-down.
- Click **choose**.
- Search for the value you want to add. You can combine up to 3 different attributes (genre, games, and channels) in 1 audience, and select up to 10 values per attribute. Both attributes and their values are connected via OR statements. For example: **Prime Video**: If building an audience based on 2 movies and 3 TV series, viewers must stream at least 1 of the movies OR 1 of the TV series to be included. **Twitch**: If building an audience based on 2 games and 3 channels, viewers must stream at least 1 of the games OR 1 of the channels to be included **IMDb**: If building an audience based on 2 actors and 3 movies, shoppers must visit 1 of the actor pages OR 1 of the movie pages to be included.
- Click **add** next to each 1 you want to include (up to 10).
- Click **D1**.
- To add another attribute, click **Add attribute** and follow steps 3-6 again.
- Click **Save** when you're finished adding attributes.

**3. Twitch attribute types**

- **Streamer**: build an audience based on user views of a specific Twitch streamer or event. Examples of streamers include pokimane and TimTheTatman.
- **Category/Game**: build an audience based on user views of a specific game or activity. Examples of games include Fortnite and League of Legends while examples of activities include Just Chatting and Travel and Outdoors.
- **Genre**: build audiences based on user views of a type of game. Examples of game genres include Real-Time Strategy, Sports, and Role-Playing. Learn about Twitch game genres.

In the Twitch directory you can view popular:

- **streamers**: select Live Channels and sort by Viewers (High to Low).
- **categories/games**: select Categories and sort by Viewers (High to Low).

Twitch audiences don't permit third-party tagging. If you include third-party tags on ad lines with these audiences, and the same ad they tagged is also used on other ad groups, their ad will be paused.

## Audience Status

Within 24 hours, audiences will have a status of either Active or Failed listed in the Campaign Manager. Only audiences with an Active status can be applied to Amazon Ads campaigns. If your audience fails, it may violate our policies or be too small. Add additional values or extend the lookback window to increase the size.

- **Pending**: Collecting data or waiting for review
- **Processing**: Audience is being built. Will become available later.
- **Active**: Ready to use in line item settings page.
- **Failed**: Cannot be built per audience size or policy violation.
