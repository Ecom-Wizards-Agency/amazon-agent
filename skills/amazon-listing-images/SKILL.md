---
name: amazon-listing-images
description: "Create Amazon listing image concepts, sequence, exact copy, and visual directions from supplied product and POE data. Use for gallery strategy, Bildkonzepte, Bildtexte, or image-copy revisions; rendering and publishing are separate."
---

# Amazon Listing Images

Browser: None (analysis and writing use supplied evidence; requested live research follows its owning skill).

Turn product facts and Product Opportunity Explorer data into images that help a
shopper choose the product. Each image answers a material buying question through
a supported benefit, relevant detail, or visible demonstration. Create the brief
and exact copy; generate image assets only when requested.

This skill can be installed on its own from the Amazon Agent repository. Supplied
product and POE files are enough; a full operator setup and Seller Central access
are not required. Other Amazon skills are optional routes when installed and needed.

## Inputs and scope

The two required inputs are **product data and POE data**. Accept files, tables,
screenshots, pasted material, or existing accessible sources. Read supplied inputs
before asking questions. Reuse facts already confirmed in the conversation.

- Establish product/variant, marketplace, copy language and placement from the
  request and evidence. A new product need not have an ASIN. Explicit English-copy
  instructions win over a German marketplace default.
- Record whether product facts are label/spec verified, brand published, operator
  confirmed, or merely marketing assertions. Establish what is sold, quantity,
  intended use, meaningful features and support for proposed claims.
- Identify each POE niche, market, capture/update dates, metric labels and units.
  Use the relevant supplied search, review, rating-impact, return and purchase-driver
  tables. Missing tabs reduce confidence; they do not automatically block the brief.
- Brand guidance, assets, price, competitors and test results improve the work when
  available. Do not require DataDive, SQP, ads access, a fresh niche pull or brand kit.
- Ask only for missing information that changes product identity or prevents an
  accurate core concept. For an unsupported optional claim, use another supported
  argument and name the specific evidence that would strengthen the concept.
- Analyze the supplied snapshot with its dates and limitations. Do not impose the
  fresh-discovery workflow or a blanket cache-age gate on archive analysis.
- For copy-only revision or translation, retain accepted strategy, order and count
  unless the user changes them or evidence contradicts them. Do not restart research
  or rewrite unrelated listing fields.

## From evidence to buying priorities

1. **Describe the buying situation.** Infer awareness from queries, audience,
   placement and context. Amazon category-search traffic commonly compares solutions
   or products; branded repeat buyers may be more aware. Platform alone does not
   prove awareness. Cold social and retargeting can differ. Label an inferred
   audience as a working assumption.
2. **Find desired experiences and purchase barriers.** Search language informs
   intended use; reviews and returns expose expectations and disappointments.
   Include relevant minority needs when they can stop purchase, such as fit,
   compatibility, quantity or unsuitable use.
3. **Keep measures distinct.** Star-rating impact describes rating association,
   not conversion lift or proven cause. A topic's net impact is not a separate
   positive/negative-review score. Mention percentages retain their sentiment or
   return denominator; they are not percentages of buyers. Do not add overlapping
   themes or average overlapping niches into a fictitious combined sample.
   Purchase-driver estimates, when supplied, are another signal, not causal proof.
4. **Filter for this product.** Separate the primary niche from adjacent use cases.
   Insect-control reviews in a lavender niche do not establish a pillow-spray use.
   Category demand and competitor claims never prove our product's capability.
5. **Match motives to product evidence.** Prioritize arguments that matter to the
   shopper, resolve uncertainty, and have a credible product answer. Use judgment
   with a short reason; do not invent weights or conversion forecasts.

Keep a compact internal trail:

`Buying motive / objection -> source and scope -> supported product answer -> visual evidence -> copy`

Separate observed evidence, creative interpretation and proof still needed.
Do not invent customer quotations.

## Build the image sequence

- Give each image one primary buying job. Show the desired benefit and the most
  consequential relevant uncertainty early. Rank later images by their incremental
  contribution to the buying decision.
- Main-image recognition and click-through differ from secondary-image persuasion.
  Use a faithful product image as the main-image default, with no invented packaging
  text or added sales badges. Verify applicable first-party Amazon image rules
  before delivering production-ready specifications.
- Choose image count from the scope. Never automatically prescribe seven images
  or require brand, travel, gift, ingredient or comparison slots. Merge weak slots.
  Respect a requested count without padding repeated claims.
