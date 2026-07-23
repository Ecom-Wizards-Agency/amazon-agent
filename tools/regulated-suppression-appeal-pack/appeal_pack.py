#!/usr/bin/env python3
"""Scaffold and validate evidence-controlled Amazon suppression appeal packs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET


MODULES = (
    "01-appeal",
    "02-technical-evidence-and-claim-register",
    "03-manufacturer-declaration",
    "04-catalog-correction-and-processing-proof",
    "05-compliance-sop",
    "06-training-guide",
    "07-manual-review",
    "08-packaging-and-label-review",
    "09-evidence-index",
    "10-submission-checklist",
)

STATUSES = (
    "Draft",
    "Evidence incomplete",
    "Senior review ready",
    "Victor signoff required",
    "Approved for manual submission",
)

PLACEHOLDER_RE = re.compile(r"\[[A-Z][A-Z0-9 _./:-]{2,}\]|\{\{[^{}]+\}\}")
ASIN_RE = re.compile(r"^[A-Z0-9-]{5,32}$")
SKU_RE = re.compile(r"^.{1,80}$")

CORE_NS = {
    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
    "dc": "http://purl.org/dc/elements/1.1/",
}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
        }


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Missing JSON file: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return data


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from iter_strings(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from iter_strings(nested)


def validate_manifest(
    manifest: dict[str, Any], report: Report, *, completeness: bool = True
) -> None:
    required = {
        "client_slug",
        "case_slug",
        "case_date",
        "marketplace",
        "issue_type",
        "status",
        "affected_products",
        "claims",
        "consistency_checks",
        "catalog_correction",
        "victor_signoff",
        "modules",
    }
    missing = sorted(required - set(manifest))
    if missing:
        report.errors.append(f"Manifest is missing required fields: {', '.join(missing)}")
        return

    slug_re = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    for key in ("client_slug", "case_slug"):
        if not slug_re.fullmatch(str(manifest.get(key, ""))):
            report.errors.append(f"{key} must be lowercase kebab-case")

    if manifest.get("status") not in STATUSES:
        report.errors.append(f"Invalid pack status: {manifest.get('status')!r}")

    products = manifest.get("affected_products")
    if not isinstance(products, list) or not products:
        report.errors.append("affected_products must contain at least one product")
    else:
        seen_asins: set[str] = set()
        seen_skus: set[str] = set()
        for index, product in enumerate(products, 1):
            if not isinstance(product, dict):
                report.errors.append(f"affected_products[{index}] must be an object")
                continue
            asin = str(product.get("asin", "")).strip()
            if not ASIN_RE.fullmatch(asin):
                report.errors.append(f"affected_products[{index}] has an invalid ASIN/reference")
            if asin in seen_asins:
                report.errors.append(f"Duplicate ASIN/reference: {asin}")
            seen_asins.add(asin)
            skus = product.get("skus")
            if not isinstance(skus, list) or not skus:
                report.errors.append(f"affected_products[{index}] must contain at least one SKU")
                continue
            for sku in skus:
                sku = str(sku).strip()
                if not SKU_RE.fullmatch(sku):
                    report.errors.append(f"Invalid SKU under {asin}: {sku!r}")
                if sku in seen_skus:
                    report.errors.append(f"Duplicate SKU across affected products: {sku}")
                seen_skus.add(sku)

    claims = manifest.get("claims")
    if not isinstance(claims, list):
        report.errors.append("claims must be an array")
    else:
        claim_ids: set[str] = set()
        for index, claim in enumerate(claims, 1):
            if not isinstance(claim, dict):
                report.errors.append(f"claims[{index}] must be an object")
                continue
            claim_id = str(claim.get("id", "")).strip()
            if not claim_id:
                report.errors.append(f"claims[{index}] is missing id")
            elif claim_id in claim_ids:
                report.errors.append(f"Duplicate claim ID: {claim_id}")
            claim_ids.add(claim_id)
            if not str(claim.get("statement", "")).strip():
                report.errors.append(f"Claim {claim_id or index} is missing a statement")
            evidence = claim.get("evidence")
            if not isinstance(evidence, list):
                report.errors.append(f"Claim {claim_id or index} evidence must be an array")
            if completeness and claim.get("material") and not claim.get("verified"):
                report.errors.append(f"Material claim {claim_id or index} is not verified")
            if completeness and claim.get("material") and not evidence:
                report.errors.append(f"Material claim {claim_id or index} has no evidence")

    consistency_checks = manifest.get("consistency_checks")
    if not isinstance(consistency_checks, list):
        report.errors.append("consistency_checks must be an array")
    else:
        allowed_consistency = {"consistent", "conflict", "not_reviewed", "not_applicable"}
        for index, check in enumerate(consistency_checks, 1):
            if not isinstance(check, dict):
                report.errors.append(f"consistency_checks[{index}] must be an object")
                continue
            subject = str(check.get("subject", "")).strip()
            status = check.get("status")
            evidence = check.get("evidence")
            if not subject:
                report.errors.append(f"consistency_checks[{index}] is missing subject")
            if status not in allowed_consistency:
                report.errors.append(
                    f"consistency_checks[{index}] has invalid status: {status!r}"
                )
            if not isinstance(evidence, list):
                report.errors.append(
                    f"consistency_checks[{index}] evidence must be an array"
                )
            if completeness and status in {"conflict", "not_reviewed"}:
                report.errors.append(
                    f"Consistency check is unresolved for {subject or index}: {status}"
                )
            if completeness and status == "consistent" and not evidence:
                report.errors.append(
                    f"Consistency check has no evidence for {subject or index}"
                )

    modules = manifest.get("modules")
    if not isinstance(modules, dict):
        report.errors.append("modules must be an object")
    else:
        unknown = sorted(set(modules) - set(MODULES))
        if unknown:
            report.errors.append(f"Unknown modules: {', '.join(unknown)}")
        for module in MODULES:
            if module not in modules:
                report.errors.append(f"Manifest is missing module: {module}")
            elif not isinstance(modules[module], dict):
                report.errors.append(f"Module record must be an object: {module}")
        for core_module in {
            "01-appeal",
            "02-technical-evidence-and-claim-register",
            "09-evidence-index",
            "10-submission-checklist",
        }:
            if (
                core_module in modules
                and isinstance(modules[core_module], dict)
                and not modules[core_module].get("required")
            ):
                report.errors.append(f"Core module must be required: {core_module}")

    correction = manifest.get("catalog_correction")
    if not isinstance(correction, dict):
        report.errors.append("catalog_correction must be an object")
    else:
        correction_status = correction.get("status")
        allowed = {"not_required", "prepared", "uploaded", "processed", "verified"}
        if correction_status not in allowed:
            report.errors.append(f"Invalid catalog correction status: {correction_status!r}")
        submitted_skus = correction.get("submitted_skus")
        if not isinstance(submitted_skus, list):
            report.errors.append("catalog_correction.submitted_skus must be an array")
            submitted_skus = []
        affected_skus = {
            str(sku)
            for product in manifest.get("affected_products", [])
            if isinstance(product, dict)
            for sku in product.get("skus", [])
        }
        unrelated_skus = sorted(set(map(str, submitted_skus)) - affected_skus)
        if unrelated_skus:
            report.errors.append(
                "Catalog correction contains unrelated SKUs: " + ", ".join(unrelated_skus)
            )
        if correction_status != "not_required" and not submitted_skus:
            report.errors.append("Catalog correction requires at least one submitted SKU")
        if (
            completeness
            and correction_status in {"processed", "verified"}
            and not correction.get("processing_summary")
        ):
            report.errors.append("Processed catalog corrections require a processing summary")
        if (
            completeness
            and correction_status == "verified"
            and not correction.get("post_update_verification")
        ):
            report.errors.append("Verified catalog corrections require post-update verification")
        if (
            isinstance(modules, dict)
            and correction_status != "not_required"
            and not modules.get("04-catalog-correction-and-processing-proof", {}).get("required")
        ):
            report.errors.append(
                "Catalog correction module must be required when a correction is in scope"
            )

    signoff = manifest.get("victor_signoff")
    if not isinstance(signoff, dict) or "approved" not in signoff:
        report.errors.append("victor_signoff must contain approved")
    elif (
        completeness
        and manifest.get("status") == "Approved for manual submission"
        and not signoff.get("approved")
    ):
        report.errors.append("Approved for manual submission requires Victor's approval")


def resolve_pack_file(pack_dir: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else pack_dir / candidate


def scan_docx(path: Path, deny_terms: Iterable[str] = ()) -> Report:
    report = Report()
    if not path.exists():
        report.errors.append(f"Missing DOCX: {path}")
        return report
    if path.suffix.lower() != ".docx":
        report.errors.append(f"Not a DOCX file: {path}")
        return report

    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            xml_text: dict[str, str] = {}
            for name in names:
                if name.endswith((".xml", ".rels")):
                    xml_text[name] = archive.read(name).decode("utf-8", errors="ignore")
    except zipfile.BadZipFile:
        report.errors.append(f"Invalid DOCX package: {path}")
        return report

    if "docProps/custom.xml" in names:
        report.errors.append(f"{path.name}: custom document properties are present")
    comment_parts = sorted(name for name in names if name.startswith("word/comments"))
    if comment_parts:
        report.errors.append(f"{path.name}: comment parts are present")

    core = xml_text.get("docProps/core.xml")
    if core:
        try:
            root = ET.fromstring(core)
            creator = (root.findtext("dc:creator", default="", namespaces=CORE_NS) or "").strip()
            modifier = (root.findtext("cp:lastModifiedBy", default="", namespaces=CORE_NS) or "").strip()
            if creator or modifier:
                report.errors.append(
                    f"{path.name}: personal core metadata remains "
                    f"(creator={creator!r}, lastModifiedBy={modifier!r})"
                )
        except ET.ParseError:
            report.errors.append(f"{path.name}: core properties XML is invalid")

    tracked = False
    hidden = False
    external_targets: list[str] = []
    for name, text in xml_text.items():
        if name.startswith("word/") and name.endswith(".xml"):
            if re.search(r"<w:(?:ins|del|moveFrom|moveTo)(?:\s|>)", text):
                tracked = True
            if "<w:vanish" in text or "<w:webHidden" in text:
                hidden = True
        if name.endswith(".rels"):
            try:
                root = ET.fromstring(text)
            except ET.ParseError:
                report.errors.append(f"{path.name}: invalid relationships XML in {name}")
                continue
            for relation in root.findall("r:Relationship", REL_NS):
                if relation.attrib.get("TargetMode") == "External":
                    external_targets.append(relation.attrib.get("Target", ""))

    if tracked:
        report.errors.append(f"{path.name}: tracked changes remain")
    if hidden:
        report.errors.append(f"{path.name}: hidden text formatting remains")
    if external_targets:
        report.warnings.append(
            f"{path.name}: external relationships require review: {', '.join(sorted(set(external_targets)))}"
        )

    package_text = "\n".join(xml_text.values()).casefold()
    for term in sorted({term.strip() for term in deny_terms if term.strip()}):
        if term.casefold() in package_text:
            report.errors.append(f"{path.name}: denylisted term remains: {term}")

    media = sorted(name for name in names if name.startswith("word/media/"))
    embeddings = sorted(name for name in names if name.startswith("word/embeddings/"))
    if media:
        report.warnings.append(f"{path.name}: contains {len(media)} embedded media file(s); inspect visually")
    if embeddings:
        report.errors.append(f"{path.name}: contains embedded object(s)")

    report.info.append(f"Scanned {path.name}")
    return report


def merge_report(target: Report, source: Report) -> None:
    target.errors.extend(source.errors)
    target.warnings.extend(source.warnings)
    target.info.extend(source.info)


def scaffold(manifest_path: Path, output_root: Path) -> Path:
    manifest = load_json(manifest_path)
    report = Report()
    validate_manifest(manifest, report, completeness=False)
    if report.errors:
        raise ValueError("Cannot scaffold invalid manifest:\n- " + "\n- ".join(report.errors))

    pack_dir = (
        output_root
        / manifest["client_slug"]
        / "support-prep"
        / f"{manifest['case_date']}-{manifest['case_slug']}"
    )
    pack_dir.mkdir(parents=True, exist_ok=False)
    shutil.copy2(manifest_path, pack_dir / "00-case-manifest.json")
    for module in MODULES:
        (pack_dir / module).mkdir()
    (pack_dir / "evidence").mkdir()
    (pack_dir / "validation").mkdir()
    write_json(
        pack_dir / "validation" / "pack-status.json",
        {
            "status": manifest["status"],
            "validation": "not_run",
            "victor_signoff": manifest["victor_signoff"],
        },
    )
    return pack_dir


def validate_pack(pack_dir: Path, allow_template_placeholders: bool = False) -> Report:
    report = Report()
    manifest_path = pack_dir / "00-case-manifest.json"
    try:
        manifest = load_json(manifest_path)
    except ValueError as exc:
        report.errors.append(str(exc))
        return report

    validate_manifest(manifest, report)
    modules = manifest.get("modules", {})
    for module in MODULES:
        module_dir = pack_dir / module
        if not module_dir.is_dir():
            report.errors.append(f"Missing module directory: {module}")
            continue
        module_record = modules.get(module, {}) if isinstance(modules, dict) else {}
        if not isinstance(module_record, dict):
            continue
        files = module_record.get("files", [])
        required = bool(module_record.get("required"))
        if required and not files:
            report.errors.append(f"Required module has no declared files: {module}")
        for value in files if isinstance(files, list) else []:
            file_path = resolve_pack_file(pack_dir, value)
            if not file_path.exists():
                report.errors.append(f"Declared module file does not exist: {value}")
                continue
            if file_path.suffix.lower() == ".docx":
                merge_report(report, scan_docx(file_path))
            if not allow_template_placeholders and file_path.suffix.lower() in {
                ".docx",
                ".md",
                ".txt",
                ".csv",
            }:
                text = extract_searchable_text(file_path)
                matches = sorted(set(PLACEHOLDER_RE.findall(text)))
                if matches:
                    report.errors.append(
                        f"{value}: unresolved placeholders: {', '.join(matches[:8])}"
                    )

    for claim in manifest.get("claims", []) if isinstance(manifest.get("claims"), list) else []:
        for evidence in claim.get("evidence", []) if isinstance(claim, dict) else []:
            if not resolve_pack_file(pack_dir, str(evidence)).exists():
                report.errors.append(
                    f"Claim {claim.get('id', '?')} references missing evidence: {evidence}"
                )

    for check in (
        manifest.get("consistency_checks", [])
        if isinstance(manifest.get("consistency_checks"), list)
        else []
    ):
        if not isinstance(check, dict):
            continue
        for evidence in check.get("evidence", []):
            if not resolve_pack_file(pack_dir, str(evidence)).exists():
                report.errors.append(
                    f"Consistency check {check.get('subject', '?')} references missing evidence: "
                    f"{evidence}"
                )

    correction = manifest.get("catalog_correction", {})
    if isinstance(correction, dict):
        for key in ("processing_summary", "post_update_verification"):
            value = correction.get(key)
            if value and not resolve_pack_file(pack_dir, str(value)).exists():
                report.errors.append(
                    f"Catalog correction references missing {key.replace('_', ' ')}: {value}"
                )

    status = manifest.get("status")
    if status in {"Victor signoff required", "Approved for manual submission"} and report.errors:
        report.errors.append(f"Status {status!r} is not allowed while validation errors remain")

    report.info.append(f"Validated pack: {pack_dir}")
    return report


def extract_searchable_text(path: Path) -> str:
    if path.suffix.lower() != ".docx":
        return path.read_text(encoding="utf-8", errors="ignore")
    chunks: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            for name in archive.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    root = ET.fromstring(archive.read(name))
                    chunks.extend(node.text or "" for node in root.findall(".//w:t", WORD_NS))
    except (zipfile.BadZipFile, ET.ParseError):
        return ""
    return "\n".join(chunks)


def load_denylist(path: Path | None) -> list[str]:
    if path is None:
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def print_report(report: Report) -> None:
    print("PASS" if report.passed else "FAIL")
    for label, values in (
        ("ERROR", report.errors),
        ("WARNING", report.warnings),
        ("INFO", report.info),
    ):
        for value in values:
            print(f"{label}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    scaffold_parser = subparsers.add_parser("scaffold", help="Create a controlled case pack")
    scaffold_parser.add_argument("--manifest", type=Path, required=True)
    scaffold_parser.add_argument("--output-root", type=Path, default=Path("output"))

    validate_parser = subparsers.add_parser("validate", help="Validate a prepared case pack")
    validate_parser.add_argument("--pack-dir", type=Path, required=True)
    validate_parser.add_argument("--json", type=Path)
    validate_parser.add_argument("--allow-template-placeholders", action="store_true")

    scan_parser = subparsers.add_parser("scan-docx", help="Inspect DOCX privacy and package hygiene")
    scan_parser.add_argument("--input", type=Path, required=True)
    scan_parser.add_argument("--denylist", type=Path)
    scan_parser.add_argument("--json", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "scaffold":
            pack_dir = scaffold(args.manifest, args.output_root)
            print(pack_dir)
            return 0
        if args.command == "validate":
            report = validate_pack(args.pack_dir, args.allow_template_placeholders)
        else:
            report = scan_docx(args.input, load_denylist(args.denylist))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print_report(report)
    if args.json:
        write_json(args.json, report.as_dict())
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
