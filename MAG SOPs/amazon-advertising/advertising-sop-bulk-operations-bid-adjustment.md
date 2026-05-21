---
title: "Advertising SOP: Bulk Operations - Bid Adjustment"
category: "Amazon Advertising"
source_url: "https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-bulk-operations-bid-adjustment"
captured_at: "2026-05-12T07:07:49Z"
---

# Advertising SOP: Bulk Operations - Bid Adjustment

Source: https://sop.myamazonguy.com/books/amazon-advertising/page/advertising-sop-bulk-operations-bid-adjustment

## **Bulk Operations - Bid Adjustment**

**Who Is This For :**This SOP is designed for advertising managers, digital marketers, or professionals responsible for optimizing ad campaigns using Amazon's bulk operations bid adjustments.

**Objective :**To provide clear and structured guidelines for effectively managing bid adjustments in bulk operations, ensuring efficiency and consistency.

**Steps for Bulk Operations - Bid Adjustment**

Preparing the Bulk File

1. Understand the Two-Day Attribution Window:

  - Exclude data from the last two days when downloading bulk operations to ensure accuracy (e.g., if today is November 25, download data from October 23 to November 23).
2. Download the Bulk File:

  - In the Campaign Manager, select a date range ending two days ago.

    ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%202.51.52%E2%80%AFAM(1).png)

    ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JgCimage.png)
  - Exclude the following from the bulk file by selecting the appropriate options:

    - Terminated Campaigns
    - Placement Data for Campaigns
    - Brand Assets Data

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%202.52.01%E2%80%AFAM.png)

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FSIimage.png)
3. Save and Name the File:

  - Use consistent naming conventions:

    - [Account Name][Start Date][End Date]_[Download Date]

      - Example: BentlySeeds_2023-10-01_2023-10-31_2023-11-25
4. Backup the Original File:

  - Always save a copy of the original file before making changes.

**Preparing the Spreadsheet**

**Filter for Enabled Campaigns: (columns R,S,T)**

1. Use filters to show only campaigns with Enabled statuses in the State, Campaign State, Ad Group State

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%202.57.54%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/9SPimage.png)

1. Add a new column “New Bid” after the “Bid” Column (Column AB)

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%203.04.18%E2%80%AFAM.png)

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/H6Nimage.png)

**Optimizing Bids**

1. Review Target ACOS:

  - Know the target ACOS for the account before making adjustments.
2. Filter for ACOS:

  - Sort the ACOS column in descending order. Highlight targets significantly above the target ACOS.
3. Make Bid Adjustments:

  - High ACOS Targets: Reduce bids.

    - Example: Multiply CPC by 0.5 (reduce by 50%).
  - Low ACOS Targets: Consider increasing bids.

    - Example: Multiply CPC by 1.20 (increase by 20%).
  - No Sales After 20 Clicks: Reduce bids or pause these targets.
  - Low Impressions (Less than 70 in 7 Days): Increase bids by a small amount (e.g., $0.02–$0.05).
4. Update the 'New Bid' Column:

  - Apply adjustments to calculate the New Bid value.

**Finalizing and Uploading**

1. Document Changes:

  - Use the operation columns to describe changes (e.g., "Reduced by 10% for high ACOS").

  ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%203.00.20%E2%80%AFAM.png)

  ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Mfaimage.png)
2. Save and Rename the File:

  - Use the following format:

    - [Account Name]SP_BulkUpload[Action]_[Date]

      - Example: BentlySeeds_SP_BulkUpload_Adjustments_2023-11-25

> 1. Before uploading your bulk file make sure to check the following
>
>   - **Before Copy-Pasting Data:**
>
>     - Ensure no filters are selected when copying into a sheet with formulas.
>     - Remove any data where bids were not change before copying.
>     - Always use Copy → Paste → Values to prevent formula errors.
>   - **Formatting & Accuracy:**
>
>     - Check decimal place formatting to avoid converting cents into whole dollars.
>     - Verify daily budget decimal formatting in the campaign column.
>     - Double-check margins on new bids (especially if using drag-to-copy).
>   - **Data Validation:**
>
>     - Compare the new sheet vs. the old sheet to ensure bid changes were applied correctly.
>     - Verify that each keyword correctly corresponds to its intended bid before uploading.
>     - Ensure that no keywords are mismatched with incorrect bids.
>     - Ensure columns R, S, and T are filtered to "Enabled".
>   - **Final Upload Process:**
>
>     - Upload every bulk file to the Asana task before marking it complete.
>     - For large bulk files, upload to the client’s folder and paste the link in the Asana task comments.

