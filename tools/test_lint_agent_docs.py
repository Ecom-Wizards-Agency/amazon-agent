import json
import sys
import tempfile
import unittest
from pathlib import Path

from tools.lint_agent_docs import (
    AGENTS_MAX_BYTES,
    AUTHORED_GLOBS,
    CHECKED_ROOTS,
    CONTRACT_WINDOW_BYTES,
    ROOT,
    ads_doctrine_drift_errors,
    agents_md_budget_errors,
    knowledge_errors,
    model_name_errors,
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
    def write_contracts(self, root: Path, *, route: str = "CDP (9223)") -> None:
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
            "logged-in DataDive session through managed Chrome CDP on port 9223\n",
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


CONTRACT_TEXT = (
    "Before any Slack write, read the posting file.\n"
    "Never inspect browser cookies or tokens.\n"
    "Missing bot access fails closed and never falls back to a personal identity.\n"
    "If personal MCP access is missing, prepare a draft or stop; never fall back to\n"
    "Grimoire.\n"
)


def write_agents_root(root: Path, agents_md: str) -> None:
    (root / "docs" / "rights").mkdir(parents=True)
    (root / "docs" / "rights" / "capability-matrix.json").write_text(
        json.dumps({"rows": []}), encoding="utf-8"
    )
    (root / "AGENTS.md").write_text(agents_md, encoding="utf-8")


class AgentsMdBudgetLintTests(unittest.TestCase):
    def budget_errors(self, agents_md: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_agents_root(root, agents_md)
            return agents_md_budget_errors(root)

    def test_contract_inside_window_passes_with_hard_wrapped_phrase(self):
        self.assertEqual([], self.budget_errors(CONTRACT_TEXT))

    def test_file_over_byte_limit_fails(self):
        errors = self.budget_errors(CONTRACT_TEXT + "x" * AGENTS_MAX_BYTES)
        self.assertTrue(any("-byte limit" in error for error in errors), errors)

    def test_phrase_after_window_fails(self):
        late = CONTRACT_TEXT.replace("Before any Slack write, read the posting file.\n", "")
        late += "y" * CONTRACT_WINDOW_BYTES + "\nBefore any Slack write, read the posting file.\n"
        errors = self.budget_errors(late)
        self.assertEqual(1, len(errors), errors)
        self.assertIn("`Before any Slack write` first appears after byte", errors[0])

    def test_drifted_phrase_is_reported_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_agents_root(
                root, CONTRACT_TEXT.replace("never falls back to a personal identity", "stops")
            )
            matrix = {"rows": [{"gates": [{
                "kind": "file_literal", "repo": "amazon-agent", "file": "AGENTS.md",
                "literal": "never falls back to a personal identity",
            }]}]}
            (root / "docs" / "rights" / "capability-matrix.json").write_text(
                json.dumps(matrix), encoding="utf-8"
            )
            errors = agents_md_budget_errors(root)
        self.assertEqual(1, len(errors), errors)
        self.assertIn("missing pinned phrase", errors[0])


class ModelNameLintTests(unittest.TestCase):
    def model_errors(self, rel: str, text: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_text(text, encoding="utf-8")
            return model_name_errors(root)

    def test_model_name_in_skill_fails(self):
        errors = self.model_errors("skills/amazon-example/SKILL.md", "Use gpt-6-sol\n")
        self.assertEqual(1, len(errors), errors)
        self.assertIn("skills/amazon-example/SKILL.md:1", errors[0])

    def test_model_name_in_nested_reference_fails(self):
        errors = self.model_errors(
            "skills/amazon-example/references/nested/guide.md", "Use gpt-6-sol\n"
        )
        self.assertEqual(1, len(errors), errors)

    def test_runtime_labelled_line_passes(self):
        self.assertEqual(
            [], self.model_errors("skills/amazon-example/SKILL.md", "**Codex.** Use gpt-6-sol\n")
        )

    def test_skill_readme_is_ignored(self):
        self.assertEqual(
            [], self.model_errors("skills/amazon-example/README.md", "Use gpt-6-sol\n")
        )


class KnowledgeLintTests(unittest.TestCase):
    """Check 10 wiring: globs, path roots and the lint_knowledge import."""

    KNOWLEDGE_TOOLS = str(ROOT / "tools" / "knowledge")
    KNOWLEDGE_MODULES = ("lint_knowledge", "build_knowledge_index", "scrub", "kb_frontmatter")

    def setUp(self):
        self.saved_path = list(sys.path)
        self.saved_modules = {name: sys.modules.get(name) for name in self.KNOWLEDGE_MODULES}

    def tearDown(self):
        sys.path[:] = self.saved_path
        for name, module in self.saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def forget_knowledge_tools(self):
        """Make lint_knowledge importable only through knowledge_errors' own setup."""
        sys.path[:] = [entry for entry in sys.path if not entry.rstrip("/").endswith("tools/knowledge")]
        for name in self.KNOWLEDGE_MODULES:
            sys.modules.pop(name, None)

    def test_authored_globs_and_checked_roots_cover_knowledge(self):
        self.assertIn("knowledge/**/*.md", AUTHORED_GLOBS)
        self.assertIn("knowledge/", CHECKED_ROOTS)

    def test_knowledge_errors_imports_lint_knowledge_from_its_own_path_setup(self):
        self.forget_knowledge_tools()
        errors = knowledge_errors(ROOT)
        self.assertFalse(any("cannot import lint_knowledge" in e for e in errors), errors)
        self.assertIn("lint_knowledge", sys.modules)
        self.assertIn(self.KNOWLEDGE_TOOLS, sys.path)

    def test_knowledge_errors_reports_a_broken_unit_in_a_temp_root(self):
        knowledge_errors(ROOT)  # loads lint_knowledge from the real tools/knowledge
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unit = root / "knowledge" / "catalog" / "KC-0001_broken-unit.md"
            unit.parent.mkdir(parents=True)
            unit.write_text("no frontmatter here\n", encoding="utf-8")
            errors = knowledge_errors(root)
        self.assertTrue(any("KC-0001_broken-unit.md" in e for e in errors), errors)

    def test_knowledge_errors_applies_the_denylist_only_when_present(self):
        knowledge_errors(ROOT)  # loads lint_knowledge from the real tools/knowledge
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            errors = knowledge_errors(root)
            self.assertFalse(any("denylist terms file missing" in e for e in errors), errors)
            (root / "_local").mkdir()
            (root / "_local" / "knowledge-redaction-terms.txt").write_text("Kestrel\n", encoding="utf-8")
            unit = root / "knowledge" / "catalog" / "KC-0001_kestrel-note.md"
            unit.parent.mkdir(parents=True)
            unit.write_text("no frontmatter, Kestrel mentioned\n", encoding="utf-8")
            errors = knowledge_errors(root)
        self.assertTrue(any("scrub term:Kestrel" in e for e in errors), errors)

    def test_knowledge_errors_names_the_missing_module(self):
        self.forget_knowledge_tools()
        with tempfile.TemporaryDirectory() as tmp:
            errors = knowledge_errors(Path(tmp))
        self.assertEqual(1, len(errors), errors)
        self.assertIn("cannot import lint_knowledge", errors[0])


if __name__ == "__main__":
    unittest.main()
