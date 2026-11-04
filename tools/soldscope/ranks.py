#!/usr/bin/env python3
"""SoldScope rank tracker responses -> the rank series shape the tools already read.

Inputs are saved MCP responses, never live calls:
  --organic / --sponsored   rank_tracker_list_phrases pages fetched with heatmap=true and
                            results_type=organic or sponsored. The page does not say which
                            type it holds, so the flag carries it.
  --history / --history-sponsored KEYWORD=RESP.json
                            rank_tracker_get_ranks_history responses (type 1 / type 2)
  --export / --export-sponsored EXPORT.json
                            rank_tracker_get_export JSON download rows (provisional: the JSON
                            field names were not captured yet; see tools/soldscope/README.md)

Default output, the shape DataDive Rank Radar data had:
  [{"keyword", "searchVolume", "ranks": [{"date", "organicRank", "sponsoredRank"}]}]
Rank 0, null, missing snapshots and ranks above 100 become 101. sponsoredRank is null when
no sponsored input was given; organicRank is null when only sponsored input was given.

--weekly-rows output, for tools/amazon-ads-monitor (--rank-json):
  [{"keyword", "rank_now", "rank_prev", "weeks_stable"}]
Weeks run Sunday to Saturday. A week's rank is the upper median of its daily organic ranks,
the same rule as load_rank in tools/sqp-supa/build_supa_workbook.py. weeks_stable counts
consecutive weeks, ending at the latest complete week, at or under --graduate-rank-max.

Exit 2 when --marketplace differs from the page group's marketplace, pages mix groups, or
a heatmap read is incomplete (rows read != meta.total, unless --allow-partial).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

NOT_RANKED = 101
HEATMAP_KEY = re.compile(r"^r_(\d{4}-\d{2}-\d{2})$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}")


class RankError(Exception):
    """Input that cannot produce trustworthy output. Exit code 2."""


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise RankError(f"cannot read {path}: {exc}") from exc


def fold_rank(v) -> int:
    """SoldScope rank -> 1..100, with 0, null, junk and > 100 as 101 (not ranked)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0 or v > 100:
        return NOT_RANKED
    return int(v)


