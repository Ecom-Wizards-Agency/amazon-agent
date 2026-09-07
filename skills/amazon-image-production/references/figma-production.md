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
   Keep operational source notes outside exported artwork.
4. Add real text nodes for the approved headline and optional supporting copy.
   Load the actual available fonts, preserve readable line breaks, and use
   auto-layout for related text/icon groups. Keep supporting diagrams and
   dimension arrows editable and grounded in the product specification.
5. Retrieve a rendered screenshot and inspect it. Check the underlying text and
   layer structure as well; a good-looking preview does not prove editability.
   Fix clipping, weak contrast, accidental crops and label errors before expanding.
6. Reuse a few layout styles across the remaining frames while giving each image's
   buying job an appropriate composition. Repeated template structure is useful
   only while it communicates the content well.

Human feedback is most valuable on the representative direction and final selected
gallery. Gather it when a material aesthetic choice is unresolved. Do not impose
an extra approval loop on already accepted direction or routine reversible edits.

## Final checks and handoff

- Compare a small preview, roughly 320-400 px wide, with the full-resolution view.
  This is an internal readability check, not a fixed marketplace specification.
- Verify frame order/count, real text contents, font substitutions, layer structure,
  source variant, crops and actual export dimensions.
- Return the file/frame links, preview and export paths where requested, plus the
  remaining retouch or human decision. Claim success only for inspected artifacts.

If Figma is unavailable, deliver a self-contained layout specification and source
assets with exact copy, positions/proportions, type hierarchy and reference mapping.
Call it a handoff, not a Figma design. If only the target link is missing, prepare
the assets and representative composition plan while that detail is unresolved.
