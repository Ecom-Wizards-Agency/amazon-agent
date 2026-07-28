#!/usr/bin/env python3
"""
Amazon Ad/Sales Audit — the standard figure set (client-agnostic, config-driven).

Emits the four charts that earn their place in every audit, straight from the
contract inputs. Each one is guarded: if its input is missing the figure is
skipped, never faked.

  fig_rank_movement.png            where each keyword's organic rank started and
                                   ended over the window (dumbbell + direction arrow,
                                   real position axis, 1 = top). The STANDARD rank
                                   chart. (needs rank_radar_json)
  fig_rank_distribution.png        organic rank spread across the DataDive MKL
                                   (needs datadive_niche_json + asin_groups)
  fig_visibility_vs_competition.png  share of category search volume ranked top 10,
                                   you vs every seller in the niche
                                   (needs datadive_niche_json + datadive_competitors_json)
  fig_reviews_vs_price.png         the review/price moat, you highlighted
                                   (needs datadive_competitors_json)
  fig_demand_segments.png          GRAPH 1: where the demand is, across four EXCLUSIVE
                                   segments (branded / competitor / generic-core /
                                   generic-head). Splitting generic is the point: folding
                                   competitor brands and unwinnable head terms into one
                                   bar overstates the addressable category ~20x.
                                   (needs sqp_csvs + brand_tokens; core_tokens to split)
  fig_purchases_vs_market.png      GRAPH 2: purchases, YOU against THE MARKET, same four
                                   segments and the SAME measure on both bars. Not a
                                   per-segment capture rate: origination biases branded
                                   and generic rates differently so they are not
                                   comparable to each other, but counts are.
                                   (needs sqp_csvs)
  fig_brand_name_leak.png          who ranks on the brand's OWN name. Copycats and
                                   namesakes farm branded demand the brand is paying
                                   to create, and external traffic only builds the
                                   brand term, so this is where that leak shows up.
                                   Guarded: needs a branded query with real demand
                                   (>= MIN_BRAND_SV) and >= 3 sellers ranked on it,
                                   so a no-brand-demand account gets no empty chart.
                                   (needs datadive_niche_json + competitors + brand_tokens)

`build_audit.py` calls this automatically and `narrative_scaffold.py` references the
files it produced, so the operator writes prose around figures that already exist.
Degrades with a WARN if matplotlib is absent; the audit never hard-fails on a chart.

Design rules (from the dataviz standard):
- ONE measure per chart, categories on the axis. Identity comes from the axis and
  direct labels, so colour is only ever emphasis: the accent marks the client, a
  neutral marks context. Never a dual axis.
- Single series means no legend; the title names it.
- Headline numbers in titles are DERIVED, never typed, so they cannot drift from
  the marks they describe.
- Palette and font come from the branding file, so figures track the brand guide.

Run standalone:  python3 tools/amazon-ad-audit/build_figures.py --config <cfg> --outdir <dir>
"""
from __future__ import annotations
import csv, json, sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from analyze_audit import rp, load_config, classify  # noqa: E402
import branding as _branding  # noqa: E402

# Floor for "the brand is actually searched for". Below this, a brand-name-leak chart
# reads as noise rather than a finding, so single-product or no-brand-demand accounts
# skip it instead of shipping an empty bar chart. Same 500 floor the SQP workbook's
# Top-Opportunities tab uses, kept here so the two agree.
MIN_BRAND_SV = 500


def _palette():
    b = _branding.load_branding({})
    p = b["palette_doc"]
    return dict(accent="#" + p["accent"], ink="#" + p["ink"], steel="#" + p["steel"],
                hair="#" + p["mistline"], cloud="#" + p["cloud"],
                font_file=b["assets"].get("brand_dir") or "", fonts=b["fonts"])


def _setup(P):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    f = HERE / "brand" / P["fonts"]["doc_font_file"]
    if f.exists():
        font_manager.fontManager.addfont(str(f))
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(f)).get_name()
    plt.rcParams.update({
        "text.color": P["ink"], "axes.labelcolor": P["ink"],
        "xtick.color": P["ink"], "ytick.color": P["ink"],
        "axes.edgecolor": P["hair"], "figure.facecolor": "white", "axes.facecolor": "white",
    })
    return plt


