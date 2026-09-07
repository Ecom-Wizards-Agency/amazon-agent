# Creator Connections Operations

This repository's Creator Connections capability is implemented by the `amazon-creator-connections` skill. It supports campaign preparation, inbox triage, qualification, campaign-level tracking, sample preparation, follow-up monitoring, and internal reporting.

The workflow is browser-led because Creator Connections is operated in Amazon Ads. Private brand, creator, tracker, and contact data stay in the live tools or local configuration and are never committed here.

For unattended work, the bot uses a dedicated persistent CDP browser profile, not a temporary in-app browser session. The operator completes a one-time Amazon Ads login in that isolated profile. If the profile returns to a sign-in page, the bot stops safely and sends a PII-free internal blocker notification through the approved Slack helper.

## Operating model

- One campaign-level tracker tab per product campaign, plus an `Undecided` tab for unclear product matches.
- One durable Creator Record ID per creator. The ID is not based on a name, address, product, or row number. It follows the creator when the final product changes.
- A central non-PII registry links the creator ID to canonical storefront and identity evidence. A separate non-PII action log records each bot decision and result.
- The bot reads current state, builds a daily action queue, and works routine items only when the local permission and Slack-helper controls are configured.
- Multi-client runs use an enabled-client roster and separate account, tracker, creator-ID, registry, queue, and message-watermark bindings for every client. A binding mismatch stops that client without affecting another client's run.

## Internal reporting cadence

The daily bot posts one internal, PII-free tracker-progress notification after each completed sweep. It shows the current pipeline across active campaign tabs, the day's net movement, verified posted-content links, the 10/10 priority sample lane, and only genuine action-needed exceptions. The configured operator mention is included so the owner receives the notification.

Each Monday, the bot creates one parent post for the prior week's summary and posts the full client-ready weekly summary as a reply in that thread. This keeps the weekly record together without creating duplicate standalone channel posts.

## Qualification and fulfillment

The bot background-checks visible storefront and content evidence before asking for proof. It requests only the information still needed. A sample can proceed only at 10/10, with a final ASIN, complete recipient details, a confirmed identity, low risk, no duplicate sample, and an MCF pre-flight that proves the correct creator, campaign, tracker row, recipient, SKU, FBA/AFN fulfillment, live MCF availability, and exactly one unit. A unique reservation binds those fields; the populated MCF form must match it before submission. Definitive failures can be cancelled and released with evidence, while uncertain outcomes remain locked for reconciliation. An active FBM listing is not MCF inventory. When the exact ASIN is blocked, the system verifies a same-campaign MCF-fulfillable alternative before contacting the creator, then waits for an explicit alternate-ASIN reply before changing the record. The local `tools/creator-connections-control/` runner is mandatory for identity resolution, score computation, the daily action queue, product-switch validation, and MCF controls. It has no Amazon credentials and does not place an order.

## Automation readiness and SP-API dependency

The Creator Connections system is ready for high-automation operation of routine work: daily inbox sweeps, identity-safe record handling, storefront background checks, qualification scoring, tracker and queue updates, follow-up scheduling, content-link monitoring, and approved message workflows. Paid MCF fulfillment is deliberately not automated yet. It remains a controlled, operator-confirmed browser action until Amazon Selling Partner API (SP-API) access is approved and the order-creation integration passes the same record, product, quantity, and fee safeguards. SP-API approval is not required to use or publish this skill update.

## Authority boundaries

The skill has four externally visible stop-gates: creator-message sends, campaign publication, MCF order creation, and Slack posting. A current operator instruction or matching local standing permission is required. Slack posts use the configured posting helper, never the Slack connector as the operator.

See the skill's `SKILL.md` and references for the executable procedure.
