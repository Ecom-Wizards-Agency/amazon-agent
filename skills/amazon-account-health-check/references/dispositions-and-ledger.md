# Findings Ledger, Dispositions, and Routing

## Findings Ledger

Maintain a private findings ledger at `{findings_ledger_path}`, stored locally next to the automation. The ledger is the automation's memory only - finding identity, history, and links to follow-up tasks - so findings are never forgotten or duplicated between runs. It is not a task system: `{follow_up_task_database}` remains the human task source of truth. Never commit the ledger to the repo or GitHub.

- Finding key: `{account}|{marketplace}|{scope}|{issue_type}`, where scope is `ASIN:<asin>` for listing-level issues, `ACCOUNT` for account-level issues (order metrics, verification, Account Health Rating), or `CASE:<id>` for case-only threads.
- Entry fields: key, account, marketplace, scope, asin, case_id, issue_type, summary, severity (critical/high/medium/low), disposition, owner, task URL, first_seen, last_verified, last_status, last_movement, last_reported, deadline, waiting_on, waiting_since, resolved_date, impact, current_state, next_step.
- If an account is skipped or blocked today, carry its entries forward unchanged. Never infer resolved from a missed check.
- Set resolved_date only after Seller Central verification. Keep resolved entries 30 days for dedup, then prune.
- Write the full updated ledger exactly once, at the end of the run, including degraded runs.
- First run: seed the ledger by sweeping the open follow-up tasks in `{follow_up_task_database}` for in-scope accounts, keeping their current assignees.

## Fields The Digest Depends On

The run posts nothing, so the digest is only as honest as what the ledger says. Three of these fields are not optional.

- `last_movement`: the date the finding's observed state actually CHANGED. Not the date you looked at it. `last_seen` and `last_verified` cannot tell "checked again, unchanged" apart from "got worse today", and that difference is what the digest uses to choose between staying silent and printing a line. Set it only when something moved: a new deadline, a status change, a worse severity, a resolution. Leave it alone on an unchanged re-check.
- `impact`, `current_state`, `next_step`: the three narrative fields behind the digest's approved card layout (`• *Issue:* / *Impact:* / *Current state:* / *Next step:*`; `summary` is the Issue). `impact` says why it matters in money or risk terms. `current_state` says exactly what the page showed THIS run, dated; refresh it on every run that verifies the finding. `next_step` is the single concrete action with a named owner (`<@slack-id>: do X by date`); touch `impact` and `next_step` only when they actually change. A finding without these fields renders as a compact one-liner instead of a card, so writing them is what upgrades the finding's visibility.
- `last_reported`: the date the finding last appeared in a digest or in an immediate escalation. Set it yourself when you post an immediate escalation; the digest pass maintains it otherwise. It re-arms the stall timer, so a stuck item nags on a cadence instead of repeating itself every single morning until the reader stops reading.
- `coverage[YYYY-MM-DD][<region>]`: a TOP-LEVEL ledger key, not a field on a finding. Each region run writes one object with `checked`, `in_scope` and `skipped` (a list of `Account MKT (reason)` strings). Write it even when the run failed, with `checked: 0`, because this entry is also the run's claim: `guard.py` reads exactly this key to decide whether the region already ran today, and a missing entry gets the run retried into a loop. A region with no entry is reported as **pending** and is never folded into the checked count. Do not skip the write to keep the numbers tidy. On 12.08.2026 a run that read zero of nine accounts still produced a post that implied full coverage, which is the failure this field exists to make impossible.

## Disposition and Routing

Dispositions are the workflow's internal routing layer: they decide what happens to each finding, then map into `{follow_up_task_database}`. They never replace task-system statuses. Before the run ends, every finding - new or carried over - must have exactly one disposition:

