import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class RoutingContractTest(unittest.TestCase):
    def test_postures_have_fixed_sources(self):
        skill = (ROOT / "skills/amazon-audit/SKILL.md").read_text()
        self.assertIn("A first-time audit is always prospect work and never calls", skill)
        self.assertIn("Monthly and actions-only audits are managed-account work and require AdLabs", skill)
        self.assertIn("Never fall back to downloaded files for these postures", skill)

    def test_project_routing_matches_skill(self):
        agents = (ROOT / "AGENTS.md").read_text()
        self.assertIn("`deep` always uses downloaded ads bulk", agents)
        self.assertIn("`monthly` and `actions` require an AdLabs profile", agents)
        self.assertIn("previews and applies route to `amazon-ppc-management`", agents)


if __name__ == "__main__":
    unittest.main()
