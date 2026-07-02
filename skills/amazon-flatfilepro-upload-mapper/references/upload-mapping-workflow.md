# FlatFilePro Upload Mapping Workflow

## Chrome Setup

- Use the Chrome plugin/browser-control surface because FlatFilePro depends on the logged-in Chrome session.
- If Chrome is not connected or FlatFilePro is logged out, ask the operator to open/login and tell you when ready.
- Do not inspect passwords, cookies, local storage, tokens, or session data.

## Account And Marketplace

At the start, check the visible `Seller & Marketplace` value if it is available. If the operator says the account is already correct, you may continue from the current screen but still mention the visible account in the handoff.

If the user has not repeated a known account or marketplace detail, check `_local/flatfilepro-upload-mapper/local-notes.md` first. Treat that file as local-only confidential memory and never copy its real account values into tracked docs.

If switching is needed:

1. Open the `Seller & Marketplace` selector.
2. Select the requested account/country.
3. Wait until the visible selector and URL/page state update.
4. Continue only after the selected value matches the target.

## Upload Flow

1. Navigate to FlatFilePro `Upload`.
2. Click `UPLOAD FILE`.
3. Select the prepared CSV.
4. If selecting the local path through Chrome's picker is slow, optionally copy the CSV to Downloads first, then select it from the top of Downloads.
5. Choose `SKU` matching unless the user asked for a different basis.
6. Select the CSV column that contains the SKU.

If the operator already selected the file or matched SKU, do not restart. Continue from the current upload/mapping screen.

## Mapping Loop

Repeat for all remaining relevant file columns:

1. In `Search file columns`, choose the CSV header.
2. Copy the exact technical header, for example `safety_warning.2.value`.
3. In `Search attributes`, paste the technical header.
4. Select the matching option. Prefer an option where the localized label is followed by the same technical header in parentheses.
5. Click `MAP ATTRIBUTES`.
6. Verify the mapped column appears in the preview table.

Do not map random helper columns, validation-note columns, comments, or any field that is not part of the upload CSV.

Map only columns that need to be transmitted. If the CSV contains intentionally empty helper/string columns, skip them instead of mapping blank values into Amazon. For nutrition work, string fields should usually be skipped unless the compliance skill intentionally filled them for a case.

FlatFilePro can briefly fail to show a file column even when it exists in the CSV. If exact search returns no file-column option, search the core family such as `safety` or `unit_count`, then choose the exact technical header from the list. Do not mark the field skipped until this retry has been attempted.

## Preview Checks

Before stopping, review:

- expected SKU rows are present
- ASINs/product titles look like the intended products
- product type looks plausible
- values appear under the intended mapped columns
- FlatFilePro does not show unexpected blocking validation errors

If validation issues are visible, capture exact field, SKU, message, and code when possible.

If a validation issue appears on the final preview, stop on that file. Do not continue to a second upload file until the issue is reviewed or the user explicitly asks to continue anyway.

Known example:

- Italy can reject `unit_count.0.type.value = gramm` with code `90004205` for `Volume/peso dell’unita di vendita`. The corrected IT value should follow the Italy export enum, for example `grams`.

## Final Stop

Stop before any final change-applying action. Leave the screen ready for the operator's final review/click and summarize what remains.
