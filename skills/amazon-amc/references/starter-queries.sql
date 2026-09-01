-- Adapt only after confirming these tables and columns with AMC get_data_sources.
-- Measurement-query examples use AdLabs runtime time-window parameters.

-- Sponsored Ads traffic by campaign and ad product.
WITH traffic AS (
    SELECT
        ad_product_type,
        campaign,
        SUM(impressions) AS impressions,
        SUM(clicks) AS clicks,
        SUM(spend) / 100000000.0 AS spend_currency
    FROM sponsored_ads_traffic
    WHERE event_date_utc BETWEEN BUILT_IN_PARAMETER('TIME_WINDOW_START')
                             AND BUILT_IN_PARAMETER('TIME_WINDOW_END')
    GROUP BY 1, 2
),
totals AS (
    SELECT
        SUM(spend_currency) AS total_spend_currency
    FROM traffic
)
SELECT
    traffic.ad_product_type,
    traffic.campaign,
    traffic.impressions,
    traffic.clicks,
    traffic.spend_currency,
    1.0 * traffic.clicks / NULLIF(traffic.impressions, 0) AS ctr,
    1.0 * traffic.spend_currency / NULLIF(traffic.clicks, 0) AS cpc_currency,
    1.0 * traffic.spend_currency / NULLIF(totals.total_spend_currency, 0) AS spend_share
FROM traffic
CROSS JOIN totals;

-- Attributed purchases and new-to-brand mix by ad product.
WITH conversions AS (
    SELECT
        ad_product_type,
        COUNT(DISTINCT user_id) AS customers,
        SUM(purchases) AS purchases,
        SUM(total_product_sales) AS attributed_sales,
        SUM(new_to_brand_purchases) AS ntb_purchases,
        SUM(new_to_brand_total_product_sales) AS ntb_sales
    FROM amazon_attributed_events_by_conversion_time
    WHERE conversion_event_date_utc BETWEEN BUILT_IN_PARAMETER('TIME_WINDOW_START')
                                        AND BUILT_IN_PARAMETER('TIME_WINDOW_END')
      AND purchases > 0
    GROUP BY 1
)
SELECT
    ad_product_type,
    customers,
    purchases,
    attributed_sales,
    ntb_purchases,
    ntb_sales,
    1.0 * attributed_sales / NULLIF(purchases, 0) AS average_order_value,
    1.0 * ntb_purchases / NULLIF(purchases, 0) AS ntb_purchase_share,
    1.0 * ntb_sales / NULLIF(attributed_sales, 0) AS ntb_sales_share
FROM conversions;
