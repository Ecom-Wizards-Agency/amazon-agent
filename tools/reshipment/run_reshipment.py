#!/usr/bin/env python3
"""Unattended reshipment run for one Seller Central region.

Pulls same-day inventory and demand for every roster account in the region,
plans reshipment against each client's team-vault profile, and posts one thread
to #amazon-check. Deterministic end to end: no model is involved, because every
step here is arithmetic and a model in the loop only adds a way to be creative
about unit counts.

Called by the wizards-ai `reshipment` pass, which owns the schedule, the
freshness guard, the retry budget and the failure alerting. Run it directly for
an attended run:

    tools/reshipment/run_reshipment.py --region us

Read-only against Amazon. It never creates, confirms or modifies a shipment.

Failure policy is skip-and-report: one account that cannot be pulled is named in
the thread and the rest still get planned. Exit is non-zero only when the region
produced nothing at all, which is what tells the caller to retry.
"""
from __future__ import annotations

import argparse
import csv
import datetime
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ROSTER = HERE / "roster.json"
CHANNEL = "C0BAZBZR49E"  # #amazon-check

sys.path.insert(0, str(HERE))
import slack_helper  # noqa: E402

# The FBA snapshot the planner reads. Only these columns are consumed; the live
# GraphQL source has no product-name field, so it is written empty.
FBA_HEADERS = ["asin", "sku", "product-name", "available", "inbound-quantity",
               "Total Reserved Quantity", "FC Transfer", "Customer Order Reserved",
               "FC Processing", "unfulfillable-quantity"]
DEMAND_DAYS = 30


def wizards_config() -> Path:
    """The wizards-ai config holding the Seller Central profiles.

    Same tolerance for the pre-31.07.2026 layout as run.sh and guard.py: this
    repo runs on machines that migrated on different days.
    """
    for candidate in ("~/os/wizards-ai/config.json", "~/Automations/wizards-ai/config.json"):
        path = Path(candidate).expanduser()
        if path.exists():
            return path
    raise SystemExit("wizards-ai config.json not found; cannot resolve Seller Central profiles.")


def provider_script() -> Path:
    """The wizards-inventory provider, at its home in the wizards-ai repo.

    The tool moved from amazon-agent/tools/ into wizards-ai on 12.08.2026
    (0c80813 removed this repo's copy); the last candidate tolerates an old
    checkout that still hosts it, same rollout tolerance as wizards_config().
    """
    for candidate in ("~/os/wizards-ai/tools/wizards-inventory/provider.mjs",
                      "~/Automations/wizards-ai/tools/wizards-inventory/provider.mjs"):
        path = Path(candidate).expanduser()
        if path.exists():
            return path
    legacy = REPO / "tools" / "wizards-inventory" / "provider.mjs"
    if legacy.exists():
        return legacy
    raise SystemExit("wizards-inventory provider.mjs not found; it lives in the wizards-ai repo.")


def provider_config(roster: dict, run_date: str) -> Path:
    """A run-scoped copy of the wizards-ai config with AWD set from the roster.

    AWD is US-only. Rather than trust every profile in the shared config to carry
    the right include_awd flag forever, derive it from the region: a new non-US
    account then cannot be added with AWD left on by accident, which is the
    mistake that silently dropped both non-US accounts on 11.08.2026.
    """
    config = json.loads(wizards_config().read_text(encoding="utf-8"))
    profiles = config.get("inventory_questions", {}).get("profiles", {})
    for account in roster["accounts"]:
        profile = profiles.get(account["profile_key"])
        if profile is not None:
            profile["include_awd"] = bool(roster["regions"][account["region"]]["awd"])
    out = HERE / f".provider-config-{run_date}.json"
    out.write_text(json.dumps(config), encoding="utf-8")
    return out


def run(cmd: list[str], timeout: int = 900, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                          timeout=timeout, env=env)


def last_json(text: str | None) -> dict | None:
    """The provider prints progress lines then one JSON payload. Take the payload."""
    for line in reversed([l for l in (text or "").splitlines() if l.strip()]):
        if line.strip().startswith("{"):
            try:
                return json.loads(line.strip())
            except json.JSONDecodeError:
                continue
    return None


