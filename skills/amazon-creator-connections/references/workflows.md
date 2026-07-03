# Creator Connections Workflow Modes

Ported from the retired Creator Connections Builder prompt generator, genericized. Every mode inherits the SKILL.md core rules: connected-browser checkpoint first, status filter applied to any message reading, and the two stop-gates (no sends, no publishes) unless explicitly approved.

## `campaign` — Prepare a new campaign

Inputs: product name, ASIN, start/end dates, commission, maximum budget, reference campaign (name or URL). Commission and budget are client decisions — take them from the brief or the client config; do not assume defaults.

1. Verify the exact product details from its live Amazon listing (title, current price, availability).
2. Follow the reference campaign's naming convention and structure, but make the description product-specific and listing-backed.
3. Create the campaign-level tracker tab (see `tracker-schema.md`) with the approved columns and metadata header.
4. Prepare every campaign field, then **stop before the final publish action** and show the complete campaign for operator/manager approval. Do not send creator messages or approve samples in this mode.

## `tracker` — Create a campaign tracker tab

Inputs: campaign (name or URL), preferred tab name.

1. Read the live campaign for its exact name, product title, ASIN, schedule, commission, status, campaign ID, campaign type, accepted creators, submitted content, budget, remaining budget, spend, orders, sales, clicks, campaign link, and product link.
2. Duplicate the client's approved tracker styling and preserve the columns exactly (`tracker-schema.md`).
3. Preserve the approved status dropdown and Yes/No content validation.
4. Do not add creator rows unless campaign or message evidence supports them. Do not alter the source campaign.

## `gaps` — Find missing campaign trackers

Inputs: campaign scope (active / all), message scope (messages containing ASINs or product links / all messages in scope after the status filter).

1. Compare live campaigns and message-linked products against every existing tab in the tracker sheet.
2. Return a prioritized list: campaign name, ASIN/product, campaign link, current status, relevant message count, submitted-content count, recommended tab name.
3. Create missing tabs only when campaign/product matching is verified. Flag campaign-token-only, multi-product, or otherwise ambiguous cases for manager review.
4. Do not change campaigns or send messages in this mode.

## `reconcile` — Full-system reconciliation

The complete controlled audit across campaigns, trackers, messages, samples, and content:

1. Inventory active campaigns and campaign metadata.
2. Inventory campaign tabs in the tracker sheet.
3. Retrace messages in scope (status filter applies) and map each by ASIN/product link, campaign reference, or explicit product name.
4. Update existing tabs, create verified missing tabs, and flag ambiguous multi-product threads.
5. Record samples, follow-ups, ghosted creators, unqualified creators, verified content, and content links using the approved dropdown statuses.
6. Report launch-ready products, missing trackers, unanswered inquiries, stale follow-ups, and manager decisions needed. Unanswered inquiries feed the reply-drafting step of `audit` mode — reconcile itself sends nothing.
