# Brand Store design

Published specification sources checked on 2026-11-12; recheck the selected slot
before export. Published API constraints do not prove current account UI availability.

Design a route from the shopper's need to the correct product or category. Freeze
the Store, marketplace, audience, page scope and destination evidence before layout.
Store implementation follows [amazon-catalog](../../amazon-catalog/SKILL.md) and its
[brand-store-updates reference](../../amazon-catalog/references/brand-store-updates.md).
This module prepares the approved design and build handoff; it grants no Amazon write.

## Module list and sizes

The [Amazon Ads Store specifications](https://advertising.amazon.com/resources/ad-specs/stores)
publish the sizes below in pixels. Recheck the selected current builder slot before
export; a historical Figma preset must not override it.

| Module | Published asset size or layout |
| --- | --- |
| Header | Hero minimum 3000 x 600; logo 400 x 400 |
| Image | Desktop minimum: full 1500 x 20, large 1500 x 1500, medium 1500 x 750, small 750 x 750 |
| Custom-mobile image | Full/large/medium minimum 1680 x 20; small 750 x 750 |
| Image with text, overlay | Full 3000 x 1500; other sizes as large/medium/small above |
| Image with text, adjacent | Full/large 1500 x 1500; medium/small 750 x 750 |
| Shoppable image | Full/medium 1500 x 750; large 1500 x 1500; small 750 x 750 |
| Gallery | Images minimum 1500 x 750 |
| Video | Cover full/large/medium 3000 x 1500 / 1500 x 1500 / 1500 x 750 |
| Background video | Full/large/medium; inspect current video constraints |
| Text, product, product grid, best sellers, recommendations, featured deals | Native responsive content; no custom raster preset |

The internal Store playbook used a 3000 x 600 desktop banner and 1688 x 338 mobile
banner. Keep these as working presets only after confirming the header's current
device controls. The published image-tile mobile minimum above does not establish a
mobile-header size. Keep important content in the central 70% of the desktop hero
as an initial crop guard, then inspect actual desktop and mobile previews.

## Select modules from their behavior

| Buying task | Design choice | Check before acceptance |
| --- | --- | --- |
| One creative with one destination | Image or image with text | Exact product or category link; mobile composition |
| Several pictured products with separate destinations | Shoppable image | Every pictured variant matches its hotspot; mobile crop and product affordance |
| Independently linked regions with custom mobile compositions | Split section of image tiles | Slices, spacing, seams and per-tile destinations |
| Explain a detail without a navigation action | Unlinked image or native text | No accidental product destination |
| Offer a category assortment | Product grid | Complete approved selection and mode, independent of current stock |
| Demonstrate motion or use | Video | Existing approved media and current slot constraints |

Inspect current module capabilities. The internal playbook observed one shared
creative for a shoppable image, with no independent mobile asset; that observation
requires rechecking. Do not promise custom mobile composition for that module
without current evidence. Prefer native image-with-text fields over embedded copy
when they preserve the accepted design and accessibility.

## Sequence and page structure

Start each page with its buying purpose, then provide a clear route to the relevant
range. A useful category page progresses through category promise, choices by need,
product/use proof, exact assortment and the remaining decision aid. A product page
can progress through core benefit, mechanism/detail, in-use demonstration, fit or
compatibility and related products. Rank sections by what the shopper needs next.
Keep informational sections unlinked and product pages at the approved navigation
level. Preserve pages outside scope.

Include at least one in-use scene and one lifestyle scene across the designed set.
Plan new photography or generation only within the accepted budget; do not create
promises from unrelated props or imply unavailable variants. Remove repeated
slogan strips that add no buying information.

## Brief for the copywriter

Provide the page tree, buying purpose per section, audience/language, selected
module fields and current limits, claim tier, approved facts with sources, exact
product/variant names, proposed proof and intended link destination. Request exact
headline, supporting copy, link text and alt text separately for each module/device.
The writer returns a field-labelled copy table with character counts and source
mapping. A category headline must describe the real assortment; a CTA must match
the destination.

Use benefits the product can support, evidence-led detail and short navigation
labels. Do not write prices, discounts, review claims, certifications, origin or
performance comparisons into art without the required support and placement check.
Leave live catalog values to native product modules. Do not invent copy to fill
an empty category or make a broad keyword result look like an approved assortment.
Reviewer copy edits return to the writer before the layout is updated.

## Figma presets

Create a page map and a separate frame group per page. Pair desktop and mobile
compositions by section ID. Start with the confirmed header and asset presets above;
for normal content images, use 3000 px-wide working canvases where useful, preserving
the chosen aspect ratio. The 20 px minimum is an upload floor, not a usable design
height. Use the client brand's fonts and palette.

Keep native copy and proof annotations editable; preserve product images as separate
replaceable assets. Use full-bleed scenes, visible depth and a large, fully visible
product when the section sells a product. Show the required product/use detail at
360 px without zooming. Keep focus labels, evidence, widget choices, destination
IDs and export instructions outside artwork. Annotate mobile crop and hotspot
positions explicitly rather than relying on a scaled desktop screenshot.

## QA and delivery gate

For every section and device, record: its buying reason; one proof element with
source; visible product bounding-box area/canvas area plus width/height percentages;
and the new decision information it adds after the preceding section. Compare
actual product share to the accepted concept target. Native text/navigation can
record 0% product share only with an approved purpose and concrete evidence; never
use that exception for an undersized product hero. The first section establishes
the opening decision. Record pass/fail and fixes per row. A failure blocks delivery.

Inspect full size and a 360 px mobile view, then inspect the assembled page for
legibility, crops, product identity, proof, sequence and scene coverage. Verify
all destinations against the pictured ASIN/variant or category. A matching image,
correct dimensions or successful export alone does not pass a Store design.

## Handoff and implementation boundary

Deliver approved direction and pilot decision, page/module order, exact Figma
file/node IDs and version, desktop/mobile asset mapping and hashes, copy, alt text,
ASIN/category destinations, hotspot positions, assortment evidence and conversion
receipt. Identify whether the request is a scoped correction or an approved page
rebuild. Include the source edition and proposed draft scope when known; the
catalog workflow verifies account, source, draft and saved state before any build.

Use amazon-catalog's brand-store-updates workflow to build the Store. It preserves
source pages, separates grid/link/image changes from rebuilds and verifies persisted
state alongside desktop/mobile previews. Publication, scheduling and moderation
submission remain with a person. This design handoff is not a live Store receipt.
