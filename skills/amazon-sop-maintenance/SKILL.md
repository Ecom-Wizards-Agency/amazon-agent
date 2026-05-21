---
name: amazon-sop-maintenance
description: Use for Amazon SOP maintenance commands and requests, including /bug, /create-sop, outdated SOPs, broken SOP links, wrong SOP steps, questionable MAG SOP guidance, and new SOP drafts. Creates local review-safe SOP bug reports or SOP drafts without editing source SOP/help/GitHub files unless Victor explicitly asks for that exact source edit.
---

# Amazon SOP Maintenance

Use this skill when Victor asks to report, review, fix, or draft an SOP, especially with `/bug`, `/create-sop`, `outdated SOP`, `broken SOP link`, `wrong SOP steps`, `SOP bug`, or `new SOP draft`.

## Storage

Default to ignored local artifacts, not GitHub source edits:

- `output/general/sop-maintenance/`
- `output/{client-or-brand}/sop-maintenance/`
- `evidence/general/sop-maintenance/`
- `evidence/{client-or-brand}/sop-maintenance/`

Dates belong in filenames:

- `YYYY-MM-DD_bug_{short-topic}.md`
- `YYYY-MM-DD_create-sop_{short-topic}.md`

Use `general` when no client or brand is involved.

## Source Safety

During `/bug` or `/create-sop`, do not edit:

- `MAG SOPs/`
- `Amazon Seller Help/`
- `Amazon Ads Help/`
- `Advertising Help After Login/`
- `agent.md`, `AGENTS.md`, `README.md`, `docs/`, `skills/`, or other GitHub source files

Only edit source files when Victor explicitly asks for that exact source update. A SOP maintenance report may recommend a source edit, but it must stop before making that edit.

## `/bug` Workflow

Create a local bug report for outdated, broken, unclear, or risky SOP guidance.

Capture:

- SOP title, path, and source link when available.
- Problem type: outdated steps, broken link, unclear wording, wrong UI, risky instruction, missing context, or duplicate/conflicting SOP.
- What is wrong and why it matters.
- Current observed Amazon UI/docs evidence when available.
- Visual proof path when screenshots or visual SOP references are used.
- Suggested correction.
- Risk level: low, medium, or high.
- Whether a source SOP edit is recommended.

Stop after creating the bug report unless Victor explicitly asks to update the source SOP or GitHub docs.

## `/create-sop` Workflow

Create a local SOP draft from a task, browser workflow, or user-provided notes.

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

Stop after creating the draft unless Victor explicitly asks to move it to pCloud or update GitHub/source files.

## Evidence

If visual proof is needed, use the pCloud visual MAG SOP archive or browser screenshots. Save screenshots and proof notes under `evidence/.../sop-maintenance/`.

Never inspect cookies, local storage, tokens, passwords, payment details, tax IDs, or private account settings while gathering SOP evidence.
