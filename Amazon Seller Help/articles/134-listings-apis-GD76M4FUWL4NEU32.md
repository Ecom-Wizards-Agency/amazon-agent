---
title: "Listings APIs"
source_url: "https://sellercentral.amazon.com/help/hub/reference/GD76M4FUWL4NEU32"
downloaded_at: "2026-05-12"
source: "Amazon Seller Central Help"
---

# Listings APIs

On this page
Automate listings to Amazon
Build and manage listings workflows
Product Type Definitions API
Listings Items API
Catalog Items API
Listing Restrictions API
Notifications API
JSON_Listings_Feed API
Availability for categories and geographic stores
Direct integration
Technical documentation
Support

Listings API (Application Programming Interface), is a new modernized suite of Selling Partner APIs for sellers, and third parties such as Catalog Service Providers (CSPs) to build programmatic integrations for listing selection in Amazon stores. The APIs provide building block functionality that help sellers/integrators to automate various listings workflows to effectively create and manage listings in Amazon stores. Sellers can use these APIs to build applications to reduce catalog management effort, reduce listing errors, and improve business performance.

Automate listings to Amazon

The Listings APIs are available to all sellers as well as third parties such as Catalog Service Providers (CSPs) to automate various listings workflows for Amazon.

Sellers have the options below to automate their listings:

Direct Integration: Seller is in charge of developing the integration (requires technical expertise and skillset to integrate)
Catalog Service provider: Seller leverages an existing solution from the Amazon Partner Network which is available in Selling Partner Appstore.

Both alternatives use Amazon APIs to retrieve and publish data. With Catalog Service Providers, a seller’s business needs might be achieved by using more than one provider.

Requirements	Option 1: Direct Integration	Option 2: CSP
Technical competency	Ability to write code in JSON*	Not Required
Working with a third party	No	Yes
Additional cost	No	Yes
Maintenance of the API channel	Required	Supported by CSP (based on CSP package)
Internal resource	Yes	Majority of work undertaken by CSP
Centralization of data and syndication across multiple channels	No	Yes
Build and manage listings workflows

We offer sellers a Building Listings Management Workflows Guide which summarizes the steps to build best-in-class listings creation and management workflows by integrating with Listings APIs. By following the recommended steps, sellers can minimize the friction encountered while creating and managing their listings on Amazon. This guide references detailed information about the individual API operations and use cases which are defined below.

Capabilities offered by Listings APIs

We provide the below APIs and notifications for programmatic integration by sellers.

Business Process	API Name & Content	Use Case	Link to use case guide
Listings	Product Type Definitions API	Search and retrieve Amazon product type definitions.	https://developer-docs.amazon.com/sp-api/docs/product-type-api-use-case-guide
Listing Items API	Create, edit, and delete Amazon listings (SKUs), including Images	https://developer-docs.amazon.com/sp-api/docs/listings-items-api-v2021-08-01-use-case-guide
Catalog Items API	Retrieve information about items in the Amazon catalog	https://developer-docs.amazon.com/sp-api/docs/catalog-items-api-v2020-12-01-use-case-guide
Listings Restrictions API	Provides details about listings restrictions for items in the Amazon catalog	https://developer-docs.amazon.com/sp-api/docs/listings-restrictions-api-v2021-08-01-use-case-guide
Notifications	Notifications API	Includes changes to the status of a product	https://developer-docs.amazon.com/sp-api/docs/notifications-api-v1-use-case-guide
Product Type Definitions API

This is a foundational API that allows sellers to search and retrieve the latest Amazon product type definitions, which describe the attributes and data requirements for items in the Amazon catalog. These schemas represent the same format used by the Listings Items API, the Catalog Items API, and the JSON_LISTINGS_FEED.

Key Features

Ability to search for the available product types based on geographic store and keywords.
Ability to retrieve product type definitions and related schemas for a given seller, Amazon product type, and Amazon geographic store
Ability to retrieve the below schema versions:
LATEST
RELEASE_CANDIDATE - provides a pre-release version of product type schemas.

This version typically contains upcoming changes, so that it allows sellers to prepare in advance.

Ability to retrieve schema requirements for:
LISTING - Requirements inclusive of product facts and sales terms.
LISTING_OFFER_ONLY - Requirements inclusive of sales terms only.
LISTING_PRODUCT_ONLY - Requirements inclusive of product facts only.
Ability to retrieve only required and conditionally required or optional and required attributes through the schema
Ability to efficiently surface all available attribute values where applicable (pick list of values)
Listings Items API

This API works with the above Product Type Definitions API and allows sellers to create, edit, and delete Amazon listings (SKUs) including product details (such as item names and bullet points) and sales terms (such as price, cost, and inventory). Using the schemas provided by the Product Type Definitions API, you can validate that the data requirements are met before submission through the Listings Items API.

Key Features

