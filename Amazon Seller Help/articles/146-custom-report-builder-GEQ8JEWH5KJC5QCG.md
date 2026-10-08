---
title: "Custom Report Builder"
source_url: "https://sellercentral.amazon.com/help/hub/reference/GEQ8JEWH5KJC5QCG"
downloaded_at: "2026-10-07"
source: "Amazon Seller Central Help"
---

# Custom Report Builder

The Custom Report Builder is a reporting wizard in Seller Central that enables you to create and save customized reporting views by dragging and dropping data fields from a given list of attributes.

The tool allows you to easily visualize various aspects of your business by building your own custom reports from a pre-populated **Business view**. Business views bring together data fields from various reports that are relevant to a particular aspect of your business, such as **Inventory**.

For example, the **Inventory** business view aggregates all key information for a given FNSKU and fulfillment center combination and a given date range. This key information includes such data as inventory that is in transit, in a fulfillment center, being delivered to buyers, lost, or damaged.

You can build custom reports in a few simple steps, which are described in more detail below:

1. Select a domain, or **Business view**.
2. Drag and drop the desired attributes.
3. Select a date range.
4. Generate your custom report.

With the Custom Report Builder, you can do the following:

- Generate a report
- Download the report
- Create and save a custom view
- Edit or delete the custom view
- Mark a view as a **Favorite** for easy access

Creating customized reporting views and saving them for future use lets you avoid having to download a full report with all the columns. Creating a customized reporting view is helpful when you’re looking for specific data fields and aren’t sure which report to use or where to find it.

For example, if you want to see data about damaged inventory units, but you’re not sure which report to use, you can go to the Custom Report Builder and select the **Inventory** business view, which will populate all the relevant attributes. Then you can add the **Damaged** attribute to your customized reporting view, and generate a report for your desired date range.

The Custom Report Builder aims to end the frustration that can arise from the following:

- The difficulty in finding the right report
- The need to jump through several tabs and reports to find the right information
- The inability to reconcile related reports due to varying granularity of the underlying data

## How to use the Custom Report Builder

To access the Custom Report Builder, select **Fulfillment** from the **Reports**drop-down menu in Seller Central. Within the tool, click **Take a tour** to learn more.

To create a customized reporting view, follow these steps:

1. Under the **Create new view** tab, select a **Business view**, or domain, for which you want to create the custom report, such as **Inventory**
2. Select your desired attributes from the **Available attributes** list, and click **Add**. The list includes attributes such as **ASIN**, **MSKU**, **Product title**, **Disposition**, **Customer shipments**, and **Customer returns**. If you change your mind and want to remove an attribute, click **Remove**. **Note:**Some attributes are mandatory in order to generate your report. These attributes will appear automatically in the **Selected attributes** field, and cannot be removed. **Tip:**To see a definition for an attribute, hover your cursor on “i” button next to it.
3. Select a date range from the **Select date range** drop-down menu, or enter a custom date range.
4. Click **Generate report**. Your custom report will include only the attributes that you have chosen.

## Save your selections

To save your customized selections for the report, click **Save view**. You can access your saved views for future use by clicking the **Your saved views** tab.

Saved views appear in the order in which they were last used. You can mark your views as **Favorite**using the toggle button to the right of each view name.

**Note:**Initially, we’re launching this tool with the **Inventory** business view and select data fields. In future phases, we’ll add more attributes from various reports, as well as other business views such **Returns** or **Shipments**.

## Frequently asked questions

#### Where can I see my previously downloaded custom reports

You can see the list of previous downloads on either the **Create new view** or **Your saved views** tab. Once you select a date range and click **Generate report**, the request will be shown in the activity table along with its current status, such as **In progress** or **Ready for download**.

Once the report has been generated, you can download it, and any previously generated reports, by clicking the corresponding **Download** button.

#### Why can’t I remove a pre-selected attribute?

The Custom Report Builder shows certain attributes as pre-selected in the **Selected attributes** field. Currently, these attributes are mandatory for creating any custom view within that business domain. These mandatory attributes define the lowest level of detail that is supported by the business view and therefore can’t be removed.

#### How can I reconcile Custom Report Builder data with other reports on Seller Central?

The Custom Report Builder combines data from multiple reports, and its data may be at a different level of detail than existing reports. As a result, reconciliation might not always be possible. However, the data between reports and the Custom Report Builder should match as long as the same level of detail and the same date ranges are being compared.

#### I can’t select the date range that I want.

Currently, the Custom Report Builder supports a 30-day time period. To view data for a broader date range, use the existing reports in Seller Central.

#### The data in the Custom Report Builder doesn’t match with the corresponding report. For example, the tool’s Inventory view doesn’t match with the Inventory Ledger report.

Initially, we are launching the Custom Report Builder with the **Inventory** business view only. The **Inventory** view should match exactly with the Inventory Ledger report for a given combination of date, FNSKU, and fulfillment center ID. If the data doesn’t match, make sure that the attributes that you selected are consistent between the two reports.

#### I can’t find the attributes I need. How can I get them added?

If you don’t see a desired attribute in the **Business view** list, please leave a comment using the **Feedback** option on bottom-left corner of the page, or through the **Rate this page** option in the Custom Report Builder, and we will try to include these attributes in our future updates.

## Attributes available in the Inventory business view

| Attribute name | Description |
| --- | --- |
| Date | The snapshot date for the data in the report |
| FNSKU | The Fulfillment Network Stock Keeping Unit (FNSKU) of the product. Amazon assigns an FNSKU to products that are stored in and fulfilled from a fulfillment center. |
| ASIN | The Amazon Standard Identification Number (ASIN) of the product. The ASIN is assigned by Amazon. |
| MSKU | The Merchant Stock Keeping Unit (MSKU) of the product. The MSKU is assigned by the seller. |
| Product title | The name of the product or item as mentioned on the order. |
| Disposition | The condition of the units in inventory, such as **Sellable** or **Damaged** |
| Starting warehouse balance | Units of the product that were available in fulfillment centers at the start of the reporting time period |
| In transit between warehouses | Units that are in transit between fulfillment centers |
| Receipts | Units that were received in shipments to fulfillment centers |
| Customer shipments | Units that were shipped out for deliveries of customer orders that Amazon fulfilled |
| Customer returns | Units that buyers have returned to fulfillment centers and that have been returned to your inventory |
| Vendor returns | Units that vendors have returned to fulfillment centers and that have been returned to your inventory |
| Warehouse transfer in/out | Total number of units that have been transshipped into and out of fulfillment centers during the reporting period |
| Found | Units that were missing but have been found and returned to your inventory |
| Lost | Units that are missing from your inventory in fulfillment centers and for which you may be eligible for reimbursement |
| Damaged | Units from your inventory in fulfillment centers that have been identified as damaged and for which you may be eligible for reimbursement |
| Disposed | Units that have been removed from your inventory and have been disposed of |
| Other events | Units from your inventory in fulfillment centers that may not be covered under the other definitions |
| Ending warehouse balance | Units of the product that were available in fulfillment centers at the end of the reporting time period |
| Unknown events | Units for which a specific event type is not yet known. Units may be categorized this way because of events that are happening during the reporting snapshot period. Expanding the reporting time period can reduce the number of unknown-events units. |
| Fulfillment center | The fulfillment center where the item is stored |
| Country | Country of the fulfillment center where the item is stored |
