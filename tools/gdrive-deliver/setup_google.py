#!/usr/bin/env python3
"""Link every Google connection the agent needs, in one run.

Delivery touches three Composio toolkits, and each one is a separate OAuth grant:

  googledrive    upload, convert and verify a delivered file
  googledocs     edit a delivered Doc in place, which is what preserves its comments
  googlesheets   edit a delivered Sheet in place, same reason

Linking them one at a time is the step people half-finish, and a half-finished setup only
shows up later as "no active connection" in the middle of a delivery. So this walks all three
in order, skips the ones already connected, and verifies the result.

Usage:
  python3 tools/gdrive-deliver/setup_google.py            link what is missing, then verify
  python3 tools/gdrive-deliver/setup_google.py --check    verify only, link nothing

Sign in with the same Google account for all three. That account is who the agent delivers
as, so it has to be the one that can reach the destination folders. Composio keeps
connections server-side under the API key in `~/.composio`, so API keys are per person and
must never be shared between machines: a shared key makes every machine deliver as whoever
linked Google first.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path

TOOLKITS = {
    "googledrive": "upload, convert and verify delivered files",
    "googledocs": "edit a delivered Doc in place, preserving its comments",
    "googlesheets": "edit a delivered Sheet in place, preserving its comments",
}


def connections(toolkit: str) -> list[dict]:
    proc = subprocess.run(["composio", "connections", "list", "--toolkit", toolkit],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"[setup] could not read connections. Is the Composio CLI installed and "
                         f"logged in (`composio login`)?\n{proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout).get(toolkit, [])
    except json.JSONDecodeError:
        raise SystemExit(f"[setup] unexpected output from the Composio CLI:\n{proc.stdout[:400]}")


def is_active(toolkit: str) -> bool:
    return any(c.get("status") == "ACTIVE" for c in connections(toolkit))


def stale(toolkit: str) -> list[str]:
    """Half-finished links. Harmless, but they make `connections list` ambiguous to read."""
    return [c.get("word_id", "?") for c in connections(toolkit) if c.get("status") != "ACTIVE"]


def google_account() -> str:
    proc = subprocess.run(["composio", "execute", "GOOGLEDRIVE_GET_ABOUT",
                           "-d", json.dumps({"fields": "user"})], capture_output=True, text=True)
    if proc.returncode != 0:
        return ""
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return ""
    data = result.get("data") or {}
    return ((data.get("user") or {}).get("emailAddress") or "")


def drive_mounts() -> list[str]:
    """Drive for Desktop mounts on this machine, if any."""
    base = Path.home() / "Library" / "CloudStorage"
    if not base.is_dir():
        return []
    return sorted(p.name.split("GoogleDrive-", 1)[1]
                  for p in base.glob("GoogleDrive-*") if "@" in p.name)


def main() -> int:
    ap = argparse.ArgumentParser(description="Link the agent's Google connections in one run.")
    ap.add_argument("--check", action="store_true", help="verify only, do not link anything")
    a = ap.parse_args()

    missing = [t for t in TOOLKITS if not is_active(t)]

    if a.check:
        pass
    elif not missing:
        print("[setup] all three Google connections are already active.")
    else:
        print(f"[setup] {len(missing)} to link: {', '.join(missing)}")
        print("[setup] Each one opens a browser. Sign in with the SAME Google account every "
              "time.\n")
        for toolkit in missing:
            print(f"[setup] linking {toolkit} ({TOOLKITS[toolkit]})")
            # stdio is inherited on purpose: `composio link` opens a browser and waits for the
            # grant, so the person running this has to see and drive it.
            proc = subprocess.run(["composio", "link", toolkit])
            if proc.returncode != 0:
                print(f"[setup] linking {toolkit} did not complete. Re-run this script to pick "
                      f"up where it stopped.", file=sys.stderr)
                return 1
            print()

    # Verify against the connection list rather than trusting the exit codes above.
    print("[setup] verifying:")
    ok = True
    for toolkit in TOOLKITS:
        active = is_active(toolkit)
        ok = ok and active
        print(f"  {'OK  ' if active else 'MISSING'} {toolkit}")
        for word_id in stale(toolkit):
            print(f"       half-finished link left over: {word_id} "
                  f"(clear it with `composio connections remove {word_id}`)")

    if not ok:
        print("\n[setup] Not finished. Re-run without --check to link what is missing.",
              file=sys.stderr)
        return 1

    account = google_account()
    if account:
        print(f"\n[setup] Connected as {account}. The agent delivers as this account, so it has "
              f"to be the one that can reach the destination folders.")

    mounts = drive_mounts()
    if mounts:
        print(f"[setup] Drive for Desktop is mounted for: {', '.join(mounts)}. Delivery can pass "
              f"a folder path, with no size limit.")
    else:
        print("[setup] No Drive for Desktop mount found, which is fine. Pass the destination as "
              "a Drive folder id or URL instead. That route caps at 5 MB per file.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
