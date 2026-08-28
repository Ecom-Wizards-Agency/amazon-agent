---
name: amazon-sb-video-briefs
description: Use for Amazon Sponsored Brands video creative work, keyword-driven concept selection, editor briefings, three-angle scripts, and per-product Creative Reference and Asset Libraries. Builds a wide POE, DataDive, Drive-keyword, SQP, ads, listing, and price evidence layer, then delivers branded native Google Docs. Testing methodology lives in the agency playbook and live results live in Notion.
---

# Amazon SB Video Briefs

Browser: Mixed. POE uses CDP over the shared debug Chrome. DataDive and AdLabs use MCP. Google Drive and Google Docs use their connected tools.

Create editor-ready Sponsored Brands video packages for Amazon search. The shopper has already typed a query and is comparing products. Each confirmed query cluster produces one video concept with three distinct openings over one shared second half.

## Load Order

1. `references/evolve-to-amazon-adaptation.md` for creative translation only.
2. `references/editor-brief-template.md` for the mandatory briefing shape.
3. `references/creative-reference-doc.md` for the evergreen product and asset reference.
4. `tools/sb-video-briefs/config.TEMPLATE.json` for the local config contract.
5. `<vault>/Playbooks/amazon-sb-video-concept-testing-playbook.md` (team vault, resolved via `AMAZON_AGENT_TEAM_VAULT` or `_local/team-vault-path.txt`) only when prior learnings or test readiness affect concept selection. Do not copy its measurement method into editor documents.
6. `skills/amazon-seo/references/health-claims-compliance.md` for internal claims QA when the category or copy needs it.

## Vocabulary

- Batch: one video concept for one query cluster.
- Angle 1, 2, 3: three openings that lead on different buying criteria.
- Cut: one angle plus the shared Part 2. There are exactly three cuts per concept.
- Awareness level: Solution Aware, Product Aware, or Most Aware only.

## Required Inputs

- Latest relevant Google Drive keyword-research workbook. Prefer the pinned workbook URL in config; otherwise find the latest authoritative workbook in the existing client Keyword Research folder.
- DataDive niche keywords and roots.
- POE full niche packs selected through the breadth workflow below.
- Per-ASIN SQP from AdLabs `search_query`.
- Current ad performance from AdLabs `target` and `ad_group`: spend, CTR, CVR, raw ACOS, and placement context where available.
- Current live listing reference JSON for each target ASIN.
- Current price and shelf-price context.
- Product facts, brand kit, and verified footage sources.

## Seller Central Account Recovery

Pass these config values to every POE command:

- `--account-name`
- `--expected-partner-account-id`
- optional `--parent-account-name`
- `--marketplace-label`

`run-poe.mjs` reads the live identity before the first search or niche request. If it is wrong, it uses trusted CDP clicks to select the configured account and marketplace, reloads POE, and re-reads `partnerAccountId`. Fetching begins only after the identity matches.

Stop with zero POE fetches when the account or marketplace is unavailable or ambiguous, the user is logged out, a human challenge appears, or the post-switch identity still differs. Never handle credentials, MFA, CAPTCHA, or account recovery.

## POE Breadth Workflow

1. Read the latest relevant Drive keyword workbook and DataDive roots before choosing seeds.
2. Produce 8 to 12 deduplicated, non-branded seeds. Cover the head term, product form, mechanism, principal uses, and meaningful attributes. Do not pad with spelling variants.
3. Search every seed. Union related niches by `nicheId`, retain seed provenance, and exclude branded, wrong-product, wrong-form, wrong-audience, and wrong-use niches.
4. Download 5 to 10 relevant full niche packs. If fewer than five qualify, download all relevant niches and record the limitation in the coverage manifest.
5. Reuse a cached pack only when it is no more than 14 days old and satisfies the same seed, relevance, and full-pack coverage requirements.
6. Mark an insufficient prior pack as `superseded` in the run manifest. Never delete historical raw data.

The coverage manifest records workbook URL, DataDive niche, roots by source, final seeds by category, related niches considered, exclusions with reasons, selected full packs, capture timestamps, cache decisions, and limitations.

