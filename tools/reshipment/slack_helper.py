"""Locate the Wizards AI Slack helper, on whichever OS this is running.

The helper lives in a separate repo (`Ecom-Wizards-Agency/wizards-ai`) cloned to
`~/os/wizards-ai` (the pre-31.07.2026 layout used `~/Automations/wizards-ai`,
still probed as a fallback for unmigrated machines). Its implementation is
`slack.py`; `slack.sh` is a bash wrapper kept for the macOS callers that
hardcode the `.sh` path.

So: prefer `slack.py` and run it with this interpreter. That works on Windows,
where there is no bash, and on macOS. Fall back to `slack.sh` only for an older
clone that predates the Python port.

Never reimplement the posting logic here. The send guard in that helper is what
stops a bot message reaching a client channel, and a second copy of it would
drift out of step with `config.json`.
"""
import subprocess
import sys
from pathlib import Path

HELPER_CANDIDATES = [
    Path.home() / "os" / "wizards-ai",
    Path.home() / "Automations" / "wizards-ai",  # pre-31.07.2026 layout
]


def helper_dir() -> Path:
    """First candidate clone that exists; the current layout wins."""
    for candidate in HELPER_CANDIDATES:
        if candidate.exists():
            return candidate
    return HELPER_CANDIDATES[0]


def helper_command() -> list:
    """argv prefix that invokes the helper. Raises if it isn't installed."""
    base = helper_dir()
    py = base / "slack.py"
    if py.exists():
        return [sys.executable, str(py)]
    sh = base / "slack.sh"
    if sh.exists():
        if sys.platform.startswith("win"):
            raise SystemExit(
                f"{sh} is a bash script and this is Windows, and {py} is missing.\n"
                "Update the wizards-ai clone (git pull). The helper was ported to "
                "Python on 30.07.2026 so it runs on both platforms."
            )
        return [str(sh)]
    raise SystemExit(
        f"Wizards AI Slack helper not found at {base}.\n"
        "Install it (the light 'posting helper' setup is enough; you do not need "
        "the scheduled bot): git clone "
        "https://github.com/Ecom-Wizards-Agency/wizards-ai.git ~/os/wizards-ai\n"
        "Then create .env with SLACK_BOT_TOKEN from 1Password."
    )


def run_helper(*args: str) -> str:
    """Call the helper and return raw stdout. Raises CalledProcessError on failure,
    which is deliberate: exit 3 is the send guard refusing, and that must be loud."""
    result = subprocess.run(helper_command() + list(args),
                            check=True, capture_output=True, text=True)
    return result.stdout
