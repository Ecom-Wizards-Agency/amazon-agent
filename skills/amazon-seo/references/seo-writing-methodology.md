# SEO Writing Methodology (condensed, in-repo)

Condensed, team-shareable version of the Ecom Wizards SEO method so the skill is
runnable from the repo alone (no Obsidian vault required). The vault
(`<your-vault>/Skills/`: `amazon-seo-writer`,
`keyword-classifier-and-filter`, `rufus-optimization`, `conversion-offers-and-copy`)
remains the deeper source. Always pair with `eu-compliance-matrix.md`.

Two phases run in order: **classify keywords → write copy → audit coverage.**

---

## 0. Verify the product before you write it

Every rule below optimises *how* a claim is worded. None of them catches a claim that is
simply **not true of the product**, and that is the failure that survives longest: it passes
the separator gate, the caps gate, the character caps and the compliance ladder, because all
of those inspect wording. Ranking Juice even rewards it, since the false attribute is usually
a high-SV head term. It surfaces months later in the reviews, which is the most expensive
place to find it.

**Before writing a single field, obtain the product's actual attributes from a primary
source and record which one you used.** Source hierarchy, best first:

| Rank | Source | Note |
|---|---|---|
| 1 | Pack artwork PDF, finished-label file, or the manufacturer's formulation spec | The only label-verified sources. Ask for them by name; "the spec" often means a carton-dimensions sheet. |
| 2 | The brand's own published ingredient list (DTC product page, Shopify `/products/<handle>.json`) | Usually accurate and immediately available. Brand-published, not label-verified: say so in the workbook. |
| 3 | A physical unit, photographed back-of-pack | Definitive for what shipped, but tells you nothing about the next batch. |
| 4 | Reviewer reports of the ingredient list | Corroboration only, never the basis for a change. Reviewers misread lists. |

**The listing's own attribute fields are NOT a source.** They are the thing under audit. A
live `Ingredients` field can carry a sibling SKU's list from a bulk upload, and it will look
entirely plausible. Worked case (NZ botanical body wash, 2026-08-31): the live `Ingredients`
value was the brand's *balm* INCI, anhydrous and surfactant-free, so it could not describe a
wash at all. Nobody had compared it to the product because it read like a real ingredient
list. It had also silently poisoned the workbook's compliance reasoning, which recorded
"contains beeswax, so not vegan" from that wrong list and therefore suppressed a rankable
token the product could legitimately have carried.

Three checks that follow from having the real list:

- **Free-from claims are decided by the ingredient list, not by the brand's marketing.** A
  brand page saying "fragrance-free" does not survive an INCI that declares Geraniol,
  Limonene, Linalool, Citral and Farnesol. The accurate claim is **"no added fragrance"**;
  the product is naturally scented by its botanical oils. Same test for sulfate-free,
  paraben-free, vegan and cruelty-free: confirm each against the list, and drop the ones the
  list cannot support. Getting this wrong is not only a compliance issue, it is a review
  magnet, because the shopper meets the truth in the shower.
- **An operator-approved inaccurate attribute is still a defect, just a scheduled one.** When
  an ingredient claim is directed into copy against the evidence, logging it is necessary but
  not sufficient. Record it in the Claim Guardrail row **with a review date**, because the
  cost arrives on someone else's desk. Worked case (same listing): the workbook recorded
  "operator-directed; product is leaf oil, false-ingredient risk accepted" and shipped. Seven
  weeks later four of the first ten Vine reviews described the product as containing the
  absent ingredient, and the lowest-scoring review of the set was titled "good formulation
  undermined by key ingredient discrepancies".
- **Read the existing reviews before rewriting an established listing.** Where several
  reviews open by *correcting* the listing, the copy has an expectation gap, and that gap is
  a conversion defect the keyword data cannot see. Fix it by stating the trait as a feature
  in the highest-visibility slot available, not by hiding it. Worked case (same listing):
  six of ten reviews opened by explaining that the wash does not lather, against imagery and
  a bullet promising "soft, creamy lather". The fix was an Item Highlights chip 1 reading
  `Soap-Free, Low-Foam Cleanser`, which is the one chip mobile search reliably renders.

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
from the complete keyword pool filtered at 1%) and the **Outlier triage** categories
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

- **Identity is a ranking and conversion requirement, not expendable copy.** Start the
  title with the consumer brand and recognizable product-line name, then place the tracked
  head term. Record both phrases in `seo_identity`; the builder requires them in the title
  and description. The tracked-lead gate ignores declared own-brand/product-line tokens, so
  there is no reason to delete identity to satisfy it. For a blend, describe the formula
  accurately, but do not replace the actual product name with a generic phrase such as
  `Supplement Blend` or `Liquid Formula`.
