#!/usr/bin/env python3
"""Measure how well ask.py finds the right source for real questions.

  python3 tools/knowledge/ask_eval.py --build [--count 30]   # sample questions from the sweep cards
  python3 tools/knowledge/ask_eval.py --run [--top 3]        # run them and print hit rates

The question bank is gitignored (`_local/knowledge-sweep/ask-eval-questions.json`):
each entry holds a card's question as asked and the repo paths that card cites
(owning skills, coverage and first-party paths that still exist). A question
counts as a hit when any expected path is among the top N hits of any layer, or
when the card's own unit (same card id in the unit provenance) is in the unit
layer. The bank samples evenly across topics by sorted card id, so reruns are
comparable.
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ask  # noqa: E402

ROOT = ask.WORKSPACE_ROOT
STORE = ROOT / "_local" / "knowledge-sweep"
BANK = STORE / "ask-eval-questions.json"


def build(count: int) -> list[dict]:
    cards = []
    for path in sorted((STORE / "cards" / "candidate").glob("CARD-*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        question = (card.get("problem_as_asked") or "").strip()
        if not question:
            continue
        expected = set()
        for skill in card.get("skills") or []:
            p = f"skills/{skill}/SKILL.md"
            if (ROOT / p).exists():
                expected.add(p)
        for field in ("coverage_paths", "first_party_source_paths", "related_sop_paths"):
            for p in card.get(field) or []:
                if isinstance(p, str) and (ROOT / p).exists():
                    expected.add(p)
        if not expected:
            continue
        cards.append({"card_id": card["card_id"], "topic": card.get("topic"), "question": question, "expected": sorted(expected)})
    by_topic: dict[str, list[dict]] = collections.defaultdict(list)
    for c in cards:
        by_topic[c["topic"]].append(c)
    picked: list[dict] = []
    topics = sorted(by_topic)
    while len(picked) < count and any(by_topic.values()):
        for t in topics:
            if by_topic[t] and len(picked) < count:
                picked.append(by_topic[t].pop(0))
    return picked


def run(top: int) -> dict:
    bank = json.loads(BANK.read_text(encoding="utf-8"))
    per_layer = {k: top for k in ask.DEFAULT_PER_LAYER}
    rows = []
    for q in bank:
        result = ask.answer(q["question"], ROOT, per_layer)
        found_in = []
        for layer, hits in result["layers"].items():
            paths = {h["path"] for h in hits}
            if any(p in paths for p in q["expected"]):
                found_in.append(layer)
        rows.append({"card_id": q["card_id"], "topic": q["topic"], "hit": bool(found_in), "layers": found_in, "expected": q["expected"]})
    hits = sum(1 for r in rows if r["hit"])
    by_topic = collections.defaultdict(lambda: [0, 0])
    for r in rows:
        by_topic[r["topic"]][1] += 1
        by_topic[r["topic"]][0] += int(r["hit"])
    return {"questions": len(rows), "hits": hits, "top": top, "by_topic": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_topic.items())}, "misses": [r for r in rows if not r["hit"]]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--count", type=int, default=30)
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args(argv)
    if args.build:
        bank = build(args.count)
        BANK.write_text(json.dumps(bank, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"built {len(bank)} questions into {BANK}")
    if args.run:
        result = run(args.top)
        print(f"hit@{result['top']}: {result['hits']}/{result['questions']} | by topic: {result['by_topic']}")
        for miss in result["misses"]:
            print(f"  miss {miss['card_id']} ({miss['topic']}): expected {', '.join(miss['expected'])[:160]}")
    if not (args.build or args.run):
        parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