- **No action needed**: clean, informational, or verified resolved. No task.
- **Action needed**: new actionable issue with no owner yet. Create a follow-up task in the same run (default assignee `{daily_runner}`), then report the finding as Assigned.
- **Assigned**: an open task already exists. Report owner, task age in days, and an OVERDUE flag when past due. Comment on the task when the state changed; raise priority or pull the due date earlier when it worsened.
- **Waiting**: action taken, now pending an external party (marketplace case reply, client documents, reinstatement review). Update the task with who it waits on and since when; set the task status to the closest waiting/blocked status the database offers. Owner stays `{daily_runner}`.
- **Escalate**: meets an escalation trigger. Task assigned to `{escalation_owner}` at the highest priority. The digest picks the finding up from the ledger and carries it, so no post is needed from the run. Post an immediate one-line escalation only when it cannot wait for the digest (deactivation warning, policy deadline inside 3 days, high-severity finding with no owner), and then set `last_reported` so the digest does not repeat it. Format in `output-and-tasks.md`.

`offboarded` and `out_of_scope` are lifecycle closures written only by the ledger maintenance command when a client leaves or is taken out of the scheduled checks; a check run never sets them and never re-opens a finding that carries one.

Escalation triggers (exhaustive - everything else defaults to `{daily_runner}`):

- account deactivation/suspension or an explicit deactivation warning
- any decision at a stop-before-risk point (appeal, acknowledgement, support reply, document upload)
- identity, bank, tax, or verification requests
- legal, IP, or counterfeit claims
- a hard marketplace deadline within 48 hours that is not already handled
- Seller Central login/MFA blockers after both approved browsers were tried

### How The Triggers Are Read

T1 to T6 are the six triggers above, in order. These readings settle the cases that were applied unevenly before the table below existed.

- **T1 deactivation.** Amazon says the account, a marketplace store, or a selling privilege (seller-fulfilled offers, a store's selling access) is deactivated, suspended or restricted, or warns in writing that it may be. A listing or offer that is removed, suppressed, deactivated for a pricing error, or "at risk of removal" is not T1. Neither is a warning about an inbound or fulfilment program such as optimized placement.
- **T2 stop-before-risk decision.** The next step is an appeal, acknowledgement, support reply, claim response or upload whose content commits the seller beyond supplying facts Amazon asked for: an admission, a root-cause and corrective-action plan, statements about the seller's own conduct, or accepting a claim, violation, removal or disposal instead of contesting it. Gathering and submitting requested documents (certificates, test, inspection or product-verification reports, safety data sheets, GPSR details, invoices, proof of delivery, tracking) is not T2, and neither is an appeal built only from such documents. Those still stop before the submit for the operator's approval under the Hard Rules; that approval is not an escalation.
- **T3 identity, bank, tax or verification.** Amazon asks the seller to verify or supply its own identity, business, bank or payment, tax or VAT, or account-contact information, INFORM certification and the emergency contact included. It applies in any marketplace the seller account reaches, including one outside the profile's marketplace. Product verification (GMP, third-party testing and inspection, safety documents) is product compliance, not T3.
- **T4 legal, IP or counterfeit.** A rights owner, an authority or Amazon alleges infringement, inauthenticity or a legal violation against the seller, or the next step is filing such a claim against another seller.
- **T5 deadline and T6 login/MFA** are rules about a date and about the browser, not about the issue type. They apply to every row below as written above and outrank its default. The table does not restate them, and a finding escalated under T5 or T6 is not a departure from the table.
- **Metric versus target.** Whether an order or delivery metric is above or below target is read from Amazon's own target and status on the page. The thresholds are Amazon's and the runner's, not this table's. A metric row escalates only on T1 wording.

### Default Disposition By Issue Type

Every finding starts from the default of its `issue_type` in the tables below. For a listed type the table outranks the severity line: severity sets task priority, never the disposition.

Defaults:

- **Escalate**: the type is itself a trigger.
- **Runner**: routes to `{daily_runner}`. Action needed on first sight, then Assigned or Waiting as the task moves. Moving among those three is the normal lifecycle, not a departure.
- **No action**: informational; no task.

A finding verified resolved in Seller Central becomes No action with `resolved_date` under any default. That is resolution, not an override.

A finding leaves its default only through one of these overrides, and only on evidence seen in this run. When that evidence holds, the override applies; the default is not a choice to keep:

- `esc`: Escalate when this finding carries evidence of T1 to T4. Name the trigger and the Amazon label or wording that carries it.
- `cov`: No action when another open finding on the same account already tracks the cause. Name that finding's issue type and scope.
- `expl`: No action when a verified, intended state explains the signal: a parent ASIN, a closed or discontinued offer, a stock-out the client confirmed as planned.
- `floor`: No action below the materiality floor that the market-signal worker or the owning weekly check applies (for any rating finding, the review-count floor the worker uses for the displayed star), or when that check's confirmation source (Amazon's Referral Fee Preview report, for fees) does not confirm the change. The floors live in that code and skill, not here.
- `wait`: Escalate types only. Waiting once the escalation owner's decision has been carried out, or none is needed, and only Amazon's dated review or reply remains. Fill `waiting_on` and `waiting_since`. Return to Escalate on any new warning, rejection or missed date.
- `scope`: `store_deactivated_indicator` only. Runner when the page shows the deactivated store belongs to a marketplace the client does not sell in and no T3 request is attached, to confirm the client's intent.
- `mon`: `market_not_monitored` only. Runner when the profile enables monitoring but no ASIN is covered.
- `own`: `price_changed` and its cluster only. Runner when the client did not set the new price.

