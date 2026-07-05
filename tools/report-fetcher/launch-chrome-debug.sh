#!/usr/bin/env bash
# Launch a DEDICATED debug Chrome for the report fetcher — a separate profile on
# the DevTools debug port that runs ALONGSIDE your normal Chrome (no need to quit
# it). Log into Seller Central once in the window that opens; the login persists
# in this profile for future runs. The debug port is localhost-only.
set -euo pipefail
PORT="${CDP_PORT:-9222}"
PROFILE="${CDP_PROFILE:-$HOME/.amazon-agent/chrome-debug}"
CHROME="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"

if curl -s "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  echo "Debug Chrome is already up on port ${PORT}. Ready — run:"
  echo "  node tools/report-fetcher/run.mjs doctor"
  exit 0
fi

mkdir -p "$PROFILE"
echo "Launching a dedicated debug Chrome (separate window/profile; your normal Chrome is untouched)…"
"$CHROME" --remote-debugging-port="$PORT" --user-data-dir="$PROFILE" \
  --no-first-run --no-default-browser-check \
  "https://sellercentral.amazon.com" >/dev/null 2>&1 &
sleep 2
echo "Done. In the NEW Chrome window, sign in to Seller Central (US / Sven's Island)."
echo "The login is saved in this debug profile for next time. Then run:"
echo "  node tools/report-fetcher/run.mjs doctor"
