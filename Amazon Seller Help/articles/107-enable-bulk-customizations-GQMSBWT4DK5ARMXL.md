---
title: "Enable bulk customizations"
source_url: "https://sellercentral.amazon.com/help/hub/reference/GQMSBWT4DK5ARMXL"
downloaded_at: "2026-05-12"
source: "Amazon Seller Central Help"
---

# Enable bulk customizations

On this page
Custom Products: Helpful tips for bulk upload
Custom Products bulk upload FAQ
Custom Products Help page guide

The bulk customization tool allows you to apply customizations to numerous ASINs at the same time through an excel file. To begin the bulk upload process, you must 1) create a base ASIN, 2) apply customizations, 3) generate and download the template, 4) enter bulk information, and 5) upload the feed and submit customizations for bulk application. Below are the instructions for the steps outlined above.

Create a Base ASIN
a. Create an ASIN through the standard ASIN creation process in Seller Central (this may include creating your ASIN via feeds, or one at a time). Before proceeding to the next step ensure that your ASIN is “active” and has an inventory quantity of 1 or greater.
Apply Customizations to an ASIN

a. Navigate to the Inventory tab and select Manage Inventory. Identify the ASIN that you would like to customize by clicking ‘Edit’ in the inventory table, and then ‘Add/edit customization information’. You will be taken to a page that allows you apply customizations to the ASIN.

Generate and Download the Template

a. After applying customizations to the ASIN, click the generate template button on the bottom of the ASIN customization page. By clicking the generate template button you are copying all of the customization fields (including fonts, font colors, labels, etc.) to a template that can be downloaded as an excel file so that other products are customizations enabled.

b. In the generate template window, enter a template name,click the save button, and click continue to view your template.

c. You will be redirected to the product customization templates page. The table on the product customization templates page will display created templates.

d. Locate the template you just created, which will be the first one in the table.

e. Click thedownload icon to download an excel template.

Enter Bulk Information

a. Open the downloaded excel file on your computer. The excel file has 5 tabs along the bottom including ‘Instructions’, ‘Template’, ‘Data Definitions’, ‘Standard Fonts’, and ‘Characters allowed.’ A short description of each of these tabs is provided below:

Instructions: This tab includes a brief overview of each tab within the file including how to save, how to upload, and file limitations.
Template: This tab contains all of the customization information you applied to your product in Step 3. This is where you will add the SKUs in bulk that you wish to take on similar customization characteristics.
Data definitions: This tab contains the explanations and acceptable values that can be used as you fill out the Template as well as whether a field is Required or Optional. We recommend printing the Data Definitions sheet for reference.
Standard fonts: There are over 100 pre-loaded standard fonts that you can offer Customers. The font names can be chosen from the "standard fonts" tab of this excel file - font names should be comma separated, for example, Abel, Acme, Arvo. You are required to have at least one font and font color for each SKU.
Note: Instructions on how to list custom fonts are included in the Data Definitions tab.
Characters allowed: This tab in the excel file serves as a reference point of all available character choices. For text and data input customizations we provide you with the ability to specify the characters that are allowed to be entered by Customers such as ‘Numbers (All languages)’, or ‘Any letters or numbers (English only)’.

b. Navigate to the template tab to begin entering information: Enter data into row 4. This row contains the product SKU and values for each of the attributes & components you entered on the customization page. Only enter one unique value per column.

Do not edit rows 1-3. Do not remove or add columns or manipulate data located within the rows 1-3 of the template - the file will not process and you will receive an error. These rows contain the unique customization identifiers for each of the customization components.
Save your File

a. Delete all tabs other than the template tab (for example, the instructions, data definitions, standard fonts, and characters allowed). In other words, the only tab that should be present in the excel file is “Template”

b. Save as Unicode text file (UTF-16 Unicode Text). If you save you file as another file type you will receive an error during upload.

Upload your file to the Product Customization Templates Page

a. Click Inventory and navigate to the ‘Manage Your Inventory’ tab in Seller Central.

b. Select the ‘Custom Products’ link.

c. Click the ‘Enable Custom Products via upload’ link

d. From the product customization template page, go the Upload product customizations tab.

