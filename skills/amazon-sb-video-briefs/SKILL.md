---
name: amazon-sb-video-briefs
description: Use for Amazon Sponsored Brands VIDEO creative work, keyword-driven video ad planning, video editor briefings, SB video scripts, video angle testing, and adapting Meta-style creative playbooks to Amazon search. Builds a data-selected shortlist of query clusters (POE + DataDive + SQP + ads data), then a branded editor briefing (one doc per batch, one section per video, three named angles over one shared second half) with script tables, sound-off design rules, Amazon specs, and an advisory health-claims table. Also owns the per-product-line Creative Reference & Asset Library. Route pure PPC structure work to amazon-campaign-builder or amazon-adlabs-audit, listing SEO to amazon-seo-keyword-workflow, and creator sourcing to amazon-creator-connections.
---

# Amazon SB Video Briefs

Browser: Mixed. CDP (`run-poe.mjs` over the shared debug Chrome) for POE pulls; DataDive and AdLabs via MCP with no browser; delivery as a branded .docx on the Google Drive desktop mount.

Turn search data into Sponsored Brands video briefs a video editor can execute without knowing Amazon. Core premise: Amazon is pull marketing. The shopper typed a query and is comparing tiles on a SERP. Videos are built per query cluster, designed sound-off, and tested with a fixed feedback loop. Meta-playbook techniques are used only through the adaptation layer, never raw.

## Load Order

1. `references/evolve-to-amazon-adaptation.md`: the methodology. Read before scripting anything.
2. `references/editor-brief-template.md`: the mandatory brief structure.
3. `references/creative-reference-doc.md`: the standing per-product-line reference the brief draws from.
4. `tools/sb-video-briefs/config.TEMPLATE.json`: per-client config contract (client configs are local-only, gitignored).
5. `skills/amazon-seo/references/health-claims-compliance.md` when the claims table is built (via the health-claims-check flow).

## Vocabulary (Evolve-aligned, one system across Amazon and Meta)

- **Batch** = one video. One shelf, one buying criterion family, one shared second half.
- **Angle 1 / 2 / 3** = the three openings. Never "Hook A/B/C". The tracker column in Evolve is `ANGLE(S)`; stay in that vocabulary.
- **Cut** = one angle plus the shared Part 2. Angles and cuts are 1:1, so there is no third tracking level.
- **Awareness level** = Solution Aware, Product Aware, or Most Aware only. Problem Aware and Unaware do not exist on Amazon search.

Cadence is roughly **3 angles per month**. Meta-scale creative programmes (50 briefs a week off an ad-intelligence tool) do not port to Amazon and must not be proposed as a production target. They are useful only as a coverage map.

## Required Data Inputs

Per client and product line, before cluster selection:

- POE Search Terms + Products for the niche (`tools/opportunity-explorer/run-poe.mjs`; observe the Account Safety rules in `skills/amazon-opportunity-explorer/SKILL.md`, including `--expect-account`). Reuse an existing POE designer pack when one is on disk rather than re-pulling.
- DataDive niche keyword grid and roots via the DataDive MCP (`get_niche_keywords`, `get_niche_roots`) for cluster boundaries and our organic rank.
- SQP per-ASIN via the AdLabs MCP `search_query` entity for impression share vs click share per query.
- Current ads performance via the AdLabs MCP `target` and `ad_group` entities: spend, CTR, CVR, ACOS, top-of-search share. An existing high-spend low-CTR SB target is the single best video candidate in the account.
- Listing reference JSON for the target ASINs (listing-capture) to verify ad-to-listing congruence and to source every claim.
- Product facts and brand kit from the client config. Never invent product claims: facts come from the config, the live listing, or the operator.

## Workflow

1. Intake: client, marketplace, **product line**, target ASINs, break-even ACOS, language, whether footage exists, and the Drive creative folder. Copy `config.TEMPLATE.json` to a local client config on first run. Never carry values from another client.
2. Data layer: pull the inputs above. Build the candidate cluster table (cluster, volume, our organic rank, impression vs click share, current spend and CTR/CVR/ACOS, price congruence against the shelf median).
3. Shortlist: apply the scorecard gates and ranking from the adaptation reference, section 5. Cap at 3 to 5 clusters. Present the shortlist with one line of evidence per cluster, and name any cluster that is **not** a creative problem (CTR already at or above shelf rate, or wrong-intent traffic) so it is not briefed by mistake. Get operator confirmation before scripting.
4. Creative Reference doc: build or refresh it per `references/creative-reference-doc.md` before the brief. The brief draws its claims and its differentiation from that doc and does not restate the evidence.
5. Classify each confirmed cluster with the query-to-awareness map (adaptation reference, section 4). Mine reviews and query phrasing for the shopper's own words.
6. Script: build the brief per `references/editor-brief-template.md`. Three angles over one shared Part 2 per video. Every angle leads on a different buying criterion; that is the isolated variable. All on-screen text is final copy in the marketplace language.
7. Claims pass (advisory): run the health-claims-check flow over every on-screen card and any VO line. One claims table for the whole batch, sorted with HIGH and MEDIUM first. Every line traces to a live-listing phrase or is flagged. Record operator decisions inline, with the source and date for anything authorised against the listing. Verify claim-critical label facts against the packaging artwork when it is reachable, and if a banned term is PRINTED on the pack, add a legibility framing rule for label close-ups.
8. Deliver: render branded via `tools/amazon-ad-audit/render_branded.py` with no cover page, and place on the Drive mount (see Delivery Rule).
9. Campaign structure: one campaign per keyword, one ad group per angle (the batch). See Measurement below. Campaign creation itself routes to amazon-campaign-builder; this skill stops at the naming and the read plan.
10. Learnings loop: when results exist, run the verdict rules and learnings checklist (adaptation reference, section 9), then write what changed back into the **Creative Reference doc**, not into a tracker.

