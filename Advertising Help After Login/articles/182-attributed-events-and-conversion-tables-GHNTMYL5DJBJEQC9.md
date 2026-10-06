---
title: "Attributed events and conversion tables"
source_url: "https://advertising.amazon.com/help/GHNTMYL5DJBJEQC9"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Attributed events and conversion tables

Learn about Amazon Marketing Cloud (AMC) attributed events and conversions tables; how they’re structured, what types of records they contain, and examples for how you can use them to measure your ad performance.

Updated on Jul 10, 2025

## Attributed events tables

**amazon_attributed_events_by_conversion_time** and **amazon_attributed_events_by_traffic_time**

The amazon_attributed_events_* tables include 1 record per conversion that can be attributed to Amazon DSP or sponsored ads campaign traffic. Traffic events are impressions and clicks. Conversions include on-Amazon events such as purchases and detail page views, as well as off-site events measured via Amazon DSP tagging solutions such as the Conversions API or Amazon AdTag. Each conversion event in the table is attributed to its corresponding traffic event. Each conversion appears once within each table, as attribution logic only allows a conversion to be attributed to 1 traffic event.

While these amazon_attributed_events_* tables include the same events, metrics, and dimensions, they differ with respect to how your query’s time window is applied.

- When using the amazon_attributed_events_by_conversion_time table, the time window applied to your query applies to the time of the conversion. The conversion events all happened within the time window that the query is run over. Alternatively, the traffic events to which the conversions were attributed to may happen up to 14 days before the time period for the query.
- The amazon_attributed_events_by_traffic_time table has the opposite behavior. The time window applied to your query applies to the time of the traffic events (that is, impression and click events), while the attributed conversions may occur up to 14 days after the traffic event.

Modeled conversion events are also available through the above tables. Reporting grains below the ad line level are available for modeled conversion events, and instead reported as NULL values. To exclude modeled conversions from insights, join attributed conversion data sets to user identifiers, traffic identifiers, or any dimension below the ad line level.

**Note:**While nonaddressable audiences appear as rows in tables where “user_id” is NULL, note that all rows with “user_id” as NULL aren’t modeled.

**Comparing AMC conversion metrics to other analytics tools**

In the ads console, Sponsored Products and Sponsored Display report metrics by traffic time, while Sponsored Brands and Amazon DSP report metrics by conversion time. While AMC supports either way of reporting conversions, be sure to leverage the appropriate table if you’re looking to compare to metrics in the ads console.

Metric names also differ between AMC and sponsored ads reporting tools. Examples of sponsored ads metrics and their AMC counterparts can be found in the table below.

| Sponsored ads metric | Sponsored ads metric name | AMC column name |
| --- | --- | --- |
| **attributedConversions14d** | 14 Day Total Orders (#) | total_purchases |
| **attributedConversions14dSameSKU** | 14 Day Advertised ASIN Orders (#) | purchases |
| **attributedUnitsOrdered14d** | 14 Day Total Units (#) | total_units_sold |
| **attributedUnitsOrdered14dSameSKU** | 14 Day Advertised ASIN Units (#) | units_sold |
| **attributedUnitsOrdered14dOtherSKU** | 14 Day Brand Halo ASIN Units (#) | brand_halo_units_sold |
| **attributedSales14d** | 14 Day Total Sales | total_product_sales |
| **attributedSales14dSameSKU** | 14 Day Advertised ASIN Sales | product_sales |
| **attributedSales14dOtherSKU** | 14 Day Brand Halo ASIN Sales | brand_halo_product_sales |

## Custom attribution tables

With the conversions and conversions_with_relevance tables, you can customize how you attribute conversions to your Amazon Ads campaigns. The amazon_attributed_events_* tables pre-attribute according to the methodology detailed in the table below, whereas you can use the conversions and conversions_with_relevance tables to choose how you want to assign or split credit across different touch points.

| Capability | amazon_attributed_events_* tables | conversions and conversions_with_relevance |
| --- | --- | --- |
| Lookback window | Customizable up to 14 days. | Customizable up to 28 days (ensure you have appropriate time logic applied to the conversion and impression events via EXTEND_TIME_WINDOW function). |
| Viewability requirements | Attributed impression must be viewable (as measured by Amazon to MRC standard). | Customizable – AMC user determines whether viewability logic should be leveraged in assignment of conversion credit. |
| Attribution logic | Last touch model prioritizes product relevance, then favors last click over last view. | Customizable – AMC user can define how to give credit (for example, first touch, last touch, or multitouch). |
| Conversion environment | Includes both on and off-Amazon conversion events. | Includes both on and off-Amazon conversion events. |
| ASINs included | Both promoted ASINs and brand halo ASINs. | Both promoted ASINs and brand halo ASINs. |

**conversions**

This table contains AMC conversion events. Ad-attributed conversions for ASINs tracked to an Amazon DSP or sponsored ads campaigns and pixel conversions are included. Conversions are ad-attributed if a user was served a traffic event within the 28-day period prior to the conversion event.

**conversions_with_relevance**

AMC’s custom attribution function allows advertisers to define their preferred attribution model, such as first touch, last touch, equal weight, or custom weight. It also allows advertisers to use a lookback window of up to 28 days when performing attribution analysis in AMC.

Custom attribution is supported for both ASIN and pixel conversions through the conversions and conversions_with_relevance tables. AMC also provides the following instructional queries, which can assist you with implementing different attribution methodologies:

- Custom Attribution - First Touch
- Custom Attribution - Last Touch
- Custom Attribution - Linear
- Custom Attribution - Position Based

**Note:** conversions and conversions_with_relevance tables contain signals related to ad-attributed Amazon conversions and pixel conversions only. Non-ad attributed Amazon conversions aren’t published within these 2 conversions tables.

**Tip:**We recommend using the Amazon Marketing Cloud data sources file to understand field information and definitions.
