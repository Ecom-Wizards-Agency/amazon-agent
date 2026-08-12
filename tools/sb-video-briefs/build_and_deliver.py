#!/usr/bin/env python3
"""Build and deliver one SB video briefing plus its Creative Reference.

First delivery renders both Markdown sources as branded DOCX files and imports
them as native Google Docs. When canonical document ids already exist, the
command updates those Docs in place through the Google Docs API so their URLs,
comments and version history are not detached. Every run verifies Drive
metadata, content readback and a non-empty PDF export before it is complete.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RENDERER = ROOT / "tools" / "amazon-ad-audit" / "render_branded.py"
DELIVER = ROOT / "tools" / "gdrive-deliver" / "deliver.py"
LEGACY_KEYS = (
    ("client", "amazon_account"),
    ("economics", "break_even_acos"),
    ("economics", "break_even_source"),
    (None, "testing"),
)
FORBIDDEN_BRIEF = (
    "claims and compliance (advisory)",
    "how angle tests are measured",
    "break-even acos",
    "break even acos",
)
FORBIDDEN_REFERENCE = FORBIDDEN_BRIEF + ("stage 1", "stage 2")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def legacy_warnings(cfg: dict) -> list[str]:
    warnings = []
    for parent, key in LEGACY_KEYS:
        present = key in cfg if parent is None else key in (cfg.get(parent) or {})
        if present:
            dotted = key if parent is None else f"{parent}.{key}"
            warnings.append(f"legacy key ignored: {dotted}")
    return warnings


def require(cfg: dict, *path: str):
    cur = cfg
    for key in path:
        if not isinstance(cur, dict) or cur.get(key) in (None, "", []):
            raise ValueError(f"missing config value: {'.'.join(path)}")
        cur = cur[key]
    return cur


def validate_config(cfg: dict) -> None:
    for path in (
        ("client", "name"),
        ("client", "product_line"),
        ("client", "marketplace"),
        ("seller_central", "account_name"),
        ("seller_central", "expected_partner_account_id"),
        ("seller_central", "marketplace_label"),
        ("delivery", "drive_folder_id"),
        ("delivery", "brief_title"),
        ("delivery", "reference_title"),
    ):
        require(cfg, *path)


def validate_markdown(path: Path, kind: str) -> None:
    if not path.is_file():
        raise ValueError(f"missing {kind} Markdown: {path}")
    text = path.read_text(encoding="utf-8")
    lower = text.lower()
    forbidden = FORBIDDEN_BRIEF if kind == "brief" else FORBIDDEN_REFERENCE
    hits = [item for item in forbidden if item in lower]
    if hits:
        raise ValueError(f"{kind} contains forbidden editor-facing sections or terms: {', '.join(hits)}")
    if kind == "brief":
        for required in ("## Global rules", "### Specs (verbatim, non-negotiable)", "### Absolute do-not list", "### Part 2: shared second half"):
            if required not in text:
                raise ValueError(f"brief missing required section: {required}")
        angles = re.findall(r"^#### Angle [123]:", text, flags=re.MULTILINE)
        if len(angles) != 3:
            raise ValueError(f"brief must contain exactly three angle headings, found {len(angles)}")
    else:
        if "## 5. Footage inventory and asset requests" not in text:
            raise ValueError("reference must contain section 5: Footage inventory and asset requests")


def import_renderer():
    sys.path.insert(0, str(RENDERER.parent))
    spec = importlib.util.spec_from_file_location("sb_render_branded", RENDERER)
    if not spec or not spec.loader:
        raise RuntimeError("could not load branded renderer")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def renderer_config(cfg: dict, title: str) -> dict:
    client = cfg["client"]
    return {
        "client": client["name"],
        "marketplaces": [client["marketplace"]],
        "date": cfg.get("date", ""),
        "branding": {
            "doc_label": title,
            "prepared_by": "Ecom Wizards",
        },
    }


def render_pair(cfg: dict, brief_md: Path, reference_md: Path, outdir: Path) -> dict[str, Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "metrics.json").write_text('{"currency":"USD"}\n', encoding="utf-8")
    renderer = import_renderer()
    brief = renderer.render(renderer_config(cfg, cfg["delivery"]["brief_title"]), outdir, brief_md, cover=False)["docx"]
    reference = renderer.render(renderer_config(cfg, cfg["delivery"]["reference_title"]), outdir, reference_md, cover=False)["docx"]
    return {"brief": Path(brief), "reference": Path(reference)}


def deliver_one(docx: Path, folder_id: str, title: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(DELIVER), str(docx), folder_id, "--name", title],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"delivery failed for {title}\n{proc.stdout}\n{proc.stderr}".strip())
    match = re.search(r"\[deliver\] Google Doc: (\S+)", proc.stdout)
    if not match:
        raise RuntimeError(f"delivery returned no verified Google Doc URL for {title}\n{proc.stdout}")
    return {"title": title, "url": match.group(1), "delivery_output": proc.stdout.strip()}


def composio(slug: str, payload: dict) -> dict:
    """Run one connected Google action and resolve Composio's file spillover."""
    proc = subprocess.run(
        ["composio", "execute", slug, "-d", json.dumps(payload)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{slug} failed: {proc.stderr.strip() or proc.stdout.strip()[:800]}")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{slug} returned non-JSON output") from exc
    if result.get("storedInFile") and result.get("outputFilePath"):
        result = load_json(Path(result["outputFilePath"]))
    if result.get("successful") is False:
        raise RuntimeError(f"{slug} failed: {result.get('error') or 'unknown connector error'}")
    return result


def unwrap(result: dict) -> dict:
    for key in ("data", "response_data", "result"):
        inner = result.get(key)
        if isinstance(inner, dict):
            return unwrap(inner)
    return result


def first_tab_bounds(document: dict) -> tuple[str | None, int]:
    data = unwrap(document)
    tabs = data.get("tabs") or []
    if tabs:
        tab = tabs[0]
        props = tab.get("tabProperties") or tab.get("tab_properties") or {}
        document_tab = tab.get("documentTab") or tab.get("document_tab") or {}
        body = document_tab.get("body") or {}
        tab_id = props.get("tabId") or props.get("tab_id")
    else:
        body = data.get("body") or {}
        tab_id = None
    content = body.get("content") or []
    end_indexes = [item.get("endIndex") or item.get("end_index") for item in content]
    end_indexes = [value for value in end_indexes if isinstance(value, int)]
    if not end_indexes:
        raise RuntimeError("Google Docs read returned no body end index")
    return tab_id, max(end_indexes) - 1


def markdown_body(path: Path) -> str:
    """Drop the source H1 because the canonical Drive title and branded header own it."""
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\A# [^\n]+\n+", "", text, count=1).rstrip() + "\n"


def update_existing_document(document_id: str, markdown_path: Path) -> dict:
    structure = composio(
        "GOOGLEDOCS_GET_DOCUMENT_BY_ID",
        {"id": document_id, "includeTabsContent": True},
    )
    tab_id, end_index = first_tab_bounds(structure)
    payload = {
        "document_id": document_id,
        "start_index": 1,
        "end_index": end_index,
        "markdown_text": markdown_body(markdown_path),
    }
    if tab_id:
        payload["tab_id"] = tab_id
    composio("GOOGLEDOCS_UPDATE_DOCUMENT_SECTION_MARKDOWN", payload)
    return {"document_id": document_id, "url": f"https://docs.google.com/document/d/{document_id}/edit"}


def document_id_from_url(url: str) -> str:
    match = re.search(r"/document/d/([A-Za-z0-9_-]+)", url)
    if not match:
        raise RuntimeError(f"could not read Google Doc id from delivery URL: {url}")
    return match.group(1)


def find_download_url(value) -> str | None:
    if isinstance(value, dict):
        for key in ("s3url", "download_url", "downloadUrl"):
            candidate = value.get(key)
            if isinstance(candidate, str) and candidate.startswith("https://"):
                return candidate
        for child in value.values():
            found = find_download_url(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_download_url(child)
            if found:
                return found
    return None


def verify_document(document_id: str, title: str, folder_id: str, source_md: Path, pdf_path: Path) -> dict:
    meta = unwrap(composio("GOOGLEDRIVE_GET_FILE_METADATA", {
        "fileId": document_id,
        "fields": "id,name,mimeType,parents,webViewLink",
        "supportsAllDrives": True,
    }))
    if meta.get("name") != title:
        raise RuntimeError(f"Drive title mismatch for {document_id}: {meta.get('name')!r}")
    if meta.get("mimeType") != "application/vnd.google-apps.document":
        raise RuntimeError(f"{title} is not a native Google Doc")
    if folder_id not in (meta.get("parents") or []):
        raise RuntimeError(f"{title} is not in configured Drive folder {folder_id}")

    plain = composio("GOOGLEDOCS_GET_DOCUMENT_PLAINTEXT", {
        "document_id": document_id,
        "include_tables": True,
        "include_tabs_content": True,
    })
    expected = next(
        line.strip("# ") for line in source_md.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    )
    if expected not in json.dumps(plain, ensure_ascii=False):
        raise RuntimeError(f"content readback failed for {title}")

    exported = composio("GOOGLEDRIVE_DOWNLOAD_FILE", {
        "fileId": document_id,
        "mime_type": "application/pdf",
    })
    download_url = find_download_url(exported)
    if not download_url:
        raise RuntimeError(f"PDF export returned no downloadable file for {title}")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(download_url, timeout=60) as response:
        pdf_path.write_bytes(response.read())
    if pdf_path.stat().st_size < 1024 or not pdf_path.read_bytes().startswith(b"%PDF-"):
        raise RuntimeError(f"invalid PDF export for {title}")
    return {
        "document_id": document_id,
        "title": title,
        "url": meta.get("webViewLink") or f"https://docs.google.com/document/d/{document_id}/edit",
        "mime_type": meta.get("mimeType"),
        "parent_id": folder_id,
        "pdf_export": str(pdf_path),
        "pdf_bytes": pdf_path.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--brief-md", required=True, type=Path)
    parser.add_argument("--reference-md", required=True, type=Path)
    parser.add_argument("--outdir", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    cfg = load_json(args.config)
    for warning in legacy_warnings(cfg):
        print(f"[sb-video] MIGRATION WARNING: {warning}", file=sys.stderr)
    validate_config(cfg)
    validate_markdown(args.brief_md, "brief")
    validate_markdown(args.reference_md, "reference")

    if args.validate_only:
        print("[sb-video] config and editor-document validation passed")
        return 0

    existing = {
        "brief": (cfg.get("delivery") or {}).get("brief_document_id"),
        "reference": (cfg.get("delivery") or {}).get("reference_document_id"),
    }
    if any(existing.values()) and not all(existing.values()):
        raise SystemExit("[sb-video] both canonical document ids must be present together")

    outdir = args.outdir or Path((cfg.get("delivery") or {}).get("source_markdown_dir", "output")) / "_delivery"
    rendered = render_pair(cfg, args.brief_md, args.reference_md, outdir)
    folder_id = cfg["delivery"]["drive_folder_id"]
    documents = []
    try:
        if all(existing.values()):
            update_existing_document(existing["brief"], args.brief_md)
            update_existing_document(existing["reference"], args.reference_md)
            mode = "updated_in_place"
            ids = existing
        else:
            brief = deliver_one(rendered["brief"], folder_id, cfg["delivery"]["brief_title"])
            reference = deliver_one(rendered["reference"], folder_id, cfg["delivery"]["reference_title"])
            ids = {
                "brief": document_id_from_url(brief["url"]),
                "reference": document_id_from_url(reference["url"]),
            }
            mode = "created"
        documents.append(verify_document(
            ids["brief"], cfg["delivery"]["brief_title"], folder_id, args.brief_md,
            outdir / "qa" / "brief.pdf",
        ))
        documents.append(verify_document(
            ids["reference"], cfg["delivery"]["reference_title"], folder_id, args.reference_md,
            outdir / "qa" / "reference.pdf",
        ))
    except Exception:
        print(f"[sb-video] delivery failed. Intermediaries retained in {outdir}", file=sys.stderr)
        raise

    manifest = {
        "status": "delivered_verified",
        "mode": mode,
        "folder_id": folder_id,
        "documents": documents,
        "completed_qa": ["title", "destination folder", "native MIME type", "content readback", "PDF export"],
    }
    manifest_path = outdir / "delivery-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print(f"[sb-video] delivery and QA complete: {manifest_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
