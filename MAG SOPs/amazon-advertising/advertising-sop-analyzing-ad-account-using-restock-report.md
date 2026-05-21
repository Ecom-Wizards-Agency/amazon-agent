---
title: "Advertising SOP: Analyzing Ad Account using Restock Report"
category: "Amazon Advertising"
source_url: "https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-analyzing-ad-account-using-restock-report"
captured_at: "2026-05-12T07:07:49Z"
---

# Advertising SOP: Analyzing Ad Account using Restock Report

Source: https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-analyzing-ad-account-using-restock-report

## **How to Use Restock Report to Analyze the Ad Account**

**Who is this for?**
Individuals dealing with Amazon accounts that have more than 100 ASINs in the catalog.

**Objective:**
The objective of this document is to identify ASINs that generate substantial organic FBA sales but have not been advertised yet, and those that have been advertised but currently do not have available FBA stock.

**Note:**
The restock reports from Amazon exclusively feature FBA SKUs, and we endeavor to prioritize advertising for these SKUs to optimize our ad performance wherever feasible.

**Steps:**

- Download the Restock Report

  - To reach the Restock Report, log in to the account and click [this link](https://sellercentral.amazon.com/restockinventory/reports?reportTypeId=94300&tbla_report-request-table=sort:%7B%22sortOrder%22%3A%22DESCENDING%22%7D;search:undefined;pagination:1;)
- Download the Advertised Product Report

  - To reach the Advertised Product Report, log in to the account and click [this link](https://advertising.amazon.com/reports/new?entityId=ENTITYKRKEX85GL3VB)
  - Select "Report type" as "Advertised product" and click "Run report"

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/srGimage.png)

- To find out the ASINs that have been advertised but don’t have active FBA stock:

  - Use VLOOKUP on your Advertised Product ASINs and get the “Available” column from Restock Report to find out if you have stock or not

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/qMUimage.png)

The ASINs that have high organic FBA sales but are not being advertised

1. Download the last x days of sales report from the Seller Central > Reports

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/4M8image.png)

Copy all the advertised ASINs from Advertised Product Report. Copy all the ASINs that have FBA sales. Then using a VLOOKUP, find out the ASINs that are not advertised but have FBA stock. Now you can also VLOOKUP the organic sales of this ASIN from Business Sales Report to find out which has the highest organic sales to prioritize your campaign creation strategy.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/vj4image.png)

Below you can find an example Excel file that is generated. You can check the reports, formulas, and structure there.

[Click here for the template](https://docs.google.com/spreadsheets/d/1V8Eh2dI80NPKgMpzi2fiXULwb021q6Dt/edit?usp=sharing&ouid=103927266653410458249&rtpof=true&sd=true)

FAQs

##### FAQs

- **Q1: What type of ASINs are prioritized for advertising?**

  - **A1:**FBA SKUs are prioritized to optimize ad performance since restock reports exclusively feature these SKUs.
- **Q2: What are the key reports needed for this analysis?**

  - **A2:**

    - **Restock Report**: For checking FBA stock availability.
    - **Advertised Product Report**: For identifying ASINs that have been advertised.
    - **Sales Report**: For organic sales data to identify high-performing ASINs.
- **Q3: How do I download the Restock Report?**

  - **A3:**Log in to the Amazon account, click the provided link to access the report, and download it.
- **Q4: How do I download the Advertised Product Report?**

  - **A4:**Log in to the Amazon account, select "Report type" as "Advertised Product," and click "Run report" to generate and download the data.
- **Q5: How do I identify advertised ASINs without active FBA stock?**

  - **A5:**Use VLOOKUP on the Advertised Product Report ASINs to pull the “Available” column from the Restock Report. This will show which advertised ASINs currently lack FBA stock.
- **Q6: How do I find ASINs with high organic FBA sales that are not advertised?**

  - **A6:**

    - Download the sales report from Seller Central.
    - Copy advertised ASINs and FBA sales ASINs into an Excel sheet.
    - Use VLOOKUP to find ASINs with FBA stock that are not in the Advertised Product Report.
    - Use VLOOKUP again with the Business Sales Report to identify ASINs with the highest organic sales for prioritizing campaign creation.
- **Q7: How can I organize and analyze the data effectively?**

  - **A7:**Use the provided template to structure your Excel file. It includes examples of reports, formulas, and analysis workflows.
- **Q8: What should I do after identifying ASINs to prioritize?**

  - **A8:**

    - Create advertising campaigns for ASINs with high organic sales and available FBA stock.
    - Monitor campaign performance to ensure ad efficiency and maximize sales.
- **Q9: Can I automate the process using Excel formulas?**

  - **A9:**Yes, formulas like VLOOKUP are key to cross-referencing data between the Restock Report, Advertised Product Report, and Sales Report.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/srGimage.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/qMUimage.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/4M8image.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/vj4image.png
