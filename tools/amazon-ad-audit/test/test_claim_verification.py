import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from claim_verification import VERDICTS, evaluate_cart_claim, parse_search_catalog_performance


def row(**overrides):
    base = {
        "query": "performance gummies",
        "impressions": 1000,
        "clicks": 100,
        "cart_adds": 20,
        "purchases": 10,
        "market_clicks": 1000,
        "market_cart_adds": 300,
        "market_purchases": 200,
        "weeks": 4,
    }
    base.update(overrides)
    return base


class CartClaimTest(unittest.TestCase):
    def test_confirms_material_underperformance(self):
        result = evaluate_cart_claim([row()])
        self.assertEqual(result["verdict"], VERDICTS["confirmed"])

    def test_rejects_when_asin_beats_market(self):
        result = evaluate_cart_claim([row(cart_adds=40, purchases=30)])
        self.assertEqual(result["verdict"], VERDICTS["not_supported"])

    def test_marks_suppression_as_confounded(self):
        result = evaluate_cart_claim([row()], suppression_confounded=True)
        self.assertEqual(result["verdict"], VERDICTS["mixed"])

    def test_rejects_thin_single_week(self):
        result = evaluate_cart_claim([row(impressions=80, clicks=4, weeks=1)])
        self.assertEqual(result["verdict"], VERDICTS["not_verifiable"])

    def test_missing_queries_during_suppression_are_confounded(self):
        result = evaluate_cart_claim([], suppression_confounded=True)
        self.assertEqual(result["verdict"], VERDICTS["mixed"])

    def test_parses_report_fetcher_scp_headers(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scp.csv"
            path.write_text(
                "Impressions: Impressions,Clicks: Clicks,Cart Adds: Cart Adds,Purchases: Purchases\n"
                "1000,100,50,25\n",
                encoding="utf-8",
            )
            result = parse_search_catalog_performance(path)
        self.assertEqual(result["impressions"], 1000)
        self.assertEqual(result["cart_adds"], 50)
        self.assertEqual(result["cart_to_purchase_rate"], 0.5)


if __name__ == "__main__":
    unittest.main()
