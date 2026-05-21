---
title: "Catalog SOP: Adding SKU_ASIN to Existing Parentage"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/catalog-sop-adding-sku-asin-to-existing-parentage"
captured_at: "2026-05-12T07:07:49Z"
---

# Catalog SOP: Adding SKU_ASIN to Existing Parentage

Source: https://sop.myamazonguy.com/books/catalog/page/catalog-sop-adding-sku-asin-to-existing-parentage

## **Adding SKU/ASIN to Existing Parentage**

**Who is this for :**This is intended for Account Specialists who are required to add SKUs to parentage that already exists.

**Objective :** To guide Account Specialists to ensure the successful adding of SKUs to existing parentage.

**Instructions:**

1. Backup file.

  - Download a Category Listings Report (CLR).
  - Save it both in the Asana task and the client's folder.
2. Download a category-specific template.
3. Identify the SKUs that you want to add to the parentage (both FBA and MFN)

We need to identify the SKUs that we will be adding to the parentage. We need to ensure that both the FBA and MFN SKUs are added to the template upload file to make the catalog more organized.

- When you have your list of ASINs that need to be parented, go to Inventory > Manage All Inventory

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/adding-sku_asin-to-existing-parentage-image-82hdtwfc.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JHKimage.png)

- Search for each one in the catalog and grab the SKU of each item under that ASIN (make sure that the “Status” and “Fulfilled by” are set to “All”).

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-2D420RDK.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/WE0image.png)

- Identify the variation name to be used for the parentage based on the variation theme that will be used. (SKUs with the same ASIN will have the same variation name).

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-XBQOTJ8K.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fwzimage.png)

- Once we have that list, we open the template we downloaded and fill out the necessary information.

4. Fill out the flat file

I. Child SKUs

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-BIOEPJF3.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/pYrimage.png)

II. Variation Data

1. Parentage: Child
2. Parent SKU: WAYTUMBLER-PARENT (this is the existing parent SKU)
3. Relationship Type: Variation
4. Variation Theme: Size (variation theme of the existing parentage)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-I1SG7NFS.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Xgaimage.png)

III. Variation Theme Name attribute

- You will need to find the attribute column that corresponds with the variation name. In this example, we are using a size parentage so we need to find the SizeName attribute on the template.
- Press CTRL + F to bring up the Find tool and enter “size” (or your variation theme” to find the size attribute.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-QT14S6CH.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/QKjimage.png)

IV. Update_Delete

**PartialUpdate**

This column should be filed with PartialUpdate. If you use “Update” instead of “PartialUpdate”, Amazon will erase the data for any cell that does not have data input in the template you create. In this case, all data would be erased except for the parentage data we are adding.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/adding-sku_asin-to-existing-parentage-image-dfh7x8po.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/8Fjimage.png)

V. Fulfillment Center ID

Under the Fulfillment Center ID, use AMAZON_NA (NA for North America, CA for Canada, MX for Mexico, etc) if it’s Fulfilled by Amazon and DEFAULT if it’s Fulfilled by Merchant.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-L1XJA39P.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/lBlimage.png)

**REMINDER:**When you submit inventory feeds to update inventory levels for items that you sell on Amazon's website, never leave the fulfillment-center-id null. For a self-fulfilled inventory, enter DEFAULT in this column. For Fulfillment by Amazon inventory, enter either AMAZON_NA, AMAZON_EU, AMAZON_JP, or AMAZON_IN depending on your marketplace. This helps ensure that each item is fulfilled as you expect it to be.

**IMPORTANT NOTE:**

- If it’s FBA, you have to fill out the following columns:

  - “batteries_required”
  - “supplier_declared_dg_hz_regulation1” under the Compliance section.
  - Pesticide Marking

    - EPA Registration Number
  - Pesticide Registration Status

    - This product is not a pesticide or pesticide device, as defined under the U.S. Federal Insecticide, Fungicide, and Rodenticide Act.

Once you have filled out all the required information for adding SKUs to a parentage, this preview serves as an example of what the flat file will look like.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-I1HWFAHJ.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FOKimage.png)

5. Save the flat file and upload it on Seller Central. Go to Catalog> Add Products via Upload > Upload your spreadsheet. Refresh the page first before attaching the file and make sure you’re on the right Amazon store. Then click Submit products.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-CI6DKNME.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Xopimage.png)

Once the file has been uploaded and processed, let it sit for 15 minutes. It can take a little time for the file to finish being processed.

Important Note:

- Monitor the Upload Status. If it says “Complete Drafts”, download the Processing Report to see what caused the error and fix it accordingly.

6. Verify if the SKUs are added to existing Parentage

Once you receive the update from Amazon about the successful processing of your upload file, find the parent in the catalog and check that the child SKUs are attached.

You can verify the parentage from these options:

**A. Manage All Inventory**

