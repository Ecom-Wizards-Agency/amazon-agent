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

## Claims postures

The brief sets one posture. It decides what the copy may claim beyond the label.

| Posture | Allowed | Skeleton |
| --- | --- | --- |
| Label facts only | What the label prints: identity, contents, amounts and directions | no `approved_sf_lines` |
| Label facts plus named structure/function lines | The above, plus only the exact lines the brief approves, only in the keys listed in `sf_keys`, each with an asterisk and the full disclaimer on the same image | `approved_sf_lines` and `sf_keys` |
| Standard | Benefits the product evidence supports, under the general Amazon and FTC rules | free keys; for a regulated product, brief-approved lines in `approved_sf_lines` and `sf_keys` |

The gate profile follows the product's category, not the posture. A regulated
product always uses its category profile; for a US dietary supplement that is
`references/claims-profiles/us-dietary-supplement.json`. A product in no regulated
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

Each writer receives the same inputs: this file, `frames.md`, `fact-sheet.md`, the
tone section of `ci-spec.md` with the site lines quoted there as allowed patterns,
the claims posture, `copy-skeleton.json`, `facts.json` and the gate command with the
profile chosen above, run from the skill folder:

`python3 -I -B scripts/check_copy.py <pack>/candidates/<set>.json --skeleton <pack>/copy-skeleton.json --profile references/claims-profiles/<profile>.json --facts <pack>/facts.json`

Each one:

1. Writes three options per free key that differ in angle, not only in wording, and
   marks its pick with a one-line reason, in its notes file
   `<pack>/candidates/<set>-options.md`.
2. Fills a copy of the skeleton with its picks as `<pack>/candidates/<set>.json`,
   leaving fixed keys untouched and respecting `max_chars`.
3. Runs the gate on that file and fixes until it reports 0 errors. Warnings are
   fixed or given a reason.

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
