---
title: "Troubleshooting SOP: Price Not Updating in Automate Pricing"
category: "Catalog"
source_url: "https://sop.myamazonguy.com/books/catalog/page/troubleshooting-sop-price-not-updating-in-automate-pricing"
captured_at: "2026-05-12T07:07:49Z"
---

# Troubleshooting SOP: Price Not Updating in Automate Pricing

Source: https://sop.myamazonguy.com/books/catalog/page/troubleshooting-sop-price-not-updating-in-automate-pricing

## **Price Not Updating in Automate Pricing**

**Who is this for?**Amazon specialists responsible for monitoring and managing SKUs using Automate Pricing.

**Objective:** To provide a step-by-step guide to identify and resolve issues when a SKU's price is not updating as expected in Automate Pricing.

**Step 1: Confirm the SKU is Active**

If a SKU is inactive, it will not be eligible for repricing through Automate Pricing.

**How to check:**

1. Go to **Inventory > Manage Inventory**.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/x5mimage.png)

1. Enter the SKU in the search bar and click **Search**.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-kagkwpzi.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/XPqimage.png)

1. Check the **Status** column to confirm it is listed as **Active**.

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-se7p6m1y.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/xenimage.png)

If the SKU is inactive, it must be reactivated before Automate Pricing can take effect.

**Step 2: Check for Manual Price Changes and Rule Settings**

Manual price changes can temporarily pause repricing, depending on your rule settings.

**A. Check if repricing is paused:**

1. Go to **Pricing > Automate Pricing**.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-5fyoc6wp.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/V6Kimage.png)

1. Under **Action Tab**, then select **Edit SKUs**.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/CCOimage.png)

1. Enter the SKU and click **Search**.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/5Baimage.png)

1. In the **Your price** column, look for the message: *"****Repricing paused: Price changed manually****."*

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/nNnimage.png)

**B. Resume repricing:**

1. Under **Action**, click the arrow next to **Take Action**.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-1ow3sx4u.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/YReimage.png)

1. Select the rule assigned to the SKU.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-98uvmk08.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/NsMimage.png)

1. Click **Start repricing**.

**Step 3: Check for Active Promotions or Sale Prices**

Automate Pricing will not adjust prices on offers with active promotions or sale prices.

**How to check:**

1. Go to **Inventory > Manage Inventory**.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-ql4qf8d5.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/pkrimage.png)

1. Enter the SKU and click **Search**.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-704tapyv.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/vuEimage.png)

1. Look at the **Price** column. A green box around the price typically indicates a promotion or sale price is active.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-ekchbp6n.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Lrzimage.png)

To allow repricing, remove any sale price or active promotion tied to the listing.

**Step 4: Check if the Offer Matches the Rule Criteria**

- Automate Pricing will only make price adjustments if the offer meets all the criteria of the assigned rule.
- For example, if a rule is set to "match the lowest price" but your listing already matches it, no price change will occur.
- Review the logic of the rule against the current offer to confirm eligibility for a price update.

**Step 5: Verify That the SKU is Assigned to a Repricing Rule**

A SKU must be assigned to a rule in Automate Pricing in order for the system to make pricing adjustments.

**How to check:**

1. Go to **Pricing > Automate Pricing**.![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-docd1596.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/YhOimage.png)

1. Click **Edit SKUs**.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/E7Rimage.png)

1. Enter the SKU and click **Search**.

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/qmHimage.png)

1. Look at the **Rule name** column.

  - If a rule is listed and the **Stop repricing** option is available under **Take Action**, then the SKU is currently active in Automate Pricing.

    ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-d4bre51i.png)

    ![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Gu3image.png)
  - If no rule is assigned, you will need to assign one to enable repricing.

    ![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-8zre7na0.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ZjOimage.png)

![image](https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-mgleml6i.png)

![image.png](https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/mFSimage.png)

**Final Notes**

- Follow the steps above in order to eliminate the most common repricing issues.
- If the issue persists after all steps have been completed, escalate to the Pricing Support team with a summary of your findings.

We welcome your feedback for improvement. Please click**[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.

## Image References

- 1. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/x5mimage.png
- 2. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-kagkwpzi.png
- 3. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/XPqimage.png
- 4. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-se7p6m1y.png
- 5. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/xenimage.png
- 6. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-5fyoc6wp.png
- 7. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/V6Kimage.png
- 8. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/CCOimage.png
- 9. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/5Baimage.png
- 10. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/nNnimage.png
- 11. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-1ow3sx4u.png
- 12. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/YReimage.png
- 13. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-98uvmk08.png
- 14. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/NsMimage.png
- 15. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-ql4qf8d5.png
- 16. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/pkrimage.png
- 17. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-704tapyv.png
- 18. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/vuEimage.png
- 19. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-ekchbp6n.png
- 20. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Lrzimage.png
- 21. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-docd1596.png
- 22. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/YhOimage.png
- 23. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/E7Rimage.png
- 24. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/qmHimage.png
- 25. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-d4bre51i.png
- 26. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/Gu3image.png
- 27. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-8zre7na0.png
- 28. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/ZjOimage.png
- 29. image: https://files.document360.io/d9e9b7a2-6758-4c75-97d3-36a6877048cf/Images/Documentation/troubleshooting-sop-price-not-updating-in-automate-pricing-image-mgleml6i.png
- 30. image.png: https://sop.myamazonguy.com/uploads/images/gallery/2025-08/scaled-1680-/mFSimage.png
