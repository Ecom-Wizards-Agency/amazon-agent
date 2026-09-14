#!/usr/bin/env python3
"""Forwarder: the implementation moved to company-ai-skills/lib/gdrive-deliver/.

Drive delivery is company-wide, not Amazon-specific, so the code left this repo
on 12.08.2026. This forwarder keeps every documented command working unchanged:

    python3 tools/gdrive-deliver/deliver.py <file> "<drive folder>" --name "..."

The lib copy's README remains the source of truth for routes, size limits, and
the account check.
"""
from forward import main

if __name__ == "__main__":
    raise SystemExit(main("deliver.py"))
