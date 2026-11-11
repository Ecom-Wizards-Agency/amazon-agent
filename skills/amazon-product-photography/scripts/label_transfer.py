#!/usr/bin/env python3
"""Paste a crisp reference label onto a rendered product so its printed text reads correctly.

Why: image models garble the printed label when the product is small in a scene. Words
turn into lookalike glyphs and numbers change. Re-prompting rarely fixes it. What works is
to take the label from a clean packshot or from the label artwork, warp it into place on
the render, carry the scene's lighting onto it and replace only the label interior. Bottle
edges, rim highlights, the cap and anything outside the label stay scene pixels.

When to use it: the render is otherwise accepted (pose, light, hands, background) and only
the label text is wrong. The product face must be close to flat or seen nearly front-on,
because the fit is one perspective transform (a homography) from four corner points. A
strongly curved face seen at an angle needs a smaller quad on the flattest part of the face.

How it works:
  1. Fit a homography from the four reference corners to the four scene corners.
  2. Warp the reference into the scene. A small product is warped at several times its
     size and box-averaged back down, so fine type is area-sampled instead of aliased.
  3. Lighting transfer: measure the low-frequency colour of the scene label and of the
     warped reference inside the quad, and multiply the reference by their ratio. Warm
     side light, falloff and colour cast survive; the garbled glyphs do not.
  4. Composite through a mask that is feathered inward from the quad edge, so pixels
     outside the quad keep their scene values. Exclude rectangles (a thumb, a cap edge
     or a reflection crossing the label) stay scene pixels. --post-blur and --soften
     blur only label pixels inside the quad, so the label edge does not darken.
  5. Optional soften rectangles blur the transferred label inside them, like depth of
     field. Use this on a very small product, where crisp fine print still reads as wrong
     numbers: soften the lower fine print and keep the brand and product name crisp.

Coordinates are image pixels with (0, 0) at the top-left corner of the top-left pixel; a
pixel's centre sits at (x + 0.5, y + 0.5). A quad is four points in the order top-left,
top-right, bottom-right, bottom-left as the label reads, written "x,y;x,y;x,y;x,y". Give
the corners of the same label area in both images and in the same order. A rectangle is
"x0,y0,x1,y1" with x1 and y1 exclusive. The tool warns (stderr and the JSON "warnings")
when a quad's first edge is not its upper edge, which usually means the corners start at
the wrong point, and when the quad is too thin for any pixel to get the full label.

Image formats: scene and reference must be 8-bit (RGB, RGBA, L, LA or P); a 16-bit,
float or CMYK file exits 2, so convert it first. Coordinates are in the displayed
orientation. A reference with an EXIF orientation tag is turned upright before use; a
scene with a non-default EXIF orientation exits 2 (save it upright first), because its
untouched pixels must stay as stored. The output keeps the scene's ICC profile and EXIF.
The output is RGB, or RGBA when the scene has alpha and the format allows it.

The untouched-pixel guarantee holds for PNG or TIFF output only. JPEG and WebP output
re-encode the whole frame, so every pixel can shift slightly; the tool warns when you ask
for them. Deliver from a PNG master.

Usage:
  label_transfer.py SCENE REFERENCE OUTPUT --ref-quad Q --scene-quad Q
      [--exclude RECT ...] [--feather PX] [--exclude-feather PX]
      [--light-radius PX] [--light-strength 0..1] [--supersample K] [--post-blur PX]
      [--soften RECT ...] [--soften-radius PX] [--soften-feather PX]
      [--preview PREVIEW.jpg] [--preview-before IMAGE]

  --preview writes a JPG with three panels around the label: before, after, and the mask
  (red is replaced, blue is excluded). --preview-before swaps the before panel for another
  image of the same size as the scene, such as the last accepted version.

Output: a JSON summary on stdout with the inputs, image sizes, quads, homography, mask area
in pixels, settings, output path and the output's sha256. Exit 0 on success, 2 on a usage
or input error (bad quad, point outside the image, unreadable file, preview size mismatch),
1 on an unexpected failure.

Dependencies: Python 3 standard library, numpy and Pillow. Run it with `python3 -I -B`
from an interpreter that has both; on machines where the system python3 lacks numpy, use
the repository virtualenv, for example `.venv/bin/python3 -I -B`.

Check the result before it ships. Read the label back at 100% and at 200% zoom, word by
word and number by number, against the label facts. The transfer copies the source label
exactly, so a glyph error in the source artwork or packshot comes through on every
transfer: fix the source once, then re-run the transfers.
"""
import argparse
import hashlib
import json
import math
import os
import sys

