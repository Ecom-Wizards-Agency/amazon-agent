# Browser Rules

- Use the persistent `grimoire` session on CDP 9223 for both direct chat and Slack. Resolve it before imports with `browserctl run --session grimoire -- …`. The separate `operator` profile on 9222 is explicit operator work, never an automatic fallback.
- Confirm Seller Central login in 9223 before account checks. An expired login pauses the affected work for brokered login or attended reauthentication in that profile; follow the degraded-run procedure if authentication cannot be restored.
- Each workflow owns its exact task tab. Hold the shared browser lock and regional account-context claim through account selection, reads and evidence capture. Concurrent requests must wait; multiple retained tabs never imply independent account sessions.
- One regional login covers every marketplace in that region. Stay on whichever Seller Central domain the active session uses (operators may be logged in via the DE, UK, IT, or another regional domain) and switch country/account only through the in-app marketplace/account switcher. Never reach another country in the same region by changing the Seller Central URL/domain - a domain change drops the session and forces a new login. The same applies to deep links such as the case log: open paths like `/cu/case-lobby` on the active session's domain.
- Verify account, marketplace, page title/tool, and date/filter context before recording.
- Repeat verification after account/marketplace switches, tool switches, or session timeouts.
- Never click `Submit appeal` during an account-health check unless the operator is present and has explicitly approved that exact action.
- Stop before appeals, acknowledgements, support contact, support replies, listing edits, shipment actions, messages, uploads, or account-changing actions.
