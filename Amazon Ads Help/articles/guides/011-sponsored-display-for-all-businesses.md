---
title: "Get started with Sponsored Display for all businesses"
source_url: "https://advertising.amazon.com/API/docs/en-us/guides/sponsored-display/non-amazon-sellers/get-started"
library: "Amazon Ads Advanced Tools Center"
section: "guides"
downloaded_at: "2026-10-07"
status: "captured"
---

# Get started with Sponsored Display for all businesses

Note

See the latest Campaign Management APIs here for the latest Campaigns, Ad Groups, Ads, and Targets objects. Use the Ad Product Pill selector to see Sponsored Display.

Amazon Ads has billions of shopping, streaming and browsing signals to help you attract new customers to your small business.

Use the power of our insights to reach relevant audiences throughout their shopping and entertainment journeys with our Sponsored Display ads, even if you do not sell in the Amazon store.

After reading this guide, you should understand the required steps to create a Sponsored Display campaign using our Amazon Ads APIs to advertise products or services not sold on Amazon in categories not already available on Amazon.com.

## Onboarding

### Join Amazon Ads Partner Network

As a partner or agency, looking to get started with Amazon Ads APIs, you will have to set up the Amazon Business Account in Amazon Ads Partner Network.

- Create an Amazon Business Account by following the "Join Partner Network" registration flow.
- You will be prompted to create:
  - Login with Amazon (LwA) account.
  - Amazon Ads Partner Network account (required for business registration).
- Once completed , you will receive an email notification (1-2 business days) about your Amazon Ads Partner Network registration.
- Approved applicants can establish a client application through Login with Amazon (LwA) that serves as a credential for requests to the Amazon Ads API. Note An agency that uses third-party tech partner solutions will need to have their Amazon Ads Manager Account (MA) allowlisted, and must complete the LwA and “Terms & Conditions” terms token acceptance process.

### Create a manager account

After joining partner network, create a manager account which allows to manage multiple advertiser accounts across multiple ad products. Manager accounts help to:

- Link different types of ad accounts.
- Link advertiser accounts in multiple countries.
- Link other manager accounts to view and manage all advertising accounts under the management of your organization in a single place while maintaining data separation for different buying teams.

Refer to this documentation for more details:

- Manager Account in Support Center.
- Manager Account developer guide.

### Complete the API onboarding process

To call Amazon Ads APIs, you will register as a developer to start the LWA application. When approved, this email address will be associated to your Amazon Ads API permissions (SLA for this step is up to 48 hours).

Tip

As a partner, we recommend using an email address that is managed by multiple individuals in your organization.

- Complete the LWA application.
- Apply for API access.
  - When applying for API access select advertising scope to manage ad campaigns and retrieve ads reporting. This is applicable to Sponsored Ads (SD, SP and SB), ADSP and AMC.
- Assign Ads API access to your LWA client application.

### Authorize your LwA application

Once your LwA client application for the Amazon Ads API has been established, any Amazon user account can now authorize your LwA application to access the advertising data and services of that account through the API.

Note

A user account is one which provides authorization to the LWA application of a partner, thereby granting access to their ads data to the partner.

From this point, you will use this Login with Amazon application to create and manage authorization credentials, which must be passed in the headers of any request to the API. To begin, see Getting started.

### Acceptance of Ads Agreement

This is a prerequisite for registering an Ads account through the Amazon Ads API. The purpose of surfacing terms token is to ensure that legal Terms & Conditions (“T&Cs”) are surfaced by the API integrator and are accepted by the LWA user (advertiser who signed into the API service of the partner by using Login with Amazon). This is a 2-step process:

- The API integrator must call POST /termsTokens API to generate a `termsToken` and `termsUrl`. The terms token url will contain a link to the Ads Agreement. Upon clicking that link, an Amazon Ads Agreement page along with the Accept & Continue button will be surfaced to the user.
- The LWA user must accept the Terms & Conditions. Upon the acceptance of Terms & Conditions, a token is activated. Each token is associated with one account request. The terms acceptance rule is the same for single account and bulk account registration.
  - Terms token needs to be accepted once per lifetime of LWA user (the customer who signed into the API service of the partner by using Login With Amazon), it does not need to be used thereafter.

Tip

