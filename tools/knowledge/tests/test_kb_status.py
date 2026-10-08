from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import kb_status  # noqa: E402

TODAY = "2026-10-06"


def unit(uid: str, **extra: object) -> dict:
    base = {
        "id": uid,
        "title": f"Unit {uid}",
        "topic": "catalog",
        "status": "reviewed",
        "verification": "unverified",
        "verified_on": "",
        "amazon_sources": [],
        "supersedes": [],
        "review_by": "2027-10",
        "file": f"knowledge/catalog/{uid}_unit.md",
    }
    base.update(extra)
    return base


def set_age(path: Path, age_days: int) -> None:
    """Set mtime to noon local time, age_days before TODAY (noon keeps DST shifts on the same date)."""
    stamp = time.mktime(time.strptime(TODAY + " 12:00", "%Y-%m-%d %H:%M")) - age_days * 86400
    os.utime(path, (stamp, stamp))


class StatusFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "knowledge" / "_index").mkdir(parents=True)
        (self.root / "knowledge" / "catalog").mkdir()
        (self.root / "Amazon Seller Help" / "articles").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_units(self, *units: dict, age_days: int = 0) -> None:
        for u in units:
            path = self.root / u["file"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("unit\n", encoding="utf-8")
            set_age(path, age_days)
        index = {"units": list(units)}
        (self.root / "knowledge" / "_index" / "knowledge-index.json").write_text(json.dumps(index), encoding="utf-8")

    def capture(self, name: str, downloaded_at: str) -> str:
        rel = f"Amazon Seller Help/articles/{name}"
        (self.root / rel).write_text(
            f'---\ntitle: "Page"\ndownloaded_at: "{downloaded_at}"\n---\n\nBody\n', encoding="utf-8"
        )
        return rel

    def report(self) -> dict:
        return kb_status.status_report(self.root, kb_status.dt.date.fromisoformat(TODAY))

    def run_main(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = kb_status.main(["--root", str(self.root), "--today", TODAY, *args])
        return code, out.getvalue()


class StatusTests(StatusFixture):
    def test_review_due(self) -> None:
        self.write_units(
            unit("KC-0001", review_by="2026-09"),
            unit("KC-0002", review_by="2026-10"),
            unit("KC-0003", review_by="bad"),
            unit("KC-0004", review_by="2025-01", status="retired"),
        )
        due = self.report()["review_due"]
        self.assertEqual([d["id"] for d in due], ["KC-0001", "KC-0003"])
        self.assertEqual(due[1]["reason"], "review_by missing or invalid")

    def test_stale_drafts(self) -> None:
        self.write_units(
            unit("KC-0001", status="draft"),
            unit("KC-0002", status="reviewed"),
            unit("KC-0003", status="draft", file="knowledge/catalog/KC-0003_new.md"),
            age_days=31,
        )
        set_age(self.root / "knowledge/catalog/KC-0003_new.md", 30)
        stale = self.report()["stale_drafts"]
        self.assertEqual([s["id"] for s in stale], ["KC-0001"])
        self.assertEqual(stale[0]["age_days"], 31)
        # The temp root is no git checkout, so the age comes from the mtime.
        self.assertEqual(stale[0]["added_from"], "mtime")

    def test_stale_drafts_prefer_the_git_add_date(self) -> None:
        self.write_units(
            unit("KC-0001", status="draft"),
            unit("KC-0002", status="draft"),
            age_days=0,
        )
        added = {
            "knowledge/catalog/KC-0001_unit.md": kb_status.dt.date(2026, 8, 1),
            "knowledge/catalog/KC-0002_unit.md": None,
        }
        calls: list[tuple[Path, str]] = []

        def fake_git(root: Path, rel: str):
            calls.append((root, rel))
            return added[rel]

        with mock.patch.object(kb_status, "git_added_date", side_effect=fake_git):
            stale = self.report()["stale_drafts"]
        self.assertEqual([(s["id"], s["added"], s["added_from"], s["age_days"]) for s in stale], [("KC-0001", "2026-08-01", "git", 66)])
        self.assertEqual(calls, [(self.root, "knowledge/catalog/KC-0001_unit.md"), (self.root, "knowledge/catalog/KC-0002_unit.md")])
        with mock.patch.object(kb_status, "git_added_date", side_effect=fake_git):
            _code, out = self.run_main()
        self.assertIn("KC-0001 knowledge/catalog/KC-0001_unit.md: draft, added 2026-08-01 per git (66 days)", out)

    def test_git_added_date_outside_a_checkout_is_none(self) -> None:
        self.write_units(unit("KC-0001", status="draft"))
        with mock.patch.dict(os.environ, {"GIT_CEILING_DIRECTORIES": str(self.root.parent)}):
            self.assertIsNone(kb_status.git_added_date(self.root, "knowledge/catalog/KC-0001_unit.md"))

    def test_changed_sources(self) -> None:
        newer = self.capture("newer.md", "2026-08-01")
        older = self.capture("older.md", "2026-05-12")
        self.write_units(
            unit("KC-0001", verification="verified", verified_on="2026-06-01", amazon_sources=[newer, older]),
            unit("KC-0002", verification="unverified", verified_on="", amazon_sources=[newer]),
            unit("KC-0003", verification="verified", verified_on="2026-08-01", amazon_sources=[newer]),
        )
        changed = self.report()["changed_sources"]
        self.assertEqual([(c["id"], c["source"]) for c in changed], [("KC-0001", newer)])
        self.assertEqual(changed[0]["downloaded_at"], "2026-08-01")

    def test_downloaded_at_only_in_frontmatter(self) -> None:
        rel = "Amazon Seller Help/articles/body.md"
        (self.root / rel).write_text("---\ntitle: x\n---\ndownloaded_at: 2026-09-01\n", encoding="utf-8")
        self.assertIsNone(kb_status.downloaded_at(self.root / rel))
        rel2 = self.capture("iso.md", "2026-09-01T10:00:00Z")
        self.assertEqual(kb_status.downloaded_at(self.root / rel2), kb_status.dt.date(2026, 9, 1))

    def test_missing_supersedes(self) -> None:
        kept = self.capture("kept.md", "2026-05-12")
        self.write_units(unit("KC-0001", supersedes=[kept, "MAG SOPs/gone.md"]))
        missing = self.report()["missing_supersedes"]
        self.assertEqual([(m["id"], m["path"]) for m in missing], [("KC-0001", "MAG SOPs/gone.md")])

    def test_plain_and_json_output_exit_zero(self) -> None:
        self.write_units(unit("KC-0001", review_by="2026-01", supersedes=["gone.md"]))
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("Past review_by: 1", out)
        self.assertIn("KC-0001 knowledge/catalog/KC-0001_unit.md: review_by 2026-01", out)
        self.assertIn("Supersedes path no longer exists: 1", out)
        self.assertIn("total: 2", out)
        code, out = self.run_main("--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["today"], TODAY)
        self.assertEqual(len(data["review_due"]), 1)
        self.assertEqual(data["stale_drafts"], [])

    def test_missing_index_exit_zero(self) -> None:
        code, out = self.run_main()
        self.assertEqual(code, 0)
        self.assertIn("not found", out)


if __name__ == "__main__":
    unittest.main()
