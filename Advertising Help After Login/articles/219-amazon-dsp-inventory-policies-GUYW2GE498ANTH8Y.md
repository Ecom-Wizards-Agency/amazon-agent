---
title: "Amazon DSP inventory policies"
source_url: "https://advertising.amazon.com/help/GUYW2GE498ANTH8Y"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon DSP inventory policies

Learn about Amazon DSP policies for all inventory, including our transparency, content, and quality standards.

Updated on Oct 21, 2025

## Introduction and overview

Amazon DSP inventory policies outline the standards and requirements for all inventory available through Amazon DSP. The policies help ensure a high-quality, high-performance, transparent, and brand-safe marketplace for advertisers while providing clear guidelines for sellers. Inventory that doesn't meet these standards and requirements won't be eligible for demand.

**Scope and authority**

The policies apply to all inventory made available through Amazon DSP, including, but not limited to Display, Video, Streaming TV (STV), and Audio inventory.

Amazon DSP reserves the right to interpret the policies and make determinations about inventory compliance. We may, at our sole discretion, choose to buy or not buy any inventory based on our interpretation of the policies and our assessment of inventory quality, suitability, and performance.

The policies will be updated to meet the evolving needs of our customers and to create efficiencies on Amazon DSP.

**Definitions**

For the purposes of the policies, we define key terms as follows:

1. **Inventory:** Any digital advertising opportunity on a property that's made available for purchase.
2. **Properties:** Digital assets such as websites and apps monetized through advertising.
3. **Seller:** Any entity making inventory available to Amazon DSP, including publishers, SSPs, intermediaries, and aggregators.
4. **Brand-safe:** Content or contexts that are appropriate and non-harmful for advertisers to place their ads in, safeguarding their brand reputation.
5. **Invalid traffic (IVT):** Any ad traffic (including bid requests and measurement beacons) that is either fraudulent, involuntary, non-human, duplicate, or otherwise illegitimate.
6. **Made for Advertising (MFA):** Inventory designed primarily to host advertising rather than provide value to users.

## Non-performant inventory

We require minimum consistent performance thresholds, including but not limited to reach, impressions, or number of monthly active users. Inventory from properties that don’t consistently meet these thresholds will be removed from eligibility for demand.

For some types of inventory, including but not limited to, those from properties predominantly dedicated to user-generated content, we may set higher thresholds for performance requirements.

## Inventory transparency

Sellers are required to provide complete and accurate information about their inventory so Amazon DSP can make informed eligibility and bidding decisions on behalf of our advertising customers and maintain marketplace integrity. Amazon DSP aligns with IAB Tech Lab standards for inventory transparency; specifically, ads.txt, app-ads.txt, sellers.json, and SupplyChain Object. In addition, certain attributes within bid requests and in measurement beacons are required as outlined below.

**ads.txt and app-ads.txt requirements**

All inventory must have a corresponding published and crawlable ads.txt or app-ads.txt file, per the IAB Tech Lab specification, that:

1. has the right entry corresponding to the publisher.id in bid requests;
2. specifies OWNERDOMAIN for the business entity that owns the domain/app being monetized;
3. uses MANAGERDOMAIN only for primary/exclusive monetization partners; and
4. employs INVENTORYPARTNERDOMAIN for explicitly authorized monetization entities, with a corresponding ads.txt or app-ads.txt hosted on the inventory partner’s domain.

**Sellers.json requirements**

All SSPs, intermediaries, and aggregators must have a published and crawlable sellers.json file, per the IAB Tech Lab Sellers.json specification, that:

1. is accessible via HTTPS;
2. contains non-confidential seller information;
3. lists accurate seller IDs, names, seller types, and business domains; and
4. accurately represents seller type (PUBLISHER, INTERMEDIARY, or BOTH).

## Content standards

Amazon DSP seeks content that's brand-safe, high-quality, and original. Amazon DSP requires sellers to comply with content standards and to ensure that their content is accessible for automated or human review. The types of content that are ineligible are listed on our Content Adjacency Policies for Amazon DSP and are periodically updated.

## Inventory quality

**Invalid Traffic (IVT)**

Any fraudulent, involuntary, non-human, duplicate, or otherwise illegitimate traffic is considered IVT and is ineligible for demand. Amazon DSP removes IVT from reported metrics and invoices to preserve metric integrity and to prevent wasted ad spend. This includes impressions, clicks, views, and other metrics. For more information on IVT, refer to the Media Rating Council guidelines on IVT.

**Made for Advertising (MFA)**

High-quality inventory provides value to advertisers and represents content that provides value to users as well. Such content doesn’t exist for the primary purpose of generating advertising revenue. Tactics prioritizing advertising revenue won’t be eligible for demand. Such tactics include, but aren’t limited to, having excessive ad density, auto-refreshing slideshows, high degree of paid traffic sources, varying ad layouts or ad load based on user journeys, among others.

**Injected ad placements**

Ad placements in pop-up/pop-under windows or injected into content not owned or authorized by the seller are ineligible for demand. Examples of these are ad placements injected by browser plugins, internet service providers (ISPs), VPNs, proxies, or other software on the user’s device or network without the explicit consent of the seller.

**Incentivized ads**

Inventory that involves compensating the viewer of an ad either in cash or cash-equivalent instruments (for example, gift cards) is ineligible for demand.

**Auto-refreshing ad placements**

Ad placements that refresh faster than once every 30 seconds or refreshed when not in-view are ineligible for demand.

**Bid caching**

