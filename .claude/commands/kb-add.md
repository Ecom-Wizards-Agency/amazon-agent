---
description: Draft a knowledge unit from this session or a sweep card, lint it, rebuild the index and stop before committing
argument-hint: "[optional card path] (e.g. '_local/knowledge-sweep/cards/CARD-0042.json'; empty = draft from this session)"
---

# /kb-add: add a knowledge unit

Turn an Amazon answer from this session, or a sweep card, into one anonymised unit under
`knowledge/<topic>/`. The rules, the unit format and the review gate are in
`docs/knowledge-library.md`. Load the `amazon-sop-maintenance` skill first; its Knowledge
Units section owns the procedure.

The new unit is **draft and unverified until a human ticks it**. Say so in every reply that
uses it.

## Steps

1. **Check that it qualifies.** Strip every client token from the lesson (brand, product,
   person, ID, amount, link, date finer than month). If what remains still teaches any
   teammate how to recognise and solve the problem, continue. If it is empty without the
   client, say it belongs in the team vault (`Clients/{Name}/Runs/`, `Amazon Ops.md` or a
   Lesson) and stop.
2. **Check for an existing unit.**
   `python3 tools/search_amazon_libraries.py "<symptom or exact error text>" --library kb --limit 5`.
   If a unit already answers it, propose an edit to that unit instead of a new one.
3. **Create the unit.**
   - With a card path as the argument:
     `python3 tools/knowledge/new_unit.py --from-card <card path>`
   - Without one: `python3 tools/knowledge/new_unit.py --title "<symptom first>" --topic <topic>`,
     then fill it from this session following `knowledge/TEMPLATE.md`.
   Keep `status: draft` and `verification: unverified`. Never set `reviewed` or `verified`
   yourself. Keep the unit under 90 lines; a long procedure goes to `sop-drafts/` and the unit
   links it.
4. **Rebuild the index and README.** `python3 tools/knowledge/build_knowledge_index.py --readme`.
   The lint checks index drift, so this step comes first.
5. **Lint until clean.** `python3 tools/knowledge/lint_knowledge.py --strict`. Fix every
   finding in the unit; never weaken the denylist or the scrub to pass.
6. **Stage the ledger row.** `new_unit.py` stages the provenance row (client, thread,
   permalink, IDs) under the gitignored `_local/knowledge-sweep/`. Leave it staged; moving it
   into the vault ledger with `python3 tools/knowledge/ledger.py append --from-staging` is a
   separate attended step the operator starts. Identifiers go in that row, never in the unit.
7. **Report and stop.** Give the unit path and id, the topic, the lint result, the index count,
   where the staged ledger row is, and who ticks it (the agency lead for any unit, the ads
   lead for ads, the operations lead for logistics, catalog, support-cases and account-health
   units from threads they owned). Stop before `git commit`.

Stop rules: never commit or push; never post to Slack or message anyone; never hand-edit a
capture library (`MAG SOPs/`, `Amazon Seller Help/`, `Amazon Ads Help/`,
`Advertising Help After Login/`, `AdLabs Help/`); nothing client-specific enters `knowledge/`.
