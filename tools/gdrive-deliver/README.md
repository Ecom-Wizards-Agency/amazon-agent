# gdrive-deliver (moved)

The implementation and its full README moved to
`company-ai-skills/lib/gdrive-deliver/` on 12.08.2026: Drive delivery is
company-wide, not Amazon-specific. **That README is the source of truth** for
routes, size limits, the account check, and what survives conversion.

Nothing changes for callers in this repo. `deliver.py`, `update_sheet.py` and
`setup_google.py` here are forwarders that exec the lib copies, so every documented command keeps
working:

```bash
python3 tools/gdrive-deliver/deliver.py <file> "<drive folder>" --name "<delivery filename>"
python3 tools/gdrive-deliver/update_sheet.py <file.xlsx> <sheet id or URL> [--dry-run]   # refresh a delivered Sheet in place
python3 tools/gdrive-deliver/setup_google.py            # one-time setup on a machine
```

The lib is expected at `~/os/company-ai-skills/lib` (override with
`EW_COMPANY_LIB`). If the forwarder cannot find it, it says so and exits
instead of guessing.
