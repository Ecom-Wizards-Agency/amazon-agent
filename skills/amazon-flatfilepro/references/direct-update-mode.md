# Direct Update Mode

Mode browser: None (FlatFilePro connector reads and writes plus local tooling; no browser).

Use this mode to change an existing listing on Amazon through the FlatFilePro
connector's `flatfilepro_update_listing_on_amazon`. It is the default for every edit
the tool can express, at any number of SKUs: copy, backend terms, structured
attributes, and MAIN and PT01 to PT09 images. Attended only. Rights row:
`flatfilepro.mcp_update` in `docs/rights/README.md`.

All local commands are `node tools/amazon-operations/ffp-mcp-update.mjs <subcommand>`.
The tool never calls FlatFilePro or Amazon. The agent calls the connector tools,
saves their results, and passes the files (or STDIN) to it. Output is JSON on stdout.
Exit 0 is ok, 2 is blocked (`{status:'blocked', reason, message}`) or held, and 3 is a
`verify` state other than `verified`, `landed_status_pending` or
`landed_pixels_unchecked`. A flag's value is always the next argument, so a
dash-prefixed SKU is safe; `--flag=value` also works. Every subcommand except
`pending` refuses with `attended_only` when `WIZARDS_AI_MODE` is set.

## When to use the workbook route instead

The direct write replaces whole attribute arrays and cannot clear, delete or touch
relationships. Use `prepare` and `upload-map` (`Update Listings` in FlatFilePro) for:

- relationships and variations (parentage, variation theme, child links)
- clearing a value or removing an element
- price, offer and stock fields (`purchasable_offer`, `list_price`,
  `uvp_list_price`, `fulfillment_availability`, `merchant_shipping_group`,
  `condition_type`, `condition_note`, `max_order_quantity`, `product_tax_code`,
  `skip_offer`, `merchant_release_date`, any `*_seller_allowed_price` and any offer
  image locator)
- brand and identifiers (`brand`, `externally_assigned_product_identifier`,
  `merchant_suggested_asin`)
- new listings
- an attended session without the FlatFilePro connector
- Grimoire, Slack and scheduled runs: the connector is an account-level claude.ai
  connector and attended only. Grimoire keeps its CDP pipeline and the
  `secondary-images` mode (`listing.images.bulk`).

The swatch image (SWCH) is never changed in either route.

## What the write tool does

- One SKU per call: `{sku, sellerId, marketplaceId, productType, attributes}`.
- Each supplied top-level attribute's whole array is replaced. Omitted attributes stay
  as they are. So a payload that changes bullet 3 must carry bullets 1, 2, 4 and 5
  unchanged; this is the carried content the base rules below protect.
- No preview and no idempotency key. A second call is a second write.
- `ACCEPTED` means Amazon accepted the submission, not that it is live. The response
  carries `runId` and `runItemId` for `flatfilepro_get_listing_update_status`, where
  only `SUCCEEDED` confirms. The production poll guidance is 1800 s.
- Images take a public `media_location` URL, so hosting through Cloudinary
  (`image_intake.py publish`) stays.

## Route

1. **Account gate and binding.** Verify the seller and marketplace, then resolve the
   IDs with `ffp-mcp.mjs binding` (`references/mcp-reads.md`). Every later step
   carries these exact `--seller-id` and `--marketplace-id` values; a saved read for
   another pair is refused (`live_mismatch`, `account_mismatch`, `fields_mismatch`).

2. **Base.** Untouched content in a payload may only come from a byte-verified source:
   - the verified connector export (`ffp-mcp.mjs fetch-export`), passed as
     `--export FILE`; or
   - when the export fails (large catalogs: `RETRY_EXHAUSTED` on 2,557 listings on
     28 October 2026), a saved `get_listings` result for the batch's SKUs, passed as
     `--listings FILE` (`missingSkus` empty). It counts only because `build` checks it
     against the live before-read on every touched attribute.

   A change that sets every non-selector leaf of an attribute carries nothing, so it
   needs no base: single-item fields such as `item_name`, `generic_keyword`,
   `product_description` and `title_differentiation`, and every image slot. A base,
   when given, must cover every SKU in the batch.

