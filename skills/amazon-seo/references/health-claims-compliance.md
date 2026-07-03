# Health-Claims Compliance Layer (self-check + risk posture + RJ-preserving rewrites)

The process layer on top of `eu-compliance-matrix.md` (which stays the EU law reference). Modeled on Amazon's own SAS "Health Claims Check" ASIN audits (AI-generated, per-claim, EU-register-checked) — we run the same check ourselves before Amazon does. **Not legal advice**; every output carries that disclaimer and ends with "final publication needs category compliance review + label verification."

Dual objective, always: **compliance AND ranking**. Ranking Juice + semantic coverage stay the priority (`seo-writing-methodology.md` §2); compliance work is done through the rewrite ladder below, which preserves keyword tokens wherever possible. Removing a claim is the last resort, not the first.

## Category risk tiers

| Tier | Categories | Posture |
|---|---|---|
| `regulated` | Supplements, foods sold with nutrition/health angles, health & beauty, topicals, medical-adjacent devices | Full self-check before delivery is mandatory. Kill **HIGH** (non-authorised/rejected) claims. Keep **MEDIUM** wording when it carries real Ranking Juice — rewrite via the ladder first, drop only if no compliant carrier exists. |
| `standard` | Household, home & kitchen, general merchandise — **not health-claim products** (per Amazon SAS account-manager guidance, more aggressive wording is acceptable here) | Claims-lite quick pass (superlatives, guarantees, comparative/competitor claims, general Amazon claim policy). Keep MEDIUM+ freely; kill only outright prohibited wording. |

Per-client override lives in the workbook config (`compliance.risk_posture`: `standard` = the above; `conservative` = also remove MEDIUM in regulated; `aggressive` = standard-tier posture even in a regulated category — operator-approved only).

## Marketplace regimes

**EU (DE/FR/IT/ES/…)** — `eu-compliance-matrix.md` is the rulebook (Reg. 1924/2006 + 432/2012 + 1925/2006; Art. 10(3) non-specific claims; Art. 12/14 disease/weight-loss). Regime specifics the SAS audits add on top of the matrix:

- Nutrition-claim thresholds are checkable arithmetic — do the math in the check: "source of protein" ≥12% of energy from protein; "high protein" ≥20%; "source of [vitamin/mineral]" ≥15% NRV per serving; "high in" ≥30% NRV; "lactose-free" ≤0.1 g/100 g; "gluten-free" ≤20 mg/kg (Reg. 828/2014); "low calorie" ≤40 kcal/100 g/ml.
- Meal-replacement-for-weight-control products: Reg. (EU) 2017/1798 sets composition (200–400 kcal/serving, ≥25% energy from protein, ≤30% from fat, micronutrient minimums) + a mandatory labelling statement. The **authorised wording is "weight control"** — "weight loss" is stronger than authorised and gets flagged.
- Non-specific health benefits ("complete", "pure", "balance", "wellbeing") are only permitted **accompanied by a specific authorised claim** (Art. 10(3)).
- National overlays: a "natural" claim next to synthetic ingredients (e.g. sucralose) is challengeable under national advertising law (DE: UWG) even when 1924/2006 doesn't apply.

**US** — no health-claims register; the frame is FDA + FTC + Amazon policy:

