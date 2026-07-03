---
name: amazon-sop-maintenance
description: Use for Amazon SOP maintenance commands and requests, including /create-sop, /fix-sop, outdated SOPs, broken SOP links, wrong SOP steps, questionable MAG SOP guidance, verified SOP corrections, synced SOP update notes, and new SOP drafts. Distinguishes human/team SOPs from Codex skills.
---

# Amazon SOP Maintenance

Use this skill when the operator asks to create, review, fix, or draft an SOP, especially with `/create-sop`, `/fix-sop`, `outdated SOP`, `broken SOP link`, `wrong SOP steps`, `SOP correction`, or `new SOP draft`.

## SOP vs Skill

Create or update a SOP when documenting a human/team Amazon process, checklist, browser workflow, or operating procedure.

Create or update a skill only when changing how Codex behaves, routes work, uses tools/scripts, or applies repeatable AI workflow instructions.

If someone asks vaguely for a workflow, default to a SOP when it is human/team process documentation. Default to a skill only when the change is about AI behavior.

## Storage

Use ignored local artifacts for screenshots, local evidence, and working notes:

- `output/general/sop-maintenance/`
- `output/{client-or-brand}/sop-maintenance/`
- `evidence/general/sop-maintenance/`
- `evidence/{client-or-brand}/sop-maintenance/`

Dates belong in filenames:

- `YYYY-MM-DD_{short-topic}.md`

Use `general` when no client or brand is involved.

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

During `/fix-sop`, source edits are allowed only after the issue has been verified against current Amazon docs, browser UI, pCloud visual archive, or user-provided evidence. Stop before pushing unless the operator explicitly asks to push.

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