3. **Live before-read.** Call `flatfilepro_get_listings_item_from_amazon` for each SKU
   and save the result under `downloads/{client}/catalog/`, one file per SKU. Starting
   this route counts as the operator's request for its live reads. A saved file may
   be trimmed to keep context small: keep `issues`, `summaries`, every touched
   attribute and all eleven image locators (`main_product_image_locator`,
   `other_product_image_locator_1` to `_9`, `swatch_product_image_locator`), and list
   the kept names in a top-level `kept_attributes`. A listed name absent from
   `item.attributes` means absent on Amazon. A read without `kept_attributes` must be
   the complete tool result: trim only with `kept_attributes`, because a slot missing
   from both an untrimmed before-read and after-read counts as empty, not as checked.
   If a touched attribute is really absent on Amazon, list it in `kept_attributes`
   (`live_incomplete` otherwise). For batches over 10 SKUs, hand the reads to read-only helper agents in
   chunks of up to 10 SKUs; they save files and return paths. The main session stays
   the only caller of the write tool. These reads feed the build; step 8 takes a
   second, fresh read right before each write.

4. **Fields.** Save `flatfilepro_get_product_type_fields` once per product type when
   the change adds an attribute, element or leaf that has no element 0 to copy
   (`structure_unknown` otherwise), and for scope `attributes`, where it supplies the
   types, `maxLength`, `maxUniqueItems` and `selectOptions`. For SEO copy it adds the
   length checks; pass it when available. The result is about 250K characters: when
   the runtime already stored it as a file, copy that file byte for byte instead of
   retyping it. Nothing in it is marked required, and `selectOptions` are suggestions
   (free text such as `100% polyester` was accepted); a value outside them needs
   `--allow-free-text ATTR` and shows as a warning in `review.md`.

5. **Build.**

   ```bash
   node tools/amazon-operations/ffp-mcp-update.mjs build \
     --seller-id S --marketplace-id M --scope seo|attributes|images \
     --changes changes.csv | --images intake-receipt-images.json \
     --live live-SKU1.json --live live-SKU2.json [--export FILE | --listings FILE] \
     [--fields fields-COAT.json] [--allow-free-text ATTR] \
     --out output/{client}/catalog/ffp-updates/<batch>/ --register-run RUN_ID
   ```

   - `--changes` (scopes `seo` and `attributes`) is a CSV with exactly
     `sku,attribute,value`, in canonical `attr.N.key` spelling counted from 0
     (`bullet_point.2.value`, `unit_count.0.type.value`). This differs from the
     `/flatfilepro-prepare` CSV, which uses the grid's `__N__` headers
     (`item_name__1__value`): that spelling and whole-element paths give `usage`.
     Row order does not matter; an index equal to the current length appends, a gap
     gives `index_gap`. A row whose attribute already has that value on Amazon gives
     `no_op_change`: verify could never show it landed, so drop the row.
   - `--images` (scope `images`) is `intake-receipt-images.json` from
     `image_intake.py publish` (`references/attended-images-mode.md`). Each `url`
     must be the `res.cloudinary.com` URL that `publish` returned, ending in
     `/<image SHA-256>.png`; any other URL gives `invalid_value`.
   - Scope `seo` allows only `item_name`, `bullet_point`, `product_description`,
     `generic_keyword` and `title_differentiation`. Scope `attributes` refuses every
     `*_image_locator` attribute. Relationship, offer and identity fields are refused
     in every scope.
   - Typing follows the field definition (`number` and `integer` become JSON numbers,
     `boolean` true or false); without one, the replaced leaf keeps its type. Carried
     leaves keep their exact JSON. An image payload is
     `[{marketplace_id, media_location}]`.
   - `--out` must not exist or must be empty. `--ledger-root` defaults to the parent
     of `--out`, where `build`, `approve` and `next` look for overlapping items in
     other batches (`submission_pending`). `build` and `approve` count both submitted
     items that are still open and approved items that were neither submitted nor
     voided; `next` counts only the submitted ones.

   It prints `batch`, `batch_sha256`, `items`, `skus_read`, `review` and
   `warnings_count`. Check `items` against the SKUs requested and name any missing
   SKU.

