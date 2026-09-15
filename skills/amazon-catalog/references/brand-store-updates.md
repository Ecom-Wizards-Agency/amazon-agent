# Brand Store audits and scoped corrections

Browser: CDP (Grimoire, port 9223; use the shared browserctl task and evidence helpers).

Use this reference for product-grid audits, wrong or missing image destinations,
approved artwork replacements and Store builds. The team vault's
`Playbooks/amazon-brand-stores-playbook.md` owns design and module-selection guidance.
For dated evidence behind these rules, read
[brand-store-kabooki-2026-09.md](brand-store-kabooki-2026-09.md) when investigating that case.
For image reuse, crop geometry and inspection side effects, see
[brand-store-swissker-2026-09.md](brand-store-swissker-2026-09.md).

## Choose the operation and authority

| Request | Operation | Boundary |
| --- | --- | --- |
| Find incorrect products, links or artwork | Read-only audit | Inspect every page; produce evidence and a correction manifest |
| Correct existing links, images or grids | Scoped draft update | Copy verified source; preserve every unapproved field |
| Build approved page structures from Figma | Draft page rebuild | State exactly which pages will be cleared and rebuilt |
| Fix merged product families or wrong listing attributes | Separate catalog workflow | Store selections do not change parentage |

In direct chat, proceed with concrete changes already authorized in the session;
do not ask for the same permission again. In Slack reasoning runs, stage the exact
proposal and use the authorized registered executor. The Store update executor is
`store.update_draft`; its operations are `set_link`, `replace_image` and `set_grid`.
It is separate from `store.build_draft`, which clears and rebuilds planned pages.
Registration, tests and browser access do not enable an executor or authorize a run.
Read the Wizards AI `store_builder/README.md` and its scoped-update reference before
preparing an executor payload. An unavailable or disabled executor is a scoped
execution blocker, not evidence that the browser UI cannot perform the action.
Do not bypass Slack executor restrictions through direct CDP calls.

Submission for moderation, scheduling and publishing are separate actions. Record
their authorized scope explicitly; a draft update never implies them. This reference
does not grant permission to upload images, send messages, alter product families or
activate a workflow.

## Establish identity and complete coverage

Verify the signed-in advertiser/account, marketplace, Store entity and subentity,
source edition ID, displayed version name and status. Recheck after navigation,
reload, tool changes or login recovery: the builder may reopen an ended version.

Read the complete page tree, scrolling its virtualized list as needed, and snapshot
all source pages, headers, navigation, settings, widgets and breakpoint content.
Record page IDs and widget IDs, not only titles or section positions. Inventory
every image, linked detail tile, standalone product and grid, including subpages
such as socks, gloves and Outlet. A page absent from Figma remains part of the audit;
its design is not permission to improvise.

For a write, compare the fresh full source snapshot with the reviewed baseline,
then create a uniquely named draft by copying that verified source. Record the new
edition ID and copied content. Do not reuse an unrelated same-name draft or modify
the source in place. Reconcile partial prior work before retrying a mutation.

## Match evidence to products and tiles

Freeze the approved Figma file/node/version or correction-sheet revision. Read
hidden rows and embedded screenshots when they carry instructions. A sheet row,
similar caption, preview position or familiar-looking asset is insufficient alone:
match the screenshot to the actual existing desktop/mobile artwork and its widget.
Identify whether the screenshot covers one tile, linked details, or a complete
image group. Enumerate the exact affected widgets before editing.

Build one reviewable manifest with source row/evidence, page and widget IDs,
current asset and destination, intended operation, replacement evidence and outcome.
Category creatives link to exact Store pages; product creatives link to verified
ASINs; informational art stays unlinked. Validate model, color, size and pack count
against catalog SKUs and the pictured product. Never substitute another size or pack
because it is available. If the requested identity is unresolved, preserve the
uncertainty and propose a temporary unlink; apply it only when authorized. Follow
an explicit removal request even when a matching product exists.

## Verify assortment independently of stock

For a category audit, obtain fresh reports for the named account and marketplace.
Verify report provenance, generated time, market indicators and known SKUs after
download; the visible selector alone does not prove the export's marketplace.
Quarantine ambiguous exports from conclusions and resolve exact SKUs in the current
market's inventory UI when appropriate. Historical reports may establish model
identity with their date stated; they do not establish current stock or parentage.

