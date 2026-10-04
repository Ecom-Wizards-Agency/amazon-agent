# Google Drive Delivery

Google Drive is for artifacts a HUMAN opens: client deliverables, and internal files the team reviews. It is not an archive for generated exhaust. Everything else follows the installed local storage policy; without one, it stays in the generic `output/`, `downloads/`, and `evidence/` defaults in `docs/local-output-storage.md`.

Every client folder in the `Ecom Wizards` shared drive has exactly two zones, a matched pair:

```
Geteilte Ablagen/Ecom Wizards/01_Client Sheets/<Client>/
  <Client> - Shared/     CLIENT-VISIBLE. The client has commenter access on this folder.
  <Client> - Internal/   Internal. Flat, no workflow subfolders.
  <other folders>        Internal by default.
```

The client boundary (what may enter `<Client> - Shared/`, the internal default, and that agents do not route work into `- Internal/`) is part of the Operating Contract in `AGENTS.md`. `<Client> - Internal/` exists for files a human needs to open in Sheets or comment on.

What agents deliver to Drive:

| Artifact | Location |
|---|---|
| Keyword research workbook (as a Google Sheet) | `<Client> - Shared/<Keyword Research>/<Country>/` |
| Audit MASTER workbook (as a Google Sheet) + narrative Google Doc | `<Client> - Shared/<Audits>/` |
| Amazon offboarding handover Google Doc + five-tab evidence Google Sheet | Exact existing handover/offboarding folder inside `<Client> - Shared/`; never create one |
| Human-facing monthly reports | `<Client> - Shared/<Reports>/` |
| SB video briefing + Creative Reference Google Docs | `<Client> - Shared/<Video Briefings>/` (one file per batch and per product line, edited in place) |
| FlatFilePro upload CSVs | NOT in Drive. `output/{client}/catalog/` |
| Raw Seller Central listing exports (Category Listings Report) | NOT in Drive. Generic working path: `downloads/{client}/catalog/`; register under the run and apply the installed artifact lifecycle. |

Subfolder names inside `<Client> - Shared/` vary per client for historical reasons (`Keyword Research` in one, `02 Keyword Research` in another). Before saving, LIST the folder and reuse the existing one. Never create a spelling or numbering variant next to an existing folder, and never create a new top-level subfolder inside `<Client> - Shared/`. The delivery rows above are not a complete inventory of what the client sees. The rule for anything else in the folder: if you did not create it, leave it exactly as it is. Do not move, rename, reorganize, or flag it as misplaced. A client folder legitimately holds team-managed folders that no agent ever writes to, `Creative Assets` being one example, and the absence of a folder from the delivery rows says nothing about whether it belongs. If an artifact you generated does not fit a delivery row, follow the installed local policy or leave it in `output/` when none is installed.

Filename convention for everything delivered to Drive:

```
YYYY-MM-DD_<Client>_<Market>_<Artifact>_v<N>.<ext>
2026-07-29_Acme_DE-IT_Preview_v1.xlsx
```

Date first and ISO always, so folders sort chronologically. Keep the client name even though the folder already carries it, because the file has to stay identifiable after it is downloaded or forwarded. Omit `<Market>` only when the artifact genuinely spans all marketplaces. Do not reuse the older `<Client> <Market> - <Artifact> - DD.MM.YYYY` or trailing-date forms. `<Artifact>` comes from the controlled list in the team SOP; if nothing fits, add it there rather than inventing one here. A native Google Doc or Sheet carries the same name without the extension.

**Deliverables become native Google files, never `.docx` or `.xlsx`.** Documents become Google Docs and workbooks become Google Sheets. An Office file in Drive cannot be commented on the way a native one can, and "Open with Google Docs/Sheets" hands the client a detached copy. Renderers still produce Office files because python-docx and openpyxl carry the branded contract. Convert with `python3 tools/gdrive-deliver/deliver.py <file> "<drive folder>" --name "<delivery filename>" --artifact-run <run-id>`. The helper verifies the native destination, emits a non-secret receipt, and retains the local Office file for artifactctl. The staged uploaded Office copy is removed unless explicitly retained; the native destination is never deleted by artifactctl.

The destination can be a Drive folder path or a Drive folder id, and the script picks the route from it. One-time setup on a machine is `python3 tools/gdrive-deliver/setup_google.py`; without it, delivery still works and prints the browser steps instead. **the gdrive-deliver README in `company-ai-skills/lib/gdrive-deliver/` is the source of truth** for the routes, the size limits, the account check and what survives conversion (the implementation moved there on 12.08.2026; `tools/gdrive-deliver/` here holds forwarders so every documented command keeps working). Read it when delivery does something unexpected, not before every delivery.

We do not render PDFs anywhere. Whoever needs one downloads it from the Doc, which also covers Amazon case attachments.

**After first delivery the file belongs to a human.** There is no "upload a new version" path for a native Google file, and re-importing over one that has been commented on detaches the comments. Re-render and re-deliver freely before the client has seen it. After that, never re-render over it.

Changes after delivery are made **in the delivered file**, which preserves comments and version history. An agent may do that directly (`GOOGLEDOCS_REPLACE_ALL_TEXT` for unambiguous strings, `GOOGLEDOCS_UPDATE_DOCUMENT_SECTION_MARKDOWN` for a bounded range, `GOOGLESHEETS_VALUES_UPDATE` for a known range in a Sheet, after reading the current content), or in the browser. Two rules: read the live file first, because the operator may have edited it and a blind global replace hits every occurrence; and a delivered file is client-visible, so confirm with the operator before editing one. Anything beyond content edits (restyling, new KPI cards, changed tables or figures, a new tab) comes from the renderer and means a new document, not an edit.

## Client-facing brand precedence

**Client-facing brand precedence is strict.** For every Amazon document, workbook, deck, or report, use this order: an explicit approved client template first; otherwise the owning workflow's branded renderer and style configuration; otherwise the Ecom Wizards brand contract; generic document or spreadsheet defaults only when the operator explicitly asks for an unbranded deliverable. Generic Google Docs, Documents, Google Sheets, and Spreadsheets skills provide construction and QA mechanics only. They may not replace the owning workflow's logo or lockup, palette, typography, running header/footer, or workbook styling. "No cover" means `cover=False`: page one begins with the content while all content-page branding remains.

Brand compliance is a delivery gate. Before a client-visible upload, verify the expected lockup or logo, palette, fonts, running header/footer and page numbers where applicable, workbook title/header/section treatments, and the absence of a generic fallback theme. Render and visually inspect every document page and every populated workbook tab after native Google conversion. A file that fails this gate is not delivered.

> The **team vault `SOPs/google-drive-structure.md` is the source of truth** for Drive structure, the `- Internal/` decision queue, archiving, permissions, and onboarding or converting a client. This file carries only what an agent needs at the moment it writes a file. It deliberately does not restate the rest, because the previous duplicate copy drifted from the SOP within two days. If the two ever disagree, the SOP wins.
