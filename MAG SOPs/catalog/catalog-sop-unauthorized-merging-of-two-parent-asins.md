---
title: "Catalog SOP: Unauthorized Merging of Two Parent ASINs"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/catalog-sop-unauthorized-merging-of-two-parent-asins"
captured_at: "2026-05-12T07:07:49Z"
---

# Catalog SOP: Unauthorized Merging of Two Parent ASINs

Source: https://sop.myamazonguy.com/books/catalog/page/catalog-sop-unauthorized-merging-of-two-parent-asins

## Unauthorized Merging of Two-Parent ASINs

**Who is this for :** This is intended for Account Specialists who will resolve the merging of two-parent ASINs that were not authorized.

**Objective :** The purpose of this is to provide guidance to Account Specialists regarding the correct process for separating two parent ASINs on Amazon's platform, to ensure that all required actions are carried out with precision and effectiveness.

**NOTE :** From time to time, Amazon will merge 2 variations and assign them to one of the two’s parent ASINs.

This is what it looks like on the Inventory Page:

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-25%20at%202.43.05%E2%80%AFAM.png)

[![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/iQsimage.png)](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/iQsimage.png)

This is what the parentage looks like in the Variation Wizard:

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-25%20at%202.43.14%E2%80%AFAM.png)

[![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Yzcimage.png)](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/Yzcimage.png)

There is no known reason why this happens at the moment. But by observation, this generally happens when 2 variations are closely similar or almost identical. The problem here is if the missing parent ASIN has an active set of child SKUs these child SKUs will appear inactive on the PDP–making the products unavailable to the buyers. This is an Amazon system glitch and we can only fix this using these 2 methods.

**Instructions:**

**Method 1 - Rebuilding Variations with Seller Support Assistance**

This is the best option when immediate action is needed:

- Pros: Faster option
- Con: Requires a lot of communication w/ Seller Support Catalog Dept, time-consuming

1. Keep the 2 merged Parent SKUs together so that all child listings will appear in the Variation Wizard. Seller Support will not see what our Inventory Page looks like, so they need to see what we’re talking about using the Variation Wizard.
2. File a case and document what happened. Attach a screenshot of your inventory page on the case.
3. Call Seller Support using the case you just opened and ask to be transferred to the Catalog Department.

  - Explain the situation by starting with “Amazon somehow merged 2 parent SKUs under 1 Parent ASIN. Please check the variation wizard so that you can see what I’m talking about.”
4. Ask them to manually delete the 2 Parent SKUs so that you can rebuild the entire parentage the way we want it to look. Do not accept their rebuttal when they say that you can delete these SKUs on your end. Simply say that you’ve tried doing it countless times and it did not work. Ask them to manually do it using their own tools and system so that when we rebuild the parentages again, we won't be picking up old parentage contributions.
5. After Seller Support deletes the 2 Parent SKUs, stay on the line. These changes will reflect immediately after 5 minutes. Do not end the call without seeing the two parent SKUs being broken apart or else you will have to start all over again.
6. Once you can see that the 2 parent SKUs have been broken up, you can now end the call and start rebuilding the variations, this time, under a different parent SKU. We need to create a different parent SKU in order to generate new Parent ASINs to avoid this incident from happening again.

Note: It will take you at least 2-3 calls before a seller support agent can really help you with the deletion. Do not give up after 2-3 tries.

**Method 2 - Delete and Relist for 24 hours**

We can use this method when immediate action is not needed.

- Pros: We don’t need to get Seller Support involved, convenient
- Con: It will take more than 24 hours to fix

If you’re not in a hurry to get this issue fixed, or if both parentages that got merged under 1 Parent ASIN have zero “0” inventory, we can opt for a delete-relist method. Ask the brand manager if they are okay with going through this method instead of method 1.

1. Simply delete both parent SKUs
2. Wait 24 hours
3. Rebuild the 2 variations using new Parent SKUs using a full update flat file (including the children SKUs)

For Full Update:

- We must ask for the client's permission to upload a full update feed file. Reach out to the POC or the client and ask for their permission. Explain why it is needed.
- Before uploading the full update feed file, you need to submit it to the team leader for QA.

Important notes to remember:

- Do not delete 1 SKU and leave the other. Both must be deleted and rebuilt using new SKUs
- Make sure you wait for a little over 24 hours before relisting the products
- Download a Category Listings Report for backup
- Use a full update flat file when re-listing

FAQS

**1. Why does Amazon merge two parent ASINs without authorization?**

