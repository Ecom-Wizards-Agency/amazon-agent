# Attended Images Mode

Mode browser: Mixed (connector reads and writes plus local intake and pixel check need no browser; the workbook fallback uses the CDP item-detail read, FlatFilePro upload and Activity readback).

Use this mode when an operator in an attended chat supplies finished image files
for named listings, including a new MAIN image. It replaces per-run survey,
inspection and verify scripts with one route. Grimoire and Slack requests keep the
`secondary-images` mode, which never touches MAIN.

Rights rows: `listing.images.attended` and `flatfilepro.mcp_update` in
`docs/rights/README.md`. The direct write is `references/direct-update-mode.md`, which
refuses every step but `pending` when `WIZARDS_AI_MODE` is set. In the workbook
fallback, the `attended_gallery` policy in `tools/amazon-operations/operations.py` refuses to
prepare or execute when `WIZARDS_AI_MODE` is set (`attended_only`), and the
FlatFilePro adapter refuses it again before opening a tab.

## Scope

- Slots: MAIN and PT01 to PT09. SWCH is never changed (`scope_violation`).
- Every slot the plan does not change is frozen in the plan and must be unchanged
  afterwards: SWCH always, MAIN unless the plan replaces it, every untouched PT slot.
- Child listings only, or standalone listings scoped explicitly. The fallback's
  parentage gate refuses parent ASINs; the direct route has no such gate, so leave
  parent SKUs out of the step 2 slot plan.
- Outside the request, nothing changes: no copy, price, variation or other fields.

## Steps

1. **Account gate and binding.** Verify the seller and marketplace, then resolve the
   IDs with `ffp-mcp.mjs binding` (`references/mcp-reads.md`).
2. **Survey (planning only).** `ffp-mcp.mjs survey --format md` on a verified export,
   or on a saved `get_listings` result, gives parentage, MAIN, SWCH, PT01 to PT09 and
   free slots per SKU. Use it to agree the slot plan with the operator. It is not
   baseline evidence; the baseline is the live before-read in step 5.
3. **Finished-file intake.** Write a manifest CSV with columns `sku`, `slot`, `file`
   and `source_ref` (Drive file, Figma frame or chat attachment) for the files the
   operator confirmed, then run, with the wizards-ai virtualenv:

   ```bash
   ~/os/wizards-ai/venv/bin/python skills/amazon-flatfilepro/scripts/image_intake.py intake \
     --manifest <manifest.csv> --receipt output/<client>/catalog/<run>/intake-receipt.json
   ```

   It refuses SWCH, duplicate SKU and slot pairs, missing source references, formats
   other than PNG or JPEG, sides under 500 px or over 10,000 px, and PNGs over
   10,000,000 bytes (Cloudinary Free rejects larger files). A JPEG, including a
   multi-picture phone JPEG, is turned upright from its rotation tag, converted to
   PNG, and both hashes are recorded; a PNG with a rotation tag is refused. Each PNG
   is copied into the wizards-ai broker root
   `mentions/bulk-images/source-archive/<sha256>.png` and never overwrites a
   different file. A refused manifest archives nothing and exits 2 with every
   refusal listed. Relative `file` paths resolve against the current directory.
4. **Host.** Run `image_intake.py publish --receipt <intake-receipt.json>` with the
   same virtualenv. It calls wizards-ai `cloudinary_assets.publish` for each entry,
   which returns an HTTPS `res.cloudinary.com` URL only after the public bytes match
   the hash; the same hash always gives the same URL and never overwrites an asset.
   It records each URL in the receipt, skips entries already hosted, and writes
   `intake-receipt-images.json`: the `--images` input for step 5. The hosted file is
   named after the PNG's SHA-256, and `build` refuses any URL that is not on
   `res.cloudinary.com` or does not end in `/<image SHA-256>.png`. Publishing
   makes the images public, so run it only for files the operator confirmed.
