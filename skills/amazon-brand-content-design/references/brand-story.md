# Brand Story design

Published specification sources checked on 2026-11-12; recheck the selected slot
before export. Published API constraints do not prove current account UI availability.

Design a carousel that gives shoppers a reason to trust the brand and find a relevant
next product. Read the accepted claim tier, brand evidence and intended ASIN scope
before planning cards. Do not reuse product-specific claims across the whole catalog.

## Module list and specification status

The [Amazon Brand Story API reference](https://developer-docs.amazon/sp-api/docs/a-plus-brand-story-modules)
provides the following published API constraints. These establish design presets;
the person's current Seller Central editor must confirm the matching UI slots.

| Module | Image minimum, px | Copy ceiling |
| --- | --- | --- |
| Image with logo, required once | Desktop 1464 x 625 | Title 30; description 135 across at most 3 rows |
| Media asset | 362 x 453 | Title 30; description 135 across at most 3 rows |
| About | Logo 315 x 145 | Title 30; slogan 450 across at most 10 rows |
| Four ASIN | Each image 166 x 182; exactly 4 products | Required title 30; optional Store ID |
| Questions | No image | Exactly 3 pairs; question 70; answer 200 across at most 3 rows |

The [Amazon Quick Start Guide](https://m.media-amazon.com/images/G/01/BX_Marketing/2023/A_Brand_Story_Quick_Start_Guide_06a-4-21-2023.pdf)
allows 1 to 19 cards and explains the Store link and ASIN assignment. This is a
published older guide, not a check of the current account.

Unverified: the mobile-background size, file byte limits/formats, exact responsive
safe zones and current account eligibility. The current fetched API field table
lists only the desktop hero size; its example includes a mobile image without a
size constraint. Do not infer dimensions from example crop coordinates or use
unconfirmed secondary-site numbers as requirements. Stop production of affected
exports until the person supplies current slot constraints or an authorized read
confirms them. Other research and copy can continue.

## Sequence

1. Establish the brand's buyer-relevant promise in the background and first card.
   Keep essentials clear of the carousel overlay and test its initial position.
2. Show the documented origin, design choice or sourcing practice that earns trust.
3. Demonstrate one distinct product principle in a real use or lifestyle scene.
4. Resolve a brand-level objection with an evidence-backed answer or detail.
5. Offer relevant catalog choices and the matching Store destination when supported.

Choose only cards with new information. The maximum is a capacity limit, not a
reason to fill every slot. Include at least one in-use and one lifestyle view in
the planned set as separate scenes; one photograph cannot count for both.
Avoid repeating the product A+ sequence immediately below the carousel.

## Brief for the copywriter

Send the writer one self-contained brief: audience, language, approved brand facts
with sources, selected claim tier, prohibited implications, chosen card order and
module fields, limits from the table, and the visual proof planned for each card.
Request exact field-labelled copy and character counts, including punctuation and
spaces. Ask for alternative short titles when mobile fit is uncertain.

Each card needs one concrete reason to consider the brand, supported by a named
fact, product detail or visible demonstration. An origin story needs supplied
facts; a mission statement alone cannot prove a product benefit. Avoid invented
founder quotations, reviews, seals, testing, sustainability or origin claims.
Provide exact approved ASINs and Store identity separately from shopper copy.
Do not add pricing, promotions, off-Amazon destinations or instructions to contact
the brand. Check the current account's content rules before handoff.

Route reviewer copy changes back through the writer. Freeze the approved wording
before layout; the designer may change line breaks without changing meaning.

## Figma presets

- Create a separate draft section, preserving the existing approved story. Name
  assets by card order, module and device. Keep focus labels and sources outside
  export bounds.
- Use the confirmed image dimensions above as asset frames. Make a separate
  assembled desktop carousel mockup; do not mistake the asset frame for the UI's
  complete card size. The text-only module uses a labelled layout mockup until
  the current UI geometry is known.
- Build the mobile hero preset only from a confirmed mobile slot. Review all
  cards in a 360 px viewport mockup with the carousel overlay, text and intended
  first-card position; do not shrink the entire desktop background into a phone.
- Keep copy native, logos and product images separately replaceable, and proof
  graphics editable. Use the client's own type and palette. A scene should show
  depth and a recognisable, fully visible product where product imagery is used.

## QA and delivery gate

Record one receipt row per card and device, plus the background: buying reason;
one supported proof element with source; product share of the frame and visibility;
what it adds over the preceding card; pass/fail and correction. Measure product
share as its visible bounding-box area divided by canvas area, and record width
and height percentages too. Agree targets in the concept pack, then compare the
render to those targets. For a text-only or logo-only card, record 0% and the
approved brand-trust purpose; it must still supply concrete proof and new value.
The first card records the opening buying question rather than a prior-card delta.

A failed or missing rubric row blocks delivery. Review at full size and in the
360 px mobile mockup: copy, product identity, supported implications, legibility,
overlap by carousel cards, crops, card order, links and incremental value. Technical
checks of layers, text and dimensions cannot pass the content by themselves.

## Handoff

Return the approved concept/pilot decision, claim tier and evidence, exact copy,
ordered module map, Figma file and node IDs, desktop/mobile assets, confirmed slot
constraints, alt text, ASIN assignment list and Store destination, source-to-export
mapping and rubric receipt. List unverified specifications beside affected assets.
Uploading, assigning ASINs, submitting and publishing Brand Story stay with a person.
Do not call a Figma mockup an uploaded or live Brand Story.
