---
description: Run a monthly Amazon account review via AdLabs (same audit skill, monthly posture, learnings-forward)
argument-hint: "[client + marketplace(s)] [monthly|actions|deep] (e.g. 'acme de it' or 'acme de actions')"
---

# Monthly Account Review (AdLabs)

Same audit as `/amazon-audit`, entered at the monthly posture. Do not duplicate logic here. Route
into the `amazon-audit` skill, which is self-contained.

The user's target is: **$ARGUMENTS**

## Steps

1. **Load the skill** `amazon-audit` and run its startup sequence: session, teams, profiles,
   profile targets, then the audit guide resource. Report which profile you matched.

2. **Confirm the brief with a single AskUserQuestion**, skipping whatever `$ARGUMENTS` or context
   already supplies. **Posture** defaults to `monthly` from this command: lean, internal,
   learnings-forward, no cover page. `actions` for the list-only run, `deep` for an onboarding-depth
   pass. Also capture profiles and marketplaces, date range (default last 30 days, compare to the
   preceding period), target source, break-even ACOS, and brand terms including sub-brand treatment.

3. **Build the learnings layer** per the skill's context step: the applied-changes batch files under
   `_local/ppc-manage/<client>/batches/`, AdLabs profile memory, the vault run notes and global
   lessons file, Notion tasks and the A/B-Tests event log, recent call summaries, and the client's
   Slack channel. **Flag anything missing.** Never assume a clean window.

   This is **not a report card** on last month's changes. Write what we learned and what we do next.
   Only attribute a metric move to a batch when the before and after windows are equal length from
   one source. Otherwise state the learning and say the attribution is not clean.

4. **Run Lens A in full**, including the funnel tripwire. Every row must produce a real number or be
   named with its reason: SQP comes from the `search_query` entity and the Business Report and stock
   from the `product` entity, so "not available" is not an answer on this path except for margin.
   Verify rank spend against DataDive Rank Radar and quote cost-per-rank.

5. **Lens B** if the tripwire fires, if the quarterly pass is due, or on request. Say which, and
   quote the number that triggered it.

6. **Deliver** the inline consolidated report plus the branded `.docx` with no cover. Workbook only
   on request. Attach GoTo links per flagged dataset and describe the filters, since the links expire.

7. **Stay read-only.** No AdLabs writes of any kind unless the operator explicitly lifts the rule for
   a specific write in this chat; then apply batch by batch with per-batch confirmation and tags.
