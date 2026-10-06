---
title: "Troubleshoot Amazon Marketing Cloud analytics queries"
source_url: "https://advertising.amazon.com/help/GCQW26UPK6U2GPMX"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Troubleshoot Amazon Marketing Cloud analytics queries

Learn how to troubleshoot your Amazon Marketing Cloud (AMC) analytics queries.

Updated on Nov 12, 2025

## Query error remediation

When submitting a query via AMC’s query editor, AMC will check that the code is valid. If it finds errors, such as incorrect SQL code, references to tables that don’t exist, or missing elements like commas or proper aggregation of columns, it will fail. In this scenario, AMC will provide an error message describing the issue and location of the error within the query. Additionally, you’ll have an ‘X’ flag directly within the editor to mark the line of code.

If you run into errors with your query, some common issues to check for include:

- Improper spelling of column or table names
- Syntax issues like missing commas
- Failure to GROUP all dimensions in your query
- Usage of unsupported SQL functions (refer to the instructional query Introduction to AMC SQL for detail on supported functions)
- Issues with JOIN method
- Final SELECT statement includes fields with a HIGH or VERY_HIGH aggregation threshold (for example, including user_id as a dimension in final SELECT statement)
- For audience queries: Failure to include user_id as a dimension in the final SELECT statement. Usage of non-audience tables in your query (audience queries can only use tables with _for_audiences appended at the end of the table name).

If you’re having more complex errors with your query structure, you can use the sandbox to help you develop custom queries by testing one common table expression (CTE) at a time. The sandbox’s features allow you to generate synthetic results for each stage of your query, helping you ensure that your code is functioning as intended. Refer to the instructional query Introduction to AMC Sandbox to learn more about this query development approach.

## Minimizing NULL values in AMC outputs

If you’ve generated a report that has a significant number of NULL values, it may be valuable to re-run the report with the aggregation threshold columns applied to determine the cause of the NULL values. If the cause of the NULL values is indeed the aggregation thresholds, there are several changes you can make to your report logic to minimize the NULL values in the output. These can be done individually or in combination. It may take some experimentation to understand which approach works best for your particular report.

To minimize the number of values rendered NULL due to aggregation thresholds, you can:

1. **Expand the time window of the query**: more time increases the likelihood that more distinct user_id values will be included in each output row, which increases the likelihood of meeting the aggregation thresholds.
2. **Broaden any filtering**that may be in place on the query.
3. Look at certain **dimensions in isolation** rather than in combination.
4. **Use less granular dimensions** in your final GROUP BY statement. For example, if you aggregate the report by line_item, it’s more likely to contain NULL values than aggregating by campaign.
