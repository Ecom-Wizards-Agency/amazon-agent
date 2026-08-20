---
name: amazon-ads
description: Use for day-to-day Amazon Ads Console work: bidding, budgets, placements, targeting, campaign settings and troubleshooting, billing warnings, and SB/SD/DSP questions. Not for: creating SP campaigns from a brief (amazon-campaign-builder), ad/sales audits (amazon-audit), Creator Connections (amazon-creator-connections), or report pulls (amazon-reporting).
---

# Amazon Ads

For Sponsored Brands video concept tests, use `<vault>/Playbooks/amazon-sb-video-concept-testing-playbook.md` (team vault, resolved via `AMAZON_AGENT_TEAM_VAULT` or `_local/team-vault-path.txt`) as the canonical measurement method. Keep live tests in the existing Notion A/B Test Program. Do not copy the method into editor briefings or Creative References.

Browser: CDP (Ads Campaign Manager; stop before changes).

## Doctrine and recall

Run `python3 tools/ads_recall.py console` before campaign work and read the returned decision, Playbook, and matching Research files in order. Skip this step quietly when the helper returns no paths. Numeric operating thresholds belong only in `_local/ads-strategy/strategy.json`; do not copy or infer them in this skill. The ownership map is `docs/ads-doctrine-sources.md`.

Sponsored Products remain the core agency doctrine. Sponsored Brands, Sponsored Display, DSP, AMC, and Brand Store work is modular: verify the marketplace mechanics and define that module's objective, economics, measurement, creative, approvals, and interaction with SP before acting. Never invent a universal spend percentage. Sponsored Products BMM is unsupported and carries plain-Broad risk; do not create it. Sponsored Brands BMM remains available only where current Amazon documentation supports it.

## Workflow

1. Use `https://advertising.amazon.com/campaign-manager` as the starting point for Ads Console work.
2. Verify advertiser/account, brand, country, marketplace, and date range.
3. Load the doctrine recall set above.
4. Search Advertising Help After Login for current Ads Console UI behavior.
5. Search Amazon Ads Help for API, bulk/no-code tools, and technical docs.
6. Use internal strategy notes for campaign logic and MAG SOPs for practical operator steps.
7. Stop before saving bids, budgets, targeting, campaigns, billing/payment settings, scheduled reports, or Creator Connections sends.

Creator Connections route: Campaign Manager > account selector > Brand content > Creator connections.
