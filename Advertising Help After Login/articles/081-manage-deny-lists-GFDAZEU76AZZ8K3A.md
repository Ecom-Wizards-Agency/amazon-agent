---
title: "Manage deny lists"
source_url: "https://advertising.amazon.com/help/GFDAZEU76AZZ8K3A"
library: "Amazon Ads Support Center"
section: "account-management"
downloaded_at: "2026-10-07"
status: "captured"
---

# Manage deny lists

Learn how to use a deny list to restrict where your ads appear.

Updated on Oct 5, 2026

Amazon Ads makes efforts to protect you from invalid traffic, unauthorized sellers, and unsafe content at no extra charge using a combination of proprietary technology, strict on-site advertising policies, and independent third-party solutions. We also manually review third-party websites, apps, and creator content for unsafe content. If a third-party website, app, or creator is identified as unsafe, it's blocked from Amazon Ads.

The StoreID deny list feature is available for advertisers in Brazil, Canada, Egypt, France, Germany, India, Italy, Mexico, Saudi Arabia, Spain, Türkiye, United Arab Emirates, United Kingdom, and the United States.

## Deny lists

You can upload a custom list of web domains, mobile app IDs, and creator tags to be excluded from delivery of Sponsored Products and Display campaigns here . These deny lists are applied to all active Sponsored Products and Display campaigns and must meet the following requirements:

- Creator tags can be blocked by entering the tag ID found in the creator's promotional URL (the text betweentag=and the&symbol).
- You can block the entire website (example.com) or subdomains from a website (news.example.com or docs.example.com); however, you can't block individual web pages, such as example.com/politics.html.
- You can't block sections of the website with a URI (Uniform Resource Identifier). (example.com/sports/)
- Mobile App IDs should never be submitted as a full URL as these can’t be processed.
- If your deny list upload exceeds 10K, you’ll need to create multiple files, each with a maximum of 10K entries. For example, if your list is 45K, you’ll need to split the list into 5 files (four 10K files and one 5K file) and upload them individually.

## Upload a deny list

To upload a deny list:

1. Create a CSV/XLSX/TSV file containing web sites, mobile apps, or creator tag IDs where you don’t want your ads to be displayed. Enter the website URL or Apple/Android app ID/creator tag ID in the first column of your file with either “WEBSITE," “APP," or "CREATOR" in the second column. You can have up to 10,000 lines with 1 entry per line. www.example.comWEBSITEcom.example.appAPP
2. In the left menu, click **Administration**.
3. Select **Account access and settings**.
4. Click **deny list**.
5. Click **Upload deny list** and select your CSV/XLSX file.
6. The **Last action** section will flag if there was an error. or if the upload was successful. You may need to wait up to 15 minutes for the operation to complete. You can refresh the page to get the latest status.
7. Once the upload operation is complete, you can click **Download report**to review the upload operation results.

**Note:** If you’re importing a list from Display, Video, and Audio campaigns, you can reuse the same list for Sponsored Products and Display but will need to modify the list to support the Sponsored Products and Display deny list format. Display, Video, and Audio campaigns lists only have a single column with the website or mobile app name, so you’ll need to add a second column to the list to include WEBSITE, APP, or Creator.

## Find Creator tags

To exclude a specific creator from promoting your products:

1. Visit the page where the creator is promoting your product.
2. Look at the URL in your browser's address bar.
3. Find the text between tag= and the & symbol—this is the creator's tag.
4. Add this tag to your deny list using the format shown above.

**Example**: In https://www.amazon.com/tag=techreviewer-20&th, the creator tag is **techreviewer-20**.

## Clear a deny list

When you clear your deny list, you’ll lose all the websites, mobile apps, and and creator tags that you added previously to the deny list. It's highly recommended that you download the list locally prior to clearing it.

To clear your deny list:

1. Click the **…** button beside **Upload deny list** and select **Clear list**. This button is only available if the list is non-empty. You’ll get a prompt indicating that the action is non-reversible and that you should download the deny list prior to completing this action.
2. Click **Clear list** to remove all items from your deny list. Check the **Last action** section to make sure that the clear operation was successful. You may need to wait up to 15 minutes for the operation to complete. You can refresh the page to get the latest status.
3. Once the clear operation is complete, make sure that the **Download your deny list** button is disabled, this indicates that the deny list is empty.

## Download a deny list

To download your deny list, click **Download deny list**. You'll see everything added over the lifetime of the list. However, if the list has been previously cleared, it will only contain items after the last time you cleared the list.
