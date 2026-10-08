---
title: "Consent requirements for Events Manager (AAT)"
source_url: "https://advertising.amazon.com/help/G2648JUCRZU662V5"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Country code and consent requirements for Events Manager (AAT)

Learn about country code and consent requirements for Amazon Ad Tag (AAT).

Updated on Aug 5, 2026

## What are country code and consent requirements?

Amazon Ad Tag (AAT) allows you to understand events that users take on your website in a privacy-safe manner. To process incoming data, Amazon requires specific information depending on the origin of the request.

**Country code** is always required. Include a countryCode field in the AAT payload to indicate the legal origin of the request. The country code follows the ISO 3166 two-letter format and must be provided in uppercase (Example: 'US', 'GB', 'FR', 'JP').

**Consent signal** is additionally required for the European Economic Area (EEA). If data originates from the EEA, you must provide a consent signal to communicate your users' privacy choices to Amazon Ads.

## Why do you need to send country code and consent?

Country code and consent signals ensure that Amazon processes your data in compliance with regional privacy regulations. Without a valid country code, Amazon can't determine the legal origin of the request and your data won't be processed.

Note: Amazon Ad Tag now requires country code and consent information for EEA as part of the AAT payload.

## Consent signal options for EEA

To meet consent requirements in the EEA, provide one of the following signals:

- Transparency and Consent Framework (TCF) by Interactive Advertising Bureau (IAB) - This is the recommended option. Refer to How to Send TCF to AAT when sending TCF signals.
- Global Privacy Protocol (GPP)
- Amazon Consent Signal (ACS): Refer to the ACS CMP Integration Guide, when sending ACS signals.

You can send consent using a third-party or advertiser-owned consent management platform (CMP).

Only ACS signals with granted EnableAdStorage and amznUserData can be processed in EEA. Don't send multiple signals. If multiple signals are provided, Amazon Ads uses TCF and ignores ACS. For more information on ACS, refer to 'Amazon Consent Signal (ACS) integration guide for consent management platforms'.

## How ConsentJS works

ConsentJS is a script that you include on your website that provides the advertiser API for setting country code and consent values. It exposes window.amznConsent, which you can use in two ways. Both approaches produce the same result.

- **Builder pattern** - chain methods to construct your consent object window.amznConsent() // returns a ConsentBuilder .setCountryCode('US') .setEnableAdStorage(true) .setEnableUserData(true) .build(); // validates, formats, stores in Ad Tag
- **Direct object** - pass a complete consent object directly window.amznConsent({ countryCode: 'US', enableAdStorage: true, enableUserData: true });

## Setup and Payload Examples

Amazon differentiates between basic setups and specific requirements in EEA countries. For the consent signal, we consider all three available options: TCF, GGP, and ACS.

Note: The examples provided represent minimum signals for the given setup. Your signals can look different.

**Setup without Consent** (applicable for countries outside EEA):

- North America (NA): For advertising activities in the USA or Canada TCF doesn’t apply. GPP may apply for US state laws (CCPA/CPRA) but is optional.
- Asia Pacific: For advertising activities in Japan, Australia, and other far East region the same requirements apply as for the NA.

- Country Code = US
- No consent signal is provided (null)

**Advertiser definition**

```
window.amznConsent() 
.setCountryCode('US')  
.setEnableAdStorage(true)  
.setEnableUserData(true)  
.build();
```

**Formatted payload**

```
{ 
 "geo": {"countryCode": "US"}, 
 "amazonConsentFormat": { 
 "amznAdStorage": "GRANTED", 
 "amznUserData": "GRANTED" 
 }, 
 "gpp": "", 
 "tcf": "", 
 "timestamp": "2026-03-02T10:00:00.000Z", 
 "version": "1" 
}
```

As the Country Code ‘US' doesn’t require a consent signal, Amazon will be able to process this data.

- Country Code = CA
- ACS provided

**Advertiser definition**

```
window.amznConsent() 
.setCountryCode('CA')  
.setEnableAdStorage(true)  
.setEnableUserData(true)  
.build();
```

**Formatted payload**

```
{ 
 "geo": {"countryCode": "CA"}, 
 "amazonConsentFormat": { 
 "amznAdStorage": "GRANTED", 
 "amznUserData": "GRANTED" 
 }, 
 "gpp": "", 
 "tcf": "", 
 "timestamp": "2025-03-02T10:00:00.000Z", 
 "version": "1" 
}
```

In this scenario, ACS was provided and permissions for amznAdStorage and amznUserData have been received from the user.

**Setup with Consent for EEA activities:** For AAT conversions within the European Economic Region (EEA, EU + UK), a consent signal is required for data processing. Amazon offers three options to provide a consent signal: TCF, GPP, and ACS. TCF and GPP are common industry standards. Most advertisers will rely on an IAB-certified Consent Management Platform (CMP) to collect and communicate consent information. Example CMPs include OneTrust, Cookie bot, or Quantcast. Please check the documentation of your CMP for information on how to communicate countryCode and Consent information for Amazon Ads.