def _frame(ax, P, xgrid=False, ygrid=False):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(P["hair"])
    ax.tick_params(length=0, labelsize=9)
    if xgrid:
        ax.xaxis.grid(True, color=P["hair"], lw=0.8); ax.set_axisbelow(True)
    if ygrid:
        ax.yaxis.grid(True, color=P["hair"], lw=0.8); ax.set_axisbelow(True)


def _title(ax, P, t, sub=None):
    ax.set_title(t, fontsize=12.5, fontweight="bold", color=P["ink"], loc="left",
                 pad=28 if sub else 10)
    if sub:
        ax.text(0, 1.015, sub, transform=ax.transAxes, fontsize=9, color=P["steel"], va="bottom")


def _client_asins(cfg):
    return {a for asins in (cfg.get("asin_groups") or {}).values() for a in asins}


def _best_rank(ranks, asins):
    vals = [ranks[a] for a in asins if ranks.get(a) is not None]
    return min(vals) if vals else None


# ------------------------------------------------------------------ figures
def _rank_movement(plt, P, cfg, out):
    """Standard rank-MOVEMENT chart: where each keyword started and ended over the
    window. A dumbbell with a direction arrow, red for slipped, green for gained,
    both endpoint ranks labelled. The axis is real rank position, 1 = top, with a
    page-2 marker.

    Why this design (operator's call, 2026-07-16): the old "rank movement" chart
    put rank on an INVERTED axis, so a tick like "22" read as "we rank 22 overall"
    when it was one keyword's worst position. Showing the actual position with a
    direction arrow removes that misread and makes better-vs-worse instant.

    Input: a DataDive Rank Radar payload at cfg["inputs"]["rank_radar_json"] —
    a list of {keyword, searchVolume, ranks:[{date, organicRank}, ...]}. Start =
    first ranked day, end = last. Guarded: returns None if the input is absent or
    unreadable, so an audit without a radar simply skips this figure.
    """
    rjp = rp((cfg.get("inputs") or {}).get("rank_radar_json"))
    if not rjp or not rjp.exists():
        return None
    try:
        payload = json.loads(rjp.read_text())
    except Exception:
        return None
    rows = []
    for k in (payload or []):
        rk = [x for x in (k.get("ranks") or []) if x.get("organicRank")]
        if not rk:
            continue
        rows.append((k.get("keyword", ""), k.get("searchVolume", 0),
                     rk[0]["organicRank"], rk[-1]["organicRank"]))
    if len(rows) < 3:
        return None
    rows = sorted(rows, key=lambda r: -r[1])[:cfg.get("rank_movement_top_n", 10)][::-1]
    GOOD, BAD = "#2E7D32", "#C0341D"
    slipped = sum(1 for _, _, s, e in rows if e > s)
    fig, ax = plt.subplots(figsize=(8.2, max(3.6, 0.5 * len(rows) + 1.2)))
    for i, (kw, sv, s, e) in enumerate(rows):
        col = BAD if e > s else (GOOD if e < s else P["steel"])
        ax.annotate("", xy=(e, i), xytext=(s, i),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=2.3, shrinkA=6, shrinkB=6), zorder=2)
        ax.scatter([s], [i], color=P["steel"], s=40, zorder=3)
        ax.scatter([e], [i], color=col, s=62, zorder=4)
        ax.text(s, i + .30, str(s), ha="center", va="bottom", fontsize=8, color=P["steel"])
        ax.text(e, i + .30, str(e), ha="center", va="bottom", fontsize=8.5, color=col, fontweight="bold")
    ax.axvline(20.5, color=P["hair"], lw=1, ls="--", zorder=1)
    ax.text(20.5, len(rows) - 0.4, "page 2 ►", ha="left", fontsize=8.5, color=P["steel"])
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows], fontsize=9)
    ax.set_xlim(0, max(e for _, _, s, e in rows) + 6)
    ax.set_xlabel("Organic rank position (1 = top of results)", fontsize=9, color=P["steel"])
    _title(ax, P, f"Rank slipped on {slipped} of {len(rows)} keywords over the window",
           f"{cfg.get('client','')} organic rank, start to end. Arrow points to where it is now; "
           "red slipped, green gained.")
    _frame(ax, P, xgrid=True)
    fig.tight_layout(); fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    return out


