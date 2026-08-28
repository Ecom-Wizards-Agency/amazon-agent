#!/usr/bin/env python3
"""Forwarder: the implementation moved to company-ai-skills/lib/gdrive-deliver/.

Drive delivery is company-wide, not Amazon-specific, so the code left this repo
on 12.08.2026. This forwarder keeps every documented command working unchanged:

    python3 tools/gdrive-deliver/deliver.py <file> "<drive folder>" --name "..."

The lib copy's README remains the source of truth for routes, size limits, and
the account check.
"""
import os
import sys
from pathlib import Path

for _candidate in (os.environ.get("EW_COMPANY_LIB", ""),
                   str(Path.home() / "os" / "company-ai-skills" / "lib")):
    if _candidate:
        _target = Path(os.path.expanduser(_candidate)) / "gdrive-deliver" / "deliver.py"
        if _target.is_file():
            os.execv(sys.executable, [sys.executable, str(_target)] + sys.argv[1:])

sys.exit("gdrive-deliver moved to company-ai-skills/lib/gdrive-deliver/ and no "
         "checkout was found (checked $EW_COMPANY_LIB, then "
         "~/os/company-ai-skills/lib). Clone Ecom-Wizards-Agency/"
         "company-ai-skills to ~/os/company-ai-skills or set the env var.")
