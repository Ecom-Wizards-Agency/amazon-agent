#!/usr/bin/env python3
"""Branding loader — single source of agency identity for every renderer/builder here.

Resolution order (first hit wins, deep-merged over the built-in neutral defaults):
  1. `_local/branding/branding.json` at the repo root (operator/agency identity —
     gitignored; copy `branding.TEMPLATE.json` there and fill it in), path
     overridable via config `branding.branding_json`.
  2. An agent-style example that ships with the repo: `branding.EXAMPLE-claude.json`
     when running under Claude Code (env CLAUDECODE/CLAUDE_CODE*), or
     `branding.EXAMPLE-codex.json` under Codex (env CODEX_*). Claude style otherwise.
  3. Built-in neutral defaults (grayscale + blue accent) — rendering always works.

Per-document keys (prepared_by, cover_subtitle, doc_label, first_time, brand_dir)
stay in the client config's `branding` block and are read by the callers via their
own `_bcfg`; this module only supplies the agency identity + palette + fonts.

See BRANDING.md for the full schema and the document layout rules.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]

_DEFAULTS = {
    "agency_name": "",
    "agency_url": "",
    "prepared_by_default": "",
    "palette_doc": {
        # document (docx/pdf/cover) palette, hex without '#'
        "ink": "1F2430", "cloud": "F4F5F7", "accent": "3B6EF6",
        "mistline": "E3E6EB", "steel": "5C6470", "mist": "9AA3B0",
        "cover_bg": "141821", "cover_slate": "2C3442", "white": "FFFFFF",
    },
    "palette_xlsx": {
        # workbook palette — keys consumed by ew_audit_style.C
        "obsidian": "141821", "carbon": "1B2029", "slate": "232A35",
        "coral": "3B6EF6", "violet": "6B7A99", "deep": "2B3B66",
        "mist": "9AA3B0", "cloud": "F4F5F7", "hairline": "E3E6EB",
        "white": "FFFFFF", "ink": "232A35",
    },
    "fonts": {
        "doc_font_name": "Inter", "doc_font_file": "Inter-Variable.ttf",
        "xlsx_font_display": "Aptos Display", "xlsx_font_body": "Aptos",
    },
    "assets": {
        "brand_dir": "",          # empty -> tools/amazon-ad-audit/brand/
        "logo_white": "logo_white.png",
        "mark": "mark_black.png",
    },
}

_CACHE: dict[str, dict] = {}


def _deep_merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        elif v not in (None, ""):
            out[k] = v
    return out


def _agent_example() -> Path:
    # Claude markers first: a Claude Code session may also carry CODEX_* vars
    # from the installed codex-companion plugin.
    if os.environ.get("CLAUDECODE") or any(k.startswith("CLAUDE_CODE") for k in os.environ):
        return HERE / "branding.EXAMPLE-claude.json"
    if any(k.startswith("CODEX") for k in os.environ):
        return HERE / "branding.EXAMPLE-codex.json"
    return HERE / "branding.EXAMPLE-claude.json"


def load_branding(cfg: dict | None = None) -> dict:
    cfg = cfg or {}
    bcfg = cfg.get("branding", {}) or {}
    path = Path(bcfg.get("branding_json") or (REPO / "_local" / "branding" / "branding.json"))
    key = str(path)
    if key in _CACHE:
        return _CACHE[key]
    if path.exists():
        data, src = json.loads(path.read_text(encoding="utf-8")), str(path)
    else:
        ex = _agent_example()
        if ex.exists():
            data, src = json.loads(ex.read_text(encoding="utf-8")), ex.name
        else:
            data, src = {}, "built-in defaults"
        print(f"[brand] no {path} — using {src}. "
              f"Copy tools/amazon-ad-audit/branding.TEMPLATE.json there for your own branding.")
    b = _deep_merge(_DEFAULTS, data)
    b["_source"] = src
    _CACHE[key] = b
    return b


# ---------------------------------------------------------------- derived strings
def prepared_by_line(b: dict, by: str) -> str:
    name = b.get("agency_name", "")
    return f"By {name} · {by}" if name else f"By {by}"


def cover_footer_left(b: dict) -> str:
    url = b.get("agency_url", "")
    return f"Confidential · {url}" if url else "Confidential"


def pdf_footer_right_prefix(b: dict) -> str:
    name = b.get("agency_name", "")
    return f"{name} · Confidential · p. " if name else "Confidential · p. "


def banner(b: dict, text: str) -> str:
    name = b.get("agency_name", "")
    return f"{name.upper()}  ·  {text}" if name else text


def prepared_by_org(b: dict) -> str:
    """The organisation named in 'Prepared by' workbook rows / scaffold bylines."""
    return b.get("agency_name") or "the operator"