For custom consent signal collections, the Amazon Consent Signal (ACS) can be used. Below are the definitions and resulting payloads for different examples:

- Country Code = FR
- TCF provided

**Advertiser definition**

```
// Advertiser gets TCF string from their CMP's __tcfapi() 
 
window.__tcfapi('getTCData', 2, function(tcData) { 
 window.amznConsent() 
 .setCountryCode('FR') // France 
 .setTcf(tcData.tcString) // IAB TCF v2 consent string from CMP 
 .build(); 
});
```

**Formatted payload**

```
{ 
 "geo": {"countryCode": "FR"}, 
 "tcf": "CQHcCQAQHcCQAPoABAENBOFgAAAAAH_AAAqIAPgAAAAA", 
 "timestamp": "2025-03-02T10:00:00.000Z", 
 "version": "1" 
}
```

- Country Code = GB
- GPP provided

Advertisers using newer CMPs that support the IAB GPP framework (which can encode TCF, USP, and other signals in a single string).

**Advertiser definition**

```
// Advertiser gets GPP string from their CMP's __gpp() API 
 
window.__gpp('getGPPData', function(gppData) { 
 window.amznConsent() 
 .setCountryCode('GB') // United Kingdom 
 .setGpp(gppData.gppString) // IAB GPP string from CMP 
 .build(); 
})
```

**Formatted payload**

```
{ 
 "geo": {"countryCode": "GB"}, 
 "gpp": "DBABLA~BVVqAAAACCA.QA", 
 "timestamp": "2025-03-02T10:00:00.000Z", 
 "version": "1" 
}
```

- Country Code = GB
- ACS provided

Advertisers who don’t use a CMP or don’t have TCF/GPP strings can rely on Amazon’s Consent Signal (ACS).

**Advertiser definition**

```
// Advertiser manages their own consent UI/banner 
 window.amznConsent() 
.setCountryCode('GB')  
.setEnableAdStorage(true)  
.setEnableUserData(true)  
.build();
```

**Formatted payload**

```
{ 
 "geo": {"countryCode": "GB"}, 
 "amazonConsentFormat": { 
 "amznAdStorage": "GRANTED", 
 "amznUserData": "GRANTED" 
 }, 
 "gpp": "", 
 "tcf": "", 
 "timestamp": "2025-03-02T10:00:00.000Z", 
 "version": "1" 
}
```

This is a simplified example for a website on which the Amazon Ad Tag is implemented. The signal is collected in France, which requires a consent signal. In this example, ACS is used (hard coded in this example). We assume that consent is granted by the user.

Note: The consent.js is loaded before the AAT script.

```
<html lang='en'> 
<head> 
<title>Ad Tag Test</title> <!-- Load ACS library first --> 
 
<script src="https://c.amazon-adsystem.com/aat/amzn-consent.js"></script> <!-- Set consent BEFORE loading ad tag --> 
<script> 
window.amznConsent() 
.setCountryCode('FR') 
.setEnableAdStorage(true) 
.setEnableUserData(true) 
.build(); 
</script> <!-- Load Amazon Ad Tag --> 
<script> 
!function(w,d,s,t,a){if(w.amzn)return;w.amzn=a=function(){w.amzn.q.push([arguments,(new Date).getTime()])};a.q=[];a.version="0.0";s=d.createElement("script");s.src="https://c.amazon-adsystem.com/aat/amzn.js";s.id="amzn-pixel";s.async=true;t=d.getElementsByTagName("script")[0];t.parentNode.insertBefore(s,t)}(window,document); 
amzn("addTag", "768411f6-fa20-33cd-2222-8cdf646d1111"); 
amzn("trackEvent", "PageView"); 
</script> 
</head> 
<body> 
<h1>Ad Tag Example Page</h1> 
<p>This page tests Amazon Ad Tag integration with ACS consent management for France (FR). Consent is set to GRANTED for both ad storage and user data.</p> 
</body> 
</html>
```

The resulting payload for this example website would look like this:

```
{ 
 "pid": "768411f6-fa20-33cd-2222-8cdf646d1111", 
 "event": "PageView", 
 "ts": "1772788831804", 
 "amazonConsentString": "{\"geo\":{\"countryCode\":\"FR\"},\"consent\":{\"amazonConsentFormat\":{\"amzn_ad_storage\":\"GRANTED\",\"amzn_user_data\":\"GRANTED\"}}}", 
 "eventSource": "amzn.js", 
 "uuid": "dfe0ee5f-d312-4acb-9fae-68dabef771c7" 
}
```