def _rank_distribution(plt, P, cfg, kws, asins, out):
    b = {"Page 1\n(rank 1-10)": 0, "Rank\n11-20": 0, "Rank\n21-50": 0, "Rank\n51+": 0,
         "Not ranked\nat all": 0}
    for k in kws:
        r = _best_rank(k.get("asinRanks") or {}, asins)
        if r is None: b["Not ranked\nat all"] += 1
        elif r <= 10: b["Page 1\n(rank 1-10)"] += 1
        elif r <= 20: b["Rank\n11-20"] += 1
        elif r <= 50: b["Rank\n21-50"] += 1
        else: b["Rank\n51+"] += 1
    labels, vals = list(b), list(b.values())
    fig, ax = plt.subplots(figsize=(9, 4.1))
    bars = ax.bar(labels, vals, color=[P["accent"]] + [P["steel"]] * 4, width=0.62)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.02, f"{v}",
                ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=P["ink"])
    _title(ax, P, f"Only {vals[0]} of {len(kws)} category keywords put you on page 1",
           f"{cfg.get('client','')} organic rank across the relevant keyword set "
           f"(DataDive, {cfg.get('windows', {}).get('datadive', '')})")
    ax.set_ylabel("Keywords", fontsize=9, color=P["steel"])
    ax.set_ylim(0, max(vals) * 1.18)
    _frame(ax, P, ygrid=True)
    fig.tight_layout(); fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    return out


def _visibility_vs_competition(plt, P, cfg, kws, comps, asins, out):
    total = sum(k.get("searchVolume") or 0 for k in kws)
    if not total:
        return None
    # One row per SELLER, not per ASIN. A brand with several ASINs in the niche is a single
    # bar, scored on its best-ranking ASIN per keyword, exactly the way the client's own
    # ASINs are aggregated below. Two rows sharing a brand name would otherwise land on the
    # same categorical tick and draw overlapping bars with two labels.
    rows = []
    by_brand = {}
    for c in comps:
        a = c.get("asin")
        if a in asins:
            continue
        by_brand.setdefault(c.get("brand", a), []).append(a)
    for brand, b_asins in by_brand.items():
        sv = sum((k.get("searchVolume") or 0) for k in kws
                 if (_best_rank(k.get("asinRanks") or {}, b_asins) or 99) <= 10)
        rows.append((brand, sv / total))
    sv_me = sum((k.get("searchVolume") or 0) for k in kws
                if (_best_rank(k.get("asinRanks") or {}, asins) or 99) <= 10)
    me = cfg.get("client", "You")
    rows.append((me, sv_me / total))
    rows.sort(key=lambda x: x[1])          # smallest first: barh draws bottom-up
    names = [r[0] for r in rows]; shares = [r[1] * 100 for r in rows]
    fig, ax = plt.subplots(figsize=(9, max(3.6, 0.36 * len(rows) + 1.6)))
    cols = [P["accent"] if n == me else P["steel"] for n in names]
    bars = ax.barh(names, shares, color=cols, height=0.62)
    for bar, s in zip(bars, shares):
        ax.text(s + 1.2, bar.get_y() + bar.get_height() / 2, f"{s:.0f}%", va="center",
                fontsize=9.5, fontweight="bold", color=P["ink"])
    for t, n in zip(ax.get_yticklabels(), names):
        if n == me:
            t.set_color(P["accent"]); t.set_fontweight("bold")
    # derive the headline so it can never drift from the bars
    mine = dict(rows)[me] * 100
    lead_n, lead_s = names[-1], shares[-1]
    _title(ax, P, f"You are visible on {mine:.0f}% of the category. {lead_n} is on {lead_s:.0f}%.",
           f"Share of the {total:,} category searches where each seller ranks in the top 10.")
    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of category search volume ranked top 10", fontsize=9, color=P["steel"])
    _frame(ax, P, xgrid=True)
    fig.tight_layout(); fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    return out


