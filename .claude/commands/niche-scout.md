# /niche-scout: discover, filter and score POE niches for a brand

Go wide in Product Opportunity Explorer: 12 to 18 seed queries, 20 to 40 candidate niches,
then filter for relevance and weight them against each other. Answers "where is the winnable
demand and what does the category punish", which the brand's own 4 to 6 auto-assigned niches
cannot. Read-only.

Load the `amazon-opportunity-explorer` skill first. Method:
`skills/amazon-opportunity-explorer/references/niche-discovery-and-scoring.md`.

The target is: $ARGUMENTS

## Steps

1. **Confirm scope** if not given: client slug, marketplace, the product, and **how the brand is
   positioned**. Positioning decides relevance, so do not skip it. Output shape does not need
   asking: the default is a ranked shortlist of 3 to 5 niches to act on, layered on top of the
   full scored map.
2. **Verify the account.** `node tools/opportunity-explorer/run-poe.mjs doctor`. POE attributes
   viewed niches to the ACTIVE Seller Central account, so a wrong-account run both corrupts the
   data and leaks browsing into another client. Stop if it is not the sanctioned account.
3. **Seed by angle, not synonym**: the product, each competing form factor for the same job,
   who it is used on, the problem in shopper words, adjacent products, and consumables.
4. **Collect:**
   ```bash
   node tools/opportunity-explorer/run-poe.mjs batch \
     --queries "seed1,seed2,..." --marketplace <cc> --client <slug> \
     --expect-account "<Brand>" --top 40
   ```
   Take the full pull, not just the related-niches grid: `searchTermMetrics` and `nichePdr`
   only come with it. Report discovered versus downloaded; never imply the downloaded set is all.
5. **Filter for relevance BEFORE scoring.** Same buyer and same job, not same hardware. A
   different segment of the same buyer is IN (a women's product men also search). A different
   species or population is OUT (human vs pet), whatever the volume. Expect POE to bridge into
   unrelated categories through any brand or component spanning them, and strip that cluster.
   A ~25% hit rate is normal. Report it.
6. **Score** volume discounted by top-5 click-share concentration and trend, then filter on
   product fit and price distance. Volume alone is not opportunity: a huge niche whose top 5
   hold 95% of clicks is a wall, not an opening.
7. **Aggregate `nichePdr` ACROSS niches**, with the count of niches each topic appears in.
   Single-niche reads mislead. Build creative only on topics that recur.
8. **Diagnose before prescribing creative.** Index SQP against the market: click-through, then
   cart-adds per click, then purchases per cart-add. Vocabulary work lifts click-through; if
   click-through already beats market, the fix is on the detail page instead.
9. **Deliver both layers.** A ranked shortlist of 3 to 5 niches with a concrete route in, on top
   of the full scored map, plus the cross-niche review and returns read. Cover greenfield and
   recovery, but greenfield only where the niche is genuinely relevant to the product, and
   **justify every entry with numbers**: volume, concentration, trend, price distance, rating
   bar. In an audit the map is a MASTER workbook tab, not narrative body: 40 niches drowns prose.

Stop rules: read-only, no listing or campaign changes. POE serves trailing windows only, so a
missed capture cannot be re-fetched; capture, then archive with `run-poe.mjs archive`.