We recommend showing Terms & Conditions as a one-time pop-up window presented to the advertiser after LwA (login with Amazon) is completed, that auto-closes when user clicks Accept & Continue. The `termsToken` is needed for the registration of your Ads account request in the next step, so keep it available.

### Account registration and billing

Register an Ads account for a business that does not sell on Amazon by calling POST /adsAccounts. Below is an example.

At the moment, the US marketplace is supported for businesses that do not sell on Amazon. There are two methods to do so:

- Single advertiser account creation: A SMB/small business request their agency to create an Ads account on their behalf. Here is the API endpoint for it POST/adsAccounts.
- Bulk Account Creation: We recommend using this option for partners allowing them to create Ads accounts in bulk at once on behalf of several advertisers. Here is the API endpoint: `POST /adsAccounts/batch` that needs to be called and a complete API call example.

Note

To use this API, your Partner Development Manager (PDM) will have to allowlist your Manager Account ID.

### Example request

Create your batch Ads accounts:

```
curl --location  'https://advertising-api.amazon.com//adsAccounts/batch'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxxx'  \
--data  '
{
  "accounts": [
    {
      "accountName": "Test Account Name 1",
      "businessIdentities": [
        {
          "identityType": "NonSellingPartnerId",
          "countryCodes": [
            "US"
          ],
          "attributes": {
            "challenge": "WAF_CAPTCHA",
            "businessFields": {
              "name": "My Advertiser 1",
              "phone": "9876543210",
              "websiteUrl": "www.myawesomeadvertiser.com",
              "addressLine1": "123 Main St",
              "city": "Austin",
              "state": "Texas",
              "zipCode": "78729"
            }
          }
        }
      ]
    }'
```

### Example request

The response immediately returns an account ID in pending status. Registration will happen asynchronously. The index field corresponds to the order in which the accounts are sent in the request. The response immediately returns an account ID in pending status. Full registration then happens asynchronously.

```
{ 
     "success" :   [ 
         { 
             "index" :   0 , 
             "adsAccount" :   { 
                 "accountName" :   "Test Account Name 1" 
                 "adsAccountId" :   "amzn1.REDACTED.<ads-account-id-1>" , 
                 "status" :   "PENDING" 
             } 
         } 
     ] , 
     "errors" :   [ ] 
 }
```

Note

The `Manager Account ID Amazon-Advertising-API-Manager-Account: <partners-network-account-id>` header needs to be passed when the Bulk registration API is called. You can call up to 20 Ads accounts per batch. Please ensure you have accepted the terms token prior to calling the batch API.

### User Permissions and Invitations

A user account permission plays a crucial role in managing access and control over Ads account. Permissions define what actions a user can perform within their Ads account. In the Amazon Ads API, permissions associated with the user account that initiates the authorization grant are crucial for determining whether subsequent API requests will be authorized.

- Setting Permissions: By default, the creator of a Sponsored Ads account has Admin permissions. Admin users can choose from two methods to enable access for other user accounts:
  - Manager Account: Allows advertisers and agencies to link and manage multiple Ads accounts. In API, user performing the linking of accounts must have Admin permission.
  - Access Control: To invite user account to the Ads account and determine the permission level of that user account, call User Invitation APIs. These APIs involve a series of operations to handle invitations from creation, listing to expiration or revocation.

### Set up billing for a newly created account

The Billing APIs setup process process establishes who is going to pay for your advertising spend with Amazon Ads by setting a billing profile and what payment method will be used by setting a payment profile. Billing set up is a prerequisite for creating and advertising campaigns on Amazon.

Below are the types of Payment methods available via API. The definition of each Payment method can be found here:

- PAYBYINVOICE (PBI) - gives eligible Amazon Business customers an extended due date for payment by purchasing on credit.
- CREDIT_CARD - This is available for individual accounts for agency/partner that have a group of advertisers who prefer using their corporate CC on the account directly. You can learn more about payment methods here.
  - You can apply the same CC for payment on multiple ad accounts, but we currently do not support applying CC to multiple accounts in bulk.

Please refer to our Billing API documentation for further details.

## 1. Create a campaign

