---
name: amazon-troubleshooting
description: "Diagnose Amazon errors, suppressions, warnings, permissions, feed failures, missing reports, and blocked workflows before corrective action."
---

# Amazon Troubleshooting

Browser: CDP (wherever the symptom is; capture exact error text).

## Workflow

1. Capture exact error text, page title, account, marketplace, entity IDs, visible warnings, and current filters.
2. Ask the libraries first: `python3 tools/knowledge/ask.py "<exact error text or symptom>"`. It ranks units, our skills, first-party help and MAG SOPs in authority order. Read the top units. When one matches, quote its Answer with its verification label, for example "draft, unverified". Then search first-party Amazon docs with the exact text, then with simplified keywords, then MAG SOPs. [Symptom routing](references/symptom-routing.md) maps each symptom family to its knowledge topic, owning skill and libraries.
3. Identify likely category: permission, eligibility, policy, data delay, file validation, budget, marketplace/account mismatch, catalog contribution conflict, or compliance.
4. Use MAG SOPs for practical UI steps after current Amazon rules are understood. MAG FAQ blocks are unsourced; never quote them as rules.
5. Prepare the next action, support-case draft, or appeal outline. For appeals and defect disputes, follow [the communications appeal-writing posture](../amazon-communications/references/appeal-writing-posture.md).
6. Stop before appeals, acknowledgements, support submissions, account-changing actions, or bulk uploads.

For Account Health rows, open `Review details` when available before summarizing.

A disagreement between a Slack observation, or a unit built from one, and an Amazon page is never resolved silently. Name both sources, apply the authority order in `docs/knowledge-library.md`, and flag it to the operator.