- **No ALL-CAPS in any visible field** (title, Item Highlights, bullets, description).
  Amazon "Product detail page rules" (Seller Help G200390640): *"Use capital letters
  only for the first letter of each word. Do not use all capital letters throughout the
  attribute."* Use **Title Case** for the title, each highlight, and bullet lead labels
  (`Scalp Nourishing Daily Serum:`), never `SCALP NOURISHING DAILY SERUM:`. Sentence case
  is fine for bullet/description bodies. Optimise the visible fields for the **shopper's
  eye** first (readable, scannable); the exact separator/caps style is flexible as long
  as it reads cleanly and stays within this no-all-caps rule.
- **THE SEPARATOR CONTRACT (the two fields must not match; get this backwards and both
  are wrong).** One line to remember: **the TITLE takes the en-dash, Item Highlights take
  the middot.**

  | Field | Separator | Never use |
  |---|---|---|
  | **Title** | spaced **EN-dash ` – `** (U+2013, not a true em-dash, not a hyphen `-`) | a comma as the *clause* separator |
  | **Item Highlights** | spaced **MIDDOT ` · `** (U+00B7) | ` – `, ` — `, ` - `, ` \| ` |

  **Why they differ (corrected 2026-07-26 against real renderings).** The original
  rationale was that the two fields merge into one unreadable line. That is wrong, and it
  is worth writing down so nobody rebuilds the argument. Amazon marks the boundary itself,
  differently per surface:

  - **Mobile search card**: brand on its own line, then the title in black, then the Item
    Highlights on a NEW LINE in smaller grey type. No pipe. The seam is typography.
  - **Mobile PDP**: same split, highlights in grey under the black title. No pipe.
  - **Desktop PDP**: the two are joined into one string with a ` | ` that Amazon inserts.
    Verified by comparing the stored fields (neither contains a pipe) with the rendered
    title.

  So the separator choice is NOT what keeps the fields apart. The reason the two fields
  still take different marks is narrower and holds anyway: **the mark must not have a
  second job on the same line.** A hyphen is a clause break, a compound-word joiner
  (heavy in DE/NL) and, in most brand titles, the title separator too. A comma is the
  natural grouping mark inside a chip. The middot has no other job, which is also what
  lets a chip carry its own internal comma list. Worked live example (Acme DE):
  `Hochdosiertes Rinderkollagen · geschmacksneutral, laktosefrei, löslich, ohne
  Zusatzstoffe · Made in Germany` needs two punctuation levels; only a non-comma outer
  mark can express it.

  **Why the dash in the title.** A title is clause-shaped (brand, then product, then
  qualifier) and a dash is what reads as a clause break. Not the hyphen `-`, which already
  lives inside words (`Puncture-Resistant`), so the same character would be doing two jobs
  in one line. Not the em-dash `—`, which is visually heavy and dominates a 75-character
  title. The en-dash is the same break with less weight.

  **Why the middot in the highlights.** Chips are list items, not clauses. A dash says "the
  sentence continues, here is an aside"; a middot says "these are separate things", which
  is what the field actually contains. Both marks cost 3 characters, so this is about what
  the mark signals to a reader, not about space.

  **Why not the comma** (this was the rule until 2026-07-26). A comma already has a job
  inside phrases, so it can never be an unambiguous delimiter. That is why the old rule
  needed a patch banning commas inside a chip, forcing rewrites like `For Dry, Crepey-Looking
  Skin` into `For Dry Crepey-Looking Skin`. When a separator makes you reword the content
  around it, the separator is wrong, and in practice the comma version reads as a run-on.
  The middot has no such collision, so **a comma inside a chip is now fine** and needs no
  workaround.

  Sub-rules that follow from it:
  - **A comma *inside* a title clause is fine** (`for Dry, Sensitive Skin`); what is
    forbidden is using a comma where the clause break belongs (`Body Oil for Women, After
    Shower Oil` should be `Body Oil for Women – After Shower Oil`).
  - **Never mix separators inside one field.** One separator per field, always.
  - **Never mix separators inside one field.** One separator per field, always.
  - The repo's no-spaced-em-dash rule governs **prose** (narratives, notes, chat, commit
    messages, docs), NOT the title field, so the workbook builder must not strip the dash
    from title copy.

  **Enforced, not remembered.** `build_keyword_workbook.py` ships a QA gate: Item
  Highlights **FAIL** the build on a dash or pipe separator, or when no ` · ` separator is
  present at all, and a title that uses a comma as its clause separator raises a
  **warning**. The gate exists because this rule was prose-only until 2026-07-26 and had
  drifted into four different conventions across live client files (en-dash, comma, hyphen
  and `·`), so older `seo_content.*.json` files may fail the gate until their separators
  are corrected. Note the contract itself was revised on 2026-07-26 from comma to middot
  (operator decision, on readability), so files written to the comma version need their
  Item Highlights re-joined with ` · ` on their next rebuild.

