"""Company delivery forwarding with Amazon-owned artifact registration."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def take_option(args: list[str], name: str) -> tuple[list[str], str | None]:
    """Remove an exact long option, preserving all other arguments and `--`."""
    remaining, value = [], None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--":
            remaining.extend(args[index:])
            break
        if arg == name:
            index += 1
            if index >= len(args) or args[index].startswith("--"):
                raise ValueError(f"{name} requires a value")
            value = args[index]
        elif arg.startswith(name + "="):
            value = arg.split("=", 1)[1]
        else:
            remaining.append(arg)
        index += 1
    if value is not None and not value.strip():
        raise ValueError(f"{name} requires a nonempty value")
    return remaining, value


def company_script(name: str) -> Path:
    for candidate in (os.environ.get("EW_COMPANY_LIB", ""),
                      str(Path.home() / "os" / "company-ai-skills" / "lib")):
        if candidate:
            target = Path(candidate).expanduser() / "gdrive-deliver" / name
            if target.is_file():
                return target
    raise ValueError(f"gdrive-deliver/{name} is missing from company-ai-skills/lib "
                     "(checked $EW_COMPANY_LIB, then ~/os/company-ai-skills/lib). "
                     "Update or clone company-ai-skills, or set EW_COMPANY_LIB.")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def registration_args(name: str, args: list[str]):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("file", type=Path)
    parser.add_argument("destination")
    if name == "deliver.py":
        parser.add_argument("--name")
        parser.add_argument("--keep-local", action="store_true")
        parser.add_argument("--keep-upload", "--keep-docx", action="store_true")
    else:
        parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(args)


def publish_receipt(fresh: Path, destination: Path | None) -> None:
    if destination is None or not fresh.is_file():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Publish atomically without truncating the previous receipt on a failed read.
    with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".drive-receipt-",
                                     delete=False) as handle:
        pending = Path(handle.name)
        try:
            handle.write(fresh.read_bytes())
            handle.flush()
        except BaseException:
            pending.unlink(missing_ok=True)
            raise
    try:
        pending.replace(destination)
    finally:
        pending.unlink(missing_ok=True)


def verified_receipt(path: Path, source: Path, original_hash: str) -> dict:
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("delivery returned no new valid receipt; local file remains unregistered") from exc
    expected_mime = {".docx": "application/vnd.google-apps.document",
                     ".xlsx": "application/vnd.google-apps.spreadsheet"}.get(source.suffix.lower())
    if (not isinstance(receipt, dict) or receipt.get("provider") != "google-drive"
            or receipt.get("verified") is not True or not receipt.get("remote_id")
            or not isinstance(receipt.get("parents"), list) or not receipt["parents"]
            or expected_mime is None or receipt.get("mime_type") != expected_mime
            or receipt.get("local_sha256") != original_hash or sha256(source) != original_hash):
        raise ValueError("delivery receipt failed verification; local file remains unregistered")
    return receipt


def main(name: str, argv: list[str] | None = None) -> int:
    try:
        args, run_id = take_option(list(sys.argv[1:] if argv is None else argv), "--artifact-run")
        target = company_script(name)
        if run_id is None or "--help" in args or "-h" in args:
            os.execv(sys.executable, [sys.executable, str(target), *args])
            return 0
        helper_args, requested_receipt = take_option(args, "--receipt-file")
        parsed = registration_args(name, helper_args)
        if getattr(parsed, "dry_run", False):
            # Keep the helper's dry-run behavior, including not writing a receipt.
            return subprocess.run([sys.executable, str(target), *args], check=False).returncode
        source = parsed.file
        destination = Path(requested_receipt) if requested_receipt is not None else None
        if destination is not None and destination.resolve() == source.resolve():
            raise ValueError("receipt-file must differ from the delivered source")
        original_hash = sha256(source)
        with tempfile.TemporaryDirectory(prefix="gdrive-registration-") as scratch:
            fresh = Path(scratch) / "receipt.json"
            # Put the option before any positional `--` separator.
            command = [sys.executable, str(target), "--receipt-file", str(fresh), *helper_args]
            result = subprocess.run(command, check=False)
            publish_receipt(fresh, destination)
            if result.returncode:
                return result.returncode
            receipt = verified_receipt(fresh, source, original_hash)
            artifactctl = Path(__file__).resolve().parents[1] / "artifactctl" / "artifactctl.py"
            registered = subprocess.run(
                [sys.executable, str(artifactctl), "register", "--run", run_id,
                 "--path", str(source), "--disposition", "verify-drive",
                 "--receipt", json.dumps(receipt)], check=False,
            )
            if registered.returncode:
                print("[gdrive-deliver] Drive delivery verified, but artifact registration failed; "
                      "local file retained.", file=sys.stderr)
            else:
                print(f"[gdrive-deliver] retained and registered {source.name} for artifactctl")
            return registered.returncode
    except (OSError, ValueError) as exc:
        print(f"[gdrive-deliver] {exc}", file=sys.stderr)
        return 2
