---
title: "Aggregation thresholds"
source_url: "https://advertising.amazon.com/help/G6ZYAPTTTE54UQPP"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Aggregation thresholds

Amazon Marketing Cloud (AMC) has aggregation thresholds in place that are apparent when you query your instance. This ensures that all AMC analyses are sufficiently aggregated.

Updated on Jul 10, 2025

Aggregation thresholds prevent AMC users from generating analyses at too fine a grain. The aggregation threshold of a column determines the restrictions that are enforced when that column is used in a query.

Before reviewing the various aggregation threshold levels, we’ll highlight an example of the column user_id, which has an aggregation threshold of VERY_HIGH and is used in multiple AMC queries. In practice, an aggregation threshold level of VERY_HIGH means that you’ll never be able to select the column in the final SELECT statement of a SQL query. The reason for this being that this statement would expose the values of the column in the final output. In this example, selecting the actual user_id in the final SELECT statement would mean including a user_id value alongside associated information, thus violating our aggregation thresholds. Even with these restrictions in place, there are many permitted uses of user_id that don’t expose the actual user_id value. Below are a few examples of insights that are possible to derive using the column user_id:

- First, many advertisers use the user_id to count the number of unique users reached by campaign.
- Second, the optimal ad frequency insight, which we reviewed in the previous section, uses the user_id.
- Third, other advertisers leverage the user_id in queries to measure the customer journey across various ad products, such as Display, OTT or Display, and Sponsored Products.

## Column classifications

Each column is classified into 1 of the categories below based on the combination of the aggregation threshold and the filtering restrictions. All categories can be found in the Amazon Marketing Cloud data sources file under the column **aggregation threshold**. The classifications are also in the schema explorer.

- **NONE** - Values from the column can be included in the output of workflows without any special restrictions being enforced. This classification is generally used for metric columns, such as impressions and clicks. The aggregation threshold is 1 and there are no filtering restrictions.
- **LOW** - Values from this column can only be included in the output of workflows if the row contains at least 2 distinct users. This classification is generally used for columns that contain dimensions that describe campaigns such as campaign_id and ad_id. The aggregation threshold is 2 and there are no filtering restrictions.
- **MEDIUM** - Values from the column can only be included in the output of workflows if the row contains at least 100 distinct users. Examples: bid_price and winning_bid_cost. The aggregation threshold is 100 and there are no filtering restrictions.
- **HIGH** - Values from the column can only be included in the output of workflows if the row contains at least 100 distinct users. The aggregation threshold is 100 and there are filtering restrictions. Filters using literal (static) values can’t be applied to the column. For example, postal_code falls into this category and this filter isn’t allowed: WHERE postal_code in (10001, 10011).
- **VERY_HIGH** - Values from the column can never be included in workflow output. They may be used for intermediate purposes in workflows as long as they’re dropped or aggregated with COUNT or COUNT DISTINCT. There’s no aggregation threshold that will reveal columns with the classification VERY_HIGH because doing so would expose events from a single user. There are also filter restrictions. Filters using literal (static) values can’t be applied to the column. For example, user_id falls into this category and this filter isn’t allowed: WHERE user_id in (111,222).
- **INTERNAL**- Values from the column can never be included in workflow output. However, they may be used for intermediate purposes in workflows as long as they’re dropped or aggregated with COUNT or COUNT DISTINCT. Examples for this type of column include advertiser_id_internal and campaign_id_internal.

If a query compares literal values to HIGH or VERY_HIGH sensitivity columns (or those derived from them), the query will be rejected. Both direct literal values and values that were influenced by literal values are considered. Literal values can originate from literal or parameter expressions to prevent indirect ways of producing a value. This protection is in place for all query constructs that could potentially compare multiple values, such as:

- Expressions that compare values such as Equals, RegexMatches, Min, among others.
- Join keys in joint operations.
- Group-by keys in aggregate operations.

## Aggregation threshold columns

To determine if NULL values are the result of the aggregation thresholds, as opposed to being a natural occurrence in your report, you can use AMC’s **Advanced options** feature within the query editor, **Append aggregation threshold columns.** These columns can be used to troubleshoot your report output and help you understand why the NULL values might be present.

To learn about aggregation threshold columns, visit Advanced options for the AMC query editor.

## Postal code example

Below is a query that allows you to evaluate purchases by postal_code. As a field with a HIGH aggregation, it may return NULL values if there’s insufficient purchase activity in a certain postal code.

```
SELECT
  postal_code,
  SUM(purchases) AS purchases,
  COUNT(DISTINCT user_id) AS customers
FROM
  amazon_attributed_events_by_conversion_time
GROUP BY
  1
```

For the purposes of this exercise, let’s imagine that the result of the query above includes 95 rows, of which 91 include postal_code values along with associated purchases totals. There are also 4 rows, which have purchase totals, but for which postal_code is NULL. The sum of the purchases in the result is 12,000. For brevity, the entire result isn’t shown here, but the head and tail of the result is shown.

Examples of the first 4 of the 91 complete rows that include both the postal_code values and purchases are below. The postal_code values are NOT NULL because there are at least 100 user_id values associated with each postal code.

| postal_code | purchases | customers |
| --- | --- | --- |
| 10001 | 752 | 749 |
| 10023 | 610 | 608 |
| 10007 | 425 | 420 |
| 10012 | 323 | 319 |

The 4 rows without a postal_code value, but with purchases are below. The postal_code values are omitted from the output because there are fewer than 100 user_id values associated with these postal codes.

| postal_code | purchases | customers |
| --- | --- | --- |
|  | 75 | 74 |
|  | 52 | 52 |
|  | 41 | 40 |
|  | 15 | 15 |

First, consider discarding the NULL rows. When it comes to managing these NULL rows, you have several options. With this sample output, we can determine the percentage of purchases that are missing a postal_code value. There were 12,000 total purchases, and only 183 (represented by the 4 records above) didn’t have a postal code match. These 4 records represent only 1.5% of all purchases. For this scenario, you should first consider discarding the NULL rows, focusing your analysis on the rest of the output.

Some other options for managing NULL rows are shown in the next section.

## Managing NULL rows

Follow these steps when your query output has NULL rows:

1. For every key metric, consider what percentage of this metric is represented by NULL vs non-NULL dimensions. In the example above, we found that 1.5% of records had a NULL value. If a low percentage of your key metrics is from NULL dimensions, it’s likely in your best interest to delete them from the file. You decide what your threshold for ‘low’ is.
2. If there are too many NULL values, you may need to make your query less granular to get meaningful insights. Try the following: Check the**aggregation threshold** of your selected columns and consider using less restrictive columns in your query. **Expand the time window of the query**: more time increases the likelihood that more distinct user_id values will be included in each output row, which increases the likelihood of meeting the aggregation thresholds. **Expand the time window of the query**: more time increases the likelihood that more distinct user_id values will be included in each output row, which increases the likelihood of meeting the aggregation thresholds. **Broaden any filtering**that may be in place on the query. **Look at certain dimensions in isolation rather than in combination. Use less granular dimensions** in your final GROUP BY statement. For example, if you aggregate the report by line_item, it’s more likely to contain NULL values than aggregating by campaign.
