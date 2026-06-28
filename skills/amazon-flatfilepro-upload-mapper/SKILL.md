---
name: amazon-flatfilepro-upload-mapper
description: Use when a prepared Amazon FlatFilePro or Flatfire Pro CSV must be uploaded, validated, matched by SKU, or mapped column-by-column in the logged-in Chrome FlatFilePro browser session. Trigger on requests like upload to FlatFilePro, use the Chrome extension, map FlatFilePro columns, match columns, validate this CSV in FlatFilePro, or leave it so the operator only has to click done.
---

# Amazon FlatFilePro Upload Mapper

## Core Rule

Use Chrome with the user's logged-in FlatFilePro session. This skill is for operating the FlatFilePro upload/mapping UI after a CSV already exists. If the CSV still needs to be created from labels or backend exports, use `amazon-flatfilepro-compliance` first.

Stop before the final action that applies catalog changes, such as `Done`, `Update`, `Submit`, `Apply`, or any force/update switch, unless the operator explicitly approves that exact final click in the current chat.

## Required Inputs

If needed information is missing, ask briefly:

```text
I need the CSV path and target FlatFilePro Seller & Marketplace, unless you already opened the right FlatFilePro upload screen.
```

Continue from the current FlatFilePro screen when the operator has already prepared the account, upload page, file, SKU matching, or mapping step.

## Local Memory

Before asking for repeated account or mapping details, check `_local/flatfilepro-upload-mapper/local-notes.md` if it exists. It may contain confidential Seller & Marketplace labels, preferred upload paths, and recurring column quirks. The `_local/` folder is ignored by Git; never copy its real account names, client brands, SKUs, ASINs, upload files, screenshots, support-case details, or other confidential values into tracked files.

## Workflow

1. Load and follow the Chrome control skill before operating Chrome.
2. Check the visible FlatFilePro `Seller & Marketplace` whenever possible.
3. If the wrong account or marketplace is selected, switch to the target Seller & Marketplace and verify the page updates.
4. Open FlatFilePro `Upload` only if not already on the upload flow.
5. Click `UPLOAD FILE` and select the prepared CSV if no file is already selected.
6. If file picker navigation is awkward, copying the CSV to Downloads is allowed as an optional convenience step.
7. In the matching step, use `SKU` as the default match basis.
8. Select the CSV's SKU column unless the operator already matched it.
9. Map remaining columns one by one.
10. Capture validation issues and stop at the final review/confirmation screen.

## Column Mapping

For each unmapped CSV column:

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

Read `references/upload-mapping-workflow.md` for the detailed UI workflow and `references/failure-handling.md` for skip/report behavior.
