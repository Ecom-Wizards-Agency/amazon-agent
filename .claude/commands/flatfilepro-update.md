---
description: Update existing Amazon listings directly through the FlatFilePro connector (copy, attributes, MAIN/PT images; live read before and after; stop before each write until the exact batch is approved)
argument-hint: "[client-market, e.g. acme-de; SKUs and the fields or image slots to change]"
---

# FlatFilePro Direct Update

Change existing listings on Amazon through the FlatFilePro connector's `flatfilepro_update_listing_on_amazon`, one SKU per write. Do not duplicate logic here. Route into the `direct-update` mode of the `amazon-flatfilepro` skill (`references/direct-update-mode.md`) and `tools/amazon-operations/ffp-mcp-update.mjs`.

The user's target is: **$ARGUMENTS**

## Steps

1. **Check the route.** Attended only, with the FlatFilePro connector loaded. Relationships and variations, clearing a value, price/offer/stock fields, brand and identifiers, new listings, a missing connector, and Grimoire or scheduled runs go to `/flatfilepro-prepare` and `/flatfilepro-upload` instead.

2. **Confirm inputs. Ask first.** Collect in one question, skipping what `$ARGUMENTS`/the conversation already supplies: brand · marketplace · SKUs · which fields or image slots change · the evidence for the new values (approved SEO copy, label/PDF, or the finished image files). Never carry a prior client's values.

3. **Load the `direct-update` mode** as source of truth, plus `references/mcp-reads.md`; for images also `references/attended-images-mode.md` (intake and hosting).

4. **Binding, base and live before-read.** Resolve the IDs with `node tools/amazon-operations/ffp-mcp.mjs binding`. Fetch the verified export when carried content needs a base (or a saved `get_listings` copy when the export fails). Save `flatfilepro_get_listings_item_from_amazon` for every SKU; over 10 SKUs, hand the reads to read-only helper agents in chunks of up to 10. Save `flatfilepro_get_product_type_fields` per product type when the mode asks for it.

5. **Build.** Author the `sku,attribute,value` changes CSV in canonical `attr.N.key` spelling (`bullet_point.2.value`; not the `/flatfilepro-prepare` CSV's `__N__` headers), or use `intake-receipt-images.json` for images, then run `ffp-mcp-update.mjs build ... --out output/<client>/catalog/ffp-updates/<batch>/`. Check `items` against the SKUs requested.

6. **Checks.** Copy passes the `amazon-seo` claims gate. Every new MAIN image gets the G1881 main-image checks; a failed check stops the MAIN change.

7. **Stop for approval.** Show `review.md` and the `batch_sha256`. Write nothing until the operator approves that exact batch in the current chat (MAIN also needs `approve --main-review FILE`). Then run `approve`. An approval expires after 12 hours; a batch approved in an earlier session needs the operator's fresh approval in this chat, then `approve` again.

8. **Submit, status, verify.** For each SKU, save a fresh live read right before the write (over 10 SKUs, read-only helpers save each chunk's reads right before the main session submits that chunk), run `next --live FILE`, call the update tool with exactly its arguments and `record` at once; a timeout is recorded with `--no-response`. `stale_base` means the listing changed since the build: close the item (void) and build a new batch. Never resubmit. Release the rest only after the first SKU verifies. Record status after `pollAfterSeconds`, save a live after-read and run `verify`; for images run `image_intake.py compare` once per verify file, then `verify --pixels`. Each verify state's next action is in the mode's step 10.

9. **Report.** Per SKU: verify state, new Amazon issues, and anything still open. Only `verified` is done; `landed_status_pending` is "landed, status pending". An item the tools cannot confirm (an `UNKNOWN` write whose live read matches, or an image the pixel check cannot tell from the before image) is closed with `close --landed` only after the operator confirms it landed; that releases the rest of the batch. `ffp-mcp-update.mjs pending --root output/<client>/catalog/ffp-updates` lists open items for a later session; an approved but unsubmitted item blocks overlapping batches until it is submitted or closed as void.
