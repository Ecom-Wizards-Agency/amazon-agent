---
description: Upload/map an already-prepared FlatFilePro CSV in the logged-in Chrome session (SKU-matched, column-by-column; stop before final apply)
argument-hint: "[CSV path + target Seller & Marketplace, or 'continue from the open upload screen']"
---

# FlatFilePro Upload Mapper

Operate the FlatFilePro upload/mapping UI to push an **already-prepared** CSV. Do not duplicate logic here — route into the `amazon-flatfilepro-upload-mapper` skill.

The user's target is: **$ARGUMENTS**

## Steps

1. **Precondition — the CSV must already exist.** If it still needs building from an export/labels/SEO copy, use `/flatfilepro-prepare` (the `amazon-flatfilepro-compliance` skill) first.

2. **Load the Chrome control skill first**, then the `amazon-flatfilepro-upload-mapper` skill as source of truth. Check `_local/flatfilepro-upload-mapper/local-notes.md` for the operator's recurring Seller & Marketplace labels / mapping quirks before asking.

3. **Confirm inputs — ask briefly** only for what's missing: the CSV path and the target FlatFilePro **Seller & Marketplace** (or continue from the screen the operator already opened).

4. **Upload + map** — `UPLOAD FILE`, choose **SKU** as the match basis, then map each CSV column to its Amazon attribute via `Search file columns` → `Search attributes` → `MAP ATTRIBUTES`. Match on the **technical header in parentheses** (e.g. `title_differentiation.0.value`), not the localized label. Skip blank helper columns; retry a transiently-hidden column by searching its family before marking it skipped.

5. **Review the preview**, then **STOP** before the final `Done / Update / Submit / Apply / force` click — that catalog-applying action requires the operator's explicit approval of that exact click in the current chat.
