# Claude Instructions

This project's source of truth for assistant behavior is `AGENTS.md` (shared by Codex, Claude, and any other assistant).

At the start of a new chat in this project:
1. Read `AGENTS.md`.
2. Follow its routing table, library search (index-first), browser checkpoint, evidence, cross-agent handoff, and stop-before-risk rules.
3. Claude-specific browser note: use the operator's connected browser (Chrome or Brave), honoring `local-browser-preference.md` if present; see the Browser Standard section in `AGENTS.md`.

Everything else (skill routing, keyword-workbook two-agent flow, Google Drive delivery rules, Creator Connections, campaign builder, ad/sales audits, pCloud visual archive) lives in `AGENTS.md` and the specialist skills under `skills/`.

Do not duplicate sections from `AGENTS.md` here. Keep this file as a lightweight entrypoint.
