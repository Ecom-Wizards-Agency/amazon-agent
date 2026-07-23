---
name: amazon-regulated-product-suppression-appeals
description: Build evidence-controlled Amazon appeal packs for serious regulated-product suppressions involving supplements, cosmetics, OTC or drug classification, medical-device classification, restricted products, packaging, labeling, manuals, unsupported claims, repeated denials, or coordinated catalog corrections. Use when a normal support reply is insufficient and the case needs declarations, technical evidence, catalog-processing proof, corrective actions, preventative controls, training, and Victor's final troubleshooting signoff.
---

# Amazon Regulated Product Suppression Appeals

Browser: Mixed (first-party policy research and catalog verification may use Chrome; pack creation and validation are local).

## Activation Boundary

Use this skill when at least one of these conditions applies:

- Amazon cites a regulated-product, FDA, drug, supplement, device, labeling, packaging, or restricted-claims concern.
- Amazon requests technical, manufacturing, testing, packaging, manual, or exemption evidence.
- An appeal was denied or standard support channels did not resolve the suppression.
- Multiple ASINs, SKUs, variations, or catalog surfaces must be reconciled.
- The appeal must prove corrective actions and durable preventative controls.

Keep routine listing errors, isolated catalog defects, and ordinary support replies in `amazon-troubleshooting`, `amazon-catalog`, or `amazon-communications`.

## Non-Negotiable Rules

- Diagnose from Amazon's exact notice. Do not assume the category or regulatory path.
- Use current first-party Amazon material for Amazon requirements. Use current regulator or authoritative source material for legal or regulatory facts.
- Never fabricate a Drug Facts panel, Supplement Facts panel, exemption, clearance, registration, test result, manufacturer relationship, certificate, signature, or regulatory conclusion.
- Distinguish seller assertions, manufacturer declarations, independent evidence, and Amazon processing records.
- Do not describe a catalog file as processed without a successful processing summary. Do not describe a correction as verified without checking the resulting catalog.
- Stop as `Evidence incomplete` when a material assertion lacks support.
- Victor is the required final troubleshooting approver unless he explicitly delegates the case.
- Uploading a catalog file, submitting an appeal, or changing a listing remains a separate approval-gated action.

## Workflow

1. Read `references/intake-contract.md` and collect the case record.
2. Read `references/module-selection.md` and select only the modules justified by the issue.
3. Build the claim-to-evidence register before drafting conclusions.
4. Review the complete product family and all seller-controlled surfaces:
   - title, bullets, description, Item Highlights
   - images, A+ Content, video
   - search terms, intended use, directions, benefits, and other backend attributes
   - packaging, labels, manuals, inserts, and QR-linked content
5. Route catalog correction work to `amazon-catalog` or `amazon-flatfilepro-compliance`. Route case wording to `amazon-communications`.
6. Generate the selected documents as DOCX masters and PDF attachment copies.
7. Validate the pack with:

```bash
python3 tools/regulated-suppression-appeal-pack/appeal_pack.py validate \
  --pack-dir "output/{client}/support-prep/{date}-{case-slug}"
```

8. Read `references/quality-gates.md`. Resolve every error before setting `Victor signoff required`.
9. Present Victor with the appeal, evidence index, unresolved-risk summary, and validation report.
10. Set `Approved for manual submission` only after Victor's recorded approval.

## Pack Contract

Every full pack uses these numbered modules:

```text
01-appeal
02-technical-evidence-and-claim-register
03-manufacturer-declaration
04-catalog-correction-and-processing-proof
05-compliance-sop
06-training-guide
07-manual-review
08-packaging-and-label-review
09-evidence-index
10-submission-checklist
```

Copy `tools/regulated-suppression-appeal-pack/manifest.TEMPLATE.json`, complete the intake, and use `appeal_pack.py scaffold` to create the controlled local structure. Client outputs belong under `output/{client}/support-prep/`.

## Status Model

Use exactly one status:

- `Draft`
- `Evidence incomplete`
- `Senior review ready`
- `Victor signoff required`
- `Approved for manual submission`

The validator must pass before the final two statuses. Victor's recorded approval is required for the final status.

## References

- Required intake and manifest fields: `references/intake-contract.md`
- Category and issue module selection: `references/module-selection.md`
- Submission quality gates: `references/quality-gates.md`
- Machine-readable manifest contract: `references/case-manifest.schema.json`

The sanitized DOCX and PDF reference library lives in the shared pCloud Amazon Agent folder under `Appeal Pack Templates/Regulated Product Suppressions/`.
