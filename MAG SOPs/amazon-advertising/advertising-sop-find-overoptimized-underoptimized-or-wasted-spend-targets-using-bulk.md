---
title: "Advertising SOP: Find Overoptimized, Underoptimized, or Wasted Spend Targets Using Bulk"
category: "Amazon Advertising"
source_url: "https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-find-overoptimized-underoptimized-or-wasted-spend-targets-using-bulk"
captured_at: "2026-05-12T07:07:49Z"
---

# Advertising SOP: Find Overoptimized, Underoptimized, or Wasted Spend Targets Using Bulk

Source: https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-find-overoptimized-underoptimized-or-wasted-spend-targets-using-bulk

## **Finding Over Optimized, Under Optimized, and Non-Converting Targets with High Ad Spent Using Bulk File**

**Who is this for :** Amazon Advertising Specialist who wants to find targets that are Overoptimized, Underoptimized and Non-Converting Targets with high Ad spent using Bulk File

**Objective :**To provide a step-by-step guide on how to easily find targets that are over-bidding, under-bidding, and non-converting for Optimization

**Procedure**

**Step 1 :**Download a bulk file for a date range that you choose - preferably 30 days of data.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-10-14%20141932.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/yLvimage.png)

**Step 2 :** Open and apply the Macro filter ( CTRL + SHIFT + Q) If you haven't utilized the macro yet, please refer to the Advertising SOP for Excel Macro Usage: Streamlining Bulk File Filtering and Bulk Optimizations.

**Step 3 :**Targets are now sorted by ACOS and wasted ad spend. We also have new columns here: Min, Max, and Bidding Strategy. For Min and Max: These columns calculate the minimum/lowest and maximum/highest values of the two data points, CPC and Current Bid.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-04-03%20at%203.47.52%E2%80%AFAM%20(1).png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/QS8image.png)

**Step 4 :** Looking for High/Low ACOS targets.

- Arrange it based on the bidding strategy (in our example above, I opted for down only bidding first)

**For Down Only:** If looking for high ACOS targets, check if your MIN matches your current bid. That means your Max indicates your CPC, helping you decide if the bids are acceptable or if a further reduction is necessary. If your MIN is your CPC, then you have to pull the ACOS down.

If looking for low ACOS targets, confirm if your MAX aligns with your current bid. That means your Min signifies your CPC, assisting you in assessing whether the bids are satisfactory or if additional bid enhancement is required. If your MAX is your CPC, your current bid is low so you have to bid higher than your MAX.

**For Up and Down:**Seeking unoptimized Up and Down targets differs, as the Up and Down bidding strategy enables Amazon to increase your bid by up to 300%. Your adjustment is limited to the current bid, as the bid is multiplied, potentially raising your CPC beyond the current bid amount. For Fixed bids: Bids and average CPC should align, unless you've recently optimized your bids. Adjustments to bids here should be kept minimal, typically around 3 to 5 cents. If there's a significant difference between CPC and current bids, it indicates that bid adjustments have been made. Note: Please double check those campaigns with placement bid adjustment either manually or in bulk(after your bulk optimizations). Placement bid adjustments can increase your bids by up to 900%.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-04-03%20at%203.48.01%E2%80%AFAM(1).png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/L8Kimage.png)

**Step 5 :** Let's now move on to examining potential wasted ad spend. Filter out targets with zero orders and review the bids to ensure they are lower than the average CPC.

Establish criteria for identifying wasted ad spend, commonly done by taking the lowest product price and dividing it by 60%. For instance, if the product price is $19.99, the calculation would be $19.99 * 0.60 = $11.99. This becomes the initial benchmark for bid reduction. Alternatively, you can begin with a straightforward approach, such as starting with $5 or $10 for wasted ad spend. If the wasted ad spend is pretty huge, you can consider pausing it.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-04-03%20at%203.48.12%E2%80%AFAM(1).png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/VzAimage.png)

In the screenshot above you will see that I have already adjusted my Current Bid lower than my CPC in order to reduce the ad spending on these targets that are overspending and not getting any sales.

**Step 6 :** Once you’re done with your bid adjustments, remove the blank cells on your “new bid” column. Press Ctrl + shift + N so your filtered workbook will get transferred to a new workbook. This macro will also automatically put “update” under the operation column.