- **Bullet contract (operator rule, 2026-07-26).** A bullet is `Label: Sentence`.
  - **Capitalise the word after the colon.** It opens a sentence, so it is `pH Balance for
    Women: A daily vaginal probiotic gummy…`, never `: a daily…`. A numeral-led sentence
    (`30 Gummies, Made to Quality Standards: 30 women's probiotic gummies per bottle`) is
    correct as-is; capitalise the first *word*, and do not reach past a numeral to
    uppercase the first letter you find.
  - **No asterisk inside a bullet.** The asterisk is a disclaimer-linking device. Inside a
    bullet it renders as literal punctuation in the search grid and in mobile snippets, and
    it promises a footnote the bullet cannot show. Put the DSHEA or compliance disclaimer in
    the **description**, as a complete standalone sentence. Removing the asterisk does not
    remove the disclaimer and does not, on its own, make hedged structure/function copy
    riskier: what carries the legal weight is the disclaimer being present on the detail
    page and the claim content itself staying inside structure/function. See
    `health-claims-compliance.md`.
  - **Build-enforced**: the build FAILS on a lowercase word after `Label:` or on any
    asterisk in a bullet.
  - **Length cap, build-enforced (operator rule, 04.09.2026): each bullet stays within
    250 characters including spaces.** Long bullets truncate on mobile and Amazon's
    per-category caps vary, so the workbook build FAILS on any bullet over 250.
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
  - **Separate chips with MIDDOTS, ONE separator per field.** See the separator contract in
    §3: Item Highlights are **middot-separated** (` · `) Title-Case chips; the spaced en-dash
    ` – ` is reserved for the TITLE, so the two fields read as visually distinct units, not
    one merged line. The middot carries no grammatical meaning, so a chip may keep its own
    internal comma without ambiguity. Never mix separators in one field. Each chip must read
    as its own scannable unit, not a run-on phrase. **Build-enforced**: a dash or pipe
    separator, or the absence of ` · `, FAILS the workbook QA gate.
    Worked separator (Acme serum, per-variation): `1 Month Supply · Lightweight &
    Non-Greasy Formula · For Thinning or Fine Hair · Thicker & Fuller-Looking · All Hair
    Types` (leading chip carries the pack size). Worked separator where the lead chip
    carries the head keyword instead (Acme body oil): `Body Oils for Women ·
    Fast-Absorbing & Non-Greasy · For Dry, Crepey-Looking Skin · Warm Vanilla Scent ·
    4 Fl Oz` (under the middot rule that chip keeps its natural internal comma).
  - **Lead with the strongest USP**, then descend; front-loaded highlights are the
    ones shown when the field truncates in the grid.
  - **HOW HARD IT TRUNCATES (measured 2026-07-26, Amazon mobile app, DE search results).**
    On a live 123-character Item Highlights value with three middot chips, the mobile
    search card showed only the FIRST chip before the ellipsis:
    `Hochdosiertes Rinderkollagen …` (about 28 characters of 123). Chips two and three,
    which carried the whole free-from block and `Made in Germany`, never appeared in
    search at all. They only became visible on the PDP.

    Consequence, and it outranks every formatting rule in this section: **chip ORDER
    matters far more than the separator glyph or the total character count.** Treat chip 1
    as the only chip guaranteed to be read in mobile search, and spend it on the single
    strongest differentiator that is NOT already in the title. Everything after chip 1 is
    PDP copy plus keyword indexing, both of which are real but neither of which wins the
    click.
  - **Brand dedup in the mobile search card (same capture).** The card printed the brand
    on its own line and then the title WITHOUT its leading brand token, even though the
    stored `item_name` starts with the brand. So a brand-first title neither costs nor
    gains display space in mobile search; the brand shows regardless. Do not add a second
    brand mention to compensate.

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
    **NOW BUILD-ENFORCED** (added 2026-07-26): the builder computes this increment and
    FAILS at 0, so a redundant IH can no longer ship. It had been prose-only guidance,
    which is exactly how one shipped.
  - **BUILD-ENFORCED: the ≤75 title and ≤125 IH caps.** Both were prose-only until
    2026-07-26 and neither was measured, so an over-length field passed every gate.
    They are now hard FAILs. **Convention the caps depend on: the FIRST LINE of the
    New Listing cell IS the publishable copy; rationale goes on the lines below it.**
    The title lead-token gate already assumed this. A cell that opens with prose
    ("RECOMMENDED (72 chars): '…'") now fails the cap until it is reordered copy-first.
  - **BUILD-ENFORCED (warning): the keyword-dump shape.** If more than 40% of chips are
    bare single words and there are ≥4 chips, the build warns. Rationale: a token list
    ("Men's · Undershirt · Vest · Chest · Girdle · Tight · Tops") maximises the coverage
    metric while failing the field's primary job, and the separator gate passes it
    happily. A second warning fires when the IH repeats a token the title already covers.
    Worked negative case (Acme US men's compression tank, 2026-07-26): an 11-chip
    single-word IH was rejected by the operator on sight. Rewritten as five attribute
    phrases it scored **identically**, because the whole increment came from three tokens
    (`tops`, `girdle`, `tight`) that fit inside readable chips or moved to backend. Then
    the new increment gate showed even that version bought only 5,665 SV once the bullets
    were counted, and reallocating to the uncovered `shaping`/`hiding`/`male` cluster took
    it to 25,734. **Readability and coverage were never in conflict; the dump was just
    lazy.** Where a high-SV token genuinely will not sit in readable copy, put it in
    **backend**, not in a field the shopper reads: `girdle` (22,802 SV) went to backend
    precisely because it reads dated to a male audience.
  - **Per-variation lead chip.** When children differ on a dimension the title no longer
    carries (because the ≤75 cap evicted it), lead each child's IH with **its own
    variation value**. That account's colour attribute encodes pack too (`1 Pack Black`,
    `3 Pack White`), so without it a 3-pack was indistinguishable from a 1-pack in the
    search grid at three times the price. Cost nothing in coverage there, because the
    description already carried the colour and size tokens: check that before spending
    the characters.
  - **Accent folding (fixed 2026-07-26).** The coverage tokeniser strips diacritics on
    both sides now. Before that, `compresión` shredded into `compresi` + `n`, so every
    accented keyword read as uncovered and a bogus 1-char `n` token appeared to gate
    44,418 SV on a US listing with Spanish demand. Any ES/FR/IT workbook built before
    this date under-reports its coverage.

  Worked example (fictional collagen powder; title already holds *collagen,
  powder, peptides, hydrolyzed, type 1 & 3, 300g, bovine*):
  `Grass-Fed & Marine-Free · For Skin, Hair & Nails · Keto & Paleo Friendly ·
  Dissolves In Coffee · Non-GMO · 30 Servings`. Title Cased, **middot-separated** (the
  dash stays in the title), USP-led, no title tokens repeated, all factual attributes
  (no dosed effect claims). Note that "For Skin, Hair & Nails" keeps its natural comma:
  under the middot rule that is no longer ambiguous.
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
    This includes **category-typical ingredients the product does not contain**. Carrying a
    competitor's format (`goat milk`, `oatmeal`, `colloidal`) buys traffic the listing cannot
    convert and is the same accuracy problem as a false visible claim.
  - **No attribute the visible copy is not allowed to state.** Backend is for terms the
    visible fields *could* carry but should not spend characters on (misspellings, synonyms,
    long tail). It is **not** a place to park a claim that failed the accuracy or compliance
    check: an untrue term is untrue in a hidden field too, and disease terms for a cosmetic
    read as drug claims wherever they sit. Route by posture, per
    `health-claims-compliance.md` (regulated + conservative skips backend for outright
    disease terms), and record the decision rather than inheriting it from the last version.
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

