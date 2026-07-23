#!/usr/bin/env python3
"""Branded audit renderer: narrative markdown + metrics -> A4 .docx + .pdf.

Client- and agency-agnostic. Consumes the operator-written `*_Sales_Audit_SCAFFOLD.md` (the narrative),
the run's `metrics.json` (for the KPI cards), the config (client / market / window / prepared_by /
first_time), the agency identity from `_local/branding/branding.json` (see BRANDING.md; falls back to a
Claude/Codex example style), and the local brand assets in `brand/`. Produces a light, readable body,
a dark **cover page** (first-time audits only), KPI stat-cards, restyled tables, a full-lockup running
header, a text-only three-part footer, and smart page-break hygiene. Degrades gracefully to plain
md_to_docx when assets are missing.

Markdown conventions (superset of md_to_docx.py — which has no image support):
  ## H2                      -> orange rule + section head
  ### Lever N: title  /  **Lever N — title**  -> orange "LEVER N" eyebrow + title
  ### H3                     -> sub-head
  > quote                    -> orange note callout
  ![caption](file.png)       -> figure + caption (path relative to the markdown file)
  | a | b |                  -> table (Ink header, tabular numbers)
  - / *  |  1.               -> bullets / numbered
  <!-- ... -->               -> dropped
KPI cards are auto-built from metrics.json and inserted right after the first H2.
"""
from __future__ import annotations
import os, re, json, base64, subprocess, html, io
from pathlib import Path

HERE = Path(__file__).resolve().parent

import branding as _branding

# palette/fonts — populated from the branding file (agency identity) via _apply_branding()
INK_H = CLOUD_H = ORANGE_H = MISTLINE_H = STEEL_H = MIST_H = ""
FONT_NAME = FONT_FILE = ""
_B: dict = {}
_CHROMES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]


def _apply_branding(b):
    global _B, INK_H, CLOUD_H, ORANGE_H, MISTLINE_H, STEEL_H, MIST_H, FONT_NAME, FONT_FILE
    _B = b
    p = b["palette_doc"]
    INK_H, CLOUD_H, ORANGE_H = p["ink"], p["cloud"], p["accent"]
    MISTLINE_H, STEEL_H, MIST_H = p["mistline"], p["steel"], p["mist"]
    FONT_NAME, FONT_FILE = b["fonts"]["doc_font_name"], b["fonts"]["doc_font_file"]


_apply_branding(_branding.load_branding({}))


def _chrome():
    for p in [os.environ.get("EW_CHROME", ""), os.environ.get("BRAND_CHROME", "")] + _CHROMES:
        if p and Path(p).exists(): return p
    return None


def _money(v, cur="USD"):
    s = "€" if cur in ("EUR", "€") else "$"
    if abs(v) >= 1_000_000: return f"{s}{v/1_000_000:.1f}M"
    if abs(v) >= 1_000: return f"{s}{round(v/1000)}K"
    return f"{s}{v:,.0f}"


def _bcfg(cfg, key, default=None):
    """Read a branding field from cfg['branding'][key], falling back to top-level, then default."""
    b = cfg.get("branding", {}) or {}
    v = b.get(key, cfg.get(key))
    return default if v in (None, "") else v


def _doc_label(cfg):
    return _bcfg(cfg, "doc_label", "Amazon Ad & Sales Audit")


