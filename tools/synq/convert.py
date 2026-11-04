#!/usr/bin/env python3
"""Saved SYNQ MCP responses -> the files the SUPA builder and the ads monitor already read.

Inputs are saved responses, never live calls. Each input file is one of:
  - a JSON list of rows (a response saved without its note),
  - the save wrapper {"note": <note text or null>, "rows": [...]},
  - the raw MCP text: an optional "NOTE ..." block followed by the JSON list.

Subcommands:
  sqp           get_sqp_data per-ASIN WEEK rows -> DIR/sqp_<period_start>.csv (SUPA SQP columns)
  search-terms  get_search_terms rows -> DIR/search_terms_<week_start>.csv (SUPA PPC) and
                DIR/searchterms_weekly_<week_end>.json (ads-monitor search-term rows)
  stock         get_inventory history rows -> DIR/stock_<week_start>.csv (asin,out_of_stock_days)
  entities      get_metrics or get_daily_metrics rows + list_campaigns (+ get_search_terms for
                match type) -> run_weekly.py entity rows. A --metrics file may carry a grain
                prefix (campaign:FILE.json target:FILE.json) for grouped rows
  totals        get_daily_metrics group_by total (+ get_sales_traffic_daily group_by total)
                -> run_monitor.py {"ad_spend","ad_sales","total_sales"}

Every run writes a receipt (<out>-receipt.json, or DIR/<subcommand>-receipt.json) with the
input sha256s and row counts. Exit 2, with only the receipt written, when an input note says
rows were cut or a bare list holds exactly 50, 500 or 2000 rows (unless --allow-truncated),
when inputs mix clients or marketplaces, when one row id carries two different contents, or
when a row has the wrong shape for the subcommand.

With --allow-truncated the output says it is partial: JSON outputs are written as
{"note": "PARTIAL: ...", "rows": [...]}, and CSV outputs are marked "truncated": true in the
receipt with a warning on stderr.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

TRUNCATION = re.compile(r"ROW LIMIT REACHED|TRUNCATED", re.IGNORECASE)
# SYNQ's default limit, a common page size and the maximum. A bare list (no
# saved note) of exactly one of these lengths may have been cut by the cap.
CAP_SIZES = (50, 500, 2000)
SALES_LABEL = "SYNQ-reported sales (attribution window unconfirmed)"
LAG_WARNING = ("Sales and Traffic runs 2 to 3 days behind SYNQ ads data; "
               "total_sales for the last 3 days may still grow")

SQP_COLUMNS = [
    "asin", "search_query", "total_click_count", "asin_click_count",
    "total_purchase_count", "asin_purchase_count", "search_query_volume",
    "total_query_impression_count", "asin_impression_count", "search_query_score",
]
# SUPA column -> SYNQ field. Market columns repeat on every ASIN row of a query and period.
SQP_ASIN_FIELDS = {
    "asin_click_count": "clicks",
    "asin_purchase_count": "purchases",
    "asin_impression_count": "impressions",
    "search_query_score": "search_query_score",
}
SQP_MARKET_FIELDS = {
    "total_click_count": "total_clicks",
    "total_purchase_count": "total_purchases",
    "search_query_volume": "search_query_volume",
    "total_query_impression_count": "total_query_impressions",
}
ST_CSV_COLUMNS = ["search_term", "campaign", "ad_group", "match_type",
                  "impressions", "clicks", "spend", "sales", "orders"]
STOCK_COLUMNS = ["asin", "out_of_stock_days"]
METRIC_FIELDS = ("impressions", "clicks", "cost", "sales", "orders")
ENTITY_GRAINS = ("campaign", "ad_group", "target", "keyword")
WEEK_START = {"sunday": 6, "monday": 0}


class ConvertError(Exception):
    """Input that cannot produce trustworthy output. Exit code 2."""


# ------------------------------------------------------------------ input

class Source:
    def __init__(self, path: str, rows: list, note: str | None, sha256: str, role: str = "",
                 bare: bool = False, grain: str | None = None):
        self.path = path
        self.role = role
        self.rows = rows
        self.note = note
        self.sha256 = sha256
        self.bare = bare  # saved without the {"note", "rows"} wrapper and without a NOTE block
        self.grain = grain  # entities: the grain prefix of a --metrics file
        self.truncated = bool(note and TRUNCATION.search(note))
        # A bare list exactly at a cap size: the note that would say "cut" was not saved.
        self.at_cap = bare and len(rows) in CAP_SIZES

    def cut_reason(self) -> str | None:
        if self.truncated:
            return f"{self.path}: {self.note}"
        if self.at_cap:
            return (f"{self.path}: a bare list of exactly {len(self.rows)} rows (a SYNQ row cap) "
                    "saved without its note")
        return None

    def receipt(self) -> dict:
        out = {"path": self.path, "sha256": self.sha256, "rows": len(self.rows),
               "note": self.note, "truncated": self.truncated, "bare_at_cap": self.at_cap}
        if self.grain:
            out["grain"] = self.grain
        return out


def _parse_text(text: str, path: str):
    """Return (rows, note, bare) from one saved response. `bare` is True for a
    list saved with neither the wrapper nor a NOTE block."""
    stripped = text.lstrip("﻿").strip()
    note = None
    bare = True
    if stripped.upper().startswith("NOTE"):
        starts = [i for i in (stripped.find("["), stripped.find("{")) if i >= 0]
        if not starts:
            raise ConvertError(f"{path}: a note with no JSON after it")
        cut = min(starts)
        note = stripped[:cut].strip() or None
        stripped = stripped[cut:]
        bare = False
    try:
        data = json.loads(stripped)
    except ValueError as exc:
        raise ConvertError(f"{path}: not JSON ({exc})") from exc
    if isinstance(data, dict):
        if "rows" not in data:
            raise ConvertError(f"{path}: an object without 'rows'; save as "
                               '{"note": <text or null>, "rows": [...]}')
        if data.get("note") is not None:
            note = str(data["note"])
        data = data["rows"]
        bare = False
    if not isinstance(data, list) or not all(isinstance(r, dict) for r in data):
        raise ConvertError(f"{path}: rows must be a list of objects")
    return data, note, bare


def load_source(path: str, role: str = "", grain: str | None = None) -> Source:
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ConvertError(f"cannot read {path}: {exc}") from exc
    rows, note, bare = _parse_text(raw.decode("utf-8"), path)
    return Source(path, rows, note, hashlib.sha256(raw).hexdigest(), role, bare=bare, grain=grain)


def split_grain(arg: str) -> tuple[str | None, str]:
    """`campaign:CAMP.json` -> ("campaign", "CAMP.json"). Only an ENTITY_GRAINS
    prefix counts; any other text before a colon stays part of the path."""
    head, sep, rest = arg.partition(":")
    if sep and head in ENTITY_GRAINS and rest:
        return head, rest
    return None, arg


class Run:
    """One subcommand run: inputs, warnings and the receipt."""

    def __init__(self, subcommand: str, args):
        self.subcommand = subcommand
        self.args = args
        self.sources: list[Source] = []
        self.warnings: list[str] = []
        self.outputs: list[dict] = []
        self.extra: dict = {}
        self.rows_deduped = 0
        self.cut_reasons: list[str] = []  # set by check_truncation under --allow-truncated

    @property
    def truncated(self) -> bool:
        return bool(self.cut_reasons)

    def load(self, paths, role: str, grains: bool = False) -> list[Source]:
        loaded = []
        for p in paths or []:
            grain = None
            if grains:
                grain, p = split_grain(p)
            src = load_source(p, role, grain)
            self.sources.append(src)
            loaded.append(src)
            if src.note and not src.truncated:
                self.warnings.append(f"{p}: note kept: {src.note}")
        return loaded

    def check_truncation(self):
        noted = [s.path for s in self.sources if s.truncated]
        at_cap = [s for s in self.sources if s.at_cap and not s.truncated]
        if not noted and not at_cap:
            return
        if self.args.allow_truncated:
            self.cut_reasons = [s.cut_reason() for s in self.sources if s.cut_reason()]
            self.warnings.append("truncated input accepted with --allow-truncated; the output "
                                 "is NOT complete: " + "; ".join(self.cut_reasons))
            return
        if noted:
            raise ConvertError("input note says rows were cut (ROW LIMIT REACHED or TRUNCATED): "
                               + ", ".join(noted) + ". Narrow the filters or raise the limit and "
                               "pull again, or pass --allow-truncated for a knowingly partial run")
        raise ConvertError(
            "a bare JSON list with exactly a row-cap count of rows ("
            + ", ".join(f"{s.path}: {len(s.rows)}" for s in at_cap)
            + "); it may have been cut and its note was not saved. Save the response with its "
            'note wrapper {"note": <text or null>, "rows": [...]}, or raise limit and pull again, '
            "or pass --allow-truncated for a knowingly partial run")

    def partial_note(self) -> str:
        """The note a partial JSON output carries, so it never looks complete downstream."""
        return ("PARTIAL: converted with --allow-truncated from cut input; the rows are NOT "
                "complete. " + "; ".join(self.cut_reasons))

    def json_payload(self, rows: list):
        """A plain list, or the {"note", "rows"} wrapper when the input was cut."""
        return {"note": self.partial_note(), "rows": rows} if self.truncated else rows

    def check_scope(self):
        """One client and one marketplace across every input row that names them."""
        for key, flag in (("client_id", "client_id"), ("marketplace", "marketplace")):
            seen = {str(r[key]) for s in self.sources for r in s.rows if r.get(key) not in (None, "")}
            want = getattr(self.args, flag, None)
            if len(seen) > 1:
                raise ConvertError(f"inputs mix {key} values {sorted(seen)}; convert one client "
                                   "and marketplace per run")
            if want and seen and seen != {want}:
                raise ConvertError(f"--{flag.replace('_', '-')} {want} but the rows say {sorted(seen)}")
            if seen:
                self.extra[key] = next(iter(seen))

    def rows(self, sources: list[Source], with_source: bool = False) -> list:
        """Rows across pages, deduplicated by id. One id with two contents exits 2.
        `with_source` returns (source, row) pairs."""
        out, by_id = [], {}
        for s in sources:
            for r in s.rows:
                rid = r.get("id")
                if rid is not None:
                    if rid in by_id:
                        if by_id[rid] != r:
                            raise ConvertError(f"row id {rid} appears twice with different contents "
                                               f"(last in {s.path}); the pages mix pulls")
                        self.rows_deduped += 1
                        continue
                    by_id[rid] = r
                out.append((s, r) if with_source else r)
        return out

    def receipt(self, ok: bool, errors: list[str]) -> dict:
        return {
            "ok": ok,
            "subcommand": self.subcommand,
            "created_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
            "allow_truncated": bool(getattr(self.args, "allow_truncated", False)),
            "truncated": self.truncated,
            "inputs": [dict(s.receipt(), role=s.role) for s in self.sources],
            "rows_read": sum(len(s.rows) for s in self.sources),
            "rows_deduped": self.rows_deduped,
            "outputs": self.outputs,
            **self.extra,
            "warnings": self.warnings,
            "errors": errors,
        }


# ------------------------------------------------------------------ helpers

def num(v) -> float:
    if v is None or isinstance(v, bool):
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", "").strip()
    if s in ("", "-", "null", "None"):
        return 0.0
    try:
        return float(s)
    except ValueError as exc:
        raise ConvertError(f"not a number: {v!r}") from exc


def clean_num(x: float):
    """Integral floats as int, others rounded to 4 decimals (SYNQ cost carries 4)."""
    x = round(float(x), 4)
    return int(x) if x == int(x) else x


def opt_num(v):
    """A number for the CSV, or None (written blank) when SYNQ sent none."""
    return None if v is None or v == "" else clean_num(num(v))


def to_date(v, what: str) -> dt.date:
    s = str(v or "")[:10]
    try:
        return dt.date.fromisoformat(s)
    except ValueError as exc:
        raise ConvertError(f"{what}: not a date: {v!r}") from exc


def week_start_of(d: dt.date, start: str) -> dt.date:
    return d - dt.timedelta(days=(d.weekday() - WEEK_START[start]) % 7)


def parse_asins(s: str | None) -> set[str] | None:
    if not s:
        return None
    return {a.strip().upper() for a in s.split(",") if a.strip()}


def write_csv(path: Path, columns: list[str], rows: list[dict]):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({c: ("" if r.get(c) is None else r.get(c)) for c in columns})


def write_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ sqp

def build_sqp(run: Run) -> dict[str, list[dict]]:
    src = run.load(run.args.pages, "sqp")
    run.check_truncation()
    run.check_scope()
    asins = parse_asins(run.args.asins)
    market: dict[tuple, dict] = {}
    weeks: dict[str, dict[tuple, dict]] = defaultdict(dict)
    for r in run.rows(src):
        if not r.get("asin"):
            raise ConvertError("an SQP row without asin (brand-level pull?); pull per-ASIN rows "
                               "with brand_level off")
        period = str(r.get("report_period") or "WEEK").upper()
        if period != "WEEK":
            raise ConvertError(f"report_period {period}; SUPA needs WEEK rows")
        start = to_date(r.get("period_start"), "period_start")
        if start.weekday() != 6:
            raise ConvertError(f"period_start {start} is not a Sunday")
        if r.get("period_end") and to_date(r["period_end"], "period_end") != start + dt.timedelta(days=6):
            raise ConvertError(f"period {start}..{r['period_end']} is not Sunday to Saturday")
        asin = str(r["asin"]).strip().upper()
        if asins and asin not in asins:
            continue
        query = str(r.get("search_query") or "").strip()
        if not query:
            raise ConvertError(f"an SQP row for {asin} {start} without search_query")
        mkey = (start.isoformat(), query.lower())
        mvals = {col: r.get(field) for col, field in SQP_MARKET_FIELDS.items()}
        if mkey not in market:
            market[mkey] = mvals
        elif market[mkey] != mvals:
            run.warnings.append(f"market columns differ across ASIN rows for '{query}' {start}; "
                                "kept the first")
        row = {"asin": asin, "search_query": query}
        row.update({col: opt_num(r.get(field)) for col, field in SQP_ASIN_FIELDS.items()})
        rkey = (asin, query.lower())
        wk = weeks[start.isoformat()]
        if rkey in wk and wk[rkey] != row:
            raise ConvertError(f"two different SQP rows for {asin} '{query}' {start}")
        wk[rkey] = row
    out = {}
    for week, rows in sorted(weeks.items()):
        built = []
        for (asin, qkey), row in rows.items():
            m = market[(week, qkey)]
            full = dict(row)
            full.update({col: opt_num(m[col]) for col in SQP_MARKET_FIELDS})
            built.append(full)
        built.sort(key=lambda x: (x["asin"], -num(x["search_query_volume"]), x["search_query"].lower()))
        out[week] = built
    if not out:
        raise ConvertError("no SQP rows left to write")
    run.extra["weeks"] = {w: {"rows": len(rs), "asins": sorted({r["asin"] for r in rs}),
                              "queries": len({r["search_query"].lower() for r in rs})}
                          for w, rs in out.items()}
    return out


def cmd_sqp(run: Run):
    out = build_sqp(run)
    d = Path(run.args.out_dir)
    d.mkdir(parents=True, exist_ok=True)
    for week, rows in out.items():
        p = d / f"sqp_{week}.csv"
        write_csv(p, SQP_COLUMNS, rows)
        run.outputs.append({"path": str(p), "rows": len(rows)})


# ------------------------------------------------------------------ search terms

def build_search_terms(run: Run):
    src = run.load(run.args.pages, "search_terms")
    run.check_truncation()
    run.check_scope()
    products = parse_asins(run.args.ad_products)
    agg: dict[str, dict[tuple, dict]] = defaultdict(dict)
    dates: dict[str, set] = defaultdict(set)
    skipped = 0
    for r in run.rows(src):
        if products and str(r.get("ad_product") or "").upper() not in products:
            skipped += 1
            continue
        term = str(r.get("search_term") or "").strip()
        if not term:
            raise ConvertError("a search-term row without search_term")
        day = to_date(r.get("report_date"), "report_date")
        ws = week_start_of(day, run.args.week_start).isoformat()
        dates[ws].add(day)
        campaign = str(r.get("campaign_name") or r.get("campaign_id") or "")
        ad_group = str(r.get("ad_group_name") or r.get("ad_group_id") or "")
        match = str(r.get("match_type") or "")
        key = (term.lower(), campaign, ad_group, match)
        rec = agg[ws].setdefault(key, {"search_term": term, "campaign": campaign, "ad_group": ad_group,
                                       "match_type": match, "impressions": 0.0, "clicks": 0.0,
                                       "spend": 0.0, "sales": 0.0, "orders": 0.0})
        rec["impressions"] += num(r.get("impressions"))
        rec["clicks"] += num(r.get("clicks"))
        rec["spend"] += num(r.get("cost"))
        rec["sales"] += num(r.get("sales"))
        rec["orders"] += num(r.get("orders"))
    if not agg:
        raise ConvertError("no search-term rows left to write")
    weeks = {}
    for ws in sorted(agg):
        rows = [{k: (clean_num(v) if isinstance(v, float) else v) for k, v in rec.items()}
                for rec in agg[ws].values()]
        rows.sort(key=lambda x: (-num(x["spend"]), x["search_term"].lower(), x["campaign"]))
        seen = sorted(dates[ws])
        info = {"rows": len(rows), "first_date": seen[0].isoformat(), "last_date": seen[-1].isoformat(),
                "days_seen": len(seen), "partial": len(seen) < 7}
        if info["partial"]:
            run.warnings.append(f"week {ws}: rows on {len(seen)} of 7 days; a quiet day and a "
                                "missing pull look the same, check the pull window")
        weeks[ws] = (rows, info)
    run.extra["weeks"] = {ws: info for ws, (_, info) in weeks.items()}
    run.extra["rows_skipped_ad_product"] = skipped
    return weeks


def cmd_search_terms(run: Run):
    weeks = build_search_terms(run)
    d = Path(run.args.out_dir)
    d.mkdir(parents=True, exist_ok=True)
    for ws, (rows, _) in weeks.items():
        we = (dt.date.fromisoformat(ws) + dt.timedelta(days=6)).isoformat()
        p = d / f"search_terms_{ws}.csv"
        write_csv(p, ST_CSV_COLUMNS, rows)
        run.outputs.append({"path": str(p), "rows": len(rows)})
        j = d / f"searchterms_weekly_{we}.json"
        write_json(j, run.json_payload(
            [{"term": r["search_term"], "campaign": r["campaign"], "ad group": r["ad_group"],
              "match type": r["match_type"], "impressions": r["impressions"],
              "clicks": r["clicks"], "spend": r["spend"], "sales": r["sales"],
              "orders": r["orders"]} for r in rows]))
        run.outputs.append({"path": str(j), "rows": len(rows)})


# ------------------------------------------------------------------ stock

def build_stock(run: Run):
    src = run.load(run.args.history, "inventory_history")
    run.check_truncation()
    run.check_scope()
    asins = parse_asins(run.args.asins)
    # pools[(asin, date)][pool_key] = fulfillable quantity
    pools: dict[tuple, dict] = defaultdict(dict)
    for r in run.rows(src):
        if not r.get("snapshot_date"):
            raise ConvertError("an inventory row without snapshot_date; pull get_inventory with "
                               "history: true")
        asin = str(r.get("asin") or "").strip().upper()
        if not asin:
            raise ConvertError("an inventory history row without asin")
        if asins and asin not in asins:
            continue
        day = to_date(r["snapshot_date"], "snapshot_date")
        if r.get("fnsku"):
            pool = f"fnsku:{r['fnsku']}"
        elif r.get("sku"):
            pool = f"sku:{r['sku']}"
        else:
            pool = f"row:{r.get('id')}"
        qty = r.get("fulfillable_quantity")
        if qty is None:
            continue
        qty = num(qty)
        held = pools[(asin, day)]
        if pool in held and held[pool] != qty:
            run.warnings.append(f"{asin} {day} {pool}: rows disagree ({held[pool]:g} vs {qty:g}); "
                                "kept the larger")
            qty = max(qty, held[pool])
        held[pool] = qty
    if not pools:
        raise ConvertError("no inventory history rows left to count")
    weeks: dict[str, dict[str, dict]] = defaultdict(dict)
    for (asin, day), held in pools.items():
        ws = week_start_of(day, run.args.week_start).isoformat()
        rec = weeks[ws].setdefault(asin, {"out": 0, "observed": 0, "pools": 0})
        rec["observed"] += 1
        rec["pools"] = max(rec["pools"], len(held))
        if sum(held.values()) <= 0:
            rec["out"] += 1
    info = {}
    for ws in sorted(weeks):
        for asin, rec in sorted(weeks[ws].items()):
            if rec["observed"] < 7:
                run.warnings.append(f"{asin} week {ws}: {rec['observed']} of 7 days have a snapshot; "
                                    "days without one are not counted")
        info[ws] = {asin: {"out_of_stock_days": rec["out"], "days_observed": rec["observed"],
                           "max_pools_per_day": rec["pools"]}
                    for asin, rec in sorted(weeks[ws].items())}
    run.extra["weeks"] = info
    return info


def cmd_stock(run: Run):
    info = build_stock(run)
    d = Path(run.args.out_dir)
    d.mkdir(parents=True, exist_ok=True)
    for ws, per_asin in info.items():
        p = d / f"stock_{ws}.csv"
        rows = [{"asin": a, "out_of_stock_days": v["out_of_stock_days"]} for a, v in per_asin.items()]
        write_csv(p, STOCK_COLUMNS, rows)
        run.outputs.append({"path": str(p), "rows": len(rows)})


# ------------------------------------------------------------------ entities

def _metric_window(r: dict) -> str:
    """The pull a metrics row came from: one get_metrics timeframe, or get_daily_metrics."""
    if r.get("timeframe"):
        return f"get_metrics timeframe {r['timeframe']}"
    return "get_daily_metrics"


def _metric_shape(r: dict) -> str:
    return "grouped" if "total_groups" in r else "raw"


def build_entities(run: Run) -> list[dict]:
    msrc = run.load(run.args.metrics, "metrics", grains=True)
    csrc = run.load(run.args.campaigns, "campaigns")
    tsrc = run.load(run.args.search_terms, "search_terms")
    run.check_truncation()
    run.check_scope()
    camp_names = {}
    for r in run.rows(csrc):
        if r.get("campaign_id") is not None:
            camp_names[str(r["campaign_id"])] = r.get("name")
    match_votes: dict[str, Counter] = defaultdict(Counter)
    kw_text, ag_names, st_camp_names = {}, {}, {}
    for r in run.rows(tsrc):
        kid = r.get("keyword_id")
        if kid is not None:
            if r.get("match_type"):
                match_votes[str(kid)][str(r["match_type"])] += 1
            if r.get("keyword_text"):
                kw_text.setdefault(str(kid), r["keyword_text"])
        if r.get("ad_group_id") is not None and r.get("ad_group_name"):
            ag_names.setdefault(str(r["ad_group_id"]), r["ad_group_name"])
        if r.get("campaign_id") is not None and r.get("campaign_name"):
            st_camp_names.setdefault(str(r["campaign_id"]), r["campaign_name"])
    match_of = {}
    for kid, votes in match_votes.items():
        if len(votes) > 1:
            run.warnings.append(f"keyword_id {kid} has several match types {dict(votes)}; kept the "
                                "most frequent")
        match_of[kid] = votes.most_common(1)[0][0]

    seen_sha: dict[str, str] = {}
    for s in msrc:
        if not any(r.get("id") is None for r in s.rows):
            continue  # rows with ids dedupe across files
        if s.sha256 in seen_sha:
            raise ConvertError(f"--metrics {s.path} is the same file as {seen_sha[s.sha256]}; "
                               "grouped rows carry no id, so it would be counted twice")
        seen_sha[s.sha256] = s.path

    kinds, dates = set(), set()
    shapes: dict[str, set] = defaultdict(set)  # grain -> {"raw", "grouped"}
    skipped: Counter = Counter()
    agg: dict[tuple, dict] = {}
    for s, r in run.rows(msrc, with_source=True):
        etype = r.get("entity_type")
        if etype and s.grain and etype != s.grain:
            raise ConvertError(f"{s.path}: prefix {s.grain}: but a row says entity_type {etype}")
        etype = etype or s.grain or run.args.entity_type
        if not etype:
            raise ConvertError("a grouped metrics row has no entity_type; prefix the file with "
                               "the group_by value used for the pull (e.g. target:FILE.json) or "
                               "pass --entity-type")
        if etype not in ENTITY_GRAINS:
            skipped[etype] += 1
            continue
        kinds.add(_metric_window(r))
        shapes[etype].add(_metric_shape(r))
        if r.get("report_date"):
            dates.add(str(r["report_date"])[:10])
        cid = None if r.get("campaign_id") is None else str(r["campaign_id"])
        eid = cid if etype == "campaign" else r.get("entity_id")
        if etype == "ad_group" and eid is None:
            eid = r.get("ad_group_id")
        if eid is None:
            raise ConvertError(f"a {etype} metrics row without an id")
        key = (etype, str(r.get("ad_product") or ""), str(eid))
        rec = agg.get(key)
        if rec is None:
            rec = agg[key] = {"entity_type": etype, "entity_id": str(eid), "campaign_id": cid,
                              "ad_group_id": None if r.get("ad_group_id") is None else str(r["ad_group_id"]),
                              "ad_product": r.get("ad_product"), "keyword_text": None,
                              **{f: 0.0 for f in METRIC_FIELDS}}
        if r.get("keyword_text") and not rec["keyword_text"]:
            rec["keyword_text"] = r["keyword_text"]
        for f in METRIC_FIELDS:
            rec[f] += num(r.get(f))
    if len(kinds) > 1:
        raise ConvertError(f"metrics rows mix windows {sorted(kinds)}; summing them would double "
                           "count. Convert one window per run")
    both = sorted(g for g, sh in shapes.items() if len(sh) > 1)
    if both:
        raise ConvertError(f"{', '.join(both)} metrics come both as raw daily rows and as grouped "
                           "rows; the same entity would be counted twice. Use one shape per grain")
    if not agg:
        raise ConvertError("no campaign, ad_group, target or keyword metrics rows to convert")

    out, unmatched = [], set()
    for rec in sorted(agg.values(), key=lambda x: (ENTITY_GRAINS.index(x["entity_type"]), -x["cost"],
                                                   x["entity_id"])):
        cid = rec["campaign_id"]
        cname = camp_names.get(cid) if cid else None
        if cname is None and cid:
            cname = st_camp_names.get(cid)
            if cname is None:
                unmatched.add(cid)
        etype, eid = rec["entity_type"], rec["entity_id"]
        if etype == "campaign":
            name = cname
        elif etype == "ad_group":
            name = ag_names.get(rec["ad_group_id"] or eid) or cname
        else:
            name = rec["keyword_text"] or kw_text.get(eid) or cname
        if not name:
            name = f"{etype} {eid}"  # never blank: the monitor skips nameless rows
        out.append({
            "entity_type": etype,
            "name": name,
            "campaign_name": cname,
            "campaign_id": cid,
            "category": "Unknown",
            "match_type": match_of.get(eid) if etype in ("target", "keyword") else None,
            "impressions": int(rec["impressions"]),
            "clicks": int(rec["clicks"]),
            "spend": clean_num(rec["cost"]),
            "sales": clean_num(rec["sales"]),
            "orders": int(rec["orders"]),
            "daily_budget": None,
            "budget_capped_days": None,
            "time_in_budget": None,
            "entity_id": eid,
            "ad_group_id": rec["ad_group_id"],
            "ad_product": rec["ad_product"],
            "source": "synq",
        })
    if unmatched:
        run.warnings.append(f"{len(unmatched)} campaign ids have no name in list_campaigns or the "
                            "search terms (pull list_campaigns without a state filter): "
                            + ", ".join(sorted(unmatched)))
    run.extra.update({
        "window": next(iter(kinds)),
        "dates": [min(dates), max(dates)] if dates else None,
        "rows_skipped_by_entity_type": dict(skipped),
        "entities_by_type": dict(Counter(r["entity_type"] for r in out)),
        "match_type_joined": sum(1 for r in out if r["match_type"]),
        "sales_label": SALES_LABEL,
    })
    return out


def cmd_entities(run: Run):
    rows = build_entities(run)
    p = Path(run.args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    write_json(p, run.json_payload(rows))
    run.outputs.append({"path": str(p), "rows": len(rows)})


# ------------------------------------------------------------------ totals

def _one_row(run: Run, sources: list[Source], what: str) -> dict:
    rows = run.rows(sources)
    if len(rows) != 1:
        raise ConvertError(f"{what}: expected exactly one row (group_by: total), got {len(rows)}")
    return rows[0]


def build_totals(run: Run) -> dict:
    ads = run.load([run.args.ads_total], "ads_total")
    st = run.load([run.args.sales_traffic] if run.args.sales_traffic else [], "sales_traffic_total")
    run.check_truncation()
    run.check_scope()
    a = _one_row(run, ads, "--ads-total")
    for f in ("cost", "sales"):
        if f not in a:
            raise ConvertError(f"--ads-total row has no '{f}'; save get_daily_metrics group_by total")
    total_sales = None
    if st:
        s = _one_row(run, st, "--sales-traffic")
        if "ordered_product_sales" not in s:
            raise ConvertError("--sales-traffic row has no 'ordered_product_sales'; save "
                               "get_sales_traffic_daily group_by total")
        total_sales = clean_num(num(s["ordered_product_sales"]))
        run.warnings.append(LAG_WARNING)
    run.extra.update({"sales_label": SALES_LABEL, "source": "SYNQ"})
    return {"ad_spend": clean_num(num(a["cost"])), "ad_sales": clean_num(num(a["sales"])),
            "total_sales": total_sales}


def cmd_totals(run: Run):
    totals = build_totals(run)
    p = Path(run.args.out)
    p.parent.mkdir(parents=True, exist_ok=True)
    write_json(p, run.json_payload([totals]) if run.truncated else totals)
    run.outputs.append({"path": str(p), "rows": 1})


# ------------------------------------------------------------------ cli

def receipt_path(args) -> Path:
    if getattr(args, "out_dir", None):
        return Path(args.out_dir) / f"{args.cmd}-receipt.json"
    out = Path(args.out)
    stem = out.name[:-5] if out.name.endswith(".json") else out.name
    return out.with_name(f"{stem}-receipt.json")


def parse_args(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--allow-truncated", action="store_true",
                       help="accept inputs whose note says rows were cut (output is partial)")
        p.add_argument("--client-id", help="fail unless every row names this SYNQ client_id")
        p.add_argument("--marketplace", help="fail unless every row names this marketplace")

    p = sub.add_parser("sqp", help="get_sqp_data -> SUPA SQP CSVs")
    p.add_argument("--pages", nargs="+", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--asins", help="comma-separated ASINs to keep (default: all)")
    common(p)

    p = sub.add_parser("search-terms", help="get_search_terms -> SUPA PPC CSVs + monitor JSON")
    p.add_argument("--pages", nargs="+", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--week-start", choices=sorted(WEEK_START), default="sunday")
    p.add_argument("--ad-products", help="comma-separated ad products to keep, e.g. SP,SB")
    common(p)

    p = sub.add_parser("stock", help="get_inventory history -> stock CSVs")
    p.add_argument("--history", nargs="+", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--week-start", choices=sorted(WEEK_START), default="sunday")
    p.add_argument("--asins", help="comma-separated ASINs to keep (default: all)")
    common(p)

    p = sub.add_parser("entities", help="metrics + campaigns -> run_weekly.py entity rows")
    p.add_argument("--metrics", nargs="+", required=True,
                   help="metrics files, each optionally prefixed with its grain "
                        f"({', '.join(ENTITY_GRAINS)}), e.g. campaign:CAMP.json target:TGT.json")
    p.add_argument("--campaigns", nargs="+", required=True)
    p.add_argument("--search-terms", nargs="+")
    p.add_argument("--entity-type", choices=ENTITY_GRAINS,
                   help="entity type for grouped rows in a --metrics file without a grain prefix")
    p.add_argument("--out", required=True)
    common(p)

    p = sub.add_parser("totals", help="ads + sales totals -> run_monitor.py figures")
    p.add_argument("--ads-total", required=True)
    p.add_argument("--sales-traffic")
    p.add_argument("--out", required=True)
    common(p)
    return ap.parse_args(argv)


COMMANDS = {"sqp": cmd_sqp, "search-terms": cmd_search_terms, "stock": cmd_stock,
            "entities": cmd_entities, "totals": cmd_totals}


def main(argv=None) -> int:
    args = parse_args(argv)
    run = Run(args.cmd, args)
    rpath = receipt_path(args)
    try:
        COMMANDS[args.cmd](run)
    except ConvertError as exc:
        rpath.parent.mkdir(parents=True, exist_ok=True)
        write_json(rpath, run.receipt(False, [str(exc)]))
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"receipt: {rpath}", file=sys.stderr)
        return 2
    if run.truncated:
        for o in run.outputs:
            o["truncated"] = True
            if o["path"].endswith(".csv"):
                # A CSV cannot carry the note; the receipt and this warning must.
                print(f"WARNING: {o['path']} was written from truncated input with "
                      "--allow-truncated and is NOT complete; never use it for SUPA, the "
                      "monitor or a proposal", file=sys.stderr)
    write_json(rpath, run.receipt(True, []))
    for w in run.warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for o in run.outputs:
        print(f"{o['path']}\t{o['rows']} rows")
    print(f"receipt: {rpath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