Ability to create a new listing, fully update an existing listing
Ability to create offer-only listings
Ability to submit product-only attributes to partially create an ‘inactive’ listing without any offer attributes which can be added at a later point in time
Ability to submit Images for listings
Ability to update and delete one or more individual attributes for an existing listing
Ability to delete an existing listing
Ability to receive real-time validation errors in response to the submissions, for example, missing required attributes.
Ability to receive a list of all catalog pipeline issues through localized issue messaging
Ability to retrieve all attribute information for seller SKUs
Catalog Items API

This API allows sellers to search and retrieve information about items (ASINs) in the Amazon catalog. This API provides reconciled information for an ASIN which is equivalent to what gets displayed on the Detail pages.

Key Features

Ability to specify which information about an ASIN needs to be retrieved
List of all item attributes (available to sellers with a selling role (Brand Representative or Reseller) assigned in the brand owning the item).
External item identifiers such as EAN, UPC, ISBN.
Images
Product type
Item sales rank data. Each sales ranking will contain the name of the category, the item's ranking, and a link to the sales ranking page on the retail website.
Item variation data. Contains the list of the ASINs of the items related to this item and whether this item is a child or parent item
Item data available to sellers. Contains item replenishment, brand, and manufacturer information.
Ability to search for ASINs using a list of product Ids, keyword search and retrieve a list of matched ASINs
Ability to retrieve list of ASINs by brand and classification refinements
Listing Restrictions API

The Listings Restrictions API allows sellers to check whether restrictions exist that prevent the creation of a listing for an item in the Amazon catalog. If an item is restricted, you may be able to take additional steps to request approval to create a listing. If no restrictions exist, you can then call the Listings Item API to create offer-only listings.

Key Features

Provides details about listings restrictions, if any, on an existing catalog item identified by ASIN
Option to filter the restrictions based on condition type
Supports checking multiple geographic stores for listings restrictions in a single call
When approval is required, this API returns next step links so you can pursue approval to create the listing
Notifications API

The notifications API lets sellers subscribe to various notifications so that they can be notified in near real-time about any events of interest.

We currently have the below notifications available for sellers:

LISTINGS_ITEM_ISSUES_CHANGE notification - Amazon sends a LISTINGS_ITEM_ISSUES_CHANGE notification whenever there is a change to the issues associated with a particular SKU that the seller owns. Issues point out that the listings item has problems that could cause the listing to become inactive, search suppressed, or have other quality problems. This notification can act as a trigger to pull all information about the issues through the Listings Item Get API.
PRODUCT_TYPE_DEFINITIONS_CHANGE notification - This notification is sent whenever there is either a new product type that gets added to Amazon or if there is an update to the schema definitions for any product type. This notification can act as a trigger to refresh and get the latest schema requirements through the Product Type Definitions API mentioned above.

JSON_Listings_Feed API

The Listings Items API mentioned above provides the ability to update individual listings one at a time. For some sellers and integrators, the Feeds API (bulk) remains their preferred method of integration. The JSON_LISTINGS_FEED works with the Product Type Definitions API and allows integrators to create, edit, and delete Amazon listings (SKUs) with the same data format used by the Listings Items API but in bulk. Listings data is interoperable between the Listings Items API and JSON_LISTINGS_FEED feed type, allowing sellers to use whichever mechanism or combination works best for their listings workflows.

Availability for categories and geographic stores

The Listings APIs is now available for Hardlines, Softlines and Consumables categories across all geographic stores worldwide excluding Books and Media categories. We are working on making these categories available in 2024, so check back again. However, inventory, price, or offer updates may be submitted for any listings item regardless of its product type.

Direct integration

Below are some of the considerations while directly integrating with the Listings APIs:

With Direct Integration the development efforts remain in-house
The data flows directly from the seller to Amazon
No intermediaries in the data exchange
Any data source the seller has can be mapped and used in the API integration
There are no dependencies on third parties
The solution can be customized based on seller’s own business needs
Flexibility to develop new features and quickly integrate to new SP-API launches
Direct integration may require longer setup time and upfront investment in building the capabilities.
The integrations need to be maintained and operated by the seller

At a high level, the process to begin direct integration requires technical teams within seller organization to take the below steps:

Register developer profile.
Create required AWS resources and SP-API application.
Develop the functionality to integrate with the various APIs.
Test the application.
Release and maintain

Technical documentation

Below is a list of useful links for technical documents:

Selling Partner API website
Key Steps to onboard with Selling Partner APIs
Product Type Definitions API
Listings Items API
Catalog Items API
Listings Restrictions API
Notifications API
Feeds API

Support

For technical issues with developer profile registration, onboarding or API integration, go to, Get support and then click Create a case with Developer Support.

For issues related to catalog submissions and support with errors encountered during submissions, go to, Get support and then click Additional resources.
