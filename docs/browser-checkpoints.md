# Browser Checkpoints

Which browser to use per agent, the login rule, and the session-verification rule live in the Browser Standard section of `AGENTS.md`. This file is the detailed per-screen procedure for logged-in Amazon workflows after local library search.

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

## Driving Seller Central Controls

Seller Central is built on `kat-*` web components. The element you can see is a host; the
control that actually responds lives inside its shadow root. This breaks the usual
automation reflexes, so prefer the techniques that are known to work:

- **Text and number fields**: JS `.focus()` on the inner `input`, then CDP `Input.insertText`.
- **Plain buttons** (Save, Confirm, a row action): `.click()` on the element works.
- **Checkboxes, radios, dropdown options**: dispatch real mouse events at coordinates
  measured in the *same* call that clicks. Open a dropdown first, then click the option
  once it has non-zero size.

These fail silently, so do not trust them:

- Setting `.value` and dispatching `input`/`change`. The field displays the value and the
  page may even compute a derived total from it, while the app's own state never updates.
- `.click()` on a custom checkbox or a dropdown option.
- Coordinates measured in an earlier call. Layout shifts between calls and the click lands
  somewhere else while still reporting success.
- `document.elementFromPoint` as a hit test. It returns the shadow host, so the test passes
  while the click misses the real control. A checkbox cell can measure 52x168 while the
  clickable box inside it is 16x16.

**Screenshot before forming a hypothesis about why a control "is not working".** Inferring
state from DOM queries is the single most expensive mistake available here: a field can
hold the right value in the DOM and still not be registered, and the missing step is
usually a button that is plainly visible on screen. Two screenshots beat fifteen DOM
queries.

**Hand the click to the operator after about three failed attempts.** A control that
resists automation takes a human seconds. Continuing to grind costs far more of the
operator's time than asking, and each failed attempt risks leaving the page in a worse
state than it started.

## Stop Points

Stop and ask the operator before the actions below unless the operator explicitly
approved that exact action in the current chat or a matching scoped permission exists in
`_local/local-permissions.md`:

- Sending creator/customer/support messages.
- Submitting Seller Support cases or replies.
- Creating, confirming, or cancelling shipments.
- Uploading bulk files.
- Saving campaign/bid/budget/targeting changes.
- Changing account settings, users, permissions, payment, tax, or legal entity details.
- Acknowledging account health or policy actions.

Approval authorizes only the reviewed action and payload. Immediately before acting,
re-verify the account, marketplace, object identifiers, quantities, prices, fees, and
selected options. If the final screen introduces or changes a material term, stop for a
new approval. After acting, capture the resulting status or identifier and report it.

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
- Exact next action if the operator must confirm or take over