Join ASINs to client SKUs, model/category, pack and variant evidence. A LEGO or other
licensed title can belong to the client's assortment; neither its title nor Amazon's
brand picker is sufficient to include or exclude it. A retail search result alone
is discovery evidence, not assortment proof. Use the local delivery postcode helper
before reading retail pages so destination settings do not create false stock claims.

Keep sellable, reserved, inbound, transfer, unfulfillable and unavailable units
separate. Preserve unknowns and offer status; do not double-count multiple reports.
Zero stock does not automatically invalidate a correctly matched product. State
stock dates and visibility effects separately. A narrowly authorized link correction
may reuse accepted identity evidence; do not silently label old stock figures fresh
or download an entire new catalog when that work is unnecessary.

## Correct the appropriate surface

**Product grids.** Audit both automated queries and saved manual selections on every
page. Breadcrumb queries can produce empty grids, while broad category terms can
return unrelated categories. Check the complete result set, not just the visible
cards. Use explicit verified ASIN lists when automated selection cannot enforce the
intended assortment. Grids should cover the matching category assortment beyond
the products pictured in Figma. Preserve valid variants and distinguish repeated
ASINs from similar-looking size cards or intentional parent/subcategory overlap.

Discover the current grid minimum, maximum and available modes; do not confuse
manual selection with an automated grid's pin list. If the verified list is too
small, report the gap without filler. If too large, present a deterministic grouping
proposal, such as an entry child per model/color, and retain full variant coverage
in the evidence. Do not silently simplify an approved exact list. Record rejected
ASINs individually. Preserve out-of-stock behavior unless changing it is authorized.
Reopen the editor after input settles; displayed counts can lag and bulk-entry
controls can appear to submit without persisting.

**Links.** Resolve Store page IDs and exact ASINs with a unique result. Set or remove
only the approved destination and required associated CTA fields. Preserve image,
crop, text, layout and other content. Inspect both device tabs; separate mobile
artwork can share a destination. Reopen and verify both the editor and saved data.

**Images and crops.** Replace only the approved widget/breakpoint with the verified
asset. Bind local file hashes and intended crop/composition to the change. Select a
unique image-specific upload input within that editor. Read the slot constraints
from the current UI; keep the intended content visible and verify saved crop data
after reopening, alongside desktop/mobile rendering. A new media URL or a Crop click
does not prove the intended crop persisted. Preserve existing mobile artwork during
unrelated corrections; a same-ratio design is not permission to remove it. If crop
readback is unavailable or differs, report a verification gap instead of success.
Inspect persisted crop fields without entering crop-edit mode on a source/live
edition: opening Crop and then Cancel can still persist display-geometry metadata.
Opening that control belongs
inside the authorized draft. Compare natural-image crop coordinates separately from
editor zoom metadata, and disclose any incidental source changes without hiding
them through an unexplained baseline refresh.

**Other modules.** Inspect current UI capabilities before declaring an operation
impossible. Video upload support exists in the rebuild driver and has mocked tests;
current-account live compatibility requires an authorized draft canary. Scoped
updates do not gain video, hotspot or layout operations by analogy. Report the
observed UI, executor coverage and authorization separately.

## Verify and deliver

Reopen every changed editor and compare saved destinations, complete grid ASIN lists,
or image/crop state with the manifest. After reload, re-read all draft pages and the
source. Permit only the approved field changes and documented UI-derived companion
fields. Compare full content so unrelated image, layout, header, grid, navigation
and setting changes cannot disappear behind a successful tile check.

Check desktop and mobile previews for every affected page; use full-store preview
coverage for a full-store audit. A preview may render only an initial product subset
or make links inert. Combine visual QA with complete persisted lists and destination
readback; describe this limitation and do not claim shopper click-through verification.

Deliver source and draft names/IDs/status, row-by-row outcomes, tile/ASIN before and
after lists, dated stock and rejected/unknown identities, preserved-field checks,
and remaining work by surface. Support causes with saved build evidence; distinguish
observed defects from inferred causes and unknown actors or dates. Register generated
evidence under the workflow run and report file disposition. A report or screenshot
alone is not proof that an operation was applied.
