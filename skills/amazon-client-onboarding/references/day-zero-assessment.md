# Day 0 Assessment

Run read-only in each explicitly included marketplace. Reconfirm account, marketplace, page, and filters whenever the surface changes.

## Assessment sequence

### 1. Identity and scope

- Confirm seller and advertiser labels, marketplace, managed brands, managed ASINs/SKUs, fulfillment model, and contracted Amazon scope.
- Compare against the client hub and `Amazon Ops.md`. Surface conflicts instead of silently changing shared facts.

### 2. Account Health and compliance

- Capture overall Account Health state and rating, policy categories, performance notifications, product-safety/recall/required-removal notices, affected ASINs/SKUs, deadlines, and open support cases.
- Capture active, inactive, suppressed, pricing-error, and Featured Offer problem counts.
- Route any deep policy investigation to `amazon-account-health-check` or `amazon-troubleshooting`; do not acknowledge, appeal, reply, or edit.

### 3. Inventory destruction protection

- Capture unfulfillable inventory by ASIN, SKU, FNSKU, quantity, and disposition.
- Capture stranded inventory by ASIN/SKU, reason, quantity, and auto-removal date.
- Read automated unfulfillable and both stranded-removal settings, schedule/age, selected action, and complete visible return destination.
- Review at least 90 days of Removal Order Detail data. Open every Pending, Planning, Processing, In-process, or equivalent active order.
- Reconcile current unfulfillable/stranded quantities against active Return, Disposal, and Liquidation orders.
- Settings changes do not cancel an existing removal order. Treat the removal-order detail page as the status authority.

Mark RED immediately for an active or unauthorized Disposal/Liquidation order, recall-required removal, disabled cancellation on a dangerous order, or material unreconciled inventory. Keep checking read-only to quantify the exposure, then escalate the same day.

### 4. Catalog, offers, and brand readiness

- Check active/inactive/suppressed offers, variation integrity, brand attribution, browse/category issues, price/Featured Offer problems, images, A+ Content, Brand Store, rating, and review baseline.
- Record issues and route repairs to `amazon-catalog`, `amazon-seo`, or `amazon-troubleshooting`. Do not edit listings during onboarding.

### 5. Fulfillment and customer experience

- Map FBA/FBM offers and capture low-stock, aged/excess, reserved, stranded, and inbound-shipment exceptions.
- Review dimension/weight/fee alerts, returns/refunds, and Voice of the Customer signals.
- Establish a baseline only. Hand recurring exceptions to `amazon-operational-checks` and full reshipment planning to `amazon-fba-inventory-planning`.

### 6. Advertising and reporting readiness

- Confirm advertiser selection, billing/readiness, active campaign/portfolio/budget counts, and report availability.
- Confirm Seller Central Business Reports, Brand Analytics/SQP, Sellerboard, SellerSonar, TrueOps, review tracking, internal task routing, and monitoring destinations where in scope.
- Do not perform a deep PPC audit or change campaigns. Create a separate `amazon-audit` or `amazon-ads-console` task when needed.

### 7. Promotions

- Inventory active and scheduled coupons, deals, Prime promotions, Subscribe & Save offers, percentage-off promotions, and Brand Tailored Promotions.
- Read `promotion-plan.md` and stage the 15% all-eligible-audience proposal.

## Result rules

- Every required check must be `PASS`, `WARN`, `FAIL`, `BLOCKED`, or `NOT_APPLICABLE`, with observed value, marketplace, timestamp, and evidence reference.
- `FAIL` or `BLOCKED` on inventory safety, recall/product safety, Account Health, or account identity is RED.
- A noncritical `WARN` must have an owner, due date, and task URL before the assessment can be considered complete.
- Do not report a clean check when the page, data, or alert source was unavailable or stale.
