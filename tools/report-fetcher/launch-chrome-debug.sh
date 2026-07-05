#!/usr/bin/env bash
# Launch Chrome with the DevTools debug port so the report fetcher can drive the
# real page (main world) over CDP. Uses your normal Chrome profile, so your
# Seller Central login carries over. Quit Chrome fully first (one instance per
# profile). The debug port is localhost-only and only open while Chrome runs.
set -euo pipefail
PORT="${CDP_PORT:-9222}"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if pgrep -x "Google Chrome" >/dev/null 2>&1; then
  echo "Chrome is already running. Quit it fully (Cmd+Q) first, then re-run this script."
  echo "(One Chrome instance per profile — the debug port can't attach to an already-running Chrome.)"
  exit 1
fi
echo "Launching Chrome with --remote-debugging-port=$PORT (your normal profile)…"
"$CHROME" --remote-debugging-port="$PORT" >/dev/null 2>&1 &
sleep 1
echo "Done. Open Seller Central, confirm you're logged in (US / Svens Island), then run:"
echo "  node tools/report-fetcher/run.mjs doctor"
