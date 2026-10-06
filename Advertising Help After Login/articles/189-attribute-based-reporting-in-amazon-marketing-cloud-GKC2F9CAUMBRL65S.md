---
title: "Attribute-based reporting in Amazon Marketing Cloud"
source_url: "https://advertising.amazon.com/help/GKC2F9CAUMBRL65S"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Attribute-based reporting in Amazon Marketing Cloud

Learn how to leverage the expanded attribute-based reporting capabilities in Amazon Marketing Cloud (AMC) for more granular campaign performance analysis and audience creation.

Updated on Nov 12, 2025

With attribute-based reporting, you can send 13 optional Events Manager attributes along with your events via Amazon Ad tag (AAT) to access comprehensive attribute-level reporting and audience creation in AMC. Additional benefits of using attribute-based reporting include a simplified workflow for granular reporting and enhanced insights into campaign performance.

| Attribute | Data type | Description | Format | Example |
| --- | --- | --- | --- | --- |
| brand | string | Brand of the advertiser or product | Minimum length: 1; Maximum length: 256; No special characters allowed | "TechNova" |
| category | string | Category of the page or product | Minimum length: 1; Maximum length: 256; No special characters allowed | "Electronics" |
| productId | string | Product IDs associated with the event, such as SKUs | Minimum length: 1; Maximum length: 256; No special characters allowed | "TN-SP5000-BLK" |
| attr1 - attr10 | string | 10 sequentially numbered attributes that can be used to provide additional context for the tracking tag | Minimum length: 1; Maximum length: 256; No special characters allowed | attr1: "Smartphone" attr2: "5G" attr3: "Black" |
| value | double | The value of the event | Minimum: 0; Maximum: 9999999999999; Up to 2 decimal points; Must be a multiple of 0.01 | 99.99 |
| unitsSold | integer | The number of items purchased | Minimum: 1; Maximum: 9999999999999 | 2 |
| currencyCode | string | The currency code associated with the 'value' of the event in ISO-4217 format | Must be a valid ISO-4217 currency code | "USD" |

**Additional considerations:**

1. For the value attribute: When used with the OFF_AMAZON_PURCHASES conversion type, it represents a monetary value. For other conversion types, it represents a non-monetary value based on your chosen scale. If not specified, a default of 0 (for OFF_AMAZON_PURCHASES) or 1 (for other types) will be applied.
2. The unitsSold attribute is only applicable for OFF_AMAZON_PURCHASES conversion type. If not provided, a default of 1 will be applied.
3. The currencyCode attribute is applicable only for OFF_AMAZON_PURCHASES conversion type. If not provided, the currencyCode setting on the conversion definition will be used.
4. For all string attributes (brand, category, productId, attr1-attr10), ensure that no special characters are in use and that the length is within the specified range.

## Query attributes in AMC

When querying AAT conversion events in AMC, customers can now include these attributes as dimensions or metrics in their AMC-generated analyses. For example, an advertiser capturing product ID values via AAT could include this attribute as a dimension in their report, allowing them to validate how Amazon DSP investment leads to off-Amazon purchases at the product ID-level. These same attributes can also be used for audience creation (that is, audience of past purchasers of specific products).

Below is an example of the type of analysis a fictional customer, TechNova, could run using these new attribute fields. This customer will have implemented AAT on their brand site so that the product ID/SKU is passed through AAT attribute productId and product name through AAT attribute attr1 for brand site purchases.

| campaign | conversion_ event_source_name | conversion_ event_name | off_amazon_ product_id | off_amazon_ attribute_attr1 | conversions | off_amazon_ product_sales | off_amazon_ roas |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TN Holiday 2024 | Amazon Ad tag | Brand Site Purchase | TN-SP5000-BLK | TechNova Smartphone 5000 Black | 500 | 10000 | 4 |
| TN Holiday 2024 | Amazon Ad tag | Brand Site Purchase | TN-LT2024-SLV | TechNova Laptop 2024 Silver | 250 | 7000 | 3 |
| TN Holiday 2024 | Amazon Ad tag | Brand Site Purchase | TN-WC100-WHT | TechNova Wireless Charger 100 White | 1000 | 20000 | 5 |
| TN Holiday 2024 | Amazon Ad tag | Brand Site Purchase | TN-BT500-RED | TechNova Bluetooth Speaker 500 Red | 750 | 14000 | 7 |

Off-Amazon attributes have a HIGH aggregation threshold. Values for these attributes will only populate in AMC reporting if the row represents 100+ users. For example, if the first row in the above report only corresponds to 10 unique users (only 10 users purchased SKU TN-SP5000-BLK), the off_amazon_product_id and off_amazon_attribute_attr1 will be NULL.

Associating conversions to an order is a required step to ensure that the AAT events flow into AMC.
