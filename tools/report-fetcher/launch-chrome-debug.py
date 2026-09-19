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

Env: CDP_PORT (9223) · CDP_PROFILE · CHROME_BIN · CDP_START_URL ·
CDP_BROWSER_MODE (machine policy, otherwise headless) · CDP_WINDOW_SIZE (1920,1080)
"""
import argparse
import errno
import json
import os
import shlex
import subprocess
import struct
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

POLICY_PATH = Path(os.environ.get(
    "AMAZON_BROWSER_POLICY",
    str(Path.home() / ".amazon-agent" / "browser-runtime" / "policy.json"),
))


def read_port_policy(port: str) -> dict:
    try:
        policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    if policy.get("schema_version") not in (None, 1):
        raise RuntimeError("BROWSER_POLICY_INVALID: unsupported schema_version")
    value = (policy.get("ports") or {}).get(str(port)) or {}
    if not isinstance(value, dict):
        raise RuntimeError("BROWSER_POLICY_INVALID: port policy must be an object")
    return value


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "browserctl"))
from browser_session import session_environment
if os.environ.get("CDP_PORT", "9223") in {"9222", "9223"}:
    os.environ.update(session_environment(os.environ.get("AMAZON_BROWSER_SESSION") or
        ("operator" if os.environ.get("CDP_PORT") == "9222" else "grimoire"), inherit=True))
PORT = os.environ.get("CDP_PORT", "9223")
PORT_POLICY = read_port_policy(PORT)
DEFAULT_PROFILE = (Path.home() / ".amazon-agent" /
                   ("wizards-ai-chrome" if PORT == "9223" else "chrome-debug"))
WINDOW_W, WINDOW_H = (os.environ.get("CDP_WINDOW_SIZE", "1920,1080").split(",") + ["1080"])[:2]
PROFILE = Path(os.environ.get("CDP_PROFILE",
                              str(PORT_POLICY.get("profile")
                                  or DEFAULT_PROFILE))).expanduser()
START_URL = os.environ.get("CDP_START_URL",
                           str(PORT_POLICY.get("start_url")
                               or "https://sellercentral.amazon.com"))
DEFAULT_MODE = os.environ.get("CDP_BROWSER_MODE",
                              str(PORT_POLICY.get("mode") or "headless"))
WINDOW_CLASS = os.environ.get("CDP_WINDOW_CLASS",
                              str(PORT_POLICY.get("window_class") or ""))
RESTART_REASON = os.environ.get("CDP_EXPLICIT_RESTART_REASON", "").strip()
RESTART_AUTHORIZED = (os.environ.get("CDP_BROWSERCTL_RESTART") == "1"
                      and bool(RESTART_REASON))
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
    override = os.environ.get("CHROME_BIN", "") or str(PORT_POLICY.get("chrome_bin") or "")
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
        default=DEFAULT_MODE,
        help="defaults to the machine policy; mode changes require browserctl restart",
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


def process_arguments(pid: int) -> list[str]:
    if sys.platform.startswith("linux"):
        try:
            return Path(f"/proc/{pid}/cmdline").read_bytes().decode().strip("\0").split("\0")
        except (OSError, UnicodeError):
            return []
    result = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                            capture_output=True, text=True, check=False)
    try:
        return shlex.split(result.stdout) if result.returncode == 0 else []
    except ValueError:
        return []


def argument_value(arguments: list[str], flag: str) -> str | None:
    for index, argument in enumerate(arguments):
        if argument.startswith(flag + "="):
            return argument[len(flag) + 1:]
        if argument == flag and index + 1 < len(arguments):
            return arguments[index + 1]
    return None


def process_matches(pid: int) -> bool | None:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        return None
    arguments = process_arguments(pid)
    if not arguments:
        return None
    profile = argument_value(arguments, "--user-data-dir")
    return bool(profile and os.path.realpath(profile) == os.path.realpath(PROFILE)
                and argument_value(arguments, "--remote-debugging-port") == str(PORT)
                and not any(arg.startswith("--type=") for arg in arguments))


def listening_processes() -> set[int] | None:
    """Resolve socket owners, not processes that merely name the debug port."""
    if sys.platform.startswith("win"):
        return None
    if sys.platform.startswith("linux"):
        sockets = set()
        for table in ("tcp", "tcp6"):
            try:
                for line in Path(f"/proc/net/{table}").read_text().splitlines()[1:]:
                    fields = line.split()
                    if fields[3] == "0A" and int(fields[1].split(":")[-1], 16) == int(PORT):
                        sockets.add("socket:[" + fields[9] + "]")
            except OSError:
                continue
        owners = set()
        if not sockets:
            return None
        try:
            entries = list(Path("/proc").iterdir())
        except OSError:
            return None
        for entry in entries:
            if not entry.name.isdigit():
                continue
            try:
                for fd in (entry / "fd").iterdir():
                    try:
                        if os.readlink(fd) in sockets:
                            owners.add(int(entry.name))
                            break
                    except OSError:
                        continue
            except OSError:
                continue
        return owners or None
    try:
        result = subprocess.run(["lsof", "-nP", f"-iTCP:{PORT}", "-sTCP:LISTEN", "-t"],
                                capture_output=True, text=True, check=False)
        return {int(pid) for pid in result.stdout.split() if pid.isdigit()} or None
    except OSError:
        return None


def find_matching_process() -> tuple[int, str] | None:
    """Verify the listening process's port and canonical profile before adoption."""
    return listener_profile_status()[1]


