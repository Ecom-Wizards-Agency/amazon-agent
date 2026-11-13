import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("sb_builder", Path(__file__).with_name("build_and_deliver.py"))
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
GLOBAL = """# Acme Widget SB Video Briefing
10.11.2026. Market: US. One complete brief.
## Global rules
### Specs (verbatim, non-negotiable)
16:9, 1920x1080. Use the full verified placement specs.
### Absolute do-not list
No invented claims.
"""
TABLE = "| Card | Time | On-screen text (final) | Visual direction |\n|---|---|---|---|\n"


def production_video(number=1):
    return f"## Video {number}: Recognition (target 6 s)\n### Timeline\n" + TABLE + "| A1 | 0–3 s | Product in use. | Show the real product moving. |\n| S1 | 3–6 s | [No added text] | Hold the current pack and loop. |\n"


def concept_video(number=1):
    body = f"## Video {number}: Product fit (target 6 s)\n### Part 1: three openings\n"
    for index in range(1, 4):
        body += f"#### Angle {index}: Criterion {index}\n" + TABLE + f"| A{index} | 0–3 s | Criterion {index}. | Demonstrate this criterion. |\n"
    return body + "### Part 2: shared second half (3–6 s)\n" + TABLE + "| S1 | 3–6 s | [No added text] | Hold the current pack and loop. |\n"