Use the POST /sd/campaigns endpoint to create a campaign. Advertisers who do not sell on Amazon must use the tactic `T00030` which denotes an audience targeting campaign and define a start date, end date, daily budget (no minimums) to get started. You can choose between a cost type of cost per click (`cpc`) or cost per thousand views (`vcpm`).

### Example requests

CPC campaign:

```
curl --location  'https://advertising-api.amazon.com/sd/campaigns'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxxx'  \
--data  '[
    {
        "name": "test-campaign-1",
        "budgetType": "daily",
        "budget": "10.00",
        "startDate": "20231010",
        "endDate": "20231101",
        "costType": "cpc",
        "state": "paused",
        "tactic": "T00030"
    }
]'
```

vCPM campaign:

```
curl --location  'https://advertising-api.amazon.com/sd/campaigns'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxxx'  \
--data  '[
    {
        "name": "test-campaign-1",
        "budgetType": "daily",
        "budget": "10.00",
        "startDate": "20231010",
        "endDate": "20231101",
        "costType": "vcpm",
        "state": "paused",
        "tactic": "T00030"
    }
]'
```

### Example response

```
[ 
     { 
         "campaignId" :   12345678 , 
         "code" :   "SUCCESS" 
     } 
 ]
```

Record your campaign ID for use in the next step.

## 2. Create one or more ad groups

Once you have created a campaign, you need to create at least one ad group. Use the POST sd/adGroups endpoint to create an ad group using the `campaignId` generated in step 1.

### bidOptimization

The `bidOptimization` in the ad group should correspond to the `costType` you chose for the campaign. `cpc` campaigns must use `clicks` as the `bidOptimization`. `vcpm` campaigns must use `reach` as the `bidOptimization`. For advertisers that do not sell on Amazon, `conversions` is not yet supported.

### creativeType

Ad groups can contain multiple product ads, but only one type of creative. For example, you can have one ad group with multiple image creatives, but you cannot have one ad group that contains both image and video creatives. If you do not enter a `creativeType`, the ad group will use `IMAGE` by default.

### Example requests

CPC campaign:

```
curl --location  'https://advertising-api.amazon.com/sd/adGroups'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxxxx'  \
--data  '[
    {
        "name": "test-adgroup-1",
        "campaignId": 12345678,
        "defaultBid": 1.1,
        "bidOptimization": "clicks",
        "state": "enabled",
        "creativeType": "IMAGE"
    }
]'
```

vCPM campaign:

```
curl --location  'https://advertising-api.amazon.com/sd/adGroups'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxxxx'  \
--data  '[
    {
        "name": "test-adgroup-1",
        "campaignId": 12345678910,
        "defaultBid": 1.3,
        "bidOptimization": "reach",
        "state": "enabled",
        "creativeType": "IMAGE"
    }
]'
```

### Example response

```
[ 
     { 
         "code" :   "SUCCESS" , 
         "adGroupId" :   510480088424692 
     } 
 ]
```

## 3. Add locations (optional)

Advertisers that do not sell on Amazon can use location-based targeting as part of their Sponsored Display campaigns. Locations are optional, but if you want to use them, they should be added after creating product ads and before creating targeting clauses. Within United States, you can target by City, State, Zip code or DMA.

- For more details, see our Locations guide.

Tip

We recommend to target the broadest reach for your business to allow our models to optimize effectively to find the most relevant audiences.

## 3. Add targeting

Advertisers that do not sell on Amazon can use audience targeting in their campaigns. Once you have identified the audience you want to use, you can add targeting clauses at the ad group level using POST /sd/targets. For more information on setting up audience targeting, see Audience targeting campaigns.

- Use the Targetable entities search API to programmatically query for segments or categories to target based on a given a set of keywords. For more information, please click here.
- Alternatively, you can call the these APIs to: (1.) discover audiences by browsing the catalog hierarchy, (2.) apply filters to narrow down to specific audiences, and (3.) identify overlapping audiences.

Tip

We recommend adding at least 15-20 targeting clauses per ad group. Adding more audiences to your ad group will provide our advanced machine learning algorithms with more opportunities to find the most relevant audiences for your business.

### Example request

