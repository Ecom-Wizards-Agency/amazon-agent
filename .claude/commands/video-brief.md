---
description: Build Sponsored Brands video editor briefs from search data (POE/DataDive clusters -> branded .docx briefing)
argument-hint: "[client-marketplace] (e.g. acme-de), optionally 'learnings' to run the post-test loop"
---

# SB Video Brief

Build keyword-driven Sponsored Brands video briefs for editors. Do not duplicate logic here. Route into the `amazon-sb-video-briefs` skill.

The user's target is: **$ARGUMENTS**

## Steps

1. **Confirm the brief intake first.** Before reading files or pulling data, collect with a single AskUserQuestion whatever `$ARGUMENTS` and the conversation do not already supply: client, marketplace, product line, target ASIN(s), break-even ACOS (or margin), on-screen text language, whether product footage exists, and the client's Drive creative folder. Never carry values over from another client. When the client already has keyword-research configs, a POE designer pack, or DataDive data on disk, reuse them instead of fresh pulls.
2. **Load the skill.** `skills/amazon-sb-video-briefs/SKILL.md` is the source of truth. Read its three references before scripting. Copy `tools/sb-video-briefs/config.TEMPLATE.json` to a local `config.<client>-<market>-<product-line>.json` on first run (client configs stay local, gitignored).
3. **Data layer.** Pull POE (account-safety rules apply, `--expect-account`), DataDive MCP, SQP and current ads performance via the AdLabs MCP as the skill directs. Build the candidate cluster table.
4. **Shortlist and stop.** Present 3 to 5 scored clusters with one line of evidence each, and name any cluster that is not a creative problem so it is not briefed by mistake. Wait for operator confirmation before any scripting.
5. **Creative Reference doc.** Build or refresh the per-product-line reference per `references/creative-reference-doc.md` before scripting. The brief draws its claims and differentiation from it.
6. **Script + claims pass.** Build the brief per `references/editor-brief-template.md`: three named angles over one shared Part 2 per video, each angle leading on a different buying criterion. Then run the health-claims-check flow over every on-screen card and VO line. Advisory mode: present MEDIUM and HIGH lines with suggested rewrites for per-line operator decisions.
7. **Deliver.** Render branded with `tools/amazon-ad-audit/render_branded.py` (no cover page, no `custom_kpis`, repo `.venv` python; see the skill's Delivery Rule for the exact call) and place the .docx on the Google Drive desktop mount in the client's creative folder. One canonical file per batch, no version suffix, edited in place.
8. **Campaign structure.** State the naming: one campaign per batch, one ad group per angle named `Angle N - <name>`. Stop there; campaign creation routes to amazon-campaign-builder.
9. **Learnings mode.** If `$ARGUMENTS` says learnings: skip 3 to 8, pull the test campaign's results, run the verdict rules and learnings checklist from the adaptation reference, and write the result back into the Creative Reference doc.
