# Amazon Agent

Amazon Agent is Victor's local runtime workspace for operating Amazon workflows with a lightweight source structure. It combines first-party Amazon help captures, Ecom Wizards MAG SOP markdown, and focused Amazon skills for Seller Central, Amazon Ads, Creator Connections, reporting, account health, FBA shipment workflows, troubleshooting, and bulk-file preparation.

## How To Use

Start with `agent.md`. It is the source of truth for assistant behavior, routing, library search order, connected-browser checkpoints, evidence capture, and stop-before-risk rules.

For most work:

1. Classify the workflow: Seller Central, Amazon Ads, Creator Connections, MAG SOP procedure, reporting, logistics, catalog, inventory, or troubleshooting.
2. Search the local markdown/runtime libraries first.
3. Use the connected Codex browser with the logged-in Amazon session when browser operation is needed. Common choices are Chrome or Brave.
4. Stop before externally visible or risky actions unless Victor explicitly approves the specific action.

This project uses one main Codex operator with specialist skills, not separate permanent specialist agents. The dispatcher skill routes work into playbooks like `amazon-seo`, `amazon-catalog`, `amazon-ads`, `amazon-inventory-planning`, `amazon-opportunity-explorer`, and `amazon-communications`.

For inventory/reshipment work, useful trigger phrases are `Weekly FBA Inventory Overview`, `reshipment planning`, `FBA inventory planning`, and `inventory overview`.

For Product Opportunity Explorer work, useful trigger phrases are `Product Opportunity Explorer`, `Opportunity Explorer`, `OEI`, `POE`, `Niche Scout`, `amazon-image-strategy`, and `oei-product-strategy`.

For SOP maintenance, use `/create-sop` to create a new tracked SOP draft in `sop-drafts/`. Use `/fix-sop` for a verified correction that updates a tracked source file and creates a synced change note in `sop-updates/`. Local evidence stays under ignored `output/{client-or-brand-or-general}/sop-maintenance/` and `evidence/{client-or-brand-or-general}/sop-maintenance/`.

Draft SOPs are intentionally available to the agent for normal workflow routing. They represent recent learnings and still-improving procedure. Use them as helpful internal guidance, but prefer first-party Amazon docs for current rules/UI and promoted MAG SOPs for settled agency process.

The routing helper can search the local Amazon libraries:

```bash
python3 "skills/amazon-operator-routing/scripts/search_amazon_libraries.py" "send to amazon shipment create fba shipment" --library mag --limit 5
```

## GitHub Repo

Canonical GitHub repo:

`https://github.com/Ecom-Wizards-Agency/amazon-agent`

The local project should stay aligned with the GitHub repo's lightweight runtime/source structure:

- `AGENTS.md`
- `agent.md`
- `skills/`
- `Amazon Seller Help/`
- `Amazon Ads Help/`
- `Advertising Help After Login/`
- `MAG SOPs/` as markdown-only SOPs
- `sop-drafts/` as review-stage SOPs that can inform current workflows
- `docs/`

## Visual MAG SOP Archive

The complete visual MAG SOP archive lives outside the GitHub/runtime project. Victor's current local placeholder path is:

`/Users/victoruhl/Documents/pCloud/Amazon Agent/MAG SOPs`

Use local/GitHub markdown SOPs first for search and routing. Use the pCloud visual archive only when visual confirmation, screenshots, GIFs, or layout references are needed.

Expected pCloud visual archive check:

- 535 Markdown files
- 3,621 assets in `assets/`
- 0 missing local image references

The pCloud folder must be locally available when visual SOPs are needed. This path is user-specific: each team member should download or sync the shared pCloud archive locally and point their setup to their own local path. Do not commit the archive or any personal sync folder into GitHub.

## Opportunity Explorer Extraction

The Product Opportunity Explorer workflow uses repo-native scripts instead of a Chrome extension:

- `tools/opportunity-explorer/extract-opportunity-explorer.js`
- `tools/opportunity-explorer/format-opportunity-explorer-export.mjs`

The scripts scrape the visible Product Opportunity Explorer page in the logged-in connected browser session and save structured JSON plus Markdown for image strategy, product strategy, SEO, and Rufus/Alexa AI workflows.

The original Chrome extension remains in pCloud only as historical/source reference during transition. Once the script is tested, it is not needed as part of the runtime workflow.

## Local Browser Preference

GitHub stores browser-neutral defaults. Each teammate can optionally create an ignored local `local-browser-preference.md` file from `docs/local-browser-preference.example.md`.

The agent should read that local preference when present. If no local preference exists, use the connected Codex browser/session available in the current chat. Browser choice never overrides account/marketplace verification or stop-before-risk rules.

## Client Profiles

Shared operational client context lives in Notion, not GitHub:

- Notion database: `Amazon Agent Ops Profiles`
- Database URL: `https://www.notion.so/b42e52380b874dd5be7c0fba6c0d017e`
- Data source: `collection://8e2f0901-3b8e-44ac-8fd6-464f834bd824`

Each row is one brand-marketplace profile, such as `Swissker US` or `Piercing XXL DE`, linked back to the existing Partner Success brand database.

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

## SOP Update History

Verified SOP corrections should create one markdown change note in `sop-updates/`. This folder is synced to GitHub as the audit trail for source SOP updates.

Do not store screenshots, GIFs, exports, or heavy evidence in `sop-updates/`. Keep those in pCloud or ignored local evidence folders and link or summarize them in the change note.

## SOP Drafts

New SOPs should start as markdown drafts in `sop-drafts/`. Drafts should still be searched by the agent during matching Amazon workflows because they often contain the newest learnings from recent runs.

Promote a draft into `MAG SOPs/` or another source library only when Victor explicitly asks. Until promoted, treat drafts as review-stage guidance: cite them in the operator note when used, and resolve conflicts in favor of first-party Amazon docs for current rules/UI and promoted SOPs for settled agency procedure.

Create or update a SOP when documenting a human/team Amazon process, checklist, browser workflow, or operating procedure. Create or update a skill only when changing how Codex behaves, routes work, uses tools/scripts, or applies repeatable AI workflow instructions.

## Local Artifact Folders

The base local artifact folders are present after clone through `.gitkeep` files, but real files inside them are ignored and must not sync to GitHub.

Use an ongoing client-first structure for generated work:

```text
output/{client-or-brand}/{workflow}/
downloads/{client-or-brand}/{source}/
evidence/{client-or-brand}/{workflow}/
output/{client-or-brand}/review-management/
```

Dates belong in filenames, not folder names.

Examples:

```text
output/swissker/seo/2026-05-21_keyword-research.md
downloads/swissker/business-reports/2026-05-21_sales-traffic.csv
evidence/swissker/account-check/2026-05-21_account-health.png
output/swissker/review-management/reviews.csv
```

Controlled workflow names:

- `seo`
- `opportunity-data`
- `ads`
- `reporting`
- `inventory`
- `catalog`
- `account-check`
- `support-prep`
- `sop-maintenance`

Use `output/` for generated analysis and deliverables, `evidence/` for screenshots/UI proof, and `downloads/` for raw Amazon exports before processing. Review management is ongoing and client-specific, so update the same client folder over time. `review-tracking/` remains ignored only as a legacy local folder for old files. If a workflow needs local context, put `README.md` or `operator-note.md` inside the relevant workflow folder. Use Notion for ongoing team status.
