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
  fig_price_vs_rating.png          price against RATING, review count as bubble size,
                                   you highlighted. Replaces the old price-vs-review-count
                                   scatter: review count needed a log axis that rendered
                                   as 10^1..10^4 (unreadable to a non-technical audience),
                                   and a "social proof" chart that omitted the rating hid
                                   the number usually doing the damage. The client's price
                                   comes from config.client_price or Business Report ASP,
                                   NEVER from DataDive, which reports the Buy Box price.
                                   Optional config.client_dtc_price draws a reference line.
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
    # Mark the top-10 boundary, NOT a "page 2" line. Amazon's first results page runs to
    # about rank 48, so a divider at 20 labelled "page 2" states something untrue; what
    # actually matters is whether the keyword still sits in the band shoppers scroll.
    ax.axvline(10.5, color=P["hair"], lw=1, ls="--", zorder=1)
    ax.text(10.5, len(rows) - 0.4, " outside the top 10 ►", ha="left", fontsize=8.5, color=P["steel"])
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
    # Rank 1-4 is split out because it is the band that actually carries sales: it is what
    # fits above the fold on mobile. Lumping it into a single "top 10" hides the difference
    # between ranking 2nd and ranking 9th, which is most of the difference in the category.
    # Never label the first band "page 1" while showing 11-20 and 21-50 separately: Amazon's
    # first results page runs to about rank 48, so the page-1 total is bands 1 through 4.
    b = {"Rank\n1-4": 0, "Rank\n5-10": 0, "Rank\n11-20": 0, "Rank\n21-50": 0, "Rank\n51+": 0,
         "Not ranked\nat all": 0}
    for k in kws:
        r = _best_rank(k.get("asinRanks") or {}, asins)
        if r is None: b["Not ranked\nat all"] += 1
        elif r <= 4: b["Rank\n1-4"] += 1
        elif r <= 10: b["Rank\n5-10"] += 1
        elif r <= 20: b["Rank\n11-20"] += 1
        elif r <= 50: b["Rank\n21-50"] += 1
        else: b["Rank\n51+"] += 1
    labels, vals = list(b), list(b.values())
    fig, ax = plt.subplots(figsize=(9, 4.1))
    bars = ax.bar(labels, vals, color=[P["accent"], P["ink"]] + [P["steel"]] * 4, width=0.62)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + max(vals) * 0.02, f"{v}",
                ha="center", va="bottom", fontsize=10.5, fontweight="bold", color=P["ink"])
    # State the count, do not grade it. "Only 319 of 500" reads as a criticism of what is
    # often a strong result, and the narrative is where the verdict belongs. Headline the
    # 1-4 band, since that is the one that decides whether the ranking converts.
    _title(ax, P, f"You rank 1-4 for {vals[0]} of {len(kws)} category keywords, "
                  f"and 1-10 for {vals[0] + vals[1]}",
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


def _money(v, cfg):
    sym = "\u20ac" if (cfg.get("currency") or "USD").upper() in ("EUR", "\u20ac") else "$"
    return f"{sym}{v:,.0f}" if float(v).is_integer() else f"{sym}{v:,.2f}"


def _client_price(cfg, asins):
    """The client's REAL selling price, never DataDive's.

    DataDive reports the BUY BOX price. During a hijack or a stock-out that is a third
    party's price, so using it puts the client in the wrong place on a price chart. A
    live audit had the client plotted at $50 against a true $33.39, which turned them
    from the third most expensive listing into a lone outlier.

    Order: explicit `config.client_price`, else ASP derived from the Business Report
    (ordered product sales / units ordered), else None and the caller falls back with a
    printed warning."""
    v = cfg.get("client_price")
    if v:
        return float(v), "config client_price"
    p = rp((cfg.get("inputs") or {}).get("business_report_csv"))
    if p and p.exists():
        sales = units = 0.0
        for r in csv.DictReader(open(p, encoding="utf-8-sig")):
            if (r.get("(Child) ASIN") or "").strip().lower() in asins:
                try:
                    sales += float((r.get("Ordered Product Sales") or "0").replace(",", "").replace("$", ""))
                    units += float(r.get("Units Ordered") or 0)
                except ValueError:
                    continue
        if units:
            return sales / units, "Business Report ASP"
    return None, None


def _price_vs_rating(plt, P, cfg, comps, asins, out):
    """Price against RATING, with review count as bubble size.

    Replaces the old price-vs-review-count scatter, which had two problems for a
    prospect audience. Review count spans three orders of magnitude so the axis had to
    be logarithmic, and it rendered as 10^1..10^4, which is unreadable to anyone who is
    not already comfortable with logs. And a chart captioned "social proof" showed only
    review VOLUME, never the rating, which is usually the number actually hurting the
    listing. Moving count to bubble size removes the log axis entirely and frees both
    axes to be things anyone reads at a glance: stars and money."""
    from matplotlib.ticker import FuncFormatter
    pts = []
    for c in comps:
        pr, rt = c.get("price"), c.get("rating")
        if pr is None or pr <= 0 or rt is None or rt <= 0:
            continue
        pts.append(dict(c, reviewCount=c.get("reviewCount") or 0))
    if len(pts) < 3:
        return None

    own = [c for c in pts if c.get("asin") in asins]
    real, src = _client_price(cfg, asins)
    if own and real:
        if abs(own[0]["price"] - real) > 0.01:
            print(f"[fig] client price {own[0]['price']:.2f} from DataDive (Buy Box) "
                  f"replaced with {real:.2f} from {src}")
        for c in own:
            c["price"] = real
    elif own:
        print("[fig] WARN: using DataDive's price for the client. It is the BUY BOX price, "
              "so a hijack or stock-out will misplace them. Set config.client_price.")

    ratings = [c["rating"] for c in pts]
    med_p = sorted(c["price"] for c in pts)[len(pts) // 2]
    # Clip the view to where the field actually sits. One 1.0-rated listing on 3 reviews
    # would otherwise flatten the 4.0-4.5 cluster that carries the comparison; it stays
    # in the data and gets called out in the subtitle instead of distorting the axis.
    lo_view = min(r for r in ratings if r >= 3.0) if any(r >= 3.0 for r in ratings) else min(ratings)
    lo_view = min(lo_view, min([c["rating"] for c in own], default=lo_view))
    clipped = [c for c in pts if c["rating"] < lo_view - 0.001]
    shown = [c for c in pts if c not in clipped]

    def bub(n):
        return 60 + (float(n) ** 0.5) * 9        # area by sqrt so 30k does not swamp 300

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.axhline(med_p, color=P["hair"], lw=1.2, zorder=1)
    ax.annotate(f"category median {_money(med_p, cfg)}", (0.995, med_p),
                xycoords=("axes fraction", "data"), textcoords="offset points",
                xytext=(0, 5), ha="right", fontsize=8, color=P["steel"], zorder=2)
    # The website line only earns its place when the website charges something DIFFERENT.
    # When the two prices match it lands exactly on the client's own bubble, and its label
    # overprints whichever rival is nearest that price (Resilia 2026-07: "your own website
    # $29.99" straight through "Clean Nutraceuticals"). Same number, twice, plus a collision.
    dtc = cfg.get("client_dtc_price")
    amz = (own[0]["price"] if own else None)
    if dtc and not (amz is not None and abs(float(dtc) - amz) <= 0.01):
        ax.axhline(float(dtc), color=P["accent"], lw=1.1, ls="--", alpha=.55, zorder=1)
        ax.annotate(f"your own website {_money(float(dtc), cfg)}", (0.995, float(dtc)),
                    xycoords=("axes fraction", "data"), textcoords="offset points",
                    xytext=(0, 5), ha="right", fontsize=8, color=P["accent"], zorder=2)

    for c in shown:
        me = c.get("asin") in asins
        ax.scatter(c["rating"], c["price"], s=bub(c["reviewCount"]) * (1.5 if me else 1),
                   color=P["accent"] if me else P["steel"], alpha=1 if me else .45,
                   edgecolor="white", linewidth=1.5, zorder=3)
    # Label the client plus the extremes that carry the argument. Labelling everything collides.
    others = [c for c in shown if c.get("asin") not in asins]
    notable = set()
    if others:
        notable |= {max(others, key=lambda c: c["price"])["asin"],
                    max(others, key=lambda c: c["rating"])["asin"],
                    max(others, key=lambda c: c["reviewCount"])["asin"]}
        if own:
            notable |= {c["asin"] for c in others if c["price"] >= own[0]["price"]}
    for c in shown:
        me = c.get("asin") in asins
        if not (me or c.get("asin") in notable):
            continue
        lab = c.get("brand", "")
        if me:
            lab = f"{lab}\n{c['rating']:.1f}\u2605 · {_money(c['price'], cfg)} · {c['reviewCount']:,.0f} ratings"
        # Rivals label above-right, the client BELOW its bubble. A rival on the same
        # rating sits within a few points of the client and the two labels overprinted.
        ax.annotate(lab, (c["rating"], c["price"]), textcoords="offset points",
                    xytext=(14, -34) if me else (12, 9),
                    fontsize=9.5 if me else 8,
                    fontweight="bold" if me else "normal",
                    color=P["ink"] if me else P["steel"], zorder=4)

    ax.set_xlabel("Customer rating (stars)", fontsize=9, color=P["steel"])
    ax.set_ylabel("Price", fontsize=9, color=P["steel"])
    ax.set_xlim(lo_view - 0.18, max(ratings) + 0.28)
    # Bubbles are sized in points, so matplotlib's data-range autoscale does not know how
    # tall they are and slices the biggest one flat against the top spine -- which is
    # always the client's, since their marker is drawn 1.5x. Add headroom explicitly.
    prices = [c["price"] for c in shown] + ([float(dtc)] if dtc else [])
    lo_p, hi_p = min(prices), max(prices)
    pad = max((hi_p - lo_p) * 0.12, 1.0)
    ax.set_ylim(lo_p - pad, hi_p + pad)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.1f}\u2605"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _money(v, cfg)))

    sub = "Bubble size is the number of ratings."
    if clipped:
        names = ", ".join(sorted({c.get("brand", "?") for c in clipped}))
        sub += f" {names} sits below {lo_view:.1f}\u2605 and is off the scale here."
    if own:
        m = own[0]
        cheaper = sum(1 for c in others if c["price"] < m["price"])
        better = sum(1 for c in others if c["rating"] > m["rating"])
        head = (f"You charge more than {cheaper} of {len(others)} rivals "
                f"and are rated below {better} of them.")
    else:
        head = "Price against rating across the niche"
    _title(ax, P, head, sub)
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
    # Do NOT claim rank 10 is the page break: page 1 runs to about rank 48 (see
    # _rank_distribution). Say what is true and what matters, which is how many rivals
    # sit on page 1 of the brand's OWN name. Count it rather than asserting it: the
    # chart routinely includes a brand past rank 48, and "every brand shown here sits
    # on page 1" is then simply false.
    on_p1 = sum(1 for r in rows if r["rank"] <= 48 and not r["is_me"])
    tail = (f'{on_p1} other brands sit on page 1 of it alongside you.' if on_p1
            else 'No other brand reaches page 1 of it.')
    _title(ax, P, head, f'Your own brand name. {int(top.get("searchVolume") or 0):,} searches. {tail}')
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
        f = _price_vs_rating(plt, P, cfg, comps, asins, outdir / "fig_price_vs_rating.png")
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