```
curl --location  'https://advertising-api.amazon.com/sd/targets'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxx'  \
--data  '[
    {
        "expression": [
            {
                "type": "audience",
                "value": [
                    {
                        "type": "audienceSameAs",
                        "value": "370208451989309147"
                    }
                ]
            }
        ],
        "bid": "1.25",
        "adGroupId": 414059429082752,
        "expressionType": "manual",
        "state": "enabled"
    }
]'
```

### Example response

```
[  
  {  
   "code" :   "SUCCESS" ,  
   "description" :   "Estimated audience size: 4.5MM - 5MM" ,  
   "targetId" :   527772488260916  
  }  
 ]
```

## 5. Create one or more product ads

Once you have a campaign and at least one ad group, you can create a product ad using the POST /sd/productAds endpoint. Product ads represent a product or service that you are advertising. For advertisers not selling on Amazon, you must include these parameters including a link to an off-Amazon website landing page for your product or service. Please refer to Sponsored Ads Guidelines and Acceptance Policies for more details.

Note

UTM parameters are supported in the landing page URL.

| Parameter | Description |
| --- | --- |
| `adGroupId` | The ID of the ad group you created in step 2. |
| `campaignId` | The ID of the campaign associated to the ad group. |
| `landingPageURL` | A link to an off-Amazon website landing page for your product or service. |
| `landingPageType` | Always set to `OFF_AMAZON_LINK`. |
| `adName` | A unique name for your ad. |
| `state` | The state of the ad. |

### Example request

```
curl --location  'https://advertising-api.amazon.com/sd/productAds'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxx'  \
--data  '[
  {
    "adGroupId": 10987654321,
    "campaignId": 12345678910,
    "landingPageURL": "https://www.myurl.com",
    "landingPageType": "OFF_AMAZON_LINK",
    "state": "enabled",
    "adName": "My ad"
  }
]'
```

### Example response

```
[ 
     { 
         "code" :   "SUCCESS" , 
         "adId" :   538691658400674 
     } 
 ]
```

## 6a. Add creative assets to an ad

Advertisers that do not sell on Amazon must build a creative to use for a Sponsored Display campaign.

For advertisers that do not sell on Amazon, all creatives require a **headline**, **logo**, and **custom images** (rectangle and square). Any image assets first need to be uploaded using the Asset library API. Once you have uploaded all necessary assets, you can build a creative using the POST /sd/creatives endpoint.

Tip

Custom images allow you to include compelling images that represent your products or brand in context or a lifestyle setting in your ad. Images must be relevant to the landing page destination of your ad, and must be of high-resolution quality and aesthetically pleasing.

Important

At this time, advertisers that do not sell on Amazon can only use image assets in campaign creatives; video assets are not yet supported.

You can learn more about building creatives in our Creative guide.

Example request:

```
curl --location  'https://advertising-api.amazon.com/sd/creatives'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxx'  \
--header  'Content-Type: application/json'  \
--header  'Authorization: Bearer Atza|xxxxxxxxxxxx'  \
--data  '[
    {
        "adGroupId": {{adGroupId}},
        "properties": {
            "headline": "Test headline for Curie Color Picker",
            "brandLogo": {
                "url": "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/75650b78-f9de-48f7-986d-12c4a93b8aaa.png",
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 0,
                    "width": 1124,
                    "height": 1110
                }
            },
            "horizontalImages": [{
                "url": "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/09f71c8c-988c-4b48-8a69-b09a1b4ea979.png",
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 0,
                    "width": 1200,
                    "height": 628
                }
            }],
            "squareImages": [{
                "url": "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/09f71c8c-988c-4b48-8a69-b09a1b4ea979.png",
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 171,
                    "width": 628,
                    "height": 628
                }
            }],
            "verticalImages": [{
                "url": "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/09f71c8c-988c-4b48-8a69-b09a1b4ea979.png",
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 308,
                    "width": 354,
                    "height": 628
                }
            }],
            "backgrounds": [{
                "color": "#288f2f"
            }]
        }
    }
]'
```

### Example response

```
[ 
     { 
         "creativeId" :   873112658567083590 , 
         "code" :   "SUCCESS" 
     } 
 ]
```

## 6b. Add multiple images to creatives

Advertisers can also upload multiple image creatives per `adGroup`. When multiple creatives are available, we will show all creatives in a carousel fashion on selected ad placements where ad slots support carousel format.

