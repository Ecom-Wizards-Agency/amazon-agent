---
name: amazon-product-photography
description: "Create, edit and enhance product photos or write reference-based photo prompts. Use for packshots, lifestyle, usage and detail photos with FLORA, Nano Banana, Seedream, Higgsfield or Magnific. Does not design listing graphics or Figma layouts."
---

# Amazon Product Photography

Browser: Mixed (supplied assets and available provider MCP first; visual-editor work follows the workspace browser standard).

Produce photographic assets or ready-to-run photo prompts. This skill owns the
photos: packshots, lifestyle scenes, real-use depictions, detail views, background
edits, retouching and selective upscaling. Human art direction remains part of the
workflow. Do not add headlines, USPs, icons, comparison tables or Figma layouts.
Existing packaging print is part of the product and must remain faithful.

This skill can be installed on its own from the Amazon Agent repository. A full
operator setup, Seller Central and Figma access are not required. Use available authorized provider tools; browser
fallback follows the current workspace's browser guidance when present. Optional
downstream skills need not be installed for photo or prompt delivery.

## Inputs

Read the supplied product facts, photos and desired shot first. An existing image
brief can guide the shot, but is not required. Neither POE, listing copy, an ASIN,
a brand kit nor a Figma file is a prerequisite for photo work.

Use `references/reference-intake.md` for reference roles and the prompt packet.
Inspect actual images before claiming knowledge of their appearance. If only text
descriptions are available, produce a clearly provisional prompt or shot plan.

- Product references define the exact variant, proportions, label, color, material
  and included quantity. Style references never override these facts.
- Separate product identity, lighting/style and composition references. Name what
  to adopt from each, and resolve conflicts rather than blending them indiscriminately.
- One suitable photo can support its observed view. Request another angle only
  when the selected shot needs it; do not block all work on a missing photo library.
- Infer a reasonable direction from supplied examples. Ask only about unresolved
  choices that materially change the shot. Preserve already accepted art direction.

## Mode and provider

A prompt-only request produces prompts and does not launch generation. A generation
or edit request should produce inspected photo assets when the authorized tools
and references are available. Do not stop at prompts if execution is possible and
requested. If access is missing, deliver the usable prompt packet and identify the
specific missing connection without pretending to have generated an image.

FLORA is the team's preferred generation workspace based on the operator's results
with references, not a universal quality ranking. Respect an explicitly chosen
alternative. Read `references/providers.md` for the selected provider and
`references/model-guidance.md` for the selected model. Nano Banana and Seedream
are still-image routes; Seedance is video and does not belong in a photo job.

Distinguish official documentation, callable tools, authenticated access and a
successfully tested workflow. Discover actual model IDs, reference slots, upload
readiness and supported settings before executing. An image mentioned in the
prompt is not automatically uploaded. Never assume a web plan's unlimited allowance
applies to MCP generation. Stay within existing authorization and the bounded batch;
prepare exact inputs and cost before seeking any missing spending permission.

## Photograph, edit or generate

1. Choose a shot that communicates the intended use or visible detail. Specify
   subject placement, camera angle, lighting, background and realistic scale.
   Reserve quiet space for future text only when requested by the downstream brief.
2. Preserve usable real product pixels where practical. Generate supporting scenery
   separately when that improves fidelity. If synthesis changes perspective or
   interaction, compare the output against the actual product references.
3. Write the exact prompt with ordered reference roles, unchanged product details,
   the desired scene or precise edit, and required aspect ratio/resolution. Use
   actual provider controls rather than assuming that writing "4K" sets output size.
4. Establish a representative candidate before extending a series. For unresolved
   taste, show a small meaningful alternative. Continue accepted direction without
   adding another approval gate. Aim to reduce retouching and selection effort.
5. Iterate from the strongest candidate with a targeted change. Masks and reference
   controls are model-specific; preservation instructions alone guarantee nothing.
   After repeated identity drift, use the real asset or obtain the needed view
   instead of unlimited retries. Poll existing timed-out jobs before resubmitting.
6. Upscale selected assets only when useful. Preserve originals and inspect label
   text, texture and edges; apparent new detail may not be real product information.

Do not invent functional mechanisms, materials, effects, dimensions, pack contents,
certifications or claims through the image. An ordinary verified-use photograph
does not require an efficacy study, but cannot establish an untested outcome.
If producing an Amazon main image, verify current applicable first-party requirements.
A packshot draft is not automatically a compliant production-ready main image.

## Photo QA and delivery

Compare against the real product at full size and intended display size. Check
silhouette, label spelling, color, quantity, material, perspective, plausible
contact shadows and any hand/product interaction. Fix actual defects before calling
a result usable. Keep original and chosen versions with source/reference mapping,
model when known, prompt/settings, run IDs and output IDs.

For each requested photo deliver either:

- The actual photo/preview and file link, useful dimensions, review status and any
  remaining retouch; or
- A ready-to-paste prompt, ordered references, supported or explicitly unverified
  settings, desired output name and shot-specific acceptance checks.

Return the requested number of photos or identify missing outputs. Do not call a
prompt an image or a generated approximation an exact product photograph. Follow
workspace artifact/storage rules. Do not publish, send messages or open Figma for
photo-only work.

## Boundaries and references

- `amazon-listing-images` owns buying strategy, gallery order and copy.
- `amazon-image-production` owns graphic composition and editable Figma layouts;
  pass selected photos there only when the user also requests that work.
- `references/reference-intake.md`: photo inputs, reference roles and prompt example.
- `references/providers.md`: researched FLORA, Higgsfield and Magnific workflows.
- `references/model-guidance.md`: dated official model guidance and enhancement limits.
- `references/evaluation-cases.md`: maintenance-only photo-scope checks.
