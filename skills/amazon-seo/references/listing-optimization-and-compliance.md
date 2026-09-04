# Listing Optimization And Compliance

Mode browser: None (local writing and compliance work; listing text comes from `amazon-listing-capture`).

Use this as the Amazon SEO specialist skill. It coordinates existing Ecom Wizards SEO skill references from the GitHub knowledge library with current Amazon first-party rules.

Naming note: the operator noted that Amazon's Rufus AI naming is moving/has moved toward Alexa or Alexa AI. Treat `Rufus`, `Alexa AI`, `Amazon AI search`, and `semantic Amazon search` as related trigger language unless current first-party Amazon docs say otherwise for a specific workflow.

## Source Order

1. Knowledge-base skill references for Ecom Wizards methodology:
   - `<your-knowledge-base>/Skills/keyword-classifier-and-filter.md`
   - `<your-knowledge-base>/Skills/amazon-seo-writer.md`
   - `<your-knowledge-base>/Skills/rufus-optimization.md`
   - `<your-knowledge-base>/Skills/amazon-image-strategy.md` when OEI/POE image strategy or visual search context matters
   - `conversion-offers-and-copy` when persuasion or voice matters
   - the client's hub note in the shared team vault (`Clients/<Name>/<Name>.md`) and prior handoff notes, which sit in that client's `Handoffs/` folder when the vault is reachable and in the repo's `output/<client>/seo/` otherwise

   Note: these knowledge-base skill files are a user-specific local reference and may not exist at the `Code/knowledge-base` path. The operator's old vault copies were archived on 27.07.2026, so the in-repo condensations below are now the primary source. This path note is user-specific. Team members should point to their own local knowledge-base/Obsidian copy. Do not commit the vault to GitHub. This is a reference source only, not a "check Obsidian for everything" rule.

   In-repo condensations (use these when the vault is unavailable; they make the skill self-contained):
   - `skills/amazon-seo/references/seo-writing-methodology.md`: keyword classification, Ranking-Juice placement priority, title/bullet/description/backend rules, Rufus/Alexa semantic layer, audit pass.
   - `skills/amazon-seo/references/eu-compliance-matrix.md`: EU health-claim rules (Reg. 1924/2006 + 432/2012 + 1925/2006), authorized-vs-prohibited by category, with worked collagen/fibre cases. Consult before writing copy or filling `triage.claim_tokens`.
   - `skills/amazon-seo/references/health-claims-compliance.md`: the compliance process layer (modeled on Amazon's SAS Health Claims Check audits): category risk tiers (regulated vs standard), EU + US regimes, the SAS-style per-claim self-check (`/health-claims-check`), and the RJ-preserving rewrite ladder (strip-effect → authorised-wording swap → ADD authorised claims → backend/PPC routing → drop last). Mandatory self-check before delivery for regulated-tier products; client-facing report only on explicit operator request.

   Reusable workflow: for full keyword-research workbooks built from DataDive and POE evidence, use `skills/amazon-seo/references/keyword-research-workbook.md` and the repo builder `tools/amazon-seo-keyword-workbook/`. The builder uses DataDive Core MKL, the complete read-only keyword pool, POE evidence, Never Ever frequency analysis, outlier triage, SEO text, and a DataDive Ranking Juice snapshot.

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
2. For an SEO audit, major SEO change, or Rank-readiness check, run `python3 tools/ads_recall.py seo-rank-gate` and read the returned decision and Research files in order. Continue quietly when it returns no paths.
3. Load only the relevant knowledge-base skill reference, not every SEO reference.
4. Search Amazon first-party docs for current constraints before finalizing copy or recommendations.
5. Use MAG SEO SOPs when the user needs the step-by-step agency workflow or Seller Central movement.
6. For regulated categories (supplements, foods with claims, health & beauty, medical-adjacent), apply `references/health-claims-compliance.md`: check restricted claims against `references/eu-compliance-matrix.md` (EU) or the US regime section, run the SAS-style self-check before delivery, and fix findings via the RJ-preserving rewrite ladder (never bare deletion) so Ranking Juice and semantic coverage survive the compliance pass. Standard-tier categories (household/general) get the claims-lite pass and may keep more aggressive wording.
7. Before approving a major SEO change or a full Rank push, verify Product Type, browse-node assignment, and required category attributes for every relevant child ASIN. Use backend catalog data, a category listing report, FlatFilePro, or equivalent evidence. Page source alone is not sufficient. Fix child-level classification drift first; any intentional browse-node change needs a documented expected outcome, monitoring plan, and rollback criteria.
8. Stop before saving or publishing listing changes, uploading flat files, or editing live catalog content.

## Listing Field Terminology

Keep these listing fields distinct in keyword workbooks, SEO drafts, and flat-file CSVs:

- Title / item name: one product title. In FlatFilePro or Amazon templates this is usually `itemName` or `item_name.*.value`.
- Item Highlights: one short highlight field, often capped at 125 characters. It is not a bullet list. In FlatFilePro exports this may map to `title_differentiation.0.value`.
- Bullet points: the normal Amazon feature bullets. In FlatFilePro/Amazon templates these use `bullet_point.*.value`.

Do not use bullet fields for Item Highlights, do not split an Item Highlight into bullets, and do not collapse normal bullets into the Item Highlights field unless the user explicitly asks for a rewritten single highlight.

### Item Highlights: the four rules that decide whether the field works

Full reasoning and worked examples in `references/seo-writing-methodology.md` (§3 separator
contract + the Item Highlights section). All four are build-gated in
`tools/amazon-seo-keyword-workbook/build_keyword_workbook.py`.

1. **Separator: the TITLE takes the spaced en-dash ` – `, Item Highlights take the spaced
   middot ` · `.** Never a dash or pipe in the highlights. A comma **inside** a chip is fine
   (`For Skin, Hair & Nails`), because the middot is the separator. Revised 2026-07-26 from
   comma to middot on readability; the middot is the only candidate mark with no second job
   on the line.
2. **Chip 1 is the only chip guaranteed to be read.** Measured on the Amazon mobile app
   (DE search, 2026-07-26): a live 123-character value truncated after its first chip, about
   28 characters, and chips 2 and 3 never appeared in search at all. So **chip order beats
   the separator glyph and beats filling the 125 characters.** Spend chip 1 on the strongest
   differentiator that is NOT already in the title, and keep it short so a second chip lands
   inside the visible window.
3. **Judge the field on its INCREMENTAL SV, never its standalone SV.** Compute what every
   other searchable field already covers, then measure what the highlights add on top. A
   field whose tokens are all covered by the title and bullets is worth zero no matter how
   good it reads. Re-audit after ANY bullet or description edit.
4. **Relevance gates inclusion.** A high-volume term goes in only if it is genuinely true of
   the product. The shopper sees this field next to the title, so an untrue term costs trust
   and CTR, which is the opposite of the field's job.

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
