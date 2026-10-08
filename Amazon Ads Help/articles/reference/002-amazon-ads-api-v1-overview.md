---
title: "Amazon Ads API v1 overview"
source_url: "https://advertising.amazon.com/API/docs/en-us/reference/amazon-ads/overview"
library: "Amazon Ads Advanced Tools Center"
section: "reference"
downloaded_at: "2026-10-07"
status: "captured"
---

# Amazon Ads API v1 overview

The Amazon Ads API v1 represents a reimagined approach to the Ads API, built from the ground up with consistency and efficiency in mind. The new API provides a seamless experience across all Amazon advertising products through a common model. This common model introduces standard concepts and naming and consistent API behavior across Sponsored Products, Sponsored Brands, Sponsored Display, Sponsored Television, and Amazon DSP.

If you are just starting out using Amazon Ads APIs, we highly recommend using these v1 APIs. They will eventually fully replace the ad product-specific APIs.

Getting started with Amazon Ads API v1

To learn about prerequisites, header values, and access, see Get started with Amazon Ads API v1. To get started with campaign management, see the campaign management overview and entity guides.

## Key benefits

- **Consistent experience**: Common field names, error handling, and resource patterns across all advertising products
- **Reduced development effort**: Significantly less code duplication when implementing features across multiple ad products
- **Single integration**: Integrate once and access multiple ad products (Sponsored Products, Sponsored Brands, Sponsored Display, etc.) through a consistent API interface
- **Future-ready**: New features and ad products will be built into this consistent framework
- **Predictable updates**: Clear versioning strategy, support windows, and deprecation timelines for major versions

## Vision

The Amazon Ads API v1 establishes the foundation for all future Amazon Ads API development. The vision includes:

- Building all new features and capabilities into the common model
- Expanding the common model across all advertising products
- Maintaining predictable release cycles and deprecation schedules
- Providing a seamless upgrade path for developers

## Developer experience

This new API structure is designed to make the development process more efficient:

- Consistent error codes and messaging across products
- Simplified documentation and implementation guides
- Reusable code patterns across different ad products
- Reduced time to market for new feature adoption
- Consistent OAS file and namespacing that makes for easy generation or integration into a client

## General availability and beta releases

For v1 APIs in beta, see Betas. APIs that have been released will be visible in the v1 API spec.

For news on feature expansions and other updates, see API v1 release notes.

## Future vision

The long-term vision for the Ads API v1 is to continue expanding the coverage of Amazon advertising products and features. We plan to generate all APIs in the Ads API v1 from a common domain model, ensuring consistent data representations and functionality across ad products. This will enable us to quickly add new ad products and features to the Ads API v1 while maintaining a consistent developer experience.

Some of the key areas we expect to expand in the future include support for:

- reporting
- recommendations
- rules
- media planning

Please let us know which features you would like to see developed and generated from a common domain model first according to priorities and where you see the most divergences today that cause inefficiency. You can submit feedback to the team via Jira.
