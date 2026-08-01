# gdrive-deliver

Turns a rendered `.docx` into a native **Google Doc** in a client's Drive folder.

Deliverables ship as Google Docs, not as `.docx` files. A `.docx` sitting in Drive cannot
be commented on the way a Doc can, and "Open with Google Docs" only ever makes the client a
detached copy. The renderer still produces `.docx` because python-docx is what gives us the
branded contract in `tools/amazon-ad-audit/BRANDING.md`. That file is now an intermediate:
it gets converted on delivery and then deleted.

## Setup, once per machine

```bash
composio link googledrive
```

Sign in as the account that owns the `Ecom Wizards` shared drive. Until that connection
exists the script stops after staging the `.docx` and tells you what to run, so a missing
connection degrades to the old behaviour instead of losing the file.

## Use

```bash
python3 tools/gdrive-deliver/deliver_doc.py \
  output/acme/reporting/Acme_US_Sales_Audit_BRANDED.docx \
  "$EW_DRIVE/01_Client Sheets/Acme/Acme - Shared/Audits" \
  --name "2026-08-02_Acme_US_Audit_v1"
```

`--name` should be the delivery filename from the AGENTS.md convention, without an
extension. Omit it and the `.docx` stem is used, which is almost never what you want for a
client-facing file.

Flags: `--keep-local` keeps the local `.docx`, `--keep-docx` keeps the uploaded `.docx`
next to the Doc. Neither is on by default.

## What it does

1. Copies the `.docx` onto the Drive desktop mount. The mount is the only workable path for
   a multi-megabyte file: the Drive MCP takes content inline as base64, so a 1 MB file is
   roughly 1.5M tokens and the call fails.
2. Waits for Drive to stamp a file id on the staged file. The id is read from the
   `com.google.drivefs.item-id#S` extended attribute rather than searched for by name, which
   is exact and also proves the upload finished.
3. Copies that file to `mimeType: application/vnd.google-apps.document`. Drive runs the same
   importer as "File > Save as Google Docs" in the Docs UI.
4. Verifies the result really is a native Doc.
5. Bins the uploaded `.docx` and deletes the local one. Nothing is deleted until step 4
   passes.

## What survives conversion

Verified 02.08.2026 on a full audit (18 pages, cover, 9 tables, 6 figures) and an SB video
briefing: full-bleed cover, running header lockup and label, three-zone footer with live
`page X of Y` (the `PAGE`/`NUMPAGES` fields import as real Docs page numbers), Inter, KPI
cards, dark-ink table headers with zebra rows, accent callouts, and every figure.

The older claim that conversion "breaks the cover, the KPI cards and the font" was tested
and is wrong. It came from an earlier renderer.

## Re-delivery

A native Doc has no "upload a new version" path in the Drive UI, and re-importing over a Doc
that has been commented on would detach those comments. So the rule is ownership, not
tooling: **the agent owns the Doc up to first delivery, a human owns it after.** Re-render
and re-deliver freely before the client has seen it. Once it is delivered, edit the Doc.