- Choose the visual that communicates evidence: product detail, scale, measured
  feature, lifestyle, actual use, contents, or supported comparison. A lifestyle
  scene makes a use case tangible; it does not prove efficacy.
- Translate broad "quality" themes into supported construction, material,
  formulation, fit or operation details, not a quality seal.
- A reason to choose us need not be exclusive. Call it a differentiator only when
  a like-for-like comparison supports it. Without competitor evidence, show our
  facts without an invented "ours vs others" table or superiority claim.
- Visual claims need the same support as text. Specify real demonstration setups;
  never fabricate tests, before/after results, review stars, certifications,
  materials, dimensions, quantities or included items.
- Showing verified intended use does not require an efficacy study. Photograph
  actual operation when useful; distinguish an ordinary application shot from
  claims about tested spray consistency, lasting effects or guaranteed results.

## Write exact copy

Use the installed `conversion-offers-and-copy` direct-response mode for persuasion
and `unslop` for natural prose. Awareness and the buying decision govern the opening,
not an automatic pain hook. If those skills are unavailable, the rules here suffice.

- Write finished copy in the requested language, not placeholders or instructions
  for the designer to invent it. Preserve the selected variant.
- Headlines express a concrete benefit, answer or product fact. Usually three to
  seven words work; clarity and necessary qualifications take precedence.
- Add a subheadline only when it adds information. Add short USPs only when they
  give distinct, relevant reasons to choose. Optional fields can be `None`.
- Carry a supported feature into its useful consequence without inventing the next
  outcome. Proven dimensions support fit decisions; an ingredient alone does not
  establish better sleep, pain relief or another physiological result.
- Claim limits should lead to another concrete argument, not a gallery of vague
  ritual slogans. Retain strong benefits when evidence supports them.
- Write naturally in English or German. Preserve factual limits in translation;
  do not strengthen a restrained claim. Follow explicit brand voice/formality.

For material claims questions use `amazon-seo` product-facts and compliance references
when installed. Otherwise check the supplied product evidence and relevant current
first-party rules directly; do not require a full Amazon operator setup. Apply the
actual category and marketplace, not blanket food/supplement rules. Check text and
implied visual claims internally. Missing optional proof must not block all draft copy.

## Deliver and review

For strategy requests, briefly explain buyer, priorities and order. For exact-copy
requests, lead with the copy. Give each image these four fields:

- **Headline:** exact customer-facing words, or `None` for the main image.
- **Subheadline:** exact words, or `None`.
- **USPs:** exact short items, or `None`.
- **What to show visually:** image type, subject, product position, demonstration
  or composition, and factual conditions the designer must respect.

Keep citations, data percentages, proof gaps and claims reasoning in a compact
internal note, separate from artwork copy. The designer must not resolve claims or
invent facts. If an asset is missing, give a feasible shot brief. Include only
relevant production restrictions, not a generic compliance appendix.

Before delivery:

- Every image adds a distinct reason, removes a distinct hesitation or answers a
  necessary product question. Remove duplicate jobs and copy repetition.
- Replace text that fits an unrelated product unchanged with something specific.
  Check headline/visual alignment and mobile readability.
- Verify variant, quantities, units, ingredient forms, denominators and each claim
  against evidence. Absence of data is not a zero score.
- Treat the sequence as a hypothesis unless tests establish performance. If asked,
  test a meaningful competing opening against conversion; assess main-image CTR
  and expectation-related returns/reviews separately.

Return a chat brief when requested. For documents or team handoffs follow workspace
delivery and artifact-registration rules; local-only paths are not team-accessible
delivery. Do not force external delivery or login for chat copy. Creating a brief
does not authorize listing uploads, campaigns, messages or publishing.

## References and routing

- `references/worked-example.md`: annotated lavender-pillow-spray example for
  reasoning/team onboarding, not a fixed sequence to copy.
- `references/evaluation-cases.md`: synthetic behavioral checks for maintenance;
  not required reading during client work.
- `amazon-opportunity-explorer` owns requested discovery/downloads. This skill owns
  image strategy/copy when product and POE evidence already exist.
- `amazon-listing-capture` owns requested live capture; `amazon-seo` owns titles,
  bullets and keyword workbooks. Do not silently expand an image brief.
- `amazon-sponsored-brands-video-briefs` owns SB video briefs.
- `amazon-product-photography` owns photo assets, retouching and photo prompts.
- `amazon-image-production` owns listing graphics and editable Figma layouts from
  this accepted brief and the supplied or selected photos.
