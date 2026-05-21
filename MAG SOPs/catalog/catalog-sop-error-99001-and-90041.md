---
title: "Catalog SOP: Error 99001 and 90041"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-99001-and-90041"
captured_at: "2026-05-12T07:07:49Z"
---

# Catalog SOP: Error 99001 and 90041

Source: https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-99001-and-90041

## **Error 99001 and 90041**

**Who is this for :** All individuals who are encountering 99001 and 90041 errors.

**Objective :** To identify mandatory attributes, supply valid values for mandatory attributes, and enable the successful upload of the flat file.

If mandatory attributes are missing or an incorrect value is supplied in your feed file, you will receive error 99001.

To identify these mandatory values, open your feed file template, then input the product type category. The selected category's required fields will be marked in red, as seen below.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-29%20at%204.00.10%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/re0image.png)

**Instructions:**

1. For unsuccessful uploads. Download the flat file report by clicking on the Download your Processing Report link.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Ocdimage.png)

2. Open the downloaded report Excel file to determine the error code. Read the error message.

Below is the sample 99001 error message.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JULimage.png)

3. Below is a screenshot of the processing report with the 99001 error. Locate all cells in the template that were highlighted in orange. This would tell you that the value stored in these fields is either invalid or missing.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Uyximage.png)

In this example, the category “Home & Kitchen › Kitchen & Dining" was used, wherein the Model and Model Name attributes (highlighted in orange) were required values but were not filled out on the initial flat file load.

4. Rework your flat file by providing the correct values for Model and Model Name attributes. Reach out to the brand manager and ask for the Model and Model Name for each child or standalone SKU if you can’t find them in the backend. Save and resubmit the flat file.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/jXKimage.png)

FAQs

**1. What is Error 99001, and why does it occur?**

- Error 99001 occurs when mandatory attributes in your flat file are either missing or contain invalid values. These attributes are essential for successfully processing and uploading your flat file.

**2. What is Error 90041, and how is it different from 99001?**

- Error 90041 typically indicates an invalid or unsupported value in your flat file. While 99001 focuses on missing required fields, 90041 emphasizes the need for valid values in specific fields.

**3. How can I identify the mandatory attributes for my product category?**

- Mandatory attributes are marked in red in the flat file template. To locate them:

  - Open the flat file template.
  - Select the appropriate product type category.
  - Review the red-highlighted fields.

**4. How do I download the processing report to investigate errors?**

- After an unsuccessful upload, click on the Download your Processing Report link in Seller Central.
- Save the file and open it in Excel to review the error details.

**5. What should I look for in the processing report when encountering 99001 or 90041 errors?**

- Look for:

  - Error code: Locate 99001 or 90041 in the report.
  - Error message: Describes the issue (e.g., missing or invalid values).
  - Highlighted fields: Orange-highlighted fields indicate the problematic attributes.

**6. What should I do if I cannot find the required attribute values?**

- If you cannot locate the required values:

  - Check the Seller Central backend for relevant data.
  - Reach out to the brand manager or POC for the missing information.
  - Ensure the values are valid and align with Amazon’s guidelines.

**7. How can I avoid Error 99001 in the future?**

- To prevent Error 99001:

  - Always use the most recent flat file template.
  - Verify all red-highlighted fields are filled with valid data before uploading.
  - Double-check category-specific requirements.

**8. Can Error 90041 occur if mandatory fields are filled?**

- Yes, Error 90041 occurs even if mandatory fields are filled but contain unsupported or incorrect values. For example, entering text in a numerical field or using invalid characters.

**9. How do I validate values in my flat file to prevent Error 90041?**

- Refer to the Valid Values tab in the flat file template for acceptable inputs.
- Avoid unsupported characters (e.g., symbols, excessive whitespace).
- Follow Amazon’s formatting guidelines for specific attributes.

**10. What happens if I ignore these errors and don’t re-upload the flat file?**

- Ignoring these errors will result in your product listings not being updated or uploaded. This could lead to incomplete or inaccurate product data in Amazon’s catalog.

**11. Can I re-upload the same file after fixing errors?**

- Yes, once you’ve corrected the errors, save the updated flat file and re-upload it to Seller Central.

**12. How do I ensure my flat file is correctly formatted before uploading?**

- Use the most recent flat file template from Seller Central.
- Verify all mandatory fields are filled.
- Cross-check data against the Valid Values tab.
- Save the file in its original format (e.g., Excel .xlsx).

**13. What should I do if I repeatedly encounter the same error codes?**

- If the same errors persist:

  - Review your flat file for consistent issues (e.g., missing or invalid fields).
  - Consult Amazon’s Seller Support for further guidance.
  - Confirm you’re using the correct product category and flat file template.

**14. Are there specific categories prone to these errors?**

- Certain categories with detailed attribute requirements (e.g., Electronics, Home & Kitchen) may be more prone to errors. Always refer to the Valid Values tab and category-specific instructions.

**15. How long does it take for updates to reflect after resolving errors?**

- Updates typically take 15 minutes to 24 hours to reflect after a successful upload. Monitor the status in Seller Central to confirm.

**16. Can I partially update the flat file to resolve errors?**

- Yes, you can use a Partial Update to modify only the fields causing errors without affecting other attributes.

**17. What should I do if mandatory attributes change after I’ve submitted the file?**

- If Amazon updates mandatory attributes for a category:

  - Download the latest flat file template.
  - Update your flat file to include the new mandatory fields.
  - Re-upload the updated file.
  - 18. How can I track the status of my upload after fixing errors?
  - Go to Catalog > Add Products via Upload > Upload Status in Seller Central. Monitor the progress and check for any new errors.

**19. What is the best way to handle bulk updates with potential errors?**

- For bulk updates:

  - Break the updates into smaller batches for easier troubleshooting.
  - Validate each batch using the Processing Report.
  - Correct errors before proceeding with additional uploads.

**20. Can Amazon Seller Support help resolve persistent errors?**

- Yes, if errors persist after multiple attempts, contact Amazon Seller Support. Provide the following details:

  - Error codes (e.g., 99001, 90041).
  - Processing Report.
  - Flat file used for the upload.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-29%20at%204.00.10%E2%80%AFAM.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/re0image.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Ocdimage.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/JULimage.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Uyximage.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/jXKimage.png
