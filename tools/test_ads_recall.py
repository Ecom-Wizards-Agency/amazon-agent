import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.ads_recall import (
    CHALLENGES,
    DECISION,
    DECISIONS,
    SOURCE_CONTRACTS,
    SYNQ_DECISION,
    contract_paths,
    recall_paths,
    resolve_vault,
)

ROOT = Path(__file__).resolve().parents[1]


class AdsRecallTests(unittest.TestCase):
    def test_resolve_and_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Clients").mkdir()
            decision = root / DECISION
            decision.parent.mkdir()
            decision.write_text("approved", encoding="utf-8")
            challenges = root / CHALLENGES
            challenges.parent.mkdir(parents=True, exist_ok=True)
            challenges.write_text("decided challenges", encoding="utf-8")
            playbook = root / "Playbooks/amazon-ppc-management-playbook.md"
            playbook.parent.mkdir()
            playbook.write_text("tested", encoding="utf-8")
            research = root / "Research/amazon-ads/bidding-and-bid-adjustments.md"
            research.parent.mkdir(parents=True, exist_ok=True)
            research.write_text("evidence", encoding="utf-8")

            with patch.dict(os.environ, {"AMAZON_AGENT_TEAM_VAULT": str(root)}):
                self.assertEqual(resolve_vault(), root.resolve())
            paths = recall_paths("management", root)
            self.assertEqual(paths[:4], [decision, challenges, playbook, research])

    def test_synq_decision_follows_doctrine_decision(self):
        self.assertEqual(DECISIONS, (DECISION, SYNQ_DECISION))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (DECISION, SYNQ_DECISION, CHALLENGES):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("x", encoding="utf-8")
            paths = recall_paths("management", root)
            self.assertEqual(paths[:3], [root / DECISION, root / SYNQ_DECISION, root / CHALLENGES])

    def test_missing_synq_decision_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (DECISION, CHALLENGES):
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                (root / rel).write_text("x", encoding="utf-8")
            self.assertEqual(recall_paths("audit", root), [root / DECISION, root / CHALLENGES])

    def test_source_contract_listed_only_when_present(self):
        self.assertEqual(SOURCE_CONTRACTS, ("docs/synq-mcp.md",))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(contract_paths("management", root), [])
            contract = root / "docs/synq-mcp.md"
            contract.parent.mkdir()
            contract.write_text("contract", encoding="utf-8")
            for surface in ("console", "management", "monitor", "audit", "campaign-builder"):
                self.assertEqual(contract_paths(surface, root), [contract])
            self.assertEqual(contract_paths("seo-rank-gate", root), [])

    def test_source_map_names_both_decisions_and_contract(self):
        import json

        source_map = json.loads((ROOT / "docs/ads-doctrine-source-map.json").read_text(encoding="utf-8"))
        self.assertEqual(source_map["decision_record"], DECISION)
        self.assertEqual(source_map["decision_records"], list(DECISIONS))
        self.assertEqual(source_map["source_contracts"], list(SOURCE_CONTRACTS))

    def test_missing_vault_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing"
            # Isolate from this machine's env var and _local pointer file.
            with patch.dict(os.environ, {}, clear=True), patch("tools.ads_recall.ROOT", Path(tmp)):
                self.assertIsNone(resolve_vault(str(missing)))

    def test_recall_gates_live_once_in_shared_skill_entrypoints(self):
        audit_entry = (ROOT / "skills/amazon-audit/SKILL.md").read_text(encoding="utf-8")
        audit_workflow = (ROOT / "skills/amazon-audit/references/audit-workflow.md").read_text(encoding="utf-8")
        seo_entry = (ROOT / "skills/amazon-seo/SKILL.md").read_text(encoding="utf-8")
        seo_listing = (ROOT / "skills/amazon-seo/references/listing-optimization-and-compliance.md").read_text(encoding="utf-8")

        self.assertEqual(audit_entry.count("tools/ads_recall.py audit"), 1)
        self.assertNotIn("tools/ads_recall.py audit", audit_workflow)
        self.assertEqual(seo_entry.count("tools/ads_recall.py seo-rank-gate"), 1)
        self.assertNotIn("tools/ads_recall.py seo-rank-gate", seo_listing)
        self.assertIn("browse-node assignment", seo_entry)
        self.assertNotIn("browse-node assignment", seo_listing)


if __name__ == "__main__":
    unittest.main()