6. **Checks before approval.**
   - **MAIN images.** Check every new MAIN image against the main-image rules in
     `Amazon Seller Help/articles/153-product-image-guide-G1881.md`: pure white
     background (RGB 255, 255, 255), product filling about 85% of the frame, the whole
     product in frame and shown once, one unit, no text, logos, borders, watermarks,
     props or mannequin, and the category rules for footwear and clothing. A
     lifestyle MAIN is allowed only for the product types the style guide names.
     Report each check; a failed check stops the MAIN change.
   - **Copy.** Title, bullets, description, Item Highlights and backend terms pass
     the `amazon-seo` claims gate (`skills/amazon-seo/references/health-claims-compliance.md`)
     before they enter a changes CSV.

7. **Approval.** Show the operator `review.md` (before and after per element, carried
   elements marked, warnings, image hashes and URLs, Amazon's issues before the
   write) and the `batch_sha256`. The write needs the operator's approval of that
   exact batch in the current chat. Then run
   `approve --batch DIR --approved-by NAME`. A batch with any MAIN image also needs
   `--main-review FILE`, a JSON file with exactly `approved_by`, `approved_at` (ISO
   timestamp with timezone, not future dated and at most 12 hours old) and `image_sha256`, the list of every
   MAIN image hash in the batch; any other set gives `main_review_required`. Write
   that file from the operator's MAIN approval in chat. Any change to `batch.json`, a
   payload or the review file after approval gives `batch_changed` or
   `main_review_required`; build a new batch instead.

   An approval expires after 12 hours, and so does its MAIN review, which is usually
   the older of the two: when either runs out, `next` refuses with `approval_expired`.
   A batch approved in an earlier session needs the operator's fresh approval of the
   exact batch in the current chat; then run `approve` again, which appends a new
   approval and returns `renewed: true` (an unexpired approval gives
   `already_approved`). `approve` refuses with `submission_pending` when an
   unsubmitted item overlaps an open or approved, unsubmitted item in another batch.

8. **Submit loop.** Repeat until `next` prints `status: complete`:
   1. Save a fresh `flatfilepro_get_listings_item_from_amazon` read of the SKU about
      to be written, right before the write, the same way as step 3. For batches over
      10 SKUs, read-only helper agents save these fresh reads in chunks of up to 10
      right before the main session submits that chunk; the main session stays the
      only writer.
   2. `next --batch DIR --live FILE` checks that read (seller, marketplace and SKU
      give `live_mismatch`; a trimmed or incomplete read gives `live_incomplete`)
      and prints one compact line with `index`, `sku`, `tool` and `arguments`. If a
      touched attribute differs from the build's before-read it refuses with
      `stale_base`: the listing changed since the build, so close the item (void)
      and build a new batch from fresh reads. `record_incomplete` means
      `responses/NNN.json` exists for an item with no submitted record; run `record`
      for it, which recovers the saved response.
   3. Call `flatfilepro_update_listing_on_amazon` with exactly those arguments. Do not
      retype, reorder or add anything.
   4. Immediately pipe the tool's response to
      `record --batch DIR --sku S` on STDIN. It saves the raw response and extracts
      `runId`, `runItemId`, `status` and `pollAfterSeconds`. A response that names
      another SKU is still recorded and exits 2 with `response_sku_mismatch`: stop and
      report it. If `responses/NNN.json` already exists from an earlier `record`
      whose ledger append failed, `record` appends the submitted event from that file,
      ignores STDIN and returns `recovered: true`.
   5. A timeout or an unclear tool error is recorded with
      `record --batch DIR --sku S --no-response --note TEXT` (status `UNKNOWN`). The
      write may have landed.

   Never resubmit. An item with any record, including `UNKNOWN`, is never offered
   again; a failed or doubtful item is resolved with a live read and `verify`, then
   `close`, and a new batch if the change is still wanted.

   **First-item hold.** The anchor is the first item that was not voided before its
   write (normally item 0). `next` releases the items after it only once the anchor's
   latest verify state is `verified` or `landed_status_pending`, or the anchor was
   closed with `--landed`. Until then it exits
   2 with `status: held`, reason `first_item_unverified`. Run steps 9 and 10 for the
   anchor first. An anchor closed after its write without `--landed` keeps the hold;
   build a new batch for the remaining items.

