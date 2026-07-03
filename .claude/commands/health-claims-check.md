---
description: Run a SAS-style health-claims self-check on a listing — per-claim risk table + RJ-preserving rewrites + authorised claims to add (internal by default)
argument-hint: "[client + marketplace + ASIN/listing URL, workbook path, or pasted copy]"
---

# Health Claims Check

Audit a listing's copy for health-claim compliance the way Amazon SAS does, without losing Ranking Juice. Do not duplicate logic here — route into the `amazon-seo` skill with `references/health-claims-compliance.md` as source of truth (EU law detail: `references/eu-compliance-matrix.md`).

The user's target is: **$ARGUMENTS**

## Steps

1. **Load `skills/amazon-seo/references/health-claims-compliance.md`.** Determine the category tier (regulated vs standard), marketplace regime (EU vs US), and the client's risk posture (workbook `compliance` block or ask briefly).

2. **Get the listing copy** — live via the `amazon-listing-capture` extractor (connected browser), from the keyword workbook's SEO Text tab, or from pasted text. Also pull the actual product facts (ingredients, per-serving values) — nutrition-claim thresholds are arithmetic and must be computed, not guessed.

3. **Walk every discrete claim** in title / Item Highlights / bullets / description / backend: classify (claim type → register/policy check → status → LOW/MEDIUM/HIGH), including the word-level red flags (bioactive-style adjectives, highlighted ingredients with rejected claims, "only"+number, "natural"+synthetics, purity wording, stronger-than-authorised wording).

4. **Propose RJ-preserving rewrites via the ladder** (strip effect keep tokens → authorised-wording swap → ADD authorised register claims the product qualifies for → backend/PPC routing → drop last). Every HIGH/MEDIUM finding gets a rewrite proposal, never a bare deletion. Include the "authorised claims to add" section for regulated-tier products.

5. **Save + report**: findings table + priority actions + overall risk to `output/<client>/seo/claims-check-<asin>-<date>.md` (with the not-legal-advice disclaimer); update the workbook config (`compliance.claims_audit`, `compliance.checked`, `triage.claim_tokens`) when a workbook exists. **Internal output only** — never prepare or send a client-facing version unless the operator explicitly requests it in the current chat; applying any copy change to a live listing stays a separate operator-confirmed action.
