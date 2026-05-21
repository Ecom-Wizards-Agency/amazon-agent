---
title: "Catalog SOP: Error 13043, 90114"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-13043-90114"
captured_at: "2026-05-12T07:07:49Z"
---

# Catalog SOP: Error 13043, 90114

Source: https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-13043-90114

## **Error 13043 and 90114**

**Who is this for:** All individuals who are encountering 13043 and 90114 errors.

**Objective:** To be able to list products with the correct price and enable the successful upload of the flat file.

- This error happens when the input value for the Price (either standard or sales) is lower than the minimum required value or if it's set to 0.
- The error usually happens when CLR is used to perform a full update for the parent listing.
- Please note that when you download the CLR or Category Listing Report, a 0.00 standard price value is usually set for all parent listings.
- To fix this, remove the value stored in the standard_price cell if the SKU is a Parent.

  - Note that a price of 0.00 is never valid and will not be accepted for all listings, either child, standalone, or parent.

**Instructions:**

1. For unsuccessful uploads. Download the flat file report by clicking on the Download your Processing Report link.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/gkIimage.png)

1. Open the downloaded report Excel file to determine the error code. Read the error message.

  - Below is the sample 90114 and 13043 error messages.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/SqCimage.png)

1. Check the ‘template’ tab of your processing report.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Ps8image.png)

1. Search for the names of affected attributes in the Excel column. Typically, errors are indicated in a dark yellow color, and the precise columns are specified in the feed processing summary tab

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/u84image.png)

1. Rework your flat file by supplying a valid product price in the standard_price column. Save and re-upload the flat file.

  - **Parent Listing** - The field 'Your Price' should remain unfilled as this listing is not available for purchase.
  - **Child Listing** - Ensure that the price you assign to each listing is not below the minimum allowable price of 0.01
2. After you have updated the flat file, proceed to upload it again and monitor the upload status.

FAQs

**1. What causes Error 13043 and 90114?**

- These errors occur when the price for a product (either standard_price or sale_price) is set to an invalid value, such as 0 or below the minimum acceptable price of 0.01.

**2. Why is the standard_price field set to 0.00 for parent listings in the CLR?**

- When you download a Category Listings Report (CLR), Amazon automatically sets the standard_price for parent listings to 0.00 because parent SKUs are not purchasable. This placeholder value must be cleared or removed before uploading the flat file.

**3. What is the difference between a parent listing and a child listing in terms of pricing?**

- Parent Listing: The standard_price field should remain blank because it is not directly sold.
- Child Listing: The standard_price field must have a valid price of at least 0.01.

**4. How do I identify affected attributes when these errors occur?**

- Download the Processing Report from the upload status page.
- Open the report and check the Template Tab for columns highlighted in dark yellow.
- Look for the attributes causing the error, typically in the standard_price or sale_price column.

**5. Can I leave the standard_price column blank for standalone SKUs?**

- No, standalone SKUs must have a valid price in the standard_price column. Leaving it blank or setting it to 0 will result in errors.

**6. How do I fix Error 13043 or 90114 for a child listing?**

- Ensure that the standard_price value is at least 0.01 or higher, depending on the product.
- Re-upload the corrected flat file and monitor the processing status.

**7. What should I do if the error persists after re-uploading the file?**

- Verify that all child SKUs have valid prices.
- Ensure the parent SKU's standard_price field is blank.
- Contact Amazon Seller Support if the issue continues, providing the Processing Report for reference.

**8. Can these errors affect multiple listings in the same file?**

- Yes, these errors can occur for multiple parent and child SKUs if the pricing information is invalid or incomplete for several listings.

**9. How do I prevent these errors in the future?**

- Always review and clean up the standard_price field for parent SKUs in the flat file.
- Double-check that all child SKUs have a valid price of at least 0.01.
- Verify pricing data before uploading by comparing it with Amazon's category-specific pricing requirements.

**10. What is the significance of the Your Price field in parent listings?**

- The Your Price field for parent listings must remain blank because parent SKUs are not directly sold. Prices should only be assigned to child listings.

**11. How long does it take for updated prices to reflect after re-uploading the file?**

- Price updates usually reflect within 15 minutes to 24 hours after a successful upload.

**12. Can I set a sale price without setting a standard price?**

- No, a valid standard_price must be entered before assigning a sale_price. Otherwise, the listing will generate an error.

**13. What happens if a child SKU's price is set below 0.01?**

- Amazon will reject the upload for that child SKU, and Error 90114 will appear in the Processing Report.

**14. How do I handle bulk errors in pricing across multiple SKUs?**

- Identify all affected SKUs using the Processing Report.
- Correct the pricing information for each SKU in the flat file.
- Re-upload the file in smaller batches if needed to simplify troubleshooting.

**15. What should I do if my valid price is still rejected?**

- If your price meets Amazon's minimum requirements but is still being rejected:

  - Verify the currency settings in your Seller Central account.
  - Contact Amazon Seller Support with the error details and Processing Report.

**16. Can I leave the sale_price field blank if I’m not running a promotion?**

- Yes, the sale_price field can be left blank if no promotional pricing is being offered.

**17. Are there any specific pricing rules for certain categories?**

- Yes, some categories have specific pricing rules or minimum price thresholds. Refer to Amazon's category-specific guidelines for details.

**18. Can I test the flat file for errors before uploading?**

- Yes, use the Validate File option in Seller Central to identify potential issues before submission.

**19. What should I include in my support ticket if I need help with these errors?**

- Provide the following details:

  - The ASINs or SKUs affected.
  - The Processing Report showing the errors.
  - A copy of the flat file you attempted to upload.

**20. How can I verify the changes after a successful upload?**

- Go to Manage Inventory in Seller Central.
- Search for the updated SKUs.
- Confirm that the prices are correctly reflected in the backend and on the product detail page.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/gkIimage.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/SqCimage.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Ps8image.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/u84image.png
