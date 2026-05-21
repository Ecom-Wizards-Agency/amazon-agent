---
title: "Get started with Multi-Location Inventory"
source_url: "https://sellercentral.amazon.com/help/hub/reference/GYCAQ9XRL273EVDX"
downloaded_at: "2026-05-12"
source: "Amazon Seller Central Help"
---

# Get started with Multi-Location Inventory


Multi-location inventory is available for all Fulfilled by Merchant (FBM) sellers with single or multi locations who provide their inventory via SP-API, Feeds API, Seller Central Manage All Inventory, and Seller Central template upload or using a third-party integrator (Multi-channel integrator). You can add as many or as few ASINs as you would like. To get the benefits of MLI, we recommend adding all of your ASINs. To use Multi-location inventory, Shipping Settings Automation must be enabled in Seller Central.Follow these steps to get started:

Create and manage your locations.
Use our Multi-Location Inventory API integration instructions to learn how to set up locations (also known as Supply Sources or S2s). Creating locations can be done via API integration or in Seller Central.
View Integration Instructions
Add or update your location-level inventory.
Use the following options to manage and update your location-level inventory for your Fulfilled by Merchant SKUs:
Option 1: Use SP-API
Option 2: Use Feeds API
Option 3: Upload a feed file in Seller Central
Option 4: Use Manage All Inventory in Seller Central
Note: For the first time only, you must zero out your "Default" fulfillment channel inventory for the SKUs for which you are sharing location-level inventory.
Enable Shipping Setting Automation (SSA) on your Shipping Template, and assign ASINs synced with MLI to this template. Follow these steps to enable Shipping Settings Automation (SSA):
From the Settings drop-down menu on the top right of Seller Central, click Shipping settings.
Go to the Shipping templates tab.
On the Shipping templates tab, you can enable Shipping Settings Automation on the following:

Click Create new shipping template and select new Shipping templates.
Choose Existing shipping templates and click Edit.
Turn on the Shipping settings automation option.
Select one or more of your Ship-from location, and click Next. These locations should match your inventory locations.
Choose from a Prime or non-Prime Shipping Template and click Next.
On the Standard shipping automation preferences page, enable automated transit time for Standard Shipping by following these steps:

Under Region preferences section, click Edit to manage your standard shipping regions.
Select the carriers and shipping services you currently use in the Carrier preferences section and click Next.
If you're shipping from a domestic fulfillment center, you can enable Premium Shipping region automation for Self-Fulfilled One-Day Delivery and Two-Day Delivery. Select the carriers and shipping services you use in the Carrier preferences section on the Premium shipping automation preferences page and click Next.
Review your shipping settings automation preferences and click Confirm.
Review and edit the Shipping fee for your shipping regions.
Click Save template.
Assign your MLI SKUs to the shipping template.

Currently, Shipping Templates are limited to 10 locations. Your ASINs synced with MLI can be on the same Shipping Template as ASINs not synced with MLI. However, this Shipping Template should be enabled with Shipping Settings Automation (SSA), and must include all of your inventory locations.

You can use MLI for Seller Fulfilled Prime and have your MLI inventory on as many Shipping Templates as you would like.

If SSA on a Shipping Template that has ASINs synced with MLI is disabled, your customers will still be able to place orders. However, your delivery promise will be based off of your manual estimation and you will not get the benefits of MLI and SSA.
