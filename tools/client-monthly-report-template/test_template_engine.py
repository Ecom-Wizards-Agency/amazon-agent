from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from template_engine import MarketplacePart, monthly_delivery_directory


class TemplateEngineTests(unittest.TestCase):
    def test_monthly_delivery_directory_uses_required_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            destination = monthly_delivery_directory("July", Path(temp_dir))
            self.assertEqual(destination, Path(temp_dir) / "July Monthly Reports")
            self.assertTrue(destination.is_dir())

    def test_monthly_delivery_directory_rejects_path_input(self) -> None:
        with self.assertRaises(ValueError):
            monthly_delivery_directory("July/Reports", create=False)

    def test_marketplace_part_requires_source_boundaries(self) -> None:
        part = MarketplacePart(
            code="US",
            display_name="United States",
            currency_symbol="$",
            sellerboard_account="Brand US",
            adlabs_profile="Brand US",
            adlabs_dashboard="Brand US",
        )
        part.validate()

        invalid = MarketplacePart(
            code="AU",
            display_name="Australia",
            currency_symbol="A$",
            sellerboard_account="",
            adlabs_profile="Brand AU",
            adlabs_dashboard="Brand AU",
            datadive_supported=False,
        )
        with self.assertRaisesRegex(ValueError, "sellerboard_account"):
            invalid.validate()


if __name__ == "__main__":
    unittest.main()
