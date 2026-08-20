#!/usr/bin/env python3
"""Resolve the ordered team-knowledge files for an Amazon Ads workflow.

This helper prints paths only. The calling agent still reads the files. An unavailable
team vault is a supported state and produces no output.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECISION = "Decisions/2026-08-11-amazon-ads-doctrine-upgrade.md"
CHALLENGES = "Research/amazon-ads/challenges.md"

SURFACES = {
    "console": {
        "playbooks": ["Playbooks/amazon-ppc-management-playbook.md"],
        "research": [
            "Research/amazon-ads/bidding-and-bid-adjustments.md",
            "Research/amazon-ads/placements-and-bid-modifiers.md",
            "Research/amazon-ads/campaign-structure.md",
        ],
    },
    "management": {
        "playbooks": ["Playbooks/amazon-ppc-management-playbook.md"],
        "research": [
            "Research/amazon-ads/bidding-and-bid-adjustments.md",
            "Research/amazon-ads/placements-and-bid-modifiers.md",
            "Research/amazon-ads/budgets-and-dayparting.md",
            "Research/amazon-ads/harvesting-and-graduation.md",
            "Research/amazon-ads/negation-thresholds.md",
            "Research/amazon-ads/ranking-vs-profit-regimes.md",
            "Research/amazon-ads/seasonality-deals-and-promotions.md",
        ],
    },
    "monitor": {
        "playbooks": ["Playbooks/amazon-ppc-management-playbook.md"],
        "research": [
            "Research/amazon-ads/attribution-measurement-and-sqp.md",
            "Research/amazon-ads/budgets-and-dayparting.md",
            "Research/amazon-ads/diagnostics-and-audits.md",
            "Research/amazon-ads/seasonality-deals-and-promotions.md",
        ],
    },
    "audit": {
        "playbooks": ["Playbooks/amazon-audit-playbook.md"],
        "research": [
            "Research/amazon-ads/diagnostics-and-audits.md",
            "Research/amazon-ads/attribution-measurement-and-sqp.md",
            "Research/amazon-ads/listing-cvr-and-creative.md",
            "Research/amazon-ads/placements-and-bid-modifiers.md",
        ],
    },
    "campaign-builder": {
        "playbooks": ["Playbooks/amazon-ppc-management-playbook.md"],
        "research": [
            "Research/amazon-ads/campaign-structure.md",
            "Research/amazon-ads/keyword-research-and-match-types.md",
            "Research/amazon-ads/product-targeting-and-conquesting.md",
            "Research/amazon-ads/budgets-and-dayparting.md",
            "Research/amazon-ads/bidding-and-bid-adjustments.md",
        ],
    },
    "seo-rank-gate": {
        "playbooks": [],
        "research": [
            "Research/amazon-ads/listing-cvr-and-creative.md",
            "Research/amazon-ads/ranking-vs-profit-regimes.md",
            "Research/amazon-ads/attribution-measurement-and-sqp.md",
        ],
    },
}


def resolve_vault(explicit: str | None = None) -> Path | None:
    candidates = []
    if explicit:
        candidates.append(Path(explicit).expanduser())
    env_path = os.environ.get("AMAZON_AGENT_TEAM_VAULT")
    if env_path:
        candidates.append(Path(env_path).expanduser())
    pointer = ROOT / "_local" / "team-vault-path.txt"
    if pointer.is_file():
        for line in pointer.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                candidates.append(Path(value).expanduser())
                break
    for candidate in candidates:
        if (candidate / "Clients").is_dir():
            return candidate.resolve()
    return None


def recall_paths(surface: str, vault: Path) -> list[Path]:
    spec = SURFACES[surface]
    ordered = [DECISION, CHALLENGES, *spec["playbooks"], *spec["research"]]
    return [vault / rel for rel in ordered if (vault / rel).is_file()]


def main() -> int:
    parser = argparse.ArgumentParser(description="List ordered Amazon Ads doctrine recall files")
    parser.add_argument("surface", choices=sorted(SURFACES))
    parser.add_argument("--vault", help="explicit team-vault path, mainly for diagnostics")
    args = parser.parse_args()
    vault = resolve_vault(args.vault)
    if vault is None:
        return 0
    for path in recall_paths(args.surface, vault):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
