---
title: "How to onboard first-party data to Amazon Ads using ADM"
source_url: "https://advertising.amazon.com/API/docs/en-us/knowledge-hub/hands-on-workshops/1st-party-data-workshop/overview"
library: "Amazon Ads Advanced Tools Center"
section: "knowledge-hub"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon Ads Data Manager (ADM): Partner Implementation Guide

A use-case-driven guide for onboarding first-party data to Amazon Ads using the Ads Data Manager API, and activating that data across Amazon DSP and Amazon Marketing Cloud (AMC).

## What is ADM?

Amazon Ads Data Manager (ADM) is a centralized data onboarding platform that enables advertisers and agencies to securely upload first-party data and activate it across Amazon Ads products. ADM serves as the bridge between your CRM/CDP data and the Amazon advertising ecosystem.

### What ADM Enables

- Upload hashed customer lists (emails, phones, addresses) for audience matching
- Create DSP audiences directly from uploaded data for programmatic campaigns
- Share datasets with AMC for advanced analytics and custom audience modeling
- Track conversion events by connecting offline/online signals to Amazon campaigns
- Manage data lifecycle with retention controls and identity deletion for privacy compliance

### Data Flow

```
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐     ┌────────── - ───────┐
│  Your CRM   │────▶│  Hash PII   │────▶│  Upload  to  ADM   │────▶│   Create  Sharing  │
│   /  CDP      │     │  (SHA -256 )  │     │  (API / UI / S3)     │     │  Rule            │
└─────────────┘     └─────────────┘     └──────────────────┘     └────────┬─── - ─────┘
                                                                          │
                                              ┌───────────────────────────┼───────────────────┐
                                              │                           │                   │
                                              ▼                           ▼                   ▼
                                     ┌────────────────┐        ┌──────────────┐     ┌──────────────┐
                                     │  DSP Audiences │        │     AMC      │     │   Events     │
                                     │  (Targeting)   │        │  (Analytics) │     │   Manager    │
                                     └────────────────┘        └──────────────┘     └──────────────┘
```

## Prerequisites

​

### 1. Amazon Ads API Credentials

You need the following credentials from the Amazon Ads API console:

- Client ID (`CLIENT_ID`)
- Client Secret (`CLIENT_SECRET`)
- Refresh Token (`REFRESH_TOKEN`)
- Manager Account ID or Advertiser ID

### 2. Python Environment

```
pip install requests python-dotenv
```

### 3. Environment Configuration

Create a `.env` file with your credentials:

```
CLIENT_ID=amzn1.REDACTED
CLIENT_SECRET=amzn1.REDACTED
REFRESH_TOKEN=Atzr|xxxxxxxx

 # Use ONE of the following (Manager Account ID is recommended for agencies) 
MANAGER_ACCOUNT_ID=amzn1.REDACTED
 # OR 
ADVERTISER_ID=ENTITYxxxxxxxxxx

 # DSP Configuration 
DSP_DESTINATION_ACCOUNT_ID=ENTITYxxxxxxxxxx     # Fallback DSP advertiser account ID 
DSP_ACCOUNT_ENTITY_ID=ENTITYxxxxxxxxxx          # Optional: DSP advertiser entity ID (if required) 
MARKETPLACE_ID=ATVPDKIKX0DER                    # Marketplace ID (default: US) 

 # AMC Configuration (Use Case 3) 
AMC_INSTANCE_ID=amcxxxxxxxxxx                   # Your AMC instance ID 
AMC_INSTANCE_NAME=My Brand AMC Instance         # Optional: human-readable AMC instance name 
AMC_DESTINATION_ACCOUNT_ID=amcxxxxxxxxxx        # Typically the same value as AMC_INSTANCE_ID
```

### 4. Authentication

Every ADM API call requires these headers:

```
Amazon-Advertising-API-ClientId :  {your_client_id}
 Authorization :  Bearer {access_token}
```

Plus ONE account identification header:

| Header | When to Use |
| --- | --- |
| `Amazon-Ads-Manager-Account-ID` | For manager/agency accounts (recommended) |
| `Amazon-Ads-AccountId` | For individual advertiser accounts |

Use exactly ONE account header per request, not both.

**⚠ Note on Single Global Account (SGA):** ADM does not currently support Single Global Accounts (SGA). You must authenticate using a Manager Account (`MANAGER_ACCOUNT_ID`) or an individual Advertiser Account (`ADVERTISER_ID`) as described above. SGA support is planned for a future release.

### 5. Base Client Class

All use cases in this guide share this common client class:

