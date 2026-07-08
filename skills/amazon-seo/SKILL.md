---
name: amazon-seo
description: Use for Amazon SEO strategy and listing copywriting: writing or re-optimizing titles, bullets, Item Highlights, description, and backend search terms; Rufus/Alexa AI semantic optimization; SEO audits; health-claims compliance ("make the listing compliant"); Never Ever classification decisions. For the DataDive-export-to-XLSX keyword-workbook build pipeline use amazon-seo-keyword-workflow; this skill writes the SEO content that feeds it.
---

# Amazon SEO

Use this as the Amazon SEO specialist skill. It coordinates existing Ecom Wizards SEO skill references from the GitHub knowledge library with current Amazon first-party rules.

Naming note: the operator noted that Amazon's Rufus AI naming is moving/has moved toward Alexa or Alexa AI. Treat `Rufus`, `Alexa AI`, `Amazon AI search`, and `semantic Amazon search` as related trigger language unless current first-party Amazon docs say otherwise for a specific workflow.

## Source Order

1. Knowledge-base skill references for Ecom Wizards methodology:
   - `<your-knowledge-base>/Skills/keyword-classifier-and-filter.md`
   - `<your-knowledge-base>/Skills/amazon-seo-writer.md`
   - `<your-knowledge-base>/Skills/rufus-optimization.md`
   - `<your-knowledge-base>/Skills/amazon-image-strategy.md` when OEI/POE image strategy or visual search context matters
   - `<your-knowledge-base>/Skills/direct-response-copywriter.md` when persuasion/voice matters
   - relevant client/project notes under `<your-knowledge-base>/Projects/Clients/`

   Note: these knowledge-base skill files are a user-specific local reference and may not exist at the `Code/knowledge-base` path. The operator's current local copies live in an Obsidian vault: `<your-vault>/Skills/` (e.g. `amazon-seo-writer.md`, `keyword-classifier-and-filter.md`, `rufus-optimization.md`, `oei-product-strategy.md`). This path is user-specific. Team members should point to their own local knowledge-base/Obsidian copy. Do not commit the vault to GitHub. This is a reference source only, not a "check Obsidian for everything" rule.

   In-repo condensations (use these when the vault is unavailable; they make the skill self-contained):
   - `skills/amazon-seo/references/seo-writing-methodology.md`: keyword classification, Ranking-Juice placement priority, title/bullet/description/backend rules, Rufus/Alexa semantic layer, audit pass.
   - `skills/amazon-seo/references/eu-compliance-matrix.md`: EU health-claim rules (Reg. 1924/2006 + 432/2012 + 1925/2006), authorized-vs-prohibited by category, with worked collagen/fibre cases. Consult before writing copy or filling `triage.claim_tokens`.
   - `skills/amazon-seo/references/health-claims-compliance.md`: the compliance process layer (modeled on Amazon's SAS Health Claims Check audits): category risk tiers (regulated vs standard), EU + US regimes, the SAS-style per-claim self-check (`/health-claims-check`), and the RJ-preserving rewrite ladder (strip-effect → authorised-wording swap → ADD authorised claims → backend/PPC routing → drop last). Mandatory self-check before delivery for regulated-tier products; client-facing report only on explicit operator request.

   Reusable workflow: for full keyword-research workbooks built from DataDive + POE exports, use `skills/amazon-seo-keyword-workflow/SKILL.md` and the repo builder `tools/amazon-seo-keyword-workbook/`. The builder uses DataDive Core MKL at 30%, Expanded MKL at 1%, POE evidence, Never Ever frequency analysis, outlier triage, SEO text, and a DataDive Ranking Juice snapshot.

   DataDive support references (Zendesk article index + SEO workflow map):
   - `skills/amazon-seo/references/datadive-support/datadive-support-index.md`
   - `skills/amazon-seo/references/datadive-support/datadive-seo-workflow-article-map.md`
   - refresh with `tools/datadive-support/refresh_datadive_support_index.py` when DataDive's help center changes (the index is metadata + links, not full article text). The script also regenerates `datadive-support-article-inventory.json` in the same folder; both are generated files, do not hand-edit.

   When to consult them (don't load preemptively; open the workflow map and search the topic only when it matters):

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
5. For regulated categories (supplements, foods with claims, health & beauty, medical-adjacent), apply `references/health-claims-compliance.md`: check restricted claims against `references/eu-compliance-matrix.md` (EU) or the US regime section, run the SAS-style self-check before delivery, and fix findings via the RJ-preserving rewrite ladder (never bare deletion) so Ranking Juice and semantic coverage survive the compliance pass. Standard-tier categories (household/general) get the claims-lite pass and may keep more aggressive wording.
6. Stop before saving or publishing listing changes, uploading flat files, or editing live catalog content.

## Listing Field Terminology

Keep these listing fields distinct in keyword workbooks, SEO drafts, and flat-file CSVs:

- Title / item name: one product title. In FlatFilePro or Amazon templates this is usually `itemName` or `item_name.*.value`.
- Item Highlights: one short highlight field, often capped at 125 characters. It is not a bullet list. In FlatFilePro exports this may map to `title_differentiation.0.value`.
- Bullet points: the normal Amazon feature bullets. In FlatFilePro/Amazon templates these use `bullet_point.*.value`.

Do not use bullet fields for Item Highlights, do not split an Item Highlight into bullets, and do not collapse normal bullets into the Item Highlights field unless the user explicitly asks for a rewritten single highlight.

## Updating an existing listing's SEO

When the task is "update the title / bullets / Item Highlights / backend" or
"re-optimize / make compliant" an existing listing (not a full keyword workbook),
**ask for these inputs up front** before writing. They gate both Ranking Juice and
compliance, and skipping them is what produces wrong titles:

1. **Anchor ASIN + marketplace.**
2. **DataDive niche ID**: the highest-leverage input. Pull the live **master keyword
   list** (`get_niche_keywords`) so you front-load the highest-SV **tracked** keyword,
   not a Roots-tab term (see methodology §2, root-vs-tracked), and the Ranking Juice
   snapshot (`get_ranking_juice`).
3. **Product facts from the label/PDP**: `form`, **blend or single ingredient**, the
   **ingredient list** (+ branded raw materials, e.g. Fibregum™), certifications
   (organic/Bio, vegan, gluten-free), and key attributes. A **blend must not lead the
   title with one ingredient**. Use a generic blend signal and recover the names in
   Item Highlights/bullets.
4. **Any intended benefit/claim angle**: screen it against
   `references/eu-compliance-matrix.md` before it reaches copy (ingredient **names**
   are factual; ingredient **effects** are health claims).

Then write per `references/seo-writing-methodology.md`, satisfying **both** traditional
SEO (Ranking-Juice coverage) **and** the semantic/Alexa layer, and keep the ≤75-char
title + ≤125-char Item Highlights structure. If a keyword workbook already exists for
the product, edit its `seo_content.<client>-<market>.json` and re-run the builder so
the QA gates (title root-vs-tracked, RJ coverage, semantic-present, brand-token) run.

## Output Standards

- Provide title, bullets, description, backend terms, and audit only when requested or useful.
- Include Ranking Juice assumptions when using keyword search volume.
- Avoid keyword stuffing; natural compliant copy beats raw keyword density.
- Mark anything that needs the operator approval before publishing.
