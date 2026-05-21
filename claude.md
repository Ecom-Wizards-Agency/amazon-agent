# Claude Instructions

This project's source of truth for assistant behavior is `agent.md`.

At the start of a new chat in this project:
1. Read `agent.md`.
2. Follow the Amazon Agent routing, library search, browser checkpoint, evidence, and stop-before-risk rules from `agent.md`.
3. Use the local visual MAG SOP archive only when screenshots/GIFs are needed. Victor's current local placeholder path is:
   `/Users/victoruhl/Documents/pCloud/Amazon Agent/MAG SOPs`
4. Use the repo-native Opportunity Explorer extraction scripts only when OEI/POE exports are needed:
   `tools/opportunity-explorer/extract-opportunity-explorer.js`
   `tools/opportunity-explorer/format-opportunity-explorer-export.mjs`

The pCloud path is user-specific. Team members should point their own setup to their own local pCloud-synced visual archive; do not commit the archive or personal sync folders to GitHub.

Do not duplicate large sections from `agent.md` here. Keep this file as a lightweight entrypoint.