Record every override on the finding itself as one dated line in `notes`: `DD.MM.YYYY disposition override <code>: default <default>, set <disposition>; <evidence seen this run>`. Re-check that evidence on every verifying run. When it no longer holds, return to the default and add a line in the same form saying so. A departure without that line disagrees with the table: the next run writes the line if the evidence still holds, and restores the default if it does not.

Where a row lists aliases, older findings keep their existing key and are updated under it; a new finding uses the first name. For a type the table does not list, reuse the listed type that describes the same Amazon label before minting a new one. If none fits, route it by the severity line and name the new type among the finish note's blockers, so the table gets a row.

Account status, identity and seller conduct:

| issue_type | Default | Trigger | Override |
|---|---|---|---|
| `account_information_deactivation_risk` | Escalate | T1, T3 | `wait` |
| `account_information_verification` | Escalate | T3 | `wait` |
| `inform_act_certification` | Escalate | T3 | `wait` |
| `emergency_contact_unverified` | Escalate | T3 | `wait` |
| `european_vat_registration_requirements` | Escalate | T3 | `wait` |
| `store_deactivated_indicator` | Escalate | T1 | `wait`, `scope` |
| `customer_reviews_policy_violation` | Escalate | T1, T2 | `wait` |
| `policy_warning_notice` | Runner | none | `esc` |
| `policy_compliance_priority_actions` (account-level summary; each priority action is also its own finding) | Runner | none | `esc`, `cov` |
| `brand_registry_access` | Runner | none | `esc` |

Order, delivery and buyer-contact metrics:

| issue_type | Default | Trigger | Override |
|---|---|---|---|
| `odr_deactivation_warning` | Escalate | T1 | `wait` |
| `late_shipment_rate_deactivation_risk` | Escalate | T1 | `wait` |
| `otdr_deactivation_risk` | Escalate | T1 | `wait` |
| `otdr_vtr_deactivation_risk` | Escalate | T1 | `wait` |
| `late_shipment_rate_above_target` | Runner | none | `esc` |
| `on_time_delivery_below_target` | Runner | none | `esc` |
| `on_time_delivery_declining` | Runner | none | `esc` |
| `valid_tracking_rate_below_target` | Runner | none | `esc` |
| `buyer_messages_over_target` | Runner | none | `esc` |
| `messages_pending_response` | Runner | none | `esc` |
| `chargebacks_pending_review` | Runner | none | `esc` |
| `atoz_nonreceipt_claim` | Runner | none | `esc` |

Product compliance and listing policy:

