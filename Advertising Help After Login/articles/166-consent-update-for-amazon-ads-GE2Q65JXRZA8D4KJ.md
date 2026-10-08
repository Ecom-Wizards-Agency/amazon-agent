---
title: "Consent update for Amazon Ads"
source_url: "https://advertising.amazon.com/help/GE2Q65JXRZA8D4KJ"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Consent update for Amazon Ads

Learn about consent signal requirements for transmitting personal information to Amazon Ads in the UK and EEA.

Updated on Oct 31, 2025

When transmitting any personal information to Amazon Ads in the United Kingdom (UK) and European Economic Area (EEA), you must provide a valid consent signal and the country code in which the customer granted the consent.

**Consent Signal**

You can either use (i) the Interactive Advertising Bureau (IAB) European Transparency and Consent Framework (TCF) signals, (ii) the Global Privacy Protocol (GPP), or (iii) the Amazon Consent Signal (ACS), to communicate UK and EEA users’ privacy choices to Amazon Ads.

Note: Make sure that you don’t send multiple signals. If multiple signals are provided, Amazon Ads will use TCF and ignore ACS.

**Country Code**

You must share a country code when passing customers’ consented data to Amazon Ads. The country code is a 2-character string in the ISO 3166 format that indicates in which country the consent was given (for example, US, GB or DE).

Note: Data uploaded without specifying a country code will be rejected.

## Amazon Consent Signal

In addition to supporting the IAB’s TCF signal and GPP, you can also use ACS to transmit the end users' privacy choices to Amazon Ads in the UK and EEA. There are 3 required parameters:

- CountryCode: The country code indicates where consent was given by the user. Acceptable values: 2-character ISO 3166 format (for example, US, GB, DE).
- amzn_user_data: Indicates whether the user has consented to Amazon processing personal data (for example, an advertising identifier) for advertising purposes. Acceptable values are "GRANTED" or "DENIED."
- amzn_ad_storage: Indicates whether the user has given Amazon consent to read or write advertising cookies or similar technologies on the user's device. Accepted inputs: "GRANTED," "DENIED," or "NULL."

Note: When amzn_ad_storage isn’t relevant, the acceptable value is " NULL" or third parties can exclude the parameter entirely.

Refer to Sending Personal Information to Amazon Ads and Amazon Consent Signal requirements for additional details.