def _report_month(cfg, M):
    """Return the deliverable month/year for the running header."""
    candidates = [str(cfg.get("date", ""))]
    windows = M.get("windows", {}) or cfg.get("windows", {}) or {}
    candidates.extend(str(windows.get(k, "")) for k in ("ads", "business_report"))
    for raw in candidates:
        dates = re.findall(r'\b(20\d{2})-(\d{2})-(\d{2})\b', raw)
        if dates:
            year, month, _ = dates[-1]
            names = ("", "JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE",
                     "JULY", "AUGUST", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER")
            mi = int(month)
            if 1 <= mi <= 12:
                return f"{names[mi]} {year}"
    return ""


def _running_text(cfg, M):
    label = _doc_label(cfg)
    month = _report_month(cfg, M)
    return {
        "header_right": f"{label.upper()} · {month}" if month else label.upper(),
        "footer_left": f"{label} · {cfg.get('client', '')}".rstrip(" ·"),
        "footer_right": _B.get("agency_url", ""),
    }


def _kpi_after(blocks):
    """Block index of the H2 to insert the KPI cards after: the verdict/summary section, else the first H2."""
    h2s = [(i, p) for i, (k, p) in enumerate(blocks) if k == "h2"]
    for i, p in h2s:
        if re.search(r'verdict|summary|snapshot|performance|the numbers', p, re.I): return i
    return h2s[0][0] if h2s else -1


def _kpis(M):
    if M.get("custom_kpis"):  # non-audit docs: [[number, label, sub-or-null], ...] in metrics.json
        return [(str(n), l, s) for n, l, s in M["custom_kpis"]]
    T = M["totals"]; cur = M.get("currency", "USD"); be = M.get("breakeven", 0.5)
    return [(_money(T["spend"], cur), "Ad spend / month", None),
            (_money(T["sales"], cur), "Ad sales", None),
            (f"{T['acos']*100:.0f}%", "Blended ACoS", f"vs ~{be*100:.0f}% break-even"),
            (f"{T['tacos']*100:.0f}%", "TACoS", None)]


# ------------------------------ markdown -> blocks ------------------------------
# Bold lead-in form: **Lever N — Title.** body text...  -> title = group2, body = group3
_LEVER_INLINE = re.compile(r'^\*\*\s*lever\s+(\d+)\s*[:\-—–]\s*(.+?)\.?\s*\*\*\s*(.*)$', re.I)
# Heading form: ### Lever N: Title   (or a bare "Lever N — Title" line)
_LEVER = re.compile(r'^(?:###\s*)?lever\s+(\d+)\s*[:\-—–]\s*(.+?)\.?$', re.I)
_IMG = re.compile(r'^!\[(.*?)\]\((.*?)\)$')
_COMMENT = re.compile(r'<!--.*?-->', re.S)


def parse_markdown(md, base_dir):
    blocks = []; tbl = []; title = None
    def flush():
        nonlocal tbl
        if tbl:
            rows = [r for r in tbl if not all(re.match(r'^:?-+:?$', c.strip() or '-') for c in r)]
            if rows: blocks.append(("table", rows))
            tbl = []
    for raw in _COMMENT.sub("", md).splitlines():
        s = raw.rstrip()
        if re.match(r'^\|.*\|\s*$', s):
            tbl.append([c.strip() for c in s.strip().strip('|').split('|')]); continue
        flush()
        if not s.strip(): continue
        if s.startswith("# "): title = s[2:].strip(); continue
        if s.strip() in ("---", "—"): continue
        mLi = _LEVER_INLINE.match(s.strip())
        if mLi:
            blocks.append(("lever", (int(mLi.group(1)), mLi.group(2).strip().rstrip("."))))
            body = mLi.group(3).strip()
            if body: blocks.append(("p", body))
            continue
        mL = _LEVER.match(s.strip())
        if mL: blocks.append(("lever", (int(mL.group(1)), mL.group(2).strip().rstrip(".")))); continue
        if s.startswith("### "): blocks.append(("h3", s[4:].strip())); continue
        if s.startswith("## "): blocks.append(("h2", s[3:].strip())); continue
        if s.startswith("> "): blocks.append(("note", s[2:].strip())); continue
        mI = _IMG.match(s.strip())
        if mI:
            p = Path(mI.group(2))
            if not p.is_absolute(): p = Path(base_dir) / p
            blocks.append(("img", (str(p), mI.group(1)))); continue
        if re.match(r'^\s*[-*] ', s): blocks.append(("bul", re.sub(r'^\s*[-*] ', '', s))); continue
        if re.match(r'^\s*\d+\. ', s): blocks.append(("num", re.sub(r'^\s*\d+\. ', '', s))); continue
        # a leading "**Prepared by ...**" byline line is cover material -> drop from body
        if re.match(r'^\*\*Prepared by', s.strip()): continue
        blocks.append(("p", s.strip()))
    flush()
    return title, blocks


def _cover_kwargs(cfg, M, blocks, brand_dir):
    client = cfg.get("client", "Client")
    markets = cfg.get("marketplaces", []) or []
    mname = "UNITED STATES" if markets == ["US"] else " / ".join(markets)
    win = (M.get("windows", {}) or cfg.get("windows", {})).get("business_report", "")
    sub = _bcfg(cfg, "cover_subtitle", "A straight look at the account, with recommendations on where to start.")
    words = sub.split(); lines = []; cur = ""
    for w in words:
        if len(cur) + len(w) + 1 > 30: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: lines.append(cur)
    inside = [(f"{i+1:02d}", t) for i, (k, t) in enumerate([b for b in blocks if b[0] == "h2"])
              if t.lower() != "sources used"][:4]
    by = _bcfg(cfg, "prepared_by", _B.get("prepared_by_default") or "the operator")
    label = _doc_label(cfg)
    return dict(brand_dir=str(brand_dir), title=client,
                eyebrow=label.upper(), dateline=f"{mname} · {win}".upper(),
                sub_lines=lines or [sub], prepared_for=client,
                prepared_by=_branding.prepared_by_line(_B, by),
                inside=inside, footer_left=_branding.cover_footer_left(_B),
                footer_right=label, palette=_B["palette_doc"], font_file=FONT_FILE,
                logo_file=_B["assets"]["logo_white"])


# ------------------------------ DOCX ------------------------------
def _render_docx(blocks, M, cfg, brand_dir, cover_png, out):
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
    from docx.enum.section import WD_SECTION
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    def _rgb(h): return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    INK = _rgb(INK_H); STEEL = _rgb(STEEL_H)
    MIST = _rgb(MIST_H); ORANGE = _rgb(ORANGE_H); WHITE = RGBColor(0xFF, 0xFF, 0xFF)
    A4_W = Inches(8.27); A4_H = Inches(11.69)
    doc = Document()
    nm = doc.styles['Normal']; nm.font.name = FONT_NAME; nm.font.size = Pt(10.5); nm.font.color.rgb = INK
    pf = nm.paragraph_format; pf.line_spacing = 1.4; pf.space_after = Pt(7); pf.widow_control = True

    def font(r):
        r.font.name = FONT_NAME; rpr = r._element.get_or_add_rPr(); rf = rpr.find(qn('w:rFonts'))
        if rf is None: rf = OxmlElement('w:rFonts'); rpr.append(rf)
        for a in ('w:ascii', 'w:hAnsi', 'w:cs'): rf.set(qn(a), FONT_NAME)

    def runs(p, text, size=10.5, color=INK, bold=False, italic=False, caps=False, tracking=None):
        for i, part in enumerate(re.split(r'\*\*(.+?)\*\*', text)):
            if part == '': continue
            r = p.add_run(part.upper() if caps else part); font(r)
            r.font.size = Pt(size); r.font.color.rgb = color; r.bold = bold or (i % 2 == 1); r.italic = italic
            if tracking is not None:
                rp = r._element.get_or_add_rPr(); sp = OxmlElement('w:spacing'); sp.set(qn('w:val'), str(tracking)); rp.append(sp)

    def para(text, **k):
        p = doc.add_paragraph(); runs(p, text, **k); return p

    def cantsplit(t):
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))

    def shade(c, h):
        s = OxmlElement('w:shd'); s.set(qn('w:val'), 'clear'); s.set(qn('w:fill'), h); c._tc.get_or_add_tcPr().append(s)

    def topborder(c, h, sz=24):
        b = OxmlElement('w:tcBorders'); t = OxmlElement('w:top')
        t.set(qn('w:val'), 'single'); t.set(qn('w:sz'), str(sz)); t.set(qn('w:color'), h); b.append(t)
        c._tc.get_or_add_tcPr().append(b)

    def no_table_borders(t):
        b = OxmlElement('w:tblBorders')
        for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            x = OxmlElement('w:' + e); x.set(qn('w:val'), 'nil'); b.append(x)
        t._tbl.tblPr.append(b)

    def compact(p):
        p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(0)

    def field(p, instruction, display):
        # Every run in the field carries the footer's own size/colour, not just the cached
        # display run. Word and Google Docs re-render the field using the field runs'
        # formatting, so an unstyled begin/instrText/separate/end leaks Normal (10.5pt Ink)
        # into the footer and the number renders bigger and darker than "page" / "of".
        def fld_run():
            r = p.add_run(); font(r); r.font.size = Pt(8); r.font.color.rgb = MIST
            return r
        r = fld_run(); begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin'); r._r.append(begin)
        r = fld_run(); instr = OxmlElement('w:instrText'); instr.set(qn('xml:space'), 'preserve'); instr.text = f' {instruction} '
        r._r.append(instr)
        r = fld_run(); separate = OxmlElement('w:fldChar'); separate.set(qn('w:fldCharType'), 'separate'); r._r.append(separate)
        r = p.add_run(display); font(r); r.font.size = Pt(8); r.font.color.rgb = MIST
        r = fld_run(); end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end'); r._r.append(end)

    def orange_rule():
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(3); p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.keep_with_next = True; p.add_run()
        pPr = p._p.get_or_add_pPr(); bd = OxmlElement('w:pBdr'); bo = OxmlElement('w:bottom')
        bo.set(qn('w:val'), 'single'); bo.set(qn('w:sz'), '24'); bo.set(qn('w:space'), '1'); bo.set(qn('w:color'), ORANGE_H)
        bd.append(bo); pPr.append(bd); p.paragraph_format.right_indent = Inches(5.4)

    def data_table(rows):
        t = doc.add_table(rows=0, cols=len(rows[0]))
        for ri, row in enumerate(rows):
            cells = t.add_row().cells
            for ci in range(len(rows[0])):
                txt = row[ci] if ci < len(row) else ''
                cells[ci].text = ''
                if ri == 0: shade(cells[ci], INK_H)
                elif ri % 2 == 0: shade(cells[ci], CLOUD_H)
                pc = cells[ci].paragraphs[0]; pc.paragraph_format.space_after = Pt(2); pc.paragraph_format.space_before = Pt(2)
                runs(pc, txt, size=8.5, color=(WHITE if ri == 0 else INK), bold=(ri == 0))
        b = OxmlElement('w:tblBorders')
        for e in ('top', 'bottom', 'insideH'):
            x = OxmlElement('w:' + e); x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), '4'); x.set(qn('w:color'), MISTLINE_H); b.append(x)
        for e in ('left', 'right', 'insideV'):
            x = OxmlElement('w:' + e); x.set(qn('w:val'), 'none'); b.append(x)
        t._tbl.tblPr.append(b); cantsplit(t)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def kpi_cards(items):
        t = doc.add_table(rows=0, cols=len(items))
        nb = OxmlElement('w:tblBorders')
        for e in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            x = OxmlElement('w:' + e); x.set(qn('w:val'), 'none'); nb.append(x)
        t._tbl.tblPr.append(nb)
        cells = t.add_row().cells
        for ci, (num, label, sub) in enumerate(items):
            c = cells[ci]; c.text = ''; shade(c, CLOUD_H); topborder(c, ORANGE_H, 24)
            p0 = c.paragraphs[0]; p0.paragraph_format.space_before = Pt(6); p0.paragraph_format.space_after = Pt(0)
            runs(p0, num, size=25, color=INK, bold=True)
            p1 = c.add_paragraph(); p1.paragraph_format.space_after = Pt(0)
            runs(p1, label, size=8, color=STEEL, bold=True, caps=True, tracking=20)
            p2 = c.add_paragraph(); p2.paragraph_format.space_before = Pt(1); p2.paragraph_format.space_after = Pt(6)
            if sub: runs(p2, sub, size=8.5, color=ORANGE)
        cantsplit(t)
        doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def image(path, caption):
        if not Path(path).exists():
            para(f"[missing image: {Path(path).name}]", size=8.5, color=STEEL, italic=True); return
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6); p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(str(path), width=Inches(6.2))
        c = doc.add_paragraph(); c.alignment = WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_after = Pt(10)
        runs(c, caption, size=8.5, color=STEEL, italic=True)

    def h2(text):
        orange_rule()
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(8); p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.keep_with_next = True; runs(p, text, size=18, color=INK, bold=True)

    def h3(text):
        p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(10); p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.keep_with_next = True; runs(p, text, size=12.5, color=INK, bold=True)

    def lever(n, title):
        p = doc.add_paragraph(); p.paragraph_format.space_before = Pt(14); p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.keep_with_next = True; runs(p, f"LEVER {n}", size=9, color=ORANGE, bold=True, caps=True, tracking=30)
        p2 = doc.add_paragraph(); p2.paragraph_format.space_after = Pt(6); p2.paragraph_format.keep_with_next = True
        runs(p2, title, size=14, color=INK, bold=True)

    def note(text):
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(9)
        pPr = p._p.get_or_add_pPr(); bd = OxmlElement('w:pBdr'); lf = OxmlElement('w:left')
        lf.set(qn('w:val'), 'single'); lf.set(qn('w:sz'), '18'); lf.set(qn('w:space'), '8'); lf.set(qn('w:color'), ORANGE_H)
        bd.append(lf); pPr.append(bd); p.paragraph_format.left_indent = Inches(0.12)
        runs(p, text, size=9.5, color=STEEL, italic=True)

    def bullet(text, num=False):
        p = doc.add_paragraph(style='List Number' if num else 'List Bullet'); runs(p, text)

    # cover section
    sec0 = doc.sections[0]; sec0.page_width = A4_W; sec0.page_height = A4_H
    if cover_png:
        for m in ('top', 'bottom', 'left', 'right'): setattr(sec0, f'{m}_margin', Inches(0))
        sec0.header_distance = Inches(0); sec0.footer_distance = Inches(0)
        cp = doc.add_paragraph(); cp.paragraph_format.space_after = Pt(0); cp.paragraph_format.space_before = Pt(0)
        # A 1pt exact line makes LibreOffice/Google Docs drop the full-page image. Normal spacing keeps
        # the editable cover visible while the zero-margin section preserves the intended full bleed.
        cp.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE; cp.paragraph_format.line_spacing = 1.0
        cr = cp.add_run(); cr.font.size = Pt(1); cr.add_picture(str(cover_png), width=A4_W)
        doc.add_section(WD_SECTION.NEW_PAGE); body = doc.sections[1]
    else:
        body = sec0
    body.page_width = A4_W; body.page_height = A4_H
    body.top_margin = Inches(0.85); body.bottom_margin = Inches(0.8)
    body.left_margin = Inches(0.85); body.right_margin = Inches(0.85)

    # Running furniture: full lockup in the header, text-only footer.
    run = _running_text(cfg, M)
    logo = Path(brand_dir) / _B["assets"].get("logo_black", "logo_black.png")
    body.header.is_linked_to_previous = False
    hp0 = body.header.paragraphs[0]; hp0.text = ''; compact(hp0)
    ht = body.header.add_table(rows=1, cols=2, width=Inches(6.57)); ht.autofit = False
    ht.alignment = WD_TABLE_ALIGNMENT.CENTER; no_table_borders(ht)
    hc0, hc1 = ht.rows[0].cells; hc0.width = Inches(2.05); hc1.width = Inches(4.52)
    for c in (hc0, hc1): c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    hp = hc0.paragraphs[0]; compact(hp)
    if logo.exists(): hp.add_run().add_picture(str(logo), width=Inches(0.9))
    elif _B.get("agency_name"): runs(hp, _B["agency_name"], size=8, color=INK, bold=True)
    hp = hc1.paragraphs[0]; compact(hp); hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    runs(hp, run["header_right"], size=7.5, color=MIST, bold=True, tracking=12)

    body.footer.is_linked_to_previous = False
    fp0 = body.footer.paragraphs[0]; fp0.text = ''; compact(fp0)
    ft = body.footer.add_table(rows=1, cols=3, width=Inches(6.57)); ft.autofit = False
    ft.alignment = WD_TABLE_ALIGNMENT.CENTER; no_table_borders(ft)
    fc0, fc1, fc2 = ft.rows[0].cells
    for c, w in zip((fc0, fc1, fc2), (2.55, 1.47, 2.55)):
        c.width = Inches(w); c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    fp = fc0.paragraphs[0]; compact(fp); runs(fp, run["footer_left"], size=8, color=MIST)
    fp = fc1.paragraphs[0]; compact(fp); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    runs(fp, "page ", size=8, color=MIST); field(fp, "PAGE", "1"); runs(fp, " of ", size=8, color=MIST); field(fp, "NUMPAGES", "1")
    fp = fc2.paragraphs[0]; compact(fp); fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    runs(fp, run["footer_right"], size=8, color=MIST)

    # render blocks (+ KPI after the verdict/summary h2)
    kpi_idx = _kpi_after(blocks)
    for i, (kind, payload) in enumerate(blocks):
        if kind == "h2":
            h2(payload)
            if i == kpi_idx: kpi_cards(_kpis(M))
        elif kind == "h3": h3(payload)
        elif kind == "lever": lever(*payload)
        elif kind == "p": para(payload)
        elif kind == "note": note(payload)
        elif kind == "bul": bullet(payload)
        elif kind == "num": bullet(payload, num=True)
        elif kind == "table": data_table(payload)
        elif kind == "img": image(*payload)
    # NUMPAGES has no cached value we can compute here, so it ships as "1". Without this
    # flag Word and Google Docs render that stale cache and a multi-page audit reads
    # "page 1 of 1". updateFields makes them recompute the footer counters on open.
    settings = doc.settings.element
    if settings.find(qn('w:updateFields')) is None:
        uf = OxmlElement('w:updateFields'); uf.set(qn('w:val'), 'true'); settings.append(uf)
    doc.save(out)
    return out