def quantity(value) -> int:
    try:
        return int(round(float(str(value or 0).replace(",", ""))))
    except ValueError:
        return 0


def pull_account(account: dict, region: dict, run_date: str, cdp_env: dict,
                 config_path: Path) -> dict:
    """Same-day inventory + demand for one account. Never raises: returns a blocker."""
    entry = {**{k: account[k] for k in ("key", "profile_key", "brand", "market", "country")},
             "fba": None, "business": None, "blocker": None, "account": None,
             "fba_offer_asins": 0, "business_rows": 0, "business_kept": 0,
             "sold_asins": 0, "recovered_fba_asins": [], "fbm_only_asins": [],
             "unresolved_selling_asins": [], "stock": {}, "awd": None,
             "checked_at": None, "shipments": None, "shipment_warning": None}
    outdir = REPO / "downloads" / account["key"] / "inventory" / run_date
    outdir.mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.datetime.now().astimezone().strftime("%H%M%S%f")
    provider_cfg = json.loads(config_path.read_text(encoding="utf-8"))
    provider_profile = ((provider_cfg.get("inventory_questions") or {}).get("profiles") or {}).get(
        account["profile_key"], {})

    proc = None
    payload = None
    for _attempt in range(3):
        try:
            proc = run(["node", str(provider_script()),
                        "--config", str(config_path),
                        "--profile", account["profile_key"], "--all-skus"], timeout=900)
        except subprocess.TimeoutExpired:
            continue
        payload = last_json(proc.stdout) or last_json(proc.stderr)
        skus = ((payload or {}).get("fba") or {}).get("skus") or []
        if payload and (payload.get("status") in ("complete", "selected") or skus):
            break
        if "authentication requires recovery" in str((payload or {}).get("error", "")).lower():
            break
    if proc is None:
        entry["blocker"] = "inventory read timed out"
        return entry

    # "partial" means an optional sub-source was unavailable (AWD outside the US)
    # while the FBA read itself succeeded. Only a missing FBA read is a blocker.
    skus = ((payload or {}).get("fba") or {}).get("skus") or []
    if not payload or (payload.get("status") not in ("complete", "selected") and not skus):
        entry["blocker"] = ((payload or {}).get("error")
                            or f"inventory read returned status="
                               f"{(payload or {}).get('status')} rc={proc.returncode}")
        return entry

    fba = payload.get("fba") or {}
    entry["account"] = f"{payload.get('account')} / {payload.get('marketplace')}"
    entry["checked_at"] = payload.get("checked_at")
    entry["stock"] = {k: fba.get(k) for k in
                      ("available", "inbound", "unfulfillable", "researching", "stored")}
    entry["stock"]["reserved_total"] = (fba.get("reserved") or {}).get("total")
    entry["stock"]["awd_buyable_in_transit_signal"] = fba.get(
        "awd_buyable_in_transit_signal", 0)
    entry["awd"] = payload.get("awd")
    if region.get("awd") and entry["awd"] is None:
        detail = "; ".join(payload.get("warnings") or []) or "AWD returned no result"
        entry["blocker"] = f"AWD could not be verified: {detail}"
        return entry

    # Demand must come only from ASINs that actually hold an FBA offer. Without
    # this a child selling well on an FBM offer gets a restock recommendation on
    # sales alone: on 11.08.2026 that produced 10,899 phantom units for two
    # AlphaInfuse children that have no FBA offer at all.
    offer_asins = {s.get("asin") for s in skus if s.get("fba_offer") and s.get("asin")}

    end = datetime.date.fromisoformat(run_date)
    start = end - datetime.timedelta(days=DEMAND_DAYS - 1)
    raw = outdir / f"business-raw-rerun-{run_stamp}.csv"
    # Only a profile-pinned seller id is suitable for mons_sel_dir_mcid. The
    # live GraphQL context can expose the delegated partner id when a profile
    # has no seller id (tmrw did this on 01.09.2026); using that as the merchant
    # id makes Report Fetcher select the wrong session context. Name-based
    # switching remains fail-closed and is the correct fallback.
    seller_id = provider_profile.get("seller_id")
    expected_account = seller_id or payload.get("account") or provider_profile.get("account_name")
    report_cmd = ["node", "tools/report-fetcher/run.mjs", "business",
                  "--start", start.isoformat(), "--end", end.isoformat(),
                  "--marketplace", region["marketplace"], "--out", str(raw),
                  "--expect-account", expected_account]
    if seller_id:
        report_cmd.extend(["--account", seller_id])
    if provider_profile.get("account_name") and provider_profile.get("marketplace_label"):
        report_cmd.extend(["--account-name", provider_profile["account_name"],
                           "--marketplace-label", provider_profile["marketplace_label"]])
    if provider_profile.get("parent_account_name"):
        report_cmd.extend(["--parent-account-name", provider_profile["parent_account_name"]])
    proc = None
    for _attempt in range(3):
        raw.unlink(missing_ok=True)
        try:
            proc = run(report_cmd, timeout=900, env_extra=cdp_env)
        except subprocess.TimeoutExpired:
            continue
        if proc.returncode == 0 and raw.exists() and raw.stat().st_size > 0:
            break
    if proc is None:
        entry["blocker"] = "business report timed out"
        return entry
    if proc.returncode != 0 or not raw.exists() or raw.stat().st_size == 0:
        tail = [l for l in (proc.stdout + proc.stderr).strip().splitlines() if l.strip()]
        entry["blocker"] = "business report: " + (tail[-1][:120] if tail else "no output")
        return entry

    with raw.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    entry["business_rows"] = len(rows)
    header = list(rows[0].keys()) if rows else []
    asin_col = (next((c for c in header if "Child" in c and "ASIN" in c), None)
                or next((c for c in header if "ASIN" in c), None))
    units_col = (next((c for c in header if c.strip() == "Units Ordered"), None)
                 or next((c for c in header if "Units Ordered" in c), None))
    if not asin_col or not units_col:
        entry["blocker"] = "business report lacks the child-ASIN or Units Ordered column"
        return entry

    sold_asins = {r.get(asin_col) for r in rows
                  if r.get(asin_col) and quantity(r.get(units_col)) > 0}
    entry["sold_asins"] = len(sold_asins)
    missing_sold = sorted(sold_asins - offer_asins)
    fbm_only = set()
    recovered_asins = set()
    unresolved = set()
    if missing_sold:
        # Exact-ASIN search is the mandatory recovery/classification step for
        # sellers absent from the page sweep. Run it in bounded batches so a
        # large hybrid FBA/FBM catalog does not exceed command-line limits.
        for offset in range(0, len(missing_sold), 40):
            batch = missing_sold[offset:offset + 40]
            search_payload = None
            search_proc = None
            for _attempt in range(3):
                try:
                    search_proc = run(["node", str(provider_script()),
                                       "--config", str(config_path),
                                       "--profile", account["profile_key"],
                                       "--search-terms", ",".join(batch)], timeout=900)
                except subprocess.TimeoutExpired:
                    continue
                search_payload = last_json(search_proc.stdout) or last_json(search_proc.stderr)
                if search_proc.returncode == 0 and (search_payload or {}).get("status") == "complete":
                    break
            if search_proc is None or search_proc.returncode != 0 or (search_payload or {}).get("status") != "complete":
                entry["blocker"] = (f"exact-ASIN verification failed at batch {offset // 40 + 1}: "
                                    f"{(search_payload or {}).get('error') or getattr(search_proc, 'returncode', 'timeout')}")
                return entry
            for search in search_payload.get("searches") or []:
                term = search.get("term")
                exact_rows = search.get("rows") or []
                fba_rows = [row for row in exact_rows if row.get("fba_offer")]
                if fba_rows:
                    recovered_asins.add(term)
                    skus.extend(fba_rows)
                elif exact_rows:
                    fbm_only.add(term)
                else:
                    unresolved.add(term)

    # De-duplicate recovered and sweep rows without collapsing separate SKUs for
    # the same ASIN. Multiple AFN offers must all contribute to stock.
    unique_skus = []
    seen_skus = set()
    for sku in skus:
        signature = (sku.get("seller_sku"), sku.get("asin"), bool(sku.get("fba_offer")))
        if signature in seen_skus:
            continue
        seen_skus.add(signature)
        unique_skus.append(sku)
    skus = unique_skus
    offer_asins = {s.get("asin") for s in skus if s.get("fba_offer") and s.get("asin")}
    unresolved.update(sold_asins - offer_asins - fbm_only)
    entry["fba_offer_asins"] = len(offer_asins)
    entry["recovered_fba_asins"] = sorted(recovered_asins)
    entry["fbm_only_asins"] = sorted(fbm_only)
    entry["unresolved_selling_asins"] = sorted(unresolved)

    reconciliation_path = outdir / f"selling-asin-reconciliation-rerun-{run_stamp}.json"
    reconciliation_path.write_text(json.dumps({
        "account": entry["account"], "checked_at": entry["checked_at"],
        "business_rows": len(rows), "selling_asins": sorted(sold_asins),
        "fba_offer_asins": sorted(offer_asins),
        "recovered_fba_asins": sorted(recovered_asins),
        "verified_fbm_only_asins": sorted(fbm_only),
        "unresolved_selling_asins": sorted(unresolved),
    }, indent=2) + "\n", encoding="utf-8")
    if unresolved:
        entry["blocker"] = (f"{len(unresolved)} selling ASIN(s) remain unexplained after exact search; "
                            f"see {reconciliation_path.name}")
        return entry

    fba_path = outdir / f"fba-live-rerun-{run_stamp}.csv"
    with fba_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FBA_HEADERS)
        writer.writeheader()
        for sku in skus:
            if not sku.get("fba_offer"):
                continue
            writer.writerow({"asin": sku.get("asin"), "sku": sku.get("seller_sku"),
                             "product-name": "", "available": sku.get("available", 0),
                             "inbound-quantity": sku.get("inbound", 0),
                             "Total Reserved Quantity": sku.get("reserved", 0),
                             "FC Transfer": sku.get("reserved_fc_transfer", 0),
                             "Customer Order Reserved": sku.get("reserved_customer_order", 0),
                             "FC Processing": sku.get("reserved_fc_processing", 0),
                             "unfulfillable-quantity": sku.get("unfulfillable", 0)})
    entry["fba"] = str(fba_path)

    kept = [r for r in rows if asin_col and r.get(asin_col) in offer_asins]
    entry["business_kept"] = len(kept)
    if not kept:
        entry["blocker"] = (f"business report has no rows for the {len(offer_asins)} "
                            f"FBA-offer ASIN(s), so demand cannot be measured")
        return entry

    business = outdir / f"business-rerun-{run_stamp}.csv"
    with business.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=header)
        writer.writeheader()
        writer.writerows(kept)
    entry["business"] = str(business)

    shipment_skus = sorted({
        str(sku.get("seller_sku") or "").strip()
        for sku in skus if sku.get("fba_offer") and sku.get("seller_sku")
    } - {""})
    if shipment_skus:
        # Reconcile the queue against the full FBA catalog recovered in this
        # run, not a stale hand-maintained shipment group. This run-scoped
        # config is private and disposable; the stable profile is untouched.
        run_group = "__run_catalog"
        profile_for_run = ((provider_cfg.get("inventory_questions") or {})
                           .get("profiles") or {}).get(account["profile_key"], {})
        profile_for_run.setdefault("shipment_groups", {})[run_group] = {
            "skus": shipment_skus
        }
        config_path.write_text(json.dumps(provider_cfg), encoding="utf-8")
        try:
            shipment_proc = run(["node", str(provider_script()),
                                 "--config", str(config_path),
                                 "--profile", account["profile_key"],
                                 "--shipment-group", run_group,
                                 "--shipment-since", run_date], timeout=900)
            shipment_payload = last_json(shipment_proc.stdout) or last_json(shipment_proc.stderr)
        except subprocess.TimeoutExpired:
            shipment_payload = None
        shipment_evidence = outdir / f"shipment-reconciliation-rerun-{run_stamp}.json"
        shipment_evidence.write_text(json.dumps(shipment_payload or {
            "status": "error", "error": "shipment reconciliation timed out"
        }, indent=2) + "\n", encoding="utf-8")
        entry["shipments"] = (shipment_payload or {}).get("shipments")
        if not shipment_payload or not entry["shipments"] or not entry["shipments"].get("queue"):
            entry["shipment_warning"] = ("open-shipment reconciliation is unverified; "
                                         f"see {shipment_evidence.name}")
    else:
        entry["shipment_warning"] = "no FBA SKU was available for shipment reconciliation"

    (outdir / f"pull-entry-rerun-{run_stamp}.json").write_text(
        json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    return entry


def source_note(entry: dict, start: str, end: str) -> str:
    awd = entry.get("awd")
    if awd is None:
        awd_note = "AWD is not offered in this marketplace."
    elif (awd.get("stored") or 0) or (awd.get("available") or 0):
        awd_note = f"AWD holds {awd.get('stored') or awd.get('available')} unit(s)."
    else:
        awd_note = "AWD queried and holds nothing."
    return (f"Same-day read-only Manage Products per-SKU read and Business Report "
            f"{start}..{end} through the Wizards AI service account. Demand restricted to "
            f"ASINs holding a verified FBA offer ({entry['business_kept']}/"
            f"{entry['business_rows']} rows kept, {entry['fba_offer_asins']} FBA-offer "
            f"ASIN(s), {len(entry['recovered_fba_asins'])} recovered by exact search, "
            f"{len(entry['fbm_only_asins'])} verified FBM-only). Inventory checked "
            f"{entry['checked_at']}. {awd_note}"
            + (f" {entry['shipment_warning']}" if entry.get("shipment_warning") else ""))


def plan(entries: list[dict], run_date: str, start: str, end: str) -> list[dict]:
    """Run the planner over the accounts that pulled cleanly. Returns manifests."""
    planned = [e for e in entries if e["fba"] and e["business"]]
    if not planned:
        return []
    config = {
        "run_date": run_date,
        "report_days": DEMAND_DAYS,
        "downloads_dir": str(REPO / "downloads"),
        "output_root": str(REPO),
        "clients": [{
            "key": e["key"], "profile_key": e["profile_key"], "brand": e["brand"],
            "market": e["market"], "country": e["country"],
            "fba": e["fba"], "business": e["business"],
            "inventory": None, "restock": None, "restock_country": None,
            # AWD stock counts against send quantities. by_sku is subtracted
            # per product; a stored total without attribution becomes a loud
            # planner warning instead of a silent overshoot.
            "awd_by_key": (e.get("awd") or {}).get("by_sku") or None,
            "awd_stored": (e.get("awd") or {}).get("stored") or 0,
            "notes": source_note(e, start, end),
        } for e in planned],
    }
    config_path = HERE / f"config.run-{run_date}.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    proc = run(["python3", str(HERE / "generate_reshipment.py"),
                "--config", str(config_path)], timeout=900)
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()
        raise SystemExit("planner failed: " + (tail[-1] if tail else "no output"))

    manifests = []
    for e in planned:
        stem = f"{run_date}_Inventory Overview_{e['brand']}_{e['market']}"
        path = REPO / "output" / e["key"] / "inventory" / f"{stem}_manifest.json"
        if not path.exists():
            e["blocker"] = "planner wrote no manifest"
            continue
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(manifest, list):
            manifest = manifest[0]
        manifest["_entry"] = e
        manifest["_slack"] = (REPO / "output" / e["key"] / "inventory" / f"{stem}_slack.txt")
        manifests.append(manifest)
    return manifests


