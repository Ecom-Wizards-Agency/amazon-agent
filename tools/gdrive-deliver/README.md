# gdrive-deliver

Turns a rendered Office file into a **native Google file** in a Drive folder.

```
.docx  ->  Google Doc
.xlsx  ->  Google Sheet
```

Deliverables ship as native Google files, not as `.docx` or `.xlsx`. An Office file sitting in
Drive cannot be commented on the way a native one can, and "Open with Google Docs/Sheets" only
ever makes the reader a detached copy. The renderers still produce Office files because
python-docx and openpyxl are what give us the branded contract in
`tools/amazon-ad-audit/BRANDING.md`. Those files are now intermediates: converted on delivery
and then deleted.

## Setup, once per machine

```bash
python3 tools/gdrive-deliver/setup_google.py
```

Delivery touches three separate Composio connections, each its own OAuth grant: `googledrive`
to deliver, `googledocs` and `googlesheets` to edit a delivered file in place afterwards. The
script links whichever are missing, one browser round per toolkit, skips the ones already
connected, and verifies the result. Sign in with the same Google account every time, and make
it the account that can reach the destination folders.

`--check` verifies without linking anything. It also flags half-finished links left behind by
an interrupted OAuth round, which are harmless but make `composio connections list` ambiguous.

Nothing here assumes a shared drive or a Workspace account. A personal Google account with
plain My Drive works the same way.

## Whose Google account this acts as

The short answer: **it cannot act as somebody else's.** When you deliver into a Drive for
Desktop mount, the script reads the account that owns that mount straight off the path (Drive
names it `GoogleDrive-<email>`), asks Composio which account it is linked as, and refuses to
deliver if the two differ:

```
[deliver] Refusing to deliver. This folder is in victor@example.com's Drive, but
Composio on this machine is linked as danica@example.com.
```

That check exists because Composio keeps connections **server-side, under the API key in
`~/.composio/user_data.json`**. Each person logging in with their own Composio account gets
their own connections, which is the normal case. But an API key copied between machines, or
put in a shared password vault as a company credential, would silently make every machine
deliver as whoever linked Google first. Do not share the key. The check is what makes that a
loud failure instead of a quiet one.

The browser path has no such failure mode at all: it uses the Google session the person is
signed into, so it is always their own account.

## Two ways in, picked from the destination

**A folder path** means the Drive for Desktop mount. The bytes are copied into the folder and
converted from there. No size limit, and the file appears in a folder the operator can already
see. This is the route to use on a machine that has the desktop client.

**A folder id or a Drive URL** needs no mount at all. The file is uploaded through the API and
converted. Capped at 5 MB by the upload tool, which covers every deliverable we render (the
largest so far is 0.7 MB) but not an arbitrary file. This is the route for a machine without
Drive for Desktop. Get the id from the folder's URL:
`https://drive.google.com/drive/folders/<this part>`. Passing the whole URL works too.

Composio's resumable upload, which would lift the 5 MB cap, returns a 400 on every chunk at
any chunk size (tested 02.08.2026). If that is fixed, the id route can use it and the cap goes
away.

## Use

```bash
# into a mounted folder
python3 tools/gdrive-deliver/deliver.py \
  output/acme/reporting/Acme_US_Sales_Audit_BRANDED.docx \
  "$EW_DRIVE/01_Client Sheets/Acme/Acme - Shared/Audits" \
  --name "2026-08-02_Acme_US_Audit_v1"

# same thing with no desktop client, by folder id
python3 tools/gdrive-deliver/deliver.py \
  output/acme/seo/Acme_US_Keyword_Research.xlsx \
  1AbCdEfGhIjKlMnOpQrStUvWxYz012345 \
  --name "2026-08-02_Acme_US_Keyword_Research_v1"
```

`--name` should be the delivery filename from the AGENTS.md convention, without an
extension. Omit it and the local stem is used, which is almost never what you want for a
client-facing file.

Flags: `--keep-local` keeps the local Office file, `--keep-upload` keeps the uploaded Office
file next to the converted one. Neither is on by default. `--keep-docx` still works as an
alias for `--keep-upload`.

## What it does

1. Gets the file into Drive, by whichever of the two routes the destination selects. On the
   mount route it waits for Drive to stamp a file id on the staged file, read from the
   `com.google.drivefs.item-id#S` extended attribute rather than searched for by name, which
   is exact and also proves the upload finished. On the id route it checks the destination is
   a real folder first, because an invalid id makes the upload land silently in the Drive root.
2. Copies that file to `mimeType: application/vnd.google-apps.document` or
   `application/vnd.google-apps.spreadsheet`. Drive runs the same importer as
   `File > Save as Google Docs/Sheets` in the UI.
3. Verifies the result really is that native type.
4. Bins the uploaded Office file and deletes the local one. Nothing is deleted until step 3
   passes, so a failed delivery leaves both copies where they are.

Without a linked Google account, the mount route still does step 1 and then prints a direct
link plus the browser steps, so the delivery degrades instead of breaking. The id route needs
the connection by definition.

## What survives conversion

**Documents**, verified 02.08.2026 on a full audit (18 pages, cover, 9 tables, 6 figures) and
an SB video briefing: full-bleed cover, running header lockup and label, three-zone footer with
live `page X of Y` (the `PAGE`/`NUMPAGES` fields import as real Docs page numbers), Inter, KPI
cards, dark-ink table headers with zebra rows, accent callouts, and every figure.

The older claim that conversion "breaks the cover, the KPI cards and the font" was tested
and is wrong. It came from an earlier renderer.

**Workbooks**, verified 02.08.2026 on a 17-tab audit MASTER and a 14-tab keyword workbook, by
converting and then exporting back to `.xlsx`: every tab, tab names including `①` and `·`,
freeze panes, merged cells, autofilters, number formats, cell fills, and live formulas.
Sheets pads each tab out to its default 1000-row grid, which is cosmetic.

Not yet tested, because neither workbook we deliver contains them: charts, embedded images,
pivot tables, conditional formatting, data validation. Test before relying on any of those
surviving.

## Re-delivery

A native Google file has no "upload a new version" path in the Drive UI, and re-importing over
one that has been commented on would detach those comments. So the rule is ownership, not
tooling: **the agent owns the file up to first delivery, a human owns it after.** Re-render
and re-deliver freely before the client has seen it. Once it is delivered, edit it in place,
which is what `googledocs` and `googlesheets` are linked for.