3. Upload the File:

- In the Campaign Manager, upload the updated file. Ensure the status shows “Successfully Completed.”

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ctMimage.png)

4. Handle Errors:

- If errors occur, review the attached error report, fix issues, and re-upload the file.

5. Verify Changes:

- Manually check one or two campaigns to confirm bid updates.

**Weekly Check-In**

1. Create a Summary Log:

  - Use the following structure to document changes:

    - Target: The keyword/ASIN adjusted.
    - Action: Reduced, increased, or paused.
    - Campaign Name: The associated campaign.
  - Combine these into a summary statement:

    - Example: “Target ‘back pain’ reduced bid in campaign SP-KW-Broad Phrase Exact by 10%.”
2. Review Campaign Performance:

  - Track metrics like ACOS, CTR, and ROAS to assess the effectiveness of adjustments.

**Final Notes**

- Contextual Analysis Is Key: Always consider broader campaign context before making drastic changes.
- Consistency Matters: Follow these steps for every bid adjustment session to ensure accuracy and efficiency.

By implementing this structured process, you can optimize bids more effectively, ensuring better campaign performance and improved ROI.

FAQs

##### **FAQs**

- **Q1: Why should data from the last two days be excluded?**

  - **A1:**Amazon uses a **two-day attribution window**, meaning recent clicks or impressions may not yet be fully attributed to sales.
  - Excluding the last two days ensures more accurate data analysis.
- **Q2: What are the guidelines for making bid adjustments?**

  - **A2: High ACOS Targets:**

    - Reduce bids.
    - Example: Multiply CPC by 0.5 (reduce by 50%).
  - **Low ACOS Targets:**

    - Increase bids.
    - Example: Multiply CPC by 1.20 (increase by 20%).
  - **No Sales After 20 Clicks:**

    - Reduce bids or pause the targets.
  - **Low Impressions (<70 in 7 Days):**

    - Slightly increase bids (e.g., by $0.02–$0.05).
- **Q3: What should I consider before making bid adjustments?**

  - **A3:**Know the **target ACOS** for the account.
  - Analyze broader campaign metrics and goals.
  - Document changes in the **operation columns** to track adjustments.
- **Q4: How do I update the "New Bid" column?**

  - **A4:**Apply bid adjustments directly to the **"New Bid"** column based on the above rules.
- **Q5: How should I save and upload the updated file?**

  - **A5:**Save the file with the format:

    - [Account Name]SP_BulkUpload[Action]_[Date]
    - Example: `BentlySeeds_SP_BulkUpload_Adjustments_2023-11-25`.
  - Upload the file in **Campaign Manager**.
  - Confirm the status as “Successfully Completed.”
- **Q6: What should I do if errors occur during the upload?**

  - **A6:**Download and review the attached error report.
  - Fix the issues and re-upload the corrected file.
- **Q7: How can I verify that changes were applied?**

  - **A7:**Manually check one or two campaigns to confirm that bid updates were applied correctly.
- **Q8: How do I document changes for weekly check-ins?**

  - **A8:** Use a **summary log** with these details:

    - **Target:** The adjusted keyword/ASIN.
    - **Action:** Reduced, increased, or paused.
    - **Campaign Name:** The associated campaign.
  - Example Summary: “Target ‘back pain’ reduced bid in campaign SP-KW-Broad Phrase Exact by 10%.”
- **Q9: How should I review campaign performance after adjustments?**

  - **A9:**Track key metrics such as:

    - **ACOS** (Advertising Cost of Sales).
    - **CTR** (Click-Through Rate).
    - **ROAS** (Return on Ad Spend).
  - Assess whether adjustments improved performance and ROI.
- **Q10: What are the key considerations for successful bid adjustments?**

  - **A10: Contextual Analysis:** Always consider the campaign’s broader performance metrics before making significant changes.
  - **Consistency:** Follow the same structured process for every bid adjustment session to maintain accuracy and efficiency.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%202.51.52%E2%80%AFAM(1).png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JgCimage.png
- 3. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%202.52.01%E2%80%AFAM.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/FSIimage.png
- 5. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%202.57.54%E2%80%AFAM.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/9SPimage.png
- 7. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%203.04.18%E2%80%AFAM.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/H6Nimage.png
- 9. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-18%20at%203.00.20%E2%80%AFAM.png
- 10. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Mfaimage.png
- 11. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ctMimage.png
