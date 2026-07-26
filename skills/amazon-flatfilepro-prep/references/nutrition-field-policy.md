# Nutrition Field Policy

## Default

Use structured numeric nutrition fields first. Do not populate nutrition string fields by default.

Examples of structured fields include:

- serving quantity, unit, and description
- total servings per container
- energy content and unit
- fat total, saturated fat, and unit
- carbohydrate total, sugars, and unit
- protein value and unit
- vitamins/minerals only where the label and template support the nutrient safely

## String Fields

String fields are defensive fields, not normal fields.

Use them only when:

- Amazon explicitly asks for both per-serving and per-100 g/ml values in the catalog text
- the template exposes only one structured nutrition block
- the active compliance case repeatedly flags nutrition despite correct numeric fields

When used, keep the string short, label-based, and marketplace-language appropriate. Do not add marketing wording or claims.

## Salt And Sodium

If the label shows salt but the export has no dedicated salt/sodium field, do not invent a column. Use an available vitamins/minerals nutrient slot only when the template clearly supports the nutrient and the previous case pattern supports that mapping. Otherwise flag salt for manual review.

## Mismatch Handling

If Amazon support provides values that conflict with the visible label, prefer the visible label for compliance work unless the user explicitly instructs otherwise for an active case. Record the conflict in the validation note.

## Collagen Case Learning

The collagen case used string fields because Amazon repeatedly asked for the nutrition catalog text to show both bases and the template exposed only one structured nutrition block. That was a case-specific defensive move and should not be copied to other supplement updates automatically.
