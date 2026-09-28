---
name: amazon-seller-assistant-case-creation
description: "Prepare a new Seller Central support request through Seller Assistant, seek human support when needed, and verify whether Amazon created a case. Use for new issues on this route; use amazon-communications for existing case replies."
---

# Seller Assistant Case Creation

Browser: CDP (shared Grimoire session on port 9223).

Use this skill for a new Seller Central support issue that opens through Seller Assistant. The recorded route reached a human support chat but did not capture an Amazon case ID or a post-send readback. Treat the chat handoff and case creation as separate, observable outcomes.

## Inputs and authority

- Get the exact seller account, marketplace, issue, desired resolution, requester and approved case owner. Collect the relevant identifiers and evidence files; use the issue's actual facts, not values from the recorded example.
- Check Manage support cases for an existing case about the same issue. Continue that case with `amazon-communications` when one exists.
- Load [the shared case workflow](../../docs/team-owned-cases.md) before any outbound message. A verified team request can provide the issue-bound mandate; an account finding or request to check status cannot. Resolve the saved owner and approved signature from the machine-local case policy.
- Use the shared case service and operation journal for a submission. The currently recorded Seller Assistant route is not proof that the service's existing case form adapter supports it. If the service cannot verify and submit through the live route, stop with the prepared draft and report the capability gap. Do not bypass the service with a browser send.

## Recorded Seller Assistant route

1. Through `browserctl`, use the managed Grimoire Chrome session. Verify login, selected seller account, marketplace and the visible Seller Central page. Keep the account and marketplace claim through the dependent work. Recheck both before any upload or submission.
2. In Seller Central, open **Help** > **Manage support cases** > **Get help with a new issue**. Confirm that the **Seller Assistant** panel appears. Use the visible controls rather than a saved coordinate or a copied session URL.
3. Enter a short factual issue summary in **Message Seller Assistant...**. Read its reply and any offered support tool. **Open the tool** may lead to a separate self-service workflow; verify its name and relevance before opening it or changing anything there.
4. If the suggested steps do not resolve the issue, say what remains unresolved and request human support in the conversation. Answer follow-up prompts only from verified facts. If the panel is too narrow to inspect the conversation, **Chat history** > conversation **Options** > **Open full-page chat** can show the same thread; verify that the thread and account are still correct.
5. When Seller Assistant offers a human handoff, read the presented terms and context before using **Approve** or an equivalent control. Confirm the composer changes from **Message Seller Assistant...** to a human-agent message field before treating the exchange as a live support chat. The agent's name is dynamic.
6. Prepare a concise message for the human agent: what is wrong, what was checked, the business impact and the exact action or explanation requested. Attach only relevant evidence. Verify the chosen file, upload completion and draft text before submission. A file picker opening is not evidence that an attachment was uploaded.
7. Submit only through the authorized, compatible case service path. Afterward, read back the exact sent message and attachment in the conversation, then check **Manage support cases** for a matching case ID and status. Record the case ID only if Amazon visibly provides one. If the result is a live chat without a case ID, report that state accurately and reconcile before any retry.

The demonstrated brand, contact address, agent name, screenshot filename and message wording were case-specific inputs. Do not copy them into another case. Authentication and identity challenges remain with the operator and the configured authentication broker.