try:
    import numpy as np
    from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError
except ImportError as exc:  # pragma: no cover - depends on the interpreter
    sys.stderr.write(
        f"label_transfer: error: needs numpy and Pillow ({exc}). Run it with an interpreter "
        "that has both, for example the repository .venv/bin/python3 -I -B.\n")
    sys.exit(2)

TOOL = "label_transfer"
MAX_SUPERSAMPLE = 8
MAX_CANVAS_PX = 64_000_000
LIGHT_RATIO_RANGE = (0.45, 2.2)
EIGHT_BIT_MODES = ("RGB", "RGBA", "L", "LA", "P")
REF_EDGE_PAD = 8
LOSSLESS_EXTS = (".png", ".tif", ".tiff")
EXIF_ORIENTATION = 0x0112


class InputError(Exception):
    """A usage or input problem; reported with exit code 2."""


# ---------------------------------------------------------------- parsing and validation

def parse_quad(text, name):
    parts = [p for p in str(text).replace(" ", "").split(";") if p != ""]
    if len(parts) != 4:
        raise InputError(f"{name} needs exactly 4 points as x,y;x,y;x,y;x,y, got {len(parts)}")
    pts = []
    for p in parts:
        xy = p.split(",")
        if len(xy) != 2:
            raise InputError(f"{name} point '{p}' is not x,y")
        try:
            x, y = float(xy[0]), float(xy[1])
        except ValueError:
            raise InputError(f"{name} point '{p}' is not numeric") from None
        if not (math.isfinite(x) and math.isfinite(y)):
            raise InputError(f"{name} point '{p}' is not finite")
        pts.append((x, y))
    return np.array(pts, np.float64)


def parse_rect(text, name):
    parts = str(text).replace(" ", "").split(",")
    if len(parts) != 4:
        raise InputError(f"{name} '{text}' needs x0,y0,x1,y1")
    try:
        x0, y0, x1, y1 = (float(v) for v in parts)
    except ValueError:
        raise InputError(f"{name} '{text}' is not numeric") from None
    if not (x1 > x0 and y1 > y0):
        raise InputError(f"{name} '{text}' needs x1 > x0 and y1 > y0")
    return (x0, y0, x1, y1)


def signed_area(q):
    x, y = q[:, 0], q[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def check_quad(q, size, name):
    w, h = size
    for x, y in q:
        if not (0 <= x <= w and 0 <= y <= h):
            raise InputError(f"{name} point ({x:g},{y:g}) is outside the {w}x{h} image")
    crosses = []
    for i in range(4):
        a, b, c = q[i], q[(i + 1) % 4], q[(i + 2) % 4]
        crosses.append((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]))
    if not (all(v > 0 for v in crosses) or all(v < 0 for v in crosses)):
        raise InputError(f"{name} is not a convex quad; give the corners in order "
                         "top-left, top-right, bottom-right, bottom-left")
    sides = [float(np.hypot(*(q[(i + 1) % 4] - q[i]))) for i in range(4)]
    if min(sides) < 2.0 or abs(signed_area(q)) < 16.0:
        raise InputError(f"{name} is too small (sides {min(sides):.1f} px, "
                         f"area {abs(signed_area(q)):.1f} px)")


