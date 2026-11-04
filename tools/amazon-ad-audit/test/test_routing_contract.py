import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def normalised(path: str) -> str:
    """File text with line wraps and runs of whitespace collapsed to single spaces."""
    return " ".join((ROOT / path).read_text(encoding="utf-8").split())


class RoutingContractTest(unittest.TestCase):
    def test_postures_have_fixed_sources(self):
        skill = normalised("skills/amazon-audit/references/audit-workflow.md")
        self.assertIn("A first-time audit is always prospect work and never calls", skill)
        self.assertIn(
            "Monthly and actions-only audits are managed-account work and require a SYNQ "
            "client (AdLabs carve-out: its AdLabs profile).",
            skill,
        )
        self.assertIn(
            "Downloaded files are allowed for these postures only for a client still being "
            "onboarded into SYNQ",
            skill,
        )
        self.assertNotIn("Never fall back to downloaded files for these postures", skill)

    def test_project_routing_matches_skill(self):
        agents = normalised("AGENTS.md")
        self.assertIn("`deep` always uses downloaded ads bulk", agents)
        self.assertIn(
            "`monthly` and `actions` require a SYNQ client (AdLabs carve-out: its AdLabs profile)", agents
        )
        self.assertIn("previews and applies route to `amazon-ppc-weekly-management`", agents)
        self.assertIn(
            "- `amazon-ppc-weekly-management`: the weekly SYNQ PPC loop (runner review, proposals, "
            "approved web-app changes); the AdLabs carve-out account keeps its AdLabs loop.",
            agents,
        )
        self.assertNotIn("- `amazon-dayparting`:", agents)


if __name__ == "__main__":
    unittest.main()
