# Amazon Agent Architecture

Status: Accepted operating structure  
Date: 2026-05-19  
Scope: Amazon Agent workspace, local Amazon libraries, Chrome operating workflow

## Goal

Increase operating efficiency by using one generalist dispatcher with a balanced set of specialist modes below it. The dispatcher should avoid broad library crawling, route work to the right specialist, and preserve the current safety model: verify account/context, capture evidence, and stop before externally visible or risky actions.

## Operating Model

The Amazon Agent should behave like a small operator team:

1. A main agent classifies the request, chooses the source ladder, and owns the final answer.
2. A specialist mode handles the deep reasoning for the selected workflow.
3. Local sources are searched narrowly through indexes and search helpers before any browser action.
4. Chrome is used for Amazon work after the workflow is clear.
5. The agent stops before sending, submitting, uploading, confirming, changing live settings, or deleting anything.

This does not require every task to spawn actual parallel subagents. For many tasks, the main agent can adopt the specialist mode internally. Actual subagents should be reserved for parallel research, independent checks, or larger work where the context split saves time.

## Balanced Specialist Structure

### 1. Amazon Generalist / Dispatcher

Owns intake, routing, source priority, risk checkpoints, and final operator notes.

Responsibilities:

- Classify the request into the closest specialist area.
- Search only the relevant source set.
- Choose whether a real subagent is useful or whether a specialist mode is enough.
- Reconcile conflicts between internal skills, Amazon first-party docs, and MAG SOPs.
- Keep the user updated with the intended path and stop points.
- Preserve the final source list, browser path, evidence, and next action.

Default output:

- What was checked.
- Which source ladder was used.
- Current workflow or final screen.
- Evidence captured or prepared.
- Confirmation needed, if any.

### 2. Troubleshooting & Account Health Specialist

For errors, suppressed listings, blocked campaigns, warnings, policy issues, account health, case-worthy problems, missing access, and ambiguous Amazon UI failures.

Primary sources:

1. Exact error text in first-party Amazon Seller Help or Advertising Help.
2. Relevant internal skills if the issue is a known Ecom Wizards workflow.
3. MAG troubleshooting/catalog SOPs for practical UI steps and screenshots.

Workflow:

- Capture exact symptom and visible labels.
- Search exact text first, then simplified keywords.
- Identify likely category: permission, eligibility, policy, data delay, file validation, budget, marketplace mismatch, account mismatch, catalog contribution conflict, or compliance.
- In Account Health, open `Review details` where available before summarizing.
- Prepare the next action or support-case draft.
- Stop before appeals, acknowledgements, support submissions, or account-changing actions.

### 3. SEO & Listing Optimization Specialist

For keyword research, listing copy, titles, bullets, descriptions, backend search terms, Rufus/semantic optimization, SEO audits, Ranking Juice, and keyword workbook workflows.

Primary sources:

1. Ecom Wizards internal skills and knowledge references:
   - `/Users/victoruhl/Code/knowledge-base/Skills/amazon-seo-writer.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/keyword-classifier-and-filter.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/rufus-optimization.md`
   - related client/project notes when relevant
2. Amazon Seller Help for current Amazon rules, requirements, prohibited claims, title/bullet/image/search-term limits, and compliance.
3. MAG SEO SOPs for practical process, Helium 10/DataDive flow, screenshots, and agency execution patterns.

Workflow:

- Use internal SEO skill logic first when creating or auditing listing content.
- Verify current Amazon constraints before finalizing content.
- Use MAG SOPs to understand how the work is executed in the frontend or workbook.
- For regulated categories, add a compliance check before output.
- Stop before publishing or saving listing changes.

### 4. Catalog Management & Flat File Specialist

For variation/parentage, suppressed listings, inactive inventory, brand attributes, title/image/A+ changes, category/browse node, feed processing errors, bulk templates, delete/relist workflows, Vendor Central catalog feeds, and Brand Registry catalog conflicts.

Primary sources:

1. Amazon Seller Help for listing rules, catalog requirements, error code definitions, Brand Registry behavior, and current UI constraints.
2. Relevant internal Ecom Wizards notes if the client or workflow has a known local playbook.
3. MAG catalog SOPs for exact frontend steps, flat-file tactics, screenshots, and workaround patterns.

Workflow:

- Identify entity: ASIN, SKU, parent/child relationship, marketplace, brand, contribution source.
- Search the exact error code or attribute label.
- Decide manual UI vs flat-file vs support case.
- Preserve current state before changing anything.
- Stop before saving listing edits, deleting/relisting, uploading feeds, or submitting cases.

### 5. Amazon Ads Specialist

For Sponsored Products, Sponsored Brands, Sponsored Display, DSP, campaign structure, bidding, budgets, targeting, placements, reporting setup, billing warnings, and Ads Console troubleshooting.

Primary sources:

