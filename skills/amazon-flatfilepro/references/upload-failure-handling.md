# Failure Handling

## Missing Inputs

If the `.xlsx` path, target account, or target marketplace is missing and the browser is not already prepared, ask only:

```text
I need the .xlsx path and target FlatFilePro Seller & Marketplace, unless you already opened the right FlatFilePro upload screen.
```

Before asking, check `_local/flatfilepro/local-notes.md` if it exists. Use it only as ignored local memory; do not quote confidential account names back into tracked files.

## Unmatched Columns

If searching the exact technical header does not produce a matching attribute:

- try the exact header once more
- try the core attribute fragment only if it is clearly the same field
- do not choose a similar but different field
- skip the column
- report it under `Skipped/unmatched columns`

Example: if `rtip_manufacturer_contact_information.0.value` does not appear as a selectable attribute, skip it and report it.

## Validation Issues

If FlatFilePro reports issues:

- capture SKU
- capture field
- capture message and error code
- do not force updates unless the operator explicitly approves the exact force action
- stop the current workflow before uploading or mapping another file unless the operator explicitly says to continue

Known issue:

- IT marketplace may reject `unit_count.0.type.value = gramm` as invalid for `Volume/peso dell’unita di vendita` with code `90004205`.
- Treat this as an upload-file enum problem, not a mapping problem. Regenerate the IT `.xlsx` using the target export enum such as `grams`, then upload/map again.

## Stale Preview Or Wrong Revision

If the selected filename is correct but a mapped preview value differs from the saved `.xlsx`:

- treat the preview as stale or the wrong import revision
- do not proceed to the final update
- reload the Imports page to clear staged mapping state
- upload the file again under a unique revision filename
- remap the fields
- compare every changed SKU-field value with the reopened `.xlsx`
- report ready only when all expected values match

FlatFilePro can retain stale preview state when another file is uploaded from an already mapped screen. Filename verification alone is not sufficient for a revised file.

## Risk Boundaries

Allowed after user asks for upload/mapping:

- open FlatFilePro in Chrome
- switch the visible Seller & Marketplace
- select/upload the `.xlsx` into the FlatFilePro upload flow
- choose SKU matching
- map attributes
- review preview/validation issues

Stop before:

- final update/apply/done/submit
- force update toggles
- any action that sends the changes to Amazon or makes catalog changes live
