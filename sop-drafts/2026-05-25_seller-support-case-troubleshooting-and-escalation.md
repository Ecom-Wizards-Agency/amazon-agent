# SOP Draft: Seller Central Support Case Troubleshooting And Escalation

Date: 2026-05-25
Status: ready for review
Owner: Amazon operations
Related workflow: Seller Central support cases, live chat escalation, inbound shipment defect disputes

## Purpose

Create a repeatable workflow for Seller Central support cases so operators gather the right evidence, avoid duplicate cases, escalate inside the correct thread, and preserve reusable learnings without committing client-specific evidence to GitHub.

## Preconditions

- The operator is in the correct Seller Central account and marketplace.
- The operator is using the preferred connected browser/session for the account.
- The operator has checked whether an existing support case, case log thread, shipment defect, or dispute path already exists.
- `_local/local-permissions.md` has been checked for standing permissions and the locally configured operator full name.
- If no full operator name is stored locally and a sender identity is needed, pause and ask Victor which full name to use before sending.
- Local evidence folders exist or can be created under `evidence/{client-or-brand}/support-prep/`.

## Required Inputs

- Account and marketplace.
- Entity IDs involved, such as ASIN, FNSKU, SKU, shipment ID, order ID, campaign ID, or existing case ID.
- Exact Amazon wording, warning, defect type, status, quantity, and visible dates.
- What was expected, what happened instead, and the business impact.
- The specific question Amazon must answer, especially any source, root-cause, or evidence request.
- Local operator full name from `_local/local-permissions.md` when chatting, submitting, or signing email-style case messages.

## Workflow

1. Confirm the account, marketplace, page title, and relevant filters or dates before taking action.
2. Search the local Amazon libraries and any relevant SOPs for the exact issue text or closest workflow.
3. Check whether an existing case or dispute already exists for the same issue.
4. If a case exists, follow up in that case unless Seller Central blocks replies or Victor explicitly asks for a new case.
5. Draft concise support text:
   - identify the entity and issue,
   - state what was checked,
   - explain why the previous answer is incomplete if escalating,
   - ask for the exact evidence or root-cause information needed.
6. Use the locally configured full operator name for traceability when Amazon asks for a sender name or when signing a support message. Do not put the actual local name in GitHub docs.
7. Prefer email communication when Seller Central allows it, but use chat when Victor approves chat or speed matters.
8. In live chat:
   - wait for the support associate's first message before sending substantive details,
   - send one focused message at a time,
   - wait for each associate reply,
   - if the associate says they are still checking, reply politely that the named operator is still waiting.
9. If Amazon gives cleanup advice but not the source or root cause, ask for the upstream evidence Amazon controls, such as receiving events, FC actions, relabeling events, inventory adjustments, source shipments, or photos/examples.
10. Save final case IDs, submitted text, important Amazon answers, and evidence paths in the live task tracker, usually Notion. Keep screenshots and raw evidence local.

## Inbound Shipment Defect Disputes

Use this path when a defect row exists and Amazon indicates photos or examples require a shipment dispute:

1. Open the shipment summary in Seller Central.
2. Go to `Problems`.
3. Find the product-level defect row.
4. Click `Resolve`.
5. Choose `Submit dispute`, not `Acknowledge the defect`, when the goal is evidence, photos, examples, or root-cause review.
6. Keep the dispute text short because Amazon may enforce a tight character limit.
7. Ask Amazon to review fulfillment-center receiving evidence and provide photos/examples of affected labels or units.
8. Ask Amazon to identify the specific failure reason, such as print quality, label placement, missing label, wrong barcode/FNSKU, inaccessible barcode, or another issue.
9. Save the submitted message and confirmation locally. If Amazon says a case ID will be created later, add a follow-up reminder in the live tracker.

## Stop-Before-Risk Points

- Stop before submitting a new case, sending a reply, starting or continuing chat, acknowledging a defect, submitting a dispute, uploading documentation, changing inventory, creating removals, or deleting listings unless Victor explicitly approved the action or a matching local permission exists.
- Stop if Seller Central changes the message materially, forces a different communication method, asks for an appeal/acknowledgement instead of a support case, or blocks duplicate case creation.
- Stop before committing screenshots, raw evidence, client-specific identifiers, local permission records, or actual operator identity to GitHub.

## Evidence And Screenshots Needed

- Save screenshots only when they show final submission, exact Amazon wording, important warnings, case IDs, or defect rows that cannot be reliably transcribed.
- Store screenshots under `evidence/{client-or-brand}/support-prep/`.
- Store generated worksheets, drafts, and operator notes under `output/{client-or-brand}/support-prep/`.
- Record the account, marketplace, entity ID type, defect or issue text, quantity or status, submitted message, final Amazon response, and follow-up date.
- Put live status, owners, due dates, case IDs, and client-specific tracking in Notion or the active task system.

## Source Docs/SOPs Used

- `skills/amazon-operator-routing/SKILL.md`
- `skills/amazon-communications/SKILL.md`
- `skills/amazon-operator-routing/references/workflow-router.md`
- Current Seller Central support and shipment defect UI observed during recent case handling

## Open Questions Or Assumptions

- Notion remains the live source of truth for client-specific case IDs, owners, due dates, and follow-up status.
- GitHub stores reusable process knowledge only.
- Actual operator identity remains local-only in `_local/local-permissions.md`.

## Promotion Notes

After team review, promote this SOP into the durable MAG/internal SOP library or link it from the Amazon communications workflow. Keep any examples generic unless Victor explicitly approves a sanitized case study.