def _reviews_vs_price(plt, P, cfg, comps, asins, out):
    # A not-yet-rated listing reports reviewCount null, which is the whole story for a
    # new launch: it must appear on this chart, not be filtered off it. Normalise null
    # to a real 0 and keep it. `_x` is the plotting position only: the axis is log, which
    # cannot place 0, so 0 reviews is clamped onto the axis floor while every comparison
    # and label below still uses the true count.
    pts = []
    for c in comps:
        p = c.get("price")
        if p is None or p <= 0:
            continue
        c = dict(c, reviewCount=c.get("reviewCount") or 0)
        c["_x"] = max(c["reviewCount"], 1)
        pts.append(c)
    if len(pts) < 3:
        return None
    med_p = sorted(c["price"] for c in pts)[len(pts) // 2]
    med_r = sorted(c["reviewCount"] for c in pts)[len(pts) // 2]
    fig, ax = plt.subplots(figsize=(9, 5.0))
    ax.axhline(med_p, color=P["hair"], lw=1.2, zorder=1)
    ax.axvline(max(med_r, 1), color=P["hair"], lw=1.2, zorder=1)
    mine = [c for c in pts if c.get("asin") in asins]
    others = [c for c in pts if c.get("asin") not in asins]
    # label the client plus the extremes that carry the argument; labelling every
    # point collides and is the anti-pattern
    notable = set()
    if others:
        notable |= {max(others, key=lambda c: c["reviewCount"])["asin"],
                    max(others, key=lambda c: c["price"])["asin"],
                    min(others, key=lambda c: c["price"])["asin"]}
    for c in pts:
        is_me = c.get("asin") in asins
        ax.scatter(c["_x"], c["price"], s=190 if is_me else 90,
                   color=P["accent"] if is_me else P["steel"], alpha=1 if is_me else .5,
                   edgecolor="white", linewidth=1.6, zorder=3)
        if is_me or c.get("asin") in notable:
            # say "no reviews yet" outright rather than let a clamped point read as one review
            lab = c.get("brand", "")
            if is_me and c["reviewCount"] == 0:
                lab = f"{lab} (no reviews yet)".strip()
            ax.annotate(lab, (c["_x"], c["price"]),
                        textcoords="offset points", xytext=(10, 7),
                        fontsize=9.5 if is_me else 8,
                        fontweight="bold" if is_me else "normal",
                        color=P["ink"] if is_me else P["steel"], zorder=4)
    if mine:
        m = mine[0]
        cheaper = sum(1 for c in others if c["price"] < m["price"])
        fewer = sum(1 for c in others if c["reviewCount"] > m["reviewCount"])
        head = ("You are the most expensive listing with the fewest reviews"
                if cheaper == len(others) and fewer == len(others)
                else "Where you sit on price and social proof")
    else:
        head = "Price and social proof across the niche"
    _title(ax, P, head, "Every competitor in the niche. Top-left is the hardest place to sell from.")
    ax.set_xlabel("Ratings count", fontsize=9, color=P["steel"])
    ax.set_ylabel("Price", fontsize=9, color=P["steel"])
    ax.set_xscale("log")
    if any(c["reviewCount"] == 0 for c in pts):
        ax.set_xlim(left=0.55)          # keep a clamped 0-review marker off the spine
    _frame(ax, P)
    fig.tight_layout(); fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    return out


def _brand_name_leak(plt, P, cfg, kws, comps, asins, out):
    """Rank on the brand's highest-volume branded query, by seller. Lower is better, so
    the bar length reads as 'how far from the top you are' and a leaking brand owns the
    longest bar on its own name. Guarded on real branded demand."""
    branded = [k for k in kws if classify(cfg, k.get("keyword") or "") == "Branded"]
    if not branded:
        return None
    top = max(branded, key=lambda k: k.get("searchVolume") or 0)
    if (top.get("searchVolume") or 0) < MIN_BRAND_SV:
        return None
    ranks = top.get("asinRanks") or {}
    brand_of = {c["asin"]: (c.get("brand") or c["asin"]) for c in comps}

    best = {}                                  # one row per seller, best-ranking ASIN wins
    for asin, r in ranks.items():
        if r is None:
            continue
        b = brand_of.get(asin, asin)
        if b not in best or r < best[b][0]:
            best[b] = (r, asin)
    if len(best) < 3:
        return None
    rows = [dict(brand=b, rank=r, is_me=a in asins) for b, (r, a) in best.items()]
    rows.sort(key=lambda x: x["rank"])
    rows = rows[:9]
    if not any(r["is_me"] for r in rows):      # always show the client, even off the top 9
        mine = [dict(brand=brand_of.get(a, a), rank=ranks[a], is_me=True)
                for a in asins if ranks.get(a) is not None]
        if mine:
            rows.append(min(mine, key=lambda x: x["rank"]))

    fig, ax = plt.subplots(figsize=(9, 4.6))
    ys = list(range(len(rows)))[::-1]
    for y, r in zip(ys, rows):
        ax.barh(y, r["rank"], height=.62, color=P["accent"] if r["is_me"] else P["steel"],
                alpha=1 if r["is_me"] else .45, zorder=2)
        ax.text(r["rank"] + .25, y, str(r["rank"]), va="center", fontsize=9.5,
                fontweight="bold" if r["is_me"] else "normal",
                color=P["ink"] if r["is_me"] else P["steel"])
    ax.set_yticks(ys); ax.set_yticklabels([r["brand"] for r in rows], fontsize=9.5)
    for t, r in zip(ax.get_yticklabels(), rows):
        if r["is_me"]:
            t.set_color(P["accent"]); t.set_fontweight("bold")

    win = rows[0]
    me = next((r for r in rows if r["is_me"]), None)
    head = (f'{win["brand"]} ranks #{win["rank"]} on "{top["keyword"]}". You are {me["rank"]}th.'
            if me and not win["is_me"] else f'Organic rank on "{top["keyword"]}"')
    _title(ax, P, head, f'Your own brand name. {int(top.get("searchVolume") or 0):,} searches. '
                        f'Anything past rank 10 is page 2.')
    ax.set_xlabel("Organic rank (lower is better)", fontsize=9, color=P["steel"])
    _frame(ax, P, xgrid=True)
    fig.tight_layout(); fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    return out


def _focus(cfg):
    """Which product line the demand figures speak for.

    A multi-line catalogue makes an account-wide demand chart misleading: the biggest
    'winnable' term ends up being whichever line has the most search volume, even when
    the business barely sells there. `sqp_focus_group` names one entry in asin_groups
    and the figures then describe that line only, which is stated on the chart itself.
    Returns (group_name, {asins}) or (None, None) for the whole account."""
    g = cfg.get("sqp_focus_group")
    groups = cfg.get("asin_groups") or {}
    if not g or g not in groups:
        return None, None
    return g, {a.lower() for a in groups[g]}


def _sqp_segments(cfg):
    """Aggregate SQP into the four exclusive demand segments.
    Market metrics (search volume, total purchases) are counted ONCE per query+week;
    our purchases accumulate across every ASIN that appeared on that query, which is
    correct: several of our ASINs can sell on one query, but the market total for it
    is a single number."""
    from analyze_audit import classify_demand, DEMAND_SEGMENTS
    agg = {k: dict(sv=0.0, pt=0.0, pa=0.0, q=defaultdict(float), qa=defaultdict(float))
           for k in DEMAND_SEGMENTS}
    seen = set()
    fgroup, fasins = _focus(cfg)
    for _grp, path in (cfg["inputs"].get("sqp_csvs") or {}).items():
        if fgroup and _grp != fgroup:
            continue
        p = rp(path)
        if not p or not p.exists():
            continue
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            q = (r.get("Search Query") or "").strip()
            if not q:
                continue
            if fasins and (r.get("ASIN") or "").strip().lower() not in fasins:
                continue
            d = agg[classify_demand(cfg, q)]
            key = (q.lower(), r.get("Reporting Date"))
            if key not in seen:
                seen.add(key)
                sv = float(r.get("Search Query Volume") or 0)
                d["sv"] += sv
                d["q"][q.lower()] += sv          # for the on-chart example query
                d["pt"] += float(r.get("Purchases: Total Count") or 0)
            pa = float(r.get("Purchases: ASIN Count") or 0)
            d["pa"] += pa
            d["qa"][q.lower()] += pa
    return agg


def _example(agg, seg, width=26):
    """A real query from the segment, so the prospect can see what the bar MEANS.
    Prefer the highest-volume query the brand actually SELLS on: the plain volume
    leader can be a term the business has no presence in, which reads as a mislabel
    rather than an example. Derived from data, never typed, so it cannot drift."""
    d = agg.get(seg, {})
    sold = {k: v for k, v in (d.get("q") or {}).items() if (d.get("qa") or {}).get(k, 0) > 0}
    qs = sold or (d.get("q") or {})
    if not qs:
        return ""
    q = max(qs.items(), key=lambda kv: kv[1])[0]
    return q if len(q) <= width else q[: width - 1] + "\u2026"


def _scope_note(fig, cfg):
    """Say on the chart which line it describes, so a hero-line number is never read
    as an account-wide one."""
    g, _ = _focus(cfg)
    if not g:
        return
    fig.text(0.005, -0.06, f"We concentrated on the hero line: {g}.",
             fontsize=8.5, style="italic", color=_palette()["steel"], ha="left")


_SEG_LABELS = {
    "Branded": "Branded\n(your name)",
    "Competitor": "Competitor\n(their names)",
    "Core": "Generic: core\n(winnable)",
    "Head": "Generic: head\n(undifferentiated)",
}


def _demand_segments(plt, P, cfg, out):
    """GRAPH 1 — where the demand is, split so the winnable part is visible.
    The old two-way version folded competitor brands AND unwinnable head terms into
    one 'Generic' bar, which overstated the addressable category by an order of
    magnitude and made category share look far worse than it is."""
    from matplotlib.ticker import FuncFormatter
    from analyze_audit import DEMAND_SEGMENTS
    agg = _sqp_segments(cfg)
    if not any(agg[k]["sv"] for k in DEMAND_SEGMENTS):
        return None
    segs = [k for k in DEMAND_SEGMENTS if agg[k]["sv"] > 0]
    vals = [agg[k]["sv"] for k in segs]
    # Accent marks the segment the audit acts on; the rest is context.
    cols = [P["accent"] if k == "Core" else P["steel"] for k in segs]
    fig, ax = plt.subplots(figsize=(9, 3.6))
    labs = [f'{_SEG_LABELS[k]}\ne.g. "{_example(agg, k)}"' for k in segs]
    ax.bar(labs, vals, color=cols, width=0.6)
    for i, v in enumerate(vals):
        ax.text(i, v * 1.02, f"{v:,.0f}", ha="center", va="bottom", fontsize=10.5,
                fontweight="bold", color=P["ink"])
    ax.set_ylabel("Searches in the window", fontsize=9, color=P["steel"])
    ax.set_ylim(0, max(vals) * 1.18)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "0" if v == 0 else f"{v/1000:.0f}K"))
    _frame(ax, P, ygrid=True)
    core = agg["Core"]["sv"]; tot = sum(vals)
    # State the measurement, not a verdict: "Only X of Y" reads as a judgement and
    # inverts whenever the core segment turns out to be large.
    fig.suptitle(f"Winnable category demand is {core:,.0f} searches, "
                 f"{core/tot:.0%} of everything searched.",
                 fontsize=12.5, fontweight="bold", color=P["ink"], x=0.005, ha="left", y=1.04)
    _scope_note(fig, cfg)
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    return out