5. **Live before-read and build.** Save `flatfilepro_get_listings_item_from_amazon`
   for each SKU and build an images batch from the step 4 list
   (`references/direct-update-mode.md`, steps 3 and 5):

   ```bash
   node tools/amazon-operations/ffp-mcp-update.mjs build \
     --seller-id S --marketplace-id M --scope images \
     --images output/<client>/catalog/<run>/intake-receipt-images.json \
     --live <live read per SKU> --out output/<client>/catalog/ffp-updates/<batch>/
   ```

   Image payloads carry nothing, so no export or field definitions are needed. Each
   payload is `[{marketplace_id, media_location}]` per changed slot; `review.md`
   shows the before URL, hash and hosted URL per slot and Amazon's issues before the
   write. SWCH is refused with `scope_violation`.
6. **MAIN checks.** Before asking for approval, check every new MAIN image against
   the main-image rules in `Amazon Seller Help/articles/153-product-image-guide-G1881.md`:
   pure white background (RGB 255, 255, 255), product filling about 85% of the frame,
   the whole product in frame and shown once, one unit, no text, logos, borders,
   watermarks, props or mannequin, and the category rules for footwear and
   clothing. A lifestyle MAIN is allowed only for the product types the style guide
   names. Report each check; a failed check stops the MAIN change.
7. **Approval.** Show the operator `review.md` with the SKUs, slots, image hashes,
   hosted URLs and MAIN check results. The write needs the operator's approval of
   that exact batch in the current chat; then run `ffp-mcp-update.mjs approve`. A
   batch that changes MAIN also needs `--main-review FILE` with exactly
   `approved_by`, `approved_at` (ISO timestamp with timezone, not future dated, at most
   12 hours old) and `image_sha256`, the list of every MAIN image hash in the batch. A mismatch returns
   `main_review_required`. The approval expires after 12 hours; after that, or in a
   later session, the operator approves the exact batch again in the current chat
   before the next write.
8. **Submit.** Run the submit loop in `references/direct-update-mode.md` (step 8):
   save a fresh live read of the SKU right before its write, run
   `next --batch DIR --live FILE` (`stale_base` means the listing changed since the
   build: close the item as void and build a new batch), call
   `flatfilepro_update_listing_on_amazon` with exactly its arguments, `record` at
   once, never resubmit, and record a timeout with `--no-response`. The first SKU
   must reach `verified` or `landed_status_pending`, or be closed with `--landed`,
   before `next` releases the rest.
9. **Status and verify.** Record `flatfilepro_get_listing_update_status` with
   `status`, save a live after-read and run `verify`. Each changed slot must show a
   new Amazon URL, and every untouched locator (SWCH, MAIN unless replaced, every
   untouched PT slot) must equal the before-read. A slot that still shows the before
   or hosted URL is `not_yet`; a slot that lost its image is `mismatch`. New issues
   naming `media_locator` and new listing-level issues are reported, and a new `ERROR`
   issue gives `issues_new_error`. The verify states and their next actions are in
   `references/direct-update-mode.md`, step 10.
10. **Pixel check.** The read-back shows an `m.media-amazon.com` URL, never the
    hosted URL, so it proves only that the slot changed. For each verify file in state
    `landed_pixels_unchecked`, run `image_intake.py compare --receipt
    <intake-receipt.json> --verify <verify file>` once with the wizards-ai
    virtualenv; one run checks every changed slot in that file. It compares aspect
    ratio, dHash and colour, and refuses to confirm an image it cannot tell apart from
    the slot's before image (`discriminating: false`). Run `verify` again with
    `--pixels <result>`. When that gives `pixels_mismatch`, the operator compares the
    archived PNG and the live image by eye; an image the operator accepts is closed
    with `close --landed` (allowed only when every other check in that verify is
    clean).
    The slot is done at verify state `verified`: pixels match and status `SUCCEEDED`.
    Pending processing stays pending; a mismatched or rejected slot is reported on its
    own (`pixels_mismatch`).

