# Native connected delivery

Use this supported route when an authorized Google connector can create/edit the native briefing but the repository builder is unavailable. Its absence alone does not block delivery. The builder remains supported wherever installed. This route changes the interface, not the briefing contract or its gates.

## Required capabilities

Read `google-workspace-deliverables`, `ecom-wizards-brand` and the video editor template. In a portable package, resolve those skills beside the video skill. Use the actual agency brand contract/tokens and approved logo assets; the product's brand rules govern the creative content, not the agency document identity. Do not create a cover or a separate Creative Reference. Missing required assets or unsupported formatting is a specific delivery blocker, not permission to use generic styling.

An approved native branded template can supply its existing logo/header and style. Copy it for a new briefing, never edit the source, replace all prior task/client content, and verify the final text against this assignment. Do not require a local logo file when the approved native template already supplies the asset. An existing canonical briefing is edited in place instead of copied.

Use a working dedicated Google connection, then the enabled Composio MCP when needed. Discover its current tools, schemas and connected account. A local Composio CLI, operator repository and signed-in browser are not prerequisites for remote MCP operations. Referenced Notion tasks/pages may be read for context without authorizing Notion writes.

## Delivery checks

For an explicitly formatting-only update, keep the existing Doc text verbatim and use its complete readback plus the approved source as the comparison baseline. Do not start new research or script writing, demand new content approval, or interpret a formatting request as permission to rewrite. Preserve prior readiness caveats and inspect every page after formatting; missing old receipts does not itself prevent an authorized layout correction.

1. Retain the complete checked source, assignment mode/cut count, portable validator output and fresh independent editor/claims review. Resolve readiness blockers before calling the briefing ready. Do not add alternate cuts to a commissioned production request.
2. Resolve the exact existing client `Video Briefings` folder and its parent ID. Confirm the connected account and delivery authorization. Never create a guessed client folder or write into a client Shared destination without exact authorization.
3. Use title `<Client> <Market> - <Product Line> SB Video Briefing` and native MIME type `application/vnd.google-apps.document`. Reuse the canonical Doc ID on updates; preserve comments, permissions, history and unrelated material. Read before editing and verify an uncertain write before retrying.
4. Write the complete briefing with native headings, actual tables, final copy and approved agency formatting. Every scripted card keeps its timing, visual direction and explicit audio/VO requirements. A Markdown creation action can seed content; its success does not establish layout or completion.
5. Re-read Drive metadata and the complete document, including all tables/tabs. Verify exact ID/title/MIME/parent and every source heading, paragraph and table-cell value against the checked source. Inspect structured content as needed to distinguish real tables/headings from plain text. Omitted content is a failure.
6. Export the same native Doc to PDF or inspect its native pages. Prefer the authenticated connector's export/download operation even if the browser is signed out. Inspect every page for brand identity, readable card tables, no clipping or split/blank-page defects, and editor completeness. Readback alone is not visual QA.
7. Save a delivery receipt with route, connected-account identity, canonical ID/URL, title/MIME/parent, source hash, mode/requested and actual cut counts, mechanical/reviewer results, full-content comparison and page-by-page visual-QA result. Stay `delivered_pending_visual_qa` while visual inspection is incomplete; state any other blocker precisely. Return the verified canonical link and readiness status.

Discover action schemas rather than copying arguments from another runtime. Useful action families include Drive metadata/folder lookup, Docs create/update/full readback and Drive PDF export/download. The repository builder verifies the same metadata, complete plaintext including tables/tabs and PDF export; this route must retain those checks.

If the available connector cannot satisfy a required step, return the checked source and exact remaining delivery handoff. Do not claim that the builder is required merely because the connector has not been tried, and do not bypass content, branding, account or approval requirements to avoid a real failure.