def _purchases_vs_market(plt, P, cfg, out):
    """GRAPH 2 — us against the market, on the SAME measure.
    Purchases both sides, so the comparison is like-for-like. Deliberately NOT a
    capture percentage per segment: origination biases branded and generic rates
    differently, so those rates are not comparable to each other. Counts are."""
    import numpy as np
    from matplotlib.ticker import FuncFormatter
    from analyze_audit import DEMAND_SEGMENTS
    agg = _sqp_segments(cfg)
    segs = [k for k in DEMAND_SEGMENTS if agg[k]["pt"] > 0]
    if not segs:
        return None
    mkt = [agg[k]["pt"] for k in segs]
    ours = [agg[k]["pa"] for k in segs]
    x = np.arange(len(segs)); w = 0.38
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.bar(x - w / 2, mkt, w, label="Market", color=P["steel"])
    ax.bar(x + w / 2, ours, w, label="You", color=P["accent"])
    for i, (m, o) in enumerate(zip(mkt, ours)):
        ax.text(i - w / 2, m, f"{m:,.0f}", ha="center", va="bottom", fontsize=9.5,
                fontweight="bold", color=P["ink"])
        share = (o / m * 100) if m else 0
        ax.text(i + w / 2, o, f"{o:,.0f}\n({share:.1f}%)", ha="center", va="bottom",
                fontsize=9.5, fontweight="bold", color=P["ink"])
    ax.set_xticks(x)
    ax.set_xticklabels([f'{_SEG_LABELS[k]}\ne.g. "{_example(agg, k)}"' for k in segs])
    ax.set_ylabel("Purchases in the window", fontsize=9, color=P["steel"])
    ax.set_ylim(0, max(mkt) * 1.22)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "0" if v == 0 else f"{v/1000:.0f}K"))
    ax.legend(frameon=False, fontsize=9, loc="upper right")
    _frame(ax, P, ygrid=True)
    ci = segs.index("Core") if "Core" in segs else None
    head = (f"On winnable category demand the market bought {agg['Core']['pt']:,.0f}. You sold {agg['Core']['pa']:,.0f}."
            if ci is not None else "Purchases: you against the market.")
    fig.suptitle(head, fontsize=12.5, fontweight="bold", color=P["ink"], x=0.005, ha="left", y=1.04)
    _scope_note(fig, cfg)
    fig.tight_layout()
    fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    return out