def listener_profile_status() -> tuple[bool | None, tuple[int, str] | None]:
    owners = listening_processes()
    verified = None
    for pid in sorted(owners or []):
        matches = process_matches(pid)
        if matches is True:
            arguments = process_arguments(pid)
            mode = "headless" if any(arg.startswith("--headless") for arg in arguments) else "headed"
            return True, (pid, mode)
        if matches is False:
            verified = False
    return verified, None


def devtools_active_port() -> str | None:
    try:
        lines = (PROFILE / "DevToolsActivePort").read_text(encoding="utf-8").splitlines()
        return lines[0] if lines else None
    except OSError:
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
    matches = process_matches(pid)
    if matches is False or (matches is None and not sys.platform.startswith("win")):
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


def broker_traverse_acl(parent: Path) -> bytes | None:
    """Retain only an installed broker's traverse entry on the private root.

    Linux chmod(0700) zeros the POSIX ACL mask, which silently disables the
    authentication broker's existing --x entry. Rebuild a restrictive access
    ACL instead of restoring the old mask, which could enable other entries.
    The binary layout is the Linux UAPI in linux/posix_acl_xattr.h.
    """
    if not sys.platform.startswith("linux"):
        return None
    import pwd
    try:
        broker_uid = pwd.getpwnam("wizards-transport").pw_uid
    except KeyError:
        return None
    try:
        acl = os.getxattr(parent, "system.posix_acl_access")
    except OSError as exc:
        if exc.errno in (errno.ENODATA, errno.EOPNOTSUPP):
            return None
        raise
    if len(acl) < 4 or (len(acl) - 4) % 8 or struct.unpack("<I", acl[:4])[0] != 2:
        raise RuntimeError("Unrecognized Linux access ACL on the browser root")
    entries = list(struct.iter_unpack("<HHI", acl[4:]))
    # A declared --x entry is the installed grant, even if an earlier chmod
    # masked it. Never add a new broker grant or retain read/write permissions.
    if (0x02, 0x01, broker_uid) not in entries:
        return None
    undefined = 0xFFFFFFFF
    private = ((0x01, 0x07, undefined), (0x02, 0x01, broker_uid),
               (0x04, 0, undefined), (0x10, 0x01, undefined), (0x20, 0, undefined))
    return struct.pack("<I", 2) + b"".join(struct.pack("<HHI", *entry) for entry in private)


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
            acl = broker_traverse_acl(parent) if not parent_created else None
            if acl is None:
                os.chmod(parent, 0o700)
            else:
                os.setxattr(parent, "system.posix_acl_access", acl)
        os.chmod(PROFILE, 0o700)


