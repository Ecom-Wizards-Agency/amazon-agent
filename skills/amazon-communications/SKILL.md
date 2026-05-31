---
name: amazon-communications
description: Use for Amazon communication workflows: Seller Support cases, case replies, buyer-seller messages, Brand Customer Reviews outreach, courtesy-refund follow-ups, Creator Connections replies, and message drafting.
---

# Amazon Communications

## Workflow

1. Confirm exact account, marketplace, brand, recipient/thread/case, and visible message context.
2. Search Amazon first-party communication rules and buyer-contact guidelines first.
3. Use Advertising Help After Login for Creator Connections UI and campaign-related creator workflows.
4. Use internal client voice notes/templates where available.
5. For Seller Support cases, chats, and email-style replies, check `_local/local-permissions.md` for the configured operator identity before drafting or sending. Use the operator's full name for traceability when Amazon asks for a sender name or when signing a message; if no full name is stored locally, pause and ask the requester/current operator before sending. Do not commit the actual local operator identity to GitHub.
6. Draft the message first and preserve any Amazon-provided template or policy warning. When feasible, show the requester the exact outbound text before sending; after sending, report the exact text sent or the local path where it was saved.
7. Stop before clicking `Send`, submitting a support case, replying to a case, or issuing/referring to refunds unless Victor confirms the exact action.

## Seller Support Case Handling

- Follow up in an existing Seller Support case whenever the issue already has a case. Open a new case only when Seller Central blocks replies, the issue is materially different, or Victor explicitly asks for a new case.
- Keep case messages concise. State the entity, the problem, what was checked, the business impact, and the exact request to Amazon.
- Ask Amazon for root-cause evidence when cleanup advice does not explain the source of the problem. Useful requests include source shipment or receipt events, fulfillment-center action history, relabeling or adjustment events, and photos or examples of affected units or labels.
- Prefer email communication when the workflow allows it, but use chat when escalation speed matters or Victor approves chat.

## Seller Support Writing Style

- Start formal case messages with `Dear Amazon Support,` or a similarly concise greeting. For short follow-ups inside an active case, `Hello Amazon team,` is acceptable.
- Keep the message short and action-oriented: acknowledge Amazon's answer if replying, restate the unresolved issue, provide only necessary identifiers or evidence references, and ask Amazon for the specific action or clarification needed.
- Do not over-explain, flatter, or include generic filler. Amazon support messages should be clear enough to route and short enough to scan.
- If Amazon's answer does not resolve the issue, explicitly say what remains unresolved, such as missing Buy Box, unresolved title update, missing image evidence, unclear relabeling reason, or missing root-cause confirmation.
- Use attachments only when they materially support the request, and explicitly reference them in the message.
- Sign email-style support messages with the operator identity from `_local/local-permissions.md` or the current user context. Do not send the literal placeholder `CURRENT USERNAME`.
- For short active-case follow-ups, use:
  `Best,`
  `CURRENT USERNAME`
- For formal case submissions or appeals, use:
  `Best regards,`
  `CURRENT USERNAME`
- Do not use `Submitted by ...` unless explicitly requested.

## Live Seller Support Chat

- Wait for the support associate's first message before sending substantive details. A short greeting is fine.
- Send one focused message at a time, then wait for the associate's next reply.
- If the associate says they are still checking or researching, reply politely that the named operator is still waiting.
- Write as the account operator using the locally configured full name, not as an anonymous assistant.

## Inbound Defect Disputes

- When Seller Support says photos or defect evidence require a shipment dispute, use the shipment page instead of creating another generic support case.
- Path: shipment summary > `Problems` > product-level defect > `Resolve` > `Submit dispute`.
- Choose `Submit dispute`, not `Acknowledge the defect`, when the goal is photos, examples, or root-cause review.
- Keep dispute text short because Amazon may enforce a tight character limit. Ask for photos/examples of affected unit labels and the specific failure reason, such as print quality, placement, missing label, wrong barcode/FNSKU, or another issue.
