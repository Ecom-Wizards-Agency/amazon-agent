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

Env: CDP_PORT (9222) · CDP_PROFILE · CHROME_BIN · CDP_START_URL ·
CDP_BROWSER_MODE (headless)
"""
import argparse
import json
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
STATE_FILE = PROFILE / ".amazon-agent-browser.json"

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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=("headed", "headless", "recovery", "stop", "status"),
        default=os.environ.get("CDP_BROWSER_MODE", "headless"),
        help="headless is the normal background mode; recovery is a visible operator session",
    )
    parser.add_argument(
        "--adopt-existing",
        action="store_true",
        help=("adopt a legacy launcher process only after verifying its port and "
              "user-data-dir; required before changing its mode"),
    )
    return parser.parse_args()


def read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def process_matches(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        return True
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "command="],
        capture_output=True, text=True, check=False,
    )
    return result.returncode == 0 and f"--user-data-dir={PROFILE}" in result.stdout


def find_matching_process() -> tuple[int, str] | None:
    """Find a legacy debug Chrome for this exact port and profile.

    Older launcher versions did not write STATE_FILE. We never infer ownership
    from an open port alone: both command-line flags must match before an
    explicit --adopt-existing can take control of that process.
    """
    if sys.platform.startswith("win"):
        return None
    result = subprocess.run(
        ["ps", "ax", "-o", "pid=,command="],
        capture_output=True, text=True, check=False,
    )
    port_flag = f"--remote-debugging-port={PORT}"
    profile_flag = f"--user-data-dir={PROFILE}"
    for line in result.stdout.splitlines():
        try:
            pid_text, command = line.strip().split(None, 1)
        except ValueError:
            continue
        if port_flag in command and profile_flag in command and "--type=" not in command:
            mode = "headless" if "--headless" in command else "headed"
            return int(pid_text), mode
    return None


def write_state(pid: int, mode: str, *, adopted: bool = False) -> dict:
    protect_profile()
    state = {
        "pid": pid, "mode": mode, "port": PORT,
        "profile": str(PROFILE), "started_at": int(time.time()),
    }
    if adopted:
        state["adopted"] = True
    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    if not sys.platform.startswith("win"):
        os.chmod(STATE_FILE, 0o600)
    return state


def stop_managed_browser(state: dict) -> None:
    pid = int(state.get("pid") or 0)
    if not process_matches(pid):
        raise RuntimeError(
            f"Debug port {PORT} is active, but its managed Chrome process could not be verified. "
            "Close only the dedicated browser and retry."
        )
    if sys.platform.startswith("win"):
        subprocess.run(["taskkill", "/PID", str(pid), "/T"], check=False,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        os.kill(pid, 15)
    for _ in range(40):
        time.sleep(0.25)
        if not port_is_up(attempts=1):
            STATE_FILE.unlink(missing_ok=True)
            return
    raise RuntimeError(f"Dedicated Chrome on port {PORT} did not stop cleanly")


def protect_profile() -> None:
    parent = PROFILE.parent
    parent_created = not parent.exists()
    parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    PROFILE.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not sys.platform.startswith("win"):
        # Harden the standard private root and parents created by this launcher.
        # A custom profile may sit under /tmp or another shared directory whose
        # permissions this process neither owns nor should change.
        if parent_created or parent == Path.home() / ".amazon-agent":
            os.chmod(parent, 0o700)
        os.chmod(PROFILE, 0o700)


def main() -> None:
    options = parse_args()
    state = read_state()
    if options.mode == "status":
        legacy = find_matching_process() if not state and port_is_up() else None
        print(json.dumps({"port": PORT, "profile": str(PROFILE),
                          "running": port_is_up(), "managed": bool(state),
                          "mode": state.get("mode") or (legacy[1] if legacy else None),
                          "pid": state.get("pid") or (legacy[0] if legacy else None),
                          "adoptable": bool(legacy)}))
        return

    if options.mode == "stop":
        if port_is_up():
            if not state:
                raise RuntimeError(
                    f"Debug port {PORT} is active, but its browser is not managed by this launcher."
                )
            stop_managed_browser(state)
        else:
            STATE_FILE.unlink(missing_ok=True)
        print(f"Dedicated Chrome on port {PORT} is stopped.")
        return

    requested = options.mode
    if port_is_up():
        if not state and options.adopt_existing:
            legacy = find_matching_process()
            if not legacy:
                raise RuntimeError(
                    f"Debug port {PORT} is active, but no Chrome process matches profile {PROFILE}."
                )
            pid, detected_mode = legacy
            adopted_mode = "recovery" if requested == "recovery" and detected_mode == "headed" else detected_mode
            state = write_state(pid, adopted_mode, adopted=True)
            print(f"Adopted legacy Chrome pid {pid} on port {PORT} ({adopted_mode} mode).")
        if state.get("mode") == requested:
            print(f"Debug port {PORT} already up in {requested} mode.")
            return
        if not state:
            raise RuntimeError(
                f"Debug port {PORT} is already used by an unmanaged dedicated Chrome. "
                f"Close that one profile before switching to {requested} mode."
            )
        stop_managed_browser(state)

    chrome = find_chrome()
    protect_profile()
    print(f"Launching {requested} debug Chrome (separate profile at {PROFILE}; "
          "your normal Chrome is untouched)...")
    # Detach so the browser outlives this process on every platform.
    kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if sys.platform.startswith("win"):
        kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0)
    else:
        kwargs["start_new_session"] = True
    command = [chrome, f"--remote-debugging-port={PORT}",
               "--remote-debugging-address=127.0.0.1",
               f"--user-data-dir={PROFILE}", "--no-first-run",
               "--no-default-browser-check"]
    if requested == "headless":
        command.append("--headless")
    command.append(START_URL)
    process = subprocess.Popen(command, **kwargs)
    write_state(process.pid, requested)

    for _ in range(20):  # up to ~10s; a cold profile is slower than the old sleep 2
        time.sleep(0.5)
        if port_is_up():
            break
    else:
        print(f"Warning: debug port {PORT} did not open within 10s. "
              "If a normal Chrome window appeared instead, close it and retry.")

    if requested != "headless":
        print("Sign into Seller Central in the NEW window "
              "(first run only - the login persists in this profile).")
    print("Next: node tools/report-fetcher/run.mjs doctor")


if __name__ == "__main__":
    main()
