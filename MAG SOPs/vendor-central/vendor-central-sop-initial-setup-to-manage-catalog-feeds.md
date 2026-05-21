---
title: "Vendor Central SOP: Initial Setup to Manage Catalog Feeds"
category: "Vendor Central"
source_url: "https://sop.myamazonguy.com/books/vendor-central/page/vendor-central-sop-initial-setup-to-manage-catalog-feeds"
captured_at: "2026-05-12T07:07:49Z"
---

# Vendor Central SOP: Initial Setup to Manage Catalog Feeds

Source: https://sop.myamazonguy.com/books/vendor-central/page/vendor-central-sop-initial-setup-to-manage-catalog-feeds

## Initial Setup to Manage Catalog Feeds

**Who is this for :**This process is for vendors using Amazon Vendor Central who need to set up and manage catalog feeds for product listings, updates, and content submissions.

**Objective :**To establish a streamlined process for managing product catalog feeds efficiently, ensuring that product data is correctly formatted and submitted to Amazon for approval.

**Steps to Set Up and Manage Catalog Feeds in Vendor Central**

1. Accessing the Catalog Feeds Section

- Log in to Vendor Central.
- Navigate to the "Items" tab in the top menu.
- Select "Manage Catalog Feeds."

1. Choosing a Submission Method

- Amazon offers two primary methods for managing catalog feeds:
- Manual Submission: Best for vendors with a small catalog or occasional updates.
- Automated Feed Submission (via API or CSP): Ideal for large catalogs that require frequent updates.

1. Selecting a Catalog Service Provider (CSP) (If Applicable)

- If you want to use a Catalog Service Provider (CSP) to manage your product data submissions:
- Check Amazon’s List of Approved CSPs:
- Navigate to Vendor Central > Manage Catalog Feeds
- If available, look for a section to authorize a CSP.
- If this option is missing, Amazon may have shifted CSP management to an API-based process.

Authorize a CSP (if required by Amazon):

- Select a CSP from the list (if applicable).
- Choose your Vendor Code from the dropdown.
- Click "Authorize" to grant them permission to submit feeds on your behalf.
- Share the Vendor Code & Token (if generated) with your CSP.

1. Preparing Your Product Data for Submission

- Before submitting a catalog feed, ensure your product data is correctly formatted according to Amazon’s Feed Specification (AFS):
- Include required attributes, such as ASIN, product title, description, images, pricing, and compliance details.
- Ensure correct file format (CSV, XML, or JSON, depending on Amazon’s current requirements).
- Validate your feed using Amazon’s available tools (if applicable).

1. Uploading Your Catalog Feed

- Go to "Manage Catalog Feeds" in Vendor Central.
- Click "Upload New Feed" or "Submit Feed" (terminology may vary).
- Choose the appropriate feed template or use your custom CSV/XML file.
- Upload the file and submit it for processing.

1. Checking Submission Status & Resolving Errors

- After submission, monitor the feed processing status under "Manage Catalog Feeds" > "Check Submission Status."

  - If errors occur:

    - Click "View Errors" to download the error report.
    - Correct any issues in your feed file.
    - Re-upload the corrected file.

1. Updating or Removing Products from the Catalog

- To update existing products, submit a revised feed with the necessary changes.
- To remove a product, mark the item as "Discontinued" or use Amazon’s product removal process.

1. API Integration for Large-Scale Catalog Management (Optional)

- For vendors managing large catalogs, integrating with Amazon’s Selling Partner API (SP-API) can help automate feed submissions. Contact Amazon Vendor Support for guidance on API access.

FAQs

**1. Can all vendors use catalog feeds, or is it restricted to specific accounts?**

- Catalog feeds are available to vendors with bulk product listings who need to manage large catalogs efficiently. Some smaller vendors may only have access to manual product uploads instead of full catalog feeds.

**2. Is a Catalog Service Provider (CSP) required, or can I manage feeds manually?**

- A CSP is optional unless Amazon requires it for specific vendor setups. If you prefer, you can submit catalog feeds manually using Vendor Central > Manage Catalog Feeds or integrate via Amazon’s SP-API for automated updates.

**3. What file formats and size limits apply to catalog feed uploads?**

- Amazon accepts CSV, XML, and JSON formats, depending on the feed type. File size limits vary, but most feed uploads should stay under 50MB to prevent processing issues. If you need to upload a larger file, split it into smaller segments.

**4. How long does it take for Amazon to process a catalog feed submission?**

- Feed processing time can range from 24 hours to several days, depending on the number of SKUs and Amazon’s review process. Check Manage Catalog Feeds > Check Submission Status for updates.

**5. What should I do if my feed submission fails multiple times?**

- If your submission fails repeatedly:

  - Download the error report and correct any mistakes.
  - Ensure all required fields are properly formatted.
  - Try submitting a smaller batch to identify the issue.
  - Contact Amazon Vendor Support if errors persist.

**6. If I submit incorrect data, will it overwrite my current listings?**

- Yes, any new feed submission will overwrite existing product data unless marked as an update-only submission. Always review your feed file carefully before uploading.

**7. Can I access historical feed submissions for reference?**

- Yes, past feed submissions can be viewed under Manage Catalog Feeds > Submission History, where you can check previous uploads and their processing status.

**8. Will updating my catalog feed affect Buy Box eligibility?**

- Yes, product detail changes (such as price, availability, or compliance updates) may impact Buy Box rankings. Ensure that your pricing, stock levels, and compliance details are accurate to remain competitive.

**9. What’s the difference between removing and discontinuing a product?**

- Removing a product makes it temporarily unavailable but allows reactivation later.
- Discontinuing a product permanently removes it from your catalog and prevents future reorders.

We welcome your feedback for improvement. Please click **[here](https://airtable.com/appWnsFw5XIb0kyLl/pagKQiwIeVedjHsRz/form)**to share your thoughts.
