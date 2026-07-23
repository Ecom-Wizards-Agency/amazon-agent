---
name: amazon-sb-video-briefs
description: Use for Amazon Sponsored Brands VIDEO creative work, keyword-driven video ad planning, video editor briefings, SB video scripts, video hook testing, and adapting Meta-style creative playbooks to Amazon search. Builds a data-selected shortlist of query clusters (POE + DataDive + SQP + ads data), then a Google Doc editor briefing (one doc per batch, sections per cluster) with script tables, 3 hook variants each, sound-off design rules, Amazon specs, and an advisory health-claims table. Route pure PPC structure work to amazon-campaign-builder or amazon-adlabs-audit, listing SEO to amazon-seo-keyword-workflow, and creator sourcing to amazon-creator-connections.
---

# Amazon SB Video Briefs

Browser: Mixed. CDP (`run-poe.mjs` over the shared debug Chrome) for POE pulls; DataDive and AdLabs via MCP with no browser; Google Doc delivery via the Google Drive MCP.

Turn search data into Sponsored Brands video briefs a video editor can execute without knowing Amazon. Core premise: Amazon is pull marketing. The shopper typed a query and is comparing tiles on a SERP. Videos are built per query cluster, designed sound-off, and tested with a fixed feedback loop. Meta-playbook techniques are used only through the adaptation layer, never raw.

## Load Order

1. `references/evolve-to-amazon-adaptation.md`: the methodology. Read before scripting anything.
2. `references/editor-brief-template.md`: the mandatory brief structure.
3. `tools/sb-video-briefs/config.TEMPLATE.json`: per-client config contract (client configs are local-only, gitignored).
4. `skills/amazon-seo/references/health-claims-compliance.md` when the claims table is built (via the health-claims-check flow).

## Required Data Inputs

Per client and marketplace, before cluster selection:

- POE Search Terms + Products for the niche (`tools/opportunity-explorer/run-poe.mjs`; observe the Account Safety rules in `skills/amazon-opportunity-explorer/SKILL.md`, including `--expect-account`).
- DataDive niche keyword grid and roots via the DataDive MCP (`get_niche_keywords`, `get_niche_roots`) for cluster boundaries and our rank.
- SQP per-ASIN (AdLabs MCP or Seller Central download) for impression vs click share per query.
- Current ads performance on candidate targets (AdLabs MCP where managed, else bulk files): spend, CTR, CVR, ACOS.
- Listing reference JSON for the target ASIN (listing-capture) to verify ad-to-listing congruence.
- Product facts and brand kit from the client config. Never invent product claims: facts come from the config or the operator.

## Workflow

1. Intake: client, marketplace, target ASIN(s), break-even ACOS, language, and whether footage exists. Copy `config.TEMPLATE.json` to a local client config on first run.
2. Data layer: pull the inputs above. Build the candidate cluster table (query cluster, volume, our impression/click share, current spend and CTR/CVR, top-3 click concentration).
3. Shortlist: apply the scorecard gates and ranking from the adaptation reference, section 5. Cap at 3 to 5 clusters per batch. Present the shortlist with one line of evidence per cluster and get operator confirmation before scripting.
4. Classify each confirmed cluster with the query-to-awareness map (adaptation reference, section 4). Mine reviews and query phrasing for the shopper's own words.
5. Script: build the script table per the skeleton (adaptation reference, section 6): frame-1 proof, differentiator, proof block, brand lockup; 3 hook variants over one shared hold. All on-screen text is final copy in the marketplace language.
6. Claims pass (advisory): run the health-claims-check flow over every on-screen text card and VO line. Build the per-line risk table with suggested rewrites for MEDIUM and HIGH. The operator decides per line; record decisions in the brief. Verify claim-critical label facts against the packaging artwork itself when it is reachable (client Drive folders often hold the print files; IDML is a ZIP of XML and greps clean), instead of leaving VERIFY rows open. Also check whether any banned term is PRINTED on the pack (branded raw materials, "bioaktiv"): if so, the brief needs an explicit legibility framing rule for label close-ups, or the banned words end up on screen through the footage.
7. Brief build: assemble the briefing exactly per `references/editor-brief-template.md` and deliver it as a Google Doc (HTML via the Drive MCP `create_file`, converted to a Doc; no cover page). One doc per batch with a section per cluster, shared global-rules section on top. Title: `<Client> <Marketplace> SB Video Briefing <topic> <date> v<N>`.
8. Test plan: fill section 10 of the brief (1 SB video campaign per cluster, exact and phrase, hook variants as separate ads where supported). Campaign creation itself routes to amazon-campaign-builder or the Ads Console flow; this skill stops at the plan.
9. Translation sync: when the operator edits the master-language text in the delivered doc, re-read the LIVE doc first, change only the edited cards' translations, and keep every other byte of the operator's version intact.
10. Learnings loop: when results exist (2 weeks or meaningful spend), run the verdict rules and learnings checklist (adaptation reference, section 9) and write the learnings block back into the brief page before the next batch is scripted.

## QA Gates

- Every brief section of the template is present; the specs box is verbatim.
- Frame-1 rule holds in every variant: product in action, query-mirroring text, no logo intro.
- One claim per video; the claim differs from what the top tiles for the query already say.
- No em-dashes, no English text in non-English marketplace briefs, numerals not words.
- Claims table covers 100% of on-screen text and VO lines; every MEDIUM/HIGH line has a suggested rewrite and an operator decision.
- Every scripted line names what is on screen (filmable test).
- Ad-to-listing congruence: the led criterion is visible in the live listing copy; if not, flag it in the brief instead of shipping silently.

## Delivery Rule

Briefs deliver as Google Docs in the client's Drive ads/creative folder (set in the client config; for numbered client structures this is the Ads folder, e.g. "07 Ads (Forecasts & Creative)"). No cover page. Finished video files and raw footage live in a subfolder next to the brief; the brief names it. ONE canonical doc per batch, title WITHOUT a version suffix, edited in place (operator rule 2026-07-23): change history lives in Google Docs version history, never in parallel v1/v2 files. The operator edits the doc directly, so ALWAYS re-read the live doc before revising and never resurrect content the operator removed. When tooling cannot edit in place, recreate the doc once and delete the superseded copies via the Drive desktop mount (they land in Drive trash).

## Outputs

- Candidate cluster table + confirmed shortlist (in-chat, then archived in the brief pages).
- One Google Doc editor briefing per batch (template above, section per cluster), including the advisory claims table and test plan.
- Learnings block appended to each brief after the test window.

## Stop Before Risk

- Stop for operator confirmation at the shortlist (step 3) and before delivering any brief whose claims table still has undecided MEDIUM/HIGH lines.
- Never launch campaigns, change bids, or upload creatives from this skill.
- POE pulls follow the account-identity safety rules; abort on account mismatch.