```
import  os
 import  json
 import  time
 import  uuid
 import  hashlib
 import  requests
 from  datetime  import  datetime
 from  dotenv  import  load_dotenv

load_dotenv()

 class   ADMClient :
     """Base client for Amazon Ads Data Manager API""" 

    BASE_URL =  "https://advertising-api.amazon.com" 
    TOKEN_URL =  "https://api.amazon.com/auth/o2/token" 

     def   __init__ ( self ):
         self .client_id = os.getenv( 'CLIENT_ID' )
         self .client_secret = os.getenv( 'CLIENT_SECRET' )
         self .refresh_token = os.getenv( 'REFRESH_TOKEN' )
         self .manager_account_id = os.getenv( 'MANAGER_ACCOUNT_ID' )
         self .advertiser_id = os.getenv( 'ADVERTISER_ID' )
         self .access_token =  None 

     def   authenticate ( self ):
         """Obtain an access token using the refresh token.""" 
        resp = requests.post( self .TOKEN_URL, data={
             'grant_type' :  'refresh_token' ,
             'refresh_token' :  self .refresh_token,
             'client_id' :  self .client_id,
             'client_secret' :  self .client_secret
        })
        resp.raise_for_status()
         self .access_token = resp.json()[ 'access_token' ]
         print ( "✓ Authenticated successfully" )

     def   _headers ( self, content_type= 'application/json' ):
         """Build request headers with the appropriate account ID.""" 
        headers = {
             'Amazon-Advertising-API-ClientId' :  self .client_id,
             'Authorization' :  f'Bearer  {self.access_token} ' ,
             'Content-Type' : content_type
        }
         if   self .manager_account_id:
            headers[ 'Amazon-Ads-Manager-Account-ID' ] =  str ( self .manager_account_id)
         elif   self .advertiser_id:
            headers[ 'Amazon-Ads-AccountId' ] =  str ( self .advertiser_id)
         else :
             raise  ValueError( "Set MANAGER_ACCOUNT_ID or ADVERTISER_ID in .env" )
         return  headers
```

​

## Key Concepts

| Concept | Description |
| --- | --- |
| Dataroom | A container for all your ADM data. One per account. Must be created before any other operation. |
| Dataset | A named collection of audience records within a dataroom. Has a schema, country code, and retention settings. |
| Sharing Rule | A rule that connects a dataset to a destination application (DSP Audiences, AMC, Events Manager). |
| Identity Resolution | The process of matching your hashed PII to Amazon identities for targeting. |
| ID Retention | When enabled, hashed data is retained for 90 days and UID tokens are refreshed automatically. |

### Supported Destination Applications

| Application ID | Description |
| --- | --- |
| `DSP_AUDIENCES` | Create audiences for Amazon DSP programmatic campaigns |
| `AMAZON_MARKETING_CLOUD` | Share data with AMC for analytics and custom queries |
| `EVENTS_MANAGER` | Connect conversion events to Amazon campaigns |

## Use Cases

| # | Use Case | Description |
| --- | --- | --- |
| 1 | ​Onboard First-Party Audience Data​ | Upload hashed customer lists to ADM for identity matching |
| 2 | ​Create a DSP Audience​ | Activate ADM data as targetable audiences in Amazon DSP |
| 3 | ​Share Data with AMC​ | Send ADM data to Amazon Marketing Cloud for analytics |
| 4 | ​Conversion Event Tracking​ | Connect offline/online conversion events to Amazon campaigns |
| 5 | ​Manage Audience Lifecycle​ | Update, remove members, and delete datasets |
| 6 | ​Identity Deletion for Privacy​ | Handle GDPR/CCPA deletion requests |
| 7 | ​Monitor Dataset Health​ | Track match rates, record counts, and dataset metrics |

## Reference

| Page | Description |
| --- | --- |
| ​API Quick Reference​ | Complete endpoint map, request limits, and status codes |
| ​Troubleshooting & Best Practices​ | Common errors, data quality checklist, and best practices |

​

## Resources

- Amazon Ads Data Manager Overview
- ADM Dataset Management Guide
- Amazon Ads API Documentation
- Amazon DSP Documentation
- Amazon Marketing Cloud Documentation

This guide is intended for Amazon Ads partners and solutions architects. All code examples are for demonstration purposes and should be adapted for production use with proper error handling, logging, and security practices.

* ​

## Contributors

Chintan Sanghavi — Chintan is a Senior Solutions Architect at Amazon Ads who works with advertisers and partners to design scalable integrations with the Amazon Ads API, with a focus on agentic AI and data onboarding architectures.

Steve Berliner — Steve is a Solutions Architect at Amazon Ads who supports partners in implementing measurement and identity solutions, specializing in conversion tracking, privacy compliance, and AMC analytics.

Mayank Arora — Mayank is a Solutions Architect at Amazon Ads who helps partners build data-driven advertising solutions, specializing in audience management, ADM integrations, and first-party data activation.
