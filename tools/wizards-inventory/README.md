# Wizards AI inventory provider

Read-only Seller Central provider for Wizards AI inventory questions. It drives a dedicated Chrome profile over localhost CDP. Wizards AI runs that profile headless in normal operation and switches the same profile to visible recovery mode when an operator must restore the Amazon session. It never reads or exports cookies, passwords, MFA codes, or browser storage.

```bash
node tools/wizards-inventory/provider.mjs \
  --config ~/os/wizards-ai/config.json \
  --profile sondur-us \
  --audit-dir ~/os/wizards-ai/mentions/inventory-audit
```

Use `--shipment-group <configured-key>` only for an explicit shipment-status question. Use `--select-only` to verify account selection without querying stock or shipments.

The provider selects and verifies the configured seller and marketplace before querying. FBA comes from the read-only Manage Products GraphQL query. AWD comes from the read-only AWD Inventory Ledger report and is explicitly marked as delayed by 24 hours. When a configured shipment group is requested, the provider also reads Shipping Queue and shipment contents without submitting any shipment action. JSON audits are retained for 14 days.

The service account is least privilege, not literally View-only in SPP. Amazon exposes Manage Products and FBA shipment reads through two Edit-only rows, so SPP grants Edit on `Manage Inventory/Add a Product` and `Manage FBA Inventory/Shipments` in addition to Reports Edit. Runtime policy remains strictly read-only. Never create, confirm, reconcile, cancel, or modify a shipment. The existing `view-only` authentication-policy identifiers remain unchanged because they name this runtime boundary.

Browser controls for the Wizards AI profile:

```bash
CDP_PORT=9223 CDP_PROFILE=~/.amazon-agent/wizards-ai-chrome \
  tools/report-fetcher/launch-chrome-debug.sh --mode headless

CDP_PORT=9223 CDP_PROFILE=~/.amazon-agent/wizards-ai-chrome \
  tools/report-fetcher/launch-chrome-debug.sh --mode recovery

CDP_PORT=9223 CDP_PROFILE=~/.amazon-agent/wizards-ai-chrome \
  tools/report-fetcher/launch-chrome-debug.sh --mode stop
```

The launcher records the managed browser PID and mode inside the dedicated profile, refuses ambiguous profile switching, binds the debugging interface explicitly to `127.0.0.1`, and restricts the profile directory to its owner. Recovery mode stops the managed headless process before opening a visible window. Headless mode performs the reverse transition after login.

Authentication states are returned as structured, non-secret statuses: `login_required`, `password_required`, `totp_required`, and `human_challenge`. Authentication failures never create screenshots. Automated password/TOTP completion remains disabled by default. It can be enabled only for the separate least-privilege Amazon service account after the Wizards AI config passes the scoped 1Password service-account checks. CAPTCHA, device approval, recovery, identity verification, and all port-9222 authentication remain human-only.