9. **Status.** After `pollAfterSeconds` (production guidance 1800 s), call
   `flatfilepro_get_listing_update_status` with the recorded `runId` and `runItemId`
   and pipe the result to `status --batch DIR --sku S`. It saves each result and
   records `status`, `outcome` and `terminal`; without a `terminal` field, `SUCCEEDED`
   or any failure word listed under `update_failed` in step 10 counts as terminal.
   Only `SUCCEEDED` confirms.

10. **Verify.** Save a live after-read the same way as step 3, then run
    `verify --batch DIR --sku S --live FILE`. It compares each touched attribute with
    the payload and the before-read, each changed image slot with the before-read,
    every untouched image locator (`protected_slots`), and Amazon's issues
    (`issues_new`: each extra occurrence of an issue on a touched attribute, with
    `media_locator` meeting any touched image slot, plus every new listing-level issue
    that names no attribute, such as a suppression). Values compare as text: strings
    are exact after trimming, so `00123` is not `123`; a decimal string drops trailing
    fractional zeros (`36.00` equals `36`); JSON numbers and booleans compare as their
    text (`0.26` equals `"0.26"`, `true` equals `"true"`). Object keys are sorted.
    Each attribute shows `result` `match`, `not_yet` or `mismatch`.

    The state is the first that applies, in this order:

    | state | meaning | next action |
    | --- | --- | --- |
    | `mismatch` | an attribute equals neither the before-read nor the payload; an image slot that had an image now has none; a slot shows a URL that is neither the before URL, the hosted URL nor an `m.media-amazon.com` URL; or a protected slot changed | if the status is terminal and the item has a `runId`: report it from the verify file, close the item with the operator's decision, and build a new approved batch if the change is still wanted. If the status is not terminal, or the write is `UNKNOWN`: the write may still be in progress, so poll status (when there is a `runId`), save a new after-read and verify again before treating it as final |
    | `update_failed` | the latest status (or the update response, before any poll) has status or outcome `FAILED`, `FAILURE`, `REJECTED`, `CANCELLED`, `CANCELED`, `ERROR`, `PARTIALLY_FAILED` or `PARTIAL_FAILURE` (any case), or the latest status is terminal and not `SUCCEEDED` | report it from the status and verify files; never resubmit. Close the item with the operator's decision, then build a new approved batch if the change is still wanted |
    | `pixels_mismatch` | a pixel result for the same SKU, slot, Amazon URL and image hash has `match: false` | open the pixels file. `discriminating: false` means the check cannot tell the new image from the before image: the operator compares both by eye and, when the right picture is live, you run `close --landed`. Otherwise the live image is not the archived PNG: report it with the compare file (step 11), close the item with the operator's decision, then build a new approved batch if the change is still wanted |
    | `issues_new_error` | a new issue with severity `ERROR` | report its code and attribute names. Close the item with the operator's decision, then build a new approved batch if the change is still wanted |
    | `not_yet` | an attribute still equals its before-read; an image slot still shows the before URL or the hosted URL, or was empty before and is still empty | wait (poll status when there is a `runId`), save a new after-read and verify again. Never resubmit. Close the item with the operator's decision if it never lands |
    | `landed_pixels_unchecked` | everything matches, but a changed image is not pixel-confirmed yet | run step 11, then verify again with `--pixels` |
    | `verified` | everything matches, every changed image is pixel-confirmed and a polled status is `SUCCEEDED` | done |
    | `landed_status_pending` | everything matches, but no polled status is `SUCCEEDED` yet | poll status until `SUCCEEDED`, then verify again. Without a `runId` (an `UNKNOWN` write) the status cannot be polled: the operator decides, and `close --landed` records that it landed |

    `verified`, `landed_status_pending` and `landed_pixels_unchecked` exit 0; every
    other state exits 3. Only `verified` and `landed_status_pending` release the
    first-item hold, apart from a `close --landed` of the anchor. New issues are
    counted against the fresh read taken at `next`, so an issue that was already on
    the listing right before the write is not blamed on it. A `SUCCEEDED` in the update response alone never verifies; it
    needs a polled status. The verify file also carries `pixel_checks` (`sku`, `slot`,
    `attribute`, `amazon_url`, `image_sha256`, `before_url`, `confirmed`, `result`
    `confirmed`, `rejected` or `unchecked`) and `update_status` (`status`, `outcome`,
    `terminal`, `succeeded`, `failed`).