# ------------------------------ PDF (HTML + Chrome) ------------------------------
def _render_pdf(blocks, M, cfg, brand_dir, cover_png, out):
    chrome = _chrome()
    if not chrome: raise RuntimeError("no headless Chrome for PDF")
    var = Path(brand_dir) / FONT_FILE

    def b64(p): return base64.b64encode(Path(p).read_bytes()).decode()
    def imguri(p): return f"data:image/png;base64,{b64(p)}"

    def inl(t):
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html.escape(t))

    def table_html(rows):
        head = "".join(f"<th>{inl(c)}</th>" for c in rows[0])
        body = "".join("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in r) + "</tr>" for r in rows[1:])
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    def kpi_html(items):
        cs = "".join(f'<div class="kpi"><div class="kn">{html.escape(n)}</div>'
                     f'<div class="kl">{html.escape(l)}</div>' +
                     (f'<div class="ks">{html.escape(s)}</div>' if s else '') + '</div>' for n, l, s in items)
        return f'<div class="kpis">{cs}</div>'

    parts = []; numctr = 0; kpi_idx = _kpi_after(blocks)
    for i, (kind, payload) in enumerate(blocks):
        if kind != "num": numctr = 0
        if kind == "h2":
            parts.append(f'<div class="rule"></div><h2>{html.escape(payload)}</h2>')
            if i == kpi_idx: parts.append(kpi_html(_kpis(M)))
        elif kind == "h3": parts.append(f'<h3>{html.escape(payload)}</h3>')
        elif kind == "lever":
            n, t = payload
            parts.append(f'<div class="lever"><div class="eyebrow">LEVER {n}</div><h3 class="lt">{html.escape(t)}</h3></div>')
        elif kind == "p": parts.append(f'<p>{inl(payload)}</p>')
        elif kind == "note": parts.append(f'<div class="note">{inl(payload)}</div>')
        elif kind == "bul": parts.append(f'<ul><li>{inl(payload)}</li></ul>')
        elif kind == "num":
            numctr += 1; parts.append(f'<div class="numline"><span class="nnum">{numctr}</span>{inl(payload)}</div>')
        elif kind == "table": parts.append(table_html(payload))
        elif kind == "img":
            f, cap = payload
            if Path(f).exists():
                parts.append(f'<figure><img src="{imguri(f)}"><figcaption>{html.escape(cap)}</figcaption></figure>')
    bodyhtml = "".join(parts).replace("</ul><ul>", "")
    run = _running_text(cfg, M)
    logo = Path(brand_dir) / _B["assets"].get("logo_black", "logo_black.png")
    logo_content = 'content:"";'
    if logo.exists():
        try:
            from PIL import Image
            im = Image.open(logo).convert("RGBA")
            bbox = im.getchannel("A").getbbox()
            if bbox: im = im.crop(bbox)
            w = 86; im = im.resize((w, max(1, round(w * im.height / im.width))), Image.Resampling.LANCZOS)
            buf = io.BytesIO(); im.save(buf, format="PNG")
            logo_content = f'content:url("data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}");'
        except Exception:
            pass
    def css_text(s): return str(s).replace('\\', '\\\\').replace('"', '\\"')
    fontcss = (f"@font-face{{font-family:{FONT_NAME};font-weight:100 900;font-style:normal;"
               f"src:url(data:font/ttf;base64,{b64(var)}) format('truetype-variations');}}") if var.exists() else ""
    coverdiv = f'<div class="cover"><img src="{imguri(cover_png)}"></div>' if cover_png else ''
    CSS = f"""{fontcss}
*{{box-sizing:border-box;}} html,body{{margin:0;padding:0;}}
body{{font-family:{FONT_NAME},'Helvetica Neue',sans-serif;color:#{INK_H};font-size:10.5pt;line-height:1.55;
 -webkit-print-color-adjust:exact;print-color-adjust:exact;}}
@page{{size:A4;margin:0.85in 0.75in 0.85in 0.75in;
 @top-left{{{logo_content}vertical-align:middle;}}
 @top-right{{content:"{css_text(run['header_right'])}";font-family:{FONT_NAME};font-size:7.5pt;font-weight:600;letter-spacing:.08em;color:#{MIST_H};vertical-align:bottom;padding-bottom:8pt;}}
 @bottom-left{{content:"{css_text(run['footer_left'])}";font-family:{FONT_NAME};font-size:8pt;color:#{MIST_H};}}
 @bottom-center{{content:"page " counter(page) " of " counter(pages);font-family:{FONT_NAME};font-size:8pt;color:#{MIST_H};}}
 @bottom-right{{content:"{css_text(run['footer_right'])}";font-family:{FONT_NAME};font-size:8pt;color:#{MIST_H};}}}}
@page cover{{margin:0;@top-left{{content:"";background:none;}}@top-right{{content:"";}}@bottom-left{{content:"";}}@bottom-center{{content:"";}}@bottom-right{{content:"";}}}}
.cover{{page:cover;break-after:page;position:relative;z-index:5;}}
.cover img{{display:block;width:8.27in;height:11.69in;}}
h2,h3,.eyebrow,.lever,.rule{{break-after:avoid;}}
tr,figure,table,.kpis,.note{{break-inside:avoid;}}
h2{{font-weight:700;font-size:19pt;margin:2pt 0 8pt;letter-spacing:-0.01em;}}
h3{{font-weight:700;font-size:13pt;margin:12pt 0 5pt;}}
.lever{{margin:16pt 0 4pt;padding-top:8pt;border-top:1px solid #{MISTLINE_H};}}
.eyebrow{{font-weight:600;font-size:8.5pt;letter-spacing:0.14em;color:#{ORANGE_H};text-transform:uppercase;}}
h3.lt{{margin:2pt 0 6pt;font-size:14.5pt;}}
.rule{{width:64px;height:4px;background:#{ORANGE_H};margin:16pt 0 8pt;border-radius:2px;}}
p{{margin:0 0 7pt;orphans:2;widows:2;}} strong{{font-weight:700;}}
ul{{margin:0 0 8pt;padding-left:16pt;}} li{{margin:0 0 4pt;}}
.numline{{margin:0 0 6pt;padding-left:14pt;}} .nnum{{color:#{ORANGE_H};font-weight:800;margin-right:8px;}}
.note{{border-left:3px solid #{ORANGE_H};background:#{CLOUD_H};padding:8pt 12pt;margin:0 0 10pt;
 font-size:9.5pt;color:#{STEEL_H};font-style:italic;border-radius:0 4px 4px 0;}}
table{{width:100%;border-collapse:collapse;margin:4pt 0 12pt;font-size:8.6pt;font-variant-numeric:tabular-nums;}}
th{{background:#{INK_H};color:#fff;font-weight:600;text-align:left;padding:6px 8px;}}
td{{padding:5px 8px;border-bottom:1px solid #{MISTLINE_H};}} tbody tr:nth-child(even){{background:#{CLOUD_H};}}
.kpis{{display:flex;gap:10px;margin:6pt 0 12pt;}}
.kpi{{flex:1;background:#{CLOUD_H};border:1px solid #{MISTLINE_H};border-top:3px solid #{ORANGE_H};border-radius:6px;padding:10px 12px;}}
.kn{{font-weight:800;font-size:22pt;letter-spacing:-0.02em;line-height:1;}}
.kl{{font-weight:600;font-size:7.5pt;letter-spacing:0.08em;text-transform:uppercase;color:#{STEEL_H};margin-top:5px;}}
.ks{{font-size:8.5pt;color:#{ORANGE_H};margin-top:2px;}}
figure{{margin:8pt 0 10pt;text-align:center;}}
figure img{{max-width:100%;border:1px solid #{MISTLINE_H};border-radius:4px;}}
figcaption{{font-size:8.5pt;color:#{STEEL_H};font-style:italic;margin-top:5px;}}"""
    doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{coverdiv}<div class="wrap">{bodyhtml}</div></body></html>'
    htmlp = Path(out).with_suffix(".html"); htmlp.write_text(doc)
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", htmlp.as_uri()], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    htmlp.unlink(missing_ok=True)
    return out


# ------------------------------ entry ------------------------------
def render(cfg, outdir, scaffold_md, cover=False, brand_dir=None):
    """Render branded .docx (+ .pdf) from the narrative markdown. Returns dict of outputs.
    Raises on hard failure; callers should fall back to md_to_docx."""
    outdir = Path(outdir).resolve(); scaffold_md = Path(scaffold_md)  # absolute so headless-Chrome file:// URI works
    _apply_branding(_branding.load_branding(cfg))
    brand_dir = Path(brand_dir or _bcfg(cfg, "brand_dir") or _B["assets"]["brand_dir"] or (HERE / "brand"))
    M = json.loads((outdir / "metrics.json").read_text())
    title, blocks = parse_markdown(scaffold_md.read_text(), scaffold_md.parent)
    stem = scaffold_md.name.replace("_SCAFFOLD.md", "").replace(".md", "")
    out_docx = outdir / f"{stem}_BRANDED.docx"
    result = {}

    cover_png = None
    if cover:
        need = [FONT_FILE, _B["assets"]["logo_white"]]
        if all((brand_dir / n).exists() for n in need):
            from brand_cover import build_cover
            cover_png = outdir / "_cover.png"
            build_cover(str(cover_png), **_cover_kwargs(cfg, M, blocks, brand_dir))
        else:
            print(f"[brand] cover skipped — assets missing in {brand_dir} (run prepare_brand_assets.py)")

    _render_docx(blocks, M, cfg, brand_dir, cover_png, out_docx)
    result["docx"] = out_docx; print("[brand] wrote", out_docx.name)
    try:
        out_pdf = outdir / f"{stem}_BRANDED.pdf"
        _render_pdf(blocks, M, cfg, brand_dir, cover_png, out_pdf)
        result["pdf"] = out_pdf; print("[brand] wrote", out_pdf.name)
    except Exception as e:
        print(f"[brand] PDF skipped: {e}")
    return result


if __name__ == "__main__":
    import argparse
    from analyze_audit import load_config
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True); ap.add_argument("--outdir", required=True)
    ap.add_argument("--md", required=True); ap.add_argument("--cover", action="store_true")
    a = ap.parse_args()
    render(load_config(a.config), a.outdir, a.md, cover=a.cover)