e. Click the ‘Upload a product customization template’ button.

f. After the file has been submitted, a row will appear in the table of the Upload product customizations page that either shows a status of ‘Inprogress’ or ‘Inqueue’.

Each of the columns displayed in the table are described below:

Batch ID: This is the identifier of the file.
Date uploaded: The date and timestamp that you submitted the file.
Records: The total SKU count in the file, the count of SKU’s processed successfully, and the amount of errors present.
Status: There are four possible status messages including InQueue, InProgress, Done, and Error.
Actions: In the event that that any of the rows had errors, an error report can be downloaded as an excel sheet with further instructions to diagnose the problems. See section 6.
Wait for the status message to read done and then refer to the records column to determine how many records processed successfully and how many rows had errors.
Once the file has uploaded successfully you will see a notification that says “file uploaded”, the name of the file that was uploaded, a trashcan icon (that allows you start over), and a ‘Submit customizations’ button.

g. Click the ‘Submit customizations’ button to begin the process of applying customization in bulk to the ASINs added in the file.

Error Report

a. In the event that that any of the rows had errors, an error report can be downloaded as an excel sheet with further instructions to diagnose the problems.

b. If you are unable to download the error report, please re-upload and submit the feed file again.

Custom Products: Helpful tips for bulk upload

The maximum file size for fonts and images is 3MB.
Include at least one font type, one font color and a value for surface_name1
Save your template somewhere that is easy to remember. If you ever need to update something, you can’t download anything that you have previously uploaded, so you will need to start again if you don’t save your template.
The easiest way to create your photos is to create them in a way where the text box is always in the same spot, this way your text box coordinates are always in the same spot. If your photo editing tools don’t give you an easy way to get coordinates, try doing one ASIN via the one-by-one method to get the coordinates.
Text boxes in the tool do not rotate, so please rotate the image.

Custom Products bulk upload FAQ
How do I get a URL for my images or fonts?

Upload images to a file hosting service and ensure that the files are not protected, for example with a password.

Why aren’t there font sizes?

The customization widget automatically resizes the font so that the text fills the space you have specified. If you want to prevent the font from resizing automatically, select a lower character limit so that the customer cannot enter text beyond the allotted area.

My preview image URL is correct, but there are still errors. How can I resolve this?

Remove any spaces that you see in the URL

Can I use the bulk upload feed to remove values? For example, to remove certain colors that I no longer support.

Yes, deletion via bulk uploads is supported, but keep in mind that you still are required to have at least one font color as well as one font type.

I manually uploaded a preview image. Can I change the image via the bulk upload?

Yes, be sure to include the surface name otherwise your report will show no errors, but it will also say that no records were processed successfully.

Does the feed catch duplicate values?

It will only catch duplicate font names, so please note that it won’t catch items such as duplicate color hex values or duplicate .ttf URLs.

Does the feed work for all categories that support Custom?

Yes

My fonts are not working on some computers or in some browsers. Why?

If you have uploaded a TrueType font (.ttf) file as your chosen font, you need to confirm that the font file is an installable .ttf. To confirm that the .ttf is an installable file, follow the steps below:

What if the custom text cannot be colored – as in laser engraving?

We recommend you find a color and font that match the experience of engraving as closely as you can.

Should I provide the information for parent SKUs, child SKUs, or both?

Both. Provide customization information for your parent SKU as if it were one of the child SKUs. However, this configuration will not be represented to customers.

Note: Product variations will first need to be built using a normal product listing feed. The Custom enablement feed does not support the creation of variation families.

In the customizable enablement tool, what is the difference between editing the parent ASIN and editing the child ASIN?

If you edit the parent ASIN using the customization enablement tool, your edits will copy through to all of your child ASINs.

If you edit the child ASIN, your edits will only occur on the specific child ASIN selected.

If you are configuring color variations, we recommend you edit each child so your preview image aligns to the correct color of the product.

Custom Products Help page guide

Custom Products
Custom Listing Guide
Enabling Bulk Customizations
Custom: Text customization
Custom: Image customization
Custom: Product configuration
Fulfilling an Order using Amazon Custom
