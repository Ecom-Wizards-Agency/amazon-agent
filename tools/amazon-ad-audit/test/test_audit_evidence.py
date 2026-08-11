import binascii
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from audit_evidence import select


def png(path, width=800, height=600, color=(255, 255, 255)):
    raw = b"".join(b"\x00" + bytes(color) * width for _ in range(height))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", binascii.crc32(kind + data) & 0xffffffff)
    payload = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    payload += chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    path.write_bytes(payload)


class EvidenceSelectionTest(unittest.TestCase):
    def test_filters_prohibited_wrong_and_duplicate_images(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            good = root / "good.png"
            duplicate = root / "duplicate.png"
            small = root / "small.png"
            png(good, color=(0, 0, 0))
            duplicate.write_bytes(good.read_bytes())
            png(small, 300, 200, color=(0, 0, 0))
            base = {"finding": "suppression", "caption": "Listing status", "section": "performance",
                    "account": "UltimaPeak US", "marketplace": "US", "priority": 80}
            rows = [
                {**base, "id": "good", "path": str(good), "source_kind": "seller_central"},
                {**base, "id": "dup", "path": str(duplicate), "source_kind": "seller_central",
                 "distinct_key": "other"},
                {**base, "id": "sqp", "path": str(good), "source_kind": "sqp"},
                {**base, "id": "small", "path": str(small), "source_kind": "amazon_pdp",
                 "distinct_key": "small"},
                {**base, "id": "wrong", "path": str(good), "source_kind": "amazon_pdp",
                 "account": "Other", "distinct_key": "wrong"},
            ]
            result = select(rows, expected_account="UltimaPeak US", marketplace="US")
            self.assertEqual([x["id"] for x in result["selected"]], ["good"])
            reasons = {x["id"]: x["reason"] for x in result["rejected"]}
            self.assertIn("duplicate", reasons["dup"])
            self.assertIn("prohibited", reasons["sqp"])
            self.assertIn("unreadable", reasons["small"])
            self.assertEqual(reasons["wrong"], "wrong account")

    def test_rejects_blank_capture_when_image_analysis_is_available(self):
        try:
            from PIL import Image  # noqa: F401
        except ImportError:
            self.skipTest("Pillow is not installed in this Python runtime")
        with tempfile.TemporaryDirectory() as td:
            blank = Path(td) / "blank.png"
            png(blank, color=(255, 255, 255))
            result = select([{
                "id": "blank", "path": str(blank), "source_kind": "competitor_creative",
                "finding": "A+ content", "caption": "A+", "section": "listing",
            }])
            self.assertEqual(result["selected"], [])
            self.assertIn("blank", result["rejected"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
