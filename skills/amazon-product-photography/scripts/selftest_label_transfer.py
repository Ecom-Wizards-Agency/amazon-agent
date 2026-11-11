#!/usr/bin/env python3
"""Synthetic tests for label_transfer.py. No client images.

Run: python3 -I -B skills/amazon-product-photography/scripts/selftest_label_transfer.py [--workdir DIR] [--keep]

Builds a patterned stand-in label, warps it into a scene with a known perspective and a
warm lighting gradient (the truth), garbles the scene label with noise, then runs
label_transfer.py and checks that the label comes back, that pixels outside the quad and
inside exclude rectangles are untouched, that the lighting gradient survives, that a
soften rectangle blurs only inside itself, that blurs do not darken the label edge, that
the ICC profile and EXIF survive, that thin or rotated quads and lossy output warn, and
that bad input (including 16-bit and rotated-EXIF scenes) exits 2. The geometry here
is computed independently of the tool. Needs numpy and Pillow in the running interpreter;
the tool is called with the same interpreter. Temp files go to the system temp folder or
to --workdir. Prints PASS or FAIL per case and exits 0 only when every case passes.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

try:
    import numpy as np
    from PIL import Image
except ImportError as exc:  # pragma: no cover - depends on the interpreter
    sys.stderr.write(f"selftest: needs numpy and Pillow ({exc}); use an interpreter that has both, "
                     "for example the repository .venv/bin/python3 -I -B\n")
    sys.exit(2)

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE / "label_transfer.py"

REF_SIZE = (600, 800)                     # w, h
REF_QUAD = np.array([[100, 100], [500, 100], [500, 700], [100, 700]], np.float64)
SCENE_SIZE = (900, 700)
SCENE_QUAD = np.array([[300, 120], [575, 165], [555, 575], [282, 605]], np.float64)
EXCLUDE = (260, 300, 360, 380)            # a "thumb" over the left edge of the label
SOFTEN = (330, 470, 520, 560)             # lower fine-print band


def q(quad):
    return ";".join(f"{x:g},{y:g}" for x, y in quad)


def make_reference(rng):
    w, h = REF_SIZE
    img = np.full((h, w, 3), 245, np.float32)
    x0, y0, x1, y1 = 100, 100, 500, 700
    lab = np.zeros((y1 - y0, x1 - x0, 3), np.float32)
    lab[:] = (70, 90, 150)
    yy, xx = np.mgrid[0:y1 - y0, 0:x1 - x0]
    # wordmark band of large blocks, a "product name" of mid blocks, fine print of small glyphs
    for i in range(8):
        bx = 30 + i * 44
        lab[40:110, bx:bx + 30] = (220, 190, 120) if i % 2 == 0 else (235, 225, 200)
    for i in range(16):
        bx = 30 + i * 22
        lab[150:180, bx:bx + 14] = (240, 240, 235)
    lab[220:400, 30:370] = (232, 224, 205)
    for r in range(8):
        for c in range(28):
            if rng.random() < 0.7:
                gx, gy = 40 + c * 11, 232 + r * 20
                lab[gy:gy + 10, gx:gx + 6] = (60, 55, 50)
    for r in range(4):
        for c in range(40):
            if rng.random() < 0.6:
                gx, gy = 30 + c * 8, 440 + r * 30
                lab[gy:gy + 12, gx:gx + 4] = (225, 225, 230)
    lab += ((xx // 50 + yy // 50) % 2)[..., None] * 8.0
    img[y0:y1, x0:x1] = lab
    return np.clip(img, 0, 255).astype(np.uint8)


def homography(src, dst):
    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.array(rows, np.float64))
    H = vt[-1].reshape(3, 3)
    return H / H[2, 2]


def inside_quad(quad, w, h, margin=0.0):
    """Pixel centres inside the convex quad, at least `margin` px from every edge."""
    X, Y = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    area = 0.5 * np.sum(quad[:, 0] * np.roll(quad[:, 1], -1) - np.roll(quad[:, 0], -1) * quad[:, 1])
    sign = 1.0 if area > 0 else -1.0
    ok = np.ones((h, w), bool)
    for i in range(4):
        (x0, y0), (x1, y1) = quad[i], quad[(i + 1) % 4]
        L = np.hypot(x1 - x0, y1 - y0)
        d = ((x1 - x0) * (Y - y0) - (y1 - y0) * (X - x0)) * sign / L
        ok &= d >= margin
    return ok


def outside_quad(quad, w, h, margin):
    return ~inside_quad(quad, w, h, -margin)


def warp_bilinear(ref, H_ref_to_scene, w, h):
    Hi = np.linalg.inv(H_ref_to_scene)
    X, Y = np.meshgrid(np.arange(w) + 0.5, np.arange(h) + 0.5)
    den = Hi[2, 0] * X + Hi[2, 1] * Y + Hi[2, 2]
    u = (Hi[0, 0] * X + Hi[0, 1] * Y + Hi[0, 2]) / den - 0.5
    v = (Hi[1, 0] * X + Hi[1, 1] * Y + Hi[1, 2]) / den - 0.5
    rh, rw = ref.shape[:2]
    u = np.clip(u, 0, rw - 1.001); v = np.clip(v, 0, rh - 1.001)
    x0 = np.floor(u).astype(int); y0 = np.floor(v).astype(int)
    fx = (u - x0)[..., None]; fy = (v - y0)[..., None]
    r = ref.astype(np.float32)
    return (r[y0, x0] * (1 - fx) * (1 - fy) + r[y0, x0 + 1] * fx * (1 - fy)
            + r[y0 + 1, x0] * (1 - fx) * fy + r[y0 + 1, x0 + 1] * fx * fy)


def lighting(w, h):
    X = (np.arange(w) + 0.5)[None, :] / w
    Y = (np.arange(h) + 0.5)[:, None] / h
    g = 0.55 + 0.7 * X + 0.1 * Y           # dark left, bright right, slight vertical falloff
    tint = np.array([1.0, 0.93, 0.82], np.float32)   # warm cast
    return g[..., None].astype(np.float32) * tint


def build_inputs(work, rng):
    ref = make_reference(rng)
    Image.fromarray(ref).save(work / "ref.png")
    w, h = SCENE_SIZE
    X, Y = np.meshgrid(np.arange(w), np.arange(h))
    bg = np.stack([150 + 40 * np.sin(X / 37.0), 140 + 30 * np.cos(Y / 23.0), 120 + 0 * X], -1)
    H = homography(REF_QUAD, SCENE_QUAD)
    warped = warp_bilinear(ref, H, w, h)
    lit = np.clip(warped * lighting(w, h), 0, 255)
    inside = inside_quad(SCENE_QUAD, w, h)
    truth = np.where(inside[..., None], lit, bg)
    truth = np.clip(np.rint(truth), 0, 255).astype(np.uint8)
    noise = rng.normal(0, 45, truth.shape)
    garbled = truth.astype(np.float32)
    garbled[inside] = garbled[inside] + noise[inside]
    garbled = np.clip(np.rint(garbled), 0, 255).astype(np.uint8)
    Image.fromarray(truth).save(work / "truth.png")
    Image.fromarray(garbled).save(work / "scene.png")
    return ref, truth, garbled, warped, inside


def run_tool(*args):
    cmd = [sys.executable, "-I", "-B", str(TOOL), *map(str, args)]
    p = subprocess.run(cmd, capture_output=True, text=True)
    summary = None
    if p.returncode == 0:
        try:
            summary = json.loads(p.stdout)
        except json.JSONDecodeError:
            summary = None
    return p.returncode, summary, p.stderr.strip()


def edge_band_cases(work, case):
    """White artwork, quad on its exact bounds, flat grey scene: every label pixel must
    come out at the scene grey, including the edge band, with and without blurs."""
    Image.fromarray(np.full((300, 200, 3), 255, np.uint8)).save(work / "white.png")
    Image.fromarray(np.full((500, 400, 3), 128, np.uint8)).save(work / "grey.png")
    rq = "0,0;200,0;200,300;0,300"
    sq_pts = np.array([[100, 100], [300, 110], [295, 410], [98, 400]], np.float64)
    band = inside_quad(sq_pts, 400, 500) & ~inside_quad(sq_pts, 400, 500, margin=10.0)
    runs = {"no blur": [], "--post-blur 3": ["--post-blur", "3"],
            "--soften r=3": ["--soften", "90,90,310,420", "--soften-radius", "3"]}
    for name, extra in runs.items():
        out = work / f"edge-{len(extra)}.png"
        rc, _, err = run_tool(work / "grey.png", work / "white.png", out,
                              "--ref-quad", rq, "--scene-quad", q(sq_pts), *extra)
        if rc != 0:
            case(f"edge band stays at the scene grey ({name})", False, f"exit {rc}: {err}")
            continue
        o = load(out)
        dev = float(np.abs(o[band] - 128.0).max())
        case(f"edge band stays at the scene grey ({name})", dev <= 2.0,
             f"max deviation {dev:.0f} in the 10 px edge band")


def load(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.float32)


def lum(a):
    return a @ np.array([0.299, 0.587, 0.114], np.float32)


def hf_energy(a, sel):
    L = lum(a)
    lap = np.abs(4 * L[1:-1, 1:-1] - L[:-2, 1:-1] - L[2:, 1:-1] - L[1:-1, :-2] - L[1:-1, 2:])
    return float(lap[sel[1:-1, 1:-1]].mean())


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--workdir", help="folder for temp files (default: a new system temp folder)")
    ap.add_argument("--keep", action="store_true", help="keep the temp files")
    a = ap.parse_args()
    if a.workdir:
        work = pathlib.Path(a.workdir).resolve()
        work.mkdir(parents=True, exist_ok=True)
        work = pathlib.Path(tempfile.mkdtemp(prefix="label-transfer-selftest-", dir=work))
    else:
        work = pathlib.Path(tempfile.mkdtemp(prefix="label-transfer-selftest-"))

    rng = np.random.default_rng(20261111)
    ref, truth, garbled, warped, inside = build_inputs(work, rng)
    w, h = SCENE_SIZE
    base = ["--ref-quad", q(REF_QUAD), "--scene-quad", q(SCENE_QUAD)]
    results = []

    def case(name, ok, detail=""):
        results.append(ok)
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  ({detail})" if detail else ""))

    # baseline run
    rc, s, err = run_tool(work / "scene.png", work / "ref.png", work / "out.png", *base,
                          "--preview", work / "preview.jpg")
    if rc != 0 or s is None:
        case("baseline run exits 0 with a JSON summary", False, f"exit {rc}: {err}")
        print(f"\n0/{len(results)} passed (baseline failed); files in {work}")
        return 1
    out = load(work / "out.png")
    T = truth.astype(np.float32); G = garbled.astype(np.float32)
    core = inside_quad(SCENE_QUAD, w, h, margin=6.0)

    # 1. transfer restores the label
    err_out = float(np.abs(out - T)[core].mean())
    err_garb = float(np.abs(G - T)[core].mean())
    case("transfer restores the label", err_out < 0.25 * err_garb and err_out < 10.0,
         f"mean abs error inside the quad {err_out:.2f} vs garbled {err_garb:.2f}")

    # 2. outside the quad is untouched
    far = outside_quad(SCENE_QUAD, w, h, margin=1.0)
    changed = int(np.any(out != G, axis=2)[far].sum())
    case("pixels outside the quad are unchanged", changed == 0, f"{changed} changed pixels outside")

    # 3. summary is honest
    sha_ok = s["output"]["sha256"] == hashlib.sha256((work / "out.png").read_bytes()).hexdigest()
    quad_area = int(inside.sum())
    area_ok = 0.9 * quad_area <= s["mask_area_px"] <= quad_area
    prev_ok = (work / "preview.jpg").is_file() and Image.open(work / "preview.jpg").format == "JPEG"
    case("JSON summary matches the output and preview exists",
         sha_ok and area_ok and prev_ok and s["scene"]["size"] == [w, h],
         f"sha256 {'ok' if sha_ok else 'mismatch'}, mask {s['mask_area_px']} of {quad_area} px, "
         f"preview {'ok' if prev_ok else 'missing'}")

    # 4. exclude rectangles stay scene pixels
    rc, s2, err = run_tool(work / "scene.png", work / "ref.png", work / "out-ex.png", *base,
                           "--exclude", ",".join(map(str, EXCLUDE)))
    if rc == 0:
        ox = load(work / "out-ex.png")
        x0, y0, x1, y1 = EXCLUDE
        same = bool(np.array_equal(ox[y0:y1, x0:x1], G[y0:y1, x0:x1]))
        far_from_ex = core.copy(); far_from_ex[y0 - 30:y1 + 30, x0 - 30:x1 + 30] = False
        still = float(np.abs(ox - T)[far_from_ex].mean())
        case("exclude rectangle stays scene pixels", same and still < 10.0,
             f"rectangle identical: {same}, error elsewhere {still:.2f}")
    else:
        case("exclude rectangle stays scene pixels", False, f"exit {rc}: {err}")

    # 5. lighting gradient survives
    unlit = warped
    band_w = 40
    cols = np.arange(w)[None, :].repeat(h, 0)
    left = core & (cols < SCENE_QUAD[:, 0].min() + 10 + band_w) & (cols >= SCENE_QUAD[:, 0].min() + 10)
    right = core & (cols > SCENE_QUAD[:, 0].max() - 10 - band_w) & (cols <= SCENE_QUAD[:, 0].max() - 10)

    def lr_ratio(img):
        return float(lum(img)[left].mean() / lum(img)[right].mean())

    r_truth, r_out, r_unlit = lr_ratio(T), lr_ratio(out), lr_ratio(unlit)
    tint_truth = float(T[core][:, 2].mean() / T[core][:, 0].mean())
    tint_out = float(out[core][:, 2].mean() / out[core][:, 0].mean())
    light_ok = (abs(r_out - r_truth) < 0.05 * r_truth and abs(r_unlit - r_truth) > 0.2 * r_truth
                and abs(tint_out - tint_truth) < 0.04)
    case("lighting gradient and warm cast survive", light_ok,
         f"left/right luminance {r_out:.3f} vs truth {r_truth:.3f} (unlit label {r_unlit:.3f}); "
         f"blue/red {tint_out:.3f} vs {tint_truth:.3f}")
    rc, _, err = run_tool(work / "scene.png", work / "ref.png", work / "out-nolight.png", *base,
                          "--light-strength", "0")
    if rc == 0:
        r0 = lr_ratio(load(work / "out-nolight.png"))
        case("--light-strength 0 keeps the reference lighting", abs(r0 - r_unlit) < 0.05 * r_unlit,
             f"left/right {r0:.3f} vs unlit {r_unlit:.3f}")
    else:
        case("--light-strength 0 keeps the reference lighting", False, f"exit {rc}: {err}")

    # 6. soften blurs only inside its rectangle
    rc, s3, err = run_tool(work / "scene.png", work / "ref.png", work / "out-soft.png", *base,
                           "--soften", ",".join(map(str, SOFTEN)), "--soften-radius", "2")
    if rc == 0:
        osf = load(work / "out-soft.png")
        x0, y0, x1, y1 = SOFTEN
        in_rect = np.zeros((h, w), bool); in_rect[y0:y1, x0:x1] = True
        diff = np.any(osf != out, axis=2)
        outside_changes = int((diff & ~in_rect).sum())
        sel = in_rect & core
        hf_base, hf_soft = hf_energy(out, sel), hf_energy(osf, sel)
        case("soften blurs only inside its rectangle",
             outside_changes == 0 and hf_soft < 0.6 * hf_base,
             f"{outside_changes} changes outside; edge energy inside {hf_soft:.1f} vs {hf_base:.1f}")
    else:
        case("soften blurs only inside its rectangle", False, f"exit {rc}: {err}")

    # 7. blurs do not darken the label edge
    edge_band_cases(work, case)

    # 8. ICC profile and EXIF survive
    icc = b"selftest-icc-profile-bytes-" + bytes(range(64))
    exif = Image.Exif(); exif[0x0131] = "label-transfer-selftest"
    Image.fromarray(garbled).save(work / "scene-icc.png", icc_profile=icc, exif=exif.tobytes())
    rc, _, err = run_tool(work / "scene-icc.png", work / "ref.png", work / "out-icc.png", *base)
    if rc == 0:
        oi = Image.open(work / "out-icc.png")
        icc_ok = oi.info.get("icc_profile") == icc
        exif_ok = oi.getexif().get(0x0131) == "label-transfer-selftest"
        case("ICC profile and EXIF survive", icc_ok and exif_ok,
             f"icc {'kept' if icc_ok else 'lost'}, exif {'kept' if exif_ok else 'lost'}")
    else:
        case("ICC profile and EXIF survive", False, f"exit {rc}: {err}")

    # 9. warnings: thin quad, rotated corner order, lossy output
    rc, s4, err = run_tool(work / "scene.png", work / "ref.png", work / "out-thin.png",
                           "--ref-quad", q(REF_QUAD), "--scene-quad", "300,300;600,300;600,302;300,302")
    thin_ok = (rc == 0 and s4 is not None and s4["mask_full_px"] == 0
               and any("full label" in x for x in s4["warnings"]) and "warning" in err)
    case("thin quad warns that nothing gets the full label", thin_ok,
         f"exit {rc}, mask_full_px {s4['mask_full_px'] if s4 else '?'}")
    rot_ref, rot_scene = np.roll(REF_QUAD, -1, axis=0), np.roll(SCENE_QUAD, -1, axis=0)
    rc, s5, err = run_tool(work / "scene.png", work / "ref.png", work / "out-rot.png",
                           "--ref-quad", q(rot_ref), "--scene-quad", q(rot_scene))
    rot_ok = rc == 0 and s5 is not None and sum("upper edge" in x for x in s5["warnings"]) == 2
    rc0, s0, _ = run_tool(work / "scene.png", work / "ref.png", work / "out-plain.png", *base)
    quiet = rc0 == 0 and s0 is not None and s0["warnings"] == []
    case("rotated corner order warns, normal order is quiet", rot_ok and quiet,
         f"rotated warnings {len(s5['warnings']) if s5 else '?'}, normal {s0['warnings'] if s0 else '?'}")
    rc, s6, err = run_tool(work / "scene.png", work / "ref.png", work / "out.jpg", *base)
    case("JPEG output warns about re-encoding",
         rc == 0 and s6 is not None and any("re-encodes" in x for x in s6["warnings"]),
         f"exit {rc}")

    # 10. usage and input errors exit 2
    Image.fromarray(np.full((h, w), 30000, np.uint16)).save(work / "scene16.png")
    ex = Image.Exif(); ex[0x0112] = 6
    Image.fromarray(garbled).save(work / "scene-rot.jpg", exif=ex.tobytes(), quality=95)
    Image.fromarray(np.zeros((h // 2, w // 2, 3), np.uint8)).save(work / "small.png")
    (work / "not-an-image.png").write_text("plain text, not a picture\n")
    bad = {
        "quad with 3 points": [work / "scene.png", work / "ref.png", work / "e1.png",
                               "--ref-quad", "100,100;500,100;500,700", "--scene-quad", q(SCENE_QUAD)],
        "scene quad outside the image": [work / "scene.png", work / "ref.png", work / "e2.png",
                                         "--ref-quad", q(REF_QUAD),
                                         "--scene-quad", "300,120;575,165;555,575;282,905"],
        "missing scene file": [work / "nope.png", work / "ref.png", work / "e3.png", *base],
        "unreadable reference file": [work / "scene.png", work / "not-an-image.png",
                                      work / "e4.png", *base],
        "crossed (bowtie) quad": [work / "scene.png", work / "ref.png", work / "e5.png",
                                  "--ref-quad", q(REF_QUAD),
                                  "--scene-quad", "300,120;555,575;575,165;282,605"],
        "preview-before size mismatch": [work / "scene.png", work / "ref.png", work / "e6.png",
                                         *base, "--preview", work / "e6.jpg",
                                         "--preview-before", work / "small.png"],
        "exclude rectangle outside the scene": [work / "scene.png", work / "ref.png",
                                                work / "e7.png", *base, "--exclude", "850,10,950,60"],
        "missing --scene-quad": [work / "scene.png", work / "ref.png", work / "e8.png",
                                 "--ref-quad", q(REF_QUAD)],
        "16-bit scene": [work / "scene16.png", work / "ref.png", work / "e9.png", *base],
        "scene with EXIF orientation 6": [work / "scene-rot.jpg", work / "ref.png",
                                          work / "e10.png", *base],
    }
    for name, args in bad.items():
        rc, _, err = run_tool(*args)
        wrote = any((work / f"e{i}.png").exists() for i in range(1, 11))
        case(f"exit 2: {name}", rc == 2 and not wrote, f"exit {rc}: {err.splitlines()[-1] if err else ''}")

    passed = sum(results)
    print(f"\n{passed}/{len(results)} passed")
    if a.keep or passed != len(results):
        print(f"files kept in {work}")
    else:
        shutil.rmtree(work, ignore_errors=True)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
