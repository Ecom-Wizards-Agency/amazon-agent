"""The offer verdict is measured, never asserted.

Two sentences in the workbook builder used to hardcode one client's competitive situation
("price outlier in a commodity category", then "price is close to the category median").
Each was true for the client it was written against and false for the next one. These tests
pin the wording to the data so the next tuning pass cannot reintroduce a fixed verdict.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build_audit_workbook import _offer_gap, _price_phrase, _proof_phrase  # noqa: E402
from narrative_scaffold import build  # noqa: E402


def comp(price, rating, reviews, med_price=16.25, med_rating=4.1, med_reviews=165):
    return dict(median_price=med_price, median_rating=med_rating, median_reviews=med_reviews,
                competitors=[dict(asin="A1", price=price, rating=rating, reviews=reviews, is_client=True),
                             dict(asin="B1", price=med_price, rating=med_rating, reviews=med_reviews)])


class OfferVerdictTest(unittest.TestCase):
    def test_premium_price_is_never_called_close_to_the_median(self):
        # The real V Gummies shape: EUR 24.95 against a EUR 16.25 median, 54% above.
        gap = _offer_gap(comp(24.95, 4.1, 972))
        self.assertAlmostEqual(gap["premium"], 0.535, places=2)
        phrase = _price_phrase(gap)
        self.assertIn("54% above the category median", phrase)
        self.assertNotIn("close to", phrase)

    def test_review_lead_is_not_reported_as_a_shortfall(self):
        # 972 reviews against a 165 median is a lead, not the "far fewer reviews" the
        # hardcoded sentence claimed.
        proof = _proof_phrase(_offer_gap(comp(24.95, 4.1, 972)))
        self.assertIn("well over the benchmark field", proof)
        self.assertNotIn("under", proof)

    def test_rating_shortfall_is_named_with_its_size(self):
        proof = _proof_phrase(_offer_gap(comp(16.00, 3.6, 60)))
        self.assertIn("rating trails the median by 0.5", proof)
        self.assertIn("well under the benchmark field", proof)

    def test_an_average_offer_produces_no_claim_at_all(self):
        gap = _offer_gap(comp(16.25, 4.1, 165))
        self.assertIsNone(_price_phrase(gap))
        self.assertIsNone(_proof_phrase(gap))

    def test_no_client_row_or_no_benchmark_yields_no_gap(self):
        self.assertIsNone(_offer_gap(None))
        self.assertIsNone(_offer_gap(dict(median_price=16.25, competitors=[
            dict(asin="B1", price=16.25, rating=4.1, reviews=165)])))


METRICS = {
    "client": "Fixture", "currency": "USD", "marketplaces": ["US"], "breakeven": 0.5,
    "channels_present": ["SP"],
    "windows": {"ads": "2026-01-01..2026-01-28", "business_report": "same", "sqp_weeks": []},
    "totals": {"spend": 100.0, "sales": 250.0, "br_total_sales": 500.0,
               "acos": 0.4, "tacos": 0.2, "ad_dependency": 0.5},
    "searchterm_bucket": {
        "Branded": {"spend": 40.0, "sales": 120.0, "acos": 1 / 3, "cvr": 0.2},
        "Generic": {"spend": 60.0, "sales": 130.0, "acos": 60 / 130, "cvr": 0.1}},
    "placement": {"Top of Search": {"spend": 60.0, "sales": 200.0, "acos": 0.3},
                  "Product Pages": {"spend": 40.0, "sales": 50.0, "acos": 0.8}},
    "business_report": {"rows": [{"asin": "B0FIXTURE0", "group": "Core", "sessions": 100,
                                  "units": 20, "sales": 500.0, "buybox": 0.95}]},
}


class RelaunchFramingTest(unittest.TestCase):
    """"The retail foundation" is one client's outage. It must not narrate a healthy account."""

    def _render(self, disruption):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        cfg = {"brand_tokens": ["fixture"], "competitor_tokens": ["rival"], "inputs": {},
               "narrative": {"mode": "evidence_hybrid", "include_levers": True,
                             "include_what_can_be_reached": True}}
        if disruption:
            cfg["comparison_windows"] = {"disruption": "2026-07-12..2026-08-08",
                                         "online_control": "2026-05-31..2026-06-27"}
        (root / "config.json").write_text(json.dumps(cfg))
        (root / "metrics.json").write_text(json.dumps(METRICS))
        rendered = build(root / "config.json", root, force=True).read_text()
        tmp.cleanup()
        return rendered

    def test_healthy_account_gets_no_relaunch_language(self):
        rendered = self._render(disruption=False)
        self.assertNotIn("relaunch", rendered)
        self.assertNotIn("retail foundation", rendered)
        self.assertIn("## What can be reached", rendered)

    def test_incident_audit_keeps_relaunch_language(self):
        rendered = self._render(disruption=True)
        self.assertIn("relaunch", rendered)
        self.assertIn("Restore the retail foundation", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
