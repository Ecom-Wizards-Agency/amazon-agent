---
title: "First-party signals in Amazon Marketing Cloud"
source_url: "https://advertising.amazon.com/help/G9MWJR9CK8PRNUXQ"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# First-party signals in Amazon Marketing Cloud

In addition to the included Amazon Ads events tables, you can upload your own first-party signals to Amazon Marketing Cloud (AMC).

Updated on Nov 21, 2025

Each AMC instance contains a variety of Amazon Ads event tables that come included. These are determined by the types of entities (for example, Amazon DSP and sponsored ads) that have been connected to your instance. These tables can be used to analyze your Amazon Ads activity. You can also upload your own first-party (1P) tables for use in combined analytics, via the AMC advertiser data upload feature or other mechanisms. The signals you choose to upload stay within your dedicated AMC instance, and can’t be accessed or exported by Amazon.

Common types of 1P records include:

- First-party audiences
- Off-Amazon transaction events, such as in-store purchase records
- Product metadata, such as a mapping of ASIN to product name, category, and other fields

Uploading 1P records unlocks a variety of sophisticated measurement and audience use cases. Independently, Amazon Ads event tables can be used to answer business questions constrained to your Amazon Ads media and associated events. For instance, “What was the incremental reach of my Amazon DSP campaigns compared to my sponsored ads campaigns?” By using 1P tables with your Amazon Ads tables, you can answer questions within your broader business context. For example, “What percent of my total customer list have I reached with my Amazon Ads media?” or “What percent of my off-Amazon transactions have been influenced by my Amazon Ads campaigns?”

To join your own tables with Amazon Ads tables, your schema needs to contain joinable fields. You can join 1P and Amazon Ads tables columns that may be common to both tables, such as ASIN or user_id. Within AMC, user-level joins between advertiser data and Amazon Ads data must be performed using AMC’s pseudonymous user_id field.

When 1P records with identifier fields are uploaded, they’re resolved to the same common, pseudonymized identifier as other records in AMC; any other 1P identifier values are discarded. While the 1P identifier values are dropped, the table’s schema as shown in the AMC UI will still list the column names, but these columns can’t be used in your queries. This is true for any 1P schema that includes identifier fields.

There are multiple methods for uploading 1P records to AMC. You can upload through Ads Data Manager, which provides both an intuitive console interface. For API options for data upload and management, visit AMC data upload. Additionally, some AMC-integrated partners such as Customer Data Platforms (CDPs) offer the ability store and organize 1P records, as well as activate them to AMC. To determine whether your CDP is AMC-integrated, please consult with your CDP representatives and refer to CDP documentation on the upload process.
