#!/usr/bin/env python3
"""Resolve the operator-local roots: Google Drive, pCloud, the team vault.

Why this exists: per-client configs used to hard-code absolute paths like
`/Users/victoruhl/Library/CloudStorage/GoogleDrive-.../Geteilte Ablagen/...`.
Those break on *any* second machine, Mac included, which is the real reason this
repo had only ever run on one computer. Resolve the root here and keep only the
relative part in configs.

Resolution order, same shape as `pcloud-archive.mjs` already uses:
  1. env var          (EW_DRIVE_ROOT / EW_PCLOUD_ROOT / AMAZON_AGENT_TEAM_VAULT)
  2. pointer file     (_local/drive-path.txt, pcloud-path.txt, team-vault-path.txt)
  3. auto-detection   (Drive only — the mount location is predictable per OS)

Everything returns "" when unavailable rather than raising, so a caller can fail
closed with a useful message instead of writing to a wrong path.

CLI:
    python3 tools/ew_paths.py            # show every resolved root
    python3 tools/ew_paths.py drive      # print one root, exit 1 if unresolved
"""
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOCAL = REPO / "_local"

# Google Drive for Desktop localizes the shared-drives folder. Ecom Wizards
# accounts are German, hence "Geteilte Ablagen"; keep English for other setups.
SHARED_DRIVE_NAMES = ("Geteilte Ablagen", "Shared drives")
TEAM_DRIVE = "Ecom Wizards"


def _first_line(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            t = line.strip()
            if t and not t.startswith("#"):
                return t
    except OSError:
        pass  # a missing pointer file is normal
    return ""


def _expand(p: str) -> str:
    return os.path.expandvars(os.path.expanduser(p)) if p else ""


def _configured(env_var: str, pointer: str) -> str:
    for candidate in (os.environ.get(env_var, ""), _first_line(LOCAL / pointer)):
        root = _expand(candidate)
        if root and Path(root).exists():
            return root
    return ""


def _detect_drive() -> str:
    """Find a Google Drive for Desktop mount holding the Ecom Wizards shared drive."""
    roots = []
    if sys.platform == "darwin":
        cloud = Path.home() / "Library" / "CloudStorage"
        roots += sorted(cloud.glob("GoogleDrive-*")) if cloud.exists() else []
    elif sys.platform.startswith("win"):
        # Drive mounts either as a lettered drive or under the user profile.
        roots += [Path(f"{c}:\\") for c in "GHIJKLMNOPQRSTUVWXYZ"]
        roots += [Path.home() / "My Drive", Path.home() / "Google Drive"]
    else:
        roots += [Path.home() / "GoogleDrive", Path.home() / "google-drive"]

    for root in roots:
        try:
            if not root.exists():
                continue
        except OSError:
            continue  # unmapped Windows drive letters raise rather than return False
        for shared in SHARED_DRIVE_NAMES:
            if (root / shared / TEAM_DRIVE).exists():
                return str(root)
        if (root / TEAM_DRIVE).exists():  # already pointed at the shared-drives level
            return str(root)
    return ""


def drive_root() -> str:
    """Root of the Google Drive mount, or "" when not configured/mounted."""
    return _configured("EW_DRIVE_ROOT", "drive-path.txt") or _detect_drive()


def drive_shared() -> str:
    """The `<drive>/<shared-drives>/Ecom Wizards` folder, or ""."""
    root = drive_root()
    if not root:
        return ""
    for shared in SHARED_DRIVE_NAMES:
        p = Path(root) / shared / TEAM_DRIVE
        if p.exists():
            return str(p)
    p = Path(root) / TEAM_DRIVE
    return str(p) if p.exists() else ""


def pcloud_root() -> str:
    """Root of the pCloud Amazon Wizards share, or "". When the mount is absent,
    the `pcloud-api` company skill is the mount-independent path."""
    return _configured("EW_PCLOUD_ROOT", "pcloud-path.txt")


def team_vault_root() -> str:
    """Root of the shared team vault, or ""."""
    root = _configured("AMAZON_AGENT_TEAM_VAULT", "team-vault-path.txt")
    return root if root and (Path(root) / "Clients").exists() else ""


ROOTS = {"drive": drive_root, "drive-shared": drive_shared,
         "pcloud": pcloud_root, "team-vault": team_vault_root}


def main() -> int:
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in ROOTS:
            print(f"unknown root: {name} (try: {', '.join(ROOTS)})", file=sys.stderr)
            return 2
        value = ROOTS[name]()
        if not value:
            print(f"{name}: not configured or not mounted", file=sys.stderr)
            return 1
        print(value)
        return 0
    for name, fn in ROOTS.items():
        print(f"{name:14} {fn() or '(not configured or not mounted)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
