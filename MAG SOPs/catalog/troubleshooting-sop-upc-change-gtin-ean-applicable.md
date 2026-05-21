---
title: "Troubleshooting SOP: UPC Change (GTIN, EAN applicable)"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/troubleshooting-sop-upc-change-gtin-ean-applicable"
captured_at: "2026-05-12T07:07:49Z"
---

# Troubleshooting SOP: UPC Change (GTIN, EAN applicable)

Source: https://sop.myamazonguy.com/books/catalog/page/troubleshooting-sop-upc-change-gtin-ean-applicable

## **UPC Change (GTIN, EAN applicable)**

**Who is this for:**

This is intended for individuals who will be changing the UPC to a GS1 barcode.

**Objective:**

This is intended to guide Amazon Specialists on how to change their UPC to a GS1 barcode (applies to active FBA/FBM listings).

This also includes scenarios where you have to troubleshoot suppressed listings and new ASINs created by Amazon due to the UPC change process.

**Procedure:**

**Required documents:**

- GS1 certificate
- Real world images displaying the correct UPC
- Manufacturer’s Website Link displaying the correct UPC
- Letter of Affiliation (If the Brand owner and the UPC owner is not the same)
- Screenshot of the old UPC from gs1 to prove that it is not the correct UPC of the product. (optional)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Vadimage.png)

**Steps:**

1. Go to Inventory Reports and download a CLR. Keep it until the task is complete as a backup.
2. Identify the listings before proceeding.

If an ASIN doesn't have an existing UPC/EAN code attached to it, proceed with a partial update using a flat file and use the UPC code provided by the client as the product ID of the listing. A listing with no UPC assigned to it looks like this

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/M5Limage.png)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-M121CN6H.png)**Partial Update template example:**

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-JEUTBFO1.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/9Lyimage.png)

If an ASIN already have a product ID assigned to it, create a duplicate ASIN with the correct UPC, have them merged, and then keep the original ASIN with the correct UPC.

Use a flat file to copy the original listing. You can add "-1" or "-DUPE" on the SKU and place the correct UPC. (push the original listing with a partial update and the duplicate SKU as Full Update to avoid data inconsistencies which might cause a problem when requesting it to merge.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Lizimage.png)

**Template A:**

Our listing was created with a random UPC instead of the proper GS1-registered barcode. One of your colleagues told us that we have to create a new listing, integrate it with our original ASIN, and then cleave/disable the incorrect UPC:

- Attribute to Update - UPC/EAN
- – Original ASIN
- (insert original ASIN)
- – Correct Product Identifier
- (insert Correct UPC/EAN)
- – New ASIN
- (insert duplicate ASIN)
- – Incorrect Product Identifier
- (Insert Incorrect UPC/EAN)
- Here is the path forward to fix this issue:
- (insert Correct UPC/EAN) is now assigned to (insert original ASIN)
- We need to integrate the ASINs first and the target should be (insert original ASIN)
- Then cleave the offers with incorrect (Insert Incorrect UPC/EAN)

*NOTE: Make sure to keep (insert original ASIN)*

**Template B:**

UPC (insert correct UPC) is now properly assigned to (insert original ASIN).

We still see the old UPC (insert old UPC).

Please DELETE and remove all of the offers under UPC (insert old UPC) because the old UPC belongs to Oasis Trading Co. Inc.

The correct UPC 850053374708 is the correct UPC that belongs to Himalayan Secrets

(Our registered brand and the correct brand of the listing)

Kindly check the provided GS1 certificate and the manufacturer's website link/images showing the correct UPC code of ASIN B0BPK27519.

We have also provided the screenshot of the incorrect UPC from the gs1 database:

- Provide GS1 Certificate
- Real-world product packaging images displaying the correct UPC or manufacturer’s website link
- Screenshot of the Incorrect UPC displaying the incorrect brand taken from [https://www.gs1us.org/tools/gs1-company-database-gepir](https://www.gs1us.org/tools/gs1-company-database-gepir)

After Seller Support approved the changes, check the back end of the listing and see if the correct UPC is displayed on the product information. If not, Upload a partial update feed file using the correct UPC as the product ID.

If UPC code does not get reflected on the backend, and/or the old UPC is still present, reopen the case. This task requires lots of back and forth with the Seller Support and 85-90% of the time, they reject your requests. I suggest being persistent and keep creating cases until it is resolved. Most of the representatives in the seller support team are not aware of a solution to fix this issue or they are not willing to help.

**Common Issues we may Encounter During the UPC Change Process in Listings:**

1. Received an error 8056 & 13013 when creating a duplicate listing for UPC change.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-W5DN5XEQ.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/bCvimage.png)

Amazon might prohibit the use of the new UPC, during duplicate creation, to fix you can try;

- Try to use a random SKU for the duplicate ASIN, if errors still persist proceed with step B.
- Create a case using the template attaching the Letter of Affiliation, real world images, GS1 Certificate and Manufacturer link of the product (if any);

“Amazon, we are currently listing a new product but received an error 8056 & 13013, we have attached our products Letter of affiliation, real world images, GS1 certificate & manufacturer’s website. Please investigate and enable our UPC”

Batch ID: 018xx”

*AS Note: This will take several back & forth with Seller Support and is time-consuming. Most of the representatives in the seller support team are not aware of a solution to fix this issue or they are not willing to help.*

**2. Duplicate ASIN and Original ASIN cannot be merged.**

Make sure that;

- Both listings are active
- Both listings have the same attributes,

You can push a full update on the original ASIN and the duplicate ASIN with a full update to make sure all the attributes are correct. Get the batch ID and submit it to seller support when sending another appeal for ASIN merge

**3. Amazon might create a new ASIN under the original SKU and the original listing will be in the “fix stranded” inventory.**

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/RrGimage.png)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-5D1J0257.png)**A. Search the suppressed SKU in the “fix stranded” list.**

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/1q5image.png)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-TZWHIEG3.png)**B. To fix the issue, delete the search suppressed ASIN (The ASIN that Amazon has created).**

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/UxLimage.png)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-3NCY33Q3.png)*It may take up to 5- 15 minutes to take effect.*

*Make sure that it is deleted, you can search the SKU to double check if it is no longer in the manage inventory.*

**C. Next step is to relist the original listing, you can relist it from the fix stranded Inventory page or add it manually.**

**Proceed to B if we don't have access to fix Stranded Page**

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-O8SBHZNZ.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ey9image.png)

1. To Fix a stranded inventory, just look for the original ASIN and click on Create New Listing.
2. It will redirect you to a page to recreate the listing and just fill in the price and click Save and Finish.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-F0WEWUIM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ljoimage.png)

It may take up to 5- 15 minutes to take effect and see the original listing back to inventory.

**How do we know if it’s fixed?**

- The listing should disappear from stranded inventory and ASIN should show as “Active” in your inventory.

We welcome your feedback for improvement. Please click**[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Vadimage.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/M5Limage.png
- 3. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-M121CN6H.png
- 4. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-JEUTBFO1.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/9Lyimage.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Lizimage.png
- 7. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-W5DN5XEQ.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/bCvimage.png
- 9. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/RrGimage.png
- 10. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-5D1J0257.png
- 11. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/1q5image.png
- 12. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-TZWHIEG3.png
- 13. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/UxLimage.png
- 14. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-3NCY33Q3.png
- 15. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-O8SBHZNZ.png
- 16. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ey9image.png
- 17. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/image-F0WEWUIM.png
- 18. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ljoimage.png
