---
description: Run an Amazon ad/sales audit (asks the job first, then only what is not already on file)
argument-hint: "[client-market] [first-time|monthly|actions] (e.g. acme-us, or 'acme us monthly')"
---

# Amazon Ad / Sales Audit

Drive the audit. Do not duplicate logic here. Route into the self-contained `amazon-audit` skill.
Its entrypoint selects the posture and loads the detailed analysis and delivery references.

The user's target is: **$ARGUMENTS**

## Steps

1. **Load the skill** `amazon-audit` as the source of truth.

2. **Ask the job first, with one AskUserQuestion, and ask nothing else in that round.** Options:
   **First-time audit** (new client onboarding or a prospect pitch, internally `deep`),
   **Monthly review** (a client we already run, `monthly`), **Actions only** (just the change list,
   `actions`). Skip this round entirely when `$ARGUMENTS` already names the job. The labels name
   the job, never the data source: onboarding a client who is already in SYNQ is a first-time
   audit.

3. **Detect and pre-fill. Silently, no question.** On `monthly` and `actions`, call SYNQ
   `list_clients` (skip `is_demo` clients and any client that is not `active`), find the brand,
   confirm it by SKU or title with `get_catalog`, then run `get_sync_status`. Found means the SYNQ
   path. The AdLabs carve-out account (US and CA) uses the AdLabs startup in the skill instead. A
   client still being onboarded into SYNQ (`docs/synq-mcp.md`) uses the download path; any other client not found is a
   blocker to report. A first-time audit skips the lookup and always takes the download path.
   Then resolve what is already on file rather than asking for it: the
   `get_catalog` goals (AdLabs carve-out: AdLabs profile memory), the client ops profile via
   `node tools/client-profiles/find-client-profile.mjs <slug>`, and the per-client config.

4. **Ask only what step 3 did not resolve, with a second AskUserQuestion.** Never carry a prior
   client's values as placeholders.
   - **First-time audit:** the full brief. Client and marketplaces, product lines and ASINs,
     the ASIN set and marketplace for SoldScope keyword research (anchor first, up to 9
     competitors) or the path to an existing `research.json`, break-even ACOS (real margin if known, else confirm we assume and
     flag), brand tokens including real misspellings and sub-brand treatment, competitor brands.
   - **Monthly review:** three fields only. Marketplaces this cycle (default all profiles found),
     date window (default last 30 days against the preceding period), and anything not in the
     tracker (stock event, promo, price change, launch). Then state what was auto-filled so a wrong
     value can be corrected in one word. Do not ask whether Lens B is due; compute and report it.
   - **Actions only:** marketplaces and window.

5. **Context first** per the skill. On `deep` that is the call notes, matched on people and product
   rather than the name alone. Flag anything missing rather than assuming a clean window.

6. **Run the lens.** Lens A on every run, including the funnel tripwire. Lens B as well on `deep`.
   Every Lens A row must produce a number or be named with its reason.

7. **Build.** On the download path: scaffold the config, run `--preflight`, gather the browser and
   SoldScope MCP inputs, then build and `--validate` until every gate passes. SoldScope calls
   that spend credits need one run approval naming the ASINs, marketplace and expected credits;
   rank-tracker writes need exact-action approval (`tools/soldscope/README.md`). If one capability is
   unavailable, hand off only that checklist to any capable agent. On the SYNQ path (AdLabs carve-out: the
   AdLabs path), build to the same depth without `build_audit.py`.

8. **Write the narrative** into the scaffold per the skill: operator voice, organic-first, lean,
   one **Problems and Solutions** section of five to seven `### Priority N:` action-led headings,
   each with a short diagnosis, one evidence sentence and one sentence beginning `I would`.
   Screenshots inline as `![caption](file.png)`, on their own line.

9. **Deliver** the MASTER `.xlsx` and the branded `.docx` to the client's Drive audit folder via
   the desktop mount. Confirm with the operator before a prospect sees anything.

Break-even ACOS is an assumption until margin is confirmed. Flag it, and every ACOS verdict
updates on the real number. Stop before any account-changing action; this is analysis only.
