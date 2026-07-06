# Parentage / Variation Flat-File Playbook

Verified end-to-end on a live US account 2026-07-04 (two SIZE families created from
standalone ASINs; v1 failed, v2 succeeded — the rules below encode why). Applies to
creating a new variation family, adding SKUs to a family, or any targeted flat-file
edit with the modern (UMP) product spreadsheet.

## Rule 1 — Use a clean blank template, never an edited Category Listings Report

Operator rule (from experience): the CLR echoes every live listing value back, and
Amazon re-validates the ENTIRE submitted row against *today's* schema — values that
were legal when first listed fail now (seen live: legacy `Gram` Unit Count Type →
error 90004205; Item Highlights at/over the 125-char cap → error 90225). Even with
"Edit (Partial Update)", every non-blank cell is submitted and validated.

- Upload base: a fresh **blank template**.
- CLR: **data source only** (current values, product type, existing parentage, SKUs)
  — never the file you upload.

Blank template download (Seller Central):

1. Catalog → Add Products via Upload → **Download Blank Template**.
2. Choose **"List products that are not currently in Amazon's catalog"**.
3. **Single-country sheet only** — deselect other marketplaces. Multi-country
   templates cause problems (operator rule).
4. Type/select the current **browse node** for the product type.

The product type in the template must match the children's existing product type —
read it from the CLR (`product_type#1.value`) before generating.

## Rule 2 — Know the modern template anatomy before touching it

Everything is declared in cell A1 (the `settings=` string): `labelRow`, 
`attributeRow`, `dataRow`, `flavor`, marketplace, product type (`ptds`, base64).
Observed: label row 4, attribute row 5; **dataRow differs by flavor** (CLR
`inventory-report-ump` = 7; blank `full-seller` = 8) — always read it, never assume.

Blank `full-seller` templates additionally contain, above the data area:
- an Amazon **example row** (e.g. row 6) and
- a **"prefilled attributes … do not delete this row" notice** (e.g. row 7) —
  leave both untouched;
- the first data row may be **prefilled from the seller's Preference Profile**
  (brand, manufacturer, target audience, etc.) — keep those values on rows that
  create new listings (parents).

Column positions differ between template downloads (even same product type).
**Map columns by attribute name from the attribute row — never by index** carried
over from another file.

Legacy → modern column mapping (Amazon's help still describes the legacy names):

| Legacy | Modern (UMP) |
| --- | --- |
| `parentage` = parent/child | `Parentage Level` (`parentage_level…value`) = Parent/Child |
| `parent_sku` | `Parent SKU` (`child_parent_sku_relationship…parent_sku`) |
| `relationship_type` = variation | **no column** — implied, defaults to variation |
| `variation_theme` | `Variation Theme Name` (`variation_theme#1.name`) |
| `update_delete` | `Listing Action` (`::record_action`): "Create or Replace (Full Update)" / "Edit (Partial Update)" / "Delete" |

## Rule 3 — Row construction

**Parent row (new listing → Full Update):**
- Unique SKU ≤40 alphanumeric chars; convention: common base + `-PARENT`
  (confirm client naming preference).
- `Listing Action` = Create or Replace (Full Update); `Parentage Level` = Parent;
  `Parent SKU` blank; `Variation Theme Name` = chosen theme (from the Valid Values
  tab for that product type; deprecated themes are labeled — do not use).
- Title must be generic — no size/color/variation terms.
- Fill **all required attributes** — Amazon's "leave non-required blank" is
  correct, but requireds are stricter than the doc implies (SKIN_MOISTURIZER
  required Product Description, Bullet Point, "Are batteries required?" on the
  parent). Check the Data Definitions sheet (Required/Conditionally Required) and
  expect the processing report to catch stragglers.
- Copy/description reused from a child must be de-variationed (strip size/count
  sentences); size-specific bullets stay off the parent.
- NO size/variation attribute value, no condition, no price/quantity, no
  fulfillment data, no package dimensions on the parent.

**Child rows (existing listings → Partial Update, MINIMAL):**
- Exactly these fields, nothing else echoed: SKU, Product Type, `Listing Action` =
  Edit (Partial Update), `Parentage Level` = Child, `Parent SKU` = parent's SKU,
  `Variation Theme Name` = same theme, and the **variation attribute value**
  (e.g. `size…value`) — which must be distinct across the family's children.
- Echoing anything more re-submits stale live values into current-schema
  validation (the Rule-1 trap).

## Rule 4 — Builder gotchas (scripted edits)

- openpyxl: `ws.cell(row, col, value=None)` **silently skips** assignment — it does
  not clear the cell. Use direct `ws.cell(...).value = v` so None actually clears;
  otherwise leftover data bleeds into overwritten rows.
- Load/save `.xlsm` with `keep_vba=True`; keep the native format.
- Never modify rows above the data row (settings/labels/attributes/example/notice).
- QA before handoff: re-read the saved file and assert (a) parents contain ONLY the
  intended fields, (b) children have exactly the minimal field set, (c) variation
  values distinct per family, (d) excluded SKUs absent, (e) no leftover rows beyond
  the intended block, (f) brand identical across parent + children.

## Rule 5 — Upload and read the result correctly

- Upload: Catalog → Add Products via Upload → Upload your spreadsheet (operator
  action — stop-before-risk). Processing 15–60 min.
- The feedback file's **Feed Processing Summary** sheet is the verdict. Read the
  per-SKU error table, not just the counts.
- **"Successful with other errors" is not failure**: the submitted change (e.g.
  parentage) applied, but Amazon flagged pre-existing live-listing compliance
  issues on those SKUs (seen: 90225 Item Highlight >125 chars on children whose
  rows didn't even contain that field). Log these as separate listing-fix tasks.
- Error 8007 on a parent ("issues with your parent SKU … before you can work on
  any child SKUs") → open Manage All Inventory, look for a Fix-listing prompt on
  the parent, resolve attributes there or via a follow-up minimal file.
- Amazon's char counting can be stricter than `len()` (values measured 123–125
  chars were flagged >125) — target ~120 for capped fields like Item Highlight.
- Verify the family per the MAG Parentage Creation SOP: Manage All Inventory
  (Status=All, Fulfilled by=All) under the parent SKU, Variation Wizard, and the
  live detail page.

## KPI baseline (recommended before merging existing ASINs)

Merging pools reviews and can shift ranks/traffic. Before upload, capture per
ASIN: Business Report by Child ASIN (30d), SQP weekly (8w), review count + star
average + BSR + price snapshots, ads 30d export, and a DataDive rank baseline.
Any ASIN intentionally left out of the family doubles as a control. Compare
4 weeks pre vs post, excluding promo-contaminated weeks (e.g. Prime Day).