1. Go to Seller Central > Inventory > Manage All Inventory and search for the parent SKU.
2. Make sure that the Status and Fulfilled by are set to “ALL”.
3. Click the dropdown next to the Parent SKU and verify that all of the child SKUs are present.

**B. Variation Wizard**

To access the Variation Wizard, follow the steps below:

- On the Inventory link in your Seller Central account, select Add a Product.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-FV080104.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/lD1image.png)

- In the Add Products page, click on create variations using Variation Wizard

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-KJ98UXL7.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/5Qiimage.png)

- Click the option “Add to or update an existing variation family” to search the ASIN.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/adding-sku_asin-to-existing-parentage-image-tuhqcbgh.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/gm9image.png)

- This is how a parentage setup looks like in ‘Variation Wizard.’

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-4YUS8DW2.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/KSRimage.png)

**C. Amazon Detail Page**

To confirm that you have successfully added the listing to your existing parentage, navigate back to the inventory page and click on the title of the child SKU. This will display the parentage of the product detail page (PDP). If the SKU you added is present within the group, it means that the addition was successful.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-JJLAMDMD.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Q5simage.png)

FAQs

**1. What should I do if the flat file upload shows errors?**

- If the upload status shows "Complete Drafts," download the Processing Report to identify and address the errors. Review the error messages, correct the relevant columns in your flat file, and re-upload the corrected file.

**2. How do I find the appropriate variation theme for my SKUs?**

- The variation theme depends on the parentage type already established. For example, if the existing parentage uses the size theme, locate the "SizeName" column in the template. Use CTRL + F to find the correct attribute column.

**3. Why is it essential to use "PartialUpdate" in the Update_Delete column?**

- Using "PartialUpdate" ensures that only the specified data in the flat file is updated, without overwriting existing information for other attributes. Using "Update" instead will erase all non-specified data in the template, potentially causing unintended issues.

**4. What Fulfillment Center ID should I use for FBA and MFN SKUs?**

- For FBA SKUs, use AMAZON_NA for North America (or the corresponding region like EU, JP, IN, etc.).
- For MFN SKUs, use DEFAULT.

**5. What additional compliance details are required for FBA products?**

- For FBA products, ensure you fill out:

  - Batteries Required (Yes/No)
  - Supplier Declared DG HZ Regulation1
  - Pesticide Marking: Select "This product is not a pesticide or pesticide device."

**6. How do I verify that the SKUs were added to the existing parentage?**

- You can verify by:

  - Manage All Inventory: Search for the parent SKU, set “Status” and “Fulfilled by” to “ALL,” and check the child SKUs under the parent.
  - Variation Wizard: Use the “Add to or update an existing variation family” option to confirm the addition.
  - Amazon Detail Page: Navigate to the child SKU’s product detail page to confirm it appears in the parent grouping.

**7. Can I add both FBA and MFN SKUs to the same parentage?**

- Yes, you can. Ensure both FBA and MFN SKUs are included in the flat file upload to maintain an organized catalog.

**8. What precautions should I take before uploading the flat file?**

- Save the flat file in the Asana task and the client’s folder for backup.
- Refresh the Seller Central page before uploading.
- Ensure all mandatory columns are filled to prevent errors.

**9. What should I do if the parentage does not appear correctly on the product detail page?**

- Check the following:

  - Verify the flat file for errors or missing data in the Processing Report.
  - Confirm the variation theme matches the existing parentage.
  - Re-upload the corrected flat file after addressing the issues.

**10. How long does it take for the updates to reflect after uploading the flat file?**

- Allow at least 15 minutes for Amazon to process the file. Check the status in Seller Central after this period.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/adding-sku_asin-to-existing-parentage-image-82hdtwfc.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JHKimage.png
- 3. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-2D420RDK.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/WE0image.png
- 5. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-XBQOTJ8K.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fwzimage.png
- 7. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-BIOEPJF3.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/pYrimage.png
- 9. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-I1SG7NFS.png
- 10. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Xgaimage.png
- 11. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-QT14S6CH.png
- 12. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/QKjimage.png
- 13. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/adding-sku_asin-to-existing-parentage-image-dfh7x8po.png
- 14. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/8Fjimage.png
- 15. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-L1XJA39P.png
- 16. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/lBlimage.png
- 17. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-I1HWFAHJ.png
- 18. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FOKimage.png
- 19. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-CI6DKNME.png
- 20. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Xopimage.png
- 21. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-FV080104.png
- 22. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/lD1image.png
- 23. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-KJ98UXL7.png
- 24. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/5Qiimage.png
- 25. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/adding-sku_asin-to-existing-parentage-image-tuhqcbgh.png
- 26. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/gm9image.png
- 27. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-4YUS8DW2.png
- 28. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/KSRimage.png
- 29. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-JJLAMDMD.png
- 30. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Q5simage.png
