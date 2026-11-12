#!/usr/bin/env python3
"""Portable mechanical checks for a complete Sponsored Brands Video briefing."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


FORBIDDEN_BRIEF = (
    "claims and compliance (advisory)",
    "how angle tests are measured",
    "break-even acos",
    "break even acos",
)
FORBIDDEN_REFERENCE = FORBIDDEN_BRIEF + ("stage 1", "stage 2")


def briefing_options(cfg: dict | None) -> tuple[str, int | None]:
    """Absent options retain the old three-angle concept-testing contract."""
    options = (cfg or {}).get("briefing", {})
    if options is None:
        options = {}
    if not isinstance(options, dict):
        raise ValueError("briefing must be an object")
    mode = options.get("mode", "concept_testing")
    if mode not in ("production", "concept_testing"):
        raise ValueError("briefing.mode must be production or concept_testing")
    cuts = options.get("requested_cuts")
    if cuts is not None and (type(cuts) is not int or cuts < 1):
        raise ValueError("briefing.requested_cuts must be a positive integer")
    if mode == "production" and cuts is None:
        raise ValueError("production briefing requires briefing.requested_cuts")
    return mode, cuts


def table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def script_cards(text: str, label: str) -> list[tuple[str, float, float, str]]:
    """Read the fixed editor table, without confusing translation/asset tables."""
    cards = []
    in_script = False
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            in_script = False
            continue
        cells = table_cells(line)
        if [cell.lower() for cell in cells] == ["card", "time", "on-screen text (final)", "visual direction"]:
            in_script = True
            continue
        if not in_script or all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if len(cells) != 4 or not all(cells):
            raise ValueError(f"{label}: every card needs id, time, final copy and visual direction")
        match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:s\s*)?(?:[-–—]|to)\s*(\d+(?:\.\d+)?)\s*s", cells[1])
        if not match:
            raise ValueError(f"{label}: invalid time interval for card {cells[0]}: {cells[1]}")
        start, end = map(float, match.groups())
        if end <= start:
            raise ValueError(f"{label}: card {cells[0]} has a non-positive duration")
        textless = cells[2].lower() in ("[no added text]", "[no text]", "[no on-screen text]")
        if not textless and len(cells[2].split()) > 7:
            raise ValueError(f"{label}: card {cells[0]} exceeds seven words")
        visible_copy = cells[2].replace("**", "").replace("`", "")
        minimum = max(2.5, len(visible_copy) / 12)
        if not textless and end - start + 0.001 < minimum:
            raise ValueError(f"{label}: card {cells[0]} needs at least {minimum:.3f} seconds for readable copy; allow a visual beat too")
        cards.append((cells[0], start, end, cells[2]))
    if not cards:
        raise ValueError(f"{label}: no scripted cards found")
    ids = [card[0] for card in cards]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{label}: duplicate card ids")
    return cards


def check_sequence(cards: list[tuple], start: float, end: float, label: str) -> None:
    cursor = start
    for card_id, card_start, card_end, _ in cards:
        if abs(card_start - cursor) > 0.001:
            raise ValueError(f"{label}: gap or overlap before card {card_id}")
        cursor = card_end
    if abs(cursor - end) > 0.001:
        raise ValueError(f"{label}: timeline ends at {cursor:g}s, expected {end:g}s")


def validate_videos(text: str, cfg: dict | None) -> dict:
    mode, requested_cuts = briefing_options(cfg)
    headings = list(re.finditer(r"^## Video\b[^\n]*$", text, re.MULTILINE))
    videos = list(re.finditer(r"^## Video (\d+):[^\n]*\(target (\d+(?:\.\d+)?)\s*s\)\s*$", text, re.MULTILINE))
    if not videos:
        raise ValueError("brief needs a Video N heading with target duration")
    if len(headings) != len(videos):
        raise ValueError("every Video heading must include its number and target duration")
    video_numbers = [int(video.group(1)) for video in videos]
    if video_numbers != list(range(1, len(videos) + 1)):
        raise ValueError("video headings must be unique and numbered from 1")
    card_count = 0
    for video in videos:
        following = text[video.end():]
        block = re.split(r"^## ", following, maxsplit=1, flags=re.MULTILINE)[0]
        label = f"Video {video.group(1)}"
        duration = float(video.group(2))
        if duration <= 0 or duration > 45:
            raise ValueError(f"{label}: SB video target must be greater than zero and at most 45 seconds")
        if mode == "production":
            if re.search(r"^#### Angle \d+:", block, re.MULTILINE):
                raise ValueError(f"{label}: production mode specifies complete cuts, not test angles")
            cards = script_cards(block, label)
            check_sequence(cards, 0, duration, label)
            final_card = cards[-1]
            card_count += len(cards)
        else:
            angles = list(re.finditer(r"^#### Angle (\d+):[^\n]*$", block, re.MULTILINE))
            if [angle.group(1) for angle in angles] != ["1", "2", "3"]:
                raise ValueError(f"{label}: concept testing requires Angle 1, 2 and 3, each once")
            shared = list(re.finditer(r"^### Part 2: shared second half[^\n]*$", block, re.MULTILINE))
            if len(shared) != 1 or shared[0].start() < angles[-1].end():
                raise ValueError(f"{label}: needs one shared Part 2 after the three angles")
            shared_cards = script_cards(block[shared[0].end():], f"{label} shared Part 2")
            shared_start = shared_cards[0][1]
            check_sequence(shared_cards, shared_start, duration, f"{label} shared Part 2")
            card_count += len(shared_cards)
            for index, angle in enumerate(angles):
                finish = angles[index + 1].start() if index < 2 else shared[0].start()
                cards = script_cards(block[angle.end():finish], f"{label} Angle {index + 1}")
                check_sequence(cards, 0, shared_start, f"{label} Angle {index + 1}")
                card_count += len(cards)
            final_card = shared_cards[-1]
        if final_card[3].lower() not in ("[no added text]", "[no text]", "[no on-screen text]"):
            raise ValueError(f"{label}: final card must be textless")
    cuts = len(videos) * (3 if mode == "concept_testing" else 1)
    if requested_cuts is not None and cuts != requested_cuts:
        raise ValueError(f"brief specifies {cuts} cuts; briefing.requested_cuts is {requested_cuts}")
    return {"mode": mode, "videos": len(videos), "cuts": cuts, "scripted_cards": card_count}


def validate_markdown(path: Path, kind: str = "brief", cfg: dict | None = None) -> dict | None:
    if not path.is_file():
        raise ValueError(f"missing {kind} Markdown: {path}")
    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    forbidden = FORBIDDEN_BRIEF if kind == "brief" else FORBIDDEN_REFERENCE
    hits = [item for item in forbidden if item in lower]
    if hits:
        raise ValueError(f"{kind} contains forbidden editor-facing sections or terms: {', '.join(hits)}")
    if kind == "brief":
        for required in ("## Global rules", "### Specs (verbatim, non-negotiable)", "### Absolute do-not list"):
            if required not in text:
                raise ValueError(f"brief missing required section: {required}")
        return validate_videos(text, cfg)
    else:
        if "## 5. Footage inventory and asset requests" not in text:
            raise ValueError("reference must contain section 5: Footage inventory and asset requests")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--brief-md", required=True, type=Path)
    parser.add_argument("--mode", choices=("production", "concept_testing"), required=True)
    parser.add_argument("--requested-cuts", type=int, required=True)
    args = parser.parse_args()
    cfg = {"briefing": {"mode": args.mode, "requested_cuts": args.requested_cuts}}
    try:
        result = validate_markdown(args.brief_md, cfg=cfg)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps({"status": "mechanical_checks_passed", **result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
