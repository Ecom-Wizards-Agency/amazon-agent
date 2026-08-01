---
description: Run an Amazon ad/sales audit (auto-detects AdLabs vs downloaded files, then asks the report posture)
argument-hint: "[client-market] [deep|monthly|actions] (e.g. acme-us, or 'acme us monthly')"
---

# Amazon Ad / Sales Audit

Drive the audit. Do not duplicate logic here. Route into the `amazon-audit` skill, which is
self-contained: the lens, the narrative standard, the workbook design and the branded-document
contract all live in `skills/amazon-audit/SKILL.md`.

The user's target is: **$ARGUMENTS**

## Steps

1. **Load the skill** `amazon-audit` as the source of truth.

2. **Detect the data source. Do not ask.** Run the AdLabs startup sequence (`start_chat_session`,
   `get_entity_data(teams)`, `get_entity_data(profiles, team_id)`) and look for the brand. Found
   means the MCP path; not found means the download path. **Name the detected source** in the next
   message so the operator can override it in one word.

3. **Confirm the brief with a single AskUserQuestion**, skipping whatever `$ARGUMENTS` or the
   conversation already supplies. Never carry a prior client's values as placeholders.
   **Posture** defaults to `deep` from this command: full narrative, cover page, MASTER workbook.
   **Also capture:** client and marketplaces, product lines and ASINs, date window, DataDive niche
   (URL or ID), break-even ACOS (real margin if known, else confirm we assume and flag), brand
   tokens including real misspellings, competitor brand names.

4. **Context first** per the skill. On `deep` that is the call notes, matched on people and product
   rather than the name alone. Flag anything missing rather than assuming a clean window.

5. **Run the lens.** Lens A on every run, including the funnel tripwire. Lens B as well on `deep`.
   Every Lens A row must produce a number or be named with its reason.

6. **Build.** On the download path: scaffold the config, `--preflight`, hand the Codex download
   task over, pull DataDive over MCP, then build and `--validate` until every gate passes. On the
   MCP path, build to the same depth without `build_audit.py`.

7. **Write the narrative** into the scaffold per the skill: operator voice, organic-first, lean,
   `Problem N` and `Lever N`, screenshots inline as `![caption](file.png)`.

8. **Deliver** the MASTER `.xlsx` and the branded `.docx` to the client's Drive audit folder via
   the desktop mount. Confirm with the operator before a prospect sees anything.

Break-even ACOS is an assumption until margin is confirmed. Flag it, and every ACOS verdict
updates on the real number. Stop before any account-changing action; this is analysis only.
