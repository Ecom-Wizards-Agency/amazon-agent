#!/usr/bin/env python3
"""Import shim: the resolver moved to company-ai-skills/lib/ew_paths.py.

The implementation left this repo on 12.08.2026 because every project needs the
same answer about the operator-local roots (Google Drive, pCloud, team vault),
and this repo was only its accidental home. This shim keeps every existing
import (`import ew_paths` / `from ew_paths import require`) and every
documented CLI call (`python3 tools/ew_paths.py drive`) working unchanged.

Resolution semantics are unchanged for this repo: pointer files still live in
this repo's `_local/`, passed through below, and the same env vars win first.
"""
import importlib.util
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOCAL = REPO / "_local"

_CANDIDATES = [
    os.environ.get("EW_COMPANY_LIB", ""),
    str(Path.home() / "os" / "company-ai-skills" / "lib"),
]


def _load():
    for candidate in _CANDIDATES:
        if not candidate:
            continue
        source = Path(os.path.expanduser(candidate)) / "ew_paths.py"
        if source.is_file():
            spec = importlib.util.spec_from_file_location("ew_paths_lib", source)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    sys.exit("ew_paths moved to company-ai-skills/lib/ew_paths.py and no "
             "checkout was found (checked $EW_COMPANY_LIB, then "
             "~/os/company-ai-skills/lib). Clone Ecom-Wizards-Agency/"
             "company-ai-skills to ~/os/company-ai-skills or set the env var.")


_lib = _load()

SOURCES = _lib.SOURCES
TOKENS = _lib.TOKENS
SETUP_HINT = _lib.SETUP_HINT


def root(name: str) -> str:
    return _lib.root(name, LOCAL)


def drive_root() -> str:
    return _lib.drive_root(LOCAL)


def pcloud_root() -> str:
    return _lib.pcloud_root(LOCAL)


def team_vault_root() -> str:
    return _lib.team_vault_root(LOCAL)


def expand_tokens(path: str) -> str:
    return _lib.expand_tokens(path, LOCAL)


def require(name: str) -> str:
    return _lib.require(name, LOCAL)


def main() -> int:
    os.environ.setdefault("EW_LOCAL_DIR", str(LOCAL))
    return _lib.main()


if __name__ == "__main__":
    sys.exit(main())
