# Amazon Agent

Amazon Agent is the operator's local runtime workspace for operating Amazon workflows with a lightweight source structure. It combines first-party Amazon help captures, Ecom Wizards MAG SOP markdown, and focused Amazon skills for Seller Central, Amazon Ads, Creator Connections, reporting, account health, FBA shipment workflows, troubleshooting, and bulk-file preparation.

## How To Use

Start with `AGENTS.md`. It is the single source of truth for assistant behavior: skill routing and trigger phrases, library search order, the Browser Standard, evidence capture, output-folder rules, and stop-before-risk rules. This README intentionally does not repeat that content; when the two disagree, `AGENTS.md` wins.

For most work:

1. Classify the workflow: Seller Central, Amazon Ads, Creator Connections, MAG SOP procedure, reporting, logistics, catalog, inventory, or troubleshooting.
2. Search the local markdown/runtime libraries first (index-first; see `AGENTS.md` Local Libraries).
3. Operate in the browser per the Browser Standard in `AGENTS.md` with the logged-in Amazon session.
4. Stop before externally visible or risky actions unless the operator explicitly approves the specific action.

This project uses one main operator (Codex or Claude) with specialist skills, not separate permanent specialist agents. The full routing table lives in `AGENTS.md` under Specialist Skill Model. Each skill under `skills/` carries its own `SKILL.md` (Claude discovery) and `agents/openai.yaml` (Codex discovery).

The search helper can search the local Amazon libraries:

```bash
python3 "tools/search_amazon_libraries.py" "send to amazon shipment create fba shipment" --library mag --limit 5
```

Doc/skill consistency is linted by `python3 tools/lint_agent_docs.py` (skill manifests, routing-table names, writing style, agent-neutral wording). Run it before committing doc or skill changes.

## GitHub Repo

Canonical GitHub repo:

`https://github.com/Ecom-Wizards-Agency/amazon-agent`

The local project should stay aligned with the GitHub repo's lightweight runtime/source structure:

- `AGENTS.md`
- `skills/`
- `Amazon Seller Help/`
- `Amazon Ads Help/`
- `Advertising Help After Login/`
- `MAG SOPs/` as markdown-only SOPs (curated for Amazon work; see `docs/mag-sops-assets.md`)
- `sop-drafts/` as review-stage SOPs that can inform current workflows
- `docs/`

## Visual MAG SOP Archive

The complete visual MAG SOP archive (all captured SOPs plus every screenshot/GIF asset) lives outside the GitHub/runtime project in pCloud. Paths, expected contents, and the curation note live in `docs/mag-sops-assets.md`. Use local/GitHub markdown SOPs first; use the pCloud visual archive only when visual confirmation, screenshots, GIFs, or layout references are needed. Do not commit the archive or any personal sync folder into GitHub.

## Local Browser Preference

GitHub stores browser-neutral defaults. Each teammate can optionally create an ignored local `local-browser-preference.md` file from `docs/local-browser-preference.example.md`. The agent reads that local preference when present; otherwise it uses the browser defined by the Browser Standard in `AGENTS.md`. Browser choice never overrides account/marketplace verification or stop-before-risk rules.

## Client Profiles

Shared operational client context lives in Notion, not GitHub:

- Notion database: `Amazon Agent Ops Profiles`
- Database URL: `<notion-database-url>`
- Data source: `<notion-data-source>`

Each row is one brand-marketplace profile, such as `Acme US` or `Example Brand DE`, linked back to the existing Partner Success brand database.

For fast local lookup, each teammate can keep an ignored cache at `_local/client-profiles/profiles.json`. Treat that cache as generated from Notion and disposable. If it is missing, stale, or conflicts with Notion, use Notion as the source of truth. See `docs/client-profiles.md` and `tools/client-profiles/`.

## What Does Not Belong In GitHub

Do not commit heavy or local work artifacts to the GitHub repo, including:

- Images and GIFs
- Zip files
- `.final-build/`
- Generated outputs
- Evidence screenshots
- Review tracking files
- Downloads and temporary files

Keep those in pCloud or ignored local-only folders. New work should use lowercase `output/`; uppercase `Output/` remains ignored only as a legacy alias.

## SOPs: Drafts, Updates, Maintenance

New SOPs start as markdown drafts in `sop-drafts/`; verified corrections to tracked source SOPs create one change note in `sop-updates/` as the audit trail. Drafts are intentionally searchable during matching workflows (newest learnings), but stay review-stage until the operator promotes them. The `/create-sop` and `/fix-sop` workflows, the SOP-vs-skill rule, and storage locations live in `skills/amazon-sop-maintenance/`.

Do not store screenshots, GIFs, exports, or heavy evidence in `sop-updates/` or `sop-drafts/`. Keep those in pCloud or ignored local evidence folders and link or summarize them in the change note.

## Local Artifact Folders

The base local artifact folders are present after clone through `.gitkeep` files, but real files inside them are ignored and must not sync to GitHub.

Use an ongoing client-first structure for generated work:

```text
output/{client}/{workflow}/
downloads/{client}/{source}/
evidence/{client}/{workflow}/
```

Dates belong in filenames, not folder names. The controlled workflow names, client-slug rules, and folder roles live in `AGENTS.md` under Local Output Storage.
