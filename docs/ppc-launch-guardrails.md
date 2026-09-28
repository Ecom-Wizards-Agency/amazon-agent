# PPC launch guardrails

This is the shared quality contract for new Ecom Wizards Amazon Ads campaigns. It applies to bulk files and console launches. Campaign-type details still come from the approved live campaign-structure source supplied for the task, normally the agency Figma board. Store private links in the gitignored run config, not in this repository.

## Required inputs

Do not build until the run has:

- the verified advertiser, marketplace, portfolio, budget, and start date;
- the approved campaign-structure reference for every requested campaign type;
- the product keyword workbook, including the Never-Ever or negation tab and the Campaign Structure tab when populated;
- verified own-brand names, aliases, misspellings, and own ASINs;
- current suggested bids for every keyword, ASIN, category, and Auto targeting group;
- product validation covering marketplace, brand, product type, parent-child variation, buyability, stock, suppression, and ad eligibility.

## Structure and naming

The approved campaign-structure card controls campaign type, targeting, bidding strategy, placements, target limits, landing page, and ad-group shape. A generic default cannot override a card.

- New agency campaigns end with `| EW`.
- The name must describe the live match type and targeting expression.
- Do not repeat fields such as `Auto | Auto`, `PAT | PAT`, or `Exact | Exact`.
- Do not add counters where the approved format does not use them.
- Derive every ad-group name mechanically from its campaign name: remove only the first goal token and the final `EW` token, keeping every middle token in the same order. Example: `Rank | SP | Exact | SKW | Widget | red widget | EW` becomes `SP | Exact | SKW | Widget | red widget`.
- When a real pack or child variation needs its own ad group, append one modifier to the final segment using ` - <variation>`, for example `SP | Exact | SKW | Widget | red widget - 3 pack`. Never copy the full campaign name into the ad group, remove extra middle tokens, or invent a variation.
- Exact, Phrase, Broad, Auto, ASIN Exact, and ASIN Expanded remain separate targeting strategies.
- SKW campaigns contain one target. Grouped Halo campaigns follow the approved target limit.
- When products have real child or pack variations, create separate variation ad groups. Do not place every product ad in one undifferentiated ad group.

## Branded and generic traffic

Classify the product before adding negatives. The own-brand dictionary contains brand tokens and aliases. It does not contain generic product descriptors.

- Generic campaigns, including Discovery, Phrase, Broad, Auto, generic Rank, Halo, Category, and competitor PAT, exclude every verified own-brand term as a campaign-level Negative Phrase.
- Discovery and PAT campaigns also receive the approved Never-Ever Negative Phrase list from the product workbook.
- Shield and other branded campaigns target own-brand queries and must not contain own-brand negatives.
- Any query containing an own-brand token is branded, including brand-plus-generic phrases.
- The preflight must reject a positive target blocked by Negative Exact or Negative Phrase.
- The preflight must reject branded targets in generic campaigns and generic targets in Shield keyword campaigns.

Example with the fictional brand `Acme`:

| Query | Intent | Route |
| --- | --- | --- |
| `blue supplement` | Generic | Discovery or generic Rank |
| `acme` | Branded | Shield |
| `acme blue supplement` | Branded | Shield |

## Auto campaigns

Create one Auto campaign per targeting group: Close Match, Loose Match, Substitutes, and Complements. Enable only the group named in that campaign and pause the other three. The group label is the disambiguator, so Auto names do not use a duplicate `Auto` token or a meaningless `01` counter.

## PAT self-targeting

- Exact self-targeting targets only verified own ASINs.
- Expanded self-targeting uses the same verified own ASINs as positive Expanded targets.
- Expanded self-targeting also adds those ASINs as Negative Exact product targets.
- Competitor ASINs never enter self-targeting campaigns.

## Bids and bidding strategy

Retrieve the current suggested bid for each target. Set its launch bid 30% below that target's suggestion and round half up to the nearest cent. The approved example is `0.75 -> 0.53`. Never apply one flat bid to targets with different suggestions.

The numeric target bid and the campaign bidding strategy are separate controls. Apply the exact strategy on the approved campaign-structure card. A mismatch blocks the build.

## Build and upload

Use separate create and update files. Update files require a fresh bulk export and real entity IDs. Create files remain paused unless the operator authorizes an enabled launch.

The technical preflight must block:

- missing structure, workbook, brand, product, or suggested-bid evidence;
- a name that conflicts with its targeting or match type;
- a generic campaign without campaign-level own-brand Negative Phrase exclusions;
- a Shield campaign with own-brand negatives;
- a positive-negative collision;
- the wrong bidding strategy;
- an Auto campaign with more or fewer than one enabled targeting group;
- an advertised product that has not passed product validation;
- a structure the builder cannot represent safely.

## Post-launch sanity check

Run the formal sanity check after Amazon processes the upload or console launch. Read the live account, not the source file alone.

Verify:

- advertiser, marketplace, portfolio, dates, state, and budget;
- campaign and ad-group names;
- match type, targets, targeting expressions, and Auto group states;
- bidding strategy, placements, and every target bid;
- advertised products and current eligibility;
- campaign-level and ad-group-level negatives;
- branded-versus-generic separation;
- Self-Targeting Expanded negative ASINs.

A processed upload is not completion. If a critical mismatch appears, keep the affected new campaign paused and prepare the exact correction. Apply another Amazon write only under the repository's approval rules, then repeat the live readback.

## Experiments and creative feedback

Before an A/B test, verify that the product is eligible and appears in the experiment selector or search. Record video creative ID, angle, product, and start date. Every review produces a metric-backed action for the designer: keep, iterate, replace, or pause.
