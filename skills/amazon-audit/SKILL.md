---
name: amazon-audit
description: "Create read-only Amazon ad and sales audits, including falling-sales and rising-ACOS diagnosis, in deep, monthly, or actions-only mode."
---

# Amazon Audit

Browser: Mixed (AdLabs and DataDive over MCP; Seller Central reports and live creative capture over CDP; local workbook and document builds).

Use this skill for every Amazon ad or sales audit. It owns three postures:

- `deep`: first-time prospect or onboarding audit from downloaded Amazon files.
- `monthly`: recurring review for an AdLabs-managed account.
- `actions`: recommendations only for an AdLabs-managed account.

It also owns diagnostic requests such as "why are sales falling?", "why did ACOS rise?", "traffic dropped", and "conversion declined". Route those requests into the relevant branch of `references/audit-workflow.md`; do not create a separate troubleshooting skill that omits stock, Buy Box, organic rank, market demand, or the account change log.

## Route The Run

1. Establish the requested posture before pulling data.
2. Read `references/audit-workflow.md` for the shared analysis gates, posture-specific source path, performance lens, grading, traps, and hard rules.
3. Load only the posture source reference named there: `references/source-bulk.md` for `deep`, or `references/source-adlabs.md` for `monthly` and `actions`.
4. Load `references/lens-b-shopper-creative.md` only when the workflow says Lens B is due.
5. Read `references/writing-and-delivery.md` before drafting or delivering the narrative.

The run is read-only. Recommendations may route to `amazon-ppc-weekly-management`, but this skill never applies campaign or account changes.
