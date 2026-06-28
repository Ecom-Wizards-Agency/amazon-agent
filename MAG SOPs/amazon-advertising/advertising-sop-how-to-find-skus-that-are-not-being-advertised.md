---
title: "Advertising SOP: How to find SKUs that are not being advertised"
category: "Amazon Advertising"
source_url: "https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-how-to-find-skus-that-are-not-being-advertised"
captured_at: "2026-05-12T07:07:49Z"
---

# Advertising SOP: How to find SKUs that are not being advertised

Source: https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-how-to-find-skus-that-are-not-being-advertised

## **How to find SKUs that are not being advertised**

**Who is this for :** This is for individuals who would like to find SKUs that are not yet being advertised on their accounts

**Objective :** To provide a step-by-step guide on how to find SKUs that are not being advertised on your pay-per-click campaigns.

**Instructions:**

**Step 1:** Download the last 60 days' bulk file.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Jaeimage.png)

**Step 2:**Open Excel and build a pivot table using SP data, click Insert, and click Pivot Table

- SKU - add as row
- Spend - add as value
- Sales - add value

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/N4dimage.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/QCiimage.png)

**Step 3:**Copy all SKUs you have and paste them to a new sheet column B

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FKhimage.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/kYyimage.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Wh0image.png)

**Step 4:** Generate an Active Listing Report. Go to Inventory Report Tab > Select Report Type: Active Listing Report

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Wwcimage.png)

**Step: 5:** By default, the generated Active Listing Report will be in a .txt format, copy all of the information on the .txt file and paste it on a new sheet.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/S44image.png)

**Step 6:** After pasting the .txt file to a new sheet, copy all SKUs from the active listing inventory report in column A together with the SKUs from the bulk file

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/G9Qimage.png)

**Step 7:**On Column C, apply the formula below.

- =IFERROR(IF(VLOOKUP(A2,$B$2:$B,1,0)=A2, "Advertised",0), "Not being advertised")

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Cneimage.png)

**Step 8:** Filter Column C and Select "Not being advertised" to find all the SKU

FAQs

- Q1: What tools or files are required for this process?

  - A1: You will need:

    - The last 60 days' bulk file.
    - Excel or a similar spreadsheet tool.
    - An Active Listing Report (accessible from the Inventory Report Tab).

- Q2: What is the step-by-step process to identify non-advertised SKUs?

  - A2: Steps

    - Step 1: Download the last 60 days' bulk file.
    - Step 2: Open Excel and create a pivot table using SP (Sponsored Products) data:

      - Add SKU as a row.
      - Add Spend and Sales as values.
    - Step 3: Copy all SKUs from the pivot table and paste them into a new sheet (Column B).
    - Step 4: Generate an Active Listing Report:

      - Go to the Inventory Report Tab.
      - Select Report Type: Active Listing Report.
    - Step 5: Open the generated Active Listing Report (a .txt file) and paste its content into a new Excel sheet.
    - Step 6: Combine SKUs from the Active Listing Report (Column A) and bulk file (Column B).
    - Step 7: Use the following formula in Column C to determine the status of each SKU:

      - =IFERROR(IF(VLOOKUP(A2,$B$2:$B,1,0)=A2, "Advertised",0), "Not being advertised" )

- Q3: How do I interpret the results in Column C?

  - A3: "Advertised": The SKU is included in your PPC campaigns.

    - "Not being advertised": The SKU is not currently included in your PPC campaigns.

- Q4: What should I do after identifying non-advertised SKUs?

  - A4: You can decide whether to include the non-advertised SKUs in your PPC campaigns, depending on their performance and advertising strategy.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Jaeimage.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/N4dimage.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/QCiimage.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FKhimage.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/kYyimage.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Wh0image.png
- 7. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Wwcimage.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/S44image.png
- 9. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/G9Qimage.png
- 10. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Cneimage.png