**Step 7 :**Now, all you have to do is copy the bids from the “new bid” column and paste that to the bid column.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-03-23%20053254.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/tJ8image.png)

**Step 8 :** You can now save the file and upload it.

> **IMPORTANT! Make sure you have all of the items checked before uploading:**
>
> - Before Copy-Pasting Data:
>
>   - Ensure **no filters** are selected when copying into a sheet with formulas.
>   - Remove any data where bids were not change before copying.
>   - Always use **Copy → Paste → Values** to prevent formula errors.
> - Formatting & Accuracy:
>
>   - Check **decimal place formatting** to avoid converting cents into whole dollars.
>   - Verify **daily budget decimal formatting** in the campaign column.
>   - Double-check **margins on new bids** (especially if using drag-to-copy).
> - Data Validation:
>
>   - Compare the **new sheet vs. the old sheet** to ensure bid changes were applied correctly.
>   - Verify that each keyword correctly corresponds to its intended bid before uploading.
>   - Ensure that no keywords are mismatched with incorrect bids.
>   - Ensure columns **R, S, and T** are **filtered to "Enabled"**.
> - Final Upload Process:
>
>   - Upload **every bulk file** to the **Asana task** before marking it complete.
>   - For **large bulk files**, upload to the **client’s folder** and paste the link in the Asana task comments.

FAQs

##### **FAQs**

**Using Macros**

- **Q1: How do I apply the Macro filter in Excel?**

  - **A1:** Use the shortcut `CTRL + SHIFT + Q` to apply the Macro filter. If the Macro isn’t set up yet, refer to the **Advertising SOP for Excel Macro Usage**.
- **Q2:** **What additional columns are added after applying the Macro filter?**

  - **A2:** New columns such as "Min," "Max," and "Bidding Strategy" are added. These help in determining bid ranges and evaluating the effectiveness of your bidding strategy.

**Bid Adjustment**

- **Q3: How should I evaluate high ACOS targets for "Down Only" bidding strategies?**

  - **A3:** For high ACOS targets, check if the "Min" value matches the current bid. If the "Min" aligns with the CPC, further reduce the bid to lower ACOS.
- **Q4:** **What adjustments are needed for low ACOS targets in "Down Only" bidding strategies?**

  - **A4:** Confirm if the "Max" value matches the current bid. If the "Max" aligns with the CPC, consider increasing the bid to enhance performance.
- **Q5: How do "Up and Down" bidding strategies differ from others?**

  - **A5:** In "Up and Down" strategies, Amazon can increase bids by up to 300%, and adjustments should primarily focus on the current bid without excessive reductions.
- **Q6:** **How should I approach bid adjustments for "Fixed Bids"?**

  - **A6:** Ensure the bid closely aligns with the CPC unless recent optimizations were made. Adjustments should be small, typically between 3-5 cents.

**Managing Wasted Ad Spend**

- **Q7:** **How do I identify wasted ad spend?**

  - **A7:** Filter for targets with zero orders. Establish criteria for bid reduction by calculating 60% of the lowest product price or starting with a simple threshold like $5 or $10.
- **Q8:** **What actions can be taken for targets with excessive wasted ad spend?**

  - **A8:** Lower the bids below the average CPC, or if the wasted spend is significant, consider pausing these targets altogether.

**Finalizing Adjustments**

- **Q9: What steps should be taken after bid adjustments?**

  - **A9:** Remove blank cells from the "New Bid" column and press `CTRL + SHIFT + N` to transfer filtered data to a new workbook. This Macro will also add "update" in the operation column.
- **Q10:** **How do I complete the process after transferring data to a new workbook?**

  - **A10:** Copy the values from the "New Bid" column and paste them into the "Bid" column. Save the file, ensuring it's formatted correctly, and upload it.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-10-14%20141932.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/yLvimage.png
- 3. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-04-03%20at%203.47.52%E2%80%AFAM%20(1).png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/QS8image.png
- 5. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-04-03%20at%203.48.01%E2%80%AFAM(1).png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/L8Kimage.png
- 7. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-04-03%20at%203.48.12%E2%80%AFAM(1).png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/VzAimage.png
- 9. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202024-03-23%20053254.png
- 10. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/tJ8image.png
