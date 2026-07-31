# Claude Instructions

This project's source of truth for assistant behavior is `AGENTS.md` (shared by Codex, Claude, and any other assistant).

At the start of a new chat in this project:
1. Read `AGENTS.md`.
2. Follow its routing table, library search (index-first), browser checkpoint, evidence, cross-agent handoff, and stop-before-risk rules.
3. Browser note: default to the CDP debug Chrome (port 9222); use the Chrome extension when the task needs the operator's own logged-in session. See the Browser Standard section in `AGENTS.md`.

Everything else (skill routing, keyword-workbook two-agent flow, Google Drive delivery rules, Creator Connections, campaign builder, ad/sales audits, pCloud visual archive) lives in `AGENTS.md` and the specialist skills under `skills/`.

Do not duplicate sections from `AGENTS.md` here. Keep this file as a lightweight entrypoint.