def check_rect(r, size, name):
    w, h = size
    x0, y0, x1, y1 = r
    if x0 < 0 or y0 < 0 or x1 > w or y1 > h:
        raise InputError(f"{name} {r} is outside the {w}x{h} scene")


def load_image(path, role):
    if not os.path.isfile(path):
        raise InputError(f"{role} '{path}' does not exist or is not a file")
    try:
        im = Image.open(path)
        im.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InputError(f"{role} '{path}' is not a readable image ({exc})") from None
    if im.mode not in EIGHT_BIT_MODES:
        raise InputError(f"{role} '{path}' has image mode {im.mode}; only 8-bit RGB, RGBA, L, "
                         "LA or P images are supported, so convert it to 8-bit RGB first")
    return im


def first_edge_warning(q, name):
    """Warn when the first edge (point 1 to point 2) is not the upper edge of the quad."""
    mids = [(q[i][1] + q[(i + 1) % 4][1]) / 2.0 for i in range(4)]
    if int(np.argmin(mids)) != 0:
        return (f"{name}: the first edge (point 1 to point 2) is not the upper edge; corners "
                "should start at top-left and run top-right, bottom-right, bottom-left. "
                "Ignore this only if the label really is turned more than 45 degrees.")
    return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------- geometry

def fit_homography(src, dst):
    """Normalised DLT: 3x3 H with dst ~ H @ [src, 1]."""
    def norm(p):
        c = p.mean(axis=0)
        d = np.sqrt(((p - c) ** 2).sum(axis=1)).mean()
        s = math.sqrt(2) / max(d, 1e-12)
        return np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]], np.float64)
    Ts, Td = norm(src), norm(dst)
    sh = np.c_[src, np.ones(4)] @ Ts.T
    dh = np.c_[dst, np.ones(4)] @ Td.T
    rows = []
    for (x, y, _), (u, v, _) in zip(sh, dh):
        rows.append([-x, -y, -1, 0, 0, 0, u * x, u * y, u])
        rows.append([0, 0, 0, -x, -y, -1, v * x, v * y, v])
    _, _, vt = np.linalg.svd(np.array(rows, np.float64))
    Hn = vt[-1].reshape(3, 3)
    H = np.linalg.inv(Td) @ Hn @ Ts
    if abs(H[2, 2]) < 1e-12:
        raise InputError("the quads give a degenerate perspective fit")
    return H / H[2, 2]


def apply_h(H, pts):
    p = np.c_[pts, np.ones(len(pts))] @ H.T
    return p[:, :2] / p[:, 2:3]


def local_scale(H, point):
    """Linear scale of H at a reference point (sqrt of the Jacobian determinant)."""
    x, y = point
    w = H[2, 0] * x + H[2, 1] * y + H[2, 2]
    u = (H[0, 0] * x + H[0, 1] * y + H[0, 2]) / w
    v = (H[1, 0] * x + H[1, 1] * y + H[1, 2]) / w
    J = np.array([[H[0, 0] - u * H[2, 0], H[0, 1] - u * H[2, 1]],
                  [H[1, 0] - v * H[2, 0], H[1, 1] - v * H[2, 1]]]) / w
    return math.sqrt(abs(np.linalg.det(J)))


def warp_perspective(img, H_src_to_dst, size, resample):
    Hi = np.linalg.inv(H_src_to_dst)
    Hi = Hi / Hi[2, 2]
    coeffs = tuple(float(v) for v in Hi.ravel()[:8])
    return img.transform(size, Image.Transform.PERSPECTIVE, coeffs, resample=resample)


def quad_inside(quad, xs, ys):
    """Boolean grid: pixel centres (xs[None, :], ys[:, None]) inside the convex quad."""
    sign = 1.0 if signed_area(quad) > 0 else -1.0
    inside = np.ones((len(ys), len(xs)), bool)
    X, Y = xs[None, :], ys[:, None]
    for i in range(4):
        (x0, y0), (x1, y1) = quad[i], quad[(i + 1) % 4]
        cross = (x1 - x0) * (Y - y0) - (y1 - y0) * (X - x0)
        inside &= (cross * sign) >= 0
    return inside


