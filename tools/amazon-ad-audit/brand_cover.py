#!/usr/bin/env python3
"""Branded audit cover (A4 @200dpi). Client- and agency-agnostic; used by render_branded.py.

Reads the variable font + white logo from the brand dir and the palette from the branding file
(_local/branding/branding.json via branding.py — see BRANDING.md). Version-D layout: smaller logo
grouped with the eyebrow, vertically centred, horizontal rules snapped onto the grid.
"""
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W,H=1654,2339; MX=140; GRID=88


def _rgb(h):
    return (int(h[0:2],16), int(h[2:4],16), int(h[4:6],16))


def _snap(v): return int(round(v/GRID))*GRID


def build_cover(out, brand_dir, title, eyebrow, dateline, sub_lines, prepared_for, prepared_by,
                inside, footer_left, footer_right, logo_w=300, logo_y=300, block_y=440, inside_y=1496,
                palette=None, font_file="Inter-Variable.ttf", logo_file="logo_white.png"):
    if palette is None:
        import branding as _branding
        palette = _branding.load_branding({})["palette_doc"]
    OBSIDIAN=_rgb(palette["cover_bg"]); WHITE=_rgb(palette["white"]); CLOUD=_rgb(palette["cloud"])
    MIST=_rgb(palette["mist"]); STEEL=_rgb(palette["steel"]); SLATE=_rgb(palette["cover_slate"])
    ORANGE=_rgb(palette["accent"])
    brand_dir = Path(brand_dir)
    var = str(brand_dir / font_file)

    def inter(w, size):
        f = ImageFont.truetype(var, size)
        try: f.set_variation_by_name(w)
        except Exception: pass
        return f

    def tracked(d, xy, text, font, fill, tr=0):
        x, y = xy
        for ch in text:
            d.text((x, y), ch, font=font, fill=fill); x += d.textlength(ch, font=font) + tr
        return x

    img = Image.new("RGB", (W, H), OBSIDIAN)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(grid)
    for x in range(0, W, GRID): gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 13), width=1)
    for y in range(0, H, GRID): gd.line([(0, y), (W, y)], fill=(255, 255, 255, 13), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), grid).convert("RGB")
    d = ImageDraw.Draw(img)

    logo = Image.open(brand_dir / logo_file).convert("RGBA")
    logo = logo.crop(logo.split()[3].getbbox())
    lh = int(logo_w * logo.height / logo.width); logo = logo.resize((logo_w, lh), Image.LANCZOS)
    img.paste(logo, (MX, logo_y), logo)

    ry = _snap(block_y)
    d.rectangle([MX, ry - 4, MX + 92, ry + 4], fill=ORANGE)
    y = ry + 46
    tracked(d, (MX, y), eyebrow, inter("SemiBold", 26), ORANGE, tr=3); y += 46
    tracked(d, (MX, y), dateline, inter("SemiBold", 22), MIST, tr=3)
    y += 96
    d.text((MX, y), title, font=inter("Black", 140), fill=WHITE); y += 196
    for ln in sub_lines:
        d.text((MX, y), ln, font=inter("Regular", 44), fill=MIST); y += 60
    y = _snap(y + 90)
    d.line([(MX, y), (W - MX, y)], fill=SLATE, width=2); y += 34
    tracked(d, (MX, y), "PREPARED FOR", inter("SemiBold", 21), STEEL, tr=3); y += 40
    d.text((MX, y), prepared_for, font=inter("Bold", 38), fill=WHITE); y += 56
    d.text((MX, y), prepared_by, font=inter("Regular", 29), fill=MIST)
    y = inside_y
    tracked(d, (MX, y), "WHAT'S INSIDE", inter("SemiBold", 21), ORANGE, tr=3); y += 54
    for num, txt in inside:
        d.text((MX, y), num, font=inter("Bold", 33), fill=ORANGE)
        d.text((MX + 78, y), txt, font=inter("Regular", 33), fill=CLOUD); y += 62
    fy = _snap(H - 150)
    d.line([(MX, fy), (W - MX, fy)], fill=SLATE, width=2)
    d.text((MX, fy + 28), footer_left, font=inter("Regular", 25), fill=STEEL)
    w = d.textlength(footer_right, font=inter("Regular", 25))
    d.text((W - MX - w, fy + 28), footer_right, font=inter("Regular", 25), fill=STEEL)
    img.save(out); return out
