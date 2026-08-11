#!/bin/bash
# Bi-weekly reshipment readiness check. Every second Monday.
#
# This does NOT run the reshipment itself. The data pull needs either the
# port-9223 service-account session (the approved unattended read-only path) or
# the operator's attended port-9222 session, and on 11.08.2026 the first was
# failing account selection on every account while the second hung on the
# account picker. Shipping an untested automation that drives Seller Central is
# worse than shipping none.
#
# What it does do is the deterministic half: resolve every account's shared
# team-vault profile, work out which accounts could actually be planned today,
# and post ONE status to #amazon-check so the run is never silently skipped.
# Victor kicks off the attended pull from there.
#
# Widen this to the full run once the service-account session is healthy and a
# real pull has been verified end to end.
set -euo pipefail
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$DIR/../.." && pwd)"
SLACK_SH="$HOME/os/wizards-ai/slack.sh"
[ -x "$SLACK_SH" ] || SLACK_SH="$HOME/Automations/wizards-ai/slack.sh"
CHANNEL="C0BAZBZR49E"   # #amazon-check
LOG="$DIR/logs/biweekly-$(date +%F).log"
mkdir -p "$DIR/logs"

# launchd has no "every other week", so the job fires every Monday and the
# parity gate drops the off weeks. Anchor is the first intended run.
ANCHOR="2026-08-17"
DAYS=$(( ( $(date +%s) - $(date -j -f "%Y-%m-%d" "$ANCHOR" "+%s") ) / 86400 ))
if [ "$DAYS" -lt 0 ] || [ $(( DAYS % 14 )) -ne 0 ]; then
  echo "$(date): off week (day $DAYS since $ANCHOR) - nothing to do" >> "$LOG"
  exit 0
fi

# The roster is the 27.07.2026 scope. Planning inputs deliberately live in each
# client's team-vault Amazon Ops.md, never here, so adjusting a timeframe for
# one account is a vault edit and takes effect on the next run with no code
# change. That is also why an account with unconfigured inputs is reported
# rather than defaulted: the numbers are a human decision.
ROSTER="alphainfuse-us jbs-de evora-body-us seranova-us shaperluv-us sondur-us svens-island-us svens-island-aus swissklip-us"

READY=""; BLOCKED=""
for key in $ROSTER; do
  line=$(node "$REPO/tools/client-profiles/find-client-profile.mjs" "$key" 2>/dev/null | python3 -c "
import json,sys
raw=sys.stdin.read().strip()
if not raw.startswith('{'):
    print('BLOCKED|no profile matched'); raise SystemExit
m=(json.loads(raw).get('matches') or [{}])[0]
r=m.get('reshipment') or {}
if r.get('enabled') is True and r.get('effective_coverage_days'):
    print(f\"READY|{m.get('profile_name')}|{r['effective_coverage_days']}d coverage\")
else:
    missing=[k for k in ('target_stock_days','lead_time_days','amazon_booking_buffer_days','minimum_monthly_sales_for_fba') if not r.get(k)]
    print(f\"BLOCKED|{m.get('profile_name') or '$key'}|missing {', '.join(missing) or 'reshipment.enabled'}\")
" 2>/dev/null || echo "BLOCKED|$key|profile lookup failed")
  case "$line" in
    READY*)   READY="$READY• $(echo "$line" | cut -d'|' -f2) · $(echo "$line" | cut -d'|' -f3)"$'\n' ;;
    *)        BLOCKED="$BLOCKED• $(echo "$line" | cut -d'|' -f2) · $(echo "$line" | cut -d'|' -f3)"$'\n' ;;
  esac
done

NREADY=$(printf '%s' "$READY" | grep -c '•' || true)
NBLOCKED=$(printf '%s' "$BLOCKED" | grep -c '•' || true)
DATESTAMP=$(date '+%d.%m.%Y')

PARENT="*Reshipment run due ${DATESTAMP}* · ${NREADY} ready · ${NBLOCKED} blocked"
TS=$("$SLACK_SH" post "$CHANNEL" "$PARENT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('ts',''))")
[ -n "$TS" ] || { echo "$(date): parent post failed" >> "$LOG"; exit 1; }

[ "$NREADY" -gt 0 ] && "$SLACK_SH" post "$CHANNEL" "*Ready to plan*
$READY" "$TS" >> "$LOG" 2>&1
[ "$NBLOCKED" -gt 0 ] && "$SLACK_SH" post "$CHANNEL" "*Blocked: planning inputs not configured*
$BLOCKED
Set these in the client's team-vault \`Amazon Ops.md\` and they join the next run." "$TS" >> "$LOG" 2>&1

echo "$(date): posted $NREADY ready, $NBLOCKED blocked" >> "$LOG"