| issue_type | Default | Trigger | Override |
|---|---|---|---|
| `food_safety_gmp_certification` | Runner | none | `esc` |
| `food_safety_skin_lightening` | Runner | none | `esc` |
| `chemical_safety_compliance` | Runner | none | `esc` |
| `gpsr_warning_safety_information` | Runner | none | `esc` |
| `gpsr_compliance_submissions` | Runner | none | `esc` |
| `gpsr_safety_warning_cluster` | Runner | none | `esc`, `cov` |
| `epr_packaging_submission` | Runner | none | `esc` |
| `fic_information_requested` | Runner | none | `esc` |
| `product_safety_issue` | Runner | none | `esc` |
| `product_safety_priority_actions` | Runner | none | `esc`, `cov` |
| `restricted_product_policy_violation` (aliases `restricted_product_policy_violations`, `restricted_products_policy_violations`) | Runner | none | `esc` |
| `category_approval_required` | Runner | none | `esc` |
| `product_detail_page_warning` | Runner | none | `esc` |
| `product_condition_complaint` | Runner | none | `esc` |
| `merchant_fulfilled_listing_investigations` | Runner | none | `esc` |
| `investigation_case` | Runner | none | `esc` |
| `automated_recall_disposal` | Runner | none | `esc` |
| `transparency_unsellable_inventory` | Runner | none | `esc` |
| `reseller_removal` | Runner | none | `esc` |
| `fair_pricing_policy_violation` | Runner | none | `esc` |
| `pricing_error_deactivated_offers` | Runner | none | `esc`, `expl` |
| `bundle_featured_offer_pricing_restrictions` | Runner | none | `esc` |
| `price_error_listings` | Runner | none | `expl` |
| `removed_detail_pages` | Runner | none | `esc`, `cov` |
| `subscribe_save_reinstatement` | Runner | none | `esc` |
| `prime_eligibility_change_notification` | Runner | none | `esc` |
| `optimized_placement_suspension_warning` | Runner | none | `esc` |

Listings, inventory, shipments and cases:

| issue_type | Default | Trigger | Override |
|---|---|---|---|
| `inactive_listings` | Runner | none | `cov`, `expl` |
| `inactive_out_of_stock` | Runner | none | `cov`, `expl` |
| `active_zero_available` | Runner | none | `cov`, `expl` |
| `out_of_stock` | Runner | none | `cov`, `expl` |
| `low_available_stockout_risk` | Runner | none | `cov`, `expl` |
| `no_active_listings` | Runner | none | `cov`, `expl` |
| `missing_offer` | Runner | none | `cov`, `expl` |
| `monitored_asin_not_listed` | Runner | none | `cov`, `expl` |
| `search_suppressed_listings` | Runner | none | `cov`, `expl` |
| `stranded_inventory` | Runner | none | `cov`, `expl` |
| `stranded_listing_error` | Runner | none | `cov`, `expl` |
| `reserved_inventory_sellable_stockout` | Runner | none | `cov`, `expl` |
| `listing_availability_collapse` | Runner | none | `esc`, `cov` |
| `featured_offer_drop` | Runner | none | `cov`, `expl` |
| `featured_offer_high_price` | Runner | none | `cov`, `expl` |
| `featured_offer_ineligible_uncompetitive_price` | Runner | none | `cov`, `expl` |
| `featured_offer_share_low` | Runner | none | `cov`, `expl` |
| `barcode_defect_manual_review` | Runner | none | `cov` |
| `carton_defect_manual_review` | Runner | none | `cov` |
| `inbound_receipt_reconciliation` | Runner | none | `cov` |
| `inbound_shipment_missing_tracking` | Runner | none | `cov` |
| `inbound_shipment_stalled` | Runner | none | `cov` |
| `shipment_problems` | Runner | none | `cov` |
| `support_cases_needing_attention` | Runner | none | `esc`, `cov` |
| `open_case_requiring_attention` | Runner | none | `esc`, `cov` |
| `performance_notification_unread` (read it; its content becomes a finding of its own type) | Runner | none | `esc`, `cov` |