11. **Image pixel check.** Image locators read back as `m.media-amazon.com` URLs,
    never the submitted URL, so a new URL proves only that something changed. For each
    verify file in state `landed_pixels_unchecked`, run once with the wizards-ai
    virtualenv; one run checks every changed slot in that file:

    ```bash
    ~/os/wizards-ai/venv/bin/python skills/amazon-flatfilepro/scripts/image_intake.py compare \
      --receipt output/{client}/catalog/<run>/intake-receipt.json \
      --verify output/{client}/catalog/ffp-updates/<batch>/verify/NNN-K.json
    ```

    It downloads the Amazon image (HTTPS `m.media-amazon.com` only) and compares it
    with the archived PNG three ways: aspect ratio (limit 0.02), a 256-bit dHash
    (limit 24 bits) and the mean colour difference of 32x32 RGB thumbnails after
    flattening transparency onto white, counted only where either image is not
    near-white so a white background cannot hide a colour variant (limit 12 on a 0 to
    255 scale). When the slot
    had an image before, it also downloads that `before_url` image. If the archived
    PNG is within every limit of the before image too, the check cannot tell old from
    new: the result shows `discriminating: false` and `match: false`, and verify then
    reports `pixels_mismatch`. In that case it is not proof of a wrong picture: show
    the operator the archived PNG and the live image, and the operator checks them
    visually and decides; when the right picture is live, run `close --landed`. The limits are provisional until
    the first live image write calibrates them, and `verify` refuses a pixel file
    whose thresholds are missing or looser than these (`pixels_thresholds`), so never
    loosen them on the command line. Exit 0 is a match on every slot, 2 a mismatch or
    refusal. The result goes to `<verify stem>-pixels.json` and is never overwritten;
    a second run on the same verify file is refused. Then run `verify` again with a
    fresh after-read and `--pixels <that file>`; it compares the new after-read, so
    run compare again if the Amazon URL changed in between.

**Done** means `verify` state `verified`: the live read-back matches the payload, every
protected slot is unchanged, every changed image is pixel-confirmed and a polled
status is `SUCCEEDED`. Report `landed_status_pending` as "landed, status pending",
never as done. Report every `issues_new` entry with its code and attribute names.

## Later sessions and closing

`pending --root output/{client}/catalog/ffp-updates` lists every open item with its
state (`built`, `approved_not_submitted`, `submitted`, `status_nonterminal`,
`status_terminal`, `unknown`, or the latest verify state other than `verified`) and
the next action. Closed and void items are not listed. It is read-only and runs
anywhere. Run it at the start of any direct-update session for that client.

An approved batch from an earlier session is not approved for this one. Before its
next write the operator approves the exact batch again in the current chat once the
12-hour approval has expired, and every write still starts with the fresh live read
of step 8. If the change is no longer wanted, void the item instead. Until each
approved item is submitted or voided, it blocks any new batch that touches the same
SKU and attribute (`submission_pending` at `build` and `approve`).

`close --batch DIR --sku S --reason TEXT --approved-by NAME [--landed]` needs the
operator's decision in chat and releases `submission_pending` for that SKU. Add
`--landed` only when the operator has confirmed that a submitted item landed
correctly. The tool allows it in two cases only, judged from the item's latest
verify file, and refuses anything else with `landed_unproven`: an `UNKNOWN` write
whose live read matches (`landed_status_pending` without a `runId`), or a
`pixels_mismatch` the operator accepted by eye where every attribute matches,
every changed slot changed, every protected slot is preserved, there is no new
`ERROR` issue and the status is `SUCCEEDED` (or cannot be polled). The closed event
records that verify file. A landed close of the first item releases the
rest of the batch, while any other close of a submitted first item keeps the hold. It
ends:

