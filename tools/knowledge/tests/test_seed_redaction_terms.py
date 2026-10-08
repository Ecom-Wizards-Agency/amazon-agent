from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "knowledge"))

import seed_redaction_terms as seed  # noqa: E402

OPS = {
    "client_slug": "nordwind-labs",
    "profiles": [
        {
            "profile_name": "Nordwind Labs US",
            "seller_central_name": "Nordwind Labs LLC",
            "amazon_ads_ppc_name": "Nordwind (same as Seller Central)",
            "main_stakeholders": "Mara Feld (CEO), Olek and Ines Brandt. Co-owner: Kai Vos (ops). Prefers email.",
            "website": "https://www.nordwindlabs.test/",
            "monitoring": {"enabled": True},
            "reshipment": {"target_stock_days": 60},
        }
    ],
}
CONFIG = {
    "client_message_rollout": {"required_score": 9, "regular_delivery": "weekly"},
    "clients": [{"name": "Kestrel Goods", "slug": "kestrel-goods", "channel_id": "C-test", "active": True}],
    "weekly_account_report": {"client_accounts": {"Heron Home": [{"account": "Heron Home EU", "currency": "EUR"}]}},
}


class SeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.vault = tmp / "vault"
        client = self.vault / "Clients" / "Nordwind Labs"
        client.mkdir(parents=True)
        (self.vault / "Clients" / "_Archive").mkdir()
        (client / "Nordwind Labs.md").write_text("---\ntype: client\nslug: nordwind-labs\n---\n", encoding="utf-8")
        ops = "# Amazon Ops\n\n```json\n" + json.dumps(OPS) + "\n```\n"
        (client / "Amazon Ops.md").write_text(ops, encoding="utf-8")
        self.config = tmp / "config.json"
        self.config.write_text(json.dumps(CONFIG), encoding="utf-8")
        self.seed_file = tmp / "seed.txt"
        self.seed_file.write_text("# seed\nOld Partner\nformer brand\n", encoding="utf-8")
        self.out = tmp / "terms.txt"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_seed(self) -> str:
        buf = io.StringIO()
        args = ["--vault", str(self.vault), "--config", str(self.config), "--out", str(self.out)]
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
            code = seed.main([*args, "--manual-seed", str(self.seed_file)])
        self.assertEqual(code, 0)
        return buf.getvalue()

    def generated(self) -> list[str]:
        lines = self.out.read_text(encoding="utf-8").splitlines()
        start = lines.index(seed.GENERATED_MARK) + 1
        end = lines.index(seed.MANUAL_MARK)
        return [line for line in lines[start:end] if line.strip()]

    def test_collects_vault_and_config_terms(self) -> None:
        self.run_seed()
        terms = {t.casefold() for t in self.generated()}
        expected = {
            "nordwind labs",
            "nordwind-labs",
            "nordwind labs us",
            "nordwind labs llc",
            "nordwind",
            "mara feld",
            "olek",
            "ines brandt",
            "kai vos",
            "nordwindlabs.test",
            "nordwindlabs",
            "kestrel goods",
            "kestrel-goods",
            "heron home",
            "heron home eu",
        }
        self.assertTrue(expected <= terms, expected - terms)
        for junk in ("_archive", "prefers email", "required_score", "weekly", "c-test", "eur", "true", "60"):
            self.assertNotIn(junk, terms)

    def test_header_and_first_run_manual_seed(self) -> None:
        output = self.run_seed()
        text = self.out.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(seed.HEADER + "\n"))
        self.assertTrue(text.endswith(f"{seed.MANUAL_MARK}\nOld Partner\nformer brand\n"))
        self.assertIn("manual terms: 2", output)
        self.assertIn(f"generated terms: {len(self.generated())}", output)

    def test_manual_section_survives_rerun(self) -> None:
        self.run_seed()
        text = self.out.read_text(encoding="utf-8")
        self.out.write_text(text + "# added by hand\nLocal Courier\n", encoding="utf-8")
        self.seed_file.write_text("Ignored On Rerun\n", encoding="utf-8")
        output = self.run_seed()
        text = self.out.read_text(encoding="utf-8")
        self.assertTrue(text.endswith("Old Partner\nformer brand\n# added by hand\nLocal Courier\n"))
        self.assertNotIn("Ignored On Rerun", text)
        self.assertIn("manual terms: 3", output)

    def test_keep_term_filters(self) -> None:
        for value in ("ab", "Amazon", "brand", "null", None, True, 12, "2026-10"):
            with self.subTest(value=value):
                self.assertIsNone(seed.keep_term(value))
        self.assertEqual(seed.keep_term(" Kestrel "), "Kestrel")


if __name__ == "__main__":
    unittest.main()
