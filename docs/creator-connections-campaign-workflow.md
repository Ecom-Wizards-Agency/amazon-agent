# Creator Connections Campaign Workflow

Status: first draft  
Last updated: 2026-05-22  
Source inputs: `Message_templates_Creator_Connections_(2).docx`, `Creator_Connections_brief_template_(3).docx`

## Related References

- [Amazon Ads operator skill](../skills/amazon-ads/SKILL.md)
- [Amazon operator routing](../skills/amazon-operator-routing/SKILL.md)
- [Creator Connections navigation note](../skills/amazon-operator-routing/references/workflow-router.md#creator-connections-navigation-note)
- [Advertising Help After Login README](../Advertising%20Help%20After%20Login/README.md)
- [Sponsored ads directory](../Advertising%20Help%20After%20Login/articles/015-sponsored-ads-G3ADZF348LBLYK22.md)
- Official Amazon help article to verify in-console: [Create and manage a Creator Connections campaign](https://advertising.amazon.com/help/GMANECFAFD49W23Y)

## Important Inputs From The Templates

### Qualification Message

Use this message when a creator asks for a free sample and the brand needs to qualify the creator before shipping product:

```text
Hello [Creator name],

Thank you for reaching out!

We have supplied a lot of samples in the past to everyone and found it was not economically viable because we did not see a return even on sample deliveries.

As a new policy, if you have driven 10k USD shipped revenue in the last 30 days, you may qualify. If you qualify, please upload a screenshot of your Amazon Influencer dashboard to Google Drive or a similar public sharing service and send us the public link through this messaging service, together with your shipping address for the sample.

Thank you for your understanding,
[Your name]
```

Variables to replace:

- `[Creator name]`
- `[Your name]`
- Revenue threshold, if the client wants a different qualification bar
- Any approved sample-shipping conditions

Do not ask creators for private login information, credentials, tokens, or non-public account access. A screenshot of performance is enough for qualification when approved by the client.

### Campaign Brief Template

The campaign brief should contain:

- Brand name
- Campaign name
- Primary product name or nickname
- Target creator type or audience
- Campaign goal
- Product highlights
- Content ideas
- Key talking points
- Claims or language to avoid
- Required compliance/disclosure language
- Commission rate
- Campaign budget

Template structure:

```markdown
## Overview

[Brand name] is launching the [Campaign name] campaign for [product name] on Amazon. We are seeking creators who reach [target audience] and can present the product authentically.

## Goals

Boost sales through authentic creator partnerships, offering customers a discount and creators a competitive commission.

## Primary Product Highlights

- [Highlight 1]
- [Highlight 2]
- [Highlight 3]
- [Highlight 4]

## Content Ideas

- Before/after demos
- Step-by-step tutorials
- Seasonal or timely use cases
- Lifestyle content showing the product solving a real problem

## Key Points

- [Manufacturing or quality proof point]
- [Core product benefit]
- [Timing or occasion]
- [Customer praise, ratings, or social proof]

## Avoid

- Comparing to or disparaging other brands
- Unsupported product claims
- Medical, performance, or regulated claims unless approved
- Any promise that is not directly supported by the product detail page, packaging, or approved client proof
```

Notes from the brief template:

- Additional disclosures are usually not required inside the brief unless the product sits in a special category, such as consumables.
- The seller remains responsible for FTC guideline and regulatory compliance.
- The minimum campaign budget noted in the template is `$5,000`.
- The budget acts as a ringfenced commission pool for Amazon Influencers and may not actually be spent.
- The template recommends setting commission to at least `15%` to make the campaign attractive to a broad range of Amazon Influencers creating shoppable video content.
- Actual budget, commission, product eligibility, category rules, and disclosure requirements must be verified in the Amazon Ads console before launch.

## First Draft Campaign Workflow

### 1. Collect Required Inputs

Before opening Creator Connections, gather:

- Advertiser/account name
- Brand
- Marketplace/country
- Product ASINs
- Product detail page links
- Product title and short product nickname
- Target creator audience
- Desired campaign name
- Campaign start and end dates
- Commission rate
- Campaign budget
- Customer discount, if applicable
- Sample policy and eligibility threshold
- Approved claims, proof points, and forbidden claims
- Sender name for creator messages

### 2. Verify Source Guidance

Search or review:

- First-party Amazon Ads help for current Creator Connections rules and UI.
- Local Advertising Help After Login for captured Amazon Ads Support Center pages.
- MAG SOPs only for practical agency procedure if a matching workflow exists.

Current local route reminder:

1. Open `https://advertising.amazon.com/campaign-manager`.
2. Select the correct account in the top-right account selector.
3. Open `Brand content` in the left navigation.
4. Click `Creator connections`.

Do not start from `https://advertising.amazon.com/choose-account?destination=/bi`, because local notes say it can show only a partial account list.

### 3. Confirm Account And Campaign Context

Before creating or editing anything, confirm:

- Advertiser/account
- Brand
- Marketplace/country
- Visible page title or tool name
- Any selected date range or filters
- Billing or eligibility warnings

Capture evidence if the UI shows warnings, eligibility limits, product restrictions, or budget/commission requirements.

### 4. Draft The Creator Brief

Use the brief template above and tailor it to the product. The brief should be concise, specific, and creator-friendly.

Quality checks:

- The product is clear in the first sentence.
- The creator knows what kind of content to make.
- Each product claim is supportable.
- Avoided claims are explicit.
- The commission and discount are aligned with campaign economics.
- Disclosure/compliance requirements are not vague.

### 5. Configure Campaign Settings

In Creator Connections, complete the campaign setup fields shown in the console. Expected settings to verify include:

- Campaign name
- Product/ASIN selection
- Campaign dates
- Budget
- Commission rate
- Customer discount or offer, if available
- Creator brief
- Any category-specific disclosure or compliance fields

Stop before launch or final submit unless the operator has approved the exact campaign settings in the current chat or a matching local standing permission exists.

### 6. Manage Creator Messages

For inbound sample requests:

1. Confirm the creator/thread.
2. Check whether the creator qualifies under the approved sample policy.
3. Use the qualification message if proof is needed.
4. Replace all variables.
5. Stop before sending unless the operator approves the exact message/thread.

If a creator sends proof of eligibility:

- Record the creator name, thread, claimed 30-day shipped revenue, proof link, product/sample requested, shipping address, and decision.
- Do not store credentials or sensitive private account data.
- Stop before promising shipment unless sample approval is confirmed.

### 7. Track Creators

Track creators from the first visible thread or campaign interaction. For now, a markdown table in the operator note is acceptable. Long term, move the same fields into an Excel workbook or Google Sheet so the team can filter by status, owner, next follow-up date, sample decision, and outcome.

Use one tracker per brand/campaign. For local working files, save drafts under:

```text
output/{client-or-brand}/ads/
```

Suggested AI table:

| Creator | Profile/thread link | Status | Last message date | Sample requested | Qualification proof | Claimed 30-day shipped revenue | Shipping info received | Product/ASIN | Next action | Owner | Follow-up date | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| [Creator name] | [Amazon thread/profile link] | New / Qualified / Waiting for proof / Sample approved / Sample declined / Active / No response / Closed | YYYY-MM-DD | Yes/No | Link or `Not requested` | USD amount or `Unknown` | Yes/No | ASIN or product nickname | Draft reply / Send qualification message / Approve sample / Monitor | [Name] | YYYY-MM-DD | Short context |

Recommended status values:

- `New`
- `Waiting for proof`
- `Qualified`
- `Sample approved`
- `Sample declined`
- `Active`
- `Needs reply`
- `No response`
- `Closed`

Future spreadsheet tabs:

- `Creators`: one row per creator/thread.
- `Campaign Settings`: brand, marketplace, campaign name, budget, commission, dates, products, offer, and disclosure notes.
- `Message Log`: date, creator, message direction, message type, summary, send status, and approval note.
- `Samples`: creator, product, approval status, shipping info received, shipment date, tracking number, and cost.
- `Performance`: creator, content/live status, attributed sales or revenue where available, commission, notes, and follow-up decision.

Do not store passwords, login details, tokens, private account screenshots, payment details, or unrelated personal data in the tracker. If using Google Sheets, keep access limited to the operating team and client-approved stakeholders.

### 8. Post-Launch Monitoring

After launch, monitor:

- Active campaign status
- Budget consumed
- Commission pool remaining
- Creator applications or participation
- Creator messages
- Creator tracker status and follow-up dates
- Video/content volume
- Sales/revenue attributed to the campaign where available
- Any warnings, paused states, billing issues, or policy notices

Recommended operator note fields:

- Account/brand/marketplace checked
- Campaign name
- Date range
- Budget
- Commission
- Products/ASINs
- Creators contacted or replied to
- Evidence captured
- Any action that still needs confirmation

## Stop-Before-Risk Points

Stop and ask for confirmation before:

- Launching a Creator Connections campaign
- Changing campaign budget, dates, commission, discount, or products
- Sending creator messages
- Approving or promising samples
- Uploading files or screenshots containing sensitive information
- Making billing, payment, permission, or account-setting changes
