---
title: "Create an app advertising campaign"
source_url: "https://advertising.amazon.com/help/GGVVDRH786R6R58Q"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Create an app advertising campaign

Learn how to configure app advertising campaigns on Amazon DSP for driving app installs and in-app actions.

Updated on Sep 4, 2026

App ads are available for users with an Amazon DSP account that also have a mobile app available on Android or Fire OS platforms. You must set up integration with a supported MMP to create an App Ad campaign.

## What is app advertising?

The App Ads program allows non-endemic advertisers (advertisers not selling on Amazon) with Android and Fire OS mobile apps to drive app installs, in-app actions, and revenue through programmatic advertising.

Learn more about app advertising.

## Create a campaign

Use the publisher-specific campaign setup instructions in the table below. You can create campaigns targeting 1 or multiple supply sources in a single campaign, but follow any publisher-specific instructions, which may include requirements for campaign, ad group, and ad asset specifications. In addition to the publisher-specific instructions, always **configure app measurement** for your campaign.

| **Reach audiences on** | **Where you can measure app conversions** | **Campaign setup instructions** |
| --- | --- | --- |
| **Publisher** | **Platform** | **Media** |
| Fire TV | Connected TV | Display and video on Feature Rotator, Inline banner | Fire TV, iOS, Android | View |
| Fire tablet | Tablet | Display and video on wakescreen | Fire tablet | View |
| Twitch | Android, iOS, Streaming TV, Web | Display and video | iOS, Android | View |
| Prime Video | Streaming TV, iOS, Android, Web | Streaming TV video ads (pre-roll, mid-roll) within movies, shows, and live sports | View |
| Amazon Live Events | Streaming TV | Amazon Live Events include streaming supply across live sports and other events - available inventory will vary by marketplace and event exclusivity. | View |
| Amazon Shopping | iOS, Android, Web | Display banners on mobile app (homepage, search results, product detail pages) | View |
| Amazon Music Free, Twitch Audio, and podcasts (Amazon Music, Wondery, ART19) and third-party (iHeart, Pandora, Audacy) | Desktop, mobile, tablet, connected TV, and smart speakers (Echo, Alexa-enabled devices, and Fire TV) | Standard audio and podcasts | View |
| Alexa Echo Show | Echo Show devices support Display (REC, ABC) and video ads on the Alexa Home Screen | Display and video on Alexa Home Screen | View |
| Amazon Digital Signage | Physical in-store signage | Whole Foods Market and Fresh digital displays | View |
| Goodreads | iOS, Android, Web | Display (standard banners, native ads on newsfeed) | View |
| IMDb | iOS, Android, Web | Display and video (in-stream and out-stream OLV) | View |
| Third-party | Android, iOS, Streaming TV | Display and video (in-stream and out-stream OLV) across third-party web and app inventory | View |

## Configure app measurement

In addition to the standard campaign setup, configure every campaign to measure app conversions. The below measurement settings must be applied to the campaign **prior** to launch, as there are no backfill or restatement processes.

1. During campaign creation, in the campaign settings page, scroll to the **Conversion tracking** section.
2. Under **Off-Amazon conversions,**click **Add conversions**.
3. Add the events you want to measure and optimize. You can identify MMP events by looking at the **Source** field. The **Source** field also distinguishes app events by platform (iOS, Android, Fire TV, Fire tablet). Associate all of your app’s conversion events with every campaign that measures the app — including Install (Mobile app first start), App Open, and Purchase (Off-Amazon purchases), plus any other events you track. Add them under **Off-Amazon conversions**, then use the **Optimize** setting to select only the events that match your campaign's goal. Associating an event enables measurement; the **Optimize** setting controls what the campaign bids toward — they are independent. At minimum, always associate **Install** and **App Open**. Associating your full event set gives Amazon’s optimization models the most complete signal and ensures your reporting reflects the full app activity your campaigns drove, not only the event you optimized toward.
4. To configure SKAdNetwork measurement, unde **SKAdNetwork**, select the iOS app you want to measure.

**Note**: If you don't see the apps or app events you want to measure, make sure that you completed the steps to set up an integration with a supported MMP.

## Brand+ and Performance+ campaigns

To measure app conversions on Brand+ and Performance+ campaigns, follow the steps in Create a campaign with Brand+ or Performance+. Then complete the **Configure app measurement** steps listed above as an additional step.

## Best practices for app conversion campaigns

For campaigns with upper/mid-funnel objectives, or with app conversion objectives, make srue tp **configure app measurement**. Associate your full set of app conversion events on these campaigns (the same events you use on your conversion campaigns). Upper- and mid-funnel campaigns (Reach, CPC, Brand+) drive app activity too, and associating all events ensures that activity is measured and credited. You don't need to optimize toward a conversion on these campaigns; instead, associate them for measurement. Follow these best practices:
