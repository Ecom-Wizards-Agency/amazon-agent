# Label To Backend Mapping

## Label Sections To Check

- product name and net quantity
- ingredients
- allergen and safety warnings
- recommended intake or daily dose
- nutrition panel, including basis columns
- serving size and servings per container
- storage instructions and shelf life
- manufacturer or food business operator contact
- batch/date markings where relevant
- bundle/set contents

## Backend Mapping Principles

- Match the language of the marketplace.
- Prefer exact label wording for mandatory warnings and instructions.
- Keep backend values neutral and factual; do not add unauthorized claims.
- For bundles, calculate weights additively only when the user provides reliable component weights or the label clearly states them.
- For unit count, use the net quantity basis needed for EU price-per-unit display, such as `450` with unit count type `grams` for a 450 g powder.

## Audit Notes

Each audit should make clear:

- which source label was used
- which SKUs were included
- which SKUs were excluded and why
- which values were changed
- which values already matched
- which values need manual review because the export lacks a safe field
