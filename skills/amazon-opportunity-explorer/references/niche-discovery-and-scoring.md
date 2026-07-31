# Niche discovery and scoring (POE breadth run)

Method for going beyond the handful of niches Amazon attaches to a brand's own ASINs, into
20 to 40 candidate niches, then filtering and weighting them. Derived from the Heusom US run
(2026-07-30, pet nail grinder), which discovered 259 niches from 14 seeds.

`merchant-niches` alone is not enough. It returns only the niches the brand's own ASINs
already sit in, which is a self-referential view: on Heusom it returned 6, of which 2 were
the brand's own name, leaving 4 real category niches. Breadth changes conclusions, so run it.

## 1. Seed

Pick 12 to 18 seed queries spanning **angles**, not synonyms. Synonyms collapse to the same
niche and waste the run. Angles that generalise:

- the product itself, and each competing **form factor** for the same job
- **who it is used on** (species, life stage, size, skin or coat type)
- the **problem** the shopper is trying to solve, in their words
- **adjacent products** bought in the same session or by the same owner
- **consumables and accessories** for the product

Seeds are cheap; full niche downloads are not. Search widely, download selectively.

## 2. Collect

```bash
node tools/opportunity-explorer/run-poe.mjs batch \
  --queries "seed1,seed2,..." --marketplace <cc> --client <slug> \
  --expect-account "<Brand>" --top 40
```

`batch` searches each seed, unions and dedupes by `nicheId` **in relevance order**, then
downloads each kept niche in full. The full download is what carries `searchTermMetrics`
(per-term T90 volume, conversion rate, click share) and `nichePdr` (review, star-rating and
returns insights), so always take the full pull, not just the related-niches grid.

`--top N` caps the full downloads, but the per-seed `*_related-niches.{json,csv}` files
record **every** niche found. Those files are the filtering input; state how many were
discovered versus downloaded, and never imply the downloaded set is the whole set.

## 3. Filter for relevance FIRST, before any scoring

**The relevance test is the same buyer and the same job, not the same hardware.** A product
aimed at women whose category men also search is the SAME niche: same shelf, same job, one
segment of the same buyer. A product for humans when the brand is a pet brand is a DIFFERENT
niche, no matter how similar the device is. Positioning, not mechanism, decides.

On Heusom this mattered twice:

- **31 of 44 downloaded niches were rotary-tool and DIY hardware** (drill press, carbide burr,
  soldering torch, oscillating saw blades). Every seed was a pet term. POE's relatedness graph
  bridged into the hardware world by itself, because Dremel is a real brand spanning dog nails
  and workshops. **Expect POE to bridge categories through any brand or component that spans
  them**, and strip that cluster with a vocabulary blocklist.
- **3 niches were human nail care** ("nail drill" at 3.66M T90 volume). Superficially the same
  device, genuinely a different buyer. Heusom is a pet brand, so these are OUT. Volume is not
  a reason to keep an irrelevant niche.

A ~25% relevance hit rate is normal and is not a failure of the run. Report the hit rate.

## 4. Score what survives

Volume is the base of opportunity, never opportunity itself. Weight it down:

| Field (from `nicheSummary` / last `trendsMetrics`) | Use |
|---|---|
| `searchVolumeT90` | base size |
| `searchVolumeGrowthT90`, `...T360` | trend; a shrinking niche is worth less than its size implies |
| `top5ProductsClickShareT7` | **openness.** High concentration means someone owns the shelf |
| `searchConversionRate` | whether the niche converts at all |
| `returnRateT360` | margin risk and review risk |
| `avgPrice` | distance from the brand's price; a large gap predicts poor generic conversion |
| `productCount`, `avgOosRateT7` | crowding and supply gaps |
| `avgRatingsOfProducts` | the rating bar to clear |

A workable shape is volume x openness x trend, then filter on product fit and price distance.
Tune per category; the point is that concentration and trend must appear, not the exact formula.

Heusom's result shows why: "dog nail grinder" (954k volume) scored near the bottom because
**95% of clicks sit in the top 5** and volume fell 15% in the quarter, while "cat nail clipper"
(592k, growing 9%, 74% concentration) scored far higher.

## 5. Read the aggregate review data across niches, not one niche

Per-niche `nichePdr` is noisy. Averaging topics across every relevant niche, and recording in
how many niches each topic appears, turns it into a category truth. On Heusom the single-niche
read was wrong twice against the 10-niche read:

- **Charging** looked minor at 5.7% and eighth in one niche; across ten it was the **number one**
  complaint topic at 10.6%, present in 9 of 10.
- **Size** was 8.8% of returns in one niche and **13.8%** across ten.

What held everywhere: functionality (27.5%) plus advertised-vs-actual (23.2%) were **51% of all
returns** in 10 of 10 niches, and ease of use was the dominant positive star-rating driver
(+1.90) in 10 of 10. Those are safe to build creative on. A topic appearing in 1 of 10 is not.

## 6. Output shape: a short action list on top of the full map

Default, set by the operator 2026-07-30: deliver **both, layered**. A ranked shortlist of 3 to 5
niches to act on, each with a concrete route in, sitting on top of the complete scored map. The
shortlist is what gets read and worked; the map is what proves the shortlist was chosen rather
than guessed, and it is what makes the category legible to a client or lead. Do not ship the map
alone (nobody acts on 40 rows) and do not ship the shortlist alone (it looks like an opinion).

Cover **both greenfield and recovery**, with two conditions:

- **Greenfield only where the niche is genuinely relevant to the product.** Volume never buys
  relevance. Apply the section 3 test first, then let a greenfield niche compete on score.
- **Every entry is justified with numbers.** Name the volume, the concentration, the trend, the
  price distance and the rating bar. A niche recommended without those is an assertion.

Recovery niches usually rank first when the brand already earns clicks and loses the cart,
because the demand is already arriving and only the conversion step is broken.

## 7. Turn it into creative, with the honest caveat

Mirroring shopper vocabulary lifts click-through. It does **not** automatically lift conversion,
and it can raise returns when the borrowed words overpromise, which is the exact mechanism
behind advertised-vs-actual. Mirror the vocabulary only where the claim is provable, and put a
number next to it.

Before recommending vocabulary work, check **where the funnel actually breaks**, using SQP
indexed against the market: click-through rate against market, then cart-adds per click, then
purchases per cart-add. On Heusom, click-through was 1.19x market on generic while cart-adds
per click were 33.2% against a market 46.6%. The listing was winning the click and losing the
detail page, so title and main-image vocabulary was the wrong surface. Diagnose before
prescribing.

## Gotchas

- **Account identity.** POE attributes viewed niches to the active Seller Central account.
  Always pass `--expect-account`, and never browse a client's niches from another account.
- **Trailing windows only.** POE cannot be re-fetched for a past period. Capture, then archive.
- `percentOfMentions` is **already a percentage**. Do not multiply by 100.
- Several numeric fields arrive as strings. Coerce before formatting.
- Review and returns insights are **niche-wide**, never per-ASIN. Say which complaints attach to
  the brand's own listing and which are the category's; they imply different fixes.
