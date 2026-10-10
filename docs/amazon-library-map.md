# Library Map

Use these folders as the first source of truth before answering or operating in Amazon.

## Amazon Knowledge

Path: `<repo-root>/knowledge`

Use first for a symptom, an error text or a "how do we handle X" question. Each unit answers one question the agency met on real accounts, with its cause, fix, verification step and stop-before point. Units are grouped by topic folder (compliance, logistics, catalog, support-cases, ads, account-health, seo, brand-registry, reporting).

Important index:

- `_index/knowledge-index.json`
- `README.md` (generated counts and unit list per topic)
- `TEMPLATE.md`

Strict rule: every unit is anonymised and labelled. No client, brand, product, person, ID, price, address or link enters a unit; provenance lives in the team vault ledger. Every unit carries `status` (draft or reviewed) and `verification` (unverified or verified), and an answer built on a unit states that label. A draft or unverified unit is a lead, not a rule. Format, review gate and authority order: `docs/knowledge-library.md`.

Search:

```bash
python3 tools/knowledge/ask.py "<question or exact error text>"
python3 tools/search_amazon_libraries.py "<exact error text or symptom>" --library kb --limit 5
```

`ask.py` is the one entry point for a question: one search over every library, hits grouped by authority (units, our skills, first-party help, drafts, MAG SOPs last and labelled with status and site revision), and a short guidance block naming the answer, the procedure, the rule page and the external fallback. `search_amazon_libraries.py` is the raw search; `--library knowledge` is the same as `kb`, `--library all` ranks units together with the captures.

## MAG SOPs

Path: `<repo-root>/MAG SOPs`

Use for agency procedures, practical Seller Central/Vendor Central workflows, listing/catalog work, ads SOPs, support-ticket style processes, shipment/FBA workflows, operational checks, and MAG-specific best practices.

Important index:

- `_index/sop-index.json`
- `README.md`

Coverage: 352 active SOPs (27 marked superseded by a repo procedure, 13 duplicates archived), captured 12.05.2026 and curated 08.07.2026, 27.07.2026 and 06.10.2026 (110 unusable SOPs dropped; the pCloud archive keeps the full capture). The index carries each SOP's `status`.

## SOP Drafts

Path: `<repo-root>/sop-drafts`

Use for review-stage workflow guidance and recent learnings that have not yet been promoted into MAG SOPs. Drafts should still be searched when a workflow matches, especially for support cases, troubleshooting, shipment defects, communications, and recently improved procedures.

Searchable now with `--library drafts`.

Treat draft SOPs as helpful but not final. If they conflict with first-party Amazon docs or promoted MAG SOPs, use Amazon docs for current rules/UI, use promoted SOPs for settled agency procedure, and mention the draft as a recent-learning source in the operator note.

## Amazon Seller Help

Path: `<repo-root>/Amazon Seller Help`

Use for first-party Seller Central help, account health, inventory, listings, orders, payments, Seller Support, FBA, global selling, Brand Registry, policy, and account settings.

Important index:

- `_index/seller-help-index.json`
- `articles/`
- `README.md`

Coverage captured on 12.05.2026: 239/239 discovered pages; 54 articles re-captured 06.10.2026 after the first capture had saved 53 empty page shells (one video page still has no text).

## Amazon Ads Help

Path: `<repo-root>/Amazon Ads Help`

Use for Amazon Ads API, no-code tools, guides, reference pages, and knowledge-hub material from the Advanced Tools documentation.

Important index:

- `_index/amazon-ads-help-index.json`
- `README.md`

Coverage captured on 13.05.2026: 27/27 originally discovered Advanced Tools pages.

Safety note: credential-heavy examples were summarized rather than stored as runnable token, secret, private-key, IAM, or bearer-header code.

## Advertising Help After Login

Path: `<repo-root>/Advertising Help After Login`

Use for Amazon Ads Support Center UI help: campaigns, bidding, budgets, targeting, reports, billing, policies, troubleshooting, Ads Console actions, and Creator Connections-related advertising workflows.

Important index:

- `_index/advertising-help-index.json`
- `articles/`
- `README.md`
- `_index/linked-expansion/remaining-linked-urls-2026-05-13.txt`

Status on 13.05.2026: 109 Chrome snapshot-indexed pages captured, plus 14 linked-expansion pages captured. 127 linked-expansion URLs remain as optional future depth, not blockers for core routing. Updated 06.10.2026: the linked expansion is complete (114 pages added, 15 dead URLs recorded) and 120 articles were re-captured verbatim.

Safety note: billing/payment identifiers, credentials, tokens, and secret values are not stored in this library.

## AdLabs Help

Path: `<repo-root>/AdLabs Help`

Use for the public AdLabs methodology articles that document the optimizer's bid, placement and RPC formulas. It backs the weekly PPC loop's rule that optimizer max-change settings are ceilings, never the step size.

Important index:

- `_index/adlabs-help-index.json`
- `articles/` (5 articles, starting with `000-formula-summary.md`)
- `README.md`

Coverage: 7 files, downloaded 26.07.2026. Search with `--library adlabs`. The optimizer preview stays the authority for per-entity numbers.

## Search Priority

Symptom, error text or how-do-we question:

1. Amazon Knowledge
2. First-party help (Amazon Seller Help, Advertising Help After Login, Amazon Ads Help)
3. MAG SOPs
4. SOP Drafts

`python3 tools/knowledge/ask.py "<question>"` applies this order automatically, with our skills ranked above first-party help and MAG SOPs last. State the unit's verification label in the answer. When a unit and a first-party page disagree, follow the authority order in `docs/knowledge-library.md` and do not resolve it silently.

Seller Central task:

1. Amazon Seller Help
2. MAG SOPs
3. SOP Drafts for recent internal workflow learnings
4. Advertising Help only if ads-related

Amazon Ads UI task:

1. Advertising Help After Login
2. Amazon Ads Help
3. MAG SOPs advertising category

Amazon Ads API or bulk/no-code docs:

1. Amazon Ads Help
2. Advertising Help After Login
3. MAG SOPs advertising category

Agency execution or SOP-style task:

1. MAG SOPs
2. SOP Drafts for recent internal workflow learnings
3. Relevant Amazon first-party help

Cross-functional troubleshooting:

Search all libraries, then reconcile sources by date and authority.

AdLabs optimizer math or bid formulas:

1. AdLabs Help
2. Amazon Ads Help
3. MAG SOPs advertising category

## Current Completeness

- Amazon Knowledge: authored, anonymised units, growing monthly; counts per topic are in `knowledge/README.md`.
- MAG SOPs: curated local MAG capture, 352 active SOPs, captured 12.05.2026 and curated 08.07.2026, 27.07.2026 and 06.10.2026; 314 carry `needs-update` until a live check confirms their limits, fees and labels.
- SOP Drafts: review-stage tracked SOPs in `sop-drafts/`, searchable with `--library drafts`; useful for recent learnings but not final until promoted.
- Amazon Seller Help: complete local Seller Help capture, 239/239 pages, captured 12.05.2026, 54 refreshed 06.10.2026 (`tools/knowledge/help_capture.mjs`).
- Amazon Ads Help: complete Advanced Tools docs capture, 27/27 pages, updated 13.05.2026.
- Advertising Help After Login: Ads Support Center capture of 237 articles; 120 re-captured verbatim and 114 linked pages added 06.10.2026 (`tools/knowledge/help_capture.mjs`), 15 dead linked URLs listed in `_index/advertising-help-missing.json`.
- AdLabs Help: public AdLabs methodology articles, 7 files, downloaded 26.07.2026.