## Workflow

1. Intake: client, marketplace, product line, ASINs, language, Seller Central identity, Drive folder, and footage state. Migrate the config when legacy break-even, flat account, or testing keys appear. Ignore those legacy values after warning.
2. Build the research layer using the breadth workflow.
3. Build 3 to 5 candidate clusters. Gate on non-branded intent, product fit, listing support, factual copy support, and solvable production requirements.
4. Rank candidates using search volume, organic rank, impression-to-click-share gap, spend, CTR, CVR, raw ACOS, price congruence, and listing support. Do not use break-even ACOS.
5. Identify clusters that are not creative problems, such as healthy CTR with a post-click conversion issue or wrong-intent traffic.
6. Present the shortlist with one evidence line per cluster. Pause for operator confirmation of one cluster per product before scripting.
7. Build or refresh the Creative Reference from the confirmed facts, shelf map, shopper language, cluster coverage, price constraint, and verified asset inventory.
8. Script the briefing. Every concept has three named angles leading on distinct buying criteria, one identical Part 2, final on-screen copy, filmable directions, sound-off rules, and a textless looping end frame.
9. Run internal line-by-line claims QA. Every visible line and VO line must trace to the live listing, packaging, or an explicit operator decision. Resolve medium and high risk before delivery. Do not include the risk table in either editor document.
10. Retain one concise absolute do-not list in the briefing so the editor cannot accidentally introduce forbidden language or imagery.
11. Run `build_and_deliver.py`. It creates both native Docs on first delivery and updates both canonical document ids in place on later runs. The command completes only after title, folder, MIME type, content readback, and PDF-export QA pass for both Docs.
12. When live test learnings exist, read them from the existing Notion A/B Test Program and use the creative learning in the next cluster or execution decision. Do not write performance methodology or results into the brief or reference.

## Internal Claims QA

- Claims validation remains a hard internal gate even though no claims appendix is delivered.
- Reject unsupported final cards and VO lines.
- Verify claim-critical product facts against packaging when available.
- When forbidden words are printed on packaging, add a framing rule that keeps them illegible.
- The editor never chooses alternate claims wording.

## Editor Deliverable QA

- All mandatory template sections and the verbatim specs box are present.
- Frame 1 shows the product in action. No logo intro, fade-in, title card, empty pack shot, blank frame, or language error.
- Exactly three distinguishable cuts are specified: one angle plus the identical shared Part 2.
- Each angle leads on a distinct buying criterion.
- Every scripted card is filmable, legible at thumbnail size, no longer than seven words, and source-traceable internally.
- The final frame is textless and loops cleanly.
- The brief contains no claims appendix, testing thresholds, measurement method, or break-even ACOS.
- The reference contains no testing method or performance result. Its asset section is section 5.
- Missing visual strategy direction is not a blocker. Missing required footage is an exact production gap.

## Delivery

Run:

`python3 tools/sb-video-briefs/build_and_deliver.py --config <config> --brief-md <file> --reference-md <file>`

Canonical titles:

- `<Client> <Market> - <Product Line> SB Video Briefing`
- `<Client> <Market> - <Product Line> - Creative Reference & Asset Library`

Keep source Markdown in `output/<client>/creative-reference/`. Never add version suffixes. If a canonical Doc already exists, edit it in place. Preserve its file id, URL, comments, permissions, and version history. Retain render intermediaries when delivery or QA fails.

## Ownership Boundary

- This skill prepares testable concepts and consumes past learnings.
- `amazon-ads` and `amazon-ppc-management` own launch, measurement, verdict, and scaling under the canonical agency playbook.
- Live tests and results belong in the existing Notion A/B Test Program and brand portal.
- Campaign creation and performance writes are outside `build_and_deliver.py`.

## Stop Before Risk

- Pause at the shortlist confirmation checkpoint.
- Never create campaigns, upload creatives, change bids or budgets, edit listings, or make another Amazon-visible change.
- Stop POE before the first data request unless Seller Central account identity and marketplace have been verified.
