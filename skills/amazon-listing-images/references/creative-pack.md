# Creative pack

A creative pack turns a filled brief (`references/brief-template.md`) into the files a
later build session needs: facts, brand CI, frames, gated image copy, a claims record,
a shot list with render prompts and a design spec. A human checks the pack before
anything is rendered. Pack mode renders nothing, builds nothing and uploads nothing.

## When to use pack mode

Use it when the brief asks for a creative pack, or when copy, shots and layout will be
produced by different people or sessions and need one fixed source. Use the normal
concept mode of `SKILL.md` for a chat brief or a copy revision. In pack mode, search
existing POE archives before declaring POE unavailable; record the source gaps and their effect on the buying jobs in the research file below.

## Stages

Each stage writes its files before the next starts. The method lives where named.

| Stage | Method | Writes |
| --- | --- | --- |
| Intake | `references/brief-template.md`; settle claim tier, generation budget and human approver together; blocking gaps stop the pack | `brief.md` |
| Research | `SKILL.md` "From evidence to buying priorities"; live listing copy through `amazon-listing-capture` when installed; galleries as in "Live galleries" below | `work/shopper-insights.md` |
| Facts | `SKILL.md` "Inputs and scope"; read the label at full size and check the label itself, then one independent refuter compares every fact with the label | `fact-sheet.md`, `facts.json` |
| Brand CI | "Brand CI from the website" below | `ci-spec.md` |
| Concept | `SKILL.md` "Build the image sequence" | `frames.md`, `copy-skeleton.json` |
| Copy | `references/image-copy.md` | `copy.json`, `gate.txt` |
| Shots and design spec | `skills/amazon-product-photography/references/reference-intake.md`; "Design rules" below | `shot-list.json`, `design-spec.md` |
| Claims | `skills/amazon-seo/references/health-claims-compliance.md`; refuter protocol in `references/image-copy.md` | `claims.md` |
| Deliver | "Pack files" below | `pack.md`, then `DONE.json` |

A change request re-runs only the stages it affects and every stage after them that
reads their output, then bumps the pack version and rewrites `DONE.json` last.

## Research evidence

Research must produce `work/shopper-insights.md` before concept work. It contains:

- POE niche, marketplace, capture date, metric scope and source paths. Use
  `amazon-opportunity-explorer` to locate the existing evidence and its pCloud
  archive before requesting a new pull. Keep archived snapshots labelled with their
  dates; record the search locations and a specific gap if no evidence exists.
  Do not imply that competitor copy proves a product claim.
- Five relevant competitor galleries, analysed slot by slot, including MAIN.
  Record ASIN, source/capture date, slot order, buying reason, proof device,
  product prominence, scene type and what each slot adds. Supplied captures can
  satisfy this research; names or listing bullets alone cannot.
- A differentiation list: where this product can look different, the shopper
  uncertainty it resolves, the product evidence and the scene that can show it.
  Separate observed evidence from creative interpretation and missing proof.

Missing galleries or POE remain explicit research gaps. Stop before approving the
concept pack until the missing research is supplied or a person accepts the named
limitation; record that decision in `pack.md`. Never replace the research file with
unattributed notes in a frame table.

## Live galleries

`amazon-listing-capture` captures copy only. Capturing the live and competitor
galleries is live research (see the Browser line in `SKILL.md`): a public retail-page
read in the connected browser under the browser rules in `AGENTS.md`. Set a local
delivery postcode first (`tools/report-fetcher/marketplace-postcode.mjs`) and keep
the screenshots as evidence. When that route is not available, `pack.md` records the galleries as not
captured, a flagged assumption.

## Brand CI from the website

- Fetch the brand's home page, the product page and one content page, and the
  stylesheets they link.
- Read colour and font-family values from those stylesheets and inline styles, not
  from screenshots, and record each hex value with the selector it came from
  (headings, body text, buttons, backgrounds). Mobile rules come from the media
  queries. A value set only by script or seen only in an image is marked unverified.
- Quote the tone exactly: three to six short lines from headlines, product copy or
  the about page, each with its URL. These become allowed patterns for the writers.
- Note product imagery: light, backgrounds, props, how people appear, if at all.
- Record each source URL and the capture date.
- Colours, fonts or a logo supplied in the brief win over the site. Note conflicts.
- Nothing on the website approves a claim. A site line that makes a claim goes into
  `ci-spec.md` as voice evidence only, never into copy.

## Skeleton

