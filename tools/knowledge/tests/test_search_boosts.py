from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SEARCH_PATH = REPO / "tools" / "search_amazon_libraries.py"

_spec = importlib.util.spec_from_file_location("search_amazon_libraries", SEARCH_PATH)
assert _spec is not None and _spec.loader is not None
search = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(search)

NOTICE = "Your listing has been removed because it is missing required compliance information."


def meta(**extra: object) -> dict:
    base: dict = {"symptom_keywords": [], "error_text": [], "verification": "unverified"}
    base.update(extra)
    return base


class ErrorTextBoostTests(unittest.TestCase):
    def boost(self, query: str, **extra: object) -> int:
        return search.knowledge_boost(meta(**extra), search.tokenize(query))

    def test_single_token_code_exact_match(self) -> None:
        self.assertEqual(self.boost("FBA_INB_0008 retry", error_text=["FBA_INB_0008"]), 120)
        self.assertEqual(self.boost("fba_inb_0008", error_text=["FBA_INB_0008"]), 120)

    def test_verbatim_notice_gets_the_boost(self) -> None:
        self.assertEqual(self.boost(NOTICE, error_text=[NOTICE]), 120)
        self.assertEqual(self.boost(NOTICE.upper().rstrip("."), error_text=[NOTICE]), 120)

    def test_part_of_a_notice_gets_the_boost(self) -> None:
        self.assertEqual(self.boost("missing required compliance information", error_text=[NOTICE]), 120)

    def test_query_longer_than_the_notice_gets_no_boost(self) -> None:
        self.assertEqual(self.boost(NOTICE + " what now", error_text=[NOTICE]), 0)

    def test_one_common_word_inside_a_notice_gets_no_boost(self) -> None:
        self.assertEqual(self.boost("listing", error_text=[NOTICE]), 0)

    def test_containment_respects_token_boundaries(self) -> None:
        self.assertEqual(self.boost("required compliance info", error_text=[NOTICE]), 0)
        self.assertEqual(self.boost("isting has", error_text=[NOTICE]), 0)

    def test_boost_counts_once_and_stacks_with_verification(self) -> None:
        self.assertEqual(
            self.boost("FBA_INB_0008", error_text=["FBA_INB_0008", "fba_inb_0008"], verification="verified"),
            135,
        )

    def test_no_error_text(self) -> None:
        self.assertFalse(search.error_text_hit([], ["anything"]))
        self.assertEqual(self.boost(NOTICE), 0)


if __name__ == "__main__":
    unittest.main()
