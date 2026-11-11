# Editable Figma production

The design deliverable is a frame with native text, separately replaceable image
assets, and editable shapes/annotations. A background photograph remains a bitmap;
do not describe every pixel as editable. Preserve real product cutouts separately
when this improves fidelity and reuse.

## Capability and target

Inspect the actual available Figma tools. On the implementation machine checked
06.09.2026, file creation, asset upload, JavaScript design editing and screenshot
tools were exposed. No client file was accessed and no live layout was tested
while authoring this skill. Tool visibility is not proof of write permission.

For an existing file, inspect its destination page, current layouts, fonts and
styles before writing. Prefer an unused draft area; do not replace approved work.
For a new file, load the available `figma-create-new-file` skill before file creation.
Before JavaScript editing, load `figma-use` and its required API references. Load
additional Figma skills when their actual workflow applies; do not turn a listing
image into an app-interface or full design-system project.

The current connected asset-upload tool accepts local raster bytes through a
single-use upload URL and can place them as an existing node's image fill. SVGs
import as editable vector trees. Discover current size/format limits from the
tool schema. Do not assume a local filesystem path works as a Figma image URL or
call an unsupported remote-image import method. Preserve destination and node IDs.

## Layout work

1. Inspect the reference images and read the approved copy. Extract a compact
   visual direction with type hierarchy, palette, spacing, image treatment and
   annotation style. Use client brand assets, not the agency brand by default.
2. Set a representative frame at the requested export dimensions. If unspecified,
   use a clearly labelled working canvas, e.g. 2000 by 2000 for a square draft;
   this is a design starting point, not a claim about Amazon requirements.
3. Place photos with correct proportions, masks and crops. Match background
   perspective, lighting and contact shadows to the product when compositing.
   Keep operational source notes outside exported artwork. For MAIN, place the
   crisp product cutout on pure white and keep its natural contact shadow.
4. Add real text nodes for the approved headline and optional supporting copy.
   Load the actual available fonts, preserve readable line breaks, and use
   auto-layout for related text/icon groups. Keep supporting diagrams and
   dimension arrows editable and grounded in the product specification.
5. Retrieve a rendered screenshot and inspect it. Check the underlying text and
   layer structure as well; a good-looking preview does not prove editability.
   Fix clipping, weak contrast, accidental crops and label errors before expanding.
   Text effects can tint the product: a headline glow over a cap once turned it
   grey. After typography, compare the product's colours with the reference.
6. Reuse a few layout styles across the remaining frames while giving each image's
   buying job an appropriate composition. Repeated template structure is useful
   only while it communicates the content well.

Human feedback is most valuable on the representative direction and final selected
gallery. Gather it when a material aesthetic choice is unresolved. Do not impose
an extra approval loop on already accepted direction or routine reversible edits.

## Build from a creative pack

A creative pack from `amazon-listing-images` already holds the accepted copy,
claims record, shot list and design spec. Build from it in this order:

1. Pull the pack into
   `output/<client>/catalog/<date>-listing-images-<product>/pack/` and check every
   sha256 value in `DONE.json` against the pulled files. A missing file or a
   mismatch stops the build until the pack is pulled again.
2. Record the human approval of the pack (who, when, which pack version) in the
   run note before rendering.
3. Re-run the gate: the local `amazon-listing-images` `scripts/check_copy.py`
   with the claims profile named in `DONE.json`, on the pack's `copy.json`,
   `copy-skeleton.json` and `facts.json`. The paths recorded in `gate.txt` belong
   to the machine that made the pack. The profile hashes it prints must match
   those in `gate.txt` and `DONE.json`; a difference means the profile changed
   since the pack, and the build stops until the pack is gated again. The errors
   and warnings must match `gate.txt`. Gate any later copy edit again before it
   goes into a frame.
4. Render the photos with `amazon-product-photography` from `shot-list.json`,
   inside the generation budget set for that task.
5. Build the frames in Figma from `copy.json` and `design-spec.md`, following
   the layout work above.
6. Read back every text layer and compare it with `copy.json` character for
   character, then view each frame at 360 px wide for the mobile check.
7. Uploading the finished images stays with `amazon-flatfilepro`.

## Review and fix rounds

Gates check words and numbers, not pictures. Before handoff, have a reviewer who
did not build the gallery inspect every frame at full size and at phone size.
Typical findings: copy that contradicts what the picture shows, wrong numbers on
a small product, pseudo-text along an edge, semi-transparent objects, broken hand
contact, colour casts. Have a second agent try to refute each finding, and fix
only the ones that survive.

Fix one defect at a time; when delegating, give each defect its own worker. Check
every fix twice: once that the defect is gone, and once that nothing around it
changed. Allow one repair round per defect, then finish it by hand or name it as a
decision. After the last fix, run a regression check on the final exports against
the previous round, and keep before and after images for every retouch.

## Final checks and handoff

- Compare a small preview, roughly 320-400 px wide, with the full-resolution view.
  This is an internal readability check, not a fixed marketplace specification.
- Verify frame order/count, real text contents, font substitutions, layer structure,
  source variant, crops and actual export dimensions.
- MAIN: every edge pixel is pure white (#FFFFFF), the product fill meets the
  current first-party main-image rule, and the export is PNG, because JPEG
  compression leaves visible ringing on white.
- Read the gallery the way a reviewer will: label crisp and correct wherever it
  shows, MAIN with a natural shadow, frames with depth rather than flat panels,
  the gallery size the brief asked for, and a reason to buy on every secondary frame.
- Return the file/frame links, preview and export paths where requested, plus the
  remaining retouch or human decision. Claim success only for inspected artifacts.

If Figma is unavailable, deliver a self-contained layout specification and source
assets with exact copy, positions/proportions, type hierarchy and reference mapping.
Call it a handoff, not a Figma design. If only the target link is missing, prepare
the assets and representative composition plan while that detail is unresolved.
