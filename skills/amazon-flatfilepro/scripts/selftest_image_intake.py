#!/usr/bin/env python3
"""Synthetic, client-neutral tests for image_intake.py. No network, no broker.

Run: ~/os/wizards-ai/venv/bin/python skills/amazon-flatfilepro/scripts/selftest_image_intake.py
(Pillow is required). Prints a PASS/FAIL summary and exits non-zero on failure.
"""
from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import image_intake as intake_mod  # noqa: E402

TMP = Path(tempfile.mkdtemp(prefix="ffp-image-intake-selftest-"))
FAILURES: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    print(f"  [{'ok' if condition else 'FAIL'}] {label}" + (f": {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(f"{label}: {detail}")


def fake_wizards(name: str) -> Path:
    root = TMP / name
    (root / intake_mod.ARCHIVE).mkdir(parents=True)
    (root / "cloudinary_assets.py").write_text("# stub\n")
    return root


def image(path: Path, fmt: str, size=(800, 800), color=(255, 255, 255)) -> Path:
    Image.new("RGB", size, color).save(path, format=fmt)
    return path


def manifest(path: Path, rows: list[list[str]]) -> Path:
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerows([["sku", "slot", "file", "source_ref"], *rows])
    return path


def picture(size=(1000, 1000), flip=False, mode="RGB", background=(255, 255, 255)) -> Image.Image:
    """A structured test picture (shapes on a background) so dHash has edges to see."""
    w, h = size
    im = Image.new(mode, size, background if mode == "RGB" else (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    for i in range(6):
        x0 = int(w * (0.05 + 0.15 * i))
        y0 = int(h * (0.1 + (0.12 * i if not flip else 0.6 - 0.1 * i)))
        draw.rectangle([x0, y0, x0 + int(w * 0.1), y0 + int(h * 0.25)], fill=(20 + 35 * i, 40, 200 - 30 * i, 255)[: len(mode)])
    draw.ellipse([int(w * 0.55), int(h * 0.55), int(w * 0.9), int(h * 0.9)], fill=(10, 120, 60, 255)[: len(mode)])
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


def silhouette(fill, size=(1000, 1000)) -> Image.Image:
    """One product shape in a single colour on white, like a colour variant of the same item."""
    w, h = size
    im = Image.new("RGB", size, (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.polygon([(w * 0.35, h * 0.1), (w * 0.65, h * 0.1), (w * 0.8, h * 0.9), (w * 0.2, h * 0.9)], fill=fill)
    draw.rectangle([w * 0.1, h * 0.15, w * 0.35, h * 0.3], fill=fill)
    draw.rectangle([w * 0.65, h * 0.15, w * 0.9, h * 0.3], fill=fill)
    return im


def encode(im: Image.Image, fmt: str, **kwargs) -> bytes:
    out = io.BytesIO()
    im.save(out, format=fmt, **kwargs)
    return out.getvalue()


def run(*argv: str) -> tuple[int, dict]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = intake_mod.main(list(argv))
    return code, json.loads(out.getvalue())


def main() -> int:
    root = fake_wizards("wizards")
    png = image(TMP / "pt01.png", "PNG", color=(10, 20, 30))
    jpg = image(TMP / "main.jpg", "JPEG")
    small = image(TMP / "small.png", "PNG", size=(400, 900))
    gif = image(TMP / "x.gif", "GIF")

    print("intake")
    good = manifest(TMP / "good.csv", [["SKU-A", "PT01", str(png), "chat attachment 1"],
                                       ["SKU-A", "main", str(jpg), "Drive file 2"]])
    receipt = TMP / "run" / "intake-receipt.json"
    code, out = run("intake", "--manifest", str(good), "--receipt", str(receipt), "--wizards-ai", str(root))
    check("valid manifest stages", code == 0 and out["entries"] == 2 and out["converted"] == 1, str(out))
    data = json.loads(receipt.read_text())
    entries = {e["slot"]: e for e in data["entries"]}
    check("slot is upper-cased", set(entries) == {"PT01", "MAIN"}, str(entries.keys()))
    pt = entries["PT01"]
    check("PNG archived byte for byte", pt["png_sha256"] == hashlib.sha256(png.read_bytes()).hexdigest()
          and Path(pt["archive_path"]).name == pt["png_sha256"] + ".png" and not pt["converted"])
    main = entries["MAIN"]
    archived = Path(main["archive_path"]).read_bytes()
    check("JPEG converted to PNG with both hashes", main["converted"] and main["original_format"] == "JPEG"
          and main["original_sha256"] == hashlib.sha256(jpg.read_bytes()).hexdigest()
          and hashlib.sha256(archived).hexdigest() == main["png_sha256"] and archived[:8] == b"\x89PNG\r\n\x1a\n")
    check("archive files sit in the broker root", all(Path(e["archive_path"]).parent == root / intake_mod.ARCHIVE
                                                      for e in data["entries"]))

    code, out = run("intake", "--manifest", str(good), "--receipt", str(receipt), "--wizards-ai", str(root))
    check("existing receipt is never overwritten", code == 2 and "already exists" in out["message"], str(out))

    again = TMP / "run" / "again.json"
    code, out = run("intake", "--manifest", str(good), "--receipt", str(again), "--wizards-ai", str(root))
    check("same bytes reuse the archived file", code == 0, str(out))

    clash_root = fake_wizards("clash")
    digest = hashlib.sha256(png.read_bytes()).hexdigest()
    (clash_root / intake_mod.ARCHIVE / f"{digest}.png").write_bytes(b"other bytes")
    code, out = run("intake", "--manifest", str(manifest(TMP / "one.csv", [["SKU-A", "PT01", str(png), "x"]])),
                    "--receipt", str(TMP / "clash.json"), "--wizards-ai", str(clash_root))
    check("different bytes under the same name are refused", code == 2 and "different content" in out["message"], str(out))

    bad = manifest(TMP / "bad.csv", [["SKU-B", "SWCH", str(png), "x"], ["SKU-B", "PT02", str(small), "x"],
                                     ["SKU-B", "PT03", str(gif), "x"], ["SKU-B", "PT04", str(png), ""],
                                     ["SKU-C", "PT01", str(png), "x"], ["SKU-C", "PT01", str(png), "x"]])
    bad_root = fake_wizards("bad")
    code, out = run("intake", "--manifest", str(bad), "--receipt", str(TMP / "bad.json"), "--wizards-ai", str(bad_root))
    message = out.get("message", "")
    check("refusals are all listed", code == 2 and all(s in message for s in
          ["row 2:", "row 3:", "row 4:", "row 5:", "row 7: duplicate"]), message)
    check("a refused manifest archives nothing", not any((bad_root / intake_mod.ARCHIVE).iterdir()))

    big_root = fake_wizards("big")
    original = intake_mod.MAX_BYTES
    intake_mod.MAX_BYTES = 100
    try:
        code, out = run("intake", "--manifest", str(manifest(TMP / "big.csv", [["SKU-D", "PT01", str(png), "x"]])),
                        "--receipt", str(TMP / "big.json"), "--wizards-ai", str(big_root))
    finally:
        intake_mod.MAX_BYTES = original
    check("files over the hosting limit are refused", code == 2 and "hosting limit" in out["message"], str(out))

    print("orientation, MPO and malformed rows")
    rotated = TMP / "rotated.jpg"
    exif = Image.Exif()
    exif[intake_mod.ORIENTATION] = 6
    Image.new("RGB", (1000, 600), (200, 200, 200)).save(rotated, format="JPEG", exif=exif)
    turn_root = fake_wizards("turn")
    code, out = run("intake", "--manifest", str(manifest(TMP / "turn.csv", [["SKU-F", "PT01", str(rotated), "x"]])),
                    "--receipt", str(TMP / "turn.json"), "--wizards-ai", str(turn_root))
    entry = json.loads((TMP / "turn.json").read_text())["entries"][0] if code == 0 else {}
    with Image.open(entry.get("archive_path", rotated)) as im:
        upright = im.size
    check("a rotated JPEG is archived upright", code == 0 and upright == (600, 1000)
          and (entry["width"], entry["height"]) == (600, 1000), f"{code} {upright} {out}")

    tagged = TMP / "tagged.png"
    Image.new("RGB", (800, 800)).save(tagged, format="PNG", exif=exif)
    code, out = run("intake", "--manifest", str(manifest(TMP / "tagged.csv", [["SKU-F", "PT02", str(tagged), "x"]])),
                    "--receipt", str(TMP / "tagged.json"), "--wizards-ai", str(fake_wizards("tagged")))
    check("a PNG with a rotation tag is refused", code == 2 and "rotation" in out["message"], str(out))

    mpo = TMP / "phone.jpg"
    Image.new("RGB", (900, 700), (1, 2, 3)).save(mpo, format="MPO", save_all=True,
                                                 append_images=[Image.new("RGB", (900, 700), (9, 9, 9))])
    with Image.open(mpo) as im:
        is_mpo = im.format == "MPO"
    code, out = run("intake", "--manifest", str(manifest(TMP / "mpo.csv", [["SKU-F", "PT03", str(mpo), "x"]])),
                    "--receipt", str(TMP / "mpo.json"), "--wizards-ai", str(fake_wizards("mpo")))
    check("a multi-picture phone JPEG is converted from its first frame", is_mpo and code == 0 and out["converted"] == 1,
          f"{is_mpo} {out}")

    extra = TMP / "extra.csv"
    extra.write_text(f"sku,slot,file,source_ref\nSKU-F,PT04,{png},x,surplus\n", encoding="utf-8")
    code, out = run("intake", "--manifest", str(extra), "--receipt", str(TMP / "extra.json"), "--wizards-ai", str(root))
    check("a row with extra cells is refused by number", code == 2 and "more cells than the header: 2" in out["message"], str(out))

    partial_root = fake_wizards("partial")
    other = image(TMP / "other.png", "PNG", color=(90, 90, 90))
    (partial_root / intake_mod.ARCHIVE / f"{hashlib.sha256(other.read_bytes()).hexdigest()}.png").write_bytes(b"junk")
    code, out = run("intake", "--manifest", str(manifest(TMP / "partial.csv", [["SKU-G", "PT01", str(png), "x"],
                                                                                 ["SKU-G", "PT02", str(other), "x"]])),
                    "--receipt", str(TMP / "partial.json"), "--wizards-ai", str(partial_root))
    left = sorted(p.name for p in (partial_root / intake_mod.ARCHIVE).iterdir())
    check("a clash on a later row archives nothing new", code == 2 and len(left) == 1 and "row 3" in out["message"],
          f"{code} {left} {out}")

    print("publish")
    calls = []

    def fake_publish(asset):
        calls.append(asset)
        return {"url": f"https://res.cloudinary.com/test/image/upload/v1/amazon-agent/{asset['sha256']}.png",
                "public_id": f"amazon-agent/{asset['sha256']}", "verified": True, "existing": False}

    args = type("A", (), {"receipt": str(receipt), "wizards_ai": str(root)})
    result = intake_mod.publish(args, publish_fn=fake_publish)
    images = json.loads(Path(result["images"]).read_text())
    check("every entry hosted once", len(calls) == 2 and result["count"] == 2, str(result))
    check("images list matches operations input shape", all(set(i) == {"sku", "slot", "artifact", "url"}
          and set(i["artifact"]) == {"path", "sha256"} for i in images), str(images))
    intake_mod.publish(args, publish_fn=fake_publish)
    check("re-running publish does not re-host", len(calls) == 2, str(len(calls)))

    Path(entries["PT01"]["archive_path"]).write_bytes(b"tampered")
    try:
        intake_mod.publish(args, publish_fn=fake_publish)
        check("changed archive file is refused", False, "no refusal")
    except intake_mod.Refused as exc:
        check("changed archive file is refused", "changed" in str(exc), str(exc))

    def unverified(asset):
        return {"url": "https://res.cloudinary.com/x.png", "verified": False}

    fresh = TMP / "run" / "fresh.json"
    code, _ = run("intake", "--manifest", str(manifest(TMP / "fresh.csv", [["SKU-E", "PT05", str(jpg), "x"]])),
                  "--receipt", str(fresh), "--wizards-ai", str(fake_wizards("fresh")))
    try:
        intake_mod.publish(type("A", (), {"receipt": str(fresh), "wizards_ai": None}), publish_fn=unverified)
        check("unverified hosting is refused", False, "no refusal")
    except intake_mod.Refused as exc:
        check("unverified hosting is refused", "verified" in str(exc), str(exc))

    def broken(asset):
        raise RuntimeError("broker unavailable")

    errored = TMP / "run" / "errored.json"
    code, _ = run("intake", "--manifest", str(manifest(TMP / "errored.csv", [["SKU-H", "PT06", str(png), "x"]])),
                  "--receipt", str(errored), "--wizards-ai", str(fake_wizards("errored")))
    try:
        intake_mod.publish(type("A", (), {"receipt": str(errored), "wizards_ai": None}), publish_fn=broken)
        check("a broker error becomes a refusal", False, "no refusal")
    except intake_mod.Refused as exc:
        check("a broker error becomes a refusal", "hosting refused: RuntimeError" in str(exc), str(exc))
    Path(json.loads(errored.read_text())["entries"][0]["archive_path"]).unlink()
    try:
        intake_mod.publish(type("A", (), {"receipt": str(errored), "wizards_ai": None}), publish_fn=broken)
        check("a missing archive file becomes a refusal", False, "no refusal")
    except intake_mod.Refused as exc:
        check("a missing archive file becomes a refusal", "missing or changed" in str(exc), str(exc))

    print("compare")
    cmp_root = fake_wizards("compare")
    art = TMP / "art.png"
    picture().save(art, format="PNG")
    clear = TMP / "clear.png"
    picture(mode="RGBA").save(clear, format="PNG")
    cmp_receipt = TMP / "cmp" / "intake-receipt.json"
    code, out = run("intake", "--manifest", str(manifest(TMP / "cmp.csv", [["SKU-P", "MAIN", str(art), "x"],
                                                                           ["SKU-P", "PT01", str(clear), "x"]])),
                    "--receipt", str(cmp_receipt), "--wizards-ai", str(cmp_root))
    cmp_entries = {e["slot"]: e for e in json.loads(cmp_receipt.read_text())["entries"]}
    check("compare fixtures staged", code == 0 and set(cmp_entries) == {"MAIN", "PT01"}, str(out))
    served: dict[str, bytes] = {}
    fetched: list[str] = []

    def fake_fetch(url):
        fetched.append(url)
        return served[url]

    intake_mod.fetch_amazon_image = fake_fetch
    counter = iter(range(1, 1000))

    def verify_file(checks: list[dict]) -> Path:
        path = TMP / "cmp" / "verify" / f"{next(counter):03d}-1.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"pixel_checks": checks}))
        return path

    def pixel(slot: str, url: str, digest: str | None = None, sku: str = "SKU-P", **before) -> dict:
        return {"sku": sku, "slot": slot, "attribute": "main_product_image_locator" if slot == "MAIN"
                else "other_product_image_locator_1", "amazon_url": url,
                "image_sha256": digest or cmp_entries[slot]["png_sha256"], **before}

    def compare(verify: Path, *extra: str, receipt_path: Path = cmp_receipt) -> tuple[int, dict]:
        return run("compare", "--receipt", str(receipt_path), "--verify", str(verify), *extra)

    url_main = "https://m.media-amazon.com/images/I/main1.jpg"
    served[url_main] = encode(picture().resize((640, 640)), "JPEG", quality=80)
    v = verify_file([pixel("MAIN", url_main)])
    code, out = compare(v)
    written = v.with_name(v.stem + "-pixels.json")
    check("the same picture re-encoded as a smaller JPEG matches",
          code == 0 and out["status"] == "compared" and out["results"][0]["match"]
          and out["results"][0]["amazon_width"] == 640 and out["results"][0]["png_width"] == 1000, str(out))
    check("the result is written next to the verify file", written.is_file()
          and json.loads(written.read_text()) == out and out["verify_file"] == str(v)
          and out["thresholds"] == {"max_dhash": intake_mod.DEFAULT_MAX_DHASH,
                                    "max_aspect_delta": intake_mod.DEFAULT_MAX_ASPECT_DELTA,
                                    "max_color_delta": intake_mod.DEFAULT_MAX_COLOR_DELTA}
          and (intake_mod.DEFAULT_MAX_DHASH, intake_mod.DEFAULT_MAX_ASPECT_DELTA,
               intake_mod.DEFAULT_MAX_COLOR_DELTA) == (24, 0.02, 12), str(written))
    first = out["results"][0]
    check("a re-encoded JPEG keeps a small, non-zero color_delta",
          0 < first["color_delta"] <= intake_mod.DEFAULT_MAX_COLOR_DELTA, str(first))
    check("a check without before_url is discriminating with null before fields",
          first["before_url"] is None and first["before_dhash_distance"] is None
          and first["before_color_delta"] is None and first["discriminating"] is True, str(first))
    before = written.read_bytes()
    code, out = compare(v)
    check("an existing result file is never overwritten", code == 2 and out["status"] == "blocked"
          and "already exists" in out["message"] and written.read_bytes() == before, str(out))

    url_other = "https://m.media-amazon.com/images/I/other.jpg"
    served[url_other] = encode(picture(flip=True), "JPEG", quality=90)
    code, out = compare(verify_file([pixel("MAIN", url_other)]))
    check("a different picture mismatches", code == 2 and out["status"] == "mismatch"
          and not out["results"][0]["match"] and out["results"][0]["dhash_distance"] > intake_mod.DEFAULT_MAX_DHASH,
          str(out))

    url_wide = "https://m.media-amazon.com/images/I/wide.jpg"
    served[url_wide] = encode(picture().resize((1000, 800)), "JPEG", quality=90)
    code, out = compare(verify_file([pixel("MAIN", url_wide)]))
    check("an aspect change mismatches", code == 2 and out["status"] == "mismatch"
          and out["results"][0]["aspect_delta"] > intake_mod.DEFAULT_MAX_ASPECT_DELTA, str(out))

    url_flat = "https://m.media-amazon.com/images/I/flat.jpg"
    served[url_flat] = encode(picture(), "JPEG", quality=85)
    code, out = compare(verify_file([pixel("PT01", url_flat)]))
    check("a transparent PNG matches the same content on white", code == 0 and out["results"][0]["match"], str(out))

    code, out = compare(verify_file([pixel("MAIN", url_main, before_url=url_main)]))
    r = out["results"][0] if out.get("results") else {}
    check("a before image equal to the new image is non-discriminating and does not match",
          code == 2 and out["status"] == "mismatch" and r["discriminating"] is False and r["match"] is False
          and r["dhash_distance"] <= intake_mod.DEFAULT_MAX_DHASH and r["before_dhash_distance"] == r["dhash_distance"]
          and fetched[-2:] == [url_main, url_main], str(out))
    code, out = compare(verify_file([pixel("MAIN", url_main, before_url=url_other)]))
    r = out["results"][0] if out.get("results") else {}
    check("a different before image passes discrimination", code == 0 and r["discriminating"] is True
          and r["match"] is True and r["before_url"] == url_other
          and r["before_dhash_distance"] > intake_mod.DEFAULT_MAX_DHASH, str(out))
    before = len(fetched)
    code, out = compare(verify_file([pixel("MAIN", url_main, before_url="https://example.com/old.jpg")]))
    check("a before_url off the Amazon image host is refused", code == 2 and out["status"] == "blocked"
          and "before_url" in out["message"] and len(fetched) == before + 1, str(out))

    before = len(fetched)
    code, out = compare(verify_file([pixel("MAIN", "https://images-na.ssl-images-amazon.com/images/I/main1.jpg")]))
    check("a non-Amazon image host is refused", code == 2 and out["status"] == "blocked"
          and "m.media-amazon.com" in out["message"] and len(fetched) == before, str(out))
    code, out = compare(verify_file([pixel("MAIN", "http://m.media-amazon.com/images/I/main1.jpg")]))
    check("plain http is refused", code == 2 and out["status"] == "blocked" and len(fetched) == before, str(out))
    code, out = compare(verify_file([pixel("MAIN", url_main, digest="0" * 64)]))
    check("an image_sha256 outside the receipt is refused", code == 2 and "SKU-P MAIN" in out.get("message", "")
          and "not in the receipt" in out["message"], str(out))

    url_pt = "https://m.media-amazon.com/images/I/pt.jpg"
    served[url_pt] = served[url_flat]
    both = verify_file([pixel("MAIN", url_other), pixel("PT01", url_pt)])
    code, out = compare(both, "--sku", "SKU-P", "--slot", "pt01")
    check("--sku/--slot checks only that entry", code == 0 and [r["slot"] for r in out["results"]] == ["PT01"]
          and fetched[-1] == url_pt, str(out))
    code, out = compare(both, "--sku", "SKU-P", "--slot", "PT02", "--out", str(TMP / "cmp" / "none.json"))
    check("--sku/--slot without a pixel check is refused", code == 2 and out["status"] == "blocked"
          and "no pixel check" in out["message"], str(out))

    print("compare: colour and colour keys")
    keyed = TMP / "keyed.png"
    ground = Image.new("RGB", (1000, 1000), (0, 0, 0))
    ImageDraw.Draw(ground).ellipse([200, 200, 800, 800], fill=(128, 128, 128))
    ground.save(keyed, format="PNG", transparency=(0, 0, 0))
    grey = TMP / "grey.png"
    silhouette((120, 120, 120)).save(grey, format="PNG")
    red = TMP / "red.png"
    silhouette((200, 30, 30)).save(red, format="PNG")
    col_receipt = TMP / "col" / "intake-receipt.json"
    code, out = run("intake", "--manifest", str(manifest(TMP / "col.csv", [["SKU-Q", "MAIN", str(red), "x"],
                                                                           ["SKU-Q", "PT01", str(keyed), "x"],
                                                                           ["SKU-Q", "PT02", str(grey), "x"]])),
                    "--receipt", str(col_receipt), "--wizards-ai", str(fake_wizards("colour")))
    col = {e["slot"]: e["png_sha256"] for e in json.loads(col_receipt.read_text())["entries"]} if code == 0 else {}
    with Image.open(keyed) as im:
        keyed_info = (im.mode, im.info.get("transparency"))
    check("colour fixtures staged", code == 0 and len(col) == 3 and keyed_info == ("RGB", (0, 0, 0)),
          f"{out} {keyed_info}")

    url_blue = "https://m.media-amazon.com/images/I/blue.jpg"
    served[url_blue] = encode(silhouette((30, 30, 200)), "JPEG", quality=85)
    code, out = compare(verify_file([pixel("MAIN", url_blue, digest=col["MAIN"], sku="SKU-Q")]), receipt_path=col_receipt)
    r = out["results"][0] if out.get("results") else {}
    check("the same shape in another colour mismatches on color_delta", code == 2 and r["match"] is False
          and r["dhash_distance"] <= intake_mod.DEFAULT_MAX_DHASH and r["aspect_delta"] == 0
          and r["color_delta"] > intake_mod.DEFAULT_MAX_COLOR_DELTA, str(out))

    url_navy = "https://m.media-amazon.com/images/I/navy.jpg"
    served[url_navy] = encode(silhouette((20, 30, 70)), "JPEG", quality=85)
    near_black = TMP / "near-black.png"
    silhouette((15, 15, 15)).save(near_black, format="PNG")
    facts = intake_mod.compare_images(served[url_navy], near_black.read_bytes())
    check("a near-shade sibling (navy vs black) on white mismatches on color_delta",
          facts["color_delta"] > intake_mod.DEFAULT_MAX_COLOR_DELTA, str(facts))

    url_red = "https://m.media-amazon.com/images/I/red.jpg"
    served[url_red] = encode(silhouette((200, 30, 30)).resize((800, 800)), "JPEG", quality=80)
    code, out = compare(verify_file([pixel("MAIN", url_red, digest=col["MAIN"], sku="SKU-Q", before_url=url_blue)]),
                        receipt_path=col_receipt)
    r = out["results"][0] if out.get("results") else {}
    check("the right colour matches and the other colour as before image discriminates", code == 0 and r["match"]
          and r["discriminating"] and r["before_color_delta"] > intake_mod.DEFAULT_MAX_COLOR_DELTA, str(out))

    url_keyed = "https://m.media-amazon.com/images/I/keyed.jpg"
    on_white = Image.new("RGB", (1000, 1000), (255, 255, 255))
    ImageDraw.Draw(on_white).ellipse([200, 200, 800, 800], fill=(128, 128, 128))
    served[url_keyed] = encode(on_white, "JPEG", quality=85)
    code, out = compare(verify_file([pixel("PT01", url_keyed, digest=col["PT01"], sku="SKU-Q")]), receipt_path=col_receipt)
    check("an RGB PNG with a tRNS colour key matches its white-background JPEG", code == 0 and out["results"][0]["match"],
          str(out))

    keyed_l = TMP / "keyed-l.png"
    ground.convert("L").save(keyed_l, format="PNG", transparency=0)
    l_bytes = keyed_l.read_bytes()
    facts = intake_mod.compare_images(served[url_keyed], l_bytes)
    check("an L PNG with a tRNS colour key is flattened onto white too",
          facts["dhash_distance"] <= intake_mod.DEFAULT_MAX_DHASH
          and facts["color_delta"] <= intake_mod.DEFAULT_MAX_COLOR_DELTA, str(facts))

    code, out = compare(verify_file([pixel("PT02", url_red, digest=col["PT02"], sku="SKU-Q")]), "--max-color-delta", "200",
                        receipt_path=col_receipt)
    check("--max-color-delta is honoured and reported", code == 0 and out["thresholds"]["max_color_delta"] == 200
          and out["results"][0]["match"], str(out))

    Path(cmp_entries["MAIN"]["archive_path"]).write_bytes(b"tampered")
    code, out = compare(verify_file([pixel("MAIN", url_main)]))
    check("an archive changed since intake is refused", code == 2 and "changed since intake" in out.get("message", ""),
          str(out))

    shutil.rmtree(TMP, ignore_errors=True)
    print(f"{'PASS' if not FAILURES else 'FAIL'}: {len(FAILURES)} failure(s)")
    for failure in FAILURES:
        print("  - " + failure)
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