Market signals and listing watch (observations, not verified Seller Central state):

| issue_type | Default | Trigger | Override |
|---|---|---|---|
| `buybox_lost` | Runner | none | `cov`, `expl`, `esc` |
| `buybox_loss_cluster` | Runner | none | `cov`, `expl`, `esc` |
| `bsr_degradation` | No action | none | none; a verified cause becomes a finding of its own type |
| `bsr_degradation_cluster` | No action | none | none; a verified cause becomes a finding of its own type |
| `bsr_competitor_proximity` (cannot fire while no competitor ASIN is registered) | Runner | none | `floor` |
| `rating_drop` | Runner | none | `floor`, `cov` |
| `rating_display_dropped` | Runner | none | `floor`, `cov` |
| `rating_display_improved` | No action, never written to the ledger (check-sequence.md) | none | none |
| `reviews_disappeared` | Runner | none | `floor`, `cov` |
| `reviews_disappeared_cluster` | Runner | none | `floor`, `cov` |
| `browse_node_changed` | No action | none | none |
| `browse_node_change_cluster` | No action | none | none |
| `root_category_changed` | Runner | none | `expl` |
| `price_changed` | No action | none | `own` |
| `price_change_cluster` | No action | none | `own` |
| `fba_fee_changed` (alias `fba_fee_change`) | Runner | none | `floor` |
| `fba_fee_change_cluster` | Runner | none | `floor` |
| `referral_fee_changed` | Runner | none | `floor` |
| `referral_fee_change_cluster` | Runner | none | `floor` |
| `package_dimensions_changed` (alias `package_measurement_changed`) | Runner | none | `floor` |
| `package_weight_changed` (alias `package_weight_change`) | Runner | none | `floor` |
| `package_measurement_change_cluster` | Runner | none | `floor` |
| `listing_content_changed` | Runner | none | `cov`, `expl` |

The weekly operational check (`amazon-operational-checks`) confirms fee, package dimension and package weight findings and owns their task; the daily run links that task instead of opening a second one.

Coverage and workflow gaps (the digest reports these as coverage gaps, not account problems):

| issue_type | Default | Trigger | Override |
|---|---|---|---|
| `market_not_monitored` | No action | none | `mon` |
| `market_data_not_covered` | Runner | none | none |
| `keepa_rate_limited` | Runner | none | none |
| `market_signal_findings_overwritten` | Runner | none | none |
| `market_state_findings_overwritten` | Runner | none | none |
| `sellersonar_stale_source` (retired source; never create) | No action | none | none |
| `buybox_check_disabled_missing_seller_id` | Runner | none | none |
| `homepage_widgets_unreadable` | Runner | none | none |
| `inventory_status_counts_unreadable` | Runner | none | none |
| `check_label_form_wrong_domain` | Runner | none | none |
| `account_name_mismatch` | Runner | none | none |
| `account_not_in_switcher` | Runner | T6 when it blocks login | none |
| `europe_session_logged_out`, `us_session_logged_out`, `rest_session_logged_out` | Runner | T6 | none |
| `read_browser_not_driveable` | Runner | T6 | none |
| `seller_central_access_blockers` | Runner | T6 | none |

For an issue type the tables do not list, severity maps to default routing: Critical findings are escalation candidates; High and Medium route to `{daily_runner}`; Low is No action needed unless recurring.

### Degraded Run

Degraded run (Seller Central blocked in both approved browsers): write the ledger under the carry-forward rule and write the coverage entry for the region with `checked: 0` and the blocked accounts in `skipped`. Carry every unverified finding forward untouched: never re-dispose it, never mark it resolved, and never restate it as verified today. Report the login blocker in the finish note, and post nothing beyond an immediate escalation if the blocker itself meets that bar. There is no queue post to fall back on, so a degraded run is visible through its coverage entry and the digest's pending count, not through a post.