class BuildAndDeliverTests(unittest.TestCase):
    def config(self, mode="production", cuts=1):
        return {
            "briefing": {"mode": mode, "requested_cuts": cuts},
            "client": {"name": "Acme", "product_line": "Widget", "marketplace": "US"},
            "seller_central": {"account_name": "Acme US", "expected_partner_account_id": "PARTNER", "marketplace_label": "United States"},
            "delivery": {"drive_folder_id": "folder", "brief_title": "Acme US - Widget SB Video Briefing"},
        }

    def validate(self, text, cfg=None):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "brief.md"
            path.write_text(text, encoding="utf-8")
            return MODULE.validate_markdown(path, cfg=cfg or self.config())

    def test_brief_only_config_accepts_one_canonical_id(self):
        cfg = self.config()
        cfg["delivery"]["brief_document_id"] = "canonical"
        MODULE.validate_config(cfg)

    def test_production_has_no_angle_or_asset_requirement(self):
        result = self.validate(GLOBAL + production_video())
        self.assertEqual((result["videos"], result["cuts"], result["scripted_cards"]), (1, 1, 2))

    def test_video_duration_accepts_both_amazon_boundaries(self):
        for mode, fixture, cuts in (("production", production_video, 1), ("concept_testing", concept_video, 3)):
            for duration in (6, 45):
                with self.subTest(mode=mode, duration=duration):
                    text = (GLOBAL + fixture()).replace("target 6 s", f"target {duration} s").replace("3–6 s", f"3–{duration} s")
                    self.assertEqual(self.validate(text, self.config(mode, cuts))["cuts"], cuts)

    def test_video_duration_rejects_outside_amazon_boundaries(self):
        for mode, fixture, cuts in (("production", production_video, 1), ("concept_testing", concept_video, 3)):
            for duration in (5, 5.999, 45.001, 46):
                with self.subTest(mode=mode, duration=duration), self.assertRaisesRegex(ValueError, "between 6 and 45"):
                    text = (GLOBAL + fixture()).replace("target 6 s", f"target {duration} s").replace("3–6 s", f"3–{duration} s")
                    self.validate(text, self.config(mode, cuts))

    def test_production_without_amazon_research_needs_no_seller_identity(self):
        cfg = self.config()
        del cfg["seller_central"]
        MODULE.validate_config(cfg)

    def test_concept_testing_requires_seller_identity(self):
        cfg = self.config("concept_testing", 3)
        del cfg["seller_central"]
        with self.assertRaisesRegex(ValueError, "seller_central.account_name"):
            MODULE.validate_config(cfg)

    def test_cut_counts_match_inputs(self):
        with self.assertRaisesRegex(ValueError, "specifies 1 cuts"):
            self.validate(GLOBAL + production_video(), self.config(cuts=2))
        result = self.validate(GLOBAL + production_video() + production_video(2), self.config(cuts=2))
        self.assertEqual((result["videos"], result["cuts"]), (2, 2))

    def test_malformed_extra_video_is_not_silently_dropped(self):
        text = GLOBAL + production_video() + production_video(2).replace("(target 6 s)", "")
        with self.assertRaisesRegex(ValueError, "every Video heading"):
            self.validate(text)

    def test_testing_checks_three_angles_per_concept(self):
        result = self.validate(GLOBAL + concept_video() + concept_video(2), self.config("concept_testing", 6))
        self.assertEqual((result["videos"], result["cuts"], result["scripted_cards"]), (2, 6, 8))
        with self.assertRaisesRegex(ValueError, "each once"):
            self.validate((GLOBAL + concept_video()).replace("#### Angle 2:", "#### Angle 1:"), self.config("concept_testing", 3))

    def test_legacy_config_keeps_concept_mode(self):
        cfg = self.config()
        del cfg["briefing"]
        self.assertEqual(self.validate(GLOBAL + concept_video(), cfg)["cuts"], 3)

    def test_testing_openings_join_shared_sequence(self):
        text = (GLOBAL + concept_video()).replace("| A2 | 0–3 s", "| A2 | 0–4 s")
        with self.assertRaisesRegex(ValueError, "expected 3s"):
            self.validate(text, self.config("concept_testing", 3))

    def test_cards_require_continuity_copy_visuals_unique_ids_and_textless_end(self):
        changes = (
            ("| S1 | 3–6 s", "| S1 | 4–6 s", "gap or overlap"),
            ("target 6 s", "target 7 s", "expected 7s"),
            ("Show the real product moving.", "", "every card"),
            ("| S1 |", "| A1 |", "duplicate card"),
            ("Product in use.", "This visible card has far too many words.", "seven words"),
            ("[No added text]", "Buy now", "textless"),
        )
        for before, after, error in changes:
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                self.validate((GLOBAL + production_video()).replace(before, after))

    def test_reading_time_checks_characters_as_well_as_word_count(self):
        copy = "Exceptionallylongword extraordinarilylongword substantivelylongword"
        text = (GLOBAL + production_video()).replace("Product in use.", copy)
        with self.assertRaisesRegex(ValueError, "seconds for readable copy"):
            self.validate(text)

    def test_bad_mode_and_count_fail_config(self):
        for options in ({"mode": "unknown"}, {"mode": "production"}, {"mode": "production", "requested_cuts": True}):
            cfg = self.config()
            cfg["briefing"] = options
            with self.subTest(options=options), self.assertRaises(ValueError):
                MODULE.validate_config(cfg)

    def test_legacy_keys_warn(self):
        cfg = self.config()
        cfg["client"]["amazon_account"] = "old"
        cfg["economics"] = {"break_even_acos": 0.5}
        cfg["testing"] = {}
        cfg["delivery"]["reference_document_id"] = "historical"
        self.assertEqual(len(MODULE.legacy_warnings(cfg)), 4)

    def test_claims_appendix_rejected(self):
        with self.assertRaisesRegex(ValueError, "forbidden"):
            self.validate("## Claims and compliance (advisory)\n")

    def test_portable_helper_runs_outside_repository(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "brief.md"
            path.write_text(GLOBAL + production_video(), encoding="utf-8")
            result = subprocess.run([sys.executable, "-I", "-B", str(MODULE.VALIDATOR), "--brief-md", str(path), "--mode", "production", "--requested-cuts", "1"], cwd=td, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["cuts"], 1)

    def delivery(self, existing=False, legacy=False):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            cfg = self.config()
            if existing:
                cfg["delivery"]["brief_document_id"] = "canonical"
            if legacy:
                cfg["delivery"].update(reference_title="Old reference", reference_document_id="historical")
            config, brief = root / "config.json", root / "brief.md"
            config.write_text(json.dumps(cfg), encoding="utf-8")
            brief.write_text(GLOBAL + production_video(), encoding="utf-8")
            argv = ["builder", "--config", str(config), "--brief-md", str(brief), "--outdir", td]
            if legacy:
                argv += ["--reference-md", str(root / "missing-reference.md")]
            with patch.object(sys, "argv", argv), patch.object(MODULE, "render_brief", return_value=root / "brief.docx") as render, patch.object(MODULE, "update_existing_document") as update, patch.object(MODULE, "deliver_one", return_value={"url": "https://docs.google.com/document/d/new-brief/edit"}) as deliver, patch.object(MODULE, "verify_document", return_value={"document_id": "verified"}) as verify, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(MODULE.main(), 0)
            manifest = json.loads((root / "delivery-manifest.json").read_text())
            self.assertEqual(len(manifest["documents"]), 1)
            self.assertEqual(manifest["status"], "delivered_pending_visual_qa")
            render.assert_called_once()
            verify.assert_called_once()
            if existing:
                update.assert_called_once_with("canonical", brief)
                deliver.assert_not_called()
                self.assertEqual(verify.call_args.args[0], "canonical")
            else:
                update.assert_not_called()
                deliver.assert_called_once()
                self.assertEqual(verify.call_args.args[0], "new-brief")

    def test_create_delivers_one_document(self):
        self.delivery()

    def test_update_preserves_brief_id_without_reference_id(self):
        self.delivery(existing=True)

    def test_legacy_reference_is_never_read_or_written(self):
        self.delivery(existing=True, legacy=True)

    def test_validate_only_uses_no_renderer_or_connector(self):
        with tempfile.TemporaryDirectory() as td:
            config, brief = Path(td) / "config.json", Path(td) / "brief.md"
            config.write_text(json.dumps(self.config()), encoding="utf-8")
            brief.write_text(GLOBAL + production_video(), encoding="utf-8")
            with patch.object(sys, "argv", ["builder", "--config", str(config), "--brief-md", str(brief), "--validate-only"]), patch.object(MODULE, "render_brief") as render, patch.object(MODULE, "composio") as connector, contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(MODULE.main(), 0)
                render.assert_not_called()
                connector.assert_not_called()

    def test_readback_catches_missing_later_script_cells(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "brief.md"
            path.write_text("# Title\nFirst line.\n" + TABLE + "| S1 | 0–3 s | Essential final copy | Final shot |\n", encoding="utf-8")
            metadata = {"name": "Brief", "mimeType": "application/vnd.google-apps.document", "parents": ["folder"]}
            with patch.object(MODULE, "composio", side_effect=[metadata, {"content": "First line."}]):
                with self.assertRaisesRegex(RuntimeError, "content readback failed"):
                    MODULE.verify_document("id", "Brief", "folder", path, Path(td) / "brief.pdf")

    def test_readback_uses_native_text_for_markdown_lists_and_links(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "brief.md"
            path.write_text("# Title\n> Specs text\n- **Final copy**\n1. [Asset](https://example.com/asset)\n*Warm light* and _natural skin_.\n", encoding="utf-8")
            self.assertEqual(MODULE.source_fragments(path), ["Specs text", "Final copy", "Asset", "Warm light and natural skin."])

    def test_existing_document_bounds_keep_final_newline(self):
        document = {"data": {"tabs": [{"tabProperties": {"tabId": "t.0"}, "documentTab": {"body": {"content": [{"endIndex": 1}, {"endIndex": 42}]}}}]}}
        self.assertEqual(MODULE.first_tab_bounds(document), ("t.0", 41))

    def test_markdown_body_drops_h1(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "brief.md"
            path.write_text("# Canonical title\n\nFirst line.\n", encoding="utf-8")
            self.assertEqual(MODULE.markdown_body(path), "First line.\n")

    def test_document_id_from_url(self):
        self.assertEqual(MODULE.document_id_from_url("https://docs.google.com/document/d/abc_DEF-123/edit"), "abc_DEF-123")


if __name__ == "__main__":
    unittest.main()