Amazon DSP bids for ad opportunities must not be reused across auctions for distinct ad opportunities. An Amazon DSP bid must only be used for the specific auction for which it was submitted. Bid caching may not be employed except for the benefit of user experience (for example, pre-auctioning video ads to continue a seamless stream). Cached bids must be for the same type of ad unit, within the same page view or stream, and for the same user or viewer.

**Auto-play video ad placements**

Out-stream ad placements that automatically play video ads (without user interaction) with sound turned on are ineligible for demand.

## Legal and regulatory compliance

Ensuring adherence to laws, regulations, and privacy standards is a top priority for Amazon DSP. Sellers must ensure that they have all rights necessary to make their inventory available on Amazon DSP, and that they and their inventory comply with all applicable laws, rules, and regulations. Sellers must post privacy policies that comply with applicable laws and inform end users about any information relating to end users that they’ll provide or is otherwise accessible to Amazon concerning the seller making their inventory available to Amazon DSP.

## Bid request attribute requirements

The following bid request attributes/values (or the equivalent for OpenRTB 2.6 or non-OpenRTB integrations) should be relayed accurately:

| Object | Attribute | Note |
| --- | --- | --- |
| Bid Request | id |  |
| imp |  |
| device |  |
| tmax |  |
| bcat | If a value is present, must use IAB Content Taxonomy 1.0. |
| cur | Must contain USD in the array. |
| Imp | id |  |
| secure | 0 = secure assets aren’t required; 1 = secure assets and markup are required. |
| bidfloorcur | Must be USD when bidfloor is passed. |
| rwdd | Indicate whether the user receives a reward for viewing the ad, where 0/null = no, 1 = yes |
| banner | Field is required if the impression is offered as a Banner ad opportunity. |
| video | Field is required if the impression is offered as a Video ad opportunity. |
| audio | Field is required if the impression is offered as an Audio ad opportunity. |
| native | Field is required if this impression is offered as a Native ad opportunity. |
| ext.skadn.skadnetlist.addl | If a value is present, it must be a comma-separated list of string SKAdNetwork IDs, expressed as lowercase strings, not included in the IAB Tech Lab shared list. The intention of the addl is to be the permanent home for raw SKAdNetwork IDs, migrating away from BidRequest.imp.ext.skadn.skadnetids. Recommended that this list doesn't exceed 10. |
| Metric | type | If a value is present, a type of metric being presented using exchange curated string names, which should be published to bidders. |
| value | If a value is present, the number must represent the value of the metric. Probabilities must be in the range 0.0 – 1.0. |
| Banner | h |  |
| w |  |
| api | The value must be 7 to support viewability measurement for apps. |
| Video | mimes | A list of supported video content MIME types. Popular MIME types supported by HTML5 players include video/mp4, video/webm, and video/ogg. For VPAID support, make sure to specify application/javascript. |
| startdelay |  |
| playbackmethod |  |
| plcmt | Required for more granular targeting of in-stream/out-stream placements. |
| api | The value must be 2 or 7 for web and 7 for app to support viewability measurement. |
| skip | Required to identify skippable vs non-skippable video placements. |
| Native | api | The value must be 7 to support viewability measurement. |
| Deal | id |  |
| Site | domain |  |
| page | Must supply the full URL (untruncated). |
| ref | Must supply the full URL (untruncated). |
| App | id |  |
| bundle | Must be the bundle ID registered with an app store (for example, Android, Apple, Fire TV). For OTT/CTV, follow the IAB Tech Lab’s OTT/CTV Store Assigned App Identification Guidelines |
| storeurl |  |
| Content | contentrating |  |
| livestream | If content is live, it must pass a value of "1." |
| Device | os |  |
| ip | This field is required if the bid request doesn’t contain the ipv6 field. |
| ipv6 |  |
| ua |  |
| devicetype |  |
| User | ext.pdt |  |
| id | Follow the IAB Tech Lab's ID Provenance guidelines for transparency around ID bridging. |
| buyeruid |
| EID | inserter | Follow the IAB Tech Lab's ID Provenance guidelines for transparency around ID bridging. |
| source |
| matcher |
| mm |
| uids |
| UID | id | Follow the IAB Tech Lab's ID Provenance guidelines for transparency around ID bridging. |
| atype |
| SupplyChain | complete | Must be 1. |
| nodes | The first node must have the seller type of PUBLISHER in the corresponding sellers.json file. |
| SupplyChainNode | asi | All Advertising System Identifiers (asi) in the schain must have accessible sellers.json files. |
| sid | Seller IDs (sid) within schain nodes must appear in corresponding sellers.json files. |
| domain |  |
| hp |  |
| Refresh | refsettings |  |
| count |  |
| RefSettings | reftype |  |

## Measurement attribute requirements

For measurement beacons, the following HTTP headers should be relayed accurately for effective IVT filtration and other purposes:

| Field | Note |
| --- | --- |
| X-Forwarded-For X-Device-IP | When the measurement beacon is proxied by a server (as it may be in case of server-side ad insertion), the X-Forwarded-For header or the X-Device-IP should be present and should represent the IP address of the client device on which the ad has been delivered. |
| User-Agent X-Device-User-Agent | The User-Agent header should reflect the user agent of the client (browser, app, device) on which the ad has been delivered. In case the measurement beacon is proxied by a server, the X-Device-User-Agent should be used to represent the user agent of the client. |
| Referer | In case of web inventory, this should be populated with the URL of the page on which the user was prior to landing on the page from where the ad opportunity was generated. |
