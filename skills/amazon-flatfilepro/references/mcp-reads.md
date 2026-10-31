# FlatFilePro MCP Reads

Mode browser: None (FlatFilePro connector reads plus local tooling; workbook upload, mapping and submit stay on CDP).

This page covers the FlatFilePro connector's reads: FlatFilePro's saved copy of each
listing, the catalog export, field definitions and live Amazon reads. Direct listing
writes are `references/direct-update-mode.md`. Workbook upload, mapping, submit and
Activity stay in the browser. Rights rows: `flatfilepro.read` and
`flatfilepro.mcp_update` in `docs/rights/README.md`.

**Attended only.** The connector is an account-level claude.ai connector, and
Grimoire cannot load those. Grimoire and scheduled jobs keep their CDP collectors.
When the connector is missing in an attended runtime, fall back to the XLSX export
or CDP read that the calling mode names.

## The connector tools

| Tool | Use |
| --- | --- |
| `flatfilepro_get_authorized_marketplaces_for_email` | Authorized seller and marketplace pairs (`selling_partner_id`, `marketplace_id`, `seller_name`, `marketplace_name`) |
| `flatfilepro_get_listings` | Saved listings for named SKUs: `seller_id`, `marketplace_id`, `asin`, `sku`, `attributes`, `productType`, `blankAttributes`, plus `missingSkus` |
| `flatfilepro_start_listings_export` | Full saved catalog as one gzip JSONL file; pass a new UUID `idempotencyKey`, default `archiveStatus` is `UNARCHIVED` |
| `flatfilepro_get_export_status` | Poll at `pollAfterSeconds` until `COMPLETED` |
| `flatfilepro_get_export_download` | Counts, SHA-256, sizes and a presigned download URL that expires in 30 minutes |
| `flatfilepro_get_listings_item_from_amazon` | Live Amazon getListingsItem for one SKU: attributes, `summaries` and Amazon's `issues` |
| `flatfilepro_get_catalog_item_from_amazon` | Live Amazon getCatalogItem for one ASIN: the ASIN view with Amazon's merged values from every contributor, not the seller's listing |
| `flatfilepro_get_product_type_fields` | Field definitions for one product type (types, `maxLength`, `maxUniqueItems`, `format`, `selectOptions`); about 250K characters |

Select the account with `sellerName` and `marketplaceCountry`, or exact IDs. When
the server reports an ambiguous selector, ask the operator to choose; never take the
first pair.

## Live Amazon reads

The direct-update route reads each SKU live before and after every write; that is a
standard step, and starting the route counts as the operator's request for those
reads. Other live reads run only when the operator asks for them. A read-only probe
on 29 October 2026 (one DE listing, product type COAT) showed:

- The live listing and FlatFilePro's saved copy held the same values in the same
  array order. The saved copy reorders object keys and adds a non-attribute
  `parentAsins` key.
- The live read returns most numbers and booleans as strings (`"0.26"`, `"false"`).
  Compare values as text, not bytes.
- Image locators read back as `m.media-amazon.com` URLs, never the URL submitted.
  The catalog read's PT image IDs do not match the listing's locator IDs. Only the
  pixel check (`image_intake.py compare`) proves which picture is in a slot.
- Issues carry `code`, `message` (in the marketplace language), `severity`,
  `attributeNames` and `categories`. Image issues name `media_locator`, not a slot.
- Field definitions mark nothing as required, and `selectOptions` are suggestions:
  free text such as `100% polyester` was accepted. Selectors such as `language_tag`
  and `marketplace_id` appear as prefilled literals.

## Which read may feed what (rule D1)

- **Upload values come only from a byte-verified source**: the MCP export after
  `fetch-export` has checked its SHA-256 and record count, or the existing FlatFilePro
  XLSX export and CDP item-detail read. `grid` refuses any other input with
  `planning_only_source`.
- **A saved `get_listings` result is a planning read.** The model copies the tool
  result into a file, so nothing proves the copy matches what the server sent. Use it
  for a slot survey, a gaps report or the SEO current-copy input, never for a workbook.
