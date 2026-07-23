# SEO Writing Methodology (condensed, in-repo)

Condensed, team-shareable version of the Ecom Wizards SEO method so the skill is
runnable from the repo alone (no Obsidian vault required). The vault
(`<your-vault>/Skills/`: `amazon-seo-writer`,
`keyword-classifier-and-filter`, `rufus-optimization`, `direct-response-copywriter`)
remains the deeper source. Always pair with `eu-compliance-matrix.md`.

Two phases run in order: **classify keywords → write copy → audit coverage.**

---

## 1. Keyword classification (before writing)

Clean the keyword list first. One wrong call cascades through the whole list.
Leave **relevant** keywords blank; mark negatives with one marker:

| Marker | Meaning | Example |
|---|---|---|
| **X** | Irrelevant word (not related to this product) | "shampoo" for a serum |
| **B** | Competitor brand | "rogaine", "glow25" |
| **C** | Different product category | "hair dryer", "modem" |

Filtering uses **word-boundary matching**: a phrase containing ANY X/B/C word is
excluded; phrases of only-blank words are included → the Master List.

In the keyword-workbook builder this maps to: the **`2 Never KWs`** tab (generated
from the Expanded 1% MKL) and the **Outlier triage** categories
(`Competitor/brand term`=B, `Wrong product form`/`Negative candidate`=X/C).
Protect real product intent: a high-frequency word is only `Never Ever` when it's
genuinely irrelevant/wrong-form/unsafe after checking examples + relevancy.

The Never-KWs tab is a **sectioned audit view**, protection-first ladder: a word is
protected if it appears in the Core-30% vocabulary, the product/listing language,
POE search terms, or configured relevant/misspell words; then brands and claim-risk
words route to their own sections (never blanket-negated); what remains becomes a
`Never Ever` single-word negative (configured junk/wrong-form/off-niche, or the auto
rule: frequent in 1% discovery, max relevancy ≤ the cut, absent from core/product/POE).
Sections: Never Ever (apply as negative phrase on the root word) → Competitor brands
(campaign-dependent: negative in rank/SKW, target in PAT/conquest) → Claim risk
(compliance review) → Review-manually near-miss band → phrase-level negative
candidates (combination-irrelevant phrases whose words are individually clean).
Every row carries Category, Why, max SV, max relevancy, and example phrases so a
human can justify each call.

The **`1. Root Keywords`** tab carries the ad-targeting signal: ⭐⭐ ad roots
(DataDive root score ≥ `ad_min_score` AND Broad SV ≥ `ad_min_sv` AND not
Brand/Claim/Form/Off-niche) are the roots that seed SKW/rank campaigns; ⭐ marks
relevant-but-below-SV-floor roots. The Category column uses the same token sets as
the Never-Ever ladder, so the two tabs never disagree about what a brand or claim
word is.

## 2. Ranking Juice (the optimization metric)

- Each master keyword has a search volume. A keyword counts toward Ranking Juice
  if it appears **once anywhere** in the listing.
- **Ranking Juice % = covered keyword SV ÷ total master SV × 100.** Maximize while
  keeping copy natural + compliant.
- **Placement priority (indexing weight): Title ≳ Item Highlights > Bullets >
  Description > Backend.** (Amazon hasn't published Item Highlights' exact weight,
  but it is searchable AND rendered next to the title in search results, so treat
  it as title-tier, not bullet-tier.)
- Individual tokens combine across fields (Amazon indexes tokens), so you don't
  need to repeat a phrase; cover its words once across the listing.
- **RJ is a coverage-allocation problem, not a stuffing problem.** Because a
  keyword counts once anywhere, the goal is to cover as many high-SV master
  keywords as possible, once each, across the searchable fields, without repeats
  and without stuffing. Front-load the highest-SV head cluster across **Title +
  Item Highlights** (the two fields shown in search), then let bullets/description
  mop up the rest.
