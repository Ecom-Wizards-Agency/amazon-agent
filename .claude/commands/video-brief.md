---
description: Build Sponsored Brands video editor briefs from search data (POE/DataDive clusters -> Google Doc briefing)
argument-hint: "[client-marketplace] (e.g. sheko-de), optionally 'learnings' to run the post-test loop"
---

# SB Video Brief

Build keyword-driven Sponsored Brands video briefs for editors. Do not duplicate logic here. Route into the `amazon-sb-video-briefs` skill.

The user's target is: **$ARGUMENTS**

## Steps

1. **Confirm the brief intake first.** Before reading files or pulling data, collect with a single AskUserQuestion whatever `$ARGUMENTS` and the conversation do not already supply: client, marketplace, target ASIN(s), break-even ACOS (or margin), on-screen text language, whether product footage exists, and the client's Drive ads/creative folder for the briefing doc. Never carry values over from another client. When the client already has keyword-research configs and POE/DataDive data on disk, reuse them instead of fresh pulls.
2. **Load the skill.** `skills/amazon-sb-video-briefs/SKILL.md` is the source of truth. Read its two references before scripting. Copy `tools/sb-video-briefs/config.TEMPLATE.json` to a local `config.<client>-<market>.json` on first run (client configs stay local, gitignored).
3. **Data layer.** Pull POE (account-safety rules apply, `--expect-account`), DataDive MCP, SQP, and current ads performance as the skill directs. Build the candidate cluster table.
4. **Shortlist and stop.** Present 3 to 5 scored clusters with one line of evidence each. Wait for operator confirmation before any scripting.
5. **Script + claims pass.** Build the script tables (3 hook variants per cluster), then run the health-claims-check flow over all on-screen text and VO lines. Advisory mode: present MEDIUM/HIGH lines with suggested rewrites for per-line operator decisions.
6. **Deliver.** Assemble ONE Google Doc per batch exactly per `references/editor-brief-template.md` (global rules on top, one section per cluster; no cover page), including specs box, claims table with decisions, and test plan. Create it via the Google Drive MCP in the client's ads/creative folder.
7. **Learnings mode.** If `$ARGUMENTS` says learnings: skip 3 to 6, pull the test campaign's results, run the verdict rules and learnings checklist from the adaptation reference, and append the learnings block to the brief page.
