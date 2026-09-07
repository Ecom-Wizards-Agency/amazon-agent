# Model guidance

Research checked 06.09.2026. Capabilities below are vendor-documented, not a
comparative quality benchmark or a live account test. Recheck the selected
provider's model ID, reference limit and settings before execution. FLORA and
other hosts may expose fewer controls than the model developer's API.

## Nano Banana

Google identifies Nano Banana 2 with Gemini 3.1 Flash Image and Nano Banana Pro
with Gemini 3 Pro Image. Its current documentation distinguishes the Lite model,
which is not optimized for multiple references or sequential editing. Prefer
testing a reference-capable variant for this workflow rather than choosing Lite
only for speed. Use intent, subject, composition and photographic language; refine
the strongest result with small changes. These are documented recommendations,
not a guarantee of label or geometry preservation.

Source: [Google Gemini image generation](https://ai.google.dev/gemini-api/docs/image-generation).

Assign clear names to subjects/references, describe aspect ratio and output use,
and separate alternative directions when comparing candidates. Use the actual
tool controls for resolution when exposed; writing "4K" does not verify file
dimensions. Keep final sales typography editable even if generated text looks good.

Source: [Google DeepMind prompt guide](https://deepmind.google/models/gemini-image/prompt-guide/).

## Seedream for still images

BytePlus's 4.0/4.5 guide recommends coherent natural-language descriptions and
explicitly assigning what each input image contributes to editing or composition.
Use that foundation without copying old parameters to a new version.

Source: [BytePlus Seedream 4.0/4.5 prompt guide](https://docs.byteplus.com/en/docs/modelark/1829186).

Seedream 5.0 Pro's official examples include distinct material/color/base-image
references and sketches or marked regions for layout control. For this workflow,
try a simple composition sketch when a verbal layout remains ambiguous. Declare
that annotation marks are guidance, not final artwork. Source photos still define
the product. Do not assume generated layer separation yields native editable
Figma text or a faithful product cutout.

Source: [ByteDance Seedream 5.0 Pro introduction](https://seed.bytedance.com/en/blog/beyond-generation-it-understands-design-introducing-seedream-5-0-pro).

Reference count is version-specific: the currently indexed BytePlus tutorial lists
10 for 5.0 Pro and 14 for 5.0 Lite/4.5/4.0. Verify the executable endpoint; do not
hardcode a universal 14-image capacity. A smaller deliberately selected pack is
usually the starting experiment, not filling the maximum.

Source: [BytePlus image generation tutorial](https://docs.byteplus.com/api/docs/ModelArk/1824121).

## Seedance for motion only

Seedance is a video family, distinct from Seedream. The official 2.5 release
describes multimodal references and timestamp-based editing; its release-time
API availability is not proof of availability in today's chosen provider. When
motion is requested, specify reference roles, start state, simple action, camera
motion, duration and end state. Use the accepted still as identity/composition
guidance where supported. Check the product through the whole clip, not just its
first frame. A still-image request should not create a video job.

Source: [ByteDance Seedance 2.5 introduction](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5).

## Magnific enhancement

Magnific offers different upscaling approaches and controls for creativity,
resemblance and detail. Prefer a conservative fidelity-oriented trial for product
assets. Compare label lettering, texture and edges before retaining the result;
greater apparent detail can introduce invented material or packaging information.
Keep the original. Upscale the selected photo asset before final Figma typography,
rather than creatively enhancing an entire finished text-heavy layout.

Sources: [Magnific image upscaler](https://www.magnific.com/ai/docs/image-upscaler),
[Magnific creative upscaler API](https://docs.magnific.com/api-reference/image-upscaler-creative/post-image-upscaler).

## Evaluate by the actual task

With permission to compare, use the same product, shot and reference roles across
models. Compare identity fidelity first, then composition, realism, useful text
space, required retouching and time/credits per accepted asset. Do not announce a
universal winner from marketing examples. The useful measure is how much designer
work remains on an accepted image, not how many files were generated.