- **Front-load the highest-SV _tracked_ keyword, not a _root_.** RJ only counts
  coverage of the **Master Keyword List** (the tracked keywords with per-keyword SV).
  A term from the **Roots** tab can show enormous *broad* SV yet not exist as a
  tracked MKL keyword. Front-loading it spends the title on volume that does not
  score. **Before you lead the title with a term, confirm it appears in the MKL with
  its own SV** (pull the niche's master keyword list, e.g. DataDive MCP
  `get_niche_keywords`). Worked case: `akazienfaser` looked like the #1 term (≈103k
  root SV) but was a root, not a tracked keyword. The RJ-scoring volume lived in the
  generic head (`ballaststoffe` 9,969 + `ballaststoffe pulver` 4,798), so the title
  led with those instead.
- **Dual objective: traditional SEO _and_ semantic/Alexa, together, not a trade-off.**
  Every searchable field must simultaneously (a) front-load high-SV **tracked** tokens
  for Ranking Juice and (b) read as natural noun-phrase stacking that Rufus/Alexa can
  parse (see §4). Write the exact-match head cluster *as* a natural phrase. Don't
  choose one goal over the other.
- The builder's `4.1 SEO Text` tab carries the DataDive **Ranking Juice** snapshot
  (current vs optimized target, per element) so you write toward the biggest gaps.

## 3. Writing rules

- **No ALL-CAPS in any visible field** (title, Item Highlights, bullets, description).
  Amazon "Product detail page rules" (Seller Help G200390640): *"Use capital letters
  only for the first letter of each word. Do not use all capital letters throughout the
  attribute."* Use **Title Case** for the title, each highlight, and bullet lead labels
  (`Scalp Nourishing Daily Serum:`), never `SCALP NOURISHING DAILY SERUM:`. Sentence case
  is fine for bullet/description bodies. Optimise the visible fields for the **shopper's
  eye** first (readable, scannable); the exact separator/caps style is flexible as long
  as it reads cleanly and stays within this no-all-caps rule.
- **Dash separators belong in the TITLE only; Item Highlights use COMMAS.** The spaced
  **EN-dash ` – `** (U+2013, not a true em-dash) is the standard *title* separator. Match
  the brand's live-title glyph. **Item Highlights are comma-separated Title-Case chips**
  (see the Item Highlights formatting rule below), NOT dash-separated, so the two fields
  stay visually distinct in the search grid. The repo's no-spaced-em-dash rule governs
  **prose** (narratives, notes, chat, commit messages, docs), NOT the title field, so the
  workbook builder must not strip the dash from title copy.
