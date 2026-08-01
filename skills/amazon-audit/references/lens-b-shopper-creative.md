# Lens B: Shopper and Creative

Runs on `deep`, on a guaranteed **quarterly** pass for managed clients, or any time the tripwire
fires (which resets the quarterly clock). This is the half that needs a browser session and a POE
pull, which is the only reason it is not monthly.

### POE reviews and returns, at breadth

Pull wide, then **filter by positioning, not by hardware.** The related-niche graph bridges
categories through brands that span them, so a wide pull returns adjacent categories that share a
supplier rather than a shopper. On one run, 31 of 40 downloaded niches were the wrong category and
came out.

Average review and returns topics **across the relevant niches**, and show the niche count beside
each. Single-niche reads are noisy: one topic ranked eighth at 5.7% in the largest niche alone and
was the most-mentioned complaint at 10.6% across ten. Exclude topics appearing in only one or two
niches.

Pull only on the operator's explicit go: POE leaks viewed niches into the active Seller Central
account, so verify the account identity first. Never fabricate POE numbers. If the data has not
been pulled, keep the section as a clear next step that names the reads and the change each drives.

### Live creative capture

Read-only over the debug Chrome on port 9222, for the client **and the top two competitors**:

```
node tools/listing-capture/capture-cdp.mjs <ASIN,ASIN,ASIN> <out.json> [tld] [lang]
node tools/listing-capture/extract-amazon-listing-images.mjs <ASIN> [--marketplace com] [--out <file.json>]
```

**The extractors return image URLs and an A+ module count, not images.** Download the hi-res URLs
into `evidence/<client>/listing-capture/` and **read every file**. Every gallery frame and every
A+ module gets looked at, never inferred from alt text. On one audit that reversed three of seven
image recommendations, all of which were already implemented and would have shipped to a lead
whose agency had done decent work.

Two rules that came out of that run:

- **Duplication across the gallery and A+ is fine, not waste.** Shoppers split into swipers and
  scrollers, and repetition aids recall. If the strongest proof sits only in A+ below the fold,
  the fix is to put it in the gallery **as well**, not to move it.
- **Three-way beats two-way.** Comparing the client against two competitors surfaces findings
  neither single comparison shows, including advantages the client holds and does not display.

Build an image coverage matrix: for each thing the category rewards or punishes (from the POE
reads), is it covered, and where. The gap is usually coverage, not quality.

### The rest of Lens B

- **Category difficulty**: review and price moat, Ranking Juice listing gap. Rating targets are
  visual: 4.2 and 4.3 render the same star image, 4.5 is the half-star jump worth pushing toward.
- **Listing copy and compliance**: check live titles against the 75-character rule (effective
  2026-07-27) and flag as time-critical when non-compliant; use the forced rewrite to front-load
  target keywords. Check claims where the category is regulated.
- **Indexing, and check the Product Type field.** The Product Type field assigns keyword indexing
  independently of the listing text, so a wrong product type kills organic rank while ads keep
  serving. **Organic gone while ads still run is the signature.** Check it per child ASIN, not
  once per family. Also watch for styled Unicode "bold" glyphs in a title, which are invisible to
  search matching, and empty backend attribute fields, which make the listing invisible to
  left-rail filtered traffic. On a greenfield or relaunch, indexing comes before spend: even a
  large bid buys nothing on a term the listing is not indexed for.
- **Judge CVR inside its AOV band, never against a blanket number.** Conversion rate correlates
  strongly and inversely with average order value, so an 8%-is-good rule of thumb is wrong at both
  ends. Base CVR is set by competitive position, roughly 1% for a weak overpriced product against
  20 to 30% for best-in-class on non-brand terms.
- **Price.** At ASIN level price and CVR move close to one-for-one inverse, and sensitivity
  concentrates above roughly $60 and on increases beyond about 30 to 40%. A naked increase of
  16 to 17% once cut CVR by 30 to 40%, while **the same increase executed as a higher anchor price
  with a coupon back to the target price held the damage to about 10%**. Because RPC is price times
  CVR, and RPC drives the bid formula, **every price or coupon change silently reprices every
  correct bid in the account**. Say so when recommending one.
- **Reviews.** A rating falling from 4.5 to 4.0 materially hurts both CTR and CVR. When a single
  ASIN's conversion drops, a prominent bad photo review is a named first check.
- **The shopper's-eye test**: leave the dashboards and look at the search page. Why would a
  shopper pick this listing over the row of alternatives at their price, with their review counts,
  with their main image? If the honest answer is "they wouldn't", that is the headline and no bid
  change fixes it.

---
