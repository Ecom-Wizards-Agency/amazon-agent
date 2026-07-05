#!/usr/bin/env bash
# Put the DevTools debug port on your NORMAL Chrome (default profile) so the
# report fetcher uses your ACTIVE Seller Central session — no separate window,
# no re-login. CDP requires Chrome to be *started* with the flag, so if Chrome is
# already running this does a GRACEFUL restart of your normal profile: cookies and
# logins persist (you stay signed in); a Seller Central tab is reopened for you.
#
# Prefer a throwaway profile instead (no restart, but you log in there once)?
#   CDP_PROFILE="$HOME/.amazon-agent/chrome-debug" tools/report-fetcher/launch-chrome-debug.sh
set -euo pipefail
PORT="${CDP_PORT:-9222}"
CHROME="${CHROME_BIN:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
START_URL="https://sellercentral.amazon.com"

if curl -s "http://127.0.0.1:${PORT}/json/version" >/dev/null 2>&1; then
  echo "Debug port ${PORT} already up. Ready → node tools/report-fetcher/run.mjs doctor"
  exit 0
fi

PROFILE_ARGS=()
if [ -n "${CDP_PROFILE:-}" ]; then
  mkdir -p "$CDP_PROFILE"
  PROFILE_ARGS=(--user-data-dir="$CDP_PROFILE")
  echo "Dedicated debug profile at $CDP_PROFILE — you'll sign into Seller Central there once."
else
  if pgrep -x "Google Chrome" >/dev/null 2>&1; then
    echo "Restarting your Chrome with the debug port (you stay logged in; Seller Central reopens)…"
    osascript -e 'quit app "Google Chrome"' >/dev/null 2>&1 || true
    for _ in $(seq 1 40); do pgrep -x "Google Chrome" >/dev/null 2>&1 || break; sleep 0.5; done
    sleep 1
  fi
fi

"$CHROME" --remote-debugging-port="$PORT" "${PROFILE_ARGS[@]}" \
  --no-first-run --no-default-browser-check "$START_URL" >/dev/null 2>&1 &
sleep 2
if [ -z "${CDP_PROFILE:-}" ]; then
  echo "Chrome relaunched with your normal profile — still signed into Seller Central."
else
  echo "Debug Chrome launched — sign into Seller Central in the new window (persists next time)."
fi
echo "Next: node tools/report-fetcher/run.mjs doctor"