- `get_listings` returns archived SKUs and does not say they are archived; it also
  has no version id, `relationships`, `summaries` or `itemName`. The export carries
  `archived` and `versionId` on every record, and its default `UNARCHIVED` scope leaves
  archived listings out.
- **The direct route applies the same rule to carried content.** A direct write
  replaces whole attribute arrays, so every untouched element it carries comes from
  the verified export, or from a saved `get_listings` copy that agrees with the live
  before-read on every touched attribute (`base_unverified`, `stale_base`). Changed
  values come from the approved changes CSV or the intake receipt, never from a
  read.
- MCP rows are never live evidence for `operations.py`. A request whose `inputs.live`
  carries `source_kind: flatfilepro_mcp_listing_read` is refused with
  `invalid_source`. Live evidence stays the CDP item-detail read
  (`tools/amazon-operations/flatfilepro-listings.mjs`) or a report. An MCP grid may be
  the `inputs.source_export`, recorded with `kind: ffp_mcp_export_grid`
  (`ffp_export` for an FFP XLSX export).
- `get_listings` and the export show FlatFilePro's saved copy, not what Amazon
  displays. For live state, the live listing read with Amazon's `issues` comes first;
  the Category Listings Report and detail page stay the authority on what shoppers
  see.

## Route

All commands are `node tools/amazon-operations/ffp-mcp.mjs <subcommand>`. Output is
JSON on stdout. Exit 0 is ok, 2 is blocked (`{status:'blocked', reason, message}`),
and 3 means `gaps` found companion gaps. A flag's value is always the next argument,
so a dash-prefixed SKU is safe; `--flag=value` also works.

1. **Binding.** Save the authorized-marketplaces result under
   `downloads/{client}/catalog/`, then run
   `binding --marketplaces FILE --seller-name N --marketplace-name M` (or
   `--seller-id S --marketplace-id M`). It returns `seller_id`, `marketplace_id`,
   `flatfilepro_display_name` and a reminder that the browser selector readback is
   still required. Reasons: `binding_ambiguous`, `binding_unavailable`,
   `marketplaces_unreadable`. Every later step must carry these exact IDs.
2. **Export.** Start the export for that pair, poll the status, then call
   `flatfilepro_get_export_download`. A 6-listing catalog finished in about 1 s. On
   28 October 2026 a 2,557-listing catalog failed twice with `RETRY_EXHAUSTED` after
   about eight minutes each. When a large catalog's export fails, build the workbook
   source from the FlatFilePro XLSX export instead, and use `get_listings` only for
   planning reads. A direct update may use a `get_listings` copy that agrees with the
   live read as its base (`references/direct-update-mode.md`).
3. **Fetch.** Pass the download result JSON to
   `fetch-export --out-dir downloads/{client}/catalog/ --register-run RUN_ID` on
   **stdin**, as a quoted heredoc. The tool checks the host, streams the file, then
   checks size and SHA-256 before decompressing, the record count, every record's
   seller and marketplace, and that an `UNARCHIVED` export holds no archived record.
   It writes `<fileName>` and `<fileName>.receipt.json` and registers both as
   `preserve`. A file this run created is removed on failure. An identical existing
   file is reused with no network call (`status: existing`). Reasons include
   `export_url_expired` (call `flatfilepro_get_export_download` again for a fresh URL
   to the same file), `export_sha_mismatch`, `export_count_mismatch`,
   `export_foreign_record`, `export_archive_mismatch` and `export_file_exists`.
   `registration: failed` keeps the file; register it by hand.
4. **Resolve.** `resolve --export FILE --asin A --sku S` (each repeatable) returns
   every non-archived SKU for each ASIN, including `-1` contribution SKUs, with
   product type, parentage and parent SKU. `excluded_archived` lists archived SKUs by
   name; report them. Reasons: `sku_missing`, `sku_duplicate`, `sku_archived`,
   `asin_unavailable`, `receipt_missing`, `receipt_mismatch`.
