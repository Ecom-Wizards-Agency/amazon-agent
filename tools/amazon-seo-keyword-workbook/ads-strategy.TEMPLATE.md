# Ads Strategy — LOCAL TEMPLATE

Copy this file to `_local/ads-strategy/strategy.md` (gitignored, never committed) and fill it with your
advertising methodology. Together with `strategy.json` (copy of `ads-strategy.TEMPLATE.json`, same folder)
it drives the Campaign Structure fill of the keyword workbook:

- `strategy.json` — mechanical thresholds and naming; read by `fill_campaign_structure.py`.
- `strategy.md` (this file) — the prose theory the AGENT reads to make judgment calls the script cannot.

Refresh rule: the source of truth for the strategy is your team's playbook system (for Ecom Wizards:
Notion). An agent with Notion access (Claude) should refresh this file from the source pages listed in the
header below when it is stale. Agents without Notion access (Codex) must use this file as-is and ask the
operator if it is missing or outdated — never guess thresholds.

---

## Header (fill in)

- Source pages: `<list your playbook page names/IDs here>`
- Last refreshed: `<YYYY-MM-DD>`
- Owner: `<who maintains this file>`

## What the agent must decide (judgment calls — write your rules for each)

1. **Intent tiering** for Rank/Shield SKW waves: which keywords are close, high-buying-intent words
   (Wave 1) vs high-volume low-intent (Wave 2) vs very broad/supplementary (Wave 3)?
   `<your definitions and examples>`
2. **Discovery root specificity**: which root keywords are specific enough for a BMM/Phrase campaign?
   `<your rule, with a good and a bad example>`
3. **Halo grouping**: how to theme long-tail keywords into halo campaigns (by root/word group)?
   `<your rule>`
4. **PAT strength**: how to call Stronger vs Weaker competitors when revenue data is missing?
   `<your fallback signals — rating, review count, market knowledge>`
5. **Promotion from the review band**: when does a keyword outside the mechanical bands still deserve
   a slot, and in which wave?
   `<your rule>`

## Strategy narrative (fill with your methodology)

- Campaign categories and their goals: `<...>`
- Budget philosophy: `<...>`
- Launch phasing: `<...>`
- Negative-keyword philosophy: `<...>`
- Bid philosophy: `<...>`

## Boundaries the script already enforces (do not re-decide these)

SV bands and caps from `strategy.json`; never/claim/form exclusions; own-brand-only in Shield;
competitor brand terms are PAT targets, never keywords; one root per discovery campaign; same-root
halo campaigns; dedupe across buckets; capacity limits; already-launched skip list.