A rollback is a new images batch with the previous images, checked and approved like
any other. Download each before-read `m.media-amazon.com` image into
`downloads/<client>/catalog/`, record its SHA-256, intake it with `source_ref` set to
the before URL, publish it and build the batch (`references/direct-update-mode.md`,
Rollback). Never replay or edit a submitted batch.

## Workbook fallback (no connector)

When the FlatFilePro connector is unavailable in the attended session, steps 5 to 10
run as a workbook plan through `tools/amazon-operations/operations.py`:

1. **Prepare the plan.** Fetch and grid the export (`references/mcp-reads.md`), run
   the CDP item-detail read (`tools/amazon-operations/flatfilepro-listings.mjs
   --request FILE`), then run `operations.py prepare` with operation `listing.images`
   and:
   - `inputs.image_policy: attended_gallery`
   - `inputs.images`: the `intake-receipt-images.json` list from step 4,
     `{sku, slot, artifact: {path, sha256}, url}` per image
   - `inputs.image_fields`: each slot mapped to the grid's header, for example
     `MAIN` to `main_product_image_locator__1__media_location` and `PT01` to
     `other_product_image_locator_1__1__media_location`
   - `inputs.live`: the CDP item-detail read, with
     `inputs.image_catalog_source: flatfilepro_listing_read`
   - `inputs.source_export: {path, sha256, kind: ffp_mcp_export_grid}`
   A refusal prints `{"status": "blocked", "reason": <code>}` and exits 2. Codes this
   path adds or narrows: `attended_only` (prepare or execute with `WIZARDS_AI_MODE`
   set), `main_review_required`, `invalid_source` (connector rows passed as
   `inputs.live`, or an unknown `source_export.kind`), `scope_violation` (a SWCH slot
   or mapping) and `missing_main_image` (a SKU with no MAIN whose MAIN the plan does
   not replace). The generic `listing.images` request fields and the session the CLI
   runs in are in `tools/amazon-operations/README.md`, which does not describe this
   path yet.
2. **MAIN checks** as in step 6.
3. **Preview.** Run `upload-map` mode with the plan's exact workbook up to the
   preview headed "Make your changes and click submit below." and stop. Compare every
   changed SKU and slot with the plan. Reload the Imports page before the execute step
   stages its own upload.
4. **Approval.** As in step 7, for the exact plan and preview; `Update Listings`
   needs it. A MAIN change passes `grant.main_image_review` with the same three keys.
5. **Execute.** `operations.py execute` with the grant. It re-reads the listings
   within five minutes of submission, refuses if a protected slot moved, records the
   MAIN review in the journal and captures the run ID.
6. **Reconcile.** `operations.py reconcile` reads Activity and the detail pages.
   Completion needs every changed slot published and processed and every protected
   slot unchanged. Pending processing stays pending; a rejected slot is reported on
   its own.

## Known limits

- Fallback only: MAIN mapping in the FlatFilePro import screen has not been run
  through the adapter. The adapter maps MAIN only when the option's visible label shows
  `main_product_image_locator__1__media_location`; otherwise it stops with
  `ffp_image_slot_unverifiable`. A hand-driven attended gallery run in September 2026
  saw exactly that label on the mapping screen, and Activity reported the slot as
  `/main_product_image_locator/0/media_location`. The first MAIN run through the
  fallback confirms it at its preview step.
- Fallback only: PT09 (`other_product_image_locator_9`) has no adapter search
  translation yet.
- Direct route: the live read-back returns Amazon's own `m.media-amazon.com` URL for
  every locator, never the hosted URL, and catalog image IDs do not match the
  listing's locator IDs. The pixel check in step 10 is the proof that the right
  picture landed. Its thresholds (dHash 24, aspect 0.02, colour 12) are provisional
  until the first live image write calibrates them; `verify` refuses a pixel file
  compared with looser ones (`pixels_thresholds`).
