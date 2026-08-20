# Check Sequence and Policy Issue Deep Dive

## Check Sequence

Step 0 of every run, before any new checks: re-check open findings. Load `{findings_ledger_path}` and the open follow-up tasks it links for in-scope accounts. Every open finding gets re-verified in Seller Central during its account's check and re-disposed (see dispositions-and-ledger.md) - the run starts by answering "what was still open yesterday, and what is its status today?", not by looking for new issues.

Process account-marketplaces by region in this order:

1. Europe accounts first.
2. US accounts second.
3. Any remaining non-Europe, non-US marketplaces last, unless the operator gives a different order.

Within each region, keep a stable marketplace/account order for the run so the ledger and the digest read in a predictable order.

For each account-marketplace:

1. Open `{preferred_browser}` and confirm Seller Central is logged in.
2. Read this account's precomputed Keepa market signals from `{market_signals_state_path}`. They are computed from Keepa before the run starts. Never fetch market signals during the check. Freshness guard: if the file is missing or its `generated_at` is not from today, record that as a blocker, treat market coverage as not performed for this run, and carry on with the rest of the check. An account whose ASINs are not registered for monitoring has no market coverage at all: record that as `not monitored`, which is not the same as clean.

   A fresh file does not mean this account was covered. The sweep is paced against Keepa's refill and carries forward the last observation for anything it did not reach, so `generated_at` can be from today while a given ASIN's record is from yesterday. **Check `observed_at` on the ASIN records themselves**, not just `generated_at` on the file. If an account's records are not from today, it has no market coverage for this run: report it as `not covered`, leave its existing market findings carried forward untouched, and do not re-verify or resolve them. Not covered is not clean.
3. Record the relevant market signals as findings:
   - BSR move, and proximity to the named competitor it is measured against
   - Buy Box / Featured Offer holder change, loss, or a new seller that looks like a hijacker
   - category / browse-node change, and root category change
   - average rating change, or reviews disappearing
   - displayed half-star change, in either direction
   - Buy Box price or offer change
   - FBA or referral fee change
   - package dimension or weight change

   Two of these need a word when you report them. A **root category** change re-benchmarks BSR against a different category, so that ASIN's rank history stops being comparable with itself. Say so rather than reporting the rank move alone. A **displayed half-star** change is the star graphic a shopper sees: Amazon rounds to the nearest half, so 4.2 shows as 4.0 and 4.3 shows as 4.5, and a one-tenth move flips the badge. `rating_display_improved` is the one signal here that is not a problem: dispose it `no_action` and do **not** write it to the ledger, because it is an event rather than a state and would sit open forever.

   No competitor ASINs are registered for any profile, deliberately, so `bsr_competitor_proximity` cannot fire on any account today. Report a BSR figure as unanchored rather than implying nobody is closing on us. Never raise the empty competitor set as a finding or a task because it is the intended state.

   Search-suppressed and inactive listings are not in Keepa. They come from Seller Central in the steps below.
4. Open Seller Central and verify the account by `{seller_central_name_field}` and the country/region by `{marketplace_field}`.
5. Check Account Health:
   - overall status and Account Health Rating
   - Policy Compliance categories and `View all`
   - `Review details` for any nonzero policy row when present
   - affected ASIN/SKU, reason, date, status, deadline, Account Health Rating impact, and next-step labels
6. Check Performance Notifications since the last run.
7. Check order/shipping metrics:
   - ODR, A-to-z, chargebacks
   - cancellation, late shipment, valid tracking, on-time delivery
8. Check homepage action indicators and product/listing health:
   - Actions tab
   - Product Performance status
   - Featured Offer %
   - active/suppressed/inactive/pricing issue states

## Policy Issue Deep Dive

When a new or materially changed Account Health policy issue appears, gather context without taking action:

1. Focus the investigation on one affected ASIN at a time. Copy the affected ASIN, related SKUs, policy issue date, policy type, status, and exact Amazon wording from Account Health.
2. Open Manage Support Cases / Case Log. In Seller Central, the known working route is `/cu/case-lobby` when older case-log URLs fail.
3. Search or scan for cases containing the affected ASIN in the subject or visible case text. Start with cases created on the policy issue date, one day before, and one day after, then extend through today when the issue is still open or when newer follow-up cases reference the same ASIN.
4. Prefer the original policy/suppression case and the most specific operational follow-up case over a broad list of duplicates. Do not list every matching case unless it adds a decision-relevant fact.
5. Open matching support cases read-only. Read the full thread history, including older pages of messages when the case is paginated. Capture:
   - case ID, subject, status, created date, latest Amazon reply date
   - Amazon's root-cause wording and customer-feedback wording, if provided
   - all affected ASINs/variations listed in the case
   - requested documents, images, deadlines, and reply/appeal instructions
   - seller/operator replies already sent and whether they actually answer Amazon's latest request
   - unresolved decision gaps, such as missing batch IDs, missing proof of upload, unclear affected SKUs, missing label images/PDFs, or conflicting Amazon instructions
6. Check Performance Notifications for the same date window if the case log is missing or incomplete.
7. Use exact Amazon wording from the case or policy row to search first-party Seller Help and local SOPs.
8. Summarize the deep dive as an operator decision brief, not a case dump:
   - what Amazon says the problem is
   - which case is the primary thread to continue
   - which secondary case adds a material fact
   - what information is still missing before the operator/operator can decide
   - recommended next action and where to take it, if safe and approved

Do not reply to the case, email Amazon, click `Submit appeal`, acknowledge warnings, upload documents, or edit listings during this check. The goal is to make the issue clear for the operator and prepare the next action, not to resolve it live.