def upper_median(vals: list[int]) -> int:
    vals = sorted(vals)
    return vals[len(vals) // 2]


def norm_kw(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def _to_date(v) -> str | None:
    """Unix seconds/milliseconds or an ISO/'YYYY-MM-DD HH:MM:SS' string -> UTC date."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        ts = v / 1000 if v > 1e11 else v
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    if isinstance(v, str):
        s = v.strip()
        if s.isdigit():
            return _to_date(int(s))
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00").replace(" ", "T"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(timezone.utc)
            return dt.date().isoformat()
        except ValueError:
            return s[:10] if DATE_RE.match(s) else None
    return None


class Series:
    """keyword -> {display, sv, organic: {date: rank}, sponsored: {date: rank}}."""

    def __init__(self):
        self.rows: dict[str, dict] = {}
        self.order: list[str] = []
        self.has = {"organic": False, "sponsored": False}

    def entry(self, keyword) -> dict:
        k = norm_kw(keyword)
        if k not in self.rows:
            self.rows[k] = {"keyword": str(keyword).strip(), "sv": None, "organic": {}, "sponsored": {}}
            self.order.append(k)
        return self.rows[k]

    def put(self, keyword, kind, day, rank, sv=None):
        e = self.entry(keyword)
        self.has[kind] = True
        if sv is not None and e["sv"] is None:
            e["sv"] = sv
        e[kind][day] = fold_rank(rank)


# ----------------------------------------------------------------------------- heatmap pages

def read_heatmap(paths, kind, series: Series, ctx: dict, allow_partial: bool):
    seen: dict = {}
    totals = set()
    for p in paths:
        page = load_json(p)
        if not isinstance(page, dict):
            raise RankError(f"{p}: not a list_phrases response")
        group = page.get("group") or {}
        if group:
            gid = group.get("id")
            if ctx.get("group_id") not in (None, gid):
                raise RankError(f"{p}: group {gid} differs from group {ctx['group_id']} in another page")
            ctx["group_id"] = gid
            if group.get("marketplace"):
                ctx.setdefault("markets", set()).add(str(group["marketplace"]).upper())
            if group.get("createdAt") and not ctx.get("created"):
                ctx["created"] = _to_date(group["createdAt"])
        meta = page.get("meta") or {}
        if "total" in meta:
            totals.add(int(meta["total"]))
        rows = page.get("data")
        if not isinstance(rows, list):
            raise RankError(f"{p}: no data list; save the full list_phrases response")
        for row in rows:
            if not isinstance(row, dict) or not row.get("phrase"):
                continue
            rid = row.get("id", row.get("phrase"))
            if rid in seen:
                continue
            seen[rid] = True
            sv = row.get("searchVolume")
            sv = int(sv) if isinstance(sv, (int, float)) and not isinstance(sv, bool) else None
            days = 0
            for key, cell in row.items():
                m = HEATMAP_KEY.match(key)
                if not m:
                    continue
                day = (cell or {}).get("date") if isinstance(cell, dict) else None
                rank = cell.get("rank") if isinstance(cell, dict) else cell
                series.put(row["phrase"], kind, day or m.group(1), rank, sv)
                days += 1
            if not days:
                series.entry(row["phrase"])["sv"] = sv
                ctx.setdefault("no_heatmap", []).append(row["phrase"])
    if len(totals) > 1:
        raise RankError(f"{kind} pages disagree on meta.total {sorted(totals)}")
    total = totals.pop() if totals else None
    ctx.setdefault("reads", {})[kind] = {"rows": len(seen), "meta_total": total}
    if total is not None and len(seen) != total and not allow_partial:
        raise RankError(f"{kind}: read {len(seen)} phrases but meta.total is {total}; fetch every page "
                        f"or pass --allow-partial")


# ----------------------------------------------------------------------------- history

def _pick_product(history: dict, product_id, asin, label):
    keys = [str(k) for k in history]
    if product_id is not None:
        if str(product_id) not in keys:
            raise RankError(f"{label}: product_id {product_id} not in history {keys}")
        return str(product_id)
    if asin:
        hits = [k for k in keys if any(str((s or {}).get("asin") or "").upper() == asin
                                       for s in history.get(k) or [])]
        if len(hits) == 1:
            return hits[0]
        if len(keys) == 1:
            # A parent product's snapshots carry the ranking child ASIN, so a
            # mismatch is not proof of the wrong product. Say so instead of
            # falling back silently.
            seen = sorted({str((s or {}).get("asin") or "").upper()
                           for s in history.get(keys[0]) or []} - {""})
            print(f"warning: {label}: --asin {asin} not in the history snapshots {seen}; using the only "
                  f"product {keys[0]} (a parent's variation ranks as its child ASIN; pass --product-id to be exact)",
                  file=sys.stderr)
    if len(keys) == 1:
        return keys[0]
    raise RankError(f"{label}: history holds products {keys}; pass --product-id")


def read_history(specs, kind, series: Series, product_id, asin):
    for spec in specs:
        if "=" not in spec:
            raise RankError(f"history input wants KEYWORD=RESP.json, got {spec!r}")
        keyword, path = spec.rsplit("=", 1)
        resp = load_json(path)
        data = resp.get("data", resp) if isinstance(resp, dict) else {}
        history = (data or {}).get("history") or {}
        if not isinstance(history, dict):
            raise RankError(f"{path}: data.history is not an object")
        series.entry(keyword)
        series.has[kind] = True
        if not history:
            continue
        pid = _pick_product(history, product_id, asin, path)
        snaps = history.get(pid)
        by_day = defaultdict(list)
        for s in snaps or []:
            day = _to_date((s or {}).get("created_at"))
            if day:
                by_day[day].append(fold_rank((s or {}).get("position")))
        for day, vals in by_day.items():
            series.put(keyword, kind, day, upper_median(vals))


# ----------------------------------------------------------------------------- export (provisional)

_EXPORT_KW = ("phrase", "keyword", "search_term", "searchTerm")
_EXPORT_DATE = ("date", "created_at", "createdAt", "tracked_at", "trackedAt", "scraped_at")
_EXPORT_RANK = ("position", "rank", "organic_position", "organicPosition", "sponsored_position",
                "sponsoredPosition")


def _first(row, keys):
    for k in keys:
        if k in row and row[k] not in (None, ""):
            return row[k]
    return None


def read_export(paths, kind, series: Series, product_id, asin):
    """Best-effort reader for rank_tracker_get_export JSON rows (raw snapshots or daily)."""
    for p in paths:
        d = load_json(p)
        rows = d.get("data", d.get("rows")) if isinstance(d, dict) else d
        if not isinstance(rows, list):
            raise RankError(f"{p}: export is not a list of rows")
        by = defaultdict(list)
        series.has[kind] = True
        for row in rows:
            if not isinstance(row, dict):
                continue
            if asin and row.get("asin") and str(row["asin"]).upper() != asin:
                continue
            if product_id is not None and row.get("product_id", row.get("productId")) not in (None, product_id):
                continue
            kw = _first(row, _EXPORT_KW)
            day = _to_date(_first(row, _EXPORT_DATE))
            if not kw or not day:
                continue
            by[(kw, day)].append(fold_rank(_first(row, _EXPORT_RANK)))
            sv = row.get("search_volume", row.get("searchVolume"))
            if isinstance(sv, (int, float)) and not isinstance(sv, bool):
                e = series.entry(kw)
                e["sv"] = e["sv"] if e["sv"] is not None else int(sv)
        for (kw, day), vals in by.items():
            series.put(kw, kind, day, upper_median(vals))


# ----------------------------------------------------------------------------- output

def to_series(series: Series, date_from=None, date_to=None, not_before=None) -> list[dict]:
    out = []
    for k in series.order:
        e = series.rows[k]
        days = sorted(set(e["organic"]) | set(e["sponsored"]))
        days = [d for d in days if (not date_from or d >= date_from) and (not date_to or d <= date_to)
                and (not not_before or d >= not_before)]
        ranks = []
        for d in days:
            ranks.append({
                "date": d,
                "organicRank": e["organic"].get(d, NOT_RANKED) if series.has["organic"] else None,
                "sponsoredRank": e["sponsored"].get(d, NOT_RANKED) if series.has["sponsored"] else None,
            })
        out.append({"keyword": e["keyword"], "searchVolume": e["sv"], "ranks": ranks})
    return out


def week_start(d: str) -> date:
    x = date.fromisoformat(d)
    return x - timedelta(days=(x.weekday() + 1) % 7)   # Sunday


def weekly_rows(series_out: list[dict], graduate_rank_max: int, cutoff: str | None = None,
                include_partial: bool = False) -> list[dict]:
    """Sunday-Saturday weekly upper medians -> ads-monitor rows.

    The latest week is the newest week whose Saturday is on or before `cutoff` (default:
    the newest date in the data), unless include_partial is set."""
    all_days = [r["date"] for s in series_out for r in s["ranks"] if r["organicRank"] is not None]
    if not all_days:
        return []
    cutoff_d = date.fromisoformat(cutoff or max(all_days))
    weeks_by_kw = {}
    for s in series_out:
        per = defaultdict(list)
        for r in s["ranks"]:
            if r["organicRank"] is not None:
                per[week_start(r["date"])].append(r["organicRank"])
        weeks_by_kw[s["keyword"]] = {w: upper_median(v) for w, v in per.items()}
    candidates = {w for m in weeks_by_kw.values() for w in m}
    if not include_partial:
        candidates = {w for w in candidates if w + timedelta(days=6) <= cutoff_d}
    else:
        candidates = {w for w in candidates if w <= cutoff_d}
    if not candidates:
        return []
    latest = max(candidates)
    rows = []
    for s in series_out:
        m = weeks_by_kw[s["keyword"]]
        if latest not in m:
            continue
        prev = m.get(latest - timedelta(days=7))
        stable, w = 0, latest
        while w in m and m[w] <= graduate_rank_max:
            stable += 1
            w -= timedelta(days=7)
        rows.append({"keyword": s["keyword"], "rank_now": m[latest], "rank_prev": prev,
                     "weeks_stable": stable, "week_start": latest.isoformat()})
    return rows


def build_parser():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--organic", nargs="+", default=[], metavar="PAGE.json",
                    help="list_phrases heatmap pages fetched with results_type=organic")
    ap.add_argument("--sponsored", nargs="+", default=[], metavar="PAGE.json",
                    help="list_phrases heatmap pages fetched with results_type=sponsored")
    ap.add_argument("--history", nargs="+", default=[], metavar="KEYWORD=RESP.json",
                    help="get_ranks_history responses with type=1 (organic)")
    ap.add_argument("--history-sponsored", nargs="+", default=[], metavar="KEYWORD=RESP.json",
                    help="get_ranks_history responses with type=2 (sponsored)")
    ap.add_argument("--export", nargs="+", default=[], metavar="EXPORT.json",
                    help="rank tracker JSON export rows, organic (provisional)")
    ap.add_argument("--export-sponsored", nargs="+", default=[], metavar="EXPORT.json",
                    help="rank tracker JSON export rows, sponsored (provisional)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--asin", help="own ASIN (picks the product in history/export inputs)")
    ap.add_argument("--product-id", type=int, help="own rank-tracker product_id")
    ap.add_argument("--marketplace", help="expected marketplace; a different group marketplace fails")
    ap.add_argument("--date-from")
    ap.add_argument("--date-to")
    ap.add_argument("--weekly-rows", action="store_true", help="write ads-monitor weekly rows instead")
    ap.add_argument("--graduate-rank-max", type=int, default=3)
    ap.add_argument("--include-partial-week", action="store_true",
                    help="let a week that ends after --date-to (or the last data day) be the latest week")
    ap.add_argument("--keep-before-group", action="store_true",
                    help="keep heatmap days before the group's createdAt (they read as not ranked)")
    ap.add_argument("--allow-partial", action="store_true",
                    help="accept heatmap pages that do not cover meta.total phrases")
    return ap


def run(args) -> tuple[list, dict]:
    if not (args.organic or args.sponsored or args.history or args.history_sponsored
            or args.export or args.export_sponsored):
        raise RankError("give at least one of --organic, --sponsored, --history, --history-sponsored, "
                        "--export, --export-sponsored")
    asin = args.asin.strip().upper() if args.asin else None
    series, ctx = Series(), {}
    if args.organic:
        read_heatmap(args.organic, "organic", series, ctx, args.allow_partial)
    if args.sponsored:
        read_heatmap(args.sponsored, "sponsored", series, ctx, args.allow_partial)
    read_history(args.history, "organic", series, args.product_id, asin)
    read_history(args.history_sponsored, "sponsored", series, args.product_id, asin)
    if args.export:
        read_export(args.export, "organic", series, args.product_id, asin)
    if args.export_sponsored:
        read_export(args.export_sponsored, "sponsored", series, args.product_id, asin)
    markets = ctx.get("markets") or set()
    if len(markets) > 1:
        raise RankError(f"pages mix marketplaces {sorted(markets)}")
    if args.marketplace and markets and markets != {args.marketplace.upper()}:
        raise RankError(f"--marketplace {args.marketplace.upper()} but the group marketplace is "
                        f"{sorted(markets)[0]}")
    not_before = None if args.keep_before_group else ctx.get("created")
    out = to_series(series, args.date_from, args.date_to, not_before)
    info = {"group_id": ctx.get("group_id"), "marketplace": next(iter(markets), None),
            "reads": ctx.get("reads", {}), "keywords": len(out),
            "days": len({r["date"] for s in out for r in s["ranks"]}),
            "clipped_before": not_before, "no_heatmap": ctx.get("no_heatmap", [])}
    if args.weekly_rows:
        if not series.has["organic"]:
            raise RankError("--weekly-rows needs organic input (--organic, --history or --export)")
        rows = weekly_rows(out, args.graduate_rank_max, args.date_to, args.include_partial_week)
        info["weekly_rows"] = len(rows)
        info["latest_week"] = rows[0]["week_start"] if rows else None
        return rows, info
    return out, info


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        out, info = run(args)
    except RankError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(info))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
