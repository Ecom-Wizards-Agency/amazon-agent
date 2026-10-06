from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TESTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / "tools" / "knowledge"))
sys.path.insert(0, str(REPO / "tools"))
sys.path.insert(0, str(TESTS_DIR))

import sop_triage as st  # noqa: E402

SCRIPT = REPO / "tools" / "knowledge" / "sop_triage.py"

D360 = "https://files.document360.io/abc/Images/Documentation/image-{n}.png?sv=2022-11-02&se=2025-07-18&sig=x%3D"
MAG = "https://sop.example.test/uploads/images/gallery/2025-08/scaled/{n}.png"

SUPPRESSED_BODY = "\n".join(
    [
        "# Catalog SOP: Fixing Suppressed Listing Variations",
        "",
        "Written in 2019 and revised in 2023.",
        "Open Help > Get support, then Contact us and check the Case Log.",
        "While the SOP does not specify a deadline, Amazon typically replies fast.",
        "Track the work in Asana and check the price history in Keepa.",
        f"![image]({D360.format(n=1)})",
        f"![image]({D360.format(n=2)})",
        f"![image.png]({MAG.format(n=3)})",
        "",
    ]
)

# file -> (title, category, body)
FIXTURE_SOPS = {
    "catalog/catalog-sop-fixing-suppressed-listing-variations.md": (
        "Catalog SOP: Fixing Suppressed Listing Variations",
        "Catalog",
        SUPPRESSED_BODY,
    ),
    "vendor-central/vendor-central-sop-disputing-chargebacks.md": (
        "Vendor Central SOP: Disputing Chargebacks",
        "Vendor Central",
        "Vendor body.\n",
    ),
    "catalog/catalog-sop-enrolling-vine-on-vendor-central.md": (
        "Catalog SOP: Enrolling Vine on Vendor Central",
        "Catalog",
        "Vine body.\n",
    ),
    "seo/seo-sop-reverse-asin-lookup-in-helium-10-cerebro.md": (
        "SEO SOP: Reverse ASIN Lookup in Helium 10 Cerebro",
        "SEO",
        "Open Helium 10, then Cerebro, then Magnet.\n",
    ),
    "catalog/catalog-sop-download-a-sales-dashboard-report.md": (
        "Catalog SOP: Download a Sales Dashboard Report",
        "Catalog",
        "Sales dashboard, first copy.\n",
    ),
    "catalog/catalog-sop-download-a-sales-dashboard-report-2.md": (
        "Catalog SOP: Download a Sales Dashboard Report",
        "Catalog",
        "Sales dashboard, second copy.\n",
    ),
    "general/general-sop-team-onboarding-basics.md": (
        "General SOP: Team Onboarding Basics",
        "General",
        "Install Helium 10. Learn Cerebro. Learn Magnet. Scribbles later.\n",
    ),
}
ARCHIVED_FILE = "_archive/catalog/catalog-sop-retired.md"


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", *args,
        ],
        cwd=root, capture_output=True, text=True, check=True,
    )


