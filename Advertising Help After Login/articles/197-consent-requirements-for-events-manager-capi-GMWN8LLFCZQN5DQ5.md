---
title: "Consent requirements for Events Manager (CAPI)"
source_url: "https://advertising.amazon.com/help/GMWN8LLFCZQN5DQ5"
library: "Amazon Ads Support Center"
section: "linked-expansion"
downloaded_at: "2026-10-07"
status: "captured"
---

# Consent requirements for Events Manager (CAPI)

Learn about consent requirements for Amazon Conversions API (CAPI) in the UK and EEA.

Updated on Oct 31, 2025

Amazon Conversions API (CAPI) allows advertisers to send real-time and offline conversion event data via server-to-server integration. It can be used to send data directly from an advertiser’s server to Amazon Ads or from advertiser’s preferred customer data platform (CDP). If you use the CAPI, you must either use (i) the Interactive Advertising Bureau (IAB) European Transparency and Consent Framework (TCF) signals, (ii) the Global Privacy Protocol (GPP) or (iii) Amazon Consent Signal (ACS), to communicate your United Kingdom (UK) and European Economic Area (EEA) users’ privacy choices to Amazon Ads.

You can pass consented events using either a partner or an advertiser-owned CAPI connector, or by using a mobile measurement partner (MMP).

## Partner CAPI connector

Amazon Ads supports many widely used partners to simplify the setup of ACS. If you use a CAPI partner, please refer to your provider’s documentation for guidance on enabling ACS and ensuring UK and EEA users’ privacy choices are correctly communicated to Amazon Ads.

If your CAPI partner supports the IAB TCF or GPP, you can choose to share either TCF or GPP as your preferred consent signal.

Note: If you’re unsure whether your CAPI partner supports ACS, contact your CAPI partner or your Amazon Ads representative for guidance.

## Advertiser-owned CAPI connector

Customers using the CAPI to import events that originate from their web, app, or offline properties directly must either use the IAB European TCF signals, the GPP, or ACS, to communicate their UK and EEA users’ privacy choices to Amazon Ads.

Refer to the Events API Instruction Guide for additional details.

## MMP

Amazon Ads supports many widely used MMPs to simplify the setup of ACS. If you use an MMP, please refer to your provider’s documentation for guidance on enabling ACS and ensuring UK and EEA users’ privacy choices are correctly communicated to Amazon Ads.

If your MMP supports the IAB TCF or the GPP, you can choose to share either TCF or GPP as your preferred consent signal.

Note: If you’re unsure whether your MMP supports ACS, contact your MMP or your Amazon Ads representative for guidance.

Refer to Mobile Measurement Partners Support for additional details.
