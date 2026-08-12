#!/usr/bin/env python3
"""
Amazon Ad/Sales Audit narrative scaffold generator.
Emits a Markdown draft following skills/amazon-audit/SKILL.md's section skeleton.
The standard mode leaves operator prompts around pre-filled KPIs. The evidence-hybrid
mode writes concise claims, evidence, and actions automatically so it can be rendered
without a manual placeholder pass.
Honors config.narrative flags (include_levers, include_30day_plan, include_what_can_be_reached).
For compatibility, include_levers now controls the combined "Problems and Solutions" section.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from branding import load_branding as _load_branding
from analyze_audit import blended_metrics_available, blended_metrics_reason


def _prepared_by_org():
    return _load_branding({}).get("agency_name") or "the operator"


def _m(v, cur):
    sym = "€" if cur in ("EUR", "€") else "$"
    return f"{sym}{v:,.0f}"


# Standard figure set from build_figures.py. Referenced only when the file exists, so a
# run without DataDive/SQP (or without matplotlib) still emits a clean scaffold.
FIGURES = {
    "fig_rank_distribution.png":
        "Organic rank across the category keyword set. Rank 1-4 is what sells; page 1 runs to rank 48.",
    "fig_visibility_vs_competition.png":
        "Share of category search volume where each seller ranks in the top 10.",
    "fig_price_vs_rating.png":
        "Price against rating. Bubble size is the number of ratings.",
    "fig_demand_segments.png":
        "Where the demand is, split so the winnable part is visible.",
    "fig_purchases_vs_market.png":
        "Purchases, you against the market, on the same measure.",
    "fig_brand_name_leak.png":
        "Organic rank on the brand's own name. Anything past rank 10 is page 2.",
}


def _fig(outdir, name):
    """Markdown image line for a figure that was actually produced, else None."""
    return f"![{FIGURES[name]}]({name})\n" if (Path(outdir) / name).exists() else None


def _evidence(outdir, section):
    """Selected screenshot lines for one narrative section."""
    manifest = Path(outdir) / "evidence_manifest.json"
    if not manifest.exists():
        return []
    rows = json.loads(manifest.read_text()).get("selected", [])
    return [f"![{row['caption']}]({row['path']})\n" for row in rows if row.get("section") == section]


def _market_sizing(cfg):
    path = (cfg.get("inputs", {}) or {}).get("market_sizing_json")
    if not path:
        return None
    q = Path(path).expanduser()
    if not q.is_absolute():
        q = Path(__file__).resolve().parents[2] / q
    return json.loads(q.read_text()) if q.exists() else None


def _hybrid_summary(cfg, totals, searchterm_bucket, channels, currency):
    comparison = cfg.get("comparison_windows", {}) or {}
    disruption = comparison.get("disruption")
    control = comparison.get("online_control")
    note = (cfg.get("inputs", {}) or {}).get("ads_bulk_source_note", "")
    parts = []
    if disruption and control:
        parts.append(
            f"The required observation window ({disruption}) is disrupted, so it is not a clean "
            f"commercial baseline. The latest clean online control is {control}."
        )
    if totals.get("br_total_sales", 0):
        # "The control data" only exists when a separate online-control window does.
        source = "In the control data" if control else "In the window"
        parts.append(
            f"{source}, the product produced {_m(totals['br_total_sales'], currency)} "
            f"in ordered-product sales from {totals.get('br_sessions', 0):,.0f} sessions."
        )
    if searchterm_bucket:
        branded = searchterm_bucket.get("Branded", {})
        generic = searchterm_bucket.get("Generic", {})
        if branded or generic:
            b = branded.get("spend", 0)
            g = generic.get("spend", 0)
            total = totals.get("spend", 0) or 1
            parts.append(
                f"The available ad snapshot allocates {b / total:.0%} of spend to branded terms and "
                f"{g / total:.0%} to generic terms."
            )
    if note:
        parts.append(f"Advertising conclusions remain directional: {note}")
    elif channels:
        parts.append(f"The available advertising data contains {', '.join(channels)}.")
    return " ".join(parts)


def _hybrid_findings(cfg, totals, searchterm_bucket, placements, claims, sqp_demand):
    findings = []
    comparison = cfg.get("comparison_windows", {}) or {}
    # Relaunch language belongs to an incident audit. On a trading account it narrates a
    # problem the client does not have, so every use of it is gated on this one flag.
    relaunching = bool(comparison.get("disruption"))
    if comparison.get("disruption") and comparison.get("online_control"):
        findings.append({
            "claim": "Availability is the first constraint, not advertising efficiency",
            "evidence": [
                f"The observation window is {comparison['disruption']}.",
                f"The clean online control is {comparison['online_control']}.",
                comparison.get("note", "The two windows must remain separate."),
            ],
            "comparison": "The disrupted window cannot be graded against a normal trading baseline.",
            "decision": "Restore and verify the listing before using paid-media changes as a growth test.",
        })

    for row in claims:
        reason = _claim_reason(row)
        if not reason:
            continue
        claim = row.get("claim", "Call statement")
        findings.append({
            "claim": claim,
            "evidence": [f"Verdict: {row.get('verdict', 'Not verifiable from available data')}.", reason],
            "comparison": "The verdict follows the audit's same-query or source-specific comparison method.",
            "decision": (
                "Do not use this claim as the basis for a recommendation."
                if row.get("verdict") == "Not supported"
                else ("Carry this conclusion into the relaunch plan." if relaunching
                      else "Carry this conclusion into the recommendation it affects.")
            ),
        })

    if searchterm_bucket and len(findings) < 4:
        total_spend = totals.get("spend", 0) or 1
        generic = searchterm_bucket.get("Generic", {})
        branded = searchterm_bucket.get("Branded", {})
        findings.append({
            "claim": "The available ad snapshot includes both branded and non-branded demand",
            "evidence": [
                f"Generic terms represent {generic.get('spend', 0) / total_spend:.0%} of captured spend.",
                f"Branded terms represent {branded.get('spend', 0) / total_spend:.0%} of captured spend.",
            ],
            "comparison": "The snapshot is too short for campaign grades, but it is enough to reject an absolute claim that non-branded advertising is absent.",
            "decision": ("Rebuild the full-window export after relaunch, then grade structure and efficiency against confirmed margin."
                         if relaunching else
                         "Grade structure and efficiency on the full-window export against confirmed margin."),
        })

    if sqp_demand and len(findings) < 4:
        core = sqp_demand.get("Core", {})
        if core:
            findings.append({
                "claim": "The useful growth pool is the winnable core, not the category headline",
                "evidence": [
                    f"Core demand averages {core.get('avg_wk_sv', 0):,.0f} searches a week.",
                    f"The product captures {core.get('capture', 0):.1%} of measured core purchases.",
                ],
                "comparison": "Head terms are real demand, but they are too broad to treat as one listing's addressable market.",
                "decision": ("Build the relaunch around the strongest core terms and measure query-level share movement."
                             if relaunching else
                             "Concentrate spend on the strongest core terms and measure query-level share movement."),
            })
    return findings[:5]


def _hybrid_priorities(cfg, totals, placements, channels, missing_channels):
    priorities = []
    comparison = cfg.get("comparison_windows", {}) or {}
    relaunching = bool(comparison.get("disruption"))
    if comparison.get("disruption"):
        priorities.append((
            "Restore the retail foundation",
            "Resolve suppression or availability, confirm the live PDP and Buy Box, then restart measurement.",
            f"The required window {comparison['disruption']} is disrupted.",
            "Daily sessions, purchasable status, Buy Box, and stock.",
        ))
    if placements:
        best = min(placements.items(), key=lambda item: item[1].get("acos") if item[1].get("acos") is not None else 999)
        worst = max(placements.items(), key=lambda item: item[1].get("acos") if item[1].get("acos") is not None else -1)
        priorities.append((
            "Rebalance placements after the listing is live" if relaunching else "Rebalance the placements",
            f"Protect {best[0]} where efficiency is strongest and reduce exposure to {worst[0]} until it proves incremental value.",
            f"Available ACOS ranges from {(best[1].get('acos') or 0):.1%} to {(worst[1].get('acos') or 0):.1%} by placement.",
            "Placement ACOS and incremental ordered sales against confirmed break-even ACOS.",
        ))
    priorities.append((
        "Use the listing as the conversion control",
        "Rebuild the gallery and A+ around the winning use case, proof, product facts, and objection handling before scaling generic traffic.",
        "The live-creative comparison and category evidence show what shoppers see at the decision point.",
        "Unit session percentage, click-to-cart, cart-to-purchase, and controlled experiment lift.",
    ))
    priorities.append((
        "Win a narrow generic wedge",
        "Separate branded protection, competitor terms, winnable core queries, and undifferentiated head terms.",
        "SQP separates where demand exists from where the product actually captures purchases.",
        "Purchase share and organic rank on the selected core query set.",
    ))
    if missing_channels:
        priorities.append((
            f"Test the missing formats: {', '.join(missing_channels)}",
            f"Add only the formats that match a clear job in the {'relaunch ' if relaunching else ''}funnel.",
            f"The available data contains {', '.join(channels)} and no measured {', '.join(missing_channels)} activity.",
            "Incremental reach, new-to-brand contribution where available, and blended ACOS.",
        ))
    return priorities[:5]


def _i_would(action):
    """Turn an imperative action into spoken first-person recommendation copy."""
    action = action.strip()
    if not action:
        return "I would define the next action after confirming the evidence."
    return "I would " + action[0].lower() + action[1:]


def _priority_section_blocks(hybrid, priorities=(), missing_channels=()):
    """Render one findings-and-actions section for standard and hybrid deep audits."""
    blocks = ["## Problems and Solutions\n"]
    if hybrid:
        for n, (title, action, evidence, measure) in enumerate(priorities, 1):
            blocks.append(f"### Priority {n}: {title}")
            blocks.append(evidence)
            blocks.append(f"{_i_would(action)} Measure {measure[0].lower() + measure[1:]}\n")
    else:
        blocks.append("<!-- operator: use 5-7 action-led priorities. Give each one short diagnosis, one evidence sentence, and one sentence beginning 'I would'. Do not repeat the diagnosis elsewhere. -->\n")
        for n in range(1, 6):
            blocks.append(f"### Priority {n}: <!-- action-led title -->")
            blocks.append("<!-- Short diagnosis and evidence. I would ... -->\n")
        if missing_channels:
            blocks.append("### Priority 6: <!-- add only the missing formats that have a clear job -->")
            blocks.append(f"<!-- Evidence: no measured {', '.join(missing_channels)} activity. I would ... -->\n")
    blocks.append("---\n")
    return blocks


def _market_decision(product):
    bench = product.get("benchmark", {}) or {}
    coverage = product.get("coverage", {}) or {}
    demand = coverage.get("exact_relevancy_weekly_equivalent", 0)
    reviews = bench.get("median_reviews", 0)
    if reviews >= 10000:
        return (
            "Large demand, but a heavy review moat. Treat this as the harder launch and require a sharply differentiated position before committing inventory."
        )
    if demand >= 50000:
        return (
            "Meaningful directional demand with a more workable moat. Validate compliance, unit economics, and a defendable core-term position before launch."
        )
    return "Keep this as a secondary test until demand coverage and a differentiated position are stronger."


def build(config_path, outdir, force=False):
    from analyze_audit import load_config

    cfg = load_config(config_path)
    outdir = Path(outdir)
    M = json.loads((outdir / "metrics.json").read_text())
    SS = json.loads((outdir / "clean" / "sqp_summary.json").read_text()) if (outdir / "clean" / "sqp_summary.json").exists() else {}
    SD = json.loads((outdir / "clean" / "sqp_demand.json").read_text()) if (outdir / "clean" / "sqp_demand.json").exists() else {}
    cur = M.get("currency", "USD"); T = M["totals"]; STB = M["searchterm_bucket"]; P = M["placement"]
    BE = M.get("breakeven", 0.50); CLIENT = M.get("client", "Client")
    markets = ", ".join(M.get("marketplaces", []) or [])
    channels = M.get("channels_present", ["SP"]); miss = [c for c in ("SB", "SD") if c not in channels]
    win = M.get("windows", {}); nflags = cfg.get("narrative", {})
    hybrid = nflags.get("mode") == "evidence_hybrid"
    L = []
    A = L.append

    A(f"# {CLIENT}: {markets} Amazon Advertising & Sales Audit\n")
    voice_guide = (cfg.get("inputs", {}) or {}).get("voice_guide_path")
    if voice_guide:
        A(f"<!-- writing authority: {voice_guide} -->")
    A(f"**Prepared by {_prepared_by_org()} · Marketplace: {markets} · Window: {win.get('ads','')}**\n")
    A(f"**Sources:** Ads bulk ({win.get('ads','')}), Business Report ({win.get('business_report','')}), "
      f"SQP ({len(win.get('sqp_weeks',[]))} weekly snapshots), DataDive niche {cfg.get('datadive_niche','')}.\n")
    A(f"> **Break-even ACOS = {BE:.0%} is an ASSUMPTION** pending confirmed margin. Every red/amber verdict keys off it.\n")
    A("---\n")

    # ---- Ads Summary ----
    windows_match = blended_metrics_available(M)
    organic = T.get("organic_implied")
    A("## Ads Summary\n")
    if hybrid:
        A(_hybrid_summary(cfg, T, STB, channels, cur) + "\n")
    else:
        A("<!-- operator: 2-3 sentences on what's really going on. Lead with the branded-carries / generic-bleeds tension and the capture wall. -->\n")
    A("| Metric | Value |")
    A("|---|---|")
    A(f"| Ad spend | {_m(T['spend'],cur)} |")
    A(f"| Ad sales | {_m(T['sales'],cur)} |")
    A(f"| **Ad ACOS** | **{T['acos']:.1%}** |")
    A(f"| Business Report sales | {_m(T['br_total_sales'],cur)} |")
    if windows_match:
        A(f"| Organic / non-ad sales (implied) | {_m(organic,cur)} |")
        A(f"| **TACOS** | **{T['tacos']:.1%}** |")
        A(f"| Ad-attributed share | {T['ad_attributed_share']:.1%} |")
        A(f"| **Ad : organic** | **{T['ad_dependency']*100:.0f} : {(1-T['ad_dependency'])*100:.0f}**"
          + (f" ({T['sales']/organic:.2f} : 1)" if organic else "") + " |")
    else:
        for label in ("Organic / non-ad sales (implied)", "TACOS", "Ad-attributed share", "Ad : organic"):
            A(f"| {label} | N/A |")
        A(f"\n*{blended_metrics_reason(M)} Blended Ads and Business Report KPIs are not reported.*")
    A("")
    A("### Traffic mix (by customer search term)\n")
    A("| Bucket | Spend | % spend | Sales | ACOS | CVR |")
    A("|---|---|---|---|---|---|")
    for b in ("Branded", "Generic", "Competitor"):
        d = STB.get(b)
        if not d:
            continue
        A(f"| {b} | {_m(d['spend'],cur)} | {d['spend']/T['spend']:.0%} | {_m(d['sales'],cur)} | {(d['acos'] or 0):.0%} | {d['cvr']:.1%} |")
    A("")
    for visual in _evidence(outdir, "summary"):
        A(visual)
    A("---\n")

    # ---- Current Account Performance ----
    A("## Current Account Performance\n")
    A("### Business Report by ASIN\n")
    A("| ASIN | Group | Sessions | Units | Sales | Buy Box |")
    A("|---|---|---|---|---|---|")
    for d in sorted(M["business_report"]["rows"], key=lambda x: -x["sales"]):
        A(f"| {d['asin']} | {d['group']} | {d['sessions']:,} | {d['units']} | {_m(d['sales'],cur)} | {d['buybox']:.0%} |")
    A("")
    if hybrid:
        br_sessions = sum(row.get("sessions", 0) for row in M["business_report"]["rows"])
        br_units = sum(row.get("units", 0) for row in M["business_report"]["rows"])
        cvr = br_units / br_sessions if br_sessions else 0
        control = (cfg.get("comparison_windows", {}) or {}).get("online_control")
        source = "in the control data" if control else "in the window"
        after = " to protect after the listing returns" if control else " to hold"
        A(f"The product generated {br_units:,.0f} units from {br_sessions:,.0f} sessions {source}, a {cvr:.1%} unit-session rate. This is the performance baseline{after}.\n")
    else:
        A("<!-- operator: one-line read-through: which line carries revenue, $0 ASINs, CVR health. -->\n")
    for visual in _evidence(outdir, "performance"):
        A(visual)
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
        # Four-way where core_tokens exist, three-way otherwise. Never present a bare
        # branded-vs-generic split: it measures the client's share against a market that
        # includes head terms no listing wins, and the figures beside it are already
        # four-way, so the table would contradict its own charts.
        LABEL = {"Branded": "Branded (your name)", "Competitor": "Competitor (their names)",
                 "Core": "Generic: core (winnable)", "Head": "Generic: head (undifferentiated)"}
        rows, src = (list(SD.items()), SD) if SD else ([(b, SS[b]) for b in ("Branded", "Generic", "Competitor") if b in SS], SS)
        A("| Segment | Queries | Avg weekly SV | SV share | Purchases in a typical week: you vs market |")
        A("|---|---|---|---|---|")
        for key, s in rows:
            A(f"| {LABEL.get(key, key)} | {s['queries']} | {s['avg_wk_sv']:,.0f} | {s['sv_share']:.1%} "
              f"| {s['brand_purch']:,} of {s['mkt_purch']:,} ({s['capture']:.1%}) |")
        A("")
        if SD and "Core" in SD and "Head" in SD:
            A("All product groups, every figure an average week. The charts below narrow to the "
              "hero line, so their totals are a subset of this table.\n")
            # WHY the head row is excluded from the opportunity, in the client's own keywords.
            # This paragraph is pre-filled rather than left as a stub because the operator has to
            # be able to say it out loud on the call. Quoting a share of the WHOLE category
            # invites the reader to believe the remainder is available to them; it is not, and if
            # nobody says so the lead walks away with a number twice its real size.
            core, head = SD["Core"], SD["Head"]
            both_sv = core["avg_wk_sv"] + head["avg_wk_sv"]
            ex_c = f' such as "{core["example"]}"' if core.get("example") else ""
            ex_h = f' such as "{head["example"]}"' if head.get("example") else ""
            A(f"**Why we split the category in two, rather than quoting one number.** Core is the "
              f"language somebody uses when they are shopping for what you sell{ex_c}. Head is the "
              f"browsing layer above it{ex_h}: real demand, genuinely searched, but no single "
              f"listing ever wins it.")
            A(f"Both are true numbers. The problem is what a combined figure implies. If we told you "
              f"you hold {(core['brand_purch'] + head['brand_purch']) / (core['mkt_purch'] + head['mkt_purch']):.1%} "
              f"of a {both_sv:,.0f}-search category, you would reasonably read the rest as available "
              f"to you. It is not. The share you can actually compete for is the core, "
              f"{core['avg_wk_sv']:,.0f} searches a week, which is "
              f"{both_sv / core['avg_wk_sv']:.1f}x smaller than the headline. Every target and every "
              f"projection in this document is set against the core, not the combined figure.\n")
            A("Where we drew that line is our judgement, from a keyword list we can show you. If you "
              "think a term sits on the wrong side, say so and the number moves.\n")
        for f in filter(None, [_fig(outdir, "fig_demand_segments.png"),
                               _fig(outdir, "fig_purchases_vs_market.png"),
                               _fig(outdir, "fig_brand_name_leak.png")]):
            A(f)
        for visual in _evidence(outdir, "demand"):
            A(visual)
        if hybrid:
            core = SD.get("Core", {}) if SD else {}
            if core:
                A(f"The commercial question is not whether category demand exists. It is whether the listing can win more of the {core.get('avg_wk_sv', 0):,.0f} weekly searches in the winnable core. Branded and generic capture remain separate comparisons because each starts from a different demand source.\n")
        else:
            A("<!-- operator: the capture number is the story: category demand is large but unconverted. CTR-vs-CVR wall. -->\n")
            A("<!-- operator: never read branded capture against generic capture. Origination biases them "
              "differently, so each is only meaningful against the market on its own query type. -->\n")
            A("<!-- operator: if the brand-leak chart rendered, somebody else is monetising demand this brand "
              "is paying to create. That usually outranks every optimisation lever. -->\n")
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
        for f in filter(None, [_fig(outdir, "fig_rank_distribution.png"),
                               _fig(outdir, "fig_visibility_vs_competition.png"),
                               _fig(outdir, "fig_price_vs_rating.png")]):
            A(f)
        for visual in _evidence(outdir, "organic") + _evidence(outdir, "datadive"):
            A(visual)
        if hybrid:
            crosser = "the relaunch has" if (cfg.get("comparison_windows", {}) or {}).get("disruption") else "the listing has"
            A(f"Price, rating, and review count set the trust threshold {crosser} to cross. A claimed strength only counts when the live competitor set does not make the same claim or show the same proof.\n")
        else:
            A("<!-- operator: frame the price/review moat: is the client a premium outlier? what does that do to generic conversion? -->")
            A("<!-- operator: uniqueness test (playbook check 4): before crediting any strength, confirm the competitors do not have it too. -->\n")
        A("---\n")

    # ---- Combined findings and actions ----
    # Keep the legacy include_levers flag as the compatibility switch for this section.
    if nflags.get("include_levers", True):
        priorities = _hybrid_priorities(cfg, T, P, channels, miss) if hybrid else ()
        for block in _priority_section_blocks(hybrid, priorities, miss):
            A(block)
        for visual in _evidence(outdir, "findings"):
            A(visual)

    # The call-claim matrix stays internal. Integrate only conclusions that materially
    # change a diagnosis or recommendation into the relevant section. Never render a
    # separate call-validation recap.

    if nflags.get("include_30day_plan", False):
        A("## Recommended 30-day plan\n")
        if hybrid:
            A("- **Days 1–7:** restore and verify the listing, Buy Box, stock, and compliance state.")
            A("- **Days 8–14:** launch the revised listing and narrow query structure with controlled budgets.")
            A("- **Days 15–21:** read SQP, Search Catalog Performance, placements, and organic rank together.")
            A("- **Days 22–30:** keep the proven terms and placements, cut weak traffic, and document the next test.\n")
        else:
            A("<!-- operator: only include if the client wants a week-by-week action plan. -->\n")
        A("---\n")
    if nflags.get("include_what_can_be_reached", False):
        A("## What can be reached\n")
        if hybrid and (cfg.get("comparison_windows", {}) or {}).get("disruption"):
            # Relaunch framing belongs to an incident audit only. On a healthy account it
            # describes a problem the client does not have.
            A("The audit supports a staged relaunch target, not a revenue promise. Exact scale and campaign grades remain conditional on confirmed contribution margin, restored availability, and enough post-relaunch data to separate listing lift from traffic mix.\n")
        elif hybrid:
            A("The audit supports a directional target, not a revenue promise. Exact scale and campaign grades remain conditional on confirmed contribution margin and on enough post-change data to separate listing lift from traffic mix.\n")
        else:
            A("<!-- operator: directional outcomes; exact once margin is confirmed. -->\n")
        A("---\n")

    # Compact directional launch appendix. It is deliberately separate from the
    # audited ASIN and never framed as client actuals or a forecast.
    market_sizing = _market_sizing(cfg)
    if market_sizing and market_sizing.get("products"):
        A("## Directional market appendix: the two next products\n")
        A("This is a market check, not a sales forecast. DataDive estimates category demand and competitor performance. It does not tell us what UltimaPeak will sell.\n")
        for product in market_sizing["products"]:
            cov = product.get("coverage", {})
            bench = product.get("benchmark", {})
            A(f"### {product['product']}")
            A(f"- **Relevant demand:** about {cov.get('exact_relevancy_weekly_equivalent', 0):,.0f} searches a week across the exact-relevancy keyword set.")
            terms = product.get("winnable_core_terms", [])[:5]
            if terms:
                A("- **Core terms:** " + ", ".join(f"{x['keyword']} ({x['monthly_search_volume']:,.0f}/month)" for x in terms) + ".")
            A(f"- **Commercial benchmark:** median price {_m(bench.get('median_price', 0), cur)}, rating {bench.get('median_rating', 0):.1f}, and {bench.get('median_reviews', 0):,.0f} reviews. DataDive estimates median 30-day competitor revenue at {_m(bench.get('median_estimated_revenue_30d', 0), cur)}.")
            A(f"- **Rankability:** {product.get('competitor_strength', '')}")
            A(f"**Decision:** {_market_decision(product)}\n")
            A(f"*Coverage note: {product.get('coverage_caveat', '')} Fresh as of {product.get('latest_research_date', '')[:10]}.*\n")
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
    if windows_match:
        A("- **Ad-vs-organic** is derived from aligned source windows (total minus ad-attributed).")
    else:
        A(f"- **Window alignment:** {blended_metrics_reason(M)} TACOS, implied organic sales, ad-attributed share, and ad-to-organic ratio are N/A.")
    A("- **SQP** SV deduped per query+week; multi-ASIN exports cap the grid (SV is a floor).\n")

    md = "\n".join(L)
    out = outdir / f"{_slug(CLIENT)}_{_slug(markets)}_Sales_Audit_SCAFFOLD.md"
    # Do NOT clobber an authored narrative. The documented workflow is "write the prose into
    # the pre-filled scaffold, then re-run the build to regenerate the branded .docx",
    # which every rebuild would otherwise silently destroy. A file still carrying the
    # `<!-- operator:` prompts is untouched boilerplate and is safe to regenerate; once those
    # are gone somebody has written into it. Pass force=True (or delete the file) to override.
    if out.exists() and "<!-- operator:" not in out.read_text() and not force:
        print(f"[narrative] KEPT authored {out.name} (no operator markers left; not regenerating). "
              f"Delete it or pass --force-scaffold to rebuild the boilerplate.")
        return out
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
    build(sys.argv[1], sys.argv[2], force="--force-scaffold" in sys.argv)
