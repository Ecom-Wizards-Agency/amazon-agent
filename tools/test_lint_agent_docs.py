import tempfile
import unittest
from pathlib import Path

from tools.lint_agent_docs import validate_datadive_routing, validate_skill_directory


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


if __name__ == "__main__":
    unittest.main()