def rect_inside(rect, xs, ys):
    x0, y0, x1, y1 = rect
    return ((ys[:, None] >= y0) & (ys[:, None] < y1)) & ((xs[None, :] >= x0) & (xs[None, :] < x1))


# ---------------------------------------------------------------- filtering

def gauss(arr, sigma):
    """Float Gaussian blur over the first two axes (FFT, reflected edges)."""
    arr = np.asarray(arr, np.float32)
    if sigma <= 0:
        return arr.copy()
    pad = int(math.ceil(3 * sigma)) + 2
    pw = [(pad, pad), (pad, pad)] + [(0, 0)] * (arr.ndim - 2)
    p = np.pad(arr, pw, mode="symmetric")
    fy = np.fft.fftfreq(p.shape[0])[:, None]
    fx = np.fft.rfftfreq(p.shape[1])[None, :]
    k = np.exp(-2.0 * (math.pi ** 2) * (sigma ** 2) * (fy ** 2 + fx ** 2))
    if arr.ndim == 3:
        k = k[..., None]
    out = np.fft.irfft2(np.fft.rfft2(p, axes=(0, 1)) * k, s=p.shape[:2], axes=(0, 1))
    return out[pad:pad + arr.shape[0], pad:pad + arr.shape[1]].astype(np.float32)


def feather_in(hard, sigma):
    """1 deep inside, ramping to exactly 0 at and beyond the edge of `hard`."""
    h = hard.astype(np.float32)
    if sigma <= 0:
        return h
    return np.clip(2.0 * gauss(h, sigma) - 1.0, 0.0, 1.0) * h


def masked_gauss(arr, mask, sigma):
    """Gaussian blur that only averages pixels where `mask` is set (normalised)."""
    if sigma <= 0:
        return np.asarray(arr, np.float32).copy()
    m = mask.astype(np.float32)
    den = np.maximum(gauss(m, sigma), 1e-6)
    out = gauss(arr * m[..., None], sigma) / den[..., None]
    return np.where(mask[..., None], out, arr).astype(np.float32)


def feather_out(hard, sigma):
    """Exactly 1 inside `hard`, ramping to 0 outside it."""
    h = hard.astype(np.float32)
    if sigma <= 0:
        return h
    return np.maximum(np.clip(2.0 * gauss(h, sigma), 0.0, 1.0), h)


# ---------------------------------------------------------------- main work

