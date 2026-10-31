# Upload And Map Mode

Mode browser: CDP (logged-in FlatFilePro session; hidden native file input, MUI autocomplete mapping; stop before Update Listings).

**Scope.** The workbook route is for what the direct update cannot do: relationships and variations, clearing a value, price, offer and stock fields, brand and identifiers, new listings, an attended session without the FlatFilePro connector, and Grimoire or scheduled runs.
Copy, backend terms, structured attributes and MAIN or PT images on an existing
listing go through `references/direct-update-mode.md` instead.

## Core Rule

Use the machine's attended default browser with its logged-in FlatFilePro session, per the Browser Standard in `AGENTS.md`. This mode operates the FlatFilePro upload/mapping UI after the upload file already exists. **FlatFilePro expects `.xlsx`** (operator, 2026-07-26); if you are handed a `.csv`, convert it to `.xlsx` before uploading rather than uploading the CSV. If the file still needs to be created from labels or backend exports, use the `prepare` mode first.

Use managed Chrome CDP on the machine's attended default session (`operator` on 9222 on Evo X1, `grimoire` on 9223 elsewhere), launched with `node tools/browserctl/browserctl.mjs run -- <command>`; Grimoire-side runs keep `--session grimoire`. The team FlatFilePro login is brokered on both ports. Do not switch this workflow to the
T3 Code in-app browser: that surface does not carry the managed login broker or
the supported `DOM.setFileInputFiles` upload path.

Stop before the final action that applies catalog changes, such as `Done`, `Update`, `Submit`, `Apply`, or any force/update switch, unless the operator explicitly approves that exact final click in the current chat.

**The hard stop is the preview screen headed "Make your changes and click submit below."** Leave it visible with the mapped chips and preview grid loaded, and do NOT click **Update Listings**. That button is not a confirmation step: it posts the bulk update and Amazon begins processing the catalog change. Never toggle the small force switch beside it either, which relabels the button **Force Update**. Verified 31.07.2026.

Mechanics worth knowing before driving it: the file chooser is a normal hidden `<input type="file">` behind a styled label, so a programmatic attach works and no OS dialog appears. **The upload starts immediately on the change event**, so verify the exact path before attaching, not after. Column mapping uses Material UI autocomplete fields (not drag-and-drop, not native `<select>`), driven by typing, arrow keys, and Enter. No step requires a trusted user gesture. Budget roughly 15-40 interactions per run, or 8-15 when `Automap` handles the technical headers.

## Required Inputs

If needed information is missing, ask briefly:

```text
I need the .xlsx path and target FlatFilePro Seller & Marketplace, unless you already opened the right FlatFilePro upload screen.
```

Continue from the current FlatFilePro screen when the operator has already prepared the account, upload page, file, SKU matching, or mapping step.

## Local Memory

Before asking for repeated account or mapping details, check `_local/flatfilepro/local-notes.md` if it exists. It may contain confidential Seller & Marketplace labels, preferred upload paths, and recurring column quirks. The `_local/` folder is ignored by Git; never copy its real account names, client brands, SKUs, ASINs, upload files, screenshots, support-case details, or other confidential values into tracked files.

## Workflow

1. Resolve the machine's attended default with `browserctl run -- …` before imports; Grimoire keeps `--session grimoire`. Use a task-owned tab with its exclusive context claim, plus the shared session lock when the session is `grimoire` on 9223; verify the FlatFilePro seller and marketplace before acting.
2. Start an `artifactctl` run for this attended workflow before creating,
   copying, or downloading a local file.
3. Check the visible FlatFilePro `Seller & Marketplace` whenever possible.
4. If the wrong account or marketplace is selected, switch to the target Seller & Marketplace and verify the page updates.
5. When the IDs were resolved with `ffp-mcp.mjs binding` (`references/mcp-reads.md`), read the selected account's seller and marketplace IDs from the app (`tools/amazon-operations/flatfilepro-account.mjs` proves them) and check both equal the binding's `seller_id` and `marketplace_id`. A mismatch stops the run before `UPLOAD FILE`.
6. Open FlatFilePro `Upload` only if not already on the upload flow.
7. Click `UPLOAD FILE` and select the prepared `.xlsx` if no file is already selected.
8. If file picker navigation is awkward, copying the `.xlsx` to Downloads is allowed as an optional convenience step. Register that new exact copy as `reproducible`; do not adopt the pre-existing source file.
9. Register any export downloaded from the exact `https://app.flatfile.pro` origin as `source-backed` with that origin. Files supplied manually by the operator remain `preserve`.
10. In the matching step, use `SKU` as the default match basis.
11. Select the file's SKU column unless the operator already matched it.
12. Map remaining columns one by one.
13. Run the mandatory pre-handoff verification below.
14. Capture validation issues and stop at the final review/confirmation screen.
15. Complete the artifact run as `success` only when the mapping run itself completed. Use `blocked` or `failed` otherwise. The handoff lists registered paths, dispositions, and the seven-day eligibility date.

## Mandatory Pre-Handoff Verification

Do not report an import as ready based only on the uploaded filename or the presence of mapped columns.

For every upload:

1. Record the exact selected server filename and upload identifier shown by FlatFilePro.
2. Confirm the expected row count and match basis.
3. Confirm every intended column appears in the mapped-column list.
4. Inspect the mapped destination values in the preview. Do not confuse FlatFilePro's existing `Title` column with the newly mapped `item_name.0.value` column.
5. When the file changes existing values, compare every changed SKU and field against the final saved `.xlsx`. Scroll or paginate until each changed row is rendered.
6. Report the number of changed SKU-field values checked and matched, such as `5/5 title changes matched`.

If the `.xlsx` was created or revised in the current run:

- reopen the final saved `.xlsx` and verify the changed cells before uploading
- use a new, unique filename for each revision
- when replacing an already staged import, reload the Imports page before uploading the revision

If any staged preview value differs from the saved `.xlsx`, fail closed. Do not report the file as ready. Reload the Imports page, upload a uniquely named revision, remap it, and repeat the preview comparison.

The public Amazon detail page is not a pre-submit validation source. It keeps showing the existing catalog contribution until the operator completes the final update and Amazon processes it. Live-page verification is a separate post-submit check.

Optional advisory check after an approved submit: `ffp-mcp.mjs rows` on the changed SKUs, from a new connector read, shows whether FlatFilePro's saved copy now carries the submitted values. It never counts as completion. Completion still needs the Activity run result and the Amazon-side source (detail page, listing issue or Category Listings Report).

## Column Mapping

For each unmapped column:

1. Select the technical header from `Search file columns`.
2. Copy or type the exact technical header into `Search attributes`.
3. Choose the suggestion whose visible label contains the same technical header in parentheses.
4. Click `MAP ATTRIBUTES`.
5. Confirm the preview table still shows the expected SKUs and values.

FlatFilePro may show localized labels, such as `Sicherheitswarnung (safety_warning.0.value)`. The technical header is the stable match target.

Skip a field when no valid attribute match appears after searching the exact technical header. Do not force a nearby-looking match. Record skipped fields in the final handoff.

Known example: `rtip_manufacturer_contact_information.0.value` may fail to match in FlatFilePro. If it cannot be mapped, skip it and report it.

## Handoff Report

When finished, tell the operator:

- selected Seller & Marketplace
- file uploaded or already selected
- match basis used or already completed
- mapped columns
- skipped or unmatched columns
- visible validation issues
- final screen/status and whether it is ready for the operator's final click

Keep the report concise.

## References

Read `references/upload-mapping-workflow.md` for the detailed UI workflow and `references/upload-failure-handling.md` for skip/report behavior.