**Then run the gates before anything is delivered or published.** The mechanical gates
enforced by `build_keyword_workbook.py` include the 75-char title cap, the 125-char Item
Highlights cap, the Item Highlights separator, and the Item Highlights **incremental**-SV
check. That last one has a trap worth naming: it is measured against the other searchable
fields, so **editing the bullets can silently take a previously-optimal IH to zero
increment**. Any bullet or description edit obliges a rebuild, not just a reread.

The builder also fails delivery when identity, POE traceability, or regulated-claims
evidence is missing:

- **The §0 attribute verification.** Name the source you used in the workbook.
- **POE traceability.** The Semantic / Alexa row must record at least one POE Search Terms
  signal and at least one POE Reviews or Returns signal, with the copy decision each caused.
  Populating POE raw tabs without applying them to the SEO is not semantic optimization.
- **The health-claims self-check** (`health-claims-compliance.md`), which is **mandatory
  before delivery for every `regulated`-tier deliverable**: supplements, foods with health
  angles, health and beauty, topicals, medical-adjacent devices. A topical sold against a
  named skin condition is regulated tier even when the copy itself is careful, so the check
  is owed on the rewrite, not only on the original. Record it in the Claim Guardrail row
  with its date and evidence file; `checked=true` without those records fails.

## Final Action (workbook handoff)

Each triaged keyword gets a Final Action from
`{Use in copy, Backend only, A+ only, PPC only, Negative, Ignore}`: `Use in copy`
for relevant semantic opportunities, `PPC only` for competitor/brand terms,
`Negative` for wrong-form/off-product, `Ignore`/`Backend only` for the rest.
This is the bridge from triage to the actual copy + PPC/backend decisions.