For each image asset to be used in the creative, please provide cropping coordinates for all 3 aspect ratios (horizontal image, square image, and vertical image). The cropping coordinates for each image are mandatory. We recommend using the same asset for all aspect ratios and applying cropping coordinates to trim the image. Upload a horizontal image and use the same asset for all aspect ratios with different cropping coordinates. Build a creative using the POST /sd/creatives endpoint.

Minimum pixel requirements for each aspect ratio are:

- `horizontalImage` : Minimum 1200x628 px (1:191 : 1)
- `squareImage` : Minimum 628x628 px (1 : 1)
- `verticalImage` : Minimum 353x628 px (9:16)

Example request:

```
curl --location  'https://advertising-api.amazon.com/sd/creatives'  \
 --header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxx'  \ 
--header  'Content-Type: application/json'  \ 
--header  'Authorization: Bearer Atza|xxxxxxxxxxxx'  \
--data  '[
    {
        "adGroupId": 277557934847123,
        "properties": {
            "headline": "Example headline",
            "brandLogo": {
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 0,
                    "width": 600,
                    "height": 100
                }
            },
            "horizontalImages": [{
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 0,
                    "width": 1200,
                    "height": 628
                }
            },
                        {
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 0,
                    "width": 1200,
                    "height": 628
                }
            }],
            "squareImages": [{
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 171,
                    "width": 628,
                    "height": 628
                }
            },{
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 171,
                    "width": 628,
                    "height": 628
                }
            }],
            "verticalImages": [{
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 308,
                    "width": 354,
                    "height": 628
                }
            },{
                "assetId": "amzn1.REDACTED",
                "assetVersion": "version_v1",
                "croppingCoordinates": {
                    "top": 0,
                    "left": 308,
                    "width": 354,
                    "height": 628
                }
            }]
        }
    }
]'
```

### Example response

```
[ 
     { 
     "creativeId" :   872345678185111234 , 
     "code" :   "SUCCESS" 
     } 
 ]
```

## 7. Pre-Moderation API (optional)

For advertisers launching Sponsored Display campaigns, the unified pre-moderation API offers real-time policy guidance based on the technical, creative, and policy components of an ad. The unified pre-moderation API ensures ad compliance before moderation, enabling alignment with sponsored ads policy guidelines.

- Refer to the pre-moderation guide for common reasons a campaign might be rejected during moderation review. A pre-moderation API sample can be found here, along with links to relevant ad policies for additional explanation of the guidelines.

Tip

This endpoint will reduce the punctuation, grammar, spelling errors, capitalization, and spacing errors that may cause your ads to get rejected.

## 8. Moderation check

Once you have created a campaign, ad group, product ad, and targeting clauses, your campaign is ready to begin serving on your inputted start date. Note that your campaign must go through our moderation process and be approved to begin serving ads. While moderation is taking place, your ad will be under “Pending review” status for up to 72 hours.

### Moderation status for ad landing page

You can call the `POST` moderation/results API to get the moderation status of the landing page of your ad. This API will return a moderation status of approved or rejected for the given ad.

### Example request

Set the `adProgramType` parameter to `SPONSORED_DISPLAY` . The `id` value is the `adId` retrieved in step 5.

```
curl --location  'https://advertising-api.amazon.com/moderation/results'  \
--header  'Content-Type: application/vnd.moderationresultsrequest.v4.1+json'  \ 
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Authorization: Bearer Atza|xxxxxxx'  \
--header  'Amazon-Advertising-API-Scope: xxxxxxxxxx'  \
--data-raw  '[
    {
        "versionIdFilter": [],
        "idType": "AD_ID",
        "adProgramType": "SPONSORED_DISPLAY",
        "nextToken": null,
        "maxResults": 1,
        "moderationStatusFilter": [],
        "id": "300088527590102"
    }
]'
```

### Response with approved moderation status

```
{ 
     "moderationResults" :   [ { 
         "versionId" :   "1.0" , 
         "idType" :   "AD_ID" , 
         "id" :   "300088527590102" , 
         "moderationStatus" :   "APPROVED" , 
         "policyViolations" :   [   ] 
     } ] 

 }
```

### Response with rejected moderation status

