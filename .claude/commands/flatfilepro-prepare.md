---
description: Prepare a narrow FlatFilePro upload file (.xlsx) from a verified connector export + evidence (SKU-keyed, full grid; file-only, upload stays manual)
argument-hint: "[client-market, e.g. acme-de; ASINs/SKUs and the fields to change]"
---

# FlatFilePro Prepare (upload .xlsx)

Build a narrow, upload-ready FlatFilePro **.xlsx** from a verified FlatFilePro export + source-of-truth evidence. Do not duplicate logic here. Route into the `amazon-flatfilepro` skill and its `scripts/prepare_flatfilepro_upload.py`.

**Scope.** Use the workbook route only for what the direct update cannot do: relationships and variations, clearing a value, price, offer and stock fields, brand and identifiers, new listings, an attended session without the FlatFilePro connector, and Grimoire or scheduled runs. Copy, backend terms, structured attributes and images on an existing listing go to `/flatfilepro-update`.

The user's target is: **$ARGUMENTS**

## Steps

1. **Confirm inputs. Ask first.** Collect in one question, skipping what `$ARGUMENTS`/the conversation already supplies: brand · marketplace · affected ASINs/SKUs · which fields change · the evidence for the new values (label/PDF for compliance, or the approved SEO copy for a listing refresh). Do not ask for an export path; step 3 fetches it. Never carry a prior client's values.

2. **Load the `prepare` mode** in `amazon-flatfilepro` as source of truth (field-mapping rules, SKU keying, audit-note format), and its `references/mcp-reads.md`.

3. **Fetch current values through the FlatFilePro connector** (attended only). Resolve the IDs with `node tools/amazon-operations/ffp-mcp.mjs binding`, run the connector export, and pass the download result on stdin to `ffp-mcp.mjs fetch-export --out-dir downloads/<client>/catalog/ --register-run <run>`; never repeat the download URL anywhere else. Then `resolve --asin`/`--sku` for every non-archived SKU (including `-1` contribution SKUs), `gaps --touch <fields>`, and `grid --out output/<client>/catalog/<name>.csv`. If the connector is unavailable, ask for a FlatFilePro XLSX export per market instead. A saved `get_listings` result is never the source.

3a. **Header matching.** The `--changes` `attribute` values must match the source headers **verbatim** or the script hard-exits (code 2). The connector grid uses FlatFilePro's export spelling: title = `item_name__1__value`; Item Highlights = `title_differentiation__1__value` (single ~125-char field, **not** bullets); bullets = `bullet_point__1__value`…`__5__value`; description = the grid's exact header. An XLSX export may use either spelling; copy whatever it has. The script normalises to canonical on write and prints the renames. Verify the finished file has no `__N__` header left.

4. **Scope note (SEO):** the skill's DEFAULT refuses to touch title/bullets/images/etc. For an SEO refresh you must **explicitly** put those copy fields in scope. Key on **`sku`**, never ASIN. Update **all** SKU contributions for the same ASIN, including `-1` frontend-controlling variants (same values on both rows). Size/variation tokens are matched per SKU by hand: author each SKU's own title/value in the changes CSV.

5. **Build.** Author the `sku,attribute,value` changes CSV, then:
   ```bash
   python3 skills/amazon-flatfilepro/scripts/prepare_flatfilepro_upload.py \
     --source <grid.csv or FFP export> --changes <changes.csv> --output <upload.xlsx> --fill-unchanged
   ```
   Exit 2 names the problem: a missing source header, a changed SKU with no source row, or a SKU the source repeats. Build **separate .xlsx files per marketplace** from each market's own export (enum spellings diverge, e.g. DE `Gramm` vs IT `Grammi`/`grammo`).

6. **Deliver**: the `upload.xlsx` + a per-SKU audit note (included/excluded SKUs, changed fields, manual-review flags). Name every excluded SKU: archived ones from `resolve`'s `excluded_archived`, any SKU missing from the source, and any SKU left out on purpose.

7. **Stop.** Uploading is a separate step. Hand off to `/flatfilepro-upload` or the operator. Never upload, save Seller Central changes, or submit cases as part of this command.