- an item that was never submitted, recorded as `void: true`: `next` never offers it
  and it no longer anchors the first-item hold. Use it for an abandoned batch or
  after `stale_base`;
- an `UNKNOWN` write that never landed;
- an `UNKNOWN` write whose live read matches (`landed_status_pending` without a
  `runId`), which can never be polled: `--landed`;
- an image the pixel check could not tell from the before image and the operator
  accepted by eye: `--landed`;
- a `mismatch`, `update_failed`, `pixels_mismatch` or `issues_new_error` item, before
  a new batch makes the change again.

## Rollback

A rollback is a new batch built from the before-read (`batch.json`
`items[].before.touched` holds the live arrays), checked and approved like any other.
For images, the before-read's `m.media-amazon.com` URL is the previous picture, and
`intake` takes only local files:

1. Download that image into `downloads/{client}/catalog/` (for example
   `curl -fsS --proto =https -o <file> <before URL>`) and record its SHA-256
   (`sha256sum <file>`) in the operator note.
2. Add it to an intake manifest with that local path as `file` and the before URL as
   `source_ref`, then run `image_intake.py intake` and `publish`
   (`references/attended-images-mode.md`, steps 3 and 4). Intake refuses a side under
   500 px.
3. Build an images batch from the new `intake-receipt-images.json`, then check,
   approve, submit and pixel-check it like any other.

A rollback that needs an element or attribute removed goes through the workbook
route. Never edit or replay a submitted batch.

## Batch directory and storage

```
output/{client}/catalog/ffp-updates/<batch>/
  batch.json          inputs with SHA-256, items with payload hash, touched attributes,
                      base source, carried content, images, warnings and the before-read
  batch.sha256        SHA-256 of batch.json
  payloads/NNN.json   exact tool arguments per SKU
  review.md           the approval view
  ledger.jsonl        append-only: built, approved, submitted, status, verify, closed
  responses/NNN.json  raw update responses
  status/NNN-K.json   raw status results
  verify/NNN-K.json   verify results (and NNN-K-pixels.json from compare)
```

The batch is internal and never goes to Drive (`docs/drive-delivery.md`).
`build --register-run` registers `batch.json`, `batch.sha256`, `review.md`, the
payloads and `ledger.jsonl` with artifactctl as `preserve`. The responses, status,
verify and pixel files written later stay in place in the batch directory,
unregistered; cleanup never removes an unregistered file. A registration failure never
fails the build; register by hand. Do not re-register the ledger in the same run, since it
keeps growing. Live reads and field definitions stay under `downloads/{client}/catalog/`.

## Refusal reasons

