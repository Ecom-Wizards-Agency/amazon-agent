# gdrive-deliver (moved)

The implementation and its full README moved to
`company-ai-skills/lib/gdrive-deliver/` on 12.08.2026: Drive delivery is
company-wide, not Amazon-specific. **That README is the source of truth** for
routes, size limits, the account check, and what survives conversion.

`deliver.py`, `update_sheet.py` and `setup_google.py` forward to the lib copies,
so existing delivery commands keep working:

```bash
python3 tools/gdrive-deliver/deliver.py <file> "<drive folder>" --name "<delivery filename>"
python3 tools/gdrive-deliver/update_sheet.py <file.xlsx> <sheet id or URL> [--dry-run]   # refresh a delivered Sheet in place
python3 tools/gdrive-deliver/setup_google.py            # one-time setup on a machine
```

The lib is expected at `~/os/company-ai-skills/lib` (override with
`EW_COMPANY_LIB`). If the forwarder cannot find it, it says so and exits
instead of guessing.

The delivery wrappers own `--artifact-run <run-id>` (also accepted as
`--artifact-run=<run-id>`). They request a fresh receipt from the company helper,
verify the native file metadata and unchanged source checksum, then call this
repository's artifactctl registration command. A supplied `--receipt-file` still
receives the new helper receipt. Missing, invalid or unverified receipts and
failed helpers never register an artifact. Dry runs never register or write a
receipt. Registration failure reports the failure and retains the local file;
these wrappers never quarantine or delete artifacts.

Without `--artifact-run`, arguments and process execution pass through unchanged.
Company helpers do not depend on Amazon code. Run their direct commands when
Amazon artifact registration is unnecessary.

Offline verification: run `python3 -m unittest discover -s tools/gdrive-deliver`.
Set `EW_COMPANY_LIB` to the release candidate's library to also check its real
receipt builders against the wrapper and artifactctl verification contracts.
