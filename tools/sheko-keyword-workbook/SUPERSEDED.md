# ⛔ SUPERSEDED — do not use

This directory was the original **Sheko-specific** keyword-workbook builder. It
has been replaced by the **client-agnostic** successor:

➡️ **`tools/amazon-seo-keyword-workbook/`** (+ the `amazon-seo-keyword-workflow` skill)

The successor generalizes everything here and adds: Core 30% + Expanded 1% MKL,
Never-Ever generation from the 1% file, POE Reviews/Returns/Semantic parsed from
JSON, DataDive export-metadata QA, and a stale-data guard. It is driven entirely
by a per-client config (`config.TEMPLATE.json` → `config.<client>-<product>-<market>.json`;
see that tool's `NEW-CLIENT.md`).

Kept for history only. The delivered client artifacts it produced
(`output/sheko/seo/…v3.xlsx` and the Italy v1) remain valid. Do not run this
builder for new work; use the successor.