def transfer(scene_rgb, ref_img, H, scene_quad, args):
    W, H_img = scene_rgb.shape[1], scene_rgb.shape[0]
    top = np.hypot(*(scene_quad[1] - scene_quad[0])); bot = np.hypot(*(scene_quad[2] - scene_quad[3]))
    lef = np.hypot(*(scene_quad[3] - scene_quad[0])); rig = np.hypot(*(scene_quad[2] - scene_quad[1]))
    qw, qh = (top + bot) / 2.0, (lef + rig) / 2.0
    feather = args.feather if args.feather is not None else max(1.0, 0.01 * min(qw, qh))
    ex_feather = args.exclude_feather if args.exclude_feather is not None else feather
    light_r = args.light_radius if args.light_radius is not None else max(4.0, 0.05 * max(qw, qh))
    soften_feather = args.soften_feather if args.soften_feather is not None else args.soften_radius

    margin = int(math.ceil(3 * max(feather, ex_feather, light_r, args.soften_radius,
                                   soften_feather, args.post_blur))) + 8
    cx0 = max(0, int(math.floor(scene_quad[:, 0].min())) - margin)
    cy0 = max(0, int(math.floor(scene_quad[:, 1].min())) - margin)
    cx1 = min(W, int(math.ceil(scene_quad[:, 0].max())) + margin)
    cy1 = min(H_img, int(math.ceil(scene_quad[:, 1].max())) + margin)
    cw, ch = cx1 - cx0, cy1 - cy0

    # scale measured at the reference point that lands on the centre of the scene quad
    scale = local_scale(H, apply_h(np.linalg.inv(H), scene_quad.mean(axis=0)[None])[0])
    if args.supersample is not None:
        k = args.supersample
    else:
        k = int(min(MAX_SUPERSAMPLE, max(1, math.ceil(1.0 / max(scale, 1e-6)))))
    k = int(max(1, min(k, math.floor(math.sqrt(MAX_CANVAS_PX / max(cw * ch, 1))))))

    # pad the reference by repeating its edge, so samples at the artwork border do not
    # pull in black from outside the image
    pad = REF_EDGE_PAD
    ref_padded = Image.fromarray(np.pad(np.asarray(ref_img), ((pad, pad), (pad, pad), (0, 0)),
                                        mode="edge"))
    unpad = np.array([[1, 0, -pad], [0, 1, -pad], [0, 0, 1]], np.float64)
    shift = np.array([[k, 0, -k * cx0], [0, k, -k * cy0], [0, 0, 1]], np.float64)
    big = warp_perspective(ref_padded, shift @ H @ unpad, (cw * k, ch * k),
                           Image.Resampling.BICUBIC)
    small = big if k == 1 else big.resize((cw, ch), Image.Resampling.BOX)
    Rw = np.asarray(small, np.float32)

    S = scene_rgb[cy0:cy1, cx0:cx1].astype(np.float32)
    xs = cx0 + np.arange(cw) + 0.5
    ys = cy0 + np.arange(ch) + 0.5
    inside = quad_inside(scene_quad, xs, ys)
    excl_hard = np.zeros_like(inside)
    for r in args.exclude_rects:
        excl_hard |= rect_inside(r, xs, ys)

    # lighting: per-channel ratio of masked low-pass maps, label pixels only on both sides
    m = (inside & ~excl_hard).astype(np.float32)
    if m.sum() < 1:
        raise InputError("the exclude rectangles cover the whole scene quad")
    den = np.maximum(gauss(m, light_r), 1e-3)[..., None]
    Ls = gauss(S * m[..., None], light_r) / den
    Lr = gauss(Rw * m[..., None], light_r) / den
    ratio = np.clip(Ls / np.maximum(Lr, 1.0), *LIGHT_RATIO_RANGE)
    if args.light_strength != 1.0:
        ratio = ratio ** args.light_strength
    Rl = np.clip(Rw * ratio, 0, 255)
    # blurs average label pixels only, so nothing outside the quad bleeds into the edge
    if args.post_blur > 0:
        Rl = masked_gauss(Rl, inside, args.post_blur)

    for r in args.soften_rects:
        w = feather_in(rect_inside(r, xs, ys), soften_feather)[..., None]
        Rl = Rl * (1 - w) + masked_gauss(Rl, inside, args.soften_radius) * w

    M = feather_in(inside, feather)
    E = feather_out(excl_hard, ex_feather) if args.exclude_rects else np.zeros_like(M)
    M = M * (1.0 - E)
    M[~inside] = 0.0
    M[excl_hard] = 0.0

    blended = np.clip(np.rint(S * (1 - M[..., None]) + Rl * M[..., None]), 0, 255).astype(np.uint8)
    out = scene_rgb.copy()
    region = out[cy0:cy1, cx0:cx1]
    sel = M > 0
    region[sel] = blended[sel]
    info = {
        "crop": [cx0, cy0, cx1, cy1],
        "scale": round(scale, 5),
        "mask_area_px": int(sel.sum()),
        "mask_full_px": int((M >= 0.999).sum()),
        "mask_weight_px": round(float(M.sum()), 1),
        "excluded_px": int((excl_hard & inside).sum()),
        "settings": {
            "feather": round(float(feather), 3),
            "exclude_feather": round(float(ex_feather), 3),
            "light_radius": round(float(light_r), 3),
            "light_strength": args.light_strength,
            "supersample": k,
            "post_blur": args.post_blur,
            "soften_radius": args.soften_radius,
            "soften_feather": round(float(soften_feather), 3),
        },
    }
    return out, M, E, (cx0, cy0, cx1, cy1), info


