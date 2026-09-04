#!/usr/bin/env python3
"""Forwarder: the implementation lives in company-ai-skills/lib/gdrive-deliver/.

Updating a delivered Google Sheet in place is company-wide, not Amazon-specific,
so it sits next to deliver.py in the lib. This forwarder keeps the documented
command working unchanged from this repo:

    python3 tools/gdrive-deliver/update_sheet.py <file.xlsx> <sheet id or URL> [--dry-run]

The lib copy's README remains the source of truth for what is preserved and
what is not.
"""
import os
import sys
from pathlib import Path

for _candidate in (os.environ.get("EW_COMPANY_LIB", ""),
                   str(Path.home() / "os" / "company-ai-skills" / "lib")):
    if _candidate:
        _target = Path(os.path.expanduser(_candidate)) / "gdrive-deliver" / "update_sheet.py"
        if _target.is_file():
            os.execv(sys.executable, [sys.executable, str(_target)] + sys.argv[1:])

sys.exit("gdrive-deliver lives in company-ai-skills/lib/gdrive-deliver/ and no "
         "checkout was found (checked $EW_COMPANY_LIB, then "
         "~/os/company-ai-skills/lib). Clone Ecom-Wizards-Agency/"
         "company-ai-skills to ~/os/company-ai-skills or set the env var.")
