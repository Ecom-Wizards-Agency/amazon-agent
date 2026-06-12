# EU Health-Claim Compliance Matrix (supplements / foods)

Practical, reusable reference for what may and may not be claimed in EU Amazon
listing copy (DE/IT/FR/ES/…). Use it when writing `seo_content` and when filling
`triage.claim_tokens`. **This is a starting reference, not legal advice** —
always verify against the current EU claims register, the product's actual
ingredient + dose, and Amazon's category rules before publishing. When unsure,
treat the claim as prohibited and ask Victor.

## The framework (what governs claims)

| Regulation | Governs | Rule of thumb |
|---|---|---|
| **Reg. 1924/2006** | Nutrition & health claims | Nutrition claims OK if the Annex criteria are met; health claims only if **authorized**. |
| **Reg. 432/2012** | The permitted-health-claims list (Art 13.1 function claims) | A function claim is allowed **only** with the exact ingredient + dose + wording on the register. |
| **Reg. 1925/2006** | Added vitamins/minerals/substances | Governs fortification + what's permitted. |
| Art. 12 / 14 (1924/2006) | Disease & weight-loss claims | Disease prevention/treatment claims are **prohibited** (except authorized risk-reduction claims). Rate/amount-of-weight-loss claims are **prohibited**. |

**Two claim types — don't confuse them:**
- **Nutrition claim** (about composition): e.g. "high in fibre", "source of protein", "low sugar". Allowed if the Annex threshold is met — **no register needed**.
- **Health claim** (effect on the body): e.g. "supports digestion", "maintains normal cholesterol". Allowed **only** if on the authorized register at the qualifying dose, in approved wording.

## Generally allowed (factual / authorized)

- **Nutrition claims** meeting the Annex thresholds — e.g. *"alto contenuto di fibre" / "high fibre"* (≥6 g/100 g or ≥3 g/100 kcal); *"fonte di fibre" / "source of fibre"* (≥3 g/100 g or ≥1.5 g/100 kcal); "source/high protein", "low/no sugar", "vegan", "lactose-free", "gluten-free" (only if true/certified).
- **Factual product attributes**: ingredient, form, peptide/fibre type, dosage per serving, kcal, solubility, taste, origin ("Made in Germany"), pack size, usage (drinks, baking).
- **Authorized function claims at the qualifying dose**, in register wording — examples:
  - *Pectin* → "contributes to the maintenance of normal blood cholesterol" (6 g/day); "reduction of blood-glucose rise after a meal" (10 g/meal).
  - *Beta-glucans* (oats/barley) → normal blood cholesterol (3 g/day).
  - *Psyllium / Plantago ovata husk* → normal blood cholesterol (7 g/day); bowel-function/transit claims for some fibres at stated doses.
  - *Glucomannan* → the only widely-authorized weight-related claim (3 g/day in 3 doses with water, in an energy-restricted diet).

## Generally prohibited (unless specifically authorized at dose)

- **Disease / treatment / cure**: "treats", "cures", "prevents", arthritis, constipation-as-condition, "anti-arthrose", diagnosis language.
- **Unauthorized body-function claims**: generic "supports joints / skin / hair / immune system / digestion / gut health" without a register entry + dose.
- **Weight-loss**: "dimagrante", "perdita di peso", "brucia grassi", rate/amount of loss (prohibited), satiety-for-weight-loss (unless the specific authorized claim + conditions).
- **Superlatives/awards** without substantiation: "Testsieger", "Nr. 1", "best quality".
- **Competitor brands** in title/bullets/backend.

## Worked cases (already applied)

| Product | Marketplace | Verdict | Why |
|---|---|---|---|
| **Collagen** (Sheko Kollagen) | DE | **No authorized health claim** → factual only (peptide type I/II/III, hydrolysate, form, solubility, origin). | Collagen has **no** authorized EU health claims; the live listing's "unterstützen nachweislich Gelenke/Haut…" was unauthorized → removed. |
| **Fibre blend** (Sheko Ballastpulver: soluble corn fibre + acacia/carob + citrus pectin) | IT | **"Alto contenuto di fibre" (nutrition claim) allowed**; digestion / bowel / satiety / weight-loss **prohibited**. | No authorized health claim applies to this blend at this dose (pectin cholesterol claim needs 6 g/day — not met). The live listing's "favorisce la digestione / sazietà / perdita di peso" were unauthorized → removed. **Not psyllium** — don't borrow psyllium's claims. |

## How to use this in a build

1. Identify the **actual ingredient(s) + dose per serving** from the listing-reference JSON / label (verify any source discrepancy, e.g. acacia vs carob).
2. Allow: matching **nutrition claims** + factual attributes + any **authorized function claim** whose ingredient + dose qualify, in register wording.
3. Put prohibited terms into `triage.claim_tokens` so the workbook flags them as `Unsupported claim/health-risk`.
4. In `seo_content` compliance notes, cite the basis (e.g. "Reg. 1924/2006 nutrition claim" or "factual only — no authorized claim").
5. Always end with: *final publication needs category compliance review + label verification.*
