import json
import tempfile
import unittest
from pathlib import Path

from tools.lint_agent_docs import (
    ads_doctrine_drift_errors,
    validate_datadive_routing,
    validate_skill_directory,
)


VALID_DESCRIPTION = "Handle a focused Amazon workflow and preserve its documented safety boundary."
VALID_SHORT_DESCRIPTION = "Handle a focused Amazon workflow"


class SkillManifestLintTests(unittest.TestCase):
    def make_skill(
        self,
        root: Path,
        *,
        description_line: str = f'description: "{VALID_DESCRIPTION}"',
        short_description: str = VALID_SHORT_DESCRIPTION,
        default_prompt: str = "Use $amazon-example to handle this Amazon workflow.",
    ) -> Path:
        skill_dir = root / "amazon-example"
        (skill_dir / "agents").mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            "---\n"
            "name: amazon-example\n"
            f"{description_line}\n"
            "---\n\n"
            "# Amazon Example\n\n"
            "Browser: None (local workflow).\n",
            encoding="utf-8",
        )
        (skill_dir / "agents" / "openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Amazon Example"\n'
            f'  short_description: "{short_description}"\n'
            f'  default_prompt: "{default_prompt}"\n',
            encoding="utf-8",
        )
        return skill_dir

    def lint(self, **kwargs) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = self.make_skill(Path(tmp), **kwargs)
            return validate_skill_directory(skill_dir)

    def test_valid_quoted_manifests_pass(self):
        self.assertEqual([], self.lint())

    def test_unquoted_colon_description_fails_yaml_parse(self):
        errors = self.lint(description_line="description: Route work: safely")
        self.assertTrue(any("invalid YAML" in error for error in errors), errors)

    def test_angle_brackets_are_rejected(self):
        errors = self.lint(
            description_line='description: "Handle <account> input safely."'
        )
        self.assertTrue(any("angle brackets" in error for error in errors), errors)

    def test_long_ui_short_description_is_rejected(self):
        errors = self.lint(short_description="x" * 65)
        self.assertTrue(any("expected 25-64" in error for error in errors), errors)

    def test_default_prompt_requires_exact_skill_name(self):
        errors = self.lint(default_prompt="Use this skill to handle the workflow.")
        self.assertTrue(any("must mention `$amazon-example`" in error for error in errors), errors)


class DataDiveRoutingLintTests(unittest.TestCase):
    def write_contracts(self, root: Path, *, route: str = "CDP (9222)") -> None:
        (root / "docs").mkdir(parents=True)
        reference = root / "skills" / "amazon-seo" / "references"
        reference.mkdir(parents=True)
        (root / "AGENTS.md").write_text(
            "DataDive web app navigation, read-only endpoint fetches, downloads, and\n",
            encoding="utf-8",
        )
        (root / "docs" / "browser-routing-map.md").write_text(
            '| DataDive full keyword pool (the old "Expanded 1% MKL") | '
            f"`amazon-seo` | {route} |\n",
            encoding="utf-8",
        )
        (reference / "keyword-research-workbook.md").write_text(
            "logged-in DataDive session through managed Chrome CDP on port 9222\n",
            encoding="utf-8",
        )

    def test_datadive_cdp_route_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_contracts(root)
            self.assertEqual([], validate_datadive_routing(root))

    def test_datadive_extension_default_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_contracts(root, route="Extension")
            errors = validate_datadive_routing(root)
            self.assertTrue(any("DataDive CDP" in error for error in errors), errors)


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