## Measurement (structural, not a preference)

AdLabs has no creative-level entity for Sponsored Brands: `advertised_product` and `product` exclude SB, and `creative_type` returns empty on SB video ad groups. Three creatives inside one ad group are invisible to reporting.

So every angle test is built the same way:

- One campaign per keyword, following the account's existing campaign convention. One ad group per angle (the batch) inside it, named `Angle N - <name>`. Never leave the Amazon default `Ad group - <timestamp>` name: it makes every AdLabs pull unreadable.
- Same keywords, same match types, same bids across the angles. The ad group name is the only difference.
- Budget sits at campaign level, so impressions will not split evenly. Read CTR, which is a rate, not click counts. If one angle sits far behind on impressions, pause the leaders until it catches up.
- **Stage 1 is CTR**, roughly 5,000 impressions per angle. Cheap, needs impressions not clicks.
- **Stage 2 is CVR and ACOS**, on the survivor only, roughly 100 to 150 clicks. Price it in the brief at the observed CPC so the operator sees the cost before agreeing.
- SQP click share is profile-level and organic plus paid. It reads at batch level only, never per angle.

**Pre-registered read.** Write win and kill thresholds into the brief before launch **only where a like-for-like control exists** (same product, same shelf, same ad type). Where none exists, the first batch creates the baseline: leave the verdict open and record the result in the Creative Reference doc afterwards. Never build a threshold from a blended figure that mixes branded and generic cohorts.

## QA Gates

- Every brief section of the template is present; the specs box is verbatim.
- Frame-1 rule holds in every angle: product in action, no logo intro, no fade-in, no title card.
- Each angle leads on a **different buying criterion**, and the brief says in one line what differs across the three.
- The awareness level is stated with a one-line justification tied to the query the shopper types.
- One claim per video; the claim is not what the top tiles for the query already say (check the Creative Reference shelf map).
- No em-dashes, no English text in non-English marketplace briefs, numerals not words.
- Claims table covers 100% of on-screen cards and VO lines; every MEDIUM and HIGH line has a suggested rewrite and an operator decision with a source.
- Every scripted line names what is on screen (filmable test). Cards without product substance are cut.
- Ad-to-listing congruence: the led criterion is visible in the live listing copy; if not, flag it in the brief instead of shipping silently.
- The final card of each shared Part 2 is textless and reads as a clean restart for the loop.

## Delivery Rule

Briefs and Creative Reference docs deliver as **branded .docx, no cover page**, rendered with `tools/amazon-ad-audit/render_branded.py`. Two ways in, both fine: call `render_branded.render(cfg, outdir, md_path, cover=False)` from python, or run the CLI and simply omit `--cover`. Do not write `--cover=False` on the CLI: it is a bare switch and argparse rejects an explicit value. Leave `custom_kpis` out of `metrics.json` so the KPI card strip is suppressed. Run it with the repo `.venv` python, which has python-docx.

Place them on the Google Drive desktop mount at `01_Client Sheets/<Client>/<Client> - Shared/Creative/` (client-facing, so inside the `- Shared` folder; reuse the existing folder name if it differs). ONE canonical file per batch and per product line, title WITHOUT a version suffix, edited IN PLACE: the link never changes and Drive keeps version history. The operator edits the file directly, so ALWAYS re-read the live file before revising and never resurrect content the operator removed.

Naming:

- `<Client> <Market> - <Product Line> SB Video Briefing.docx`
- `<Client> <Market> - <Product Line> - Creative Reference & Asset Library.docx`

Keep the source markdown in `output/<client>/creative-reference/` so a re-render is reproducible.

## Outputs

- Candidate cluster table and confirmed shortlist (in-chat).
- One Creative Reference & Asset Library per product line (evergreen).
- One branded editor briefing per batch: global rules, one section per video, three named angles over one shared Part 2, one claims table.
- Learnings written back into the Creative Reference doc after each test window.

## Stop Before Risk

- Stop for operator confirmation at the shortlist (step 3) and before delivering any brief whose claims table still has undecided MEDIUM or HIGH lines.
- Never launch campaigns, change bids, or upload creatives from this skill.
- POE pulls follow the account-identity safety rules; abort on account mismatch.
- Never script a claim the live listing contradicts without an explicit, dated operator authorisation recorded in the claims table, and always name the listing-alignment fix that removes the moderation risk.
