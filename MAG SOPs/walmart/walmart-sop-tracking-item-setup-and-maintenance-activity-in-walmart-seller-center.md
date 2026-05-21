---
title: "Walmart SOP: Tracking Item Setup and Maintenance Activity in Walmart Seller Center"
category: "Walmart"
source_url: "https://sop.myamazonguy.com/books/walmart/page/walmart-sop-tracking-item-setup-and-maintenance-activity-in-walmart-seller-center"
captured_at: "2026-05-12T07:07:49Z"
---

# Walmart SOP: Tracking Item Setup and Maintenance Activity in Walmart Seller Center

Source: https://sop.myamazonguy.com/books/walmart/page/walmart-sop-tracking-item-setup-and-maintenance-activity-in-walmart-seller-center

## **Tracking Item Setup and Maintenance Activity in Walmart Seller Center**

**Who is this for?** This SOP is amazon specialists who manage multiple client accounts and need to track, manage, and resolve item setup or maintenance activities within Walmart Seller Center.

**Purpose**: To ensure the proper tracking of item setup and maintenance activities within Walmart Seller Center, including monitoring feed submission results, resolving errors, and maintaining accurate product listings.

**Overview**

Whenever items are created or updated in Walmart Seller Center, such as changes to prices, inventory, lag time, or shipping templates, a **Feed ID** will be provided. This ID allows sellers to track the submission’s progress and identify whether the operation was successful or if any errors occurred. Monitoring the Activity Feed dashboard helps sellers stay on top of any issues that may arise during the uploading process, including missing information or exceeding file size limits.

**Process Workflow**

**1. Submitting a Feed**

- **Prepare Feed Data**:

  - Ensure that all required information is included in the feed, such as SKU, price, inventory, and any other necessary attributes.
  - Keep file sizes within the specified limits to prevent upload errors (see feed limits below).
- **Submit the Feed**:

  - Navigate to the **Seller Center** and upload the feed file for item creation or update.
  - Upon successful submission, a **Feed ID** will be generated.
- **Monitor Activity Feed Dashboard**:

  - Access the **Activity Feed** dashboard to track feed progress. You will see:

    - Success or error status of the submission.
    - Error messages, if applicable, which will help identify what needs correction.
- **Addressing Errors**:
  If any errors are encountered, refer to the error report to review the details of the problem and identify the root cause.

Feed Limits and Processing Times

### **Feed Limits and Processing Times**

| Feed Type | Operation | Max Feeds/Hour | Max File Size | Items per Feed | Processing Time |
| --- | --- | --- | --- | --- | --- |
| Item Feed | Bulk create/update items | 10/hour | 25 MB | 10,000 | 4 hours |
| Single Item (UI) | Single item creation in Seller Center | 10/hour | N/A | 1 | 4 hours |
| Price Feed | Bulk price update | 10/hour | 10 MB | 10,000 | 4 hours |
| Inventory Feed | Bulk inventory update | 10/hour | 5 MB | 50,000 | 30 minutes |
| Promo Feed | Bulk promotions update | 6/day | 10 MB | 10,000 | 4 hours |
| Lag Time Feed | Bulk lag time update for items | 6/day | 5 MB | 10,000 | 4 hours |
| Shipping Template | Bulk map SKUs to shipping templates | 10 | 10 MB | 10,000 | 4 hours |

#### **Note:**

- During high-volume periods, such as holidays or sales events, feed limits may be reduced. These limits will be communicated to the team when they are in effect.

**2. Viewing and Downloading Errors**

**Viewing Errors in Seller Center**

