#!/usr/bin/env python3
"""Launch a DEDICATED debug Chrome for the report fetcher.

A separate profile on the DevTools debug port that runs ALONGSIDE your normal
Chrome (no need to quit it). Log into Seller Central once in the window that
opens; the login persists in this profile for future runs. The debug port is
localhost-only.

Why not your normal Chrome profile? Chrome 136+ silently IGNORES
--remote-debugging-port on the default user-data-dir (verified on Chrome 149 on
2026-07-05: the browser starts fine, the port never opens). A graceful restart of
the real profile therefore can NEVER expose CDP, so the dedicated profile is the
only working path on current Chrome.

This is the cross-platform implementation. `launch-chrome-debug.sh` is a thin
bash wrapper kept because docs and muscle memory refer to it; do not duplicate
the logic there.

    python3 tools/report-fetcher/launch-chrome-debug.py

Env: CDP_PORT (9222) · CDP_PROFILE · CHROME_BIN · CDP_START_URL
"""
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PORT = os.environ.get("CDP_PORT", "9222")
PROFILE = Path(os.environ.get("CDP_PROFILE",
                              str(Path.home() / ".amazon-agent" / "chrome-debug")))
START_URL = os.environ.get("CDP_START_URL", "https://sellercentral.amazon.com")

CHROMES = [
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    # Windows: Chrome increasingly installs per-user, so check LOCALAPPDATA too.
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    # Linux
    "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser",
]


def port_is_up(attempts: int = 3) -> bool:
    """Is a debug Chrome already listening? Retried, because a single transient
    failure here makes us try to launch a SECOND browser on a profile that is
    already locked — noisy at best. urlopen also honours proxy env vars, so ask
    for 127.0.0.1 with the proxy explicitly disabled."""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for i in range(attempts):
        try:
            opener.open(f"http://127.0.0.1:{PORT}/json/version", timeout=3)
            return True
        except (urllib.error.URLError, OSError):
            if i + 1 < attempts:
                time.sleep(0.4)
    return False


def find_chrome() -> str:
    override = os.environ.get("CHROME_BIN", "")
    if override:
        if not Path(override).exists():
            sys.exit(f"CHROME_BIN points at {override}, which does not exist.")
        return override
    for candidate in CHROMES:
        if candidate and Path(candidate).exists():
            return candidate
    sys.exit("No Chrome/Chromium/Edge found. Install Google Chrome, or set "
             "CHROME_BIN to the browser executable.")


def main() -> None:
    if port_is_up():
        print(f"Debug port {PORT} already up. "
              "Ready -> node tools/report-fetcher/run.mjs doctor")
        return

    chrome = find_chrome()
    PROFILE.mkdir(parents=True, exist_ok=True)
    print(f"Launching debug Chrome (separate profile at {PROFILE}; "
          "your normal Chrome is untouched)...")
    # Detach so the browser outlives this process on every platform.
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0)
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen([chrome, f"--remote-debugging-port={PORT}",
                      f"--user-data-dir={PROFILE}", "--no-first-run",
                      "--no-default-browser-check", START_URL], **kwargs)

    for _ in range(20):  # up to ~10s; a cold profile is slower than the old sleep 2
        time.sleep(0.5)
        if port_is_up():
            break
    else:
        print(f"Warning: debug port {PORT} did not open within 10s. "
              "If a normal Chrome window appeared instead, close it and retry.")

    print("Sign into Seller Central in the NEW window "
          "(first run only - the login persists in this profile).")
    print("Next: node tools/report-fetcher/run.mjs doctor")


if __name__ == "__main__":
    main()