- Amazon occasionally merges two parent ASINs when their variations are very similar or nearly identical. This is believed to be a system glitch and not the result of seller actions. However, the exact reason for these unauthorized merges is unknown.

**2. What are the consequences of merged parent ASINs?**

- When two parent ASINs are merged:

  - Child SKUs from the missing parent ASIN may become inactive on the product detail page (PDP), making them unavailable for purchase.
  - Inventory and sales may be negatively impacted until the issue is resolved.

**3. How can I confirm if two parent ASINs were merged?**

- Check the Variation Wizard in Seller Central. If the variations from two different parent ASINs appear under one parent, the ASINs have likely been merged.
- On the Inventory Page, the child SKUs for the missing parent ASIN will appear inactive.

**4. What should I do before attempting to fix merged parent ASINs?**

- Download a Category Listings Report to back up your existing listing data. This ensures you have a record of the original parent-child relationships and listing attributes before making changes.

**5. Which method should I use to resolve merged parent ASINs?**

- Use Method 1 (Rebuilding Variations with Seller Support Assistance) if immediate action is required, especially when inventory is active, and the products need to be available for purchase.
- Use Method 2 (Delete and Relist for 24 hours) if immediate action is not necessary, or if both parent ASINs have zero inventory.

**6. Why does Method 1 require involving Seller Support’s Catalog Department?**

- The Catalog Department has the necessary tools to manually delete the merged parent ASINs, which is not possible through Seller Central. This ensures the system removes all old parentage data, allowing you to rebuild the variations without legacy conflicts.

**7. What should I do if Seller Support denies my request to delete merged parent ASINs?**

- Politely insist that you’ve already attempted the process on your end without success. Explain that only Seller Support can delete the parent ASINs using their internal tools. Be persistent, as it may take 2–3 calls to find an agent who can help.

**8. Why is it necessary to create new parent SKUs after resolving the issue?**

- Creating new parent SKUs prevents the system from re-using old parentage contributions, reducing the risk of the issue recurring. New SKUs help establish fresh relationships between parent and child listings.

**9. What are the risks of using Method 2 (Delete and Relist)?**

- Potential risks include:

  - A delay of over 24 hours before the products are reactivated.
  - Losing previous sales history or performance data associated with the original parent ASINs.
  - Inactive listings during the relisting process may temporarily affect visibility and sales.

**10. What should I include in the full update flat file for relisting?**

- The flat file should include:

  - New parent SKUs and child SKUs.
  - Complete product attributes, including titles, bullet points, and descriptions.
  - Accurate inventory and pricing information.
  - Ensure the "update_delete" column is set to "PartialUpdate" for all rows.

**11. Why do both parent SKUs need to be deleted in Method 2?**

- Deleting only one parent SKU can leave residual data in the system, causing errors when rebuilding variations. Deleting both ensures a clean slate for re-establishing parent-child relationships.

**12. How do I monitor the resolution process after making changes?**

- For Method 1, confirm with Seller Support during the call that the parent ASINs are deleted and check the Variation Wizard to ensure the merge is undone.
- For Method 2, wait at least 24 hours after deletion, then check Seller Central to verify the new parentage is correctly established.

**13. What should I do if the issue persists after applying either method?**

- Reopen the case with Seller Support and provide screenshots or supporting documents (e.g., Category Listings Report, Variation Wizard view) to illustrate the problem. Be clear about the actions already taken and request further assistance.

**14. How can I prevent unauthorized merging of parent ASINs in the future?**

- While unauthorized merges cannot be completely prevented, you can:

  - Ensure clear and distinct variation attributes for different parent ASINs.
  - Regularly monitor your inventory for any unexpected changes in parent-child relationships.
  - Maintain updated backups of your Category Listings Report for quicker resolution if issues arise.

**15. What are the best practices for communicating with Seller Support during this process?**

- Be specific and concise:

  - Clearly explain the issue as an unauthorized merge.
  - Direct them to review the Variation Wizard for the affected ASINs.
  - Request manual deletion of the parent ASINs using their tools.
  - Remain patient and persistent, as resolution may require multiple interactions.

**16. Can I use these methods for unrelated parent-child listing errors?**

- These methods are specific to unauthorized merging of two parent ASINs. For other listing errors, consult Amazon's Seller Central guidelines or file a separate case with Seller Support.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-25%20at%202.43.05%E2%80%AFAM.png
- 2. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/iQsimage.png
- 3. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/Screenshot%202025-01-25%20at%202.43.14%E2%80%AFAM.png
- 4. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Yzcimage.png