def main() -> None:
    options = parse_args()
    state = read_state()
    if options.mode == "status":
        running = port_is_up()
        verified, matching = listener_profile_status() if running else (None, None)
        legacy = matching if not state else None
        print(json.dumps({"port": PORT, "profile": str(PROFILE),
                          "running": running, "managed": bool(state),
                          "profile_verified": verified,
                          "devtools_active_port": devtools_active_port(),
                          "mode": state.get("mode") or (legacy[1] if legacy else None),
                          "pid": state.get("pid") or (legacy[0] if legacy else None),
                          "adoptable": bool(legacy)}))
        return

    if options.mode == "stop":
        if not RESTART_AUTHORIZED:
            raise RuntimeError(
                "EXPLICIT_RESTART_REQUIRED: stop Chrome through browserctl restart with a reason"
            )
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
    if requested != DEFAULT_MODE and not RESTART_AUTHORIZED:
        raise RuntimeError(
            "MODE_CHANGE_REQUIRES_RESTART: change Chrome mode through browserctl restart "
            "with a reason"
        )
    if port_is_up():
        if not state and options.adopt_existing:
            legacy = find_matching_process()
            if not legacy:
                raise RuntimeError(
                    f"Debug port {PORT} is active, but no Chrome process matches profile {PROFILE}."
                )
            pid, detected_mode = legacy
            state = write_state(pid, detected_mode, adopted=True)
            print(f"Adopted legacy Chrome pid {pid} on port {PORT} ({detected_mode} mode).")
        if state.get("mode") == requested:
            print(f"Debug port {PORT} already up in {requested} mode.")
            return
        if not state:
            raise RuntimeError(
                f"Debug port {PORT} is already used by an unmanaged dedicated Chrome. "
                f"Adopt it explicitly before managing it."
            )
        raise RuntimeError(
            f"MODE_CHANGE_REQUIRES_RESTART: debug port {PORT} is running in "
            f"{state.get('mode') or 'unknown'} mode; requested {requested}. "
            "Use browserctl restart with an explicit reason."
        )

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
    # Pin the UI language for every marketplace. Seller Central renders in the
    # browser's language, so a .de or .co.jp host otherwise hands back a page
    # whose account names, marketplace names and button labels are localized.
    # On 11.08.2026 that silently broke every scheduled inventory pass: the
    # picker offered "Vereinigte Staaten" while the automation looked for
    # "United States". Setting it here rather than on the Amazon account keeps
    # it a local browser preference and changes nothing on the seller profile.
    # Always a full desktop viewport, headless included. Headless Chrome otherwise
    # starts at 800x600, which is small enough that Amazon serves a narrow layout:
    # lazy-loaded gallery and A+ modules never enter the viewport, screenshots come
    # out cramped or clipped, and evidence captures land near the 600x350 floor the
    # selector rejects. One size for every mode and both ports (9222 here, 9223 for
    # the Wizards AI read browser, which launches through this same file).
    # No on-device model in a scraping profile. Chrome downloads Gemini Nano through
    # the optimization guide for browser AI features we never use, and it is not small:
    # on 12.08.2026 OptGuideOnDeviceModel held 4.0 GB of the port-9222 profile's 5.5 GB.
    # The agent already brings its own model. Disabling the feature stops the download
    # and the periodic re-download after each component update.
    command = [chrome, f"--remote-debugging-port={PORT}",
               "--remote-debugging-address=127.0.0.1",
               f"--user-data-dir={PROFILE}", "--no-first-run",
               "--no-default-browser-check",
               f"--window-size={WINDOW_W},{WINDOW_H}",
               "--lang=en-US", "--accept-lang=en-US,en",
               "--disable-features=OptimizationGuideOnDeviceModel,"
               "OptimizationGuideModelDownloading"]
    if WINDOW_CLASS:
        if not all(character.isalnum() or character in "._-" for character in WINDOW_CLASS):
            raise RuntimeError("BROWSER_POLICY_INVALID: unsafe window class")
        command.append(f"--class={WINDOW_CLASS}")
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
