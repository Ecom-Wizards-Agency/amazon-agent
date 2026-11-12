# Image copy

How the words on listing images are written, judged and checked in a creative pack
(`references/creative-pack.md`). The general copy rules in `SKILL.md` "Write exact
copy" still apply; this file adds the pack's rules, the claims postures and the
writer and judge protocol.

## What the words have to do

A shopper sees each image for about two seconds, usually on a phone at about 360 px
wide, while comparing it with lookalike products. Each image has one buying job, and
its words do that job and nothing else.

- One idea per image. The headline carries it; everything else supports it.
- Headlines are usually 3 to 7 words. Eyebrows are 1 to 3 words in capitals. The
  subheadline is one sentence. Chips and callouts are a few words.
- Concrete beats clever. Numbers, names and plain nouns from the label beat adjectives.
- Every fact is true to the label and reads the same way everywhere it appears. Pick
  one serving or usage phrase ("per 2-capsule serving", "per 10 ml spray") and use
  it in every frame.
- No beat repeats across frames. If two frames say the same thing, one of them loses
  its job.
- No filler that fits any other product. A line just as true of a competitor gets
  rewritten with this product's facts.
- The brand's voice comes from `ci-spec.md`. No exclamation marks or hype unless the
  brand itself writes that way.

## Claim tiers (claims postures)

The brief chooses one tier at intake. Give the person the product's primary buying
benefit, the evidence for it, and the conversion tradeoff for each tier below. These
are qualitative costs, not forecasts of conversion lift or a legal safe harbour.

| Tier / existing posture name | Allowed | Conversion cost | Skeleton |
| --- | --- | --- | --- |
| 1. Label facts only | Verified printed identity, contents, amounts and directions, subject to category rules below | Can explain contents and use, but may remove the buyer's main reason to choose the product; do not quietly substitute storage facts for that benefit | no `approved_sf_lines` |
| 2. Label facts plus named structure/function lines | Tier 1 plus the exact supported, brief-approved lines in designated frames, where the category permits them | Restores the named benefit only; exact phrasing, required disclaimers and restricted placement consume space and limit the story | `approved_sf_lines` and `sf_keys` |
| 3. Standard | Benefits supported by product evidence within the category, marketplace and Amazon/FTC rules | Gives more room to explain why to buy; requires stronger substantiation and claims review and may still exclude the desired promise | free keys; regulated lines use `approved_sf_lines` and `sf_keys` |
| Cosmetic, when chosen at intake | Sourced scalp-care, appearance and practical benefits, verified product facts and directions, and sourced ingredient facts; no invented finished-product result | Can answer cosmetic buying questions; unsupported efficacy remains an evidence gap | free keys under the applicable category rules |

If the chosen tier removes the product's primary benefit, stop at intake before
concept, copy or production. Show the person the applicable tiers with the exact benefit
retained/lost, the supporting evidence or gap and each conversion cost. Ask them to
choose or confirm a narrower practical-benefit direction explicitly. Approval
cannot make an unsupported or prohibited claim usable. Record the decision in
`brief.md` and `claims.md`; no agent may accept that tradeoff for the person.

The claim tier chosen at intake governs the job; the agent must not tighten it on
its own. If the person chooses a cosmetic tier, sourced ingredient facts are
allowed as facts about the ingredient, without implying a finished-product result.
Every cosmetic benefit, fact and direction needs a source recorded by key in
`claims.md`. Appearance and safety wording needs substantiation and refuter review;
it is not banned solely for naming appearance or safety. Apply the ingredient versus
finished-product distinction in the category checks below. Unanswered shopper questions
follow the evidence-gap delivery rule in `references/creative-pack.md`.

A claims refuter's crop, label-hiding or product-size restriction also goes to the
person with the exact risk, compliant alternative and conversion cost. Do not make
the product small or unrecognisable to force a pass. Copy changes from a reviewer
go back through the writer, then through the copy gate and affected claims checks.

The gate profile follows the product's category, not the posture. A regulated
product always uses its category profile; for a US dietary supplement that is
`references/claims-profiles/us-dietary-supplement.json`; for a US cosmetic, use
`references/claims-profiles/us-cosmetic.json` (draft, unverified; awaiting human
category compliance review before publication). A product in no regulated
category uses `references/claims-profiles/amazon-standard.json`. Disease and drug
claims are banned in every posture. For a regulated product the standard posture
adds only the benefit lines the brief approves, through `approved_sf_lines` and
`sf_keys`, or through an `allow` entry in `facts.json` for an approved word.
Claims law and the risk ladder are in
`skills/amazon-seo/references/health-claims-compliance.md`.

## Regulated categories

Applies to every regulated product, in every posture.

- No disease words (treat, cure, prevent, diagnose, any named condition) and no
  body-system or health-effect words outside an approved structure/function line.
- No cleanse, detox or flush language. No results or timing promises ("you'll feel",
  "in days", "works").
