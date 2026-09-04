# Access Preflight

Run this before creating the Day 0 onboarding task. Test capability by opening the required surface in the exact account and marketplace. Do not rely on a client checkbox or a generic permission label.

## Required surfaces

Record one result for each account-marketplace:

1. `account_selector`: select and visibly confirm the correct seller account and marketplace.
2. `account_health`: read Account Health, policy categories, and Performance Notifications.
3. `inventory_settings`: read automated unfulfillable and stranded inventory settings, including the saved return destination.
4. `removal_reports`: read Removal Order Detail and open active order details.
5. `catalog`: read Manage All Inventory, listing status, variations, pricing issues, and Featured Offer state.
6. `brand_registry_analytics`: verify the connected brand, selling role, Brand Analytics, and SQP access where the program is available.
7. `brand_tailored_promotions`: open Brand Tailored Promotions and view live audiences/eligibility.
8. `ads_console`: select the correct advertiser and read campaigns, portfolios, budgets, billing/readiness, and reports.
9. `seller_reporting`: request or read the Seller Central reports needed by the assessment.

`PASS` means the surface was opened and its account/marketplace context was visible. `BLOCKED` includes missing permissions, absent role, unavailable account, login friction, or an ambiguous selector. Use `NOT_APPLICABLE` only when Amazon does not offer the program in that store or the contracted scope explicitly excludes it. Inventory safety surfaces can never be `NOT_APPLICABLE` for an FBA account.

## Conditional blocker task

When every required surface passes, do not create an access task.

When one or more surfaces are blocked, create or update exactly one Notion task:

- Title: `ACCESS BLOCKER - Amazon permissions - {Client} - {Marketplace}`
- Status: `Blocked`
- Priority: `High`; use `Urgent` when inventory-safety or Account Health access is missing.
- Task Type: `Client Success & Strategy`
- Body: account label, marketplace, each missing surface, observed error or absent menu, exact role/permission requested, client action, verification owner, and evidence timestamp.

Do not include Sellerboard, SellerSonar, TrueOps, Drive, Slack, or passwords in this task. Those are integration readiness checks inside the Day 0 assessment. Never request shared credentials; use the client's authorized-partner or individual secondary-user flow.

Stop after creating/updating the blocker. Do not partially run onboarding.
