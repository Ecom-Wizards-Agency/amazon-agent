---
title: "Get started with Postman"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/postman"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-05-13"
status: "captured"
---

# Get started with Postman

Postman is a UI tool for making API calls, storing variables, and performing basic automations. Amazon Ads provides a Postman collection with commonly used endpoints for testing the API and generating code samples.

## Before you begin

This tutorial assumes:

- You have onboarded to the API.
- You have generated access and refresh tokens.
- You have either the Postman desktop app or web application.

## File import and environment setup

1. Download the Postman [environment file](https://raw.githubusercontent.com/amzn/ads-advanced-tools-docs/main/postman/Amazon_Ads_API_Environment.postman_environment.json).
2. Download the Postman [collection file](https://raw.githubusercontent.com/amzn/ads-advanced-tools-docs/main/postman/Amazon_Ads_API.postman_collection.json).
3. Import both files into Postman.
4. In **Collections**, confirm **Amazon Ads API** appears.
5. In **Environments**, confirm **Amazon Ads API** appears.
6. Select **Amazon Ads API Environment**.
7. Add credentials in the **Current Value** column.

## Required environment credentials

| Environment value | Description |
| --- | --- |
| Login with Amazon client identifier | Identifies the authorized Login with Amazon application. |
| Login with Amazon client secret | Secret for the authorized Login with Amazon application. Store only in Postman's Current Value field or a secrets manager. |
| Refresh credential | Used by Postman to request a fresh access token. Treat as sensitive. |

If the advertising account is outside North America, update `api_url` from the default North America URL. See [API endpoints](https://advertising.amazon.com/API/docs/en-us/reference/api-overview#api-endpoints).

## Get a fresh access token

1. In **Collections**, open **Amazon Ads API**.
2. Set active environment to **Amazon Ads API**.
3. Open **POST Access token from refresh token**.
4. Confirm the refresh credential, client identifier, and client secret resolve from the active environment.
5. Send the request.
6. Confirm a `200 OK` response.
7. Return to the environment and confirm `access_token` and `token_expires_at` are populated.

`token_expires_at` tracks token expiration. The Postman collection checks this and refreshes tokens automatically when needed.

## Get your profile ID

To make API calls, you need a `profileId`.

- If known, enter it directly into the `profileId` environment variable.
- If unknown, use **Profiles > GET Profiles** to return profiles associated with the account.
- The first profile returned is added automatically; if multiple exist, copy the desired profile ID into the environment.

## Next steps

- [Make your first call](https://advertising.amazon.com/API/docs/en-us/guides/get-started/first-call)
- [Request a report](https://advertising.amazon.com/API/docs/en-us/guides/reporting/v2/sponsored-ads-reports)
- [Request a snapshot](https://advertising.amazon.com/API/docs/en-us/guides/exports/get-started)
- [Create a test account](https://advertising.amazon.com/API/docs/en-us/guides/account-management/test-accounts/create-test-accounts)

## Currently supported by the Postman collection

- Authentication
- Sponsored ads reporting
- Sponsored ads snapshots
- Test accounts
- Account management
- Amazon Marketing Stream
- Sponsored Products campaign management v3
- Product metadata
- Sponsored Display for non-Amazon sellers
- Budget usage
- Budget rules
- Exports
- Partner opportunities

> Note: Sponsored Display endpoints have a separate collection and tutorial.

## Environment variable definitions

| Environment value | Description |
| --- | --- |
| Login with Amazon client identifier | Client ID of an authorized Login with Amazon application. |
| Login with Amazon client secret | Client secret of an authorized Login with Amazon application. |
| `permission_scope` | Scope used for account permissions. Default for general API use is `advertising::campaign_management`. |
| `redirect_uri` | URL included in **Allowed Return URLs** for Login with Amazon. Default is `https://amazon.com`. |
| `access_token` | Access token used for API calls; valid for 60 minutes. |
| `refresh_token` | Token used to refresh the access token. |
| `token_expires_at` | Timestamp when the access token expires. |
| `profileId` | Profile ID associated with the Amazon Ads account. |
| `auth_grant_url` | URL prefix for auth calls. |
| `token_url` | URL prefix for token calls. |
| `api_url` | URL prefix for general API calls. |

## Support

Feedback or questions can be opened in the [GitHub repository](https://github.com/amzn/ads-advanced-tools-docs).
