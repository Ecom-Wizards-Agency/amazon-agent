# Amazon Ad / Sales Audit Toolkit

Client-agnostic builder for the Ecom Wizards Amazon ad/sales audit — the same deliverable we ship for real client audits, now driven entirely by a per-client config instead of a hand-copied fork.

**One config, drop the inputs, run.** Nothing is client-specific in the code. To start a new audit, copy `config.TEMPLATE.json` and follow `NEW-CLIENT.md`. Local `config.<client>-<market>.json` files are worked examples (gitignored); only `config.TEMPLATE.json` is committed.

The narrative voice, section structure, and workbook layout follow `docs/amazon-ad-audit-playbook.md` (the standard). This toolkit produces the workbooks and a numbers-filled narrative **scaffold**; the operator writes the prose, findings, and levers per the playbook.

## What it produces

| Deliverable | File | Built by |
|---|---|---|
| Master workbook (primary) | `<date>_<Client>_<MKT>_Amazon_Audit_MASTER.xlsx` | `build_master_workbook.py` |
| Ad/Sales audit workbook | `<date>_<Client>_<MKT>_Ad_Audit_Branded.xlsx` | `build_audit_workbook.py` |
| SQP Intelligence workbook | `<date>_<Client>_<MKT>_SQP_Intelligence.xlsx` | `build_sqp_workbook.py` |
| Narrative scaffold (operator edits) | `<date>_<Client>_<MKT>_Sales_Audit.md` / `.docx` | `narrative_scaffold.py` + `md_to_docx.py` |

The **master** merges the audit + SQP tabs under a built one-page `① Overview` (KPI strip incl. ad:organic ratio, traffic-mix with SQP purchase-capture, placement, findings, recommendations).

## Required inputs (the contract, in `config.inputs`)

| Input | Source | Who gathers it |
|---|---|---|
| Ads bulk `.xlsx` | Amazon Ads console (bulk operations) | Codex (connected browser download) |
| Business Report `.csv` | Seller Central → Business Reports | Codex (connected browser download) |
| Multi-ASIN SQP `.csv` (per product group) | Brand Analytics → Search Query Performance | Codex (connected browser download) |
| DataDive niche JSON | DataDive MCP (`get_niche_keywords` / `get_niche_competitors`) | Claude (MCP pull) |

Run `build_audit.py --config <cfg> --preflight` to get a copy-ready Codex handoff for the missing browser downloads, or a READY status.

## Commands

```bash
# 1. Preflight — emits a Codex download task or READY
python3 tools/amazon-ad-audit/build_audit.py --config tools/amazon-ad-audit/config.<client>-<market>.json --preflight

# 2. Build everything (analyze → 3 workbooks → master → narrative scaffold)
python3 tools/amazon-ad-audit/build_audit.py --config tools/amazon-ad-audit/config.<client>-<market>.json

# 3. QA gates
python3 tools/amazon-ad-audit/build_audit.py --config tools/amazon-ad-audit/config.<client>-<market>.json --validate
```

## Files

- `ew_audit_style.py` — shared workbook styling; palette/fonts come from the local branding file (see BRANDING.md). ACOS is always a ratio, never divided by 100.
- `analyze_audit.py` — parser → `metrics.json` + `clean/*.csv` + `clean/sqp_summary.json`.
- `build_audit_workbook.py` / `build_sqp_workbook.py` / `build_master_workbook.py` — the three builders.
- `narrative_scaffold.py` + `md_to_docx.py` — narrative draft.
- `build_audit.py` — orchestrator (`--config` / `--preflight` / `--validate`).
- `config.TEMPLATE.json`, `NEW-CLIENT.md`, `WORKFLOW.md` — onboarding.

## Break-even ACOS

`breakeven_acos` in the config is an **assumption** until margin is confirmed. Every red/amber ACOS verdict keys off it (green <30% · light-green <break-even · amber ≤60% · red >60%). Swap the real number and rebuild.
