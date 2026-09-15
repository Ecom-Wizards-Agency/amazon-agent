#!/usr/bin/env python3
"""Render the checked-in rights table, or check it without writing."""
import argparse
from pathlib import Path

from rights_matrix import load, render_table, validate

ROOT = Path(__file__).resolve().parents[2]
BEGIN = "<!-- rights-matrix:begin -->"
END = "<!-- rights-matrix:end -->"


def rendered_readme(matrix, source):
    if source.count(BEGIN) != 1 or source.count(END) != 1 or source.index(BEGIN) >= source.index(END):
        raise ValueError("README needs one ordered pair of rights-matrix markers")
    before, tail = source.split(BEGIN)
    _, after = tail.split(END)
    return before + BEGIN + "\n\n" + render_table(matrix) + "\n" + END + after


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 on stale output; do not write")
    args = parser.parse_args(argv)
    matrix = load(ROOT / "docs/rights/capability-matrix.json")
    errors = validate(matrix)
    if errors:
        parser.exit(1, "\n".join(errors) + "\n")
    path = ROOT / "docs/rights/README.md"
    source = path.read_text(encoding="utf-8")
    result = rendered_readme(matrix, source)
    if args.check:
        if result != source:
            parser.exit(1, "rights README is stale; run tools/rights/render_rights_matrix.py\n")
    else:
        path.write_text(result, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