1. Advertising Help After Login for Ads Console UI workflows.
2. Amazon Ads Help for advanced tools, API, no-code tools, bulk sheets, and official technical docs.
3. Internal Ecom Wizards strategy notes when the request involves account strategy or agency methodology.
4. MAG advertising SOPs for practical operating steps.

Workflow:

- Start Ads UI work from `https://advertising.amazon.com/campaign-manager`.
- Verify selected advertiser/account, brand, country, and date range.
- Use Ads Console support docs for current UI behavior.
- Use internal strategy when deciding campaign structure or optimization logic.
- Stop before saving campaign, bid, budget, targeting, billing, or scheduled-report changes.

### 6. Creator Communications & Support Case Specialist

Separate from Ads because the risk profile is communication, not campaign operation. Covers Creator Connections messages, buyer-seller messages, support cases, case replies, courtesy refund follow-ups, creator campaign communication, and message drafting.

Primary sources:

1. Amazon first-party communication rules and buyer-contact guidelines.
2. Advertising Help After Login for Creator Connections UI and campaign-related creator workflows.
3. Internal Ecom Wizards/client voice notes and templates where available.
4. MAG SOPs for practical frontend steps and message-thread navigation.

Workflow:

- Confirm exact account, marketplace, brand, recipient/thread/case, and visible message context.
- Draft the message first.
- Record any Amazon-provided template text or policy warning.
- Stop before clicking `Send`, submitting a support case, replying to a case, or issuing/referring to a refund unless Victor explicitly confirms the exact action.

Creator Connections route:

1. Open `https://advertising.amazon.com/campaign-manager`.
2. Select the correct account in the top-right account selector.
3. Open `Brand content`.
4. Click `Creator connections`.

### 7. Reporting & Analytics Specialist

For Seller Central reports, Amazon Ads reports, SQP, business reports, search term reports, bulk downloads, sales/traffic comparisons, YoY/WoW analysis, and workbook outputs.

Primary sources:

1. Internal Ecom Wizards analytics skills when generating analysis or workbooks:
   - `/Users/victoruhl/Code/knowledge-base/Skills/amazon-sqp-intelligence-suite.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/amazon-yoy-analysis.md`
2. Amazon Seller Help or Advertising Help for current report definitions, locations, filters, and download behavior.
3. MAG SOPs for step-by-step report generation where useful.

Workflow:

- Confirm report type, account, marketplace, date range, entity level, and destination folder.
- Search official docs for report definitions and current UI.
- Use internal analytics skill logic for workbook generation and interpretation.
- Save deliverables under `output/{client-or-brand}/{YYYY-MM-DD}-reporting/` and evidence under `evidence/{client-or-brand}-reporting-{YYYY-MM-DD}/`. Save review management work under `output/{client-or-brand}/{YYYY-MM-DD}-review-management/` or `output/{client-or-brand}/review-management/`.
- Stop before creating scheduled reports, changing report settings, or downloading sensitive reports to an unclear destination.

### 8. Opportunity Explorer / Image Strategy Specialist

For Product Opportunity Explorer, OEI/POE, Niche Scout exports, product image strategy, product development ideas, and connecting niche insights to Amazon AI search strategy.

Primary sources:

1. Ecom Wizards internal skills and knowledge references:
   - `/Users/victoruhl/Code/knowledge-base/Skills/amazon-image-strategy.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/oei-product-strategy.md`
   - `/Users/victoruhl/Code/knowledge-base/Skills/rufus-optimization.md`
2. Seller Central/Product Opportunity Explorer docs for current access and export behavior.
3. MAG SOPs for practical frontend movement when useful.

Workflow:

- Confirm account, marketplace, niche/product/category, and intended output.
- Use the repo-native Opportunity Explorer extractor and formatter when an OEI/POE export is needed.
- Victor confirmed ownership and backend clearance for reusing the previous extension logic in repo-native scripts.
- Prioritize returns, negative reviews, success factors, positioning opportunity, seasonal patterns, demographics, and search terms when generating image or product recommendations.
- Treat Rufus, Alexa AI, Amazon AI search, and semantic Amazon search as related trigger language unless current first-party docs say otherwise.
- Stop before publishing listing copy, images, A+ content, or catalog changes.

### 9. FBA / Logistics / Inventory Specialist

For Send to Amazon, FBA shipments, shipment reconciliation, AWD, restock planning, removals, returns, inventory health, reserved inventory, seller-fulfilled shipping settings, and logistics troubleshooting.

Primary sources:

1. Amazon Seller Help for current FBA, inventory, shipping, AWD, and return rules.
2. Internal Ecom Wizards/client notes for account-specific inventory and supply-chain context.
3. MAG logistics/catalog SOPs for practical steps and screenshots.

Workflow:

- Confirm marketplace, account, SKU/ASIN list, shipment ID if present, quantities, destination, and dates.
- Search official FBA/inventory docs first.
- Use MAG SOPs for the frontend path.
- Capture warnings, placement options, fees, labels, shipment IDs, and reconciliation states.
- Stop before confirming shipments, buying labels, submitting placement/shipping choices, creating removal orders, or changing shipping settings.