- **Title**: keyword-rich, benefit-led, front-load the highest-SV exact terms.
  **Limit: ≤75 characters including spaces** (all marketplaces, all categories
  except media, per Amazon policy effective **2026-07-27**; the old ~200-char limit
  applies only to titles published before that date). Spend the 75 chars on the
  highest-SV head cluster + the key differentiator; every term that no longer
  fits moves to **Item Highlights**. Transition note: a title written before
  2026-07-27 can stay live until then, but every new/updated listing should ship
  the ≤75-char title + Item Highlights now.
  - **Split compounds into separate tokens (compounding languages: DE/NL).** Amazon
    indexes tokens, so the compound `Ballaststoffpulver` is ONE token, whereas
    `Ballaststoffe Pulver` is two, covering `ballaststoffe` (9,969) **and**
    `ballaststoffe pulver` (4,798) **and** `pulver`. Prefer the separated / hyphenated
    form when it widens coverage without hurting readability.
  - **Blend vs single-ingredient framing.** If the product is a **blend** of several
    ingredients, do NOT lead the title with one of them. It is inaccurate and
    narrows coverage. Lead with the generic category term + a **blend signal**
    (`-Komplex`, `-Mix`, `3 lösliche Fasern`) and push the individual ingredient
    **names** to Item Highlights + bullets + backend. Because Item Highlights is
    searchable and title-tier, the ingredient SV is recovered without the title
    overclaiming one component (title and Item Highlights carry *different* terms;
    see the don't-repeat-tokens rule below). If the product is genuinely
    **single-ingredient**, lead with that ingredient. Worked case: a 3-fibre blend
    (Fibregum™ Akazienfaser + lösliche Maisfaser + Zitrus-Pektin) → title
    `… Ballaststoffe Pulver … Ballaststoff-Komplex, 80% löslich`, with the three
    fibre names in Item Highlights.
  - **Ingredient NAMES are factual (allowed); ingredient EFFECTS are health claims.**
    Naming a fibre/ingredient is a factual attribute; ascribing an effect to it
    (präbiotisch, "improves digestion", blood-sugar, satiety, gut flora) is an
    unauthorized EU health claim unless on the register at dose. See
    `eu-compliance-matrix.md`.
- **Item Highlights**: new field paired with the title (≤125 characters
  including spaces), **searchable** and shown with the title in search results +
  on the PDP. **This is a SEPARATE field from the bullet points below. The two
  coexist; Item Highlights does NOT replace the 5 bullets.**

  **Highlight the ITEM first: it is a shopper-facing field, not a blind keyword
  tank.** Because the shopper *sees* it next to the title in the search grid, it
  does two jobs at once, in this priority order:
  1. **Mirror what the shopper searches, for CTR.** Surface the product's real
     **USPs / differentiators**, phrased the way buyers search them. When the
     highlight visibly echoes the query (the attribute or use-case they typed),
     the listing reads as "this is exactly it" and **click-through rises**. This
     is the primary job.
  2. **Recover high-SV terms the 75-char title could not hold, for Ranking
     Juice.** It is title-tier and searchable, so it is also the title's overflow
     tank for keyword coverage.

  **Relevance gates inclusion; SV ranks within the relevant set.** Only include a
  high-SV keyword if it is **genuinely true of the product**. A high-volume term
  that is *not* a real attribute of the item is forbidden here: shown in search
  it erodes trust and CTR (and risks accuracy/compliance), the opposite of the
  field's purpose. Among the terms that *are* genuinely connected, prioritise
  high-SV ones the anchor ranks **weakly** on (most RJ headroom).

  **Formatting (apply every time):**
  - **Title Case each highlight**: capitalize the principal words, e.g.
    `Grass-Fed Bovine Collagen`, not `grass-fed bovine collagen`.
  - **Separate chips with COMMAS, ONE separator per field.** Item Highlights are
    **comma-separated** (`, `) Title-Case chips; the spaced en-dash ` – ` is reserved for
    the TITLE, so the two fields read as visually distinct units, not one merged line.
    Because the comma IS the separator, **no chip may contain an internal comma** —
    rephrase the chip if it would. Never mix separators in one field. Each chip must read
    as its own scannable unit, not a run-on phrase. Worked separator (AlphaInfuse
    serum, per-variation): `1 Month Supply, Lightweight & Non-Greasy Formula, For
    Thinning or Fine Hair, Thicker & Fuller-Looking, All Hair Types` (leading chip
    carries the pack size).
  - **Lead with the strongest USP**, then descend; front-loaded highlights are the
    ones shown when the field truncates in the grid.

  **Compliance + hygiene (same rules as the title):**
  - **Health-claim conform.** Ingredient/attribute **names** and use-case framing
    are factual (allowed); ingredient **effects** are health claims. Exclude them
    unless on the EU register at dose (see `eu-compliance-matrix.md`). No
    competitor brands.
  - **Do NOT repeat title tokens**: a covered keyword already counts; repeating
    it wastes the field. Spend it on genuine, uncovered USPs and high-SV
    attributes.
  - **QA gate: measure the IH's _incremental_ SV, not its SV.** Compute the tokens
    covered by every searchable field EXCEPT the IH, then check what the IH adds on
    top. If that increment is ~0, the IH is redundant and must be reallocated to the
    highest-SV genuinely-relevant terms still uncovered anywhere. This especially
    bites when the bullets/description are written or swapped by someone else (e.g.
    owner-supplied copy): an IH that was optimal against the old bullets can silently
    go to 0 increment once the visible copy changes. **Always re-audit the IH after
    any bullet/description edit.** Worked case (a DE supplement shake): owner bullets used
    "Protein" throughout, making a "Protein/Proteinshake" IH 0-increment; it was
    rebuilt around the uncovered, genuinely-true "Eiweißshake"/"Diätshake" compounds
    for +5,276 SV.

  Worked example (fictional collagen powder; title already holds *collagen,
  powder, peptides, hydrolyzed, type 1 & 3, 300g, bovine*):
  `Grass-Fed & Marine-Free, For Skin Hair & Nails, Keto & Paleo Friendly,
  Dissolves In Coffee, Non-GMO, 30 Servings`. Title Cased, **comma-separated** (the
  dash stays in the title), USP-led, no title tokens repeated, all factual attributes
  (no dosed effect claims). Note that **no chip contains an internal comma**. "For Skin
  Hair & Nails" drops it, and "Non-GMO" / "30 Servings" are their own chips, so the
  comma stays unambiguous as the separator.
- **5 bullets** ("About this item"): each a benefit-led micro-PAS (problem → agitate → solve),
  **Title-Case lead label (NOT ALL-CAPS)**; weave in mid-SV terms naturally.
- **Description**: longer copy covering remaining keywords + brand story +
  objection handling. (Often the biggest Ranking-Juice gap because it's empty.)
- **Backend search terms** (Generic Keywords / Search Terms field): the hidden
  index field. **≤250 bytes** (bytes, not characters: umlauts/accented chars cost
  2; stay under the cap or Amazon silently drops everything after it). Per Amazon's
  official guidance:

  **DO:**
  - **Use the full 250 bytes**: every unused byte is wasted ranking potential.
  - **Add synonyms & alternative spellings** (e.g. `Jacke` / `Jacket` / `Mantel`).
  - **Include common misspellings** of the product name; shoppers search with typos.
  - **Add long-tail keywords**: specific, high-purchase-intent queries.
  - **Add use-case & occasion** terms (e.g. `Geburtstagsgeschenk`, `Bürobedarf`, `Camping`).
  - **Add foreign-language keywords** when shoppers use them, e.g. English terms on
    a German marketplace if buyers actually search them.
  - **Write each word only once**: Amazon still indexes it for every combination.
  - **Separate words with spaces**: no commas or punctuation needed.
  - **Re-audit regularly**: at least quarterly or after any product change.

  **DON'T:**
  - **No repetition of title / bullet / Item Highlights / description terms**: Amazon
    indexes visible copy automatically; repeating it here wastes bytes. (This is why
    backend carries *only* what the visible fields don't.)
  - **No competitor brand names**: violates Amazon policy and can get the listing
    suppressed.
  - **No punctuation** (commas, semicolons, hyphens): wastes bytes with no benefit.
  - **No other products' ASINs or product numbers.**
  - **No irrelevant keywords**: Amazon penalises keyword-stuffing with off-topic terms.
  - **No offensive, discriminatory, or misleading terms**: leads to suppression.
  - **No prices or temporary claims** (`günstig`, `Angebot`, `neu`): they change and
    aren't indexable.
  - **No HTML tags or special characters**: not indexed.
  - **No quality claims or comparisons** (`besser als`, `Nr. 1`): policy violation.

  Misspellings, plural/grammar variants, and cross-language synonyms are exactly what
  backend is *for*. Keep them out of visible copy and put them here.
- **Never keyword-stuff.** Natural compliant copy beats density. Each keyword once.

## 4. Rufus / Alexa AI (semantic layer)

Amazon's AI search ranks by **meaning**, not exact match. Complementary to keyword SEO:

- **Noun-phrase stacking:** dense natural phrases stacking *product identity +
  key attribute + use case + audience* (e.g. "professional ceramic straightener
  for thick curly hair").
- **Inference mapping:** map customer needs → features, demographics → language,
  use cases → scenarios, likely questions → answers embedded in copy.
- Feed it customer **questions/needs** (from POE Customer Review Insights), not
  just keywords. Rufus thinks in questions. The builder surfaces these in
  `POE Semantic Insights` and `POE Raw - Reviews`.

## 5. Audit pass (close gaps)

After the first draft: compute Ranking-Juice coverage, list missed keywords by
SV, and optimize placement to close the gaps, without stuffing and without
breaking compliance.

## Final Action (workbook handoff)

Each triaged keyword gets a Final Action from
`{Use in copy, Backend only, A+ only, PPC only, Negative, Ignore}`: `Use in copy`
for relevant semantic opportunities, `PPC only` for competitor/brand terms,
`Negative` for wrong-form/off-product, `Ignore`/`Backend only` for the rest.
This is the bridge from triage to the actual copy + PPC/backend decisions.
