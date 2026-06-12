# Library Map

Use these folders as the first source of truth before answering or operating in Amazon.

## MAG SOPs

Path: `/Users/<your-username>/Codex Projects/Amazon Agent/MAG SOPs`

Use for agency procedures, practical Seller Central/Vendor Central workflows, listing/catalog work, ads SOPs, support-ticket style processes, shipment/FBA workflows, operational checks, and MAG-specific best practices.

Important index:

- `_index/sop-index.json`
- `README.md`

Coverage captured on 2026-05-12: 534 SOPs.

## SOP Drafts

Path: `/Users/<your-username>/Codex Projects/Amazon Agent/sop-drafts`

Use for review-stage workflow guidance and recent learnings that have not yet been promoted into MAG SOPs. Drafts should still be searched when a workflow matches, especially for support cases, troubleshooting, shipment defects, communications, and recently improved procedures.

Treat draft SOPs as helpful but not final. If they conflict with first-party Amazon docs or promoted MAG SOPs, use Amazon docs for current rules/UI, use promoted SOPs for settled agency procedure, and mention the draft as a recent-learning source in the operator note.

## Amazon Seller Help

Path: `/Users/<your-username>/Codex Projects/Amazon Agent/Amazon Seller Help`

Use for first-party Seller Central help, account health, inventory, listings, orders, payments, Seller Support, FBA, global selling, Brand Registry, policy, and account settings.

Important index:

- `_index/seller-help-index.json`
- `articles/`
- `README.md`

Coverage captured on 2026-05-12: 239/239 discovered pages.

## Amazon Ads Help

Path: `/Users/<your-username>/Codex Projects/Amazon Agent/Amazon Ads Help`

Use for Amazon Ads API, no-code tools, guides, reference pages, and knowledge-hub material from the Advanced Tools documentation.

Important index:

- `_index/amazon-ads-help-index.json`
- `README.md`

Coverage captured on 2026-05-13: 27/27 originally discovered Advanced Tools pages.

Safety note: credential-heavy examples were summarized rather than stored as runnable token, secret, private-key, IAM, or bearer-header code.

## Advertising Help After Login

Path: `/Users/<your-username>/Codex Projects/Amazon Agent/Advertising Help After Login`

Use for Amazon Ads Support Center UI help: campaigns, bidding, budgets, targeting, reports, billing, policies, troubleshooting, Ads Console actions, and Creator Connections-related advertising workflows.

Important index:

- `_index/advertising-help-index.json`
- `articles/`
- `README.md`
- `_index/linked-expansion/remaining-linked-urls-2026-05-13.txt`

Status on 2026-05-13: 109 Chrome snapshot-indexed pages captured, plus 14 linked-expansion pages captured. 127 linked-expansion URLs remain as optional future depth, not blockers for core routing.

Safety note: billing/payment identifiers, credentials, tokens, and secret values are not stored in this library.

## Search Priority

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

## Current Completeness

- MAG SOPs: complete local MAG capture, 534 SOPs, captured 2026-05-12.
- SOP Drafts: review-stage tracked SOPs in `sop-drafts/`; useful for recent learnings but not final until promoted.
- Amazon Seller Help: complete local Seller Help capture, 239/239 pages, captured 2026-05-12.
- Amazon Ads Help: complete Advanced Tools docs capture, 27/27 pages, updated 2026-05-13.
- Advertising Help After Login: core Ads Support Center capture complete for 109/109 Chrome-indexed pages; linked expansion is partial at 14 captured and 127 remaining, updated 2026-05-13.
