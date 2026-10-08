---
title: "Best practices for using the Ads Agent in AMC to generate AMC SQL queries"
source_url: "https://advertising.amazon.com/help/GZTSBQTMR2VHPL85"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Best practices for using the Ads Agent in AMC to generate AMC SQL queries

Guidelines for writing effective prompts when using the Ads Agent in AMC.

Updated on Mar 30, 2026

When writing prompts to generate your SQL query, you can follow some guidelines to improve the quality of the results. Your prompts can range from basic to advanced based on how clear, accurate, and well detailed your prompts are.

The Ads Agent in AMC doesn't look up lists of your campaign IDs, ASINs, keywords, or audience segment names. Instead, it filters based on the description you provide. Include exact campaign IDs, ASINs, keywords, and audience segment names in your prompt, or modify the generated SQL before submitting the query.

**Example:**

- Basic audience query: "Create an audience of users who have viewed my product pages at least 3 times but haven't made a purchase in the last 7 days"
- Advanced audience query: "Engage customers who are in the top-10 percentile of viewers for my brand store and have clicked on at least 2 different campaigns but haven't purchased in 90 days"

To ensure that your query prompts are effective, follow these best practices when writing your prompts:

- Specify the type of query (either audience or analytical)Example: “Create an audience query that ...” or “Create an analytical query to ...”
- Be specific when writing about conditions **Example:**"Engage new-to-brand customers who purchased over $100" is more effective than "engage new-to-brand customers"
- Include time windows wherever possible **Example:**Use "in the last 14 days" instead of "recently"
- Specify the conditions clearly **Example:**You can write "top 10% of customers by total sales revenue" instead of "high-value customers".

## Customizing your query

The generated query allows for customization to match specific requirements. You can modify the code by adding filters for specific ASINs, campaign IDs, or other relevant parameters. If you require help understanding any customization requirements, ask for clarification or examples. When optimizing the SQL queries ensure:

- **Review table joins:** Examine the SQL to ensure that table joins are implemented efficiently. Look for opportunities to simplify or consolidate joins where possible.
- **Check date range implementations:** Verify that date range filters and time windows are properly applied in the SQL and ensure that date comparisons are optimized for performance.
- **Verify filter conditions:** Review all filter criteria to confirm they accurately reflect the intended audience parameters. Double-check that numerical thresholds, percentiles, and other conditions are correctly translated.
- **Use specific table/column names:**Make sure the SQL is referencing valid AMC data source table/column names.
- **Specific value reference:**The audience SQL query generator doesn’t generate specific ASIN/campaign name/brand name or product names. Include specific values.
- **Use AMC-supported syntaxes:**Ensure that your modified query conforms to AMC supported SQL functions and syntax.
- **Use query editor controls:**Leverage controls directly from a right-click context menu in the query editor, making it faster to edit, explain, and fix queries.
- **Transfer queries between editor and chat:** Open AI-generated SQL directly into the query editor from the Ads Agent in AMC chat and review changes with a side-by-side comparison view.

## Sample prompts

**Sample prompts for getting AMC product help**

- “How do I filter by ad product type?”
- “What is the difference between the conversions table and the conversions_all table?”
- “How do I create an audience”
- “What is the minimum seed size for a lookalike audience?”
- “How do I use custom parameters”

**Sample prompts for audience query generation**

- "Engage new-to-brand customers who purchased from ASINs XXXX, YYYY, or ZZZZ in the last 30 days"
- "Create an audience of users in top 25% of total product sales for ASINs XXXX and YYYY over the last 90 days"
- "Create an audience that added products XXXXX, YYYYY to their cart but didn't purchase in the past 3 months"
- "Engage users who spent over 10 minutes on brand store pages after interacting with my Amazon DSP campaigns"
- "Engage users interested in personal finance who added products to their cart but didn't purchase in the US marketplace"
- "Create an audience of users with pickup trucks in their Amazon Garage"

**Sample prompts for measurement query generation**

- "Write an exploratory query to fetch campaign IDs for my sponsored ads campaigns."
- "Create a query that will show me the top 25th percentile of product sales."
- "Create a query that calculates the total product sales this year from new-to-brand users acquired in January 2025"
- "Create a query highlighting the path to conversions per campaign"
