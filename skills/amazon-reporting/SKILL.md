---
name: amazon-reporting
description: Use for Amazon reporting and analytics: Seller Central reports, Amazon Ads reports, SQP, SCP, business reports, search term reports, bulk downloads, period comparisons, dashboards, and Excel/CSV workbook outputs.
---

# Amazon Reporting

## Source Order

1. Knowledge-base analytics skill references for workbook logic:
   - `/Users/<your-username>/Code/knowledge-base/Skills/amazon-sqp-intelligence-suite.md`
   - `/Users/<your-username>/Code/knowledge-base/Skills/amazon-yoy-analysis.md`

   Note: these knowledge-base skill files are a user-specific local reference and may not exist at the `Code/knowledge-base` path. The operator's current local copies live in an Obsidian vault: `/Users/<your-username>/Obsidian/<your-vault>/Skills/` (e.g. `amazon-sqp-intelligence-suite.md`, `amazon-yoy-analysis.md`). This path is user-specific — team members should point to their own local knowledge-base/Obsidian copy. Do not commit the vault to GitHub. This is a reference source only, not a "check Obsidian for everything" rule.
2. Amazon Seller Help or Advertising Help After Login for current report definitions, locations, filters, and download behavior.
3. MAG SOPs for practical report generation steps.

## Workflow

1. Confirm account, marketplace, report type, date range, entity level, and destination folder.
2. Search official docs for report definitions/current UI.
3. Use internal analytics references for workbook generation and interpretation.
4. Save deliverables under `output/{client-or-brand}/reporting/` with dates in filenames unless the user specifies pCloud/Drive.
5. Stop before creating scheduled reports, changing report settings, or downloading sensitive reports to an unclear destination.
