#!/usr/bin/env python3
"""Read the operator-local roots: Google Drive, pCloud, the team vault.

This module deliberately does NOT go looking for those folders. Finding them is
`company-setup`'s job — it knows that Drive lives under
~/Library/CloudStorage/GoogleDrive-<account> on macOS but a drive letter or
~/My Drive on Windows, and that the shared-drives folder name is localized. It
detects once and writes the answer into `_local/*-path.txt` here. This repo is
the Amazon Agent; where a machine keeps its files is not its business.

So the contract is: setup writes, tools read. Adding detection back here would
put the same guess in two places, and the copy that is wrong is always the one
running on somebody else's machine.

Resolution order, per root:
  1. env var       (EW_DRIVE_ROOT / EW_PCLOUD_ROOT / AMAZON_AGENT_TEAM_VAULT)
  2. pointer file  (_local/drive-path.txt / pcloud-path.txt / team-vault-path.txt)

Everything returns "" when unconfigured or unmounted, rather than raising, so a
caller can fail closed with a useful message instead of writing to a wrong path.
Per-client configs should store only the part BELOW the resolved root: absolute
"/Users/<name>/..." paths break on every machine but the one they were written on.

    python3 tools/ew_paths.py               # show every resolved root
    python3 tools/ew_paths.py drive         # print one, exit 1 if unresolved
"""
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOCAL = REPO / "_local"

# (env var, pointer file, a child that proves the path is really mounted)
SOURCES = {
    "drive": ("EW_DRIVE_ROOT", "drive-path.txt", ""),
    "pcloud": ("EW_PCLOUD_ROOT", "pcloud-path.txt", "1_Delivery/1.1_Clients"),
    "team-vault": ("AMAZON_AGENT_TEAM_VAULT", "team-vault-path.txt", "Clients"),
}
SETUP_HINT = ("Run the company-setup bootstrap (--role amazon-operator) to write "
              "the pointer files, or set the env var for this run.")


def _first_line(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            t = line.strip()
            if t and not t.startswith("#"):
                return t
    except OSError:
        pass  # a missing pointer file is normal on a fresh clone
    return ""


def root(name: str) -> str:
    """Resolved root for "drive" / "pcloud" / "team-vault", or ""."""
    env_var, pointer, proof = SOURCES[name]
    for candidate in (os.environ.get(env_var, ""), _first_line(LOCAL / pointer)):
        if not candidate:
            continue
        path = Path(os.path.expandvars(os.path.expanduser(candidate)))
        # A configured path that is not mounted is worse than none: it would be
        # created as a plain local folder and the files would never sync.
        if path.exists() and (not proof or (path / proof).exists()):
            return str(path)
    return ""


def drive_root() -> str:
    """The 'Ecom Wizards' shared drive on this machine, or ""."""
    return root("drive")


def pcloud_root() -> str:
    """The pCloud 'Amazon Wizards' share, or "". When the mount is absent, the
    `pcloud-api` company skill is the mount-independent path."""
    return root("pcloud")


def team_vault_root() -> str:
    return root("team-vault")


TOKENS = {"{drive}": "drive", "{pcloud}": "pcloud", "{vault}": "team-vault"}


def expand_tokens(path: str) -> str:
    """Replace a leading {drive} / {pcloud} / {vault} token with the resolved root.

    This is how per-client configs stay portable: store
    "{drive}/04_Sales Audits/Luhxe" instead of an absolute
    "/Users/<name>/Library/CloudStorage/GoogleDrive-.../Geteilte Ablagen/...".
    A path with no token is returned unchanged, so old configs keep working.

    Raises SystemExit if a token is used but that root is unconfigured — silently
    dropping it would write the deliverable into a stray relative folder.
    """
    if not path:
        return path
    text = str(path)
    for token, name in TOKENS.items():
        if text.startswith(token):
            return os.path.join(require(name), text[len(token):].lstrip("/\\"))
    return text


def require(name: str) -> str:
    """Same as root(), but exits with the fix instead of returning ""."""
    value = root(name)
    if not value:
        env_var, pointer, _ = SOURCES[name]
        sys.exit(f"{name} root is not configured or not mounted.\n"
                 f"  checked: ${env_var}, then _local/{pointer}\n  {SETUP_HINT}")
    return value


def main() -> int:
    if len(sys.argv) > 1:
        name = sys.argv[1]
        if name not in SOURCES:
            print(f"unknown root: {name} (try: {', '.join(SOURCES)})", file=sys.stderr)
            return 2
        value = root(name)
        if not value:
            env_var, pointer, _ = SOURCES[name]
            print(f"{name}: not configured or not mounted "
                  f"(${env_var} / _local/{pointer})", file=sys.stderr)
            return 1
        print(value)
        return 0
    for name in SOURCES:
        print(f"{name:12} {root(name) or '(not configured or not mounted)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
