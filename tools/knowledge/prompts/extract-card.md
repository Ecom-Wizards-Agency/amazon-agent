# Extracting a knowledge card from a source thread

You are reading one Slack thread (or a lesson, run note or SOP) and deciding whether it holds something any teammate could reuse on another account. If it does, you write one card that follows `tools/knowledge/card.schema.json`. The card keeps the identifiers; the unit built from it later never does.

## Read first

1. Read the whole thread, parent and every reply, in detailed format. Note who asked, who answered, who executed, and whether the resolution is visible in the thread or happened in a call, an email, a screenshot, a case or a video.
2. Separate three things: what the person saw (the symptom and any exact Amazon wording), why it happened (the mechanism), and what fixed it (the steps and who did them).
3. Run `python3 tools/search_amazon_libraries.py "<three to five words from the symptom>" --limit 8` and record whether a unit, a first-party article or a MAG SOP already covers the answer (`coverage_verdict` none, partial or full, with the paths, and `net_new` in one sentence).

## Write the card

- `title`: symptom first, as a teammate would ask it. No brand, product, person, ID or amount.
- `generic_lesson`: what any seller in that situation should do. This becomes the Answer section. Two to four sentences, active voice.
- `root_cause`: the mechanism, not the story. If the thread never establishes it, say so and set `resolution_status` to `diagnosis-only` or `unknown`.
- `resolution_steps`: numbered steps with exact UI labels or deep links when the thread shows them. Mark steps that need an operator approval (sends, appeals, submissions).
- `error_text`: every verbatim Amazon notice or code in the thread. This is the most searchable field.
- `symptom_keywords`: three to six phrasings people actually use.
- `fix_source`: who found the fix (agency, client, amazon-support, first-party-doc). `who_answered` and `who_executed` may differ.
- `evidence_location`: where the proof lives. A screenshot-only or call-only answer gets `confidence: low` unless a first-party page backs it.
- `confidence`: high only when a first-party rule backs the answer or the fix was confirmed more than once; medium when the thread shows the fix working once; low otherwise.
- `client_specific_to_strip`: every token that must not reach the unit (brand, product, people, ASINs, case and shipment IDs, prices, counts, addresses, 3PLs, links).
- `participants_external`: true when client staff, suppliers or Amazon staff wrote in the thread. Such cards are generalised to the product category level, never quoted.
- `publishable`: false when the lesson cannot be stated without identifying the client or depends on a private arrangement. `policy_risk`: true when the practice may breach Amazon policy (for example a counterfeit claim against a lawful reseller); give the reason. The agency lead decides both.
- `marketplaces`: from the channel or the thread; set `marketplace_inferred` true when not stated.
- `identifiers`, `channel_id`, `parent_ts`, `related_ts`, `permalink`, `client_slug`: ledger fields. Fill them; they stay in the card and the vault ledger.

## Do not

- Do not invent a root cause, a deadline, an eligibility rule or a timing. Say "not established in the thread".
- Do not merge two problems into one card. Sibling threads about the same problem get one card with `related_ts`.
- Do not resolve a disagreement between the thread and an Amazon page. Record the page in `contradicts_paths` and keep both statements.
- Do not write strategy opinions (skip a product's ads during an event, run a price test) as rules. Those become `kind: decision-aid` with the conditions stated, or stay out.
