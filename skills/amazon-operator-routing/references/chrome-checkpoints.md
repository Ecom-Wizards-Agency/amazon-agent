# Browser Checkpoints

Use the teammate's connected Codex browser for logged-in Amazon workflows after local library search. Common choices are Chrome or Brave.

If `local-browser-preference.md` exists in the project root, read it before browser work and use that preferred connected browser when available. If no local preference exists, use the connected browser/session available in the current chat.

Before acting in Amazon, verify the connected browser/session is logged in and confirm the selected account/advertiser, marketplace/country, visible page title/tool, and date range or filters when relevant. If the preferred browser is unavailable or not logged in, pause and ask which connected browser/session to use.

## Before Navigating

- Confirm the target account, brand/client, and marketplace if the task could affect more than one account.
- Search local docs and keep the relevant article/SOP paths ready.
- Identify risky actions in advance.
- If the user has not named a download folder, pause before downloading reports or exports.
- For Amazon Ads, start from `https://advertising.amazon.com/campaign-manager` and choose the account from the top-right account selector. Do not start Creator Connections from ~~`https://advertising.amazon.com/choose-account?destination=/bi`~~ because it can show only a partial account list.

## During Navigation

At each major screen, record:

- Page title or visible heading
- Account/entity/marketplace selector
- Relevant object ID: ASIN, SKU, order ID, case ID, shipment ID, campaign ID, ad group ID, report ID
- Selected filters and date range
- Visible warning/error/status text
- Table headers and key row values
- Sort order, pagination state, and whether filters hide rows
- Buttons that would submit, send, save, upload, confirm, create, delete, or change state

## Screenshot Rules

Take or save screenshots when:

- The page contains an error, warning, rejection reason, or account-health issue.
- A table shows report data, validation errors, file-upload errors, campaign status, or case history.
- The user needs a visual record of the route or final state.
- The UI is new or ambiguous and should become part of the future knowledge base.

## Stop Points

Stop and ask Victor before:

- Sending creator/customer/support messages.
- Submitting Seller Support cases or replies.
- Creating, confirming, or cancelling shipments.
- Uploading bulk files.
- Saving campaign/bid/budget/targeting changes.
- Changing account settings, users, permissions, payment, tax, or legal entity details.
- Acknowledging account health or policy actions.

## Cybersecurity-Safe Handling

- Do not copy, store, or repeat credentials, API secrets, bearer tokens, refresh tokens, payment identifiers, bank details, tax IDs, or private keys.
- If Amazon documentation shows credential examples, summarize the concept and link/path to the source instead of saving runnable secret-handling code.
- Avoid broad local process inspection, process killing, browser resets, or cleanup commands while operating the connected browser.
- If a page contains sensitive account data, capture only the minimum labels, statuses, IDs, and non-secret evidence needed for the task.

## Final Operator Note

End operational work with:

- What was done
- Source docs/SOPs used
- Final screen/state
- Files downloaded or prepared
- Open risks or unresolved issues
- Exact next action if Victor must confirm or take over