def post(region_label: str, manifests: list[dict], blocked: list[dict], run_date: str) -> str:
    """One thread per region run. The parent is what the freshness guard claims on."""
    stamp = datetime.date.fromisoformat(run_date).strftime("%d.%m.%Y")
    sending = [m for m in manifests if m["sendUnits"] > 0]
    quiet = [m for m in manifests if m["sendUnits"] == 0]
    units = sum(m["sendUnits"] for m in sending)

    # Exceptions-only thread (operator decision, 13.08.2026): the parent carries
    # the all-clear as a compact count, and only accounts that actually need
    # units or are blocked earn a reply. Per-account "No reshipment needed"
    # lists and the repeated methodology block were noise the reader had to
    # scroll past to find the exceptions.
    parent = (f"*Reshipment Plan ({region_label}) {stamp}* · {len(manifests)} planned · "
              f"{units:,} unit(s) to send")
    if quiet:
        parent += f" · {len(quiet)} need nothing"
    if blocked:
        parent += f" · {len(blocked)} blocked"
    result = json.loads(slack_helper.run_helper("post", CHANNEL, parent))
    thread = result["ts"]

    for m in sending:
        body = m["_slack"].read_text(encoding="utf-8") if m["_slack"].exists() else ""
        detail = body.split("\n\n*Reshipment*\n", 1)[1] if "\n\n*Reshipment*\n" in body else ""
        entry = m["_entry"]
        slack_helper.run_helper("post", CHANNEL, (
            f"*{entry['brand']} {entry['market']}* · {m['sendUnits']:,} unit(s) · "
            f"{m['effectiveCoverageDays']}d coverage\n{detail}").strip(), thread)

    if blocked:
        slack_helper.run_helper("post", CHANNEL, "*Not planned this run*\n" + "\n".join(
            f"• {b['brand']} {b['market']} · {b['blocker']}" for b in blocked), thread)

    return json.loads(slack_helper.run_helper("permalink", CHANNEL, thread))["permalink"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", required=True)
    parser.add_argument("--date", default=datetime.date.today().isoformat())
    parser.add_argument("--account-key", action="append",
                        help="Limit the run to one or more roster account keys")
    parser.add_argument("--dry-run", action="store_true",
                        help="pull and plan, print the result, post nothing")
    args = parser.parse_args()

    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    if args.region not in roster["regions"]:
        raise SystemExit(f"unknown region {args.region}; "
                         f"known: {', '.join(roster['regions'])}")
    region = roster["regions"][args.region]
    accounts = [a for a in roster["accounts"] if a["region"] == args.region]
    if args.account_key:
        requested = set(args.account_key)
        known = {a["key"] for a in accounts}
        unknown = sorted(requested - known)
        if unknown:
            raise SystemExit(f"account key(s) not in region {args.region}: {', '.join(unknown)}")
        accounts = [a for a in accounts if a["key"] in requested]
    if not accounts:
        print(f"no accounts in region {args.region}")
        return 0

    end = datetime.date.fromisoformat(args.date)
    start = (end - datetime.timedelta(days=DEMAND_DAYS - 1)).isoformat()
    cdp_env = {"CDP_PORT": os.environ.get("CDP_PORT", "9223"),
               "CDP_PROFILE": os.environ.get(
                   "CDP_PROFILE", str(Path.home() / ".amazon-agent/wizards-ai-chrome"))}

    config_path = provider_config(roster, args.date)
    entries = []
    for account in accounts:
        entry = pull_account(account, region, args.date, cdp_env, config_path)
        state = entry["blocker"] or (f"{entry['fba_offer_asins']} FBA-offer ASIN(s), "
                                     f"{entry['business_kept']}/{entry['business_rows']} rows")
        print(f"{entry['key']:18} {state}", flush=True)
        entries.append(entry)

    manifests = plan(entries, args.date, start, args.date)
    blocked = [e for e in entries if e["blocker"]]

    if not manifests:
        print(f"region {args.region}: nothing planned; {len(blocked)} blocked")
        return 1

    if args.dry_run:
        for m in manifests:
            print(f"  {m['_entry']['brand']:14} send={m['sendUnits']:>6} "
                  f"excess={m['excessUnits']:>6} coverage={m['effectiveCoverageDays']}d")
        print(f"(dry run: nothing posted; {len(blocked)} blocked)")
        return 0

    print(post(region["label"], manifests, blocked, args.date))
    return 0


if __name__ == "__main__":
    sys.exit(main())
