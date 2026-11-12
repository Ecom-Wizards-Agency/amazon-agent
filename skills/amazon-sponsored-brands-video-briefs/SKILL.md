---
name: amazon-sponsored-brands-video-briefs
description: "Build evidence-led Sponsored Brands video concepts, scripts and complete editor briefings. Use for a commissioned video or a three-angle concept test; campaign execution stays separate."
---

# Amazon Sponsored Brands Video Briefs

Browser: Mixed. POE uses CDP over the shared debug Chrome. SoldScope and SYNQ use MCP (AdLabs carve-out: the AdLabs MCP). Google Drive and Google Docs use their connected tools.

Deliver one complete editor briefing as a native Google Doc. It contains final copy, timing, visual and audio direction, relevant product and brand rules, and the exact requested deliverables. Research and claims evidence stay internal; a separate Creative Reference is no longer delivered.

## Choose the assignment

| Mode | Use when | Output and checkpoint |
|---|---|---|
| `production` | The operator has agreed the objective and concept | The requested complete cuts. Do not invent alternate hooks or repeat open-ended cluster selection. |
| `concept_testing` | The task is to discover and test creative direction | Three named openings per confirmed query cluster, over one identical shared second half. Stop at the shortlist for operator confirmation before scripting. |

Record mode and requested cuts in the assignment and delivery receipt; the repository-builder route also records `briefing.mode` and `briefing.requested_cuts` in its config. A production Video section is one complete cut; a concept-testing Video section is one concept with three cuts. Count scripts before language/export duplicates. An absent mode in a legacy builder config retains concept testing.

Targeting intent is a separate input. Discovery defaults to non-branded queries. A specific operator request for branded recognition, such as an own-brand production video, controls that assignment; record it internally without turning it into a standing waiver. An explicitly agreed production concept does not require a second shortlist approval. Claims support and action approvals still apply.

## Load order

1. `references/editor-brief-template.md` for the editor document.
2. `references/evolve-to-amazon-adaptation.md` for creative translation. Its discovery and three-angle rules apply to concept testing; the explicit assignment above controls production mode.
3. `references/creative-reference-doc.md` for internal evidence, product facts and asset handling.
4. `references/connected-delivery.md` for native-connector delivery, or `tools/sb-video-briefs/config.TEMPLATE.json` when using the repository builder.
5. `<vault>/Playbooks/amazon-sb-video-concept-testing-playbook.md`, resolved through `AMAZON_AGENT_TEAM_VAULT` or `_local/team-vault-path.txt`, when test readiness or prior learnings affect the work. Measurement stays outside the editor document.
6. `skills/amazon-seo/references/health-claims-compliance.md` when the category or copy needs claims QA.

## Inputs and evidence

Every assignment needs the client, marketplace, language, placement, current ASIN/variant and pack, objective, requested cuts, approved factual basis, brand guidance, and footage state. Do not assume a visual direction identifies an available source clip. Include verified asset links only when useful; do not infer rights. A known missing required shot becomes an exact production gap.

Production may use supplied verified research and an approved direction. Collect missing claim-critical evidence before drafting final copy. Do not require fresh paid research or the complete discovery process for an already agreed concept.

Concept discovery additionally uses:

- Latest authoritative Drive keyword workbook, preferring the pinned URL, and SoldScope `research.json` / `roots.csv`. Credit-spending calls need one run approval naming ASINs, marketplace and expected credits; rank-tracker writes need exact-action approval (`tools/soldscope/README.md`).
- Relevant full POE packs through the breadth workflow below.
- Per-ASIN SQP and current target/ad-group metrics from SYNQ. Start with `list_clients`, skip demo clients, verify the client by SKU/title with `get_catalog`, then check `get_sync_status`. Retain response notes and never treat row-limited results as complete. Use the AdLabs profile only for its carve-out account.
- Live listing-reference JSON, current shelf-price context, and listing support for the proposed buying criterion.

## POE identity and breadth

Pass `--account-name`, `--expected-partner-account-id`, optional `--parent-account-name`, and `--marketplace-label` to every POE command. `run-poe.mjs` must verify the live identity before fetching. Stop with zero fetches if the account or marketplace is unavailable, ambiguous or still wrong after switching, or login/human challenge prevents verification. Use the repository login broker for login recovery; do not inspect credentials or handle human challenges.

