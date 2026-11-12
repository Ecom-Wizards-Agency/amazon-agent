# A+ content design

Published specification sources checked on 2026-11-12; recheck the selected slot
before export. Published API constraints do not prove current account UI availability.

Build a sequence that explains the product, proves its relevant advantages and
resolves purchase barriers. Confirm Basic or Premium access and selected module
slots before choosing canvas sizes. A six-module plan needs Premium capacity; do
not compress it into Basic by quietly dropping the buying argument.

## Module list and sizes

The [Amazon A+ overview](https://sellercentral.amazon.com/help/hub/reference/external/G202102930?locale=en_us)
lists five Basic and seven Premium placements. Availability and field limits must
be confirmed in the person's current A+ Content Manager. Keep Basic and Premium
modules in separate documents.

The [Amazon Standard template guide](https://m.media-amazon.com/images/G/35/sp-marketing-toolkit/Sellerfacingguides/BO/Standard_A_Module_Templates.pdf)
provides these published image sizes in pixels. It does not settle every editor
variant; use current slot readback when a selected module differs.

| Standard module | Published image size |
| --- | --- |
| Single Image & Sidebar | 300 x 400 main; 350 x 175 sidebar |
| Single Left / Single Right Image | 300 x 300 |
| Four Images & Text | Legacy PDF: 200 x 200 each; API minimum: 220 x 200 each |
| Comparison Chart | 150 x 300 per product |
| Four Image Highlights | 400 x 400 primary; secondary size unverified |
| Single Image & Specs Detail / Single Image & Highlights | 300 x 300 |
| Three Images & Text | 300 x 300 each |
| Four Images / Text Quadrant | 135 x 135 each |
| Image & Dark / Light Text Overlay | 970 x 300 |
| All Text / Technical Specifications | No image |

The [Amazon API examples](https://developer-docs.amazon/sp-api/docs/a-plus-content-examples)
give a 220 x 200 minimum for `StandardFourImageTextModule`, differing from the
legacy PDF's 200 x 200. Before choosing dimensions, explicitly match the selected
Four Images & Text module and image slot in the live builder and record its
constraints. Stop design for that slot until the match is confirmed.

The API examples also document Company Logo (600 x 180), Image Header with Text (970 x 600),
and Multiple Image Text (300 x 300 per highlight). These are additional catalog
entries, not permission to reinterpret a differently named legacy template. Match
the current selected module and its field limits before export.

The [Amazon Premium module reference](https://developer-docs.amazon/sp-api/docs/a-plus-premium-modules)
publishes the following image minimums. D/M means desktop/mobile; these are asset
sizes rather than the full rendered UI geometry.

| Premium module | Image minimum, px |
| --- | --- |
| Image Text | 800 x 600 |
| Full Background Image / Full Background Text | D 1464 x 600; M 600 x 450 |
| Four Column Images | 300 x 225 each |
| Dual Image Text | 650 x 350 each |
| Image / Navigation / Regimen Carousel | D 1464 x 600; M 600 x 450 per panel |
| Three Column Comparison | 300 x 225 each |
| Comparison Carousel | D 488 x 700; M 600 x 450 each |
| Comparison Scroller | 200 x 225 each |
| Hotspot Image / Hotspot Image Text | D 1464 x 600; M detail 600 x 450 |
| Text / FAQ / Tech Specs | No image |
| Video Text | Preview 800 x 600 |
| Hero Video | Preview 1464 x 600; video 960 x 540 |
| Video Image Carousel | D image/preview 800 x 600; M image 600 x 450 |

Do not invent an additional mobile image slot for modules without one. Select
existing approved video only when it solves a buying task; video production uses
its owning workflow. Unverified variants, byte limits and field constraints stay
in the specification gaps until confirmed for the selected module.

## Sequence

Use this six-module starting structure when the product evidence supports it:

| Order | Buying job | Evidence or visual |
| --- | --- | --- |
| 1 | Core benefit in the buyer's setting | Lifestyle hero with recognisable product |
| 2 | Most consequential functional advantage | In-use demonstration or measured detail |
| 3 | Explain why it works | Material, construction or mechanism close-up |
| 4 | Show everyday suitability | Distinct use or wardrobe/environment context |
| 5 | Resolve selection uncertainty | Fit, compatibility, dimensions or routine guide |
| 6 | Close with a reason to trust | Sourced brand/product fact and clear product view |

This structure takes the buying progression from a completed six-module apparel
set; product-specific facts, styling and comparison claims do not transfer. Change
order or combine modules when a different objection deserves priority. Every
module must add decision information; a repeated icon footer does not earn a slot.
For Basic, make a deliberate five-module sequence with complete buying coverage.

Include at least one in-use and one lifestyle scene. Record required assets and
accepted generation budget before commissioning any new image; existing faithful
photography may satisfy the need. A scene implies a claim, so check how the product
is used and what outcome it appears to promise.

## Brief for the copywriter

Give the separate writer the accepted concept, audience and language, product and
variant identity, source-backed benefits, claim tier, prohibited implications,
module sequence and buying job, visual proof and confirmed field limits. Request
exact field-labelled copy: eyebrow where used, headline, accent line, supporting
copy, proof label, disclaimer and alt text; include character counts for native
module fields. Keep embedded image copy distinct from Amazon's native fields to
avoid duplicating a headline in the finished page.

Each headline should make the practical buying reason clear. A material percentage,
dimension, routine or demonstrated fit can supply proof when supported. Preserve
units, qualifiers and serving bases. Ask the writer to explain the conversion
tradeoff when a claim restriction removes the primary benefit; follow intake's
human decision before drafting around it. Never invent a statistic, comparison,
review, test, certification, origin or efficacy claim. Carry operator-supplied
facts with their evidence status; they are not independently verified by layout.

Return reviewer copy changes to the writer. Freeze approved copy before building
all modules, retaining required qualifications and disclaimers at readable sizes.

## Figma presets

For the six-module photo sequence, use paired desktop frames at 1464 x 600 and
mobile frames at 600 x 450, only after matching the selected Premium slots. Name
frames by order, module and device. Start other selected modules from the asset
sizes in the table and model native UI text separately.

Adapt mobile composition rather than scaling a wide frame down. As a working
starting point on a 600 px mobile canvas, use headlines around 34 to 35 px and
supporting text at least 23 px, then read the actual render at 360 px. These are
internal design presets, not Amazon requirements. If exact copy does not fit,
reflow or return it to the writer.

Keep scene photographs raster, copy native, and supporting graphics editable.
Use the client's type and palette, full-bleed scenes where suitable, an eyebrow /
headline / accent hierarchy, one proof element and visible depth. Keep the product
large, identifiable and fully visible in product-led scenes. Preserve focus labels,
copy sources and production notes outside export bounds.

## QA and delivery gate

Record each module/device in the receipt: buying reason; one proof element and
source; product bounding-box area/canvas area plus width/height percentages; and
what it adds over the module before it. Compare actual product share and visibility
to the accepted concept target. A fit-guide detail may add a close-up
when it clarifies the fit, while retaining a fully visible product anchor at the
accepted prominence target; record both the purpose and product identity.
The first module states the opening buying question. Mark pass/fail and correction.
Missing evidence, a failed row or a redundant module blocks delivery.

Review every module full size and at 360 px, then inspect the assembled desktop
and mobile sequence. Check copy, proof, product fidelity, crops, labels, faces and
hands, readability, scene coverage and the sequence's incremental value. Verify
frame count and native text against the approved copy, image dimensions and source
mapping. Technical checks alone never pass A+ content.

## Handoff

Return the accepted pilot decision, claim tier, evidence and copy, selected Amazon
module map and confirmed slot constraints, ordered Figma file/node IDs, paired
assets, alt text, intended ASIN/variant assignments, source-to-export mapping and
per-module conversion receipt. Flag remaining specification gaps beside affected
assets. A person uploads A+ content, verifies the native desktop/mobile preview,
assigns ASINs and submits/publishes it. Delivering Figma frames is not publication.