## Source Priority Ladder

Use the source ladder according to task type. The rule is strict, but internal Ecom Wizards skills can outrank Amazon first-party docs when the user is asking for agency-owned methodology or generated work.

### A. Internal Skill Output Or Agency Methodology

Examples: write Amazon SEO, fill SEO workbook, Ranking Juice audit, SQP intelligence workbook, YoY analysis, Ecom Wizards campaign strategy, client-specific playbook.

Priority:

1. Ecom Wizards internal skill references and client/project notes.
2. Amazon first-party docs for current rules, limits, and compliance.
3. MAG SOPs for practical frontend/workbook movement.

### B. Current Amazon Rules, UI, Policies, Eligibility, Error Text

Examples: title requirements, buyer messaging rules, account health policy issue, listing error code, FBA rule, Ads Console status, report definitions.

Priority:

1. Amazon first-party docs:
   - Amazon Seller Help for Seller Central/catalog/FBA/account/policy.
   - Advertising Help After Login for Ads Console UI and creator-related Ads workflows.
   - Amazon Ads Help for Ads API, bulk/no-code tools, and technical docs.
2. Internal Ecom Wizards notes if the client/workflow has known context.
3. MAG SOPs for operator steps, screenshots, practical workarounds, and frontend navigation.

### C. Pure MAG Procedure Request

Examples: user explicitly asks for the MAG SOP flow or wants the My Amazon Guy procedure.

Priority:

1. MAG SOPs.
2. Amazon first-party docs to verify anything that may have changed.
3. Internal notes if client-specific context matters.

## Efficient SOP Search Strategy

Do not crawl the full SOP/help folders by default. Use a staged search:

1. Classify the task.
2. Search the relevant index or helper with 1-3 targeted queries.
3. Open only the top 2-5 relevant files.
4. If results are weak, search synonyms or exact UI labels.
5. If sources conflict, prefer the source ladder above.
6. Record the specific files used in the final operator note.

Search query pattern:

- First pass: exact Amazon UI label or error text.
- Second pass: normalized workflow term, such as `variation parentage`, `search optimization`, `campaign budget`, or `send to amazon`.
- Third pass: specialist synonyms only if needed.

## Metadata And Mentions Strategy

Yes, it makes sense to add better mentions, but the efficient version is not to manually edit every source file. Better options:

### Recommended: Routing Manifest

Create a small curated routing manifest that maps task types to keywords, preferred source folders, internal skills, and high-value SOP/docs.

Example fields:

- `specialist`
- `trigger_phrases`
- `source_priority`
- `internal_skills`
- `official_docs`
- `mag_sops`
- `browser_start_url`
- `stop_before`

Benefits:

- Fast to search.
- Easy to maintain.
- Does not pollute captured source docs.
- Lets the dispatcher route before opening large files.

### Optional: Frontmatter Tags For Curated Files

For a small number of high-value local docs, add frontmatter aliases/tags:

```yaml
agent_specialist: seo-listing
triggers:
  - write seo
  - ranking juice
  - backend search terms
source_role: internal-skill
```

Use this for internal skill references and custom operating docs, not every captured Amazon/MAG page.

### Not Recommended: Editing Every Captured SOP

Avoid adding mentions to every MAG or Amazon article. The libraries are source captures; broad editing adds maintenance cost and can blur the line between source material and routing metadata.

## When To Use Actual Subagents

Use actual subagents only when their work is independent enough to run in parallel:

- Troubleshooting specialist researches exact error text while the main agent gathers browser evidence.
- SEO specialist audits keyword coverage while the dispatcher verifies Amazon compliance requirements.
- Catalog specialist reviews flat-file strategy while the main agent checks the current listing state.
- Reporting specialist prepares workbook logic while the main agent downloads or verifies reports.

Keep the main agent responsible for:

- Final decision.
- Risk checks.
- User confirmation.
- Browser actions.
- Final operator note.

## Proposed Next Implementation Steps

1. Add this architecture into the routing skill once approved.
2. Update `AGENTS.md` source priority from broad local-library search to the strict source ladder.
3. Update `workflow-router.md` with specialist routing rows.
4. Update `library-map.md` so official Amazon docs are listed before MAG for current rules/UI, while internal Ecom Wizards skills are first for agency-owned workflows.
5. Add a compact routing manifest, for example:
   - `skills/amazon-operator-routing/references/routing-manifest.json`
6. Optionally update `search_amazon_libraries.py` to support source groups such as:
   - `--library official-seller`
   - `--library official-ads`
   - `--library mag`
   - `--library all-official`

## Open Decisions

- Whether the routing manifest should live in this workspace only, or whether a work-level copy should also live in `/Users/victoruhl/Code/knowledge-base`.
- Whether internal skills should be included in the search helper directly, or kept separate through the global knowledge-base search.
- Whether real subagents should be used frequently, or only when there is a clear parallelism benefit.