# ------------------------------------------------------------------ entry
def build(config_path, outdir) -> list:
    cfg = load_config(config_path)
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    P = _palette()
    try:
        plt = _setup(P)
    except Exception as e:
        print(f"[fig] skipped (no matplotlib: {e})")
        return []

    asins = _client_asins(cfg)
    made = []
    kws = comps = None
    kp = rp(cfg["inputs"].get("datadive_niche_json"))
    if kp and kp.exists():
        kws = json.loads(kp.read_text()).get("keywords") or None
    cp = rp(cfg["inputs"].get("datadive_competitors_json"))
    if cp and cp.exists():
        comps = json.loads(cp.read_text()).get("competitors") or None

    f = _rank_movement(plt, P, cfg, outdir / "fig_rank_movement.png")
    if f: made.append(f)

    if kws and asins:
        made.append(_rank_distribution(plt, P, cfg, kws, asins, outdir / "fig_rank_distribution.png"))
        if comps:
            f = _visibility_vs_competition(plt, P, cfg, kws, comps, asins,
                                           outdir / "fig_visibility_vs_competition.png")
            if f: made.append(f)
            f = _brand_name_leak(plt, P, cfg, kws, comps, asins,
                                 outdir / "fig_brand_name_leak.png")
            if f: made.append(f)
    if comps:
        f = _reviews_vs_price(plt, P, cfg, comps, asins, outdir / "fig_reviews_vs_price.png")
        if f: made.append(f)
    f = _demand_segments(plt, P, cfg, outdir / "fig_demand_segments.png")
    if f: made.append(f)
    f = _purchases_vs_market(plt, P, cfg, outdir / "fig_purchases_vs_market.png")
    if f: made.append(f)

    for m in made:
        print(f"[fig] wrote {Path(m).name}")
    if not made:
        print("[fig] no figures: DataDive/SQP inputs absent")
    return made


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    build(a.config, a.outdir)