```
{ 
     "nextToken" :   null , 
     "moderationResults" :   [ { 
         "id" :   "300090250700402" , 
         "idType" :   "AD_ID" , 
         "versionId" :   "1.0" , 
         "moderationStatus" :   "REJECTED" , 
         "etaForModeration" :   null , 
         "policyViolations" :   [ { 
             "policyLinkUrl" :   "https://advertising.amazon.com/en-us/resources/ad-policy/creative-acceptance?ref_=a20m_us_spcs_cap#prohibitedproductsandservices" , 
             "policyDescription" :   "The content or product(s) isn't policy compliant." , 
             "violatingTextContents" :   [ { 
                 "moderatedComponent" :   "landing_page" , 
                 "reviewedText" :   "https://www.testpage.com" , 
                 "violatingTextEvidences" :   [ { 
                     "violatingText" :   "https://www.testpage.com" , 
                     "violatingTextPosition" :   { 
                         "start" :   0 , 
                         "end" :   21 
                     } 
                 } ] 
             } ] , 
             "violatingImageContents" :   [ ] , 
             "violatingVideoContents" :   [ ] , 
             "violatingAsinContents" :   [ ] 
         } ] 
     } ] 
 }
```

### Moderation status for an ad creative

You can call the `GET` /sd/creatives API to get the moderation status of an ad creative. This API will return detailed rejection reasons for ad creatives if rejected by moderation. This API accepts either `adGroupId` or `creativeId` as filter parameters. The `creativeId` filter will return the moderation results for that creative. The `adGroupId` filter will return the moderation status of all creatives under that ad group.

### Request with creative ID

```
curl --location --request GET  'https://advertising-api.amazon.com/sd/creatives?language=en-US&creativeIdFilter=354572625772967'  \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Amazon-Advertising-API-Scope: xxxxxx'  \
--header  'Accept: application/json'  \
--header  'Authorization: Bearer Atza|xxxxxx
```

### Response if moderation is approved

```
[ 
     { 
         "creativeId" :   869892967981643111 , 
         "moderationStatus" :   "APPROVED" , 
         "etaForModeration" :   null , 
         "policyViolations" :   [ ] 
     } 
 ]
```

### Response if moderation is rejected

```
[ { 
     "creativeId" :   871494925610510680 , 
     "moderationStatus" :   "REJECTED" , 
     "etaForModeration" :   null , 
     "policyViolations" :   [ { 
         "policyDescription" :   "The content or product(s) isn't policy compliant." , 
         "policyLinkUrl" :   "https://advertising.amazon.com/en-us/resources/ad-policy/creative-acceptance?ref_=a20m_us_spcs_cap#prohibitedproductsandservices" , 
         "violatingHeadlineContents" :   [ { 
             "reviewedText" :   "sample" , 
             "textEvidence" :   [ { 
                 "violatingText" :   "sample" , 
                 "violatingTextPosition" :   { 
                     "start" :   0 , 
                     "end" :   6 
                 } 
             } ] 
         } ] , 
         "violatingBrandLogoContents" :   [ { 
             "reviewedImageUrl" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/c9f2412d-7c1b-4964-9907-936077b53187.png" , 
             "imageEvidences" :   [ { 
                 "violatingImageCrop" :   { 
                     "topLeftX" :   0 , 
                     "topLeftY" :   0 , 
                     "height" :   790 , 
                     "width" :   1023 
                 } 
             } ] 
         } ] , 
         "violatingCustomImageContents" :   [ { 
                 "reviewedImageUrl" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/dea0f804-a411-4244-beef-83406665e932.jpeg" , 
                 "imageEvidences" :   [ { 
                     "violatingImageCrop" :   { 
                         "topLeftX" :   0 , 
                         "topLeftY" :   0 , 
                         "height" :   1200 , 
                         "width" :   1920 
                     } 
                 } ] 
             } , 
             { 
                 "reviewedImageUrl" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/dea0f804-a411-4244-beef-83406665e932.jpeg" , 
                 "imageEvidences" :   [ { 
                     "violatingImageCrop" :   { 
                         "topLeftX" :   0 , 
                         "topLeftY" :   0 , 
                         "height" :   1200 , 
                         "width" :   1920 
                     } 
                 } ] 
             } , 
             { 
                 "reviewedImageUrl" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/dea0f804-a411-4244-beef-83406665e932.jpeg" , 
                 "imageEvidences" :   [ { 
                     "violatingImageCrop" :   { 
                         "topLeftX" :   0 , 
                         "topLeftY" :   0 , 
                         "height" :   1200 , 
                         "width" :   1920 
                     } 
                 } ] 
             } 
         ] , 
         "violatingVideoContents" :   [ ] 
     } ] 
 } ]
```

