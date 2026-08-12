"""Hard-wrapped markdown must render as paragraphs, not as one paragraph per line.

The block parser is line-based. Before unwrap_soft_breaks() a prose paragraph wrapped at
100 columns became one docx paragraph per line, and any inline span straddling a wrap
shipped to the client as literal asterisks. Four reached a delivered audit.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_branded import unwrap_soft_breaks, parse_markdown  # noqa: E402


class UnwrapSoftBreaksTest(unittest.TestCase):
    def test_bold_across_a_wrap_survives_as_one_span(self):
        md = "You convert at **13.3% against a market\n9.0%**. That is good."
        self.assertEqual(unwrap_soft_breaks(md),
                         "You convert at **13.3% against a market 9.0%**. That is good.")
        _, blocks = parse_markdown(md, ".")
        self.assertEqual([b[0] for b in blocks], ["p"])
        self.assertNotIn("\n", blocks[0][1])

    def test_indented_continuation_joins_its_bullet(self):
        md = "- Ads bulk export, including SP and SB\n  plus the search-term reports\n- Second bullet"
        _, blocks = parse_markdown(md, ".")
        self.assertEqual([b[0] for b in blocks], ["bul", "bul"])
        self.assertEqual(blocks[0][1], "Ads bulk export, including SP and SB plus the search-term reports")

    def test_block_constructs_still_start_their_own_block(self):
        md = ("## Ads Summary\nYou spend a lot.\n\n| a | b |\n| 1 | 2 |\n\n"
              "> a pull note\n\n![cap](x.png)\n\n### Priority 1: Do the thing\nBody line one.")
        _, blocks = parse_markdown(md, ".")
        self.assertEqual([b[0] for b in blocks],
                         ["h2", "p", "table", "note", "img", "h3", "p"])

    def test_a_blank_line_still_separates_paragraphs(self):
        _, blocks = parse_markdown("one a\none b\n\ntwo", ".")
        self.assertEqual(blocks, [("p", "one a one b"), ("p", "two")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
