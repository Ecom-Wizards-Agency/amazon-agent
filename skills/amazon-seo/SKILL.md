---
name: amazon-seo
description: "Run Amazon keyword research, build keyword workbooks, write and audit listing SEO, optimize for semantic search, and check claims compliance."
---

# Amazon SEO

Browser: Mixed (listing writing and workbook builds are local; DataDive and POE inputs use their owning MCP or browser workflows).

Use this skill for Amazon keyword research, keyword workbooks, listing optimization, semantic search, and claims compliance.

## Modes

- `keyword-research`: gather DataDive, POE, and listing inputs; build, validate, and deliver the keyword-research workbook. Read `references/keyword-research-workbook.md`.
- `listing-optimization`: write or audit titles, Item Highlights, bullets, descriptions, and backend terms. Read `references/listing-optimization-and-compliance.md` and `references/seo-writing-methodology.md`.
- `health-claims-check`: run the regulated or standard claims pass. Read `references/health-claims-compliance.md` and the marketplace-specific rules it routes to.
- `campaign-structure-fill`: fill the workbook's visual PPC plan only. Read the Campaign Structure section in `references/keyword-research-workbook.md`.

## Shared Rules

- Treat Rufus, Alexa AI, Amazon AI search, and semantic Amazon search as related trigger language unless current first-party documentation distinguishes them.
- Use `amazon-listing-capture` for live listing copy and `amazon-opportunity-explorer` for POE evidence.
- Keep title, Item Highlights, and bullet fields distinct.
- For an SEO audit, major SEO change, or Rank-readiness check, run `python3 tools/ads_recall.py seo-rank-gate` and read the returned decision and Research files in order. Continue quietly when it returns no paths.
- Before approving a major SEO change or a full Rank push, verify Product Type, browse-node assignment, and required category attributes for every relevant child ASIN using backend catalog evidence. Page source alone is insufficient. Fix child-level classification drift first; any intentional browse-node change needs a documented expected outcome, monitoring plan, and rollback criteria.
- Run the mandatory claims self-check before delivering regulated-category SEO work.
- Stop before publishing listing changes, uploading flat files, or applying campaign changes.
