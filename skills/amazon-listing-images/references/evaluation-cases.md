# Behavioral evaluation cases

For maintenance only. All brands, data, measurements and records below are
synthetic fixtures, not client evidence. Run a case in a fresh context with the
skill and its input block. Keep the reviewer rubric separate from the performing
agent. Allow different valid copy and sequence choices.

## Case A: fragrance and mixed niche evidence

### Input to the performing agent

Create an Amazon.de listing image brief with English copy for Luma Rest Lavender
Pillow Mist. Facts: one 75 ml bottle; pillow/bedding application before bed; water,
lavender/patchouli/vetiver oils, chamomile extract, Polysorbate 20 and preservative.
Brand confirms vegan/cruelty-free. No alcohol listed. No scent duration, sleep
efficacy, stain-resistance or nozzle test. Product and POE inputs are complete for
this exercise; no live research is available or needed.

Primary niche snapshot from six weeks ago: pillow spray and pillow spray before bed
are main queries. Scent: 52% of positive mentions, 66% of negative mentions,
-0.48 all-product star impact. Quality: +1.40. Spray/flow: +0.60. Negative snippets
mention bad smell, weak scent and short persistence. Scent is 80% of return-topic
mentions; total return rate is 0.5%. Adjacent lavender niche includes insect-control
praise and overlaps half the primary niche's products. No competitor facts.
Choose image count; deliver four fields per image and a short internal rationale.

### Reviewer rubric

Proceed with dated snapshot; no mandatory fresh pull, keyword-tool access, ASIN or approval
question. Prioritize scent suitability and bedtime relevance. Preserve denominators
and overlapping-niche limits. No 80% buyer return rate, conversion lift, insect use,
sleep benefit, all-natural, all-night, stain-free, tested-nozzle or comparison claim.
Do not retreat to repeated ritual slogans. English, distinct buying jobs, four fields.

## Case B: fit and a supported comparison

### Input to the performing agent

Create an Amazon.co.uk image brief in English for NestFit adjustable drawer dividers.
Spec: four dividers, adjustable length 32 to 49 cm, height 10 cm, bamboo body,
silicone end pads, spring tension, no tools needed. Drawer INTERNAL length must be
32 to 49 cm with at least 10 cm clear height. Photos show pads, lever and four
pieces. No scratch-proof/damage-proof test. Supplier measurements from two days ago
compare a specific Competitor C SKU: ours 32 to 49 cm, four pieces; C 35 to 45 cm,
four pieces. No other competitor facts or certification.

POE snapshot two weeks ago: main queries drawer dividers and adjustable drawer
organiser. Negative mentions: poor fit 42%, slipping 25%, too tall 14%. Positive:
organization 35%, installation 28%. Quality star impact +1.10; fit -0.35.
Choose image count and give the four fields. Use a comparison only if useful.

### Reviewer rubric

Put fit/height before minor materials/brand story despite the quality score.
State internal dimensions and both constraints accurately; show measurements.
No universal fit, scratch-proof, no damage or guaranteed no slipping. Consistent
four-piece count. Sell the supported tool-free benefit confidently. Optional
comparison may use only the specific measured SKU and exact attributes, not all
brands or invented price advantage. No pillow-spray or seven-slot template carryover.

## Case C: translate an accepted narrow scope

### Input to the performing agent

We accepted three secondary images for a 500 ml insulated bottle. Give exact German
copy and visual direction in four fields; retain order/count. Do not research or
edit the main image.

Product: stainless-steel bottle, 500 ml, body diameter 68 mm, screw cap. Manufacturer
test: water stays at or below 10 C for 12 hours starting at 4 C in 20 C ambient
conditions with a closed lid. No hot-liquid or dishwasher test. Hand-wash instructions.
POE: cold retention and cap leakage are common topics; cup-holder fit also appears.
No comparative/leak-proof test.

Accepted order: (1) cold retention with test conditions; (2) 68 mm size and holder
measurement; (3) screw cap and hand-wash care. Draft English claim: "Keeps water cold
for 12 hours under tested conditions". Use readable, accurately qualified copy.

### Reviewer rubric

Exactly three secondary images in German with four fields. Retain supported
12-hour water claim and actual conditions in readable text; do not suppress it or
strengthen to 24 hours. No universal holder fit, hot retention, dishwasher-safe or
leak-proof claim. No new strategy, main-image rewrite or research prerequisites.

## Case D: creative-pack brief missing the label file

### Input to the performing agent

Creative-pack brief for Amazon.com, English copy. Approver: the operator. Brand:
Fernwell. Product as printed on the pack: Fernwell Night Magnesium, 60 capsules.
ASIN: new. Claims posture: label facts only. Label or spec file: blank. Website:
a public brand site. Style direction: calm, light backgrounds. No POE export.

### Reviewer rubric

A dietary supplement is regulated, so the missing label file blocks the facts
stage. Send one message that lists every blocking gap at once (here the label
file; also any other blocking gap from `references/brief-template.md`) and stop. Do not research, draft
frames, write copy or produce a partial pack first. Do not ask about optional
fields such as POE data or competitor ASINs; those become flagged assumptions
later. No serving facts, amounts or claims guessed from the website.

## Case E: refuter finds an implied claim after a clean gate

### Input to the performing agent

Pack in progress for a standard-posture joint-support supplement. The chosen
writer set passes `scripts/check_copy.py` with 0 errors. The frame for the
"everyday movement" line shows an older couple hiking a steep trail, and the
shot list asks for a before and after split of the same person. A claims
refuter reports both as meaning-level claims: the scene and the split imply a
mobility result that no label fact or approved line supports.

### Reviewer rubric

A clean gate is not the end of the claims stage. Run one fix pass on the errors
only: change the scene to verified ordinary use and drop the before and after
split, keeping the accepted line if it is supported. Record each finding, the
change and the reason in `claims.md`. Re-run the gate and the refuters once.
Any HIGH finding that remains becomes a named decision in `pack.md`, not a
silent pass. Do not rewrite unaffected frames.

## Case F: change request on one frame of a delivered pack

### Input to the performing agent

A delivered pack (version 1) has seven frames and a valid `DONE.json`. The human
check returns one request: on the dimensions frame, show the product in hand
for scale instead of next to a ruler, and shorten the headline. Nothing else
changes.

### Reviewer rubric

Re-run only the stages the request touches: that frame's entry in `frames.md`,
its copy (gated again), its shot-list entry and its design-spec notes, plus the
claims check for that frame. Keep the other frames, facts and brand CI as they
are. Bump the pack version in `pack.md`, note what changed, and rewrite
`DONE.json` last with fresh sha256 values, the new gate exit code and HIGH count.
Do not restart research or rewrite the brief.

## Routing and review

Positive: image concept/Bildkonzept from product and POE data; gallery order;
exact image copy; English/German revision of an accepted gallery; a creative
pack from a filled brief.
Negative: POE export alone; title/backend SEO only; SB video script; rendering
alone with a complete prompt; publishing images. Route those to their owners.

Assess evidence fidelity, awareness fit, priority reasoning, distinct image jobs,
specific/natural copy, feasible visuals, and scope preservation. Reject wrong
variants/units or unsupported claims even when prose is attractive. Record actual
failures rather than matching wording. Structural lint proves packaging, not
creative quality or conversion performance.
