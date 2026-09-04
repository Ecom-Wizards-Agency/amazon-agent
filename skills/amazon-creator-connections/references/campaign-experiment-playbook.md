# Creator Campaign Experiment Playbook

Use this playbook to prepare product-specific Creator Connections campaigns that attract qualified, product-relevant creators transparently. Do not publish a campaign until the operator has approved its exact title, description, ASIN, dates, budget, and commission.

## One product and one hypothesis

Each campaign must map to one product or tightly controlled ASIN set and one acquisition hypothesis. Assign a non-PII experiment ID and record:

- product name and exact ASINs
- audience/problem fit
- campaign goal
- title hypothesis
- description hypothesis
- approved commission and budget
- start and end dates
- creator cohort rule
- primary and guardrail metrics

Use a 28 to 56 day test window when the client asks for a one-to-two-month experiment. The client owns the final duration. Do not compare tests with different dates, products, stock conditions, or commission rates as though title wording alone caused the result.

## Title structure

Lead with relevance, not vague excitement:

`{Product or problem} | {specific creator fit or content opportunity} | {approved incentive, optional}`

Good title hypotheses make the creator recognize three things quickly: what the product is, who it is useful for, and what content opportunity exists. Avoid unsupported outcomes, urgency that is not real, guaranteed earnings, and generic wording such as `Amazing Product Opportunity`.

Commission percentage is an optional test variable, not a default. Include it in one controlled title variant only when the client has approved the exact percentage and the campaign setup matches it. A percentage can improve initial attention, but it may also attract incentive-first applicants with weak product fit. Compare it against a relevance-led title while holding product, dates, description, stock, and eligibility constant.

## Required description structure

Every campaign description uses these labeled sections in this order:

1. `CAMPAIGN GOAL`
   - State the customer problem, intended audience, and content behavior the campaign is meant to generate.
   - Describe success without promising views, sales, rankings, payment, or future work.
2. `WHY THIS PRODUCT / CREATOR FIT`
   - Explain the product use case and the creator niches or lived-use contexts that make sense.
3. `CONTENT DIRECTIONS`
   - Give two to four distinct, optional storytelling angles. Keep creator voice flexible.
4. `KEY TALKING POINTS`
   - List only product facts supported by the listing, approved brand evidence, or supplied substantiation.
5. `MUST SHOW OR SAY`
   - Identify the exact product, required disclosure, correct use, and any essential demonstration.
6. `DO NOT SAY OR SHOW`
   - Prohibit unsupported claims, competitor disparagement, review manipulation, inaccurate use, prohibited audiences, and any brand-specific risks.
7. `DELIVERABLE AND TRACKING`
   - State the requested content format and ask the creator to send the final live video or post link so performance can be tracked.

## Controlled title and description test

Create no more than two live variants for the same product during one test cycle:

- Variant A, relevance-led: product/problem plus specific creator fit.
- Variant B, incentive-led or alternate hook: change only the approved title hook or one clearly documented description opening.

Prevent false conclusions:

- assign each applicant to the first campaign in which they appeared
- deduplicate by Creator Record ID, not display name
- mark creators already known to the brand before the test
- report new-to-brand qualified creators separately from repeat creators
- compare inquiry count, verified 10/10 rate, sample acceptance, content-post rate, and cost per posted creator
- log overlap, stock outages, product switches, and campaign date differences

Do not claim that a variant found new creators until the deduplicated Creator Record IDs prove it.

## Pre-publication review block

Present each proposed campaign in this format:

```text
Experiment ID:
Product / ASIN:
Duration:
Campaign goal:
Title:
Description:
Commission:
Budget:
Primary metric:
Guardrails:
What changed from the control:
```

The final check must confirm exact product mapping, supported talking points, complete must/must-not guidance, approved commercial terms, inventory readiness, non-overlapping experiment logic, and no private creator or client data in reusable repository files.

## Future platform expansion

Keep the experiment model platform-neutral: creator identity, product mapping, qualification, sample reservation, content link, and outcome metrics are canonical fields. Store platform campaign IDs and platform-specific eligibility or messaging rules as adapters. Do not reuse an Amazon permission, message template, commission rule, or fulfillment assumption for another platform such as Levanta without explicit validation.
