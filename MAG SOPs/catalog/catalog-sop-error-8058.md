---
title: "Catalog SOP: Error 8058"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-8058"
captured_at: "2026-05-12T07:07:49Z"
---

# Catalog SOP: Error 8058

Source: https://sop.myamazonguy.com/books/catalog/page/catalog-sop-error-8058

## **Error 8058**

**Who is this for :** All individuals who received error 8058 while updating a listing using a flat file.

**Objective :** To ensure that all are equipped to resolve error code 8058, they need to understand how to troubleshoot it.

**Instructions:**

The error occurs when you have missing attributes for the specified field name in your inventory file template.

Amazon describes this as an error that occurs when an invalid value for a certain field name is provided in the inventory file template.

We will use the feed file below as an example. This task requires a full update to fix an error in the Product Detail Page.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.36%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/AQVimage.png)

You have the option to download the uploaded template and review the attributes that have been impacted by accessing the Feed Processing Summary tab within the template.

The Feed Processing Summary will show “Some attributes are missing for SKU:[50-01-00]”. However, the summary will not specify which attributes are missing and from what column.

1. To fix this, go to Inventory and click Manage All Inventory.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.43%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/zPUimage.png)

1. Search for the SKU or the ASIN that you need to fix. Then, click on Edit.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.51%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/3m4image.png)

3. The Detail Page will show you which Tab has the missing attributes.

- For example, the missing attributes are found on the Compliance Tab. Click on the Tab and look for the error.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.58%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/HC1image.png)

The missing attribute could be "Item_weight_unit_of_measure". This field is required because there is a value for Item Weight.

1. Complete the missing attributes, then click on Save and Finish.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.47.06%E2%80%AFAM.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/lhUimage.png)

1. Open the Inventory File Template again and add the missing attribute. Then re-upload the file.

You should be able to successfully add the file without any errors.

Note: If you can’t find any errors in the backend, you may need to file a Case and ask Support to identify the missing attribute in the feed file.

FAQs

**1. What does Error 8058 mean, and how do I know which attributes are missing?**

- Error 8058 occurs when an inventory file template has missing or incorrect attributes for one or more fields. It’s usually due to a required field being left blank or an invalid value being entered. The Feed Processing Summary tab can help you identify which SKU(s) are affected, but it won’t specify the exact missing attributes. You’ll need to go through the inventory file or check the detail page for the affected product to locate the missing field(s).

**2. How do I access the Feed Processing Summary, and what does it show?**

- The Feed Processing Summary can be found in the template you uploaded. This summary shows which SKU(s) have missing or invalid attributes but won’t identify the specific field. Look for messages like “Some attributes are missing for SKU:[50-01-00]” to understand which products are affected. You’ll still need to manually check the associated attributes for those products.

**3. What are some common attributes that can cause Error 8058?**

- While the missing attribute could vary, a common example is Item_weight_unit_of_measure, which becomes a required field if Item Weight is filled in the inventory file. Other typical missing attributes could include Product Type, Brand, Material, or Compliance details. You should check the detail page of the product or your inventory file template to identify which field is incomplete.

**4. How do I find missing attributes on the product’s detail page?**

- To find missing attributes, go to Manage All Inventory and search for the SKU or ASIN causing the error. Then click on Edit. The Detail Page will show you which tab has missing or incomplete fields (such as Compliance, Product Details, etc.). If the missing field is not immediately visible, it might be under a specific tab like Compliance or Shipping.

**5. What should I do if I can't find the missing attribute in the backend?**

- If you can’t find the missing attribute after checking the Detail Page, the next step is to file a case with Amazon Seller Support. Provide them with your inventory file and details about the error, and they should help you identify the missing attribute(s). Be sure to include as much detail as possible in your case to help them assist you faster.

**6. How can I fix the missing attributes in my inventory file?**

- Once you’ve identified the missing attribute(s) through the product detail page, go back to your Inventory File Template and add the missing information in the appropriate field(s). Then, re-upload the updated file to Amazon Seller Central. Be sure to save the file in the correct format (e.g., CSV or Excel) before uploading.

**7. What should I do after I’ve re-uploaded the inventory file?**

- After re-uploading your inventory file, you should check the Feed Processing Summary again to ensure that there are no more errors. If the upload was successful, you should see no error messages related to the SKU or ASIN you fixed. If errors persist, it may indicate that there are additional missing fields or issues that need to be addressed.

**8. How do I handle multiple missing attributes in one inventory file?**

- If you’re dealing with multiple missing attributes in the same inventory file, you’ll need to go through each affected SKU and review the relevant fields. The process is the same: access Manage All Inventory, edit the SKU(s), and check each tab to find the missing information. Once all the attributes are added, re-upload the file and verify that the issue is resolved.

**9. How can I ensure I don’t encounter Error 8058 in the future?**

- To avoid Error 8058 in the future, always double-check your inventory file for any missing or incorrectly entered attributes before uploading it. Ensure that all required fields are filled out, especially those linked to Product Weight, Compliance, or Shipping information. You can also use Amazon's template validation tools to help ensure all necessary attributes are included before submission.

**10. How do I contact Amazon Seller Support if I can’t resolve the issue?**

- If you’ve followed the steps to troubleshoot Error 8058 but are still unable to find the missing attribute(s), you may need to contact Seller Support. To file a case, go to Seller Central, select Help, and choose Contact Us. Provide a detailed description of the issue, including your inventory file and any error messages, so they can assist you effectively.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.36%E2%80%AFAM.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/AQVimage.png
- 3. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.43%E2%80%AFAM.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/zPUimage.png
- 5. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.51%E2%80%AFAM.png
- 6. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/3m4image.png
- 7. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.46.58%E2%80%AFAM.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/HC1image.png
- 9. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-30%20at%201.47.06%E2%80%AFAM.png
- 10. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/lhUimage.png
