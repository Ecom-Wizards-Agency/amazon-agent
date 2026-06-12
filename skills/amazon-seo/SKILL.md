---
name: amazon-seo
description: Use for Amazon SEO and listing optimization work: keyword research workbooks, Never Ever classification, Master Keyword Lists, Ranking Juice, title/bullets/description/backend search terms, Rufus/Alexa AI semantic optimization, SEO audits, compliance checks, and listing copy intended for Seller Central or flat files.
---

# Amazon SEO

Use this as the Amazon SEO specialist skill. It coordinates existing Ecom Wizards SEO skill references from the GitHub knowledge library with current Amazon first-party rules.

Naming note: Victor noted that Amazon's Rufus AI naming is moving/has moved toward Alexa or Alexa AI. Treat `Rufus`, `Alexa AI`, `Amazon AI search`, and `semantic Amazon search` as related trigger language unless current first-party Amazon docs say otherwise for a specific workflow.

## Source Order

1. Knowledge-base skill references for Ecom Wizards methodology:
   - `/Users/victoruhl/Code/knowledge-base/Skills/keyword-classifier-and-filter.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/amazon-seo-writer.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/rufus-optimization.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/amazon-image-strategy.md` when OEI/POE image strategy or visual search context matters
   - `/Users/victoruhl/Code/knowledge-base/Skills/direct-response-copywriter.md` when persuasion/voice matters
   - relevant client/project notes under `/Users/victoruhl/Code/knowledge-base/Projects/Clients/`

   Note: these knowledge-base skill files are a user-specific local reference and may not exist at the `Code/knowledge-base` path. Victor's current local copies live in an Obsidian vault: `/Users/victoruhl/Obsidian/Victors Second Brain/Skills/` (e.g. `amazon-seo-writer.md`, `keyword-classifier-and-filter.md`, `rufus-optimization.md`, `oei-product-strategy.md`). This path is user-specific — team members should point to their own local knowledge-base/Obsidian copy. Do not commit the vault to GitHub. This is a reference source only, not a "check Obsidian for everything" rule.

   In-repo condensations (use these when the vault is unavailable — they make the skill self-contained):
   - `skills/amazon-seo/references/seo-writing-methodology.md` — keyword classification, Ranking-Juice placement priority, title/bullet/description/backend rules, Rufus/Alexa semantic layer, audit pass.
   - `skills/amazon-seo/references/eu-compliance-matrix.md` — EU health-claim rules (Reg. 1924/2006 + 432/2012 + 1925/2006), authorized-vs-prohibited by category, with worked collagen/fibre cases. Consult before writing copy or filling `triage.claim_tokens`.

   Reusable workflow: for full keyword-research workbooks built from DataDive + POE exports, use `skills/amazon-seo-keyword-workflow/SKILL.md` and the repo builder `tools/amazon-seo-keyword-workbook/`. The builder uses DataDive Core MKL at 30%, Expanded MKL at 1%, POE evidence, Never Ever frequency analysis, outlier triage, SEO text, and a DataDive Ranking Juice snapshot.

   DataDive support references (Zendesk article index + SEO workflow map):
   - `skills/amazon-seo/references/datadive-support/datadive-support-index.md`
   - `skills/amazon-seo/references/datadive-support/datadive-seo-workflow-article-map.md`
   - refresh with `tools/datadive-support/refresh_datadive_support_index.py` when DataDive's help center changes (the index is metadata + links, not full article text).

   When to consult them (don't load preemptively — open the workflow map and search the topic only when it matters):

   | If the task involves… | Consult the DataDive topic | Builder step it informs |
   |---|---|---|
   | MKL thresholds / which export | "Master Keyword List", relevancy | Core `30%` → `3.1`; Expanded `1%` → `3.2`/Never-Ever |
   | Roots / word frequency | "Roots" | `1. Root Keywords`, Never-Ever frequency |
   | Outliers / relevancy meaning | "Outliers", "Relevancy" | `Outlier - Opportunity KWs` triage |
   | Ranking Juice scoring | "What is Ranking Juice" | `4.1 SEO Text` RJ column + placement priority |
   | Listing Builder | "Listing Builder" | title/bullet/description drafting |
   | Rank Radar / tracking | "Rank Radar" | post-publish rank monitoring (not part of the build) |
2. Amazon Seller Help for current title, bullet, description, image, search-term, prohibited-claim, and category rules.
3. MAG SEO SOPs for Helium 10/DataDive process, agency execution steps, and practical checks.

## Workflow

1. Identify whether the task is keyword cleanup, SEO writing, Rufus/semantic optimization, audit, or publishing support.
2. Load only the relevant knowledge-base skill reference, not every SEO reference.
3. Search Amazon first-party docs for current constraints before finalizing copy or recommendations.
4. Use MAG SEO SOPs when the user needs the step-by-step agency workflow or Seller Central movement.
5. For regulated categories, explicitly check restricted claims against `references/eu-compliance-matrix.md` and avoid medical, disease, cure, guaranteed-result, weight-loss, or unsupported compliance-sensitive language.
6. Stop before saving or publishing listing changes, uploading flat files, or editing live catalog content.

## Output Standards

- Provide title, bullets, description, backend terms, and audit only when requested or useful.
- Include Ranking Juice assumptions when using keyword search volume.
- Avoid keyword stuffing; natural compliant copy beats raw keyword density.
- Mark anything that needs Victor approval before publishing.
