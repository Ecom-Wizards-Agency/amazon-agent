# Creative Reference & Asset Library

The standing document behind every brief. It holds what stays true between tests, so brief number two is cheaper than brief number one.

**One document per PRODUCT LINE, not per client.** A client selling collagen and a diet shake needs two. The shelf, the claims and the shopper language are different, and mixing them produces a brief that leads on the wrong criterion.

**Evergreen.** No performance numbers, no baselines, no dated decision log. Anything that changes with a reporting window belongs in the brief. If a section would be stale in six weeks, it does not go here.

Delivered as a branded Google Doc, no cover, alongside the briefs in the client's Drive creative folder. Named `<Client> <Market> - <Product Line> - Creative Reference & Asset Library`.

## Structure

```
# <Client> <Product Line>: Creative Reference & Asset Library
<product line, market, language, last reviewed>
<one reference doc per product line note>
<evergreen note>

## How to use this document
## 1. Product and claim master
## 2. The shelf map: what the tiles already say
## 3. Cluster coverage
## 4. The shopper's own language
## 5. Footage inventory and asset requests
```

## How to use this document

Three or four sentences: this is the standing reference behind every brief, it contains no scripts, testing method, or results, what each section is for, and when it gets updated. Update it before the next brief when product facts, shelf conditions, shopper language, or assets change.

## 1. Product and claim master

- **The catalogue.** One row per ASIN: ASIN, product, size, role in the line.
- **What the product is.** Form, hero ingredient, origin, certifications, who it is for. One short paragraph.
- **The price constraint.** Our price band against the shelf median, per shelf. Then one line on what that forces creatively: a large price gap means the video has to earn the premium in two seconds, parity means it only has to differentiate. This is the single most load-bearing fact in the document.
- **What we may say, verbatim from the live listing.** A bullet per approved phrase, quoted exactly. Scripts draw from this list and nowhere else.
- **Standing claim decisions.** Operator or founder authorisations that persist, with the residual risk and the fix that removes it. Plus standing rules such as "no videos for branded keywords".
- **What needs substantiation before it goes on screen.** Claims that are live in the listing but not yet provable on file.
- **Never on screen or in voiceover.** The categorical bans.

## 2. The shelf map: what the tiles already say

One table per shelf:

| Claim already taken | Who says it |
|---|---|

Quote the competitor's own title wording and name the brand. Then two lines: which claim is the **category default** (leading on it wins nothing), and what is **still open**.

This section is why the brief no longer needs a "shelf says" block. It exists so no brief burns its one claim on something a cheaper competitor already says.

## 3. Cluster coverage

| Cluster | Search volume | Our organic rank | Creative coverage |
|---|---|---|---|

Coverage means whether a video exists for that shelf, not how it performed. Add short notes for micro-shelves we already own, and for clusters that are **not creative problems** (CTR already at shelf rate, or wrong-intent traffic) so nobody briefs them by mistake.

## 4. The shopper's own language

From POE review mining, per shelf, split into what they praise and what they complain about. Give the mention percentage and the verbatim snippets.

Close with the design translation: which complaints are filmable and claim-free. That is usually the safest and most differentiated territory the brand has, and it is what the texture and after-feel angles are built from.

## 5. Footage inventory and asset requests

Keep the heading even when no source is verified. Use one row per asset:

| Asset | Verified source link | Orientation | Resolution | Editor suitability | Rights status | Crop, reshoot, or production instruction |
|---|---|---|---|---|---|---|

Use exact Drive or pCloud links. State whether each asset is editor-ready, reference-only, or unsuitable. Do not infer rights. Record `not independently verified` when that is the real status.

Missing required footage becomes an exact production gap with the shot, orientation, resolution, and action needed. Missing strategy direction is not a blocker and does not become a fake footage request.

## Rendering

Same pipeline as the brief: `tools/amazon-ad-audit/render_branded.py` with `cover=False`, run from the repo `.venv` python, with a `metrics.json` containing no `custom_kpis` so the KPI card strip is suppressed. Keep the source markdown in `output/<client>/creative-reference/`.
