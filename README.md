# Amazon Agent

Amazon Agent is the operator's local runtime workspace for operating Amazon workflows with a lightweight source structure. It combines first-party Amazon help captures, Ecom Wizards MAG SOP markdown, and focused Amazon skills for Seller Central, Amazon Ads, Creator Connections, reporting, account health, FBA shipment workflows, troubleshooting, and bulk-file preparation.

## How To Use

Designers who only need image concepts/copy and product-photo prompts can use the
[selective design installation prompt](docs/design-skills-installation.md).
It installs only those two skills; full Amazon operator setup is unnecessary.

Start with `AGENTS.md`. It is the single source of truth for assistant behavior: the Operating Contract (account, approval, safety, Drive and Slack identity rules), skill routing, library search order and the Browser Standard. Output-folder rules are in `docs/local-output-storage.md`. This README intentionally does not repeat that content; when the two disagree, `AGENTS.md` wins.

For most work:

1. Classify the workflow: Seller Central, Amazon Ads, Creator Connections, MAG SOP procedure, reporting, logistics, catalog, inventory, or troubleshooting.
2. Search the local markdown/runtime libraries first (index-first; see `AGENTS.md` Local Libraries).
3. Operate in the browser per the Browser Standard in `AGENTS.md` with the logged-in Amazon session.
4. Stop before externally visible or risky actions unless the operator explicitly approves the specific action.

This project uses the current working agent as one main operator with specialist skills, not separate permanent specialist agents. The agent owns each workflow end to end when the required capabilities are available; any handoff is capability-based and optional. The full routing table lives in `AGENTS.md` under Specialist Skill Model. Each skill under `skills/` carries runtime-specific discovery manifests, but the shared instructions are agent-neutral.

The search helper can search the local Amazon libraries:

```bash
python3 "tools/search_amazon_libraries.py" "send to amazon shipment create fba shipment" --library mag --limit 5
```

`--library kb` searches the anonymised knowledge units in `knowledge/`, which are the first stop for a symptom, an error text or a how-do-we question (see `docs/knowledge-library.md`).

Doc/skill consistency is linted by `python3 tools/lint_agent_docs.py` (parsed skill manifests, bounded UI metadata, routing-table names, writing style, and agent-neutral wording). Run it before committing doc or skill changes.

## GitHub Repo

Canonical GitHub repo:

`https://github.com/Ecom-Wizards-Agency/amazon-agent`

The local project should stay aligned with the GitHub repo's lightweight runtime/source structure:

- `AGENTS.md`
- `skills/`
- `knowledge/` as anonymised, verification-labelled answers from real account work (rules in `docs/knowledge-library.md`)
- `Amazon Seller Help/`
- `Amazon Ads Help/`
- `Advertising Help After Login/`
- `MAG SOPs/` as markdown-only SOPs (curated for Amazon work; see `docs/mag-sops-assets.md`)
- `sop-drafts/` as review-stage SOPs that can inform current workflows
- `docs/`

## Visual MAG SOP Archive

The complete visual MAG SOP archive (all captured SOPs plus every screenshot/GIF asset) lives outside the GitHub/runtime project in pCloud. Paths, expected contents, and the curation note live in `docs/mag-sops-assets.md`. Use local/GitHub markdown SOPs first; use the pCloud visual archive only when visual confirmation, screenshots, GIFs, or layout references are needed. Do not commit the archive or any personal sync folder into GitHub.

## Browser Choice

Routing is by session, not by agent, and lives in the Browser Standard in `AGENTS.md`. The per-workflow table is `docs/browser-routing-map.md`. Browser choice never overrides account/marketplace verification or stop-before-risk rules.

Grimoire's Slack and scheduled runs use the shared `grimoire` session on port
9223, and Grimoire always stays there. Attended direct chat uses the machine's
attended default, set per machine in `routing.attended_cdp_port` of the
setup-owned browser policy: Evo X1 sets 9222, so attended work there runs on the
separate `operator` browser with the operator's own Seller Central login; every
other machine keeps `grimoire` on 9223. Launch attended browser commands with
`node tools/browserctl/browserctl.mjs run -- <command>`; session resolution and
pinning are in `tools/browserctl/README.md`. Action rights come from the
capability matrix in `docs/rights/README.md`, not from the port. The T3 Code
in-app browser is explicit only and is never a silent fallback, especially for
login, upload, or download work.

CDP runners start or reuse the machine-policy profile automatically on the first
applicable task. Seller Central and FlatFilePro may use the exact-origin
authentication broker on ports 9222 and 9223. Human challenges still require an
explicit attended `browserctl restart` with a reason.

New downloads and generated files are tracked by exact path with `artifactctl`.
Successful runs become eligible after seven days, then a weekly verified job
moves eligible files into a 30-day local quarantine before exact-file purge.
Changed, unregistered, failed-run, manual, and unresolved files remain
preserved. The lifecycle never deletes remote FlatFilePro, pCloud, or Drive
data.

## Client Profiles

Shared operational client context lives in the private, Obsidian-synced agency vault, not GitHub. Each client has `Clients/{Name}/Amazon Ops.md`, containing one or more brand-marketplace profiles such as `Acme US` or `Example Brand DE`.

Amazon Agent reads those files directly through `AMAZON_AGENT_TEAM_VAULT` or `_local/team-vault-path.txt`; it does not maintain a second profile-data cache. See `docs/client-profiles.md` and `tools/client-profiles/`.

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

Dates belong in filenames, not folder names. The controlled workflow names, client-slug rules, and folder roles live in `docs/local-output-storage.md`.
