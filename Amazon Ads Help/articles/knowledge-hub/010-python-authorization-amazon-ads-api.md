---
title: "Step-by-Step Guide: Implementing Amazon Ads API Authorization Flow using Python"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/blogs/usage-examples/2025-03-step-by-step-guide-authorization-amazon-ads-api-requests-using-python"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-05-13"
status: "captured"
security_note: "Credential-bearing examples summarized instead of saved as runnable code."
---

# Amazon Ads API Authorization Flow Using Python

This article explains the Amazon Ads OAuth2 authorization flow for developers who need to access advertiser data through the Amazon Ads API.

## Security note

The source page includes examples for client secrets, authorization codes, access tokens, refresh tokens, bearer headers, and local token files. This local capture intentionally summarizes the workflow instead of storing runnable credential-handling code. Use the official source page when implementing, and store real credentials only in an approved secret manager.

## Authorization flow visual

![Amazon Ads authorization flow](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/authorization_flow.png)

![Authorization URL components](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/authorization_url.png)

![Login with Amazon client credential location](https://d3a0d0y2hgofx6.cloudfront.net/en-us/_images/usage-examples/lwa_client.png)

## Key roles

| Role | Meaning |
| --- | --- |
| API caller | The client application, usually a Login with Amazon application, requesting access. |
| Advertiser | The resource owner who approves access to advertising data and services. |
| Login with Amazon authorization server | Issues authorization codes, access tokens, and refresh tokens after approval. |
| Amazon Ads API endpoints | Resource server endpoints that return data or perform actions after valid authorization. |

## Key values

| Value | Source | Notes |
| --- | --- | --- |
| Client ID | Amazon Developer Console, Login with Amazon security profile | Identifies the client app. |
| Client secret | Amazon Developer Console, Login with Amazon security profile | Treat as a secret. Never save in docs or chat. |
| Return URL | Amazon Developer Console app configuration | Must match the redirect used in the authorization URL. |
| Authorization code | Redirect after advertiser grants access | Short-lived; exchange quickly for tokens. |
| Access token | Login with Amazon token endpoint | Short-lived permit used for API calls. |
| Refresh token | Login with Amazon token endpoint | Long-lived credential used to refresh access tokens. |
| Profile ID | Amazon Ads profiles endpoint | Identifies the advertiser account and marketplace context. |

## Workflow

1. Complete Amazon Ads API onboarding and create the Login with Amazon application.
2. Retrieve the LwA client ID, client secret, and configured return URL from the Amazon Developer Console.
3. Build an authorization URL with the approved scopes and return URL.
4. Have the advertiser log in and approve access.
5. Capture the short-lived authorization code from the redirect URL.
6. Exchange the authorization code for an access token and refresh token.
7. Use the access token and client ID to retrieve available advertiser profiles.
8. Use the profile ID as request scope for Amazon Ads API operations.
9. Refresh the access token when it expires.

## Python implementation options

| Option | Library | Best for |
| --- | --- | --- |
| Direct token calls | `requests` | Developers who want to see each OAuth request explicitly. |
| OAuth client library | `requests-oauthlib` | Developers who want helper functions for authorization URLs, token exchange, and token refresh. |

## Required headers for most API calls

| Header | Purpose |
| --- | --- |
| `Amazon-Advertising-API-ClientId` | Identifies the Login with Amazon client application. |
| `Authorization` | Carries the current access token as a bearer token. |
| `Amazon-Advertising-API-Scope` | Carries the selected advertiser profile ID for scoped operations. |
| `Accept` and `Content-Type` | Must match the API version and resource media type. |

## Checkpoints

- Confirm the advertiser account and region before retrieving profiles.
- Confirm which scopes are required before asking the advertiser to approve access.
- Keep authorization codes, access tokens, refresh tokens, client secrets, and profile-level data out of documentation.
- For production, use a secret manager rather than local credential files.
- Stop before requesting authorization from a real advertiser unless the user explicitly approves the permission scope and target account.
- Stop before making any write or mutation request through the API.

## Routing use

Use this page when the user asks about Amazon Ads API authorization, Login with Amazon, profile IDs, access tokens, refresh tokens, Python setup, or why API calls require client ID, bearer token, and profile scope.
