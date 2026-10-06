---
title: "Permissions definitions for the Ads API"
source_url: "https://advertising.amazon.com/help/GR9KP77YZUD3UEZD"
library: "Amazon Ads Support Center"
section: "account-management"
downloaded_at: "2026-10-07"
status: "captured"
---

# Permissions definitions for the Ads API

Learn about available API permissions and access levels for Amazon Ads API integrations across sponsored ads and Display, Video, and Audio campaigns

Updated on Oct 1, 2026

You can use the Amazon Ads API to enable a third-party application to manage your accounts (Sponsored ads, DSP, Manager Account) on Amazon. They can programmatically call the Amazon Ads API on your behalf with all the same permissions as the account that sets up the integration. Click here to learn more about the Amazon Ads API and request access.

## Sponsored ads permissions

| Resource | Associated permission | User with this permission level can... |
| --- | --- | --- |
| Campaign | advertiser_campaign_edit | Create new campaigns as well as view, edit, clone all campaigns associated with the account. |
| advertiser_campaign_view | View existing campaigns but not modify them. |
| Reports | nemo_report_edit | Create new reports as well as view and edit all reports associated with the account. |
| nemo_report_view | Create new reports as well as view and edit all reports associated with the account. |
| BillingHistory | nemo_transactions_edit | View and edit access to Billing History. Access to promo codes and all invoices associated with the account. Can download invoices. |
| nemo_transactions_view | View-only access to Billing History. Access and download all invoices associated with the account but can’t add a promotion code on the account. |
| PaymentSettings | adv_billing_edit | View and edit access to Payment Settings. View and modify payment information associated with the account. |
| adv_billing_view | View the payment information associated with the account but not modify it. |
| Stores | amazon_stores_edit | View and edit access to the Store builder. Create new Stores pages as well as view and edit all Stores pages associated with the account. |
| amazon_stores_view | View-only access to the Store Builder. View all Stores associated with the account but not create or modify Stores Pages. |

## Display, Video, and Audio campaigns permissions

For each resource, you can assign view or edit access. With view access, the API can only view these features. With edit access, it will have all the same permissions as the user who set up the API integration.

| Resource | Associated permission |
| --- | --- |
| Campaign | campaign_view |
| campaign_edit |
| Creative | creative_view |
| creative_edit |
| Inventory | inventory_view |
| inventory_edit |
| Audiences | audiences_view |
| audiences_edit |
| Events | event_manager_view |
| event_manager_edit |
| Reports | reports_limited |
| reports_edit |
