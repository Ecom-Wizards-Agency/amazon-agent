#!/usr/bin/env bash
# Launch a DEDICATED debug Chrome for the report fetcher — a separate profile on
# the DevTools debug port that runs ALONGSIDE your normal Chrome (no need to quit
# it). Log into Seller Central once in the window that opens; the login persists
# in this profile for future runs. The debug port is localhost-only.
#
# Why not your normal Chrome profile? Chrome 136+ silently IGNORES
# --remote-debugging-port on the default user-data-dir (verified on Chrome 149
# on 2026-07-05: the browser starts fine, the port never opens). A graceful
# restart of the real profile therefore can NEVER expose CDP — the dedicated
# profile is the only working path on current Chrome.
set -euo pipefail
PORT="${CDP_PORT:-9222}"
PROFILE="${CDP_PROFILE:-$HOME/.amazon-agent/chrome-debug}"
CHROME="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
START_URL="${CDP_START_URL:-https://sellercentral.amazon.com}"

if curl -s "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  echo "Debug port ${PORT} already up. Ready → node tools/report-fetcher/run.mjs doctor"
  exit 0
fi

mkdir -p "$PROFILE"
echo "Launching debug Chrome (separate profile at $PROFILE; your normal Chrome is untouched)…"
"$CHROME" --remote-debugging-port="$PORT" --user-data-dir="$PROFILE" \
  --no-first-run --no-default-browser-check "$START_URL" >/dev/null 2>&1 &
sleep 2
echo "Sign into Seller Central in the NEW window (first run only — the login persists in this profile)."
echo "Next: node tools/report-fetcher/run.mjs doctor"
