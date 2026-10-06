from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "tools" / "knowledge"))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(TESTS_DIR))

import sop_apply_triage as apply_mod  # noqa: E402
import sop_triage as st  # noqa: E402
from test_sop_triage import build_fixture  # noqa: E402

VENDOR = "vendor-central/vendor-central-sop-disputing-chargebacks.md"
VINE = "catalog/catalog-sop-enrolling-vine-on-vendor-central.md"
HELIUM = "seo/seo-sop-reverse-asin-lookup-in-helium-10-cerebro.md"
DASH = "catalog/catalog-sop-download-a-sales-dashboard-report.md"
DASH2 = "catalog/catalog-sop-download-a-sales-dashboard-report-2.md"
RICH = "catalog/catalog-sop-fixing-suppressed-listing-variations.md"
ONBOARD = "general/general-sop-team-onboarding-basics.md"
SKILL = "skills/amazon-catalog/SKILL.md"


def call(*args: str) -> tuple[int, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = apply_mod.main(list(args))
    return code, out.getvalue() + err.getvalue()


class ApplyCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        build_fixture(self.root, with_git=True)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(st.main(["signals", "--root", str(self.root)]), 0)
        self.csv_path = self.root / "_local" / "knowledge-sop-triage" / "triage.csv"
        self.index_path = self.root / "MAG SOPs" / "_index" / "sop-index.json"
        self.readme_path = self.root / "MAG SOPs" / "README.md"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def set_verdicts(self, verdicts: dict[str, dict]) -> None:
        _, rows = st.read_csv(self.csv_path)
        for row in rows:
            row.update(verdicts.get(row["file"], {}))
        st.write_csv(self.csv_path, rows)

    def good_verdicts(self) -> None:
        self.set_verdicts(
            {
                VENDOR: {"verdict": "drop", "verdict_reason": "Vendor Central"},
                HELIUM: {"verdict": "drop"},
                DASH2: {"verdict": "merge", "merge_into": DASH},
                RICH: {
                    "verdict": "supersede",
                    "superseded_by": SKILL,
                    "flags": "old-nav; url-tokens",
                    "knowledge_value": "high",
                },
                DASH: {"verdict": "keep"},
                ONBOARD: {"verdict": "update", "knowledge_value": "low"},
            }
        )

    def tree_snapshot(self) -> dict[str, bytes]:
        return {
            p.relative_to(self.root).as_posix(): p.read_bytes()
            for p in sorted((self.root / "MAG SOPs").rglob("*"))
            if p.is_file()
        }


class CheckTests(ApplyCase):
    def test_check_passes_on_valid_verdicts(self) -> None:
        self.good_verdicts()
        code, out = call("--root", str(self.root), "--check")
        self.assertEqual(code, 0, out)
        self.assertIn("0 problems", out)

    def test_check_failures(self) -> None:
        self.set_verdicts(
            {
                VENDOR: {"verdict": "maybe"},
                RICH: {"verdict": "supersede", "superseded_by": "docs/does-not-exist.md"},
                VINE: {"verdict": "supersede"},
                DASH2: {"verdict": "merge", "merge_into": DASH},
                DASH: {"verdict": "merge", "merge_into": ONBOARD},
                ONBOARD: {"verdict": "merge"},
            }
        )
        code, out = call("--root", str(self.root), "--check")
        self.assertEqual(code, 1)
        self.assertIn(f"{VENDOR}: invalid verdict 'maybe'", out)
        self.assertIn(f"{RICH}: superseded_by target does not exist: docs/does-not-exist.md", out)
        self.assertIn(f"{VINE}: supersede without superseded_by", out)
        self.assertIn(f"{DASH2}: merge_into target {DASH} is itself marked merge", out)
        self.assertIn(f"{ONBOARD}: merge without merge_into", out)

    def test_apply_refuses_when_check_fails(self) -> None:
        self.set_verdicts({VENDOR: {"verdict": "drop"}, VINE: {"verdict": "bogus"}})
        before = self.tree_snapshot()
        code, out = call("--root", str(self.root), "--apply", "--approved-by", "Tester")
        self.assertEqual(code, 1)
        self.assertIn("not applied", out)
        self.assertEqual(self.tree_snapshot(), before)

    def test_apply_requires_approved_by(self) -> None:
        self.good_verdicts()
        before = self.tree_snapshot()
        code, out = call("--root", str(self.root), "--apply")
        self.assertEqual(code, 2)
        self.assertIn("--approved-by", out)
        self.assertEqual(self.tree_snapshot(), before)


class ApplyTests(ApplyCase):
    def test_dry_run_prints_commands_and_writes_nothing(self) -> None:
        self.good_verdicts()
        before = self.tree_snapshot()
        csv_before = self.csv_path.read_bytes()
        code, out = call("--root", str(self.root), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn(f"git rm -q -- 'MAG SOPs/{VENDOR}'", out)
        self.assertIn(f"git rm -q -- 'MAG SOPs/{HELIUM}'", out)
        self.assertIn(f"git mv -- 'MAG SOPs/{DASH2}' 'MAG SOPs/_archive/{DASH2}'", out)
        self.assertIn("nothing written", out)
        self.assertEqual(self.tree_snapshot(), before)
        self.assertEqual(self.csv_path.read_bytes(), csv_before)
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", "MAG SOPs"],
            cwd=self.root, capture_output=True, text=True, check=True,
        ).stdout
        self.assertEqual(status, "")

    def test_apply(self) -> None:
        self.good_verdicts()
        code, out = call(
            "--root", str(self.root), "--apply", "--approved-by", "Tester", "--date", "2026-10-06"
        )
        self.assertEqual(code, 0, out)
        for line in (
            "dropped 2",
            "merged 1 (1 files moved to the archive)",
            "superseded 1",
            "updated 1",
            "kept 1",
            "index entries: 8 before, 6 after",
            "README regenerated:",
        ):
            self.assertIn(line, out)

        sop_root = self.root / "MAG SOPs"
        self.assertFalse((sop_root / VENDOR).exists())
        self.assertFalse((sop_root / HELIUM).exists())
        self.assertFalse((sop_root / DASH2).exists())
        self.assertTrue((sop_root / "_archive" / DASH2).exists())
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", "MAG SOPs"],
            cwd=self.root, capture_output=True, text=True, check=True,
        ).stdout
        self.assertIn(f'D  "MAG SOPs/{VENDOR}"', status)
        self.assertIn("R  ", status)

        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        by_file = {e["file"]: e for e in data["captured"]}
        self.assertNotIn(VENDOR, by_file)
        self.assertNotIn(HELIUM, by_file)
        merged = by_file[f"_archive/{DASH2}"]
        self.assertEqual(merged["status"], "merged")
        self.assertEqual(merged["merge_into"], DASH)
        self.assertTrue(merged["archived"])
        rich = by_file[RICH]
        self.assertEqual(rich["status"], "superseded")
        self.assertEqual(rich["superseded_by"], SKILL)
        self.assertEqual(rich["triaged_on"], "2026-10-06")
        self.assertEqual(rich["flags"], ["old-nav", "url-tokens"])
        self.assertEqual(rich["knowledge_value"], "high")
        self.assertEqual(by_file[DASH]["status"], "active")
        self.assertEqual(by_file[ONBOARD]["status"], "needs-update")
        self.assertEqual(by_file[ONBOARD]["knowledge_value"], "low")
        self.assertNotIn("status", by_file[VINE])
        self.assertNotIn("body", rich)
        self.assertEqual(data["dropped"][-1], {"what": "2 SOPs triaged as unusable", "date": "2026-10-06"})
        self.assertEqual(data["dropped"][0]["what"], "AI ChatGPT prompts")

        readme = self.readme_path.read_text(encoding="utf-8")
        self.assertIn(
            f"- [Catalog SOP: Fixing Suppressed Listing Variations]({RICH}) (superseded by `{SKILL}`)",
            readme,
        )
        self.assertIn("Active SOP entries: **4** (1 superseded) (plus 2 archived)", readme)
        self.assertIn(f"(_archive/{DASH2}) (merged into `{DASH}`)", readme)
        self.assertIn("2 SOPs triaged as unusable (dropped 2026-10-06)", readme.replace("\n", " "))

        # a second apply with the same sheet changes nothing on disk
        index_bytes, readme_bytes = self.index_path.read_bytes(), self.readme_path.read_bytes()
        code, out = call(
            "--root", str(self.root), "--apply", "--approved-by", "Tester", "--date", "2026-10-06"
        )
        self.assertEqual(code, 0, out)
        self.assertIn("dropped 0", out)
        self.assertEqual(self.index_path.read_bytes(), index_bytes)
        self.assertEqual(self.readme_path.read_bytes(), readme_bytes)


if __name__ == "__main__":
    unittest.main()