### Request with ad group ID

```
curl --location --request GET  '[https://advertising-api.amazon.com/sd/creatives?adGroupIdFilter=354572625772967' ](https://advertising-api.amazon.com/sd/creatives?adGroupIdFilter=354572625772967) \
--header  'Amazon-Advertising-API-ClientId: amzn1.REDACTED'  \
--header  'Amazon-Advertising-API-Scope: xxxxxx'  \
--header  'Accept: application/json'  \
--header  'Authorization: Bearer Atza|xxxxxx
```

### Response with moderation rejected

```
[ 
     { 
         "creativeId" :   "869892967981643111" , 
         "adGroupId" :   "511558610648815" , 
         "creative" :   { 
             "headline" :   "No color - reach in flight" , 
             "hasTermsAndConditions" :   null , 
             "creativeBrandLogo" :   { 
                 "url" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/d4c96cab-ec2e-4485-a47a-c686a2a5d6d9.png" , 
                 "assetId" :   "amzn1.REDACTED" , 
                 "assetVersion" :   "version_v1" , 
                 "croppingCoordinates" :   { 
                     "top" :   0 , 
                     "left" :   0 , 
                     "width" :   2976 , 
                     "height" :   834 
                 } , 
                 "rectCustomImage" :   null , 
                 "squareCustomImage" :   null , 
                 "squareImages" :   null , 
                 "horizontalImages" :   null , 
                 "verticalImages" :   null 
             } , 
             "creativeType" :   null , 
             "customImage" :   { 
                 "url" :   null , 
                 "assetId" :   null , 
                 "assetVersion" :   null , 
                 "croppingCoordinates" :   null , 
                 "rectCustomImage" :   null , 
                 "squareCustomImage" :   null , 
                 "squareImages" :   [ 
                     { 
                         "url" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/d4c96cab-ec2e-4485-a47a-c686a2a5d6d9.png" , 
                         "assetId" :   "amzn1.REDACTED" , 
                         "assetVersion" :   "version_v1" , 
                         "croppingCoordinates" :   { 
                             "top" :   0 , 
                             "left" :   382 , 
                             "width" :   834 , 
                             "height" :   834 
                         } 
                     } 
                 ] , 
                 "horizontalImages" :   [ 
                     { 
                         "url" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/d4c96cab-ec2e-4485-a47a-c686a2a5d6d9.png" , 
                         "assetId" :   "amzn1.REDACTED" , 
                         "assetVersion" :   "version_v1" , 
                         "croppingCoordinates" :   { 
                             "top" :   0 , 
                             "left" :   3 , 
                             "width" :   1593 , 
                             "height" :   834 
                         } 
                     } 
                 ] , 
                 "verticalImages" :   [ 
                     { 
                         "url" :   "https://m.media-amazon.com/images/S/al-na-9d5791cf-3faf/d4c96cab-ec2e-4485-a47a-c686a2a5d6d9.png" , 
                         "assetId" :   "amzn1.REDACTED" , 
                         "assetVersion" :   "version_v1" , 
                         "croppingCoordinates" :   { 
                             "top" :   0 , 
                             "left" :   564 , 
                             "width" :   470 , 
                             "height" :   834 
                         } 
                     } 
                 ] 
             } , 
             "video" :   null , 
             "callToActions" :   null , 
             "backgrounds" :   [ 
                 { 
                     "color" :   "#53a07b" 
                 } 
             ] 
         } , 
         "moderationStatus" :   "APPROVED" 
     } 
 ]
```

## Next steps

### Reporting

To view campaign performance data, you can use the reporting API.

For more information, see:

- Report types
- Get started with reporting

Note

Restatements - Given small changes to impression and click data may happen up to 3 days after the initial click date due to the traffic validation process. We recommend retrieving click and impression data again after three days to ensure you have the latest data.
