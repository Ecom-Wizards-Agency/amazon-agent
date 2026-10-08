---
title: "Amazon Consent Signal (ACS) integration guide for consent management platforms"
source_url: "https://advertising.amazon.com/help/GKJQ7E8SE9BRG73Q"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon Consent Signal (ACS) integration guide for consent management platforms

Learn how to send Amazon Consent Signal (ACS) using JavaScript integrations.

Updated on Aug 11, 2026

Advertisers can send Amazon Consent using either Consent Management Platforms (CMP) or their own Consent Management banner.

To streamline the integration process, Amazon Ads has developed a JavaScript library that simplifies how third parties integrate Amazon Consent Signal (ACS) into their CMP by triggering the amznConsent call, as outlined below. Implementation can be done either by the CMP or directly by advertisers with their own consent management banner implementation.

Note: Make sure that you don’t send multiple signals. If multiple signals are provided, Amazon Ads will use TCF and ignore ACS.

## Country code requirement

A 2-character country code in ISO 3166 format is required for all data uploads to Amazon Ads, regardless of region. The country code represents the jurisdiction whose laws apply to processing the user's data.

- Data uploaded without a country code will be rejected.
- If no country code is provided, Amazon Ads defaults to the most conservative processing logic.

## Import the ACS-JS library to the CMP banner

```
<script src="https://c.amazon-adsystem.com/aat/amzn-consent.js"></script>
```

When the script loads, all consent settings are defaulted to 'DENIED.' These settings remain in place until the user interacts with the CMP (Example**:** clicking **Accept**), at which point the CMP should update the consent state using the amznConsent method.

## Passing consent from CMP banner to ACS-JS

Both of the options below will set a domain 1P JS cookie (amzn_consent) as well as trigger a browser event (amznConsentChange). This method won’t work if the CMP integration can’t set 1P cookies.

If Amazon Ad Tag (amzn.js) is also integrated with the advertiser website, it will listen to the browser event (amznConsentChange) and/or check for the 1P cookie (amzn_consent) and ensure future event triggers and collection of 1P user data are restricted based on the consent provided. The latest production version of Amazon Ad Tag (amzn.js) has been updated to interoperate with Amazon Consent Library (amzn-consent.js).

**Option 1:** Builder Pattern (Recommended)

```
window.amznConsent()
    .setIpAddress('192.168.1.1')
    .setCountryCode('UK')
    .setEnableAdStorage('GRANTED')
    .setEnableUserData('DENIED')
    .build();
```

**Option 2:** Direct Initialization by providing the JSON object (Not Recommended)

```
window.amznConsent({
    ipAddress: '192.168.1.1',
    countryCode: 'UK',
    enableAdStorage: 'GRANTED',
    enableUserData: 'DENIED',

      });
```

**Key fields and requirements**

The following fields are required.

| Field | Description | Values | Requirement |
| --- | --- | --- | --- |
| Geo.CountryCode | The 2-character ISO 3166 country code where consent was granted. | Examples: UK, DE, FR | Required for all data uploads globally |
| Consent.AmazonConsentFormat.amzn_user_data | Indicates whether the user has consented to Amazon processing personal data (for example, an advertising identifier) for advertising purposes. | "GRANTED" or "DENIED" | Required for UK and EEA country codes |
| Consent.AmazonConsentFormat.amzn_ad_storage | Indicates whether the user has given Amazon consent to read or write advertising cookies or similar technologies on the user's device. | "GRANTED" or "DENIED" | Required for UK and EEA country codes |

Note: Data uploaded without specifying a country code will be rejected.