def build_fixture(root: Path, with_git: bool = True) -> None:
    sop_root = root / "MAG SOPs"
    entries = []
    for rel, (title, category, body) in FIXTURE_SOPS.items():
        path = sop_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\n"
            f'title: "{title}"\n'
            f'category: "{category}"\n'
            'captured_at: "2026-05-12T07:07:49Z"\n'
            "---\n\n" + body,
            encoding="utf-8",
        )
        entries.append(
            {
                "title": title,
                "category": category,
                "chapter": None,
                "url": f"https://sop.example.test/{rel}",
                "captured_at": "2026-05-12T07:07:49Z",
                "file": rel,
                "body_length": len(body),
                "image_count": body.count("!["),
                "body": "dropped by slimming",
            }
        )
    archived = sop_root / ARCHIVED_FILE
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text("# Retired\n", encoding="utf-8")
    entries.append(
        {"title": "Catalog SOP: Retired", "category": "Catalog", "file": ARCHIVED_FILE, "archived": True}
    )
    index = {
        "captured_at": "2026-05-12T07:07:49Z",
        "total_entries": len(entries),
        "captured_count": len(entries),
        "failure_count": 0,
        "categories": sorted({e["category"] for e in entries}),
        "captured": entries,
    }
    (sop_root / "_index").mkdir(parents=True, exist_ok=True)
    (sop_root / "_index" / "sop-index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    (sop_root / "README.md").write_text("# placeholder\n", encoding="utf-8")
    skill = root / "skills" / "amazon-catalog" / "SKILL.md"
    skill.parent.mkdir(parents=True, exist_ok=True)
    skill.write_text("Fix suppressed listings and broken variations here.\n", encoding="utf-8")
    other = root / "docs" / "unrelated.md"
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text("Nothing about that topic.\n", encoding="utf-8")
    if with_git:
        git(root, "init", "-q")
        git(root, "add", "-A")
        git(root, "commit", "-q", "--no-verify", "-m", "fixture")


def rows_by_file(path: Path) -> dict[str, dict]:
    return {r["file"]: r for r in st.read_csv(path)[1]}


def run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


class FixtureCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        build_fixture(self.root, with_git=False)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def signals(self) -> dict[str, dict]:
        sigs, missing = st.collect_signals(self.root)
        self.assertEqual(missing, [])
        return {s["file"]: s for s in sigs}


class SignalTests(FixtureCase):
    def test_skips_archived_and_scans_active(self) -> None:
        sigs = self.signals()
        self.assertEqual(set(sigs), set(FIXTURE_SOPS))
        self.assertNotIn(ARCHIVED_FILE, sigs)

    def test_every_signal_on_the_rich_sop(self) -> None:
        s = self.signals()["catalog/catalog-sop-fixing-suppressed-listing-variations.md"]
        self.assertEqual(s["title"], "Catalog SOP: Fixing Suppressed Listing Variations")
        self.assertEqual(s["category"], "Catalog")
        self.assertEqual(s["body_length"], len(SUPPRESSED_BODY))
        self.assertEqual(s["image_count"], 3)
        self.assertEqual(s["images_document360"], 2)
        self.assertEqual(s["images_mag_2025"], 1)
        self.assertFalse(s["no_images"])
        # 2026 only appears in the frontmatter, which is excluded
        self.assertEqual(s["years"], ["2019", "2022", "2023", "2025"])
        self.assertEqual(s["tools"], ["asana", "keepa"])
        self.assertEqual(s["old_nav_hits"], 3)
        # "While the SOP does not specify" counts once, plus "typically"
        self.assertEqual(s["faq_unsourced_hits"], 2)
        self.assertEqual(s["url_tokens"], 2)
        self.assertEqual(s["overlap_files"], ["skills/amazon-catalog/SKILL.md"])
        self.assertEqual(s["drop_class"], "")
        self.assertEqual(s["sibling_group"], "")
        self.assertFalse(s["helium10_body_heavy"])
        self.assertEqual(s["pre_verdict"], "review")
        self.assertTrue(s["pre_reason"].endswith("."))

    def test_no_images_and_helium_heavy(self) -> None:
        s = self.signals()["general/general-sop-team-onboarding-basics.md"]
        self.assertTrue(s["no_images"])
        self.assertTrue(s["helium10_body_heavy"])
        self.assertEqual(s["pre_verdict"], "review")
        self.assertIn("Helium 10", s["pre_reason"])
        self.assertEqual(s["tools"], ["cerebro", "helium 10", "magnet", "scribbles"])

    def test_helium_heavy_is_false_when_drop_class_set(self) -> None:
        s = self.signals()["seo/seo-sop-reverse-asin-lookup-in-helium-10-cerebro.md"]
        self.assertEqual(s["drop_class"], "tool-in-title")
        self.assertFalse(s["helium10_body_heavy"])

    def test_drop_classes(self) -> None:
        sigs = self.signals()
        classes = {f: s["drop_class"] for f, s in sigs.items() if s["drop_class"]}
        self.assertEqual(
            classes,
            {
                "vendor-central/vendor-central-sop-disputing-chargebacks.md": "vendor-central-category",
                "catalog/catalog-sop-enrolling-vine-on-vendor-central.md": "vendor-titled",
                "seo/seo-sop-reverse-asin-lookup-in-helium-10-cerebro.md": "tool-in-title",
            },
        )
        for f in classes:
            self.assertEqual(sigs[f]["pre_verdict"], "drop")
        self.assertEqual(st.drop_class({"title": "Walmart SOP: Items", "file": "x/y.md"}), "walmart")
        self.assertEqual(
            st.drop_class({"title": "Advertising SOP: How To Use Bulk Comparison Tool or Jan’s Tool"}),
            "tool-in-title",
        )
        self.assertEqual(st.drop_class({"title": "Catalog SOP: Vendor Codes"}), "vendor-titled")
        self.assertEqual(st.drop_class({"title": "Catalog SOP: Vendors"}), "")

    def test_sibling_grouping(self) -> None:
        sigs = self.signals()
        a = sigs["catalog/catalog-sop-download-a-sales-dashboard-report.md"]
        b = sigs["catalog/catalog-sop-download-a-sales-dashboard-report-2.md"]
        self.assertTrue(a["sibling_group"].startswith("sib-"))
        self.assertEqual(a["sibling_group"], b["sibling_group"])
        self.assertEqual(a["pre_verdict"], "merge-candidate")
        others = [s for f, s in sigs.items() if s["sibling_group"] and s is not a and s is not b]
        self.assertEqual(others, [])

    def test_sibling_rules(self) -> None:
        self.assertEqual(st.normalize_title("Catalog SOP: Report -2"), "catalog sop report")
        self.assertEqual(
            st.normalize_title("Catalog SOP: Feed Processing Error Code - 5665"),
            "catalog sop feed processing error code 5665",
        )
        entries = [
            {"file": "a.md", "title": "Catalog SOP: How to Cancel FBA Removal Order"},
            {"file": "b.md", "title": "Catalog SOP: How to Cancel FBA Shipment"},
            {"file": "c.md", "title": "Catalog SOP: Error 5887"},
            {"file": "d.md", "title": "Catalog SOP: Error 8026"},
            {"file": "e.md", "title": "Catalog SOP: Error 8026 -3"},
        ]
        groups = st.sibling_groups(entries)
        self.assertEqual(groups["a.md"], groups["b.md"])
        self.assertEqual(groups["d.md"], groups["e.md"])
        self.assertNotIn("c.md", groups)
        self.assertNotEqual(groups["a.md"], groups["d.md"])

    def test_distinctive_words(self) -> None:
        self.assertEqual(
            st.distinctive_words("Catalog SOP: How to Create and Download a Seller Central Report"),
            [],
        )
        self.assertEqual(
            st.distinctive_words("Catalog SOP: Fixing Suppressed Listing Variations"),
            ["suppressed", "variations", "listing"],
        )


class CliTests(FixtureCase):
    def test_drop_list_prints_paths_only_and_writes_nothing(self) -> None:
        out_dir = self.root / "out"
        res = run_cli("signals", "--root", str(self.root), "--out-dir", str(out_dir), "--drop-list")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(
            res.stdout.splitlines(),
            [
                "MAG SOPs/catalog/catalog-sop-enrolling-vine-on-vendor-central.md",
                "MAG SOPs/seo/seo-sop-reverse-asin-lookup-in-helium-10-cerebro.md",
                "MAG SOPs/vendor-central/vendor-central-sop-disputing-chargebacks.md",
            ],
        )
        self.assertFalse(out_dir.exists())

    def test_signals_is_default_and_writes_csv_in_column_order(self) -> None:
        res = run_cli("--root", str(self.root), "--out-dir", "out")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("drop: 3", res.stdout)
        self.assertIn("merge-candidate: 2", res.stdout)
        self.assertIn("vendor-central-category: 1", res.stdout)
        out = self.root / "out"
        with (out / "triage.csv").open(encoding="utf-8", newline="") as fh:
            header = next(csv.reader(fh))
        expected = (
            "file,title,category,pre_verdict,pre_reason,drop_class,sibling_group,"
            "helium10_body_heavy,years,tools,old_nav_hits,faq_unsourced_hits,url_tokens,"
            "overlap_files,verdict,verdict_reason,superseded_by,merge_into,flags,"
            "knowledge_value,policy_risk"
        ).split(",")
        self.assertEqual(header, expected)
        rows = st.read_csv(out / "triage.csv")[1]
        self.assertEqual(len(rows), len(FIXTURE_SOPS))
        rich = next(r for r in rows if r["file"].endswith("suppressed-listing-variations.md"))
        self.assertEqual(rich["years"], "2019; 2022; 2023; 2025")
        self.assertEqual(rich["helium10_body_heavy"], "false")
        self.assertTrue(all(r["verdict"] == "" for r in rows))
        lines = (out / "signals.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), len(FIXTURE_SOPS))
        self.assertIn("images_document360", json.loads(lines[0]))

    def test_merge_verdicts_partial_and_rerun_preserves(self) -> None:
        self.assertEqual(run_cli("--root", str(self.root)).returncode, 0)
        csv_path = self.root / "_local" / "knowledge-sop-triage" / "triage.csv"
        before = rows_by_file(csv_path)
        target = "catalog/catalog-sop-download-a-sales-dashboard-report-2.md"
        partial = self.root / "partial.csv"
        partial.write_text(
            "file,verdict,merge_into\n"
            f"{target},merge,catalog/catalog-sop-download-a-sales-dashboard-report.md\n",
            encoding="utf-8",
        )
        res = run_cli("merge-verdicts", "--root", str(self.root), "--from", str(partial))
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        after = rows_by_file(csv_path)
        self.assertEqual(after[target]["verdict"], "merge")
        self.assertEqual(after[target]["merge_into"], "catalog/catalog-sop-download-a-sales-dashboard-report.md")
        for col in st.SIGNAL_COLUMNS:
            self.assertEqual(after[target][col], before[target][col])
        for f, row in after.items():
            if f != target:
                self.assertEqual(row, before[f])

        # a rerun of signals keeps the verdict columns
        self.assertEqual(run_cli("--root", str(self.root)).returncode, 0)
        rerun = rows_by_file(csv_path)
        self.assertEqual(rerun[target]["verdict"], "merge")

        # unknown keys and bad verdicts are refused without writing
        bad = self.root / "bad.csv"
        bad.write_text("file,verdict\nnope.md,keep\n" f"{target},maybe\n", encoding="utf-8")
        snapshot = csv_path.read_bytes()
        res = run_cli("merge-verdicts", "--root", str(self.root), "--from", str(bad))
        self.assertEqual(res.returncode, 1)
        self.assertIn("unknown file key", res.stdout)
        self.assertIn("invalid verdict", res.stdout)
        self.assertEqual(csv_path.read_bytes(), snapshot)

    def test_summary(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(st.main(["signals", "--root", str(self.root)]), 0)
        buf = io.StringIO()
        with redirect_stdout(buf):
            self.assertEqual(st.main(["summary", "--root", str(self.root)]), 0)
        out = buf.getvalue()
        self.assertIn(f"(none): {len(FIXTURE_SOPS)}", out)
        self.assertIn("Catalog: 4", out)
        self.assertIn("Vendor Central: 1", out)


if __name__ == "__main__":
    unittest.main()
