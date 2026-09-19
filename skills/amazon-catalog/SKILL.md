---
name: amazon-catalog
description: "Audit and prepare Amazon catalog changes, including variations, feeds, and Brand Registry conflicts; build and correct Brand Store drafts, product grids, image links and approved artwork."
---

# Amazon Catalog

Browser: Mixed (file builds are local; template downloads/uploads run over CDP; exact approval is required before upload).

## Workflow

1. Identify account, marketplace, ASIN, SKU, parent/child relationship, brand, and contribution source.
2. Search Amazon Seller Help first for current listing rules, error definitions, catalog requirements, and Brand Registry behavior.
3. Search internal notes if the client/workflow has known context.
4. Use MAG catalog SOPs for step-by-step UI or flat-file execution.
5. Decide manual UI vs flat-file vs support case.
6. Preserve current state before edits.
7. Before saving listing changes, deleting/relisting, uploading feeds, or submitting
   support cases, obtain the operator's explicit approval for that exact action and
   reviewed payload in the current chat, or verify a matching scoped permission in
   `_local/local-permissions.md`.
8. Immediately before the approved action, re-verify the account, marketplace, ASINs,
   SKUs, operation, and file or field values. If the final screen changes a material term,
   stop for new approval. After submission, capture the batch or submission identifier
   and verify the processing result per SKU.

## Team Entry Points

For variation and parentage work, load `references/team-catalog-change-workflow.md` and the technical `references/parentage-flatfile-playbook.md`.

- **Start catalog variation change**: gather or discover the account, marketplace, operation, fresh Category Listings Report, fresh single-marketplace blank template, product type, parent/children, theme, customer-facing values, and GTIN/offer details for new children. Create a manifest, then run the change-pack builder.
- **Validate catalog upload file**: run the change-pack validator against the manifest and prepared `.xlsm`. Report every blocking issue before upload.
- **Review processing summary**: run the summary reviewer, explain the verdict per SKU, and state the exact next step and verification gate.

Tool location: `tools/amazon-catalog-change-pack/`.

Every build must produce a scoped change pack under `output/{client}/catalog/{date}-{operation}/`.
Review `02-change-manifest.md` before upload. The current agent may perform the final
submission only after the exact file and operation receive approval under the gate above;
otherwise hand the validated pack to the assigned senior.

Routine titles, bullets, descriptions, images, backend attributes, and normal listing-content edits remain in FlatFilePro. Do not route those through the variation builder.

## Parentage / Variation Flat Files

For creating or editing variation families (parentage) or any targeted flat-file edit, load `references/parentage-flatfile-playbook.md` BEFORE building or reviewing the file. Non-negotiables from live-verified runs:

- Upload base = a fresh **blank template** (single-country, correct browse node), downloaded from the **target seller account itself**. Never reuse another client's template, and never reuse one whose marketplace or product type differs. Verify it before building: the `settings=` string in cell A1 of the `Template` sheet carries `contributorId=amzn1.cr.o.<merchantId>`, and that merchant id must equal the one the account resolves to. A template from another account carries that account's contributor id, preference profile and browse-classification selection, and may ship prefilled data rows belonging to that client. The Category Listings Report is a **data source only**; re-uploading its echoed values fails current-schema validation.
- Parent rows: Full Update, generic title, ALL required attributes filled (Data Definitions sheet), no variation/offer/condition data.
- Child rows: minimal Partial Update (parentage fields + the variation attribute value, nothing else echoed).
- Map template columns by attribute name, never by index; read `dataRow` from the settings cell (it varies by template flavor).
- Read the Feed Processing Summary per SKU; "successful with other errors" = change applied, pre-existing listing issues flagged separately.
- When merging existing ASINs, capture the pre-merge KPI baseline first (see playbook).
- For delete, detach, reparent, and rebuild operations, generate ordered files and enforce a processing/verification gate between file 01 and file 02. Never combine the destructive step with the rebuild.

## Brand Store Updates

Store build/update draft work is enabled for current managed-ready clients. A concrete authenticated team request binds the account, frozen plan and assets and authorizes execution without a second Victor approval. New active/onboarding clients inherit eligibility once identity and connections resolve; pauses, revocations, offboarding and reporting-only restrictions remain effective. Slack requests use `wizards-ai/store_requests.py`; Merlin remains disabled. Submit, schedule and publish remain separate actions.

For Brand Store audits, corrections and builds, load
[references/brand-store-updates.md](references/brand-store-updates.md). For module
selection, Figma translation, crops and mobile composition, also load the team
vault's `Playbooks/amazon-brand-stores-playbook.md`.

- Audit every subpage, including nested and undesigned pages. Distinguish artwork,
  destinations, product selections, stock and catalog relationships.
- For corrections, copy the verified source into a new named draft and change only
  the approved fields. Page rebuilding is a separate operation.
- Verify product identity against the client's assortment, model, pack and variant.
  Brand-picker acceptance and title wording alone do not establish eligibility.
- Reopen changed editors, verify saved values and desktop/mobile results, and
  compare the entire draft and source before reporting success.
- Direct-chat authorization and Slack executor authorization have different
  entry points. Neither changes the requirement for exact scope; submission,
  scheduling and publishing require their own authorization.
