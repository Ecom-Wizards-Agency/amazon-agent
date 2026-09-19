import copy
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

RIGHTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RIGHTS))
import rights_matrix as rights
import render_rights_matrix as renderer


class RightsMatrixTests(unittest.TestCase):
    def setUp(self):
        self.matrix = rights.load(RIGHTS.parents[1] / "docs/rights/capability-matrix.json")

    def test_current_matrix_valid(self):
        self.assertEqual(rights.validate(self.matrix), [])

    def test_docs_paths_check_available_repositories(self):
        self.matrix["rows"] = [self.matrix["rows"][0]]
        row = self.matrix["rows"][0]
        with tempfile.TemporaryDirectory() as tmp:
            roots = {repo: Path(tmp) / repo for repo in rights.REPOS}
            for repo, root in roots.items():
                with self.subTest(repo=repo):
                    row["docs"] = [{"repo": repo, "path": "evidence.md", "note": "Evidence."}]
                    self.assertEqual(rights.validate(self.matrix, roots), [])
                    root.mkdir()
                    self.assertIn(f"{repo}/evidence.md", " ".join(rights.validate(self.matrix, roots)))
                    (root / "evidence.md").write_text("Evidence")
                    self.assertEqual(rights.validate(self.matrix, roots), [])

    def test_vault_docs_are_not_resolved(self):
        row = self.matrix["rows"][0]
        row["docs"] = [{"repo": "vault", "path": "agency/SOPs/missing.md",
                        "note": "Unversioned team vault, ~/os/agency."}]
        self.assertEqual(rights.validate(self.matrix), [])
        row["docs"][0]["repo"] = "unknown"
        self.assertIn("invalid docs entry", " ".join(rights.validate(self.matrix)))

    def test_malformed_rows_return_errors(self):
        for value in (None, {}, {"rows": [None]}, {**self.matrix, "rows": [{"id": []}]}):
            with self.subTest(value=value):
                self.assertTrue(rights.validate(value))

    def test_required_evidence_and_unique_identity(self):
        for key, value in (("gates", []), ("docs", []), ("verified_on", "2026-99-01"),
                           ("grimoire", {"state": "maybe", "how": "x"}), ("port", 9333)):
            matrix = copy.deepcopy(self.matrix)
            matrix["rows"][0][key] = value
            with self.subTest(key=key):
                self.assertTrue(rights.validate(matrix))
        self.matrix["rows"].append(self.matrix["rows"][0])
        self.assertIn("duplicate id", " ".join(rights.validate(self.matrix)))

    def test_doc_only_requires_justification(self):
        self.matrix["rows"][0]["gates"] = [{"kind": "doc_only", "justification": ""}]
        self.assertTrue(rights.validate(self.matrix))
        self.matrix["rows"][0]["gates"][0]["justification"] = "Human approval policy, no code gate."
        self.assertEqual(rights.validate(self.matrix), [])

    def test_wrong_enum_types_return_errors(self):
        for field in ("grimoire", "docs", "gates"):
            matrix = copy.deepcopy(self.matrix)
            matrix["rows"][0][field] = {"state": [], "how": "x"} if field == "grimoire" else [{"repo": [], "kind": []}]
            self.assertTrue(rights.validate(matrix))

    def test_lint_skips_missing_siblings_but_checks_present_ones(self):
        spec = importlib.util.spec_from_file_location("rights_doc_lint", RIGHTS.parent / "lint_agent_docs.py")
        lint = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lint)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "amazon-agent"
            directory = root / "docs/rights"
            directory.mkdir(parents=True)
            row = copy.deepcopy(self.matrix["rows"][0])
            row["gates"] = [{"kind": "file_literal", "repo": "wizards-ai", "file": "gate.py", "literal": "exists"}]
            matrix = {**self.matrix, "rows": [row]}
            (directory / "capability-matrix.json").write_text(json.dumps(matrix))
            (directory / "README.md").write_text(renderer.rendered_readme(matrix, renderer.BEGIN + renderer.END))
            notice = io.StringIO()
            with contextlib.redirect_stderr(notice):
                self.assertEqual(lint.rights_matrix_errors(root), [])
            self.assertIn("missing sibling wizards-ai", notice.getvalue())
            sibling = root.parent / "wizards-ai"
            sibling.mkdir()
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertTrue(lint.rights_matrix_errors(root))
            (sibling / "gate.py").write_text("exists")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(lint.rights_matrix_errors(root), [])
            (directory / "README.md").write_text(renderer.BEGIN + renderer.END)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertIn("stale rendered rights matrix", " ".join(lint.rights_matrix_errors(root)))

    def test_python_symbols_without_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "code.py").write_text("raise RuntimeError('never import')\nA = {'live': unavailable_function}\nB: list = ['live']\nC = ('live',)\nD = set()\n")
            for symbol in ("A", "B", "C"):
                gate = {"kind": "python_symbol_contains", "repo": "amazon-agent", "file": "code.py", "symbol": symbol, "value": "live"}
                self.assertTrue(rights.resolve_gate({"amazon-agent": root}, gate)[0])
                gate["value"] = "missing"
                self.assertFalse(rights.resolve_gate({"amazon-agent": root}, gate)[0])
            gate.update(symbol="D")
            self.assertFalse(rights.resolve_gate({"amazon-agent": root}, gate)[0])

    def test_json_pointer_escaping_and_strict_indices(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data.json").write_text(json.dumps({"a/b": {"~key": [True, {"active": 1}]}}))
            gate = {"kind": "json_pointer_equals", "repo": "amazon-agent", "file": "data.json", "pointer": "/a~1b/~0key/0", "value": True}
            self.assertTrue(rights.resolve_gate({"amazon-agent": root}, gate)[0])
            gate["value"] = 1
            self.assertFalse(rights.resolve_gate({"amazon-agent": root}, gate)[0])
            for pointer in ("/a~2b", "/a~1b/~0key/-1", "/a~1b/~0key/01", "bad"):
                gate["pointer"] = pointer
                self.assertFalse(rights.resolve_gate({"amazon-agent": root}, gate)[0])
            gate.update(kind="json_pointer_contains", pointer="/a~1b/~0key/1", value="active")
            self.assertTrue(rights.resolve_gate({"amazon-agent": root}, gate)[0])
            gate.update(pointer="/a~1b/~0key", value=True)
            self.assertTrue(rights.resolve_gate({"amazon-agent": root}, gate)[0])

    def test_missing_files_literals_and_path_escape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "gate.txt").write_text("required literal")
            gate = {"kind": "file_literal", "repo": "amazon-agent", "file": "gate.txt", "literal": "required"}
            self.assertTrue(rights.resolve_gate({"amazon-agent": root}, gate)[0])
            for file in ("missing", "../gate.txt", "/tmp/gate.txt", "~/gate.txt"):
                gate["file"] = file
                self.assertFalse(rights.resolve_gate({"amazon-agent": root}, gate)[0])

    def test_digest_is_canonical_and_sensitive(self):
        reordered = dict(reversed(list(self.matrix.items())))
        self.assertEqual(rights.digest(self.matrix), rights.digest(reordered))
        reordered["updated_on"] += "-changed"
        self.assertNotEqual(rights.digest(self.matrix), rights.digest(reordered))

    def test_renderer_preserves_narrative_and_detects_drift(self):
        source = f"Intro\n{renderer.BEGIN}\nstale\n{renderer.END}\nTail\n"
        rendered = renderer.rendered_readme(self.matrix, source)
        self.assertTrue(rendered.startswith("Intro\n"))
        self.assertTrue(rendered.endswith("\nTail\n"))
        self.assertNotEqual(rendered, source)
        self.assertEqual(rendered, renderer.rendered_readme(self.matrix, rendered))
        with self.assertRaises(ValueError):
            renderer.rendered_readme(self.matrix, "no markers")

    def test_all_available_checkout_gates(self):
        root = RIGHTS.parents[1]
        roots = {name: root.parent / name for name in rights.REPOS}
        for row in self.matrix["rows"]:
            for gate in row["gates"]:
                if gate.get("repo") and not roots[gate["repo"]].exists():
                    continue
                with self.subTest(row=row["id"], gate=gate):
                    ok, detail = rights.resolve_gate(roots, gate)
                    self.assertTrue(ok, detail)


if __name__ == "__main__":
    unittest.main()