- **Disease claims** (treat/cure/prevent/mitigate a disease, or naming diseases as the product's purpose) make a supplement or cosmetic an unapproved drug — never in copy. This includes disease-audience targeting: naming conditions (eczema, psoriasis, arthritis…) as what the product is *for*.
- **Structure/function claims** are permitted for supplements ("supports immune health") but require substantiation, the FDA disclaimer on-label, and no disease implication. Cosmetics are limited to appearance/cleansing claims — "reduces wrinkles' appearance" is cosmetic, "regrows hair" / "stimulates follicles" is a drug claim (OTC monograph territory).
- **FTC**: objective claims need competent and reliable evidence; guarantees and superlatives without substantiation are the risk in `standard`-tier categories too.
- **Amazon's own restricted-claims policy is the binding layer in practice** — Amazon suppresses/flags listings for claim language regardless of FDA nuance (see Seller Help: product detail page rules, restricted products, category style guides). Recurring patterns from our runs: a category label can itself be claim-adjacent (a hero keyword like "hair regrowth" may be tolerated as category language but is claim-risk-for-review — decide per listing, document in the config `_claim_tokens_note`); disease-audience words can be routed to backend/PPC after cosmetic-vs-drug review instead of visible copy.

## The self-check (our SAS-style audit)

Run per listing (live copy captured via `amazon-listing-capture`, the workbook's SEO Text tab, or pasted copy). Walk **every discrete claim** in title / Item Highlights / bullets / description / backend / A+ (when available) and record:

| Field | Content |
|---|---|
| Original text | Verbatim, with location (title/bullet #/IH/backend) + EN translation if needed |
| Claim type | health claim / non-specific health benefit / nutrition claim / factual-compositional / marketing-taste-quality / origin |
| Relevant ingredient | What the claim hangs on |
| Register/policy check | EU: register status + Annex threshold math. US: disease vs structure/function vs cosmetic + Amazon policy |
| Status | `authorised` / `non-authorised` / `uncertain-needs-legal` / `nutrition-ok` / `nutrition-below-threshold` / `low-risk-factual` |
| Risk | LOW / MEDIUM / HIGH |
| Suggested rewrite | RJ-preserving (ladder below) — never "delete" without a replacement proposal |

Close with: summary table by risk level, **priority action list** (HIGH first), **authorised claims to ADD** (see ladder step 3), overall risk rating, disclaimer line.

Classification heuristics the SAS audits confirmed (word-level red flags):

- **"bioactive"** (bioaktiv) and similar physiological-function adjectives = health claim even inside an otherwise factual phrase → HIGH when the ingredient has no authorised claim.
- **Ingredient highlighted in marketing copy = implied claim** even with zero benefit words: featuring an ingredient with rejected claims (e.g. L-carnitine) in a bullet next to weight/fitness context implies the rejected benefit → HIGH. Fix: keep it in the ingredient list only, remove from bullets.
- **"only" + a number** ("only 200 calories") converts a factual statement into an implied low-calorie benefit → MEDIUM; drop "only" or contextualise.
- **"natural"** + any synthetic ingredient in the list → MEDIUM (national advertising law).
- **"100% pure"** and similar purity-implies-health wording → MEDIUM non-specific benefit; replace with the specific factual absence statement ("without colorants, flavors, sweeteners, preservatives").
- **Stronger-than-authorised wording**: the register wording is the ceiling ("weight control", not "weight loss"; "contributes to", not "boosts").
- Factual-compositional statements are reliably LOW: ingredient names/types, process descriptions (peptide size, hydrolysis), solubility, accurate free-from claims, origin/quality ("Made in Germany"). This is the compliant floor every listing can stand on — and confirms the names-vs-effects core rule.

## The RJ-preserving rewrite ladder

Apply in order — each step keeps more Ranking Juice than the next:

1. **Strip the effect, keep the tokens** (names-not-effects): the keyword-bearing nouns stay in copy as factual attributes; only the benefit framing goes.
2. **Swap to the authorised wording that carries the same tokens**: "weight loss" → "weight control" (authorised for compliant meal replacements); "boosts X" → register wording "contributes to normal X". Semantic search still connects the intent; the tokens still index.
3. **ADD authorised claims that carry rankable tokens** (the offensive move): check the product's actual nutrition profile against the register — protein ≥12% energy unlocks "protein contributes to the growth and maintenance of muscle mass" / "…maintenance of normal bones"; each vitamin/mineral at ≥15% NRV unlocks its register claims (immune system, tiredness/fatigue, energy metabolism…). These are keyword-bearing, high-intent phrases the listing gets **for free, compliantly**. Every regulated-tier check must include this section.
4. **Route what copy can't carry**: per posture tier — claim-risky search terms go to backend (indexing without visible claim) or PPC (`final_action`: "Backend only"/"PPC only") instead of being lost. In `regulated` + conservative posture, skip backend for outright disease terms.
5. **Drop** — only when no compliant carrier exists at any level. Record the SV lost (the compliance tax — the builder now reports it).

## Worked examples (sanitized from real Amazon SAS audits, amazon.de, 2026)

**Collagen powder (DE, supplement):** SAS flagged HIGH: "Natürliches **Bioaktives** Kollagen Hydrolysat" in the title — "bioaktiv" implies physiological function; all 22 collagen register entries are non-authorised → remove the one word, keep "Kollagen Hydrolysat Peptide Typ 1, 2, 3" (factual, keyword-bearing). MEDIUM: "Proteinpulver" in title (implied nutrition claim; collagen is incomplete protein, no nutrition table on PDP) → "Kollagen Pulver" or substantiate; "100% rein" → replace with the factual additive-free statement. LOW (kept): ingredient/type listing incl. branded raw materials as pure identification, peptide-size process description, solubility, laktosefrei, Made in Germany. Net effect on RJ: one adjective and one generic word traded; every tracked keyword survived.

**Meal-replacement shake (DE, food):** SAS flagged HIGH: an ingredient with EFSA-rejected claims (L-carnitine) highlighted in bullets next to weight/fitness context → ingredient list only. HIGH→fix by swap: title "for Weight Loss" → authorised "for Weight Control" (+ verify Reg. 2017/1798 composition + mandatory statement). MEDIUM: "27 vitamins and minerals" (not an authorised claim format — each nutrient needs ≥15% NRV individually) → name the qualifying ones as "source of" claims; "only 200 calories" → "200 kcal per serving"; "naturally delicious" + sucralose → taste wording without "natural". **Section 5 move**: the audit itself listed authorised claims to ADD (protein→muscle mass, protein→bones, vitamin D/C→immune system, magnesium→tiredness/fatigue…) — rankable copy handed over by the compliance check.

## When it runs

- **Mandatory before delivery** for every `regulated`-tier SEO deliverable (keyword workbook SEO tab, listing refresh, flat-file copy). The workbook builder warns when `compliance.category_tier` is `regulated` and no check is recorded (`compliance.checked`).
- **Claims-lite pass** for `standard` tier: superlatives/guarantees/competitor claims only, unless the copy borrows health language.
- **On-demand** for any listing via `/health-claims-check` (live listing, workbook, or pasted copy — anchor or competitor).
- Findings are saved under `output/{client}/seo/` (e.g. `claims-check-<asin>-<date>.md`) and feed `triage.claim_tokens` + the config `compliance.claims_audit` block + `seo_content` per-row compliance notes.

**Client-facing report note:** an EW-branded client deliverable version of this check (brand doc pipeline, SAS-style layout) is possible but is **only produced when the operator explicitly requests it for a specific client in the current chat**. It is never a default output and is never sent to a client otherwise. The default consumer of the check is internal: the SEO build and the operator note.
