---
title: "Catalog SOP: Feed Processing Error Code - 8115"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/catalog-sop-feed-processing-error-code-8115"
captured_at: "2026-05-12T07:07:49Z"
---

# Catalog SOP: Feed Processing Error Code - 8115

Source: https://sop.myamazonguy.com/books/catalog/page/catalog-sop-feed-processing-error-code-8115

## **Feed Processing Error Code - 8115**

**Who is this for:** This is for All individuals who are encountering 8115 errors.

**Objective:** To ensure that all are able to address the 8115 error whenever it appears in the processing report.

**Error Code: 8115**

Error Message:

This error occurs when you submit an invalid ConditionType value in your inventory file or product data feed. Valid values for ConditionType may include:

- New
- Refurbished
- UsedLikeNew
- UsedVeryGood
- UsedGood
- UsedAcceptable
- CollectibleLikeNew
- CollectibleVeryGood
- CollectibleGood
- CollectibleAcceptable

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Cbnimage.png)

Note: Some ConditionType values might not be valid in all product categories.

**Instructions:**

1. From the template you uploaded previously, locate the column “Condition”

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-2lblrqnj.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/y3Fimage.png)

2. Highlight the condition type ‘New’ and then clear the contents.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-56dvzc6q.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/SLnimage.png)

3. After you have cleared the condition type fields successfully, you can use the drop-down option to select the appropriate condition type based on the valid values.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-wyo734jm.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/bO5image.png)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-uswkh2n1.png)

**IMPORTANT NOTE: Avoid dragging the condition type for the rest of the SKUs and instead make use of the drop-down option.**

4. Once done, resubmit your product data with a valid Condition Type value and monitor the upload status.

If you continue getting the 8115 error even if the condition type is correctly filled out, perform a [full update](https://sop.myamazonguy.com/books/catalog/page/catalog-sop-full-update-flat-file). After completing a full update and the problem persists, you may need to perform deleting the product and relist it after at least twenty-four hours from the time of deletion with a full update flat file with the correct attributes using [this SOP](https://sop.myamazonguy.com/books/catalog/page/catalog-sop-file-uploads-delete-relist).

FAQs

**1. How do I check which ConditionType values are valid for my product category?**

- Amazon does not allow all ConditionType values for every category. To check which ones are accepted:

  - Go to Seller Central > Add a Product and search for your item.
  - Click on the listing and check the available condition options.
  - Alternatively, download an inventory template for your category, and refer to the Valid Values tab to see the approved ConditionTypes.

**2. Why shouldn't I drag the ConditionType for multiple SKUs?**

- Dragging can cause errors because:

  - It may accidentally copy an invalid condition for certain SKUs.
  - Some cells might not format correctly when dragged.
  - Amazon may reject the file if the condition field is inconsistent.
  - Best Practice: Use the drop-down menu for each SKU or copy and paste carefully to ensure accuracy.

**3. Why does a full update help resolve the 8115 error?**

- A full update ensures Amazon receives and processes all product attributes correctly. If there are conflicting data points in previous partial updates, a full update replaces them with correct values, reducing potential listing errors.

**4. How long does it take for the 8115 error to resolve after making corrections?**

- If the issue is due to an incorrect condition type, updates should reflect within 15–30 minutes after a successful upload.
- If a full update is required, changes may take up to 24 hours to process. (Get permissions from client first)
- If deletion and relisting are necessary, wait at least 24 hours after deletion before re-uploading to avoid data conflicts.

**5. I followed all the steps and the error still appears. What should I do?**

- If you've cleared the condition type, done a full update, and even deleted/relisted the product but the error persists:

  - Try using "Partial Update" instead of "Full Update" to refresh the condition.
  - Check if Amazon has a listing restriction on your product’s condition type.
  - Contact Amazon Seller Support and provide:
  - SKU(s) affected
  - The exact error message
  - A copy of the feed file you uploaded
  - Steps you’ve already taken

**6. What causes Error 8115?**

- This error is usually caused by:

  - Entering a condition type that is not allowed in your product category.
  - A formatting issue in the "Condition" column of the inventory file.
  - Amazon’s system temporarily not recognizing an update due to a backlog.

**7. Can I update the condition type through the Manage Inventory page instead of a feed file?**

- Yes, but this only works for a few listings at a time.
- Go to Inventory > Manage Inventory in Seller Central.
- Find the affected product and click Edit.
- Update the Condition field manually.
- Click Save and Finish to update the listing.
- For bulk updates, a flat file upload is recommended.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Cbnimage.png
- 2. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-2lblrqnj.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/y3Fimage.png
- 4. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-56dvzc6q.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/SLnimage.png
- 6. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-wyo734jm.png
- 7. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/bO5image.png
- 8. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/feed-processing-error-code---8115-image-uswkh2n1.png
