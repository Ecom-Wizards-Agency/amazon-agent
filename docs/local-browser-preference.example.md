# Local Browser Preference Example

Copy this file to the project root as `local-browser-preference.md` if you want to save a personal browser preference for Amazon work.

Do not commit `local-browser-preference.md`. It is ignored by Git because browser choices, session notes, profile names, and account access context are personal/local.

Example:

```text
Scripted workflows (report fetcher, POE, listing capture): the shared CDP debug Chrome
(tools/report-fetcher/launch-chrome-debug.sh, port 9222). Launch/reuse it by default.
Interactive UI work: Chrome via the connected-browser extension.
Fallback for read-only checks: the internal agent browser.
```

Rules:

- Prefer the shared CDP debug Chrome for any workflow that has a script/CDP runner (see the Browser Standard in `AGENTS.md`).
- For interactive work, use the connected browser/session that is available in the current chat.
- Common choices are Chrome or Brave.
- Verify the selected account/advertiser, marketplace/country, page title/tool, and date range or filters before acting.
- If the preferred browser is unavailable or not logged in, pause and ask which connected browser/session to use.
- Never store passwords, cookies, tokens, account secrets, payment details, tax IDs, or profile paths in this file.
