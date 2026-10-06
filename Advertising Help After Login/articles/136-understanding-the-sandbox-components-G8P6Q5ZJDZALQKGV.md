---
title: "Understanding the sandbox components"
source_url: "https://advertising.amazon.com/help/G8P6Q5ZJDZALQKGV"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Understanding the sandbox components

The Amazon Marketing Cloud (AMC) sandbox has multiple components that allow you to safely build and test queries.

Updated on Feb 24, 2026

## Components overview

**Note:**Sponsored ads advertisers accessing AMC via instant self-service will not be able to use Sandbox.

- **Use case library:** The use case library is a comprehensive collection of ready-to-use custom solutions and instructional queries (IQs). AMC users can either directly implement these solutions or modify the SQL code of an IQ to address common measurement and audience analysis needs. Read the Introduction to Sandbox instructional query (IQ) to get started with some basic use cases.
- **Query editor**: The **Query editor** tab allows you to access the query editor and associated components to help you write queries. A query contains the AMC SQL commands that allow you to access and view signals based on your tailored requirement. Review section below for additional information on this tab.
- **Paid features**: This is AMC’s premium subscription model, which provides options for deeper analysis of your audiences, campaigns, and outcomes. However, the subscription capability is disabled in the sandbox instance. Navigate to your advertiser instance to subscribe to Paid Features offerings. Keep in mind, some paid features are available for only certain advertisers. **We have a synthetic version of these tables readily available in the sandbox.** You can view these by navigating to the query editor tab, and click the subscriptions in the schema explorer.

## Query editor

The query editor page has 3 main areas: schema explorer, query editor, and submitted queries.

**Schema explorer**

This section is located on the left pane and lists the available tables. Click a table to list its metrics and dimensions. A tooltip displays the description and the signal type of the selected column. To insert a table or column into your query, double-click on the item name (table or column). The schema explorer also allows you to preview a table.

- **Table preview:** With the table preview feature, you can quickly inspect the schema and get concrete source information of selected tables. Specifically, you can view the top 100 rows of a table with a single click. This helps to develop a more contextual understanding about table structure and record format. To preview a table in the sandbox instance, click the **Run Preview** icon. The SELECT [columns] FROM table_name LIMIT 100 query populated in the query editor and automatically submitted for execution. This query is run with the aggregation controls off. The result of this query is a row level information of a table, which is output as a file that you can download from the **Submitted queries** section.

**Query editor**

This section is located in the center, and it’s where you author and run SQL queries using synthetic signals.

This interface is further divided into:

1. **SQL code** is the area where you’ll type your SQL query.
2. **Custom parameters** is the area where you store user-defined parameters that you can use to customize instructional queries, per your business requirements.
3. Filter options can be based on **Date range** and **Time zone**.
4. Use the **Query timeout** drop-down to select the time after which AMC will stop running the query. If the time-out is done, AMC will stop even if the queries are still running.
5. Apply **Advanced Options** (**Append aggregation threshold columns**).

You can use the toggle button to **Show custom parameters** pane. The **Aggregation controls** toggle is specific and unique to the AMC sandbox.

**Note:**This feature is also available via API. Refer to the Sandbox API documentation.

Using the aggregations controls toggle, you can choose whether or not to apply aggregation thresholds to analyses generated atop synthetic signals.

- With **Aggregation controls** set to **on**, you can generate aggregated analyses based on synthetic signals. This simulates the analytics experience of using advertiser instances in AMC.
- With **Aggregation controls** set to **off**, you can view event-level synthetic signals when querying. This helps you inspect the underlying composition of your queries. This view is NOT available in the advertiser instances.

**Submitted queries**

This section is located at the bottom of the query editor lists all queries that you have run in the query editor. If your query is accurate and executed successfully, a **Download** link appears in the UI alongside the query, in the **Results** column, allowing you to download your query results. There’s also an indicator, which tells you whether the queries ran with the aggregation controls or not. The **Action** column allows you to reopen the code in the query editor or copy the execution ID of the query. In case you need assistance on some aspect of your query from AMC Support, quote the query execution ID.

After reviewing the output results, you can copy the code from the SQL code section of the query editor and paste the code in the SQL code section of the query editor in the instance you work on and derive actual results to help you generate insights.
