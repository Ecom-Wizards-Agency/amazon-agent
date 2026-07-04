#!/usr/bin/env python3
"""Regenerate the (gitignored) brand assets used by render_branded.py.

Operator-local helper with Ecom Wizards default source paths (override via env vars).
Agency identity (palette/fonts/strings) lives in _local/branding/branding.json — see BRANDING.md.

Sources are OPERATOR-LOCAL (pCloud / installed fonts) and never committed — like the MAG-SOP local
path in CLAUDE.md. Point EW_PCLOUD_ROOT at your local pCloud brand root (or override the individual
EW_* paths below). Outputs land in tools/amazon-ad-audit/brand/ (gitignored).

Produces: logo_white.png, logo_black.png (transparent, from the SVGs), mark_black.png (rocket mark
cropped from the black logo, for footers), and Inter-Variable.ttf (copied).

macOS has no rsvg/inkscape/cairosvg, so SVG->PNG uses headless Chrome --screenshot (see the
`ecom-wizards-brand-doc-pipeline` memory). Override any path via env vars.

    python3 tools/amazon-ad-audit/prepare_brand_assets.py
"""
import os, subprocess, shutil, sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
BRAND = HERE / "brand"; BRAND.mkdir(exist_ok=True)

PC = os.environ.get("EW_PCLOUD_ROOT", "<your-pcloud>/Account shares/Amazon Wizards")
LOGO_SVG_DIR = os.environ.get("EW_LOGO_SVG_DIR",
    f"{PC}/2_Company/2.1_Branding/Amazon Wizards/SVG/Logo/Ecom Wizards")
INTER_TTF = os.environ.get("EW_INTER_TTF",
    f"{PC}/3_Learning/3.3_TheFutur/The Perfect Proposal/Templates/01_Full Template/"
    "InDesign-Template/Document fonts/Inter-VariableFont_slnt,wght.ttf")
CHROME = os.environ.get("EW_CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")


def _svg_to_png(svg, out, w=2452, h=872):
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--default-background-color=00000000",
                    f"--window-size={w},{h}", f"--screenshot={out}", str(svg)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _crop_mark(black_png, out):
    im = Image.open(black_png).convert("RGBA"); a = im.split()[3]
    cols = [sum(a.getpixel((x, y)) for y in range(0, im.height, 6)) for x in range(im.width)]
    started = False; gap0 = None
    for x, v in enumerate(cols):
        if v > 0: started = True
        if started and v == 0:
            run = 1
            while x + run < len(cols) and cols[x + run] == 0: run += 1
            if run > im.width * 0.03: gap0 = x; break
    gap0 = gap0 or int(im.width * 0.24)
    mark = im.crop((0, 0, gap0, im.height)); mark = mark.crop(mark.split()[3].getbbox())
    mark.save(out)


def main():
    missing = [p for p in (Path(LOGO_SVG_DIR), Path(INTER_TTF), Path(CHROME)) if not p.exists()]
    if missing:
        print("[brand] MISSING local sources — set env vars or fix paths:")
        for m in missing: print("   ", m)
        return 1
    for name, png in (("logo_white_no_background", "logo_white.png"),
                      ("logo_black_no_background", "logo_black.png")):
        svg = Path(LOGO_SVG_DIR) / f"{name}.svg"
        tmp = BRAND / f"_{name}.svg"; shutil.copy(svg, tmp)
        _svg_to_png(tmp, BRAND / png); tmp.unlink(missing_ok=True)
        print("[brand] wrote", png)
    _crop_mark(BRAND / "logo_black.png", BRAND / "mark_black.png"); print("[brand] wrote mark_black.png")
    shutil.copy(INTER_TTF, BRAND / "Inter-Variable.ttf"); print("[brand] wrote Inter-Variable.ttf")
    print("[brand] done ->", BRAND)
    return 0


if __name__ == "__main__":
    sys.exit(main())
