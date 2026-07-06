#!/usr/bin/env python3
"""
Amazon Ad/Sales Audit narrative scaffold generator.
Emits a Markdown draft following docs/amazon-ad-audit-playbook.md's section skeleton,
with KPIs/tables PRE-FILLED from metrics.json + sqp_summary.json and prose/problem/lever
bodies left as `<!-- operator: ... -->` stubs for the operator to write in the agency voice.
Honors config.narrative flags (include_levers, include_30day_plan, include_what_can_be_reached).
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from branding import load_branding as _load_branding


def _prepared_by_org():
    return _load_branding({}).get("agency_name") or "the operator"


from analyze_audit import load_config


def _m(v, cur):
    sym = "€" if cur in ("EUR", "€") else "$"
    return f"{sym}{v:,.0f}"


def build(config_path, outdir):
    cfg = load_config(config_path)
    outdir = Path(outdir)
    M = json.loads((outdir / "metrics.json").read_text())
    SS = json.loads((outdir / "clean" / "sqp_summary.json").read_text()) if (outdir / "clean" / "sqp_summary.json").exists() else {}
    cur = M.get("currency", "USD"); T = M["totals"]; STB = M["searchterm_bucket"]; P = M["placement"]
    BE = M.get("breakeven", 0.50); CLIENT = M.get("client", "Client")
    markets = ", ".join(M.get("marketplaces", []) or [])
    channels = M.get("channels_present", ["SP"]); miss = [c for c in ("SB", "SD", "RAS") if c not in channels]
    win = M.get("windows", {}); nflags = cfg.get("narrative", {})
    L = []
    A = L.append

    A(f"# {CLIENT}: {markets} Amazon Advertising & Sales Audit\n")
    A(f"**Prepared by {_prepared_by_org()} · Marketplace: {markets} · Window: {win.get('ads','')}**\n")
    A(f"**Sources:** Ads bulk ({win.get('ads','')}), Business Report ({win.get('business_report','')}), "
      f"SQP ({len(win.get('sqp_weeks',[]))} weekly snapshots), DataDive niche {cfg.get('datadive_niche','')}.\n")
    A(f"> **Break-even ACOS = {BE:.0%} is an ASSUMPTION** pending confirmed margin. Every red/amber verdict keys off it.\n")
    A("---\n")

    # ---- Ads Summary ----
    organic = T["br_total_sales"] - T["sales"]
    A("## Ads Summary\n")
    A("<!-- operator: 2-3 sentences on what's really going on. Lead with the branded-carries / generic-bleeds tension and the capture wall. -->\n")
    A("| Metric | Value |")
    A("|---|---|")
    A(f"| Ad spend | {_m(T['spend'],cur)} |")
    A(f"| Ad sales | {_m(T['sales'],cur)} |")
    A(f"| **Ad ACOS** | **{T['acos']:.1%}** |")
    A(f"| Total ordered product sales | {_m(T['br_total_sales'],cur)} |")
    A(f"| Organic / non-ad sales (implied) | {_m(organic,cur)} |")
    A(f"| **TACOS** | **{T['tacos']:.1%}** |")
    A(f"| **Ad : organic** | **{T['ad_dependency']*100:.0f} : {(1-T['ad_dependency'])*100:.0f}**"
      + (f" ({T['sales']/organic:.2f} : 1)" if organic else "") + " |\n")
    A("### Traffic mix (by customer search term)\n")
    A("| Bucket | Spend | % spend | Sales | ACOS | CVR |")
    A("|---|---|---|---|---|---|")
    for b in ("Branded", "Generic", "Competitor"):
        d = STB.get(b)
        if not d:
            continue
        A(f"| {b} | {_m(d['spend'],cur)} | {d['spend']/T['spend']:.0%} | {_m(d['sales'],cur)} | {(d['acos'] or 0):.0%} | {d['cvr']:.1%} |")
    A("")
    A("---\n")

    # ---- Current Account Performance ----
    A("## Current Account Performance\n")
    A("### Business Report by ASIN\n")
    A("| ASIN | Group | Sessions | Units | Sales | Buy Box |")
    A("|---|---|---|---|---|---|")
    for d in sorted(M["business_report"]["rows"], key=lambda x: -x["sales"]):
        A(f"| {d['asin']} | {d['group']} | {d['sessions']:,} | {d['units']} | {_m(d['sales'],cur)} | {d['buybox']:.0%} |")
    A("")
    A("<!-- operator: one-line read-through: which line carries revenue, $0 ASINs, CVR health. -->\n")
    A("### Ads by format\n")
    A(f"Channels present: **{', '.join(channels)}**." + (f" Missing: **{', '.join(miss)}**." if miss else "") + "\n")
    A("### Placement\n")
    A("| Placement | Spend | Sales | ACOS |")
    A("|---|---|---|---|")
    for p, d in sorted(P.items(), key=lambda x: -x[1]["spend"]):
        A(f"| {p} | {_m(d['spend'],cur)} | {_m(d['sales'],cur)} | {(d['acos'] or 0):.1%} |")
    A("")
    A("---\n")

    # ---- Demand / SQP ----
    if SS:
        A("## Demand: what shoppers are actually doing (SQP)\n")
        A("| Intent | Queries | SV share | Purchase capture (brand ÷ market) |")
        A("|---|---|---|---|")
        for b in ("Branded", "Generic", "Competitor"):
            s = SS.get(b)
            if not s:
                continue
            A(f"| {b} | {s['queries']} | {s['sv_share']:.1%} | {s['capture']:.1%} ({s['brand_purch']}/{s['mkt_purch']}) |")
        A("")
        A("<!-- operator: the capture number is the story: category demand is large but unconverted. CTR-vs-CVR wall. -->\n")
        A("---\n")

    # ---- DataDive ----
    cj = cfg["inputs"].get("datadive_competitors_json")
    if cj and Path(cj if Path(cj).is_absolute() else (Path(__file__).resolve().parents[2] / cj)).exists():
        from build_audit_workbook import _adapt_competitors
        client_asins = {a for asins in (cfg.get("asin_groups") or {}).values() for a in asins}
        comp = _adapt_competitors(
            json.loads(Path(cj if Path(cj).is_absolute() else (Path(__file__).resolve().parents[2] / cj)).read_text()),
            client_asins)
        A("## DataDive: category difficulty & the price/review gap\n")
        A(f"Category median price **{_m(comp['median_price'],cur)}**, median reviews **{comp['median_reviews']:.0f}**, median rating **{comp['median_rating']}**.\n")
        A("<!-- operator: frame the price/review moat: is the client a premium outlier? what does that do to generic conversion? -->\n")
        A("---\n")

    # ---- Good and Bad ----
    A("## Good and Bad\n")
    A("<!-- operator: fold strengths inline as read-throughs. Then number the problems. -->\n")
    A("**Problem 1: <!-- title -->.** <!-- evidence -->\n")
    A("**Problem 2: <!-- title -->.** <!-- evidence -->\n")
    A("**Problem 3: <!-- title -->.** <!-- evidence -->\n")
    A("---\n")

    # ---- Growth Levers ----
    if nflags.get("include_levers", True):
        A("## Growth Levers\n")
        A("<!-- operator: order by impact on the ceiling. Offer track (reviews/expectations, positioning) usually leads; PPC restructure + placement + missing channels follow. -->\n")
        A("**Lever 1: <!-- reviews / expectation reset -->.**\n")
        A("**Lever 2: <!-- positioning / winning use case -->.**\n")
        A("**Lever 3: <!-- restructure PPC (waste falls out of a clean setup) -->.**\n")
        A("**Lever 4: <!-- narrow generic wedge -->.**\n")
        A("**Lever 5: <!-- placement rebalance -->.**\n")
        if miss:
            A(f"**Lever 6: <!-- add {', '.join(miss)} -->.**\n")
        A("---\n")

    if nflags.get("include_30day_plan", False):
        A("## Recommended 30-day plan\n")
        A("<!-- operator: only include if the client wants a week-by-week action plan. -->\n")
        A("---\n")
    if nflags.get("include_what_can_be_reached", False):
        A("## What can be reached\n")
        A("<!-- operator: directional outcomes; exact once margin is confirmed. -->\n")
        A("---\n")

    # ---- Sources / Method ----
    A("## Sources used\n")
    A(f"- Ads bulk ({win.get('ads','')}): reconciles to spend {_m(T['spend'],cur)} / sales {_m(T['sales'],cur)}.")
    A(f"- Business Report ({win.get('business_report','')}): total sales {_m(T['br_total_sales'],cur)}.")
    A(f"- SQP: {len(win.get('sqp_weeks',[]))} weekly snapshots.")
    A(f"- DataDive niche {cfg.get('datadive_niche','')}.\n")
    A("## Method notes\n")
    A(f"- **Break-even ACOS = {BE:.0%} is an assumption** pending margin.")
    A(f"- **Branded split** from the Search Term Report; Branded = {', '.join(cfg.get('brand_tokens',[]))}.")
    A("- **Ad-vs-organic** is derived (total − ad-attributed); directional.")
    A("- **SQP** SV deduped per query+week; multi-ASIN exports cap the grid (SV is a floor).\n")

    md = "\n".join(L)
    out = outdir / f"{_slug(CLIENT)}_{_slug(markets)}_Sales_Audit_SCAFFOLD.md"
    out.write_text(md)
    print("[narrative] wrote", out.name, f"({len(md.split())} words)")
    # optional docx
    try:
        import importlib.util
        if importlib.util.find_spec("docx"):
            import subprocess
            docx = out.with_suffix(".docx")
            subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "md_to_docx.py"), str(out), str(docx)], check=False)
    except Exception:
        pass
    return out


def _slug(s):
    import re
    return re.sub(r"[^A-Za-z0-9]+", "-", (s or "x")).strip("-")


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