For discovery, combine workbook and SoldScope roots into 8 to 12 deduplicated non-branded seeds covering head term, form, mechanism, uses and attributes. Search every seed, union by nicheId, retain provenance and exclude irrelevant niches. Download 5 to 10 relevant full packs, or all relevant packs when fewer than five qualify. Cached packs must be no older than 14 days and meet the same coverage requirements. Mark insufficient prior packs superseded without deleting raw history.

The internal manifest records workbook URL, SoldScope run/ASINs/marketplace/search_id, roots, seeds, considered niches, exclusions, selected packs, timestamps, cache decisions and limitations.

## Workflow

1. Confirm mode, scope and inputs. Keep evidence and operator decisions internal.
2. For concept discovery, build 3 to 5 candidate clusters. Gate on intent/product fit, factual and listing support, and solvable production requirements. Rank by volume, organic rank, impression-to-click-share gap, spend, CTR, CVR, raw ACOS, price congruence and listing support. Exclude post-click or wrong-intent problems. Present one evidence line per cluster and stop for confirmation.
3. Give the writer the agreed objective, factual basis, brand/pack rules, requested cuts and relevant prior learnings. Keep planning language out of final copy.
4. Write the complete briefing. Production follows the agreed sequence; concept testing has three distinct buying criteria and one shared Part 2 per concept. Every card has final text, timing and filmable visual intent. State audio/VO explicitly; voiceover and any particular duration are assignment choices.
5. Run internal line-by-line QA on visible copy, VO and visual implications. Trace facts to verified listing/packaging evidence or an explicit operator decision. Resolve medium/high claims risk. Keep only concise, relevant do-not instructions in the briefing. The editor never chooses alternate claim wording.
6. Run the portable mechanical validator. Have a fresh reviewer inspect factual support, shopper relevance, natural copy, visual feasibility and editor completeness. Consolidate issues into one targeted writer revision and recheck it. Any unresolved factual or production blocker stays visible and prevents a ready verdict.
7. Deliver the single briefing through the repository builder or the supported native-connector route in `references/connected-delivery.md`, then inspect the native/PDF pages. Preserve the canonical brief ID. Historical reference Docs are untouched.
8. Record editor questions, corrections and production blockers with the job. Consume actual creative-test learnings from the existing Notion A/B Test Program; retain their context. Propose small workflow changes for review rather than editing instructions automatically.

## Mechanical checks

The standard-library helper travels with this skill and works from a task workspace:

`python3 -I -B <skill-root>/scripts/validate_brief.py --brief-md <file> --mode production --requested-cuts 1`

Use `--mode concept_testing --requested-cuts 3` for one test concept. Success reports `mechanical_checks_passed`, videos, cuts and scripted cards. It checks sections, per-video angle structure, cut count, nonempty card fields, unique local card IDs, seven-word cards, a reading-time floor of 2.5 seconds or visible characters divided by 12, continuous timing, shared-sequence joins, SBV target duration and textless endings. The reviewer still allows a visual beat. Mechanical checks do not establish claims support, creative quality, footage availability or visual QA.

## Delivery

For the repository-builder route:

`python3 tools/sb-video-briefs/build_and_deliver.py --config <config> --brief-md <file>`

Use the canonical title `<Client> <Market> - <Product Line> SB Video Briefing`. Keep the existing source Markdown destination, typically `output/<client>/creative-reference/`; this historical folder name does not imply a second deliverable. Preserve the existing file ID, URL, comments, permissions and version history. Legacy reference config and `--reference-md` are ignored with warnings and never cause reference writes.

The builder checks title, existing client Video Briefings folder, native MIME type, complete content readback and PDF export. Its manifest remains `delivered_pending_visual_qa` until the attending operator workflow inspects every page for brand and editor requirements. Local Markdown, DOCX, PDFs and ZIPs are staging, not delivery.

When the repository builder is absent, use the supported native-connector route in `references/connected-delivery.md` if its capabilities and verification gates are available. Connected Composio MCP does not require a local CLI or operator repository. Hand off only the specific delivery steps that neither route can satisfy. Never claim completion, substitute an unbranded upload, or write to a client-visible destination without authorization. Grimoire runs do not write to Drive. A placement change to Prime Video or Streaming TV requires its format and specs; do not run SBV-only validation against another placement.

## Ownership and stops

- This skill owns creative briefings and consumes learnings. Ads skills own launch, measurement, verdicts and scaling; results live in the existing Notion program and portal.
- Stop before Amazon-visible actions, campaigns, creative uploads, bid/budget or listing changes. Those are outside this builder.
- Stop at open concept-selection approval; continue an already approved production assignment without repeating it.