- - Navigate to the [**Activity Feed**](https://seller.walmart.com/catalog/account-feed) dashboard in Seller Center.
  - In the **Errors** column, click the number to view a detailed error list.
  - The popup window will display:

    - - A summary of the errors within the feed.
      - A list of the affected SKUs and the corresponding error messages.

**Downloading an Error Report**

- - In the **Error Report** column, click the **download icon** to download an error report.
  - The report will be available in **XLSX** or **CSV** format. You can open it using Microsoft Excel or another spreadsheet application.
  - Use the error report to:

    - Review multiple errors quickly.
    - Identify and fix issues in your original feed.

**3. Fixing Errors**

After reviewing errors, you have two options for resolution:

**Fixing the Root Cause**

- - **Update the Original Feed**: If the error is due to incorrect or missing data, fix the issue at the source level (e.g., correcting the SKU data or missing pricing) and resubmit the feed.
  - **Resubmit the Feed**: Once corrections are made, resubmit the updated feed for processing.

**Creating and Submitting a New Feed**

- - **New Feed for Error Items**: If only certain items failed, create a new feed containing only the items that encountered errors and submit it for processing.

**4. Pending Review and Trust & Safety Issues**

If an item has been flagged by Walmart’s Trust and Safety Policies, the [**Pending Review**](https://seller.walmart.com/catalog/pending-review) dashboard will provide additional insights. If a feed is flagged, take the necessary steps to resolve the issue and ensure that your listings comply with Walmart's policies.

**Additional Guidelines**

- Always **double-check your feed** for completeness and accuracy before submitting to avoid errors.
- During high-volume times, such as holidays, be aware of **reduced feed limits** and plan feed submissions accordingly to avoid delays.
- Use **error reports** to efficiently manage large-scale feed errors and quickly correct issues that impact multiple items.

FAQs

**1. What is the purpose of the Feed ID in Walmart Seller Center?**The Feed ID is provided whenever you create or update items in Seller Center (e.g., updating prices, inventory, or shipping templates). It allows you to track item setup and view maintenance activity in the Activity Feed dashboard, helping you identify successful submissions or errors.

**2. What should I do if I encounter an error after submitting a feed?**If an error occurs, check the error details by selecting the number in the Errors column in Seller Center. You can either update your original feed to fix the issue and resubmit it or create a new feed with only the items that had errors and submit it.

**3. How do I view errors in Walmart Seller Center?**To view errors in Seller Center, navigate to the Activity Feed and select a number in the Errors column. A popup window will display the errors and corresponding SKUs.

**4. Can I download an error report?**Yes, you can download an error report by selecting the download icon in the Error Report column. This will download a spreadsheet of your errors as an XLSX or CSV file, which you can open with Microsoft Excel.

**5. How do I fix errors from my feed submission?**Once you review the errors, you can either:

- Fix the issue at the source level by updating the original feed and resubmitting it.
- Or, create and submit a new feed containing only the items that had errors.

**6. What should I do if I encounter error messages related to Trust and Safety Policies?**If your item is flagged by Trust and Safety Policies, you can navigate to the Pending Review dashboard for additional insight and to address the issue.

**7. What is the maximum number of feeds I can submit per hour/day?**The feed limits vary depending on the type of feed. For example:

- Item Feed: 10 per hour
- Price Feed: 10 per hour
- Inventory Feed: 10 per hour
- Promo Feed: 6 per day
- Lag Time Feed: 6 per day
- Shipping Template Feed: 10 per day

**8. What happens if I exceed the feed limits?**If you exceed the feed limits (e.g., submitting too many updates within one hour or uploading a file that is too large), you may encounter errors. It's important to stay within the maximum feed limits to ensure smooth processing.

**9. How can I download the error report if I have multiple errors?**You can download a detailed error report by selecting the download icon in the Error Report column. This report will be in XLSX or CSV format, making it easier to review and fix errors in bulk.

**10. Is it necessary to monitor the Activity Feed dashboard after a successful feed submission?**Yes, it's important to monitor the Activity Feed dashboard even after receiving a success message. This ensures that any errors that occurred during the submission process are identified and resolved quickly.

**11. Are there any feed limits during high-volume periods?**Yes, during high-volume periods like holidays or sales events, Walmart may temporarily reduce the feed limits. These changes will be communicated to your teams when they are in effect.

**12. I’ve submitted my feed and received a success message. Should I still monitor the Activity Feed dashboard?**

Yes. Even if you receive a success message, it's important to continue monitoring the Activity Feed dashboard. Errors can still occur after the feed submission, and prompt resolution of any issues will ensure quicker processing of your requested actions.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.