`copy-skeleton.json` lists every frame (`id`, `order`, `job`) and every text slot as
a key with `role`, `fixed`, `max_chars` and `text`. It may also carry
`approved_sf_lines`, `sf_keys` (the keys that may hold an approved line, whose frames
must also carry the disclaimer) and `optional_empty_keys`.

- **Fixed keys** (`"fixed": true`) hold exact text from the label or a decision:
  stat values, ingredient rows, the disclaimer. The gate requires them unchanged.
- **Free keys** (`"fixed": false`) start empty and are what the writers fill.

Default `max_chars` for free keys: eyebrow 26, headline 44 to 52, subheadline 85 to
95, chip 30, stat label 18. Shorten a limit when the layout needs it; raise one only
with a reason in `frames.md`.

## Copy gate

`scripts/check_copy.py` checks the mechanical layer. Run it from the skill folder and
give the pack files by their path:

`python3 -I -B scripts/check_copy.py <pack>/copy.json --skeleton <pack>/copy-skeleton.json --profile references/claims-profiles/us-dietary-supplement.json --facts <pack>/facts.json`

Use `references/claims-profiles/amazon-standard.json` only for a product in no
regulated category; the profile follows the category, not the claims posture
(`references/image-copy.md`).
`facts.json` holds the product-specific part: product name and stem, allowed numbers,
extra banned words, unit values and pattern rules; its schema is documented in the
script. `scripts/selftest_check_copy.py` proves the gate on an invented product.
Exit 0 means no errors. The output starts with the command, the working folder and
the sha256 of every profile file in the extends chain; `gate.txt` keeps the full
output of the final run.

## Pack files

| File | Holds |
| --- | --- |
| `pack.md` | The one page the human checks: identity and sources; claims posture; frame table with job, scene and headline; the gate line; refuter counts by severity; decisions needed (risk acceptances, exceptions); assumptions; holds before upload; the command that pulls the pack into `output/<client>/catalog/<date>-listing-images-<product>/pack/` |
| `brief.md` | The filled brief as received, plus answers to blocking questions |
| `fact-sheet.md` | Every label fact with where it sits on the label and how it was verified; label errors or gaps found, each as a hold; the product's physical look and the photo it comes from |
| `facts.json` | The gate's per-product facts |
| `ci-spec.md` | Palette with roles and hex, type families and weights, tone quotes, imagery notes, logo file, sources and dates |
| `work/shopper-insights.md` | POE archive sources and gaps, five slot-by-slot competitor galleries, and supported visual differentiation |
| `frames.md` | Frame table: buying job, evidence, scene, text slots, decisions |
| `copy-skeleton.json` | The skeleton above |
| `copy.json` | The final copy, the skeleton with every free key filled |
| `gate.txt` | Final gate output with its exit code, starting with the command line and the profile hashes the gate prints |
| `claims.md` | Posture, every refuter finding with key, quote, severity and resolution, and remaining HIGH items |
| `shot-list.json` | `references`: each input file with a role (`P1` product front, `S1` style, `C1` composition; see the reference-intake roles). `slots`: `id`, `frames`, `aspect_ratio`, `reference_inputs`, `prompt`, `scene_type` and an `acceptance` check specific to the shot; a generation budget with currency/spend cap, maximum attempts and repair allowance, including zero when using supplied assets |
| `design-spec.md` | Per-frame layout over the photo, type, colour, depth and the checks below |
| `DONE.json` | Written last: job id, pack version, sha256 per file, gate exit code, claims profile name with the sha256 of each profile file in its extends chain, HIGH count. Its presence is the completion signal; a pack without it is unfinished |

## Shots and creative approval

The shot list must include at least one in-use scene showing the product used as
instructed, and a separate lifestyle scene showing the buyer and a relevant setting.
A hand holding a pack without using it does not satisfy in-use; a generic studio
still does not satisfy lifestyle. Neither scene may imply an unapproved result.
Map both to frame IDs. If claims or missing assets prevent either, stop and give
the person the scene options and conversion cost rather than quietly dropping it.

Record the generation budget before production: new scenes versus reusable supplied
photos, attempt cap, spend cap and repair allowance. Zero is valid when suitable
assets already exist. A budget is a ceiling, not permission to spend or a universal
scene count; obtain the task's tool authorization before paid generation. Stop at
the cap and request a decision if required scenes still fail.

A person approves the creative direction on one representative pilot frame before
expanding the gallery. Record who, when and the exact version. The agent driving
the job cannot approve it. A person's explicit waiver is recorded in the receipt
and delivery note; prior approval of that same direction remains valid.

## Design rules

Use the following photo-led structure for secondary frames, adapted to the client's
own brand. It does not prescribe another product's colours or typefaces:

- Full-bleed scenes with space planned for type; avoid isolated cutouts on empty
  panels as the default. Light, perspective and contact shadows create depth.
- Stack eyebrow, headline and accent line as one readable hierarchy. An accent
  belongs to the headline's idea, not a second unrelated promise. Supporting copy
  stays subordinate. Use the client's type, palette and voice.
- Give every frame one focal proof element: a sourced number with its qualifier,
  a visible demonstration, a labelled material/detail, a readable facts panel or
  another product-specific piece of evidence. Decorative icons alone are not proof.
- Keep the product large and fully visible, with its silhouette and identity clear
  at phone size. Compose the scene around it. Detail views may add a close-up while
  retaining a fully visible product anchor; record the prominence target per frame.
- Supporting graphics are allowed: editable cards, chips, badges, diagrams, leader
  lines and annotations can make the proof readable. A design spec may not ban
  supporting graphics as a class. Use them when they explain the evidence, with
  no invented seals or unsupported claims; do not obscure the product or hands.
- Overlays and restrained cards may support text contrast and separation. Keep
  photographic shadows consistent and avoid flat repeated panels that add no job.

Amazon's mobile gallery shows a 2000 px image at about 360 to 414 px wide, a scale of
about 0.18 to 0.21. Minimums on the 2000 px canvas:

| Element | Minimum | On a phone |
| --- | --- | --- |
| Headline | 150 px | 27 px |
| Stat numerals | 260 px | 47 px |
| Stat unit or qualifier | 56 px | 10 px |
| Subheadline | 64 px | 12 px |
| Eyebrow (capitals, wide tracking) | 48 px | 9 px |
| Chips and labels | 56 px | 10 px |
| Ingredient doses | 52 px | 9.5 px |
| Supplement Facts title | 84 px | 15 px |
| Supplement Facts rows and column heads | 52 px | 9.5 px |
| Fine print (disclaimer, footnotes, caution) | 40 px | 7.5 px |

- When text does not fit at these sizes, widen the box, reflow or add a line; the
  copy is fixed once gated.
- Contrast is at least 4.5:1 for text under 150 px and 3:1 for larger text, measured
  against the photo pixels behind it. Add or strengthen a gradient overlay to get there.
- The words come only from `copy.json`. MAIN carries no text and no added shapes.
- Focus labels that name each frame's job sit outside every frame, so they are never
  exported and never part of the copy readback.
- When a frame carries a structure/function line, the full disclaimer is on that same
  image. A brief decision may extend it to every frame that shows the pack.
- Keep text clear of faces, hands and the product label.
- The label shows crisp and as printed wherever the product is visible. When the
  product is too small for its fine print to read correctly, the spec asks for the
  fine print softened like depth of field with the brand and product name crisp.
- MAIN shows the product on pure white with a natural contact shadow.
- Each secondary frame gives the shopper a reason to buy. A frame that only
  identifies the product is weak; give it a benefit or merge it into another frame.
- Final checks: read back every text layer against `copy.json`, then view each frame
  downscaled to 360 px wide and read every line without zooming.

## Conversion gate

Plan the rubric in `frames.md` and apply it to the actual final exports at 360 px
and full resolution. Copy readback, dimensions, hashes and contrast are necessary
technical checks; they never pass a gallery on their own.

| Field per frame | Pass condition |
| --- | --- |
| Buying reason | A specific supported benefit or uncertainty resolved for this shopper; identity or a generic adjective alone fails a secondary frame |
| Proof element | Name the one focal visible proof and its fact/source; it substantiates the reason rather than merely decorating it |
| Product share | Record the visible full-product bounding-box width and height as percentages of the frame, plus whether the silhouette is complete; compare with the frame's planned prominence target and confirm recognition at 360 px. A small/cropped product or a missed target fails; revise layout or obtain a person's explicit target revision with its conversion cost |
| Increment | State what new buying question this frame answers over the previous frame; a repeated beat fails and must be replaced or merged |

MAIN is assessed for faithful recognition, visible contents, product share and the
current Amazon main-image rules. Its visible shipped product is its proof; it needs
no added headline or sales graphics. Its increment is the opening recognition job.

Record each field as pass/fail with an evidence path and a reason, then an overall
result per frame. Any failed field blocks delivery of the gallery. Fix the frame
and recheck its neighbours; do not average away a failure or describe a failing set
as delivered. Pack-mode rubric entries are planned checks, never proof that an
unrendered gallery passed. The production receipt records the actual results and
the in-use/lifestyle frame IDs, budget usage and creative approval or waiver.
