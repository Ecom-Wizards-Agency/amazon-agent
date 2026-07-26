---
name: amazon-sqp-competitor-check
description: Check keyword-level competitors in Amazon Brand Analytics Search Query Performance (SQP) via the Seller Central UI. Trigger on "SQP competitor check" or when per-query competitor ASIN shares/prices are needed (AdLabs MCP only exposes our own share). Read-only; browser capture runs in Codex when Claude has no connected session. Codex twin: ~/.codex/skills/amazon-sqp-competitor-check/SKILL.md.
---

# Amazon SQP Competitor Check

Browser: Mixed (Claude coordinates and analyzes; the Seller Central capture runs in Codex when Claude has no connected session).

You are working hand in hand with Codex to check keyword-level competitors in Amazon Brand Analytics Search Query Performance (SQP).

Inputs:
- Client or seller account: [ACCOUNT]
- Marketplace: [MARKETPLACE]
- Target ASIN: [ASIN]
- Exact keywords: [KEYWORD LIST]
- Reporting range and period: [RANGE / WEEK]
- Requested output: [FORMAT OR DESTINATION]

Workflow:

1. Determine whether you have explicit permission and a connected Seller Central browser session.
2. If interactive browser access is unavailable, prepare a precise Codex handoff using the inputs above. Do not guess Amazon data.
3. Codex should use Chrome and verify:
   - Seller Central is logged in
   - The correct seller account is selected
   - The correct marketplace is selected
   - Brand Analytics and Search Query Performance are open
   - The requested reporting period is active
4. Open Brand Analytics -> Search Analytics -> Search query performance.
5. Select ASIN view.
6. Select the exact target ASIN and verify its product title.
7. Select and apply the requested reporting range and period.
8. For each exact keyword:
   - Open the exact matching query.
   - Do not merge spelling variants, translations, or singular/plural forms.
   - If the query is absent, record it as not present for that ASIN and period.
   - Verify the query, ASIN, marketplace, and reporting period on the detail page.
   - Capture query volume, total impressions, total clicks, and click rate.
   - Capture the target ASIN's impressions, impression share, clicks, and click share.
   - Capture the top 10 ASINs shown by Amazon, including product title, ASIN, brand, median price, impressions, impression share, clicks, and click share.
9. Keep the target ASIN in the benchmark table, but exclude it from any list labeled "competitors."
10. Treat Amazon's displayed order as its top-ASIN comparison order. Do not re-label it as a ranking by impressions or clicks.
11. Compare click share against impression share as a diagnostic signal. Do not claim causation without supporting evidence.
12. Keep the workflow read-only. Stop if Amazon requests login credentials, an OTP, or authentication.

If Codex must perform the browser capture, output this handoff:

```
CODEX HANDOFF: SQP COMPETITOR CAPTURE

Account: [ACCOUNT]
Marketplace: [MARKETPLACE]
Target ASIN: [ASIN]
Exact keywords: [KEYWORDS]
Reporting period: [PERIOD]

For each keyword, return:
- Query volume
- Total impressions
- Total clicks
- Click rate
- Target-ASIN impressions
- Target-ASIN impression share
- Target-ASIN clicks
- Target-ASIN click share
- Amazon's displayed top-10 ASIN table
- Missing-data or UI caveats
```

After Codex returns the capture, analyze it using this table:

| Amazon order | Product | ASIN | Brand | Median price | Impressions | Impression share | Clicks | Click share |
|---:|---|---|---|---:|---:|---:|---:|---:|

Lead with the verified account, marketplace, target ASIN, reporting period, and exact keyword. Then provide the target benchmark, competitor comparison, concise evidence-based observations, and any caveats.

Standing cautions (house rules):
- POE/account-identity rule applies to any SC browsing: verify the ACTIVE Seller Central account is the client's before opening SQP (viewing leaks footprint into the active account).
- SQP shares are single-digit for virtually everyone; judge funnel shape (purchase/click share vs impression share), not absolute share.
