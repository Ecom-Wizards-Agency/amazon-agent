# Branding, delivery, and QA

## Branding ownership

The workflow brand contract overrides generic document and spreadsheet defaults. Use:

- agency identity: `_local/branding/branding.json` or the explicit approved run-config path;
- binary assets: the approved `tools/amazon-ad-audit/brand/` directory or explicit equivalent;
- document renderer: `tools/amazon-ad-audit/render_branded.py`;
- workbook styling: `tools/amazon-ad-audit/branding.py` and `ew_audit_style.py`;
- document label: `Amazon Account Handover`;
- cover: off.

No cover means no standalone cover page. It does not remove the branded header, footer, logo, typography, palette, KPI treatment, or workbook styling.

The builder intentionally fails before rendering when approved branding is missing. Do not bypass this by pointing it to an example or allowing the neutral renderer fallback.

## Local QA

Before delivery, confirm:

- title, client, cutoff, successor, audience, and included markets are correct;
- excluded markets appear nowhere in the Doc or workbook;
- every material number has source refs and an extraction timestamp;
- comparison windows have equal inclusive day counts;
- recent changes are provisional and have review dates;
- no profitability or Required RPC appears for unverified economics;
- the complete latest material advertising change is in the Doc;
- the Doc includes engagement delivery, creative/POE reuse guidance, open items, and verified client links;
- the workbook has exactly five tabs and no `#REF!`;
- RPC, ACOS, and Required RPC formulas match a manual spot check;
- header logo, footer, typography, tables, page flow, and final page are visually clean;
- there is no cover and no stranded final page;
- filenames follow `YYYY-MM-DD_Client_Markets_Artifact_vN`.

Use the document and spreadsheet inspection tools available in the environment. If a visual renderer is available, render the DOCX and inspect every page. If not, inspect the package structure and perform final visual QA in the converted native Google Doc before exposing it to the client.

## Native Google delivery

Deliver only after local validation:

```bash
python3 tools/amazon-client-offboarding/build_handover.py \
  --config <run-config.json> \
  --deliver
```

The builder calls `tools/gdrive-deliver/deliver.py` for DOCX to Google Doc and XLSX to Google Sheet conversion. It never creates the destination. Do not use `--keep-upload` for the Office intermediaries.

Verify the returned native files open with client permissions and preserve branding, formulas, tab names, live page fields, and links. Record the native URLs in the run note. Do not send them unless the user separately authorizes communication.
