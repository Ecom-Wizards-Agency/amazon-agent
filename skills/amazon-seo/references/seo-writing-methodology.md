# SEO Writing Methodology (condensed, in-repo)

Condensed, team-shareable version of the Ecom Wizards SEO method so the skill is
runnable from the repo alone (no Obsidian vault required). The vault
(`/Users/victoruhl/Obsidian/Victors Second Brain/Skills/` — `amazon-seo-writer`,
`keyword-classifier-and-filter`, `rufus-optimization`, `direct-response-copywriter`)
remains the deeper source. Always pair with `eu-compliance-matrix.md`.

Two phases run in order: **classify keywords → write copy → audit coverage.**

---

## 1. Keyword classification (before writing)

Clean the keyword list first — one wrong call cascades through the whole list.
Leave **relevant** keywords blank; mark negatives with one marker:

| Marker | Meaning | Example |
|---|---|---|
| **X** | Irrelevant word (not related to this product) | "shampoo" for a serum |
| **B** | Competitor brand | "rogaine", "glow25" |
| **C** | Different product category | "hair dryer", "modem" |

Filtering uses **word-boundary matching**: a phrase containing ANY X/B/C word is
excluded; phrases of only-blank words are included → the Master List.

In the keyword-workbook builder this maps to: the **`2 Never KWs`** tab (one-word
true negatives, generated from the Expanded 1% MKL) and the **Outlier triage**
categories (`Competitor/brand term`=B, `Wrong product form`/`Negative candidate`=X/C).
Protect real product intent — a high-frequency word is only `Never Ever` when it's
genuinely irrelevant/wrong-form/unsafe after checking examples + relevancy.

## 2. Ranking Juice (the optimization metric)

- Each master keyword has a search volume. A keyword counts toward Ranking Juice
  if it appears **once anywhere** in the listing.
- **Ranking Juice % = covered keyword SV ÷ total master SV × 100.** Maximize while
  keeping copy natural + compliant.
- **Placement priority (indexing weight): Title > Bullets > Description > Backend.**
- Individual tokens combine across fields (Amazon indexes tokens), so you don't
  need to repeat a phrase — cover its words once across the listing.
- The builder's `4.1 SEO Text` tab carries the DataDive **Ranking Juice** snapshot
  (current vs optimized target, per element) so you write toward the biggest gaps.

## 3. Writing rules

- **Title** — keyword-rich, benefit-led, front-load the highest-SV exact terms;
  within the marketplace limit (~200 chars on most EU stores).
- **5 bullets** — each a benefit-led micro-PAS (problem → agitate → solve),
  capitalized lead label; weave in mid-SV terms naturally.
- **Description** — longer copy covering remaining keywords + brand story +
  objection handling. (Often the biggest Ranking-Juice gap because it's empty.)
- **Backend search terms** — only keywords NOT already in visible copy; no
  duplicates, no competitor brands, ≤250 bytes. Misspellings/variants go here.
- **Never keyword-stuff.** Natural compliant copy beats density. Each keyword once.

## 4. Rufus / Alexa AI (semantic layer)

Amazon's AI search ranks by **meaning**, not exact match. Complementary to keyword SEO:

- **Noun-phrase stacking:** dense natural phrases stacking *product identity +
  key attribute + use case + audience* (e.g. "professional ceramic straightener
  for thick curly hair").
- **Inference mapping:** map customer needs → features, demographics → language,
  use cases → scenarios, likely questions → answers embedded in copy.
- Feed it customer **questions/needs** (from POE Customer Review Insights), not
  just keywords — Rufus thinks in questions. The builder surfaces these in
  `POE Semantic Insights` and `POE Raw - Reviews`.

## 5. Audit pass (close gaps)

After the first draft: compute Ranking-Juice coverage, list missed keywords by
SV, and optimize placement to close the gaps — without stuffing and without
breaking compliance.

## Final Action (workbook handoff)

Each triaged keyword gets a Final Action from
`{Use in copy, Backend only, A+ only, PPC only, Negative, Ignore}` — `Use in copy`
for relevant semantic opportunities, `PPC only` for competitor/brand terms,
`Negative` for wrong-form/off-product, `Ignore`/`Backend only` for the rest.
This is the bridge from triage to the actual copy + PPC/backend decisions.
