# Claude Instructions

This project's source of truth for assistant behavior is `agent.md`.

At the start of a new chat in this project:
1. Read `agent.md`.
2. Follow the Amazon Agent routing, library search, connected-browser checkpoint, evidence, and stop-before-risk rules from `agent.md`.
3. Use the local visual MAG SOP archive only when screenshots/GIFs are needed. The operator's current local placeholder path is:
   `<your-pcloud>/Amazon Agent/MAG SOPs`
4. Use the repo-native Opportunity Explorer extraction scripts only when OEI/POE exports are needed:
   `tools/opportunity-explorer/extract-opportunity-explorer.js`
   `tools/opportunity-explorer/format-opportunity-explorer-export.mjs`
5. Use the `amazon-listing-capture` skill + `tools/listing-capture/extract-amazon-listing-copy.js` (connected browser) to capture live listing copy (title/bullets/link) for anchor + competitors into the listing-reference JSON; it feeds the keyword-workbook ASINs tab and replaces the legacy ZeroWork scrape.
6. Use the `amazon-campaign-builder` skill + `tools/amazon-campaign-builder/` (`/create-campaigns`) to build SP campaign bulk-upload files from a text brief — file-only output, paused by default; uploading or any AdLabs push stays a separate operator-confirmed action.

## Cross-Agent Handoff

When a task is likely to continue in Codex or another assistant, finish with a copy-ready handoff prompt and save it in the relevant client/project note. Do not make the operator translate between agents.

The handoff must include:
- objective and explicit non-goals
- source files and exact paths
- account, marketplace, ASINs, niche IDs, and date range
- what was already verified
- caveats, blockers, and risky actions to avoid
- the next exact action for the other agent

Saved protocol + templates: `<your-vault>/Context/codex-claude-handoff-protocol.md` and a per-client handoff template under your vault's `Projects/Clients/<client>/cross-agent-handoff-template.md`.

For keyword-workbook runs the handoff is auto-generated — run `tools/amazon-seo-keyword-workbook/build_keyword_workbook.py --config <cfg> --preflight` to emit a copy-ready Codex task for missing inputs (or a READY status). The builder is client-agnostic (copy `config.TEMPLATE.json` for a new client; see `NEW-CLIENT.md`). Claude's role: write the SEO content and run the build. Codex's role: gather the browser/POE + DataDive-UI inputs to the contract paths, then stop. See `tools/amazon-seo-keyword-workbook/WORKFLOW.md` and the `amazon-seo-keyword-workflow` skill.

For keyword-research workbook delivery, use Google Drive only. Do not copy final keyword-research workbooks to pCloud. Target folder pattern: `Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/Keyword Research/<Country>/` — one `Keyword Research` folder per client with a sub-folder per country (NOT a folder per run). If the client has only one country, the workbook goes directly in `…/<Client>/Keyword Research/` with no country sub-folder.

The pCloud path is user-specific. Team members should point their own setup to their own local pCloud-synced visual archive; do not commit the archive or personal sync folders to GitHub.

Do not duplicate large sections from `agent.md` here. Keep this file as a lightweight entrypoint.
