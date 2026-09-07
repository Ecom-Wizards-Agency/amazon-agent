#!/usr/bin/env python3
"""Forwarder: the implementation lives in company-ai-skills/lib/gdrive-deliver/.

Updating a delivered Google Sheet in place is company-wide, not Amazon-specific,
so it sits next to deliver.py in the lib. This forwarder keeps the documented
command working unchanged from this repo:

    python3 tools/gdrive-deliver/update_sheet.py <file.xlsx> <sheet id or URL> [--dry-run]

The lib copy's README remains the source of truth for what is preserved and
what is not.
"""
from forward import main

if __name__ == "__main__":
    raise SystemExit(main("update_sheet.py"))
