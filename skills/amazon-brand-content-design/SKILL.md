---
name: amazon-brand-content-design
description: "Design Amazon A+ content, Brand Stores and Brand Story from product and shopper evidence. Use for module strategy, copywriter briefs, Figma layouts and conversion QA; upload and publication follow the format handoff."
---

# Amazon brand content design

Browser: Mixed (supplied evidence and local design planning need none; public specification research uses web tools; Store execution follows amazon-catalog's CDP route).

Turn verified product facts and shopper evidence into a format-specific concept
pack, copywriter brief and editable design. The job owner selects the deliverable,
briefs a separate copywriter, judges the returned copy and owns the final QA.
Explicit user scope wins over defaults here; it never waives claims or action gates.

## Choose the format

Load only the module for the requested deliverable.

| Deliverable | Reference | Completion boundary |
| --- | --- | --- |
| A+ content | [references/a-plus.md](references/a-plus.md) | Approved desktop/mobile modules and upload manifest; a person uploads and submits |
| Brand Store | [references/brand-store.md](references/brand-store.md) | Approved page designs and build handoff to amazon-catalog; a person publishes |
| Brand Story | [references/brand-story.md](references/brand-story.md) | Approved background/cards and upload manifest; a person uploads and submits |

Listing galleries use `amazon-listing-images`; photo-only work uses
`amazon-product-photography`. Sponsored Brands video briefs use `amazon-sponsored-brands-video-briefs`. Store
catalog corrections and builder operations use `amazon-catalog`.

## Intake and research

Read existing evidence first. Establish product/variants, marketplace, language,
format and account capability (Basic/Premium where relevant), buyer, objective,
page/ASIN scope, source assets, brand CI, claim evidence and a human approver.
Reuse relevant `work/shopper-insights.md` or create it using the research method in
`skills/amazon-listing-images/references/creative-pack.md`: archived POE through
`amazon-opportunity-explorer` and pCloud where available, five competitor galleries
slot by slot, differentiation and explicit source gaps. Add format-specific
competitor modules/pages rather than treating a listing gallery as the whole page.

Set the claim tier with its conversion cost using
`skills/amazon-listing-images/references/image-copy.md`. If it removes the primary
benefit, stop at intake and present the person's choices before design. Record the
generation budget, including zero for supplied assets, and required in-use and
lifestyle scenes. Photo generation needs its own authorization; a design request
alone does not authorize paid tools.

Verify the current selected module's published specs and record URL, check date,
asset dimensions, copy limits and mobile behavior. Historical presets below are
starting points. Unverified limits block upload readiness for that asset; prepare a
labelled draft and request the person's current builder requirements without
inventing a specification or taking over the upload.

## Concept, copy and build

1. Create the sequence with one buying job, source-backed proof element, product
   prominence target and incremental contribution per frame/module. Include at
   least one instructed in-use scene and a separate relevant lifestyle scene.
2. Present the concept pack and one pilot for a person's approval before expanding
   production. Record approver, date, version or explicit pilot waiver. The agent
   driving the work cannot approve it. Reuse approval already given for this scope.
3. Send a self-contained brief to the separate copywriter: module IDs/order, jobs,
   audience, verified facts/source IDs, allowed exact claims, prohibited implications,
   brand voice examples, language, text slots/limits and return schema in the format
   module. Fixed facts and disclaimers stay fixed. Do not assume authority to message
   a person or an external service merely because a writer handoff is needed.
4. Judge copy for buying relevance, voice, source fidelity and policy. Route edits
   back through the writer; recheck claims and any applicable mechanical copy gate.
   The listing-image gate's schema is not an A+ or Store field validator. Unsupported
   claims block the affected module even when they fit a character limit.
5. Build editable Figma frames from the accepted version using the installed Figma
   skills and `amazon-image-production` layout mechanics. Keep copy and supporting
   graphics editable, source photos separately replaceable and notes outside exports.
   Use client CI and preserve existing approved content. Inspect every device frame.

## Conversion QA and receipt

Apply the conversion rubric in
`skills/amazon-listing-images/references/creative-pack.md` to every final module,
card and device adaptation, alongside each format's technical checks. Record:

- Buying reason and the shopper uncertainty it resolves.
- One visible proof element, its source and what it substantiates.
- Product share as full-product bounding-box width/height percentages, complete
  silhouette, target and recognition at 360 px. For navigation/logo/brand-only
  modules record a justified role exception and its linked product module; it cannot
  excuse a product-benefit module with a small/cropped product.
- What the module adds over the preceding module; an opener establishes its job.

A failed field blocks delivery. Do not average scores or call a technically correct
set passed. Fix and recheck affected neighbours and both device views. The receipt
binds results to export hashes and Figma nodes, records scene IDs, budget usage,
human approval/waiver, copy and claims versions, specification verification and
outstanding holds. The format reference adds its handoff fields. A held draft is
labelled held; successful design delivery never implies publication.

## Installation boundary

The canonical folder stays in this repository. The existing company setup
`amazon-operator` role discovers Amazon skills from this repository's skills root
and links them into the runtimes that operator uses; keep that role gate and use
symlinks rather than copies. This skill does not join the two-skill selective
designer installation. Repository authoring does not install runtime links or
change another checkout; run the established role bootstrap after the PR is merged
when installation is authorized.
