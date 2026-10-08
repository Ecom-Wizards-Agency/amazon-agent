---
name: amazon-sop-maintenance
description: "Create, verify, and correct Amazon SOP drafts, links, steps, and update notes while keeping SOPs distinct from agent skills."
---

# Amazon SOP Maintenance

Browser: None (docs/local work; UI verification during /fix-sop, when needed, runs over CDP).

Use this skill when the operator asks to create, review, fix, or draft an SOP, especially with `/create-sop`, `/fix-sop`, `outdated SOP`, `broken SOP link`, `wrong SOP steps`, `SOP correction`, or `new SOP draft`.

## SOP vs Skill

Create or update a SOP when documenting a human/team Amazon process, checklist, browser workflow, or operating procedure.

Create or update a skill only when changing how the current agent behaves, routes work, uses tools/scripts, or applies repeatable AI workflow instructions.

If someone asks vaguely for a workflow, default to a SOP when it is human/team process documentation. Default to a skill only when the change is about AI behavior.

## Storage

Use ignored local artifacts for screenshots, local evidence, and working notes:

- `output/general/sop-maintenance/`
- `output/{client}/sop-maintenance/`
- `evidence/general/sop-maintenance/`
- `evidence/{client}/sop-maintenance/`

`{client}` is the normalized lowercase-kebab client slug from `AGENTS.md`. Use `general` when no client or brand is involved.

Dates belong in filenames:

- `YYYY-MM-DD_{short-topic}.md`

Use the GitHub-synced `sop-updates/` folder only for final change notes after a SOP correction has been verified and applied to a tracked source file:

- `sop-updates/YYYY-MM-DD_{short-topic}.md`

Use the GitHub-synced `sop-drafts/` folder for newly created SOP drafts:

- `sop-drafts/YYYY-MM-DD_{short-topic}.md`

Do not store screenshots, GIFs, exports, zip files, or heavy artifacts in `sop-updates/` or `sop-drafts/`. Link to or summarize local/pCloud evidence instead.

## Source Safety

During `/create-sop`, do not edit:

- `MAG SOPs/`
- `Amazon Seller Help/`
- `Amazon Ads Help/`
- `Advertising Help After Login/`
- `AGENTS.md`, `README.md`, `docs/`, `skills/`, or other GitHub source files

Only edit source files when the operator explicitly asks for that exact source update.

Knowledge units under `knowledge/` are the one authored exception: an attended session may create or edit a unit and regenerate the index and README with the commands in Knowledge Units. Captures stay read-only in every session: never hand-edit `MAG SOPs/`, `Amazon Seller Help/`, `Amazon Ads Help/`, `Advertising Help After Login/` or `AdLabs Help/`, even to fix a unit's source. Unattended runs do not write units.

During `/fix-sop`, source edits are allowed only after the issue has been verified against current Amazon docs, browser UI, pCloud visual archive, or user-provided evidence. Stop before pushing unless the operator explicitly asks to push.

## Knowledge Units

A learning becomes a knowledge unit instead of a SOP draft when it is one question with an answer that fits a unit under 90 lines: a symptom, an error text, a rule or a decision a teammate could ask again. A longer step-by-step procedure stays a SOP draft in `sop-drafts/`, and the unit links it.

Apply the rule in `docs/knowledge-library.md`: strip every client-specific token (brand, product, person, ID, amount, link, date finer than month). If what remains still teaches any teammate how to recognise and solve the problem on any account, it is a unit. If it is empty or meaningless without the client, it belongs in the team vault (`Clients/{Name}/Runs/`, `Amazon Ops.md` or a one-line Lesson).

Commands, run from the repo root:

1. `python3 tools/knowledge/new_unit.py --from-card <card.json>` or `--title ... --topic ...` creates the unit with the next `KC-NNNN` id and stages its ledger row.
2. Fill the unit from `knowledge/TEMPLATE.md`: every frontmatter key in order, every body section, symptom-first title.
3. `python3 tools/knowledge/lint_knowledge.py --strict` checks format, enums, cited paths and the privacy scrub. Fix every finding.
4. `python3 tools/knowledge/build_knowledge_index.py --readme` regenerates `knowledge/_index/knowledge-index.json` and `knowledge/README.md`.
5. `python3 tools/knowledge/ledger.py check` confirms every unit has a ledger row; `append --from-staging` moves staged rows into the team vault ledger in an attended session.

Review gate: a unit enters as `status: draft` and `verification: unverified` and stays there until a human ticks it. The agency lead ticks any unit; the ads lead ticks ads units; the operations lead ticks logistics, catalog, support-cases and account-health units from threads they owned. The agency lead decides every policy-risk or not-publishable card. The tick sets `status: reviewed`. Only a live read-only check in the attended browser, or a matching first-party capture, sets `verification: verified` with `verified_on` and `verified_how`. An agent never ticks its own unit.

Privacy: nothing with a client name, product name, person's name, ASIN, SKU, FNSKU, EAN, shipment, case, order or removal ID, merchant token, price, unit count, address, 3PL or vendor name, Slack ID, Slack permalink, or Drive, Notion, Zoom or Cap link enters `knowledge/`. People appear as roles only. Provenance goes to the team vault ledger, joined by the unit id.

## `/fix-sop` Workflow

Use `/fix-sop` for the full correction loop.

1. Identify the affected SOP title, path, and source link.
2. Verify the correct version using current Amazon docs, current browser UI, pCloud visual archive, or user-provided evidence.
3. Update the relevant tracked SOP/source file locally.
4. Create one synced change note in `sop-updates/YYYY-MM-DD_{short-topic}.md` using `sop-updates/TEMPLATE.md`.
5. Run checks, normally `git diff --check` and any relevant search/helper check.
6. Stop before pushing unless the operator explicitly asks to push.

The change note should include:

- Problem.
- Verification.
- Change made.
- Files changed.
- Checks run.
- Evidence summary or links.
- Follow-up.

## `/create-sop` Workflow

Create a new tracked SOP draft from a task, browser workflow, or user-provided notes.

Save the draft in `sop-drafts/YYYY-MM-DD_{short-topic}.md` using `sop-drafts/TEMPLATE.md`.

Draft structure:

- Title.
- Purpose.
- Preconditions.
- Required inputs.
- Step-by-step workflow.
- Evidence/screenshots needed.
- Stop-before-risk points.
- Source docs/SOPs used.
- Open questions or assumptions.
- Promotion notes.

Do not promote the draft into `MAG SOPs/` or another source library unless the operator explicitly asks.

## Evidence

If visual proof is needed, use the pCloud visual MAG SOP archive or browser screenshots. Save screenshots and proof notes under `evidence/.../sop-maintenance/`.

Never inspect cookies, local storage, tokens, passwords, payment details, tax IDs, or private account settings while gathering SOP evidence.