5. **Grid.** `grid --export FILE --sku S ... --out output/{client}/catalog/<name>.csv`
   writes a CSV with a `sku` column and FlatFilePro's export header spelling, plus
   `<name>.csv.provenance.json` with the export hash, job and CSV hash. It refuses to
   overwrite. `--blank-columns` adds an empty column for each blank path that has an
   occurrence index and a leaf key, such as `apparel_size[0].height_type` as
   `apparel_size__1__height_type`. A change that names one writes that header into
   the upload workbook, so check it against the target template first. Bare blank
   names such as `material` get no column and are listed in `blank_attributes_bare`;
   filling one needs the technical header from the target template, and prepare
   refuses the bare name with `Missing source header`. To fill a bare blank
   attribute such as an empty `generic_keyword`, take its technical header from the
   target template and pass `--add-column generic_keyword__1__value` (repeatable).
   The tool adds an empty column only when that attribute is absent from every
   selected record and listed in its analysed `blankAttributes`; otherwise it stops
   with `attribute_not_blank`, `blank_status_unknown` or `column_present`. The
   provenance records each added column. Register the CSV and its provenance as
   `reproducible`.

Every `--export` read re-hashes the file against its receipt first.

## Other reads

These accept `--export FILE` or `--listings FILE` (a saved `get_listings` result)
plus `--sku S ...`. A `--listings` file must cover exactly the requested SKUs with an
empty `missingSkus`, and the output says `planning_only: true`. Every output names
its source: `transport`, `tool` (`flatfilepro_get_export_download` or
`flatfilepro_get_listings`), `arguments_sha256` (SHA-256 of the resolved arguments:
`{jobId}` for an export, `{marketplaceId, sellerId, skus}` in `--sku` order for
`get_listings`) and `raw_sha256` of the source file.

- `rows`: normalized per-SKU rows with nested values flattened, plus `version_id`,
  `archived` and blank-attribute status per record.
- `survey [--format json|csv|md]`: per SKU, parentage, MAIN, SWCH, PT01 to PT09 and
  free slots. A `--listings` survey starts with a "Planning read only" line.
- `gaps [--touch attr,attr]`: saved attribute groups with a member missing, for the
  attributes the change touches (`unit_count`, item, package and display weights,
  `*_dimensions`, `nutritional_info` serving fields). Exit 3 blocks the build until
  the change supplies every listed member or leaves the group alone. It also lists
  touched attributes that are blank today, attribute candidates that are blank (for
  `amazon-seo`, filled only from approved label or source-of-truth values; they are
  bare names, so the upload header comes from the target template) and free image
  slots. `blankAttributesStatus: SCHEMA_UNAVAILABLE` means unknown, not
  complete.
- `listing-json`: title, bullets, description, Item Highlights and backend terms per
  SKU, labelled `ffp-saved-backend`, in the shape `ranking_score.py` reads.

## Header spelling

The grid uses FlatFilePro's export spelling, so it stands in for an FFP XLSX export
anywhere one is used. Occurrence `i` becomes `__{i+1}__`: `item_name__1__value`.
Nested object keys join with one underscore: `unit_count__1__type_value`,
`item_dimensions__1__height_unit`. Nested arrays add `__{j+1}__`:
`purchasable_offer__1__our_price__1__schedule__1__value_with_tax`. An array of
strings ends with an empty key: `color__1__standardized_values__1__`. The prepare
script rewrites each `__N__` to `.{N-1}.` on write.

## The download URL is a bearer secret

Anyone holding the URL can download the client's whole catalog until it expires.
It already appears once in the tool result. Do not repeat it in chat, a command
argument, a saved file, a log, a receipt, an error report or a handoff; the only
second copy is the stdin heredoc to `fetch-export`. The tool redacts URLs from its
own messages and never writes the URL to its receipt. When the URL expires, request
a new one rather than reusing a copy.

## Storage

Exports, receipts and saved connector results stay internal under
`downloads/{client}/catalog/`; grids and their provenance under
`output/{client}/catalog/`. None of them goes to Drive (`docs/drive-delivery.md`).