def write_preview(path, before, after, M, E, crop, scene_quad):
    W, H = after.shape[1], after.shape[0]
    qw = scene_quad[:, 0].max() - scene_quad[:, 0].min()
    qh = scene_quad[:, 1].max() - scene_quad[:, 1].min()
    pad = int(max(16, 0.15 * max(qw, qh)))
    bx0 = max(0, int(scene_quad[:, 0].min()) - pad); by0 = max(0, int(scene_quad[:, 1].min()) - pad)
    bx1 = min(W, int(math.ceil(scene_quad[:, 0].max())) + pad)
    by1 = min(H, int(math.ceil(scene_quad[:, 1].max())) + pad)
    Mf = np.zeros((H, W), np.float32); Ef = np.zeros((H, W), np.float32)
    cx0, cy0, cx1, cy1 = crop
    Mf[cy0:cy1, cx0:cx1] = M; Ef[cy0:cy1, cx0:cx1] = E
    sl = (slice(by0, by1), slice(bx0, bx1))
    over = after[sl].astype(np.float32)
    m, e = Mf[sl][..., None] * 0.45, Ef[sl][..., None] * 0.45
    over = over * (1 - m) + np.array([255, 40, 40], np.float32) * m
    over = over * (1 - e) + np.array([40, 90, 255], np.float32) * e
    panels = [before[sl], after[sl], np.clip(over, 0, 255).astype(np.uint8)]
    ph = by1 - by0
    z = 2.0 if ph * 2 <= 1200 else 1200.0 / ph
    imgs = []
    for p in panels:
        im = Image.fromarray(p)
        imgs.append(im.resize((max(1, round(im.width * z)), max(1, round(im.height * z))),
                              Image.Resampling.LANCZOS))
    gap, head = 12, 22
    sheet = Image.new("RGB", (sum(i.width for i in imgs) + gap * (len(imgs) + 1),
                              imgs[0].height + head + gap), (250, 250, 250))
    d = ImageDraw.Draw(sheet)
    x = gap
    for im, label in zip(imgs, ("before", "after", "mask: red replaced, blue excluded")):
        d.text((x, 5), label, fill=(20, 20, 20))
        sheet.paste(im, (x, head))
        x += im.width + gap
    sheet.save(path, quality=92)


def build_parser():
    ap = argparse.ArgumentParser(
        prog="label_transfer.py",
        description="Warp a crisp reference label onto a rendered product, carry the scene "
                    "lighting onto it and replace only the label interior.")
    ap.add_argument("scene", help="the render whose label is garbled")
    ap.add_argument("reference", help="clean packshot or label artwork with the correct label")
    ap.add_argument("output", help="where to write the corrected render (.png recommended)")
    ap.add_argument("--ref-quad", required=True,
                    help="label corners in the reference: x,y;x,y;x,y;x,y (TL, TR, BR, BL)")
    ap.add_argument("--scene-quad", required=True,
                    help="the same corners in the scene, same order")
    ap.add_argument("--exclude", action="append", default=[], metavar="RECT",
                    help="x0,y0,x1,y1 scene rectangle that stays scene pixels (repeatable)")
    ap.add_argument("--feather", type=float, default=None,
                    help="inward mask feather, Gaussian sigma in scene px (default 1%% of the quad)")
    ap.add_argument("--exclude-feather", type=float, default=None,
                    help="outward feather around exclude rectangles (default: --feather)")
    ap.add_argument("--light-radius", type=float, default=None,
                    help="low-pass sigma for the lighting transfer in scene px (default 5%% of the quad)")
    ap.add_argument("--light-strength", type=float, default=1.0,
                    help="0 keeps the reference lighting, 1 takes the full scene lighting")
    ap.add_argument("--supersample", type=int, default=None,
                    help="warp supersampling factor 1..8 (default: chosen from the scale)")
    ap.add_argument("--post-blur", type=float, default=0.0,
                    help="Gaussian sigma applied to the whole transferred label to match scene softness")
    ap.add_argument("--soften", action="append", default=[], metavar="RECT",
                    help="x0,y0,x1,y1 scene rectangle where the transferred label is blurred "
                         "like depth of field (repeatable)")
    ap.add_argument("--soften-radius", type=float, default=1.5,
                    help="Gaussian sigma for --soften rectangles in scene px")
    ap.add_argument("--soften-feather", type=float, default=None,
                    help="inward feather of --soften rectangles (default: --soften-radius)")
    ap.add_argument("--preview", help="write a before, after and mask preview JPG here")
    ap.add_argument("--preview-before",
                    help="image used as the before panel instead of the scene (same size)")
    return ap


