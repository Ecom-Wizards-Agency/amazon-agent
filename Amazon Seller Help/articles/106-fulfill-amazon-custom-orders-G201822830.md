---
title: "Fulfill Amazon Custom orders"
source_url: "https://sellercentral.amazon.com/help/hub/reference/G201822830"
downloaded_at: "2026-05-12"
source: "Amazon Seller Central Help"
---

# Fulfill Amazon Custom orders

On this page
Steps to retrieve customization data from an order
Manage orders tool
Order report files
Amazon Selling Partner APIs
Customization information details from zip files

Amazon now offers the ability to create product listings that support customization experiences for buyers.

You can access the Amazon Custom program once your seller account has been registered for the program. For more information about Amazon Custom and to apply, click here. For information on how to configure listings using Amazon Custom, click here.

Steps to retrieve customization data from an order

The customization information (such as a photo upload or the name to be printed on the product) is available in the following locations after an order is placed:

Manage orders tool
Order reports files
Amazon Selling Partner APIs (SP-API)
Manage orders tool

To access the customization information for an order from the Manage orders tool in Seller Central, follow the below steps:

From the Orders drop-down menu, click Manage orders.
Click the order number for the order which contains the customizable product (For example, 114-6923471-2011994).
Within the Order contents section, under the Product name column, click Show more for the customizable product. Then click Customization information.
The Customization information page displays the following information:
The information provided by the buyer for each of the customizations in each of the surfaces.
A Download button that allows you to download a .zip file which contains the customization information.
Note: Internet Explorer might not properly display details on the Customization information page.
Order report files

To retrieve the customization information from the downloadable order reports, follow these steps:

From the Orders drop-down menu, select Order reports.
Select New orders or Unshipped orders, located on the top left of the page.
Click Request report. When the most recent report is ready, click Download in the Download column.
Open the report in Microsoft Excel or another spreadsheet program.
The last two columns of the report are Customized-URL and Customized-page.
Note: In order to see Custom information on order reports, go to Orders > Order reports . In the upper right, click the Add or Remove columns link. On the Add or remove order report columns page, scroll down, select Customized URLs, and then click Save changes. This adds two columns containing links to customization information for your orders that you can then download as a .zip file.
Customized-URL

This link downloads a .zip file which contains the customization information - details about this .zip file can be found below.

Customized-page

This brings you to the customization information page as described above.

Amazon Selling Partner APIs
Important: You must be an Amazon SP-API developer in order to send an Orders request.

You can also access the customization links through APIs. To retrieve the customization information in an automated way, follow these steps:

Sign up for SP APIs at https://developer.amazonservices.com.
You will receive access token, refresh token, Seller ID and MarketplaceId. Save this information, as they will be used as inputs to call the APIs.
To call SP API follow the steps at: https://developer-docs.amazon.com/sp-api/docs/tutorial-test-selling-partner-api-endpoints.
For generating an Unshipped Order Report, you need to call the following APIs:
CreateReport API - OrderReportType as _"GET_FLAT_FILE_ACTIONABLE_ORDER_DATA"_.
GetReport API - returns ReportId.
GetReportDocument API - takes ReportId as input and generates the UnshippedOrderReport as an xml file.

Customization information details from zip files

The downloadable .zip file contains different data formats depending on whether your customizable products are using the text-based customization features and options-based customization features, or the image-based customization features.

Text Customization and Product Configuration (Options)

Note: For a limited time, you might see that some of your .zip files for orders contain only a .JSON (JavaScript Object Notation) file, while others might contain an .XML (Extensible Markup Language) file and .JPG file in addition to a .JSON file. For .JSON files included with these additional two file types, theversion 3.0 schema and its associated customization data elements are still provided. In the new version of the .JSON file, however, the customization data elements are also available in a different schema called customizationData.

If your order’s .zip file contains only a .JSON file:

Unzip the file.
Open the .JSON file using a text editor program. (You can also read JSON files using an online JSON viewer.)
Find a JSON viewer.
Copy the text from the text editor program, paste it into your JSON viewer, and click the Viewer tab.
Expand the version 3.0 section; you will see the text and the chosen fonts and colors and/or selected options and pricing.

If your order’s .zip file contains a .JSON file, an .XML file, and .JPG file(s):

Unzip the file.
Open the .JSON or .XML file using a text editor program. (You can also read JSON files using an online JSON viewer.)
Find a JSON or XML viewer.
Copy the text from the text editor program, paste it into your JSON viewer and click the Viewer tab, or for XML paste the text into your viewer and click Highlight or Tree to view the data.
Expand the version 3.0 section or the customizationData section; you will see the text and the chosen fonts and colors, and selected options and pricing. Note that version3.0 provides the same structure and contents as that in the standalone .JSON file.
There is one .JPG file included for each of the product’s surfaces. Each .JPG file contains an image for the product’s surface preview area with the buyer-supplied customizations. You can use these to manually verify what the buyer saw at the time of adding the product to the cart.

Note: If you are unable to view the JSON file or unable to read the data, try changing the name of the downloaded .zip file to "1.zip" (just add .zip to the end of the file name).

Image-based customization

Unzip the file - the unzipped file contains several different file formats.
.JPG or .PNG: If the buyer uploads an image, the image file will be provided to you as a .JPG. If the buyer chooses a gallery image, you will be provided either a .JPG or .PNG of the image, depending on the file type you used to create the gallery.
JSON: You can read a JSON easily by following the instructions above under 'Text Customization and Product Configuration (Options).' If the buyer selects one of your gallery images, the JSON will contain the name of the image file that you included in your gallery. The JSON will also contain the dimensions of the printable area that you provided when configuring the product listing. Lastly, the JSON offers the name of the SVG file that contains all of the image-related customization information for this order. The SVG is explained below.
SVG: If the buyer uploads an image or adds text, the image file, text information, size, rotation, and position of each of the details will be reflected in this file. The SVG represents a 3200x3200 perfect square which you can align to your 400x400 mask image to understand exactly what the buyer saw when the order was placed.
Note: For image customization you will receive the full image as provided by the buyer, even if a mask is in place. It is up to you to manipulate and place the image on the product accordingly.