- No quality, origin, testing, transparency or free-from claims in our copy
  (certified, tested, clinical, patented, made in a named country, no proprietary
  blend, gluten free), even when the pack prints them, unless the brief approves the
  exact line and `facts.json` lifts its pattern with `allow`. The pack's own seals may
  show on the photographed product; our words do not repeat them.
- Claim-adjacent terms printed on the pack, such as a mechanism word, stay out of our copy.
- No superiority or comparison, reviews or ratings, price, guarantee or refund.
- No dosage form, allergen, free-from or timing instruction the label does not print.
- Give amounts only as the label gives them. Never derive a per-unit figure the label
  does not print, and do not spell out a unit abbreviation the label leaves short.
- A line next to a structure/function line adds no ingredient that, together with
  it, implies a disease.
- Images make claims too. No symptoms, organs, vessels or medical settings, and no
  people acting out a result under a benefit line: a couple out hiking under a
  mobility line reads as a promised result.

## Writers

Three writers, each in its own separate context, each with a different angle:

1. **Label reader:** leads with the printed facts and what they settle for the shopper.
2. **Shopper benefit:** leads with the practical gain each frame's job offers.
3. **Brand voice:** writes the way the brand's own site writes.

Each writer receives the shopper question per frame, sourced facts and a description
of the picture, plus this file, the brand tone and approved claim tier/category rules.
Never send a line-by-line copy skeleton, prewritten headline or another writer's
lines. Keep `copy-skeleton.json` with the job runner for mechanical assembly and
validation after writing. A comparison between two writers counts only when both
received these independent inputs; retain the actual briefs. The 12.11.2026 rerun's
`blind-pairs.md` returned near-identical lines under a shared copy skeleton.

Each one:

1. Composes three different copy options per frame under its assigned lens, marks
   its pick with a one-line reason in `<pack>/candidates/<set>-options.md`, and saves
   the picked words by frame and text role in `<pack>/candidates/<set>-draft.json`.
2. Returns those words without fitting them to a supplied line-by-line skeleton.
   Fixed label facts and required disclaimers remain exact.

The job runner maps each draft verbatim to the skeleton's keys, preserving fixed
keys and limits, as `<pack>/candidates/<set>.json`, then runs:

`python3 -I -B scripts/check_copy.py <pack>/candidates/<set>.json --skeleton <pack>/copy-skeleton.json --profile references/claims-profiles/<profile>.json --facts <pack>/facts.json`

Return failed lines or missing roles to their writer with the relevant constraint
and finding, keeping accepted wording unchanged; do not rewrite during mapping.
Gate again until 0 errors and explain warnings. Exit 3 (`review_required`) allows
candidate judging with a review hold; pack clearance requires the refuter record
and named person's sign-off in `claims.md`, bound by `DONE.json`, as specified in
`references/creative-pack.md`. Judge only sets with no mechanical errors below.

A set that cannot reach 0 errors drops out, and `pack.md` says so. The
`candidates/` folder is working material, not one of the pack files.

## Blind judges

- Anonymise the three sets: shuffle them to neutral labels and keep the key out of
  the judges' inputs. Apply it only after judging.
- Three judges, each in its own context: a conversion copywriter, the target shopper
  and the brand director. For each free key a judge sees one candidate per gated set,
  the line that set put in its `<set>.json`, and picks one with a one-line reason,
  judging the frame's job at 360 px. The other options in the notes files were never
  gated; they serve the fix pass only.
- The majority pick builds `copy.json`. With three different picks, the target
  shopper's pick wins and `pack.md` notes the split.
- Lines from different sets can clash. Check the assembled copy for a repeated beat
  or a second serving phrase, then gate it again to 0 errors.

## Claims refuters

Two refuters, each in its own context, try to prove the assembled copy wrong:

1. **Policy:** FDA, FTC and Amazon policy, using
   `skills/amazon-seo/references/health-claims-compliance.md`.
2. **Facts and images:** every number, count and name against the label, and what each
   scene implies next to its words, including the claims printed on the pack itself.

Each finding names the key, quotes the text and rates it HIGH, MEDIUM or LOW. Then:

1. One fix pass that changes only lines with findings, with no restyling.
2. Gate again to 0 errors, and both refuters once more.
3. A HIGH that remains goes to `pack.md` as a decision for the human, with the
   quote, the risk and a compliant alternative. Every finding goes into `claims.md`.

## Lessons

- The gate catches only the mechanical layer: banned words, fixed keys, numbers,
  lengths. Meaning-level errors need the refuters: a false count ("six ingredients"
  on a five-ingredient label), a second serving phrase, an origin claim in plain
  words, or a product name on the pack that differs from the listing.
- Voice is the usual weak spot. Writers given the brand's own site lines as allowed
  patterns sound like the brand; writers given adjectives sound like everyone else.
