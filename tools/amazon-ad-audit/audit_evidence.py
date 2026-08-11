#!/usr/bin/env python3
"""Select high-value screenshot evidence for the branded audit narrative."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

PROHIBITED = {"sqp", "google_sheet", "workbook", "spreadsheet"}


def image_size(path):
    data = Path(path).read_bytes()[:32]
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return struct.unpack(">II", data[16:24])
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (0, 0)


def image_content_fraction(path):
    """Estimate how much of a capture contains visible content rather than blank white space."""
    try:
        from PIL import Image, ImageStat
        with Image.open(path) as im:
            sample = im.convert("L")
            sample.thumbnail((400, 400))
            hist = sample.histogram()
            pixels = max(1, sum(hist))
            nonwhite = sum(hist[:245]) / pixels
            contrast = ImageStat.Stat(sample).stddev[0]
            return nonwhite, contrast
    except Exception:
        return None


def select(candidates, *, expected_account=None, marketplace=None,
           target=8, maximum=10, min_width=600, min_height=350):
    accepted = []
    rejected = []
    hashes = set()
    distinct = set()
    # Python's sort is stable, so equal-priority candidates keep the capture order.
    # The capture manifest is evidence chronology and should decide which duplicate survives.
    ordered = sorted(candidates, key=lambda x: -int(x.get("priority", 0)))
    for row in ordered:
        reason = None
        path = Path(row.get("path", ""))
        kind = str(row.get("source_kind", "")).lower()
        if kind in PROHIBITED:
            reason = f"prohibited source kind: {kind}"
        elif not row.get("finding") or not row.get("caption"):
            reason = "missing named finding or caption"
        elif expected_account and row.get("account") and row["account"] != expected_account:
            reason = "wrong account"
        elif marketplace and row.get("marketplace") and row["marketplace"] != marketplace:
            reason = "wrong marketplace"
        elif not path.exists() or not path.is_file():
            reason = "missing file"
        else:
            width, height = image_size(path)
            if width < min_width or height < min_height:
                reason = f"unreadable dimensions: {width}x{height}"
            else:
                content = image_content_fraction(path)
                if content and content[0] < 0.03 and content[1] < 18:
                    reason = f"blank or unreadable capture: content={content[0]:.1%}, contrast={content[1]:.1f}"
        digest = None
        if reason is None:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest in hashes:
                reason = "duplicate image"
        key = row.get("distinct_key") or row.get("finding")
        if reason is None and key in distinct and not row.get("must_include"):
            reason = "duplicate finding"
        if reason:
            rejected.append({"id": row.get("id"), "reason": reason})
            continue
        high_value_extra = int(row.get("priority", 0)) >= 90 and row.get("must_include")
        if len(accepted) >= target and not high_value_extra:
            rejected.append({"id": row.get("id"), "reason": "soft target reached"})
            continue
        if len(accepted) >= maximum:
            rejected.append({"id": row.get("id"), "reason": "hard maximum reached"})
            continue
        selected = dict(row)
        selected["width"], selected["height"] = image_size(path)
        content = image_content_fraction(path)
        if content:
            selected["content_fraction"], selected["contrast"] = content
        accepted.append(selected)
        hashes.add(digest)
        distinct.add(key)
    return {"selected": accepted, "rejected": rejected, "target": target, "maximum": maximum}


def run(candidates_path, out_path, **kwargs):
    candidates = json.loads(Path(candidates_path).read_text())
    if isinstance(candidates, dict):
        candidates = candidates.get("candidates", [])
    payload = select(candidates, **kwargs)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidates", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--account")
    ap.add_argument("--marketplace")
    ap.add_argument("--target", type=int, default=8)
    ap.add_argument("--maximum", type=int, default=10)
    args = ap.parse_args()
    print(run(args.candidates, args.out, expected_account=args.account,
              marketplace=args.marketplace, target=args.target, maximum=args.maximum))
