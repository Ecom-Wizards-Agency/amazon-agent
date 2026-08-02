#!/usr/bin/env python3
"""Deliver a .docx to Google Drive as a native Google Doc.

The Drive desktop mount is the only sane way to move a multi-megabyte file into Drive
(the Drive MCP takes content inline as base64, so a 1 MB file costs roughly 1.5M tokens
and the call fails). A mount can only put bytes in a folder though: it cannot ask Drive
to convert anything. So this does both halves.

  1. copy the .docx onto the mount and wait for Drive to assign it a file id
  2. ask Drive to copy that file to mimeType application/vnd.google-apps.document,
     which runs the same importer as "File > Save as Google Docs" in the Docs UI
  3. verify the result really is a native Doc
  4. bin the uploaded .docx and delete the local one, unless told to keep them

Step 2 goes through the Composio CLI, which holds the Google auth. One-time setup on a
machine: `composio link googledrive`, signing in as the account that owns the shared drive.
Without that connection the script stops after step 1 and says so, which leaves the .docx
sitting in the right folder: degraded, not broken.

Usage:
  python3 tools/gdrive-deliver/deliver_doc.py <local.docx> <drive-folder-on-the-mount> \\
      [--name "2026-08-02_Acme_US_Audit_v1"] [--keep-local] [--keep-docx]

The folder argument is a path inside the Google Drive mount, the same path any other
workflow would copy into. The Doc is created in that folder and inherits its sharing.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

DOC_MIME = "application/vnd.google-apps.document"
ITEM_ID_XATTR = "com.google.drivefs.item-id#S"


class NoConnection(Exception):
    """Composio has no Google account linked on this machine."""


def mount_account(path: Path) -> str | None:
    """The Google account that owns the Drive mount `path` sits in.

    Drive for Desktop names its mount `GoogleDrive-<email>`, so the destination folder
    states whose Drive it is. That is what makes the identity check below possible without
    asking anybody to configure their own address anywhere.
    """
    for part in path.resolve().parts:
        if part.startswith("GoogleDrive-") and "@" in part:
            return part.split("GoogleDrive-", 1)[1]
    return None


def linked_account() -> str:
    """The Google account Composio is linked as on this machine. Raises NoConnection."""
    about = unwrap(composio("GOOGLEDRIVE_GET_ABOUT", {"fields": "user"}))
    return (about.get("user") or {}).get("emailAddress", "")


def drive_id(path: Path) -> str | None:
    """The Drive file/folder id the desktop client stamps on every synced item.

    Reading the id off the file beats searching Drive by name: it is exact, it costs
    nothing, and it tells us the upload finished. The attribute simply does not exist
    until Drive has taken the file.
    """
    try:
        out = subprocess.run(["xattr", "-p", ITEM_ID_XATTR, str(path)],
                             capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        return None
    return out.stdout.strip() or None


def wait_for_upload(path: Path, timeout: int = 180) -> str:
    deadline = time.time() + timeout
    while time.time() < deadline:
        fid = drive_id(path)
        if fid:
            return fid
        time.sleep(3)
    raise SystemExit(f"[deliver] Drive never picked up {path.name} within {timeout}s. "
                     "Check that Google Drive for Desktop is running and synced.")


def composio(slug: str, payload: dict) -> dict:
    proc = subprocess.run(["composio", "execute", slug, "-d", json.dumps(payload)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"[deliver] {slug} failed.\n{proc.stderr.strip() or proc.stdout.strip()}\n"
                         "If this says there is no connected account, run: composio link googledrive")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"[deliver] {slug} returned output that is not JSON:\n{proc.stdout[:800]}")
    # A tool that could not run still exits 0 and reports the failure in the payload. The
    # missing-connection case is the one an operator actually hits, so it gets said plainly:
    # the .docx is already staged in the right folder, only the conversion did not happen.
    if result.get("successful") is False:
        err = result.get("error") or json.dumps(result)[:400]
        if "connection" in str(err).lower():
            raise NoConnection(str(err))
        raise SystemExit(f"[deliver] {slug} failed: {err}")
    return result


def unwrap(result: dict) -> dict:
    """Composio wraps the API response; the shape has moved before, so accept both."""
    for key in ("data", "response_data", "result"):
        inner = result.get(key)
        if isinstance(inner, dict):
            return unwrap(inner) if any(k in inner for k in ("data", "response_data")) else inner
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Deliver a .docx to Drive as a native Google Doc.")
    ap.add_argument("docx", type=Path, help="local .docx to deliver")
    ap.add_argument("folder", type=Path, help="destination folder inside the Google Drive mount")
    ap.add_argument("--name", help="name for the Google Doc (default: the .docx stem)")
    ap.add_argument("--keep-local", action="store_true", help="keep the local .docx after conversion")
    ap.add_argument("--keep-docx", action="store_true", help="keep the uploaded .docx in Drive too")
    a = ap.parse_args()

    if a.docx.suffix.lower() != ".docx":
        raise SystemExit(f"[deliver] {a.docx.name} is not a .docx")
    if not a.docx.is_file():
        raise SystemExit(f"[deliver] no such file: {a.docx}")
    if not a.folder.is_dir():
        raise SystemExit(f"[deliver] destination folder does not exist: {a.folder}")

    # Whose Drive are we writing into, and who would we be acting as? Composio keeps its
    # connections server-side under the API key in ~/.composio, so a key copied between
    # machines would silently make everybody deliver as whoever linked Google first. Rather
    # than rely on people setting that up correctly, refuse to act as the wrong account.
    owner = mount_account(a.folder)
    scripted = True
    try:
        acting_as = linked_account()
    except NoConnection:
        scripted = False
        acting_as = ""
    if scripted and owner and acting_as and owner.lower() != acting_as.lower():
        raise SystemExit(
            f"[deliver] Refusing to deliver. This folder is in {owner}'s Drive, but Composio on "
            f"this machine is linked as {acting_as}.\n"
            f"[deliver] The Doc would be created and owned by the wrong person. Fix it with "
            f"`composio link googledrive` signed in as {owner}, or deliver through the browser, "
            f"which always uses the Google session you are actually signed into.")
    if scripted and acting_as:
        print(f"[deliver] acting as {acting_as}")

    # A folder created moments ago has no Drive id yet either, so poll it the same way
    # rather than reporting "not in a Drive mount" for a folder that plainly is.
    try:
        parent_id = wait_for_upload(a.folder, timeout=60)
    except SystemExit:
        raise SystemExit(f"[deliver] {a.folder} has no Drive id. Either it is not inside a synced "
                         "Google Drive mount, or Drive for Desktop is not running.")

    staged = a.folder / a.docx.name
    shutil.copy2(a.docx, staged)
    print(f"[deliver] staged {staged.name} in {a.folder.name}")
    file_id = wait_for_upload(staged)
    print(f"[deliver] Drive id {file_id}")

    name = a.name or a.docx.stem
    try:
        copied = unwrap(composio("GOOGLEDRIVE_COPY_FILE_ADVANCED", {
            "fileId": file_id, "name": name, "mimeType": DOC_MIME, "parents": [parent_id],
        }))
    except NoConnection:
        # No linked Google account on this machine. The file is already in the right folder,
        # so the conversion is the only missing step and a logged-in browser does it just as
        # well: same importer, same result. Hand the operator the exact steps rather than
        # making the delivery depend on a one-time CLI login.
        print(f"\n[deliver] No Google account linked to Composio on this machine, so the\n"
              f"conversion could not be scripted. {staged.name} is staged in the destination\n"
              f"folder and nothing was deleted. Finish it either way:\n\n"
              f"  In the browser (no setup, uses the session you are already signed into):\n"
              f"    1. open https://docs.google.com/document/d/{file_id}/edit\n"
              f"    2. File > Save as Google Docs\n"
              f"    3. rename the new Doc to: {name}\n"
              f"    4. bin {staged.name} and delete {a.docx}\n\n"
              f"  Or once, to script it from here on:  composio link googledrive\n",
              file=sys.stderr)
        return 2
    doc_id = copied.get("id")
    if not doc_id:
        raise SystemExit(f"[deliver] conversion returned no file id:\n{json.dumps(copied)[:800]}")

    meta = unwrap(composio("GOOGLEDRIVE_GET_FILE_METADATA",
                           {"fileId": doc_id, "fields": "id,name,mimeType,webViewLink,parents"}))
    if meta.get("mimeType") != DOC_MIME:
        raise SystemExit(f"[deliver] {name} came back as {meta.get('mimeType')}, not a Google Doc. "
                         "Nothing was deleted; inspect it in Drive.")
    print(f"[deliver] Google Doc: {meta.get('webViewLink') or doc_id}")

    # Only now, with a verified native Doc in the same folder, is anything removed.
    if not a.keep_docx:
        staged.unlink()
        print(f"[deliver] binned the uploaded {staged.name}")
    if not a.keep_local:
        a.docx.unlink()
        print(f"[deliver] deleted local {a.docx.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