| reason | meaning |
| --- | --- |
| `usage` | bad flags, CSV columns or path spelling (export `__N__` spelling, whole-element paths), wrong input for the scope, two bases, empty STDIN |
| `attended_only` | `WIZARDS_AI_MODE` is set |
| `relationship_field` | a relationship attribute (`*relationship*`, `parentage_level`, `variation_theme`, `parentAsins`, `childAsins`); use the workbook route |
| `offer_field` | a price, offer or stock attribute (the list under "When to use the workbook route instead"); use the workbook route |
| `identity_field` | `brand` or an identifier; use the workbook route |
| `scope_violation` | outside the scope's fields, any `*_image_locator` attribute outside scope `images`, or SWCH |
| `empty_value` | an empty or whitespace value, or an empty image URL |
| `invalid_value` | a bad number or boolean, a path naming an object, a bad slot or image hash, or an image URL that is not the `res.cloudinary.com` URL from `publish` ending in `/<image SHA-256>.png` |
| `no_op_change` | a non-image attribute whose new value equals the live before-read; drop the row |
| `duplicate_change` | the same SKU and path, or SKU and slot, twice |
| `live_unreadable` | a live file is unreadable or not JSON |
| `live_mismatch` | a live read for another source, seller or marketplace, or a SKU outside the batch; at `next` and `verify`, a read for another SKU |
| `live_incomplete` | `kept_attributes` misses a touched attribute or an image locator, or a read without `kept_attributes` lacks a touched attribute (list it in `kept_attributes` to assert it is absent on Amazon) |
| `live_missing` / `live_duplicate` | not exactly one live read per SKU |
| `sku_missing` / `sku_duplicate` / `sku_archived` | the base does not cover a SKU cleanly |
| `account_mismatch` | the export or `get_listings` copy belongs to another seller or marketplace |
| `listings_unreadable` / `fields_unreadable` | a saved JSON file cannot be read |
| `fields_mismatch` | field definitions for another seller or marketplace |
| `product_type_mismatch` / `product_type_unknown` | base and live disagree on the product type, or neither has one |
| `stale_base` | at `build`, the live before-read differs from the base on a touched attribute (fetch a fresh base); at `next`, the fresh read differs from the build's before-read (close the item as void and build a new batch) |
| `base_unverified` | carried content with no verified export or agreeing `get_listings` base |
| `structure_unknown` | a new attribute, element or leaf with no element 0 and no field definition |
| `index_gap` | an element index past the end of the array |
| `max_length` / `max_items` | over the definition's `maxLength` or `maxUniqueItems` |
| `free_text_unapproved` | a value outside `selectOptions` without `--allow-free-text` |
| `batch_exists` | `--out` is not empty |
| `submission_pending` | the same SKU with an overlapping attribute is submitted and open, or (at `build` and `approve`) approved but neither submitted nor voided, in another batch under the ledger root |
| `count_mismatch` | SKUs read and items built differ |
| `batch_missing` / `batch_changed` | no `batch.json`, or it or a payload changed since the build |
| `ledger_invalid` | a corrupt ledger line, or a ledger without `batch.json` |
| `already_approved` / `not_approved` | approval state; `already_approved` only while the approval is under 12 hours old |
| `approval_expired` | at `next`, the latest approval or its MAIN review is older than 12 hours; the operator approves the exact batch (and any MAIN images) again in this chat, then run `approve` with a fresh review file |
| `landed_unproven` | `close --landed` on an item whose latest verify is not one of the two cases the tools cannot settle (see `close`) |
| `main_review_required` | the MAIN review is missing or invalid, or its file changed after approval |
| `first_item_unverified` | the anchor item is not yet `verified` or `landed_status_pending`, or was closed after its write without `--landed` (status `held`) |
| `record_incomplete` | at `next`, `responses/NNN.json` exists for an item with no submitted record; run `record`, which recovers it |
| `already_recorded` / `out_of_order` | `record` sequencing |
| `response_sku_mismatch` | the response names another SKU; it is still recorded |
| `status_without_run` / `status_mismatch` | no run IDs, or a status result for another run |
| `item_missing` / `not_submitted` / `already_closed` | item selection, `verify` on an item with no submission record, and `close` on an item already closed |
| `pixels_unreadable` | a `--pixels` file without a `results` list |
| `pixels_thresholds` | a `--pixels` file whose `thresholds` are missing, not numeric, or looser than `max_dhash` 24, `max_aspect_delta` 0.02 and `max_color_delta` 12 |

## Known limits

- The model copies each payload into the tool call. A copy error goes live and shows
  only at `verify`; the first-item hold limits the damage to one SKU per batch.
- The response and status shapes are not documented. `record` and `status` look for
  `runId`, `runItemId`, `status` and `pollAfterSeconds` at the top level and one level
  down; when they are missing the item shows `unknown` in `pending` and is settled by
  a live read, `verify` and `close`.
- `verify` compares whole arrays. If Amazon adds keys on read-back, the result is a
  `mismatch` that shows both values; review it before calling it a failure.
- The pixel limits (dHash 24, aspect 0.02, colour 12) are provisional; the first live
  image write calibrates them in `image_intake.py` and `ffp-mcp-update.mjs` together.
- The colour check compares pixel by pixel and skips only the near-white background,
  so an image Amazon re-centred or re-padded can fail it although it is the right
  picture, and so can a wide-gamut PNG (the check ignores embedded colour profiles).
  A `pixels_mismatch` is a reason to look, not proof: the operator compares the
  images by eye.
- Each SKU costs one write and three live reads (before the build, right before the
  write, and after it). Large batches are slow, not cheap.