def run(argv):
    args = build_parser().parse_args(argv)
    if not (0.0 <= args.light_strength <= 1.0):
        raise InputError("--light-strength must be between 0 and 1")
    for name in ("feather", "exclude_feather", "light_radius", "soften_feather"):
        v = getattr(args, name)
        if v is not None and (v < 0 or not math.isfinite(v)):
            raise InputError(f"--{name.replace('_', '-')} must be 0 or more")
    if args.post_blur < 0 or args.soften_radius < 0:
        raise InputError("--post-blur and --soften-radius must be 0 or more")
    if args.supersample is not None and not (1 <= args.supersample <= MAX_SUPERSAMPLE):
        raise InputError(f"--supersample must be 1..{MAX_SUPERSAMPLE}")
    if args.soften and args.soften_radius <= 0:
        raise InputError("--soften needs --soften-radius above 0")

    out_path = os.path.abspath(args.output)
    for role, p in (("scene", args.scene), ("reference", args.reference)):
        if os.path.abspath(p) == out_path:
            raise InputError(f"output would overwrite the {role} image")
    if not os.path.isdir(os.path.dirname(out_path)):
        raise InputError(f"output folder '{os.path.dirname(out_path)}' does not exist")
    ext = os.path.splitext(out_path)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"):
        raise InputError("output must end in .png, .jpg, .jpeg, .webp, .tif or .tiff")
    if args.preview:
        pv = os.path.abspath(args.preview)
        if os.path.splitext(pv)[1].lower() not in (".jpg", ".jpeg"):
            raise InputError("--preview must end in .jpg or .jpeg")
        if pv in (out_path, os.path.abspath(args.scene), os.path.abspath(args.reference)):
            raise InputError("--preview would overwrite an input or the output")
        if not os.path.isdir(os.path.dirname(pv)):
            raise InputError(f"preview folder '{os.path.dirname(pv)}' does not exist")
    if args.preview_before and not args.preview:
        raise InputError("--preview-before needs --preview")
    warnings = []
    if ext not in LOSSLESS_EXTS:
        warnings.append(f"{ext} output re-encodes the whole frame, so pixels outside the quad "
                        "can change; write PNG or TIFF to keep them exact")

    scene_im = load_image(args.scene, "scene")
    ref_im = load_image(args.reference, "reference")
    orient = scene_im.getexif().get(EXIF_ORIENTATION, 1)
    if orient not in (0, 1):
        raise InputError(f"scene has EXIF orientation {orient}; save it upright first (for "
                         "example with PIL.ImageOps.exif_transpose) so coordinates match "
                         "the stored pixels")
    ref_im = ImageOps.exif_transpose(ref_im)
    ref_q = parse_quad(args.ref_quad, "--ref-quad")
    scene_q = parse_quad(args.scene_quad, "--scene-quad")
    check_quad(ref_q, ref_im.size, "--ref-quad")
    check_quad(scene_q, scene_im.size, "--scene-quad")
    if (signed_area(ref_q) > 0) != (signed_area(scene_q) > 0):
        raise InputError("the two quads run in opposite directions; list both as "
                         "top-left, top-right, bottom-right, bottom-left")
    for qq, name in ((ref_q, "--ref-quad"), (scene_q, "--scene-quad")):
        msg = first_edge_warning(qq, name)
        if msg:
            warnings.append(msg)
    args.exclude_rects = [parse_rect(r, "--exclude") for r in args.exclude]
    args.soften_rects = [parse_rect(r, "--soften") for r in args.soften]
    for r in args.exclude_rects:
        check_rect(r, scene_im.size, "--exclude")
    for r in args.soften_rects:
        check_rect(r, scene_im.size, "--soften")
    before_arr = None
    if args.preview_before:
        b = load_image(args.preview_before, "--preview-before")
        if b.size != scene_im.size:
            raise InputError(f"--preview-before is {b.size[0]}x{b.size[1]} but the scene is "
                             f"{scene_im.size[0]}x{scene_im.size[1]}")
        before_arr = np.asarray(b.convert("RGB"))

    alpha = scene_im.getchannel("A") if scene_im.mode in ("RGBA", "LA") else None
    scene_rgb = np.asarray(scene_im.convert("RGB"))
    ref_rgb = ref_im.convert("RGB")

    H = fit_homography(ref_q, scene_q)
    if np.max(np.abs(apply_h(H, ref_q) - scene_q)) > 0.05:
        raise InputError("the quads give an unstable perspective fit; check the corner order")

    out, M, E, crop, info = transfer(scene_rgb, ref_rgb, H, scene_q, args)
    if info["mask_full_px"] == 0:
        warnings.append("no pixel gets the full label: the quad is thinner than the feather "
                        "allows, so the label is only half blended; lower --feather or check "
                        "the corners")

    out_im = Image.fromarray(out)
    if alpha is not None and ext in (".png", ".webp", ".tif", ".tiff"):
        out_im.putalpha(alpha)
    save_kw = {"quality": 95} if ext in (".jpg", ".jpeg", ".webp") else {}
    if scene_im.info.get("icc_profile"):
        save_kw["icc_profile"] = scene_im.info["icc_profile"]
    exif = scene_im.getexif()
    if len(exif):
        save_kw["exif"] = exif.tobytes()
    out_im.save(out_path, **save_kw)

    preview_path = None
    if args.preview:
        preview_path = os.path.abspath(args.preview)
        write_preview(preview_path, before_arr if before_arr is not None else scene_rgb,
                      out, M, E, crop, scene_q)

    summary = {
        "tool": TOOL,
        "scene": {"path": os.path.abspath(args.scene), "size": list(scene_im.size),
                  "mode": scene_im.mode, "sha256": sha256_file(args.scene)},
        "reference": {"path": os.path.abspath(args.reference), "size": list(ref_im.size),
                      "mode": ref_im.mode, "sha256": sha256_file(args.reference)},
        "ref_quad": ref_q.round(3).tolist(),
        "scene_quad": scene_q.round(3).tolist(),
        "homography": np.round(H, 8).tolist(),
        "exclude": [list(r) for r in args.exclude_rects],
        "soften": [list(r) for r in args.soften_rects],
        **info,
        "output": {"path": out_path, "size": list(out_im.size), "sha256": sha256_file(out_path)},
        "preview": preview_path,
        "warnings": warnings,
        "next_check": "read the label back at 100% and 200% zoom against the label facts",
    }
    for w in warnings:
        sys.stderr.write(f"{TOOL}: warning: {w}\n")
    print(json.dumps(summary, indent=2))
    return 0


def main(argv=None):
    try:
        return run(sys.argv[1:] if argv is None else argv)
    except InputError as exc:
        sys.stderr.write(f"{TOOL}: error: {exc}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
