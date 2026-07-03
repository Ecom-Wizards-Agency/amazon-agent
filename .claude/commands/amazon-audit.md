---
description: Run an Amazon ad/sales audit (ads bulk + Business Report + SQP + DataDive → MASTER workbook + narrative)
argument-hint: "[client-market] — new audit each time, e.g. acme-us"
---

# Ad / Sales Audit

Drive the end-to-end Amazon ad/sales audit. Do not duplicate logic here — route into the `amazon-ad-audit` skill and the `tools/amazon-ad-audit/` toolkit, and follow `docs/amazon-ad-audit-playbook.md` for the narrative.

The user's target is: **$ARGUMENTS**

## Steps

1. **Confirm the brief — ask first.** Collect with a single AskUserQuestion (one field per question), skipping only what `$ARGUMENTS`/the conversation already supplies. Never carry a prior client's values as placeholders.
   **Required:** client/brand · marketplace(s) · product lines + ASINs · DataDive niche (URL or ID) · break-even ACOS (real margin if known, else confirm we assume-and-flag). **Also capture:** brand tokens (+ real misspellings), competitor brand names.

2. **Load the skill** `amazon-ad-audit` as source of truth; read the playbook `docs/amazon-ad-audit-playbook.md`.

3. **Scaffold the config** — copy `tools/amazon-ad-audit/config.TEMPLATE.json` → `config.<client>-<market>.json` and fill it. Do not reuse another client's config values.

4. **Preflight** — `build_audit.py --config <cfg> --preflight`. If browser inputs are missing, hand the emitted Codex download task to Codex and stop. Claude pulls the DataDive niche via MCP to the config paths.

5. **Build + QA** — once READY, `--config <cfg>` to build (analyze → audit + SQP workbooks → MASTER → narrative scaffold), then `--validate` (all gates must pass).

6. **Write the narrative** into the pre-filled scaffold per the playbook (operator voice, lean; Problems + Growth Levers; screenshots inline as `![caption](file.png)`). The build renders a branded **A4 / Inter** `.docx` + `.pdf` (EW CI, `render_branded.py`) — **cover page for first-time audits only** (`branding.first_time` / `--cover` / `--no-cover`); regular updates skip the cover. One-time per machine: `prepare_brand_assets.py` for the gitignored `brand/` assets.

7. **Deliver** the MASTER `.xlsx` + branded `.docx` **+ `.pdf`** to the client's Google Drive audit folder; confirm with the operator before a prospect sees it. The A4 `.docx` edits in Google Docs (don't convert to a native gdoc — it breaks the cover/cards).

Break-even ACOS is an assumption until margin is confirmed — flag it, and every ACOS verdict updates on the real number.
