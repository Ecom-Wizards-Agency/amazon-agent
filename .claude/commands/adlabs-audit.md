---
description: Run an AdLabs-MCP PPC audit of a managed account (context-first, 10-step per marketplace, Rank-Radar verified, read-only)
argument-hint: "[client + marketplace(s)] [audit|actions] (e.g. 'acme de it' or 'acme de actions')"
---

# AdLabs PPC Audit

Drive an AdLabs-based audit of a managed account. Do not duplicate logic here. Route into the `amazon-adlabs-audit` skill as source of truth.

The user's target is: **$ARGUMENTS**

## Steps

1. **Load the skill** `skills/amazon-adlabs-audit/SKILL.md` and follow its startup sequence (session → teams → profiles → profile targets → audit guide).

2. **Context first.** Pull AdLabs profile memory, the local/Notion client ops profile, the brand's A/B-Tests event log (rows overlapping the window: tests, promos, stock events, launches), and recent client call summaries. **Flag anything missing.** Never assume a clean window.

3. **Confirm the brief** with one AskUserQuestion, skipping what `$ARGUMENTS`/context already supplies: profiles/marketplaces · date range (default last 30 days) · target source (Optimization Groups > profile targets; break-even ACOS if known) · brand terms + sub-brand treatment · mode (`audit` full / `actions` list-only).

4. **Run the audit** per the skill: steps 1–4 per marketplace → midpoint check-in → steps 5–10, plus the DataDive Rank-Radar verification of every rank campaign (cost-per-rank verdicts, profile currency). Apply the grading rules (group targets, ACOS-ratio rule, spend reconciliation).

5. **Deliver** inline (default) or, on request, the styled `.xlsx` + `.docx` to the client's Drive `Audits/` folder per the skill's deliverable spec.

6. **Stay read-only.** No AdLabs writes of any kind unless the operator explicitly lifts the rule for a specific write in this chat; then apply batch-by-batch with per-batch confirmation and tags.
