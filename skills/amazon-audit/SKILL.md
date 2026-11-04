---
name: amazon-audit
description: "Create read-only Amazon ad and sales audits, including falling-sales and rising-ACOS diagnosis, in deep, monthly, or actions-only mode."
---

# Amazon Audit

Browser: Mixed (SYNQ and SoldScope over MCP, AdLabs over MCP for the AdLabs carve-out account only; Seller Central reports, read-only SYNQ gap pages and live creative capture over CDP; local workbook and document builds).

Knowledge units for this area live in knowledge/ads/; search them first with python3 tools/search_amazon_libraries.py "<symptom>" --library kb.

Use this skill for every Amazon ad or sales audit. It owns three postures:

- `deep`: first-time prospect or onboarding audit from downloaded Amazon files.
- `monthly`: recurring review for a managed account.
- `actions`: recommendations only for a managed account.

`monthly` and `actions` need a SYNQ client. The AdLabs carve-out account (US and CA) uses its
AdLabs profile instead. The clients still being onboarded into SYNQ (identified in
`docs/synq-mcp.md`) may use the download path until they are onboarded; any other client without a SYNQ client is a blocker to report.

It also owns diagnostic requests such as "why are sales falling?", "why did ACOS rise?", "traffic dropped", and "conversion declined". Route those requests into the relevant branch of `references/audit-workflow.md`; do not create a separate troubleshooting skill that omits stock, Buy Box, organic rank, market demand, or the account change log.

## Route The Run

1. Establish the requested posture before pulling data.
2. Run `python3 tools/ads_recall.py audit` and read the returned decision, Playbook, and Research files in order. Continue quietly when it returns no paths.
3. Read `references/audit-workflow.md` for the shared analysis gates, posture-specific source path, performance lens, grading, traps, and hard rules.
4. Load only the posture source reference named there: `references/source-bulk.md` for `deep` and for a client still being onboarded into SYNQ, `references/source-synq.md` for `monthly` and `actions` on a SYNQ client, or `references/source-adlabs.md` for AdLabs carve-out only.
5. Load `references/lens-b-shopper-creative.md` only when the workflow says Lens B is due.
6. Read `references/writing-and-delivery.md` before drafting or delivering the narrative.

The run is read-only. Recommendations may route to `amazon-ppc-weekly-management`, but this skill never applies campaign or account changes.

Keyword, competitor and rank data come from SoldScope: keyword research for the ASIN set and the rank tracker for rank history. SoldScope calls that spend credits need one run approval naming the ASINs, marketplace and expected credits; rank-tracker writes need exact-action approval (`tools/soldscope/README.md`).
