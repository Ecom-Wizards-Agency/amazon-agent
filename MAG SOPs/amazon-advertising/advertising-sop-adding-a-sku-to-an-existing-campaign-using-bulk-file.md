---
title: "Advertising SOP: Adding a SKU to an Existing Campaign Using Bulk File"
category: "Amazon Advertising"
source_url: "https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-adding-a-sku-to-an-existing-campaign-using-bulk-file"
captured_at: "2026-05-12T07:07:49Z"
---

# Advertising SOP: Adding a SKU to an Existing Campaign Using Bulk File

Source: https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-adding-a-sku-to-an-existing-campaign-using-bulk-file

## **Adding a SKU to an Existing Campaign Using Bulk File**

**Who is this for?**

This SOP is intended for advertising specialists managing Amazon Sponsored Products campaigns and aims to guide them in efficiently adding a SKU to campaigns using bulk uploads.

**Objective:**

This procedure outlines the steps to add a specific SKU to an existing Amazon campaign using a bulk file.

**Steps:**

**1. Request a Bulk File:**

- **Navigate to Bulk Files**: Open the Bulk Files section of your Amazon Advertising account.
- **Set the Date Range**: You can choose any date range. We recommend just choosing yesterday since it will be faster to be available for download
- **Select Filters**:

  - Ensure the filter options **Campaign Items with Zero Impressions** and **Sponsored Products Data** are checked. These are the only essential criteria.
- **Generate File**: Click on **Create Spreadsheet for Download** and wait for the file to be available for download.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ASjimage.png)

**2. Download the File:**

- Once the file is ready, click **Download** to save it.
- Open the file once the download is complete.

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/929image.png)

**3. Prepare the Bulk File:**

- **Open the Sponsored Products Campaigns Tab**: In the file, navigate to the **Sponsored Products Campaigns** tab.
- **Enable Filters**:

  - Press **Ctrl + Shift + L** to enable filtering.
  - If this does not work, go to the **Home** tab in Excel, click on **Sort & Filter**, and then choose **Filter**.

**4. Filter Data:**

- **Filter by Product Ad**:

  - Find **Column B** labeled "Entity".
  - From the dropdown menu, unselect everything except **Product Ad**.
  - Click **OK**.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/cl1image.png)

- **Filter by ASIN**:

  - In **Column W**, locate the ASIN of the product to which you want to add the new SKU.
  - Copy the ASIN and paste it into the filter field in **Column W**.
  - Click **OK** to apply the filter.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/GgYimage.png)

- **Filter by SKU**:

  - Ensure that the SKU is unique. If there are multiple SKUs for the same ASIN, make sure to filter by the specific SKU you want to add.

    ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/8hMimage.png)

**5. Modify the File:**

- **Remove Paused Data**: In **Columns R, S, and T**, remove any paused data, unless you intend to include paused information for the SKU. This data is generally unnecessary when adding a new SKU.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/mdYimage.png)

- **Copy the Filtered Data**:

  - After filtering, select all and copy them by pressing **Ctrl + C**.
  - Open a new sheet by pressing **Ctrl + N** in Excel and paste the copied data into this new sheet using **Ctrl + V**.

**6. Adjust the File for Upload:**

- **Operation Field**:

  - In the new sheet, find the **Operation** column and set the value to **Create**. This will tell Amazon to add the new SKU to the campaign.

    ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fZsimage.png)

- **Auto-Populate**:

  - Auto-populate the operation for all rows in the sheet by filling down the **Operation** column.
- **Update the SKU**:

  - In the **SKU** column, replace the placeholder SKU with the SKU you want to add.
  - Copy the new SKU and paste it down the entire column to apply it to all rows.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Dl2image.png)

**7. Finalize and Save:**

- Once all adjustments are made, save the file with a relevant name and ensure it is saved in a location on your computer where you can easily find it.

> **⚠️IMPORTANT! Make sure you have all of the items checked before uploading:⚠️**
>
> - **Before Copy-Pasting Data:**
>
>   - Ensure **no filters** are selected when copying into a sheet with formulas.
>   - Remove any data where bids were not change before copying.
>   - Always use **Copy → Paste → Values** to prevent formula errors.
> - **Formatting & Accuracy:**
>
>   - Check **decimal place formatting** to avoid converting cents into whole dollars.
>   - Verify **daily budget decimal formatting** in the campaign column.
>   - Double-check **margins on new bids** (especially if using drag-to-copy).
> - **Data Validation:**
>
>   - Compare the **new sheet vs. the old sheet** to ensure bid changes were applied correctly.
>   - Verify that each keyword correctly corresponds to its intended bid before uploading.
>   - Ensure that no keywords are mismatched with incorrect bids.
>   - Ensure columns **R, S, and T** are **filtered to "Enabled"**.
> - **Final Upload Process:**
>
>   - Upload **every bulk file** to the **Asana task** before marking it complete.
>   - For **large bulk files**, upload to the **client’s folder** and paste the link in the Asana task comments.

**8. Upload the Bulk File:**

- Return to the **Bulk File** section in your Amazon Advertising account.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/19xsY3image.png)

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ASjimage.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/929image.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/cl1image.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/GgYimage.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/8hMimage.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/mdYimage.png
- 7. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/fZsimage.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Dl2image.png
- 9. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/19xsY3image.png
