import json
import tempfile
import unittest
from pathlib import Path

from tools.lint_agent_docs import ads_doctrine_drift_errors


def write_fixture(root: Path, strategy_value: float, consumer_value: float) -> tuple[Path, Path]:
    (root / "_local/ads-strategy").mkdir(parents=True)
    strategy = root / "_local/ads-strategy/strategy.json"
    strategy.write_text(
        json.dumps({"management": {"run_rate": {"warn_above": strategy_value}}}),
        encoding="utf-8",
    )
    (root / "tools").mkdir()
    (root / "tools/consumer.py").write_text(
        f'DEFAULTS = {{\n    "warn_above": {consumer_value},\n}}\n', encoding="utf-8"
    )
    (root / "docs").mkdir()
    source_map = root / "docs/ads-doctrine-source-map.json"
    source_map.write_text(
        json.dumps(
            {
                "schema": "amazon-agent.ads-doctrine-source-map.v1",
                "canonical_strategy": "_local/ads-strategy/strategy.json",
                "mirrors": [
                    {
                        "id": "warn",
                        "canonical_key": "management.run_rate.warn_above",
                        "consumer": {
                            "path": "tools/consumer.py",
                            "pattern": r'^\s*"warn_above"\s*:\s*(?P<value>-?\d+(?:\.\d+)?)',
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return source_map, strategy


class AdsDoctrineLintTests(unittest.TestCase):
    def test_ads_doctrine_mirror_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_map, strategy = write_fixture(root, 1.1, 1.10)
            self.assertEqual(ads_doctrine_drift_errors(root, source_map, strategy), [])

    def test_ads_doctrine_mirror_drift_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_map, strategy = write_fixture(root, 1.2, 1.1)
            errors = ads_doctrine_drift_errors(root, source_map, strategy)
            self.assertEqual(len(errors), 1)
            self.assertIn("doctrine drift", errors[0])

    def test_optional_missing_strategy_key_is_not_guessed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_map, strategy = write_fixture(root, 1.1, 1.1)
            data = json.loads(source_map.read_text(encoding="utf-8"))
            data["mirrors"][0]["canonical_key"] = "management.sufficiency.unresolved"
            data["mirrors"][0]["required"] = False
            source_map.write_text(json.dumps(data), encoding="utf-8")
            self.assertEqual(ads_doctrine_drift_errors(root, source_map, strategy), [])


if __name__ == "__main__":
    unittest.main()
