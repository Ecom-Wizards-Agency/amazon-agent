#!/usr/bin/env python3
"""Stage finished listing images for the attended-images mode and host them.

intake:  read a manifest CSV (sku, slot, file, source_ref), check each image,
         convert JPEG to PNG, copy the PNG into the wizards-ai broker root as
         <sha256>.png and write one provenance receipt. Nothing leaves the machine.
publish: host every receipt entry through wizards-ai cloudinary_assets.publish,
         which returns a URL only after the public bytes match the SHA-256, and
         write the `images` list for an operations.py `listing.images` request.
compare: after a direct image write, Amazon's live listing shows its own
         m.media-amazon.com URL, never the URL we submitted. Download that image and
         compare it with the archived PNG of the same receipt entry (aspect ratio, a
         256-bit dHash and the mean colour difference of 32x32 RGB thumbnails) to confirm
         the right picture landed in the slot. When the pixel check carries before_url
         (the slot's image before the write), that image is fetched too; a check whose
         archived PNG is also within every threshold of the before image cannot tell the
         two apart, so it is reported as not discriminating and never matches.

Run with the wizards-ai virtualenv (Pillow, broker client):
  ~/os/wizards-ai/venv/bin/python skills/amazon-flatfilepro/scripts/image_intake.py intake \
      --manifest manifest.csv --receipt output/<client>/catalog/<run>/intake-receipt.json
  ~/os/wizards-ai/venv/bin/python skills/amazon-flatfilepro/scripts/image_intake.py publish \
      --receipt output/<client>/catalog/<run>/intake-receipt.json
  ~/os/wizards-ai/venv/bin/python skills/amazon-flatfilepro/scripts/image_intake.py compare \
      --receipt output/<client>/catalog/<run>/intake-receipt.json \
      --verify output/<client>/catalog/<run>/verify/001-1.json [--sku S --slot PT01] \
      [--max-dhash 24] [--max-aspect-delta 0.02] [--max-color-delta 12] [--out FILE]

Manifest `file` paths may be absolute or relative to the current directory. Exit 0
on success, 2 when any row is refused (every refusal is listed; nothing is archived
or hosted for a refused manifest) or when hosting refuses an entry. compare exits 0
when every checked slot matches (aspect, dHash and colour within the thresholds, and
discriminating) and 2 on any mismatch or refusal; its result goes to
--out (default <verify stem>-pixels.json beside the verify file, never overwritten).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MAX_BYTES = 10_000_000  # Cloudinary Free rejects larger images; the broker allows 25 MiB.
MIN_SIDE, MAX_SIDE = 500, 10_000
SLOT = re.compile(r"MAIN|PT0[1-9]")
ARCHIVE = Path("mentions/bulk-images/source-archive")
AMAZON_IMAGE_HOST = "m.media-amazon.com"
FETCH_TIMEOUT = 30
FETCH_MAX_BYTES = 30_000_000
# Provisional thresholds: recalibrate after the first live direct image write shows how far
# Amazon's re-encoded copy drifts from the archived PNG.
DEFAULT_MAX_DHASH = 24  # of 256 bits
DEFAULT_MAX_ASPECT_DELTA = 0.02
DEFAULT_MAX_COLOR_DELTA = 12  # mean absolute per-channel difference, 0-255


class Refused(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def wizards_root(value: str | None) -> Path:
    root = Path(value or os.environ.get("WIZARDS_AI_ROOT") or Path.home() / "os" / "wizards-ai").expanduser().resolve()
    if not (root / "cloudinary_assets.py").is_file() or not (root / ARCHIVE).is_dir():
        raise Refused(f"wizards-ai checkout with {ARCHIVE} not found at {root}")
    return root


def read_manifest(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {"sku", "slot", "file", "source_ref"} <= set(reader.fieldnames):
            raise Refused("manifest needs columns sku, slot, file, source_ref")
        rows = list(reader)
    if not rows:
        raise Refused("manifest has no rows")
    extra = [number for number, row in enumerate(rows, start=2) if None in row]
    if extra:
        raise Refused("rows with more cells than the header: " + ", ".join(map(str, extra)))
    return [{k: (v or "").strip() for k, v in row.items()} for row in rows]


ORIENTATION = 0x0112


def png_bytes(path: Path) -> tuple[bytes, dict]:
    """Return upright PNG bytes plus facts about the supplied file; refuse anything unusable."""
    from PIL import Image, ImageOps

    if path.is_symlink() or not path.is_file():
        raise Refused(f"{path}: not a regular file")
    original = path.read_bytes()
    try:
        with Image.open(io.BytesIO(original)) as im:
            fmt, size = im.format, im.size
            im.verify()
    except Exception:
        raise Refused(f"{path}: not a readable image") from None
    if fmt not in {"PNG", "JPEG", "MPO"}:
        raise Refused(f"{path}: {fmt} is not PNG or JPEG")
    if fmt == "PNG":
        # PNG bytes are hosted unchanged, so a rotation tag would be lost on the way to Amazon.
        with Image.open(io.BytesIO(original)) as im:
            if im.getexif().get(ORIENTATION, 1) != 1:
                raise Refused(f"{path}: PNG carries an EXIF rotation; re-export it upright without the tag")
        data = original
    else:
        # Camera JPEGs (MPO is a multi-picture JPEG) often store sideways pixels plus a rotation
        # tag; apply it so the hosted PNG looks the way the operator saw the file. MPO uses frame 0.
        with Image.open(io.BytesIO(original)) as im:
            im.seek(0)
            upright = ImageOps.exif_transpose(im).convert("RGB")
            size = upright.size
            out = io.BytesIO()
            upright.save(out, format="PNG")
            data = out.getvalue()
    if min(size) < MIN_SIDE or max(size) > MAX_SIDE:
        raise Refused(f"{path}: {size[0]}x{size[1]} px is outside {MIN_SIDE} to {MAX_SIDE} px per side")
    facts = {"original_format": fmt, "original_sha256": sha256(original), "original_bytes": len(original),
             "width": size[0], "height": size[1], "converted": fmt != "PNG"}
    if len(data) > MAX_BYTES:
        raise Refused(f"{path}: PNG is {len(data)} bytes, over the {MAX_BYTES}-byte hosting limit; re-export smaller")
    return data, facts


def archive_target(root: Path, data: bytes) -> Path:
    """Name <sha256>.png; an existing file there must be a regular file with the same bytes."""
    target = root / ARCHIVE / f"{sha256(data)}.png"
    if target.is_symlink() or (target.exists() and (not target.is_file() or sha256(target.read_bytes()) != sha256(data))):
        raise Refused(f"{target} exists with different content")
    return target


def archive(target: Path, data: bytes) -> None:
    """Write through a synced temp file and a hard link, so the name never holds partial bytes."""
    if target.exists():
        return
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    with open(temporary, "xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        os.link(temporary, target)
    except FileExistsError:
        if sha256(target.read_bytes()) != sha256(data):
            raise Refused(f"{target} exists with different content") from None
    finally:
        temporary.unlink()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def intake(args) -> dict:
    root = wizards_root(args.wizards_ai)
    rows = read_manifest(Path(args.manifest))
    if Path(args.receipt).exists():
        raise Refused(f"{args.receipt} already exists; use a new receipt per batch")
    errors, staged, seen = [], [], set()
    for number, row in enumerate(rows, start=2):
        sku, slot = row["sku"], row["slot"].upper()
        if not sku or not SLOT.fullmatch(slot):
            errors.append(f"row {number}: needs a SKU and a MAIN or PT01..PT09 slot (SWCH is never changed)")
            continue
        if (sku, slot) in seen:
            errors.append(f"row {number}: duplicate {sku} {slot}")
            continue
        seen.add((sku, slot))
        if not row["source_ref"]:
            errors.append(f"row {number}: source_ref is required (Drive file, Figma frame or chat attachment)")
            continue
        try:
            data, facts = png_bytes(Path(row["file"]).expanduser())
        except Refused as exc:
            errors.append(f"row {number}: {exc}")
            continue
        try:
            target = archive_target(root, data)
        except Refused as exc:
            errors.append(f"row {number}: {exc}")
            continue
        staged.append((row, slot, data, facts, target))
    if errors:
        raise Refused("; ".join(errors))
    entries = []
    for row, slot, data, facts, target in staged:
        archive(target, data)
        entries.append({"sku": row["sku"], "slot": slot, "source_ref": row["source_ref"],
                        "original_file": Path(row["file"]).name, **facts,
                        "png_sha256": sha256(data), "png_bytes": len(data), "archive_path": str(target)})
    receipt = {"schema_version": 1, "created_at": now(), "manifest": str(Path(args.manifest).resolve()),
               "wizards_ai_root": str(root), "entries": entries}
    write_json(Path(args.receipt), receipt)
    return {"status": "staged", "receipt": args.receipt, "entries": len(entries),
            "converted": sum(e["converted"] for e in entries)}


def publish(args, publish_fn=None) -> dict:
    receipt_path = Path(args.receipt)
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    root = wizards_root(args.wizards_ai or receipt.get("wizards_ai_root"))
    if publish_fn is None:
        sys.path.insert(0, str(root))
        from cloudinary_assets import publish as publish_fn
    images = []
    for entry in receipt["entries"]:
        path = Path(entry["archive_path"])
        if (path.parent != root / ARCHIVE or path.is_symlink() or not path.is_file()
                or sha256(path.read_bytes()) != entry["png_sha256"]):
            raise Refused(f"{path} is missing or changed since intake")
        if not entry.get("hosted"):
            try:
                result = publish_fn({"path": str(path), "sha256": entry["png_sha256"]})
            except Exception as exc:
                raise Refused(f"{entry['sku']} {entry['slot']}: hosting refused: {type(exc).__name__}: {exc}") from None
            if result.get("verified") is not True or not str(result.get("url", "")).startswith("https://"):
                raise Refused(f"{entry['sku']} {entry['slot']}: hosting did not return a verified HTTPS URL")
            entry["hosted"] = {"url": result["url"], "public_id": result.get("public_id"),
                               "existing": result.get("existing"), "verified_at": now()}
            write_json(receipt_path, receipt)
        images.append({"sku": entry["sku"], "slot": entry["slot"],
                       "artifact": {"path": str(path), "sha256": entry["png_sha256"]},
                       "url": entry["hosted"]["url"]})
    images_path = receipt_path.with_name(receipt_path.stem + "-images.json")
    write_json(images_path, images)
    return {"status": "hosted", "receipt": str(receipt_path), "images": str(images_path), "count": len(images)}


def amazon_image_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(str(url))
    return parsed.scheme == "https" and parsed.hostname == AMAZON_IMAGE_HOST and not parsed.username


class _AmazonOnlyRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not amazon_image_url(newurl):
            raise Refused(f"redirect to {newurl} leaves https://{AMAZON_IMAGE_HOST}")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_amazon_image(url: str) -> bytes:
    """Download one Amazon image: 30 s timeout, 30 MB cap, no redirect off the Amazon image host."""
    opener = urllib.request.build_opener(_AmazonOnlyRedirects)
    with opener.open(urllib.request.Request(url, headers={"User-Agent": "amazon-agent-image-compare"}),
                     timeout=FETCH_TIMEOUT) as response:
        if not amazon_image_url(response.geturl()):
            raise Refused(f"download ended at {response.geturl()}, not https://{AMAZON_IMAGE_HOST}")
        data = response.read(FETCH_MAX_BYTES + 1)
    if len(data) > FETCH_MAX_BYTES:
        raise Refused(f"{url}: larger than {FETCH_MAX_BYTES} bytes")
    return data


def _flat_image(data: bytes):
    """Open image bytes as RGB, with any transparency flattened onto white."""
    from PIL import Image

    with Image.open(io.BytesIO(data)) as im:
        im.seek(0)
        im.load()
        # An RGB or L PNG can carry a tRNS colour key, which Pillow reports only in im.info.
        if im.mode in {"RGBA", "LA", "PA"} or "transparency" in im.info:
            rgba = im.convert("RGBA")
            flat = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            flat.alpha_composite(rgba)
            return flat.convert("RGB")
        return im.convert("RGB")


def dhash(im) -> int:
    """256-bit difference hash: grayscale, 17x16 LANCZOS, left pixel brighter than right neighbour."""
    from PIL import Image

    small = im.convert("L").resize((17, 16), Image.LANCZOS)
    pixels = list(small.getdata())
    bits = 0
    for row in range(16):
        for col in range(16):
            left, right = pixels[row * 17 + col], pixels[row * 17 + col + 1]
            bits = (bits << 1) | (left > right)
    return bits


NEAR_WHITE = 245


def color_delta(a, b) -> float:
    """Mean absolute per-channel difference of 32x32 RGB thumbnails, 0-255, over the pixels where
    either image is not near-white, so a white background cannot dilute a colour difference."""
    from PIL import Image

    left = a.convert("RGB").resize((32, 32), Image.LANCZOS).tobytes()
    right = b.convert("RGB").resize((32, 32), Image.LANCZOS).tobytes()
    total = count = 0
    for i in range(0, len(left), 3):
        l, r = left[i:i + 3], right[i:i + 3]
        if min(l) >= NEAR_WHITE and min(r) >= NEAR_WHITE:
            continue
        total += sum(abs(x - y) for x, y in zip(l, r))
        count += 3
    return round(total / count, 3) if count else 0.0


def compare_images(amazon: bytes, png: bytes) -> dict:
    a, p = _flat_image(amazon), _flat_image(png)
    aspect_a, aspect_p = a.width / a.height, p.width / p.height
    return {"amazon_width": a.width, "amazon_height": a.height, "png_width": p.width, "png_height": p.height,
            "aspect_delta": round(abs(aspect_a - aspect_p) / aspect_p, 6),
            "dhash_distance": bin(dhash(a) ^ dhash(p)).count("1"), "color_delta": color_delta(a, p)}


def _within(facts: dict, max_aspect: float, max_dhash: int, max_color: float) -> bool:
    return (facts["aspect_delta"] <= max_aspect and facts["dhash_distance"] <= max_dhash
            and facts["color_delta"] <= max_color)


def _fetch_checked(fetch_fn, label: str, url: str) -> bytes:
    if not amazon_image_url(url):
        raise Refused(f"{label} {url!r} is not https://{AMAZON_IMAGE_HOST}")
    try:
        data = fetch_fn(url)
    except Refused as exc:
        raise Refused(f"{label}: {exc}") from None
    except Exception as exc:
        raise Refused(f"{label}: download failed: {type(exc).__name__}: {exc}") from None
    if len(data) > FETCH_MAX_BYTES:
        raise Refused(f"{label}: Amazon image is larger than {FETCH_MAX_BYTES} bytes")
    return data


def compare(args, fetch_fn=None) -> dict:
    fetch_fn = fetch_fn or fetch_amazon_image
    max_dhash = DEFAULT_MAX_DHASH if args.max_dhash is None else args.max_dhash
    max_aspect = DEFAULT_MAX_ASPECT_DELTA if args.max_aspect_delta is None else args.max_aspect_delta
    max_color = getattr(args, "max_color_delta", None)
    max_color = DEFAULT_MAX_COLOR_DELTA if max_color is None else max_color
    if max_dhash < 0 or max_aspect < 0 or max_color < 0:
        raise Refused("--max-dhash, --max-aspect-delta and --max-color-delta must not be negative")
    if (args.sku is None) != (args.slot is None):
        raise Refused("--sku and --slot go together")
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    root = wizards_root(getattr(args, "wizards_ai", None) or receipt.get("wizards_ai_root"))
    verify_path = Path(args.verify)
    verify = json.loads(verify_path.read_text(encoding="utf-8"))
    out_path = Path(args.out) if args.out else verify_path.with_name(verify_path.stem + "-pixels.json")
    if out_path.exists():
        raise Refused(f"{out_path} already exists; it is never overwritten")
    checks = verify.get("pixel_checks") if isinstance(verify, dict) else None
    if not isinstance(checks, list) or not checks:
        raise Refused(f"{verify_path} has no pixel_checks")
    if args.sku is not None:
        checks = [c for c in checks if c.get("sku") == args.sku and str(c.get("slot", "")).upper() == args.slot.upper()]
        if not checks:
            raise Refused(f"{args.sku} {args.slot.upper()}: no pixel check in {verify_path}")
    results = []
    for check in checks:
        sku, slot = check.get("sku"), str(check.get("slot", "")).upper()
        url, digest = str(check.get("amazon_url") or ""), check.get("image_sha256")
        before_url = check.get("before_url") or None
        entry = next((e for e in receipt.get("entries", []) if e.get("sku") == sku and e.get("slot") == slot
                      and e.get("png_sha256") == digest), None)
        if entry is None:
            raise Refused(f"{sku} {slot}: image_sha256 {digest} is not in the receipt for that slot")
        path = Path(entry["archive_path"])
        if (path.parent != root / ARCHIVE or path.is_symlink() or not path.is_file()
                or sha256(path.read_bytes()) != entry["png_sha256"]):
            raise Refused(f"{path} is missing or changed since intake")
        amazon = _fetch_checked(fetch_fn, f"{sku} {slot}: amazon_url", url)
        before = None if before_url is None else _fetch_checked(fetch_fn, f"{sku} {slot}: before_url", str(before_url))
        archived = path.read_bytes()
        try:
            facts = compare_images(amazon, archived)
            before_facts = None if before is None else compare_images(before, archived)
        except Exception as exc:
            raise Refused(f"{sku} {slot}: could not read the image: {type(exc).__name__}: {exc}") from None
        discriminating = before_facts is None or not _within(before_facts, max_aspect, max_dhash, max_color)
        match = _within(facts, max_aspect, max_dhash, max_color) and discriminating
        results.append({"sku": sku, "slot": slot, "amazon_url": url, "image_sha256": digest,
                        "before_url": before_url, "archive_path": str(path), **facts,
                        "before_dhash_distance": None if before_facts is None else before_facts["dhash_distance"],
                        "before_color_delta": None if before_facts is None else before_facts["color_delta"],
                        "discriminating": discriminating, "match": match})
    result = {"status": "compared" if all(r["match"] for r in results) else "mismatch",
              "thresholds": {"max_dhash": max_dhash, "max_aspect_delta": max_aspect, "max_color_delta": max_color},
              "verify_file": str(verify_path), "results": results}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "x", encoding="utf-8") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    one = sub.add_parser("intake")
    one.add_argument("--manifest", required=True)
    one.add_argument("--receipt", required=True)
    one.add_argument("--wizards-ai")
    two = sub.add_parser("publish")
    two.add_argument("--receipt", required=True)
    two.add_argument("--wizards-ai")
    three = sub.add_parser("compare")
    three.add_argument("--receipt", required=True)
    three.add_argument("--verify", required=True)
    three.add_argument("--sku")
    three.add_argument("--slot")
    three.add_argument("--max-dhash", type=int)
    three.add_argument("--max-aspect-delta", type=float)
    three.add_argument("--max-color-delta", type=float)
    three.add_argument("--out")
    three.add_argument("--wizards-ai")
    args = parser.parse_args(argv)
    try:
        if args.command == "compare":
            result = compare(args)
            print(json.dumps(result))
            return 0 if result["status"] == "compared" else 2
        result = intake(args) if args.command == "intake" else publish(args)
    except Refused as exc:
        print(json.dumps({"status": "blocked", "message": str(exc)}))
        return 2
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
