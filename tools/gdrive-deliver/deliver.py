#!/usr/bin/env python3
"""Deliver a rendered file to Google Drive as a native Google Doc or Google Sheet.

A `.docx` in Drive cannot be commented on the way a Doc can, and "Open with Google Docs"
hands the reader a detached copy our edits never reach. The same is true of an `.xlsx` and
Sheets. Renderers keep producing Office files because python-docx and openpyxl are what carry
the branded layout, so those files are intermediates: converted on delivery, then deleted.

  .docx -> native Google Doc
  .xlsx -> native Google Sheet

Both go through the same Drive importer that `File > Save as Google Docs/Sheets` runs in the
browser. Verified 02.08.2026 on a full 18-page branded audit, an SB video briefing, a 17-tab
audit MASTER workbook and a 14-tab keyword workbook.

Two ways to get the file into Drive, picked from the destination argument:

  a folder path   ->  Drive for Desktop mount. Copies the bytes into the folder, reads the
                      Drive id off the mount, converts. No size limit, and the file lands in
                      the folder the operator can already see.
  a folder id     ->  no mount needed. Uploads through the API, then converts. Capped at 5 MB
                      by the upload tool, which covers every deliverable we render (the
                      largest so far is 0.7 MB), but not an arbitrary file.

The mount route is the one a machine with Drive for Desktop should use. The id route exists
because not everybody running this agent has the desktop client, or a shared drive.

Conversion needs an API call that can set a target mimeType. Neither the mount nor the Drive
MCP's `copy_file` offers one, so it goes through the Composio CLI, which holds the Google
auth. One-time setup on a machine: `python3 tools/gdrive-deliver/setup_google.py`. Without a
connection the mount route still stages the file and prints the browser steps, which leaves
the delivery degraded rather than broken.

Usage:
  python3 tools/gdrive-deliver/deliver.py <local file> <drive folder path or id> \\
      [--name "2026-08-02_Acme_US_Audit_v1"] [--keep-local] [--keep-upload]
"""
from __future__ import annotations
import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# What each rendered file type becomes, and what the browser fallback is called for it.
TARGETS = {
    ".docx": {
        "mime": "application/vnd.google-apps.document",
        "label": "Google Doc",
        "menu": "File > Save as Google Docs",
        "url": "https://docs.google.com/document/d/{id}/edit",
    },
    ".xlsx": {
        "mime": "application/vnd.google-apps.spreadsheet",
        "label": "Google Sheet",
        "menu": "File > Save as Google Sheets",
        "url": "https://docs.google.com/spreadsheets/d/{id}/edit",
    },
}
FOLDER_MIME = "application/vnd.google-apps.folder"
ITEM_ID_XATTR = "com.google.drivefs.item-id#S"
UPLOAD_LIMIT = 5 * 1024 * 1024  # GOOGLEDRIVE_UPLOAD_FILE's documented cap


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


def composio(slug: str, payload: dict, file: Path | None = None) -> dict:
    cmd = ["composio", "execute", slug, "-d", json.dumps(payload)]
    if file is not None:
        cmd += ["--file", str(file)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"[deliver] {slug} failed.\n{proc.stderr.strip() or proc.stdout.strip()}\n"
                         "If this says there is no connected account, run: "
                         "python3 tools/gdrive-deliver/setup_google.py")
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise SystemExit(f"[deliver] {slug} returned output that is not JSON:\n{proc.stdout[:800]}")
    # A tool that could not run still exits 0 and reports the failure in the payload. The
    # missing-connection case is the one an operator actually hits, so it gets said plainly:
    # on the mount route the file is already in the right folder, only the conversion did not
    # happen.
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


def parse_destination(dest: str) -> tuple[str, str | Path]:
    """Decide whether the destination is a mount folder or a Drive folder id.

    A path that exists locally is a mount folder. Anything else has to be an id, either bare
    or inside a Drive URL, because a folder path that does not exist is a typo we should
    catch here rather than halfway through a delivery.
    """
    path = Path(dest).expanduser()
    if path.is_dir():
        return "mount", path
    url = re.search(r"/folders/([A-Za-z0-9_-]{10,})", dest)
    if url:
        return "id", url.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", dest):
        return "id", dest
    raise SystemExit(f"[deliver] destination is neither an existing folder nor a Drive folder "
                     f"id: {dest}")


def convert(file_id: str, name: str, parent_id: str, target: dict) -> dict:
    """Copy a Drive file to a native Workspace type and verify what came back.

    Every Ecom Wizards client folder lives in a shared drive, and Drive v3 hides shared-drive
    items from calls that do not set supportsAllDrives. Composio sets it for us today, but it
    is passed explicitly so delivery does not depend on an undocumented default. It is a
    no-op for a My Drive destination, which is what somebody without a shared drive has.
    """
    copied = unwrap(composio("GOOGLEDRIVE_COPY_FILE_ADVANCED", {
        "fileId": file_id, "name": name, "mimeType": target["mime"], "parents": [parent_id],
        "supportsAllDrives": True,
    }))
    new_id = copied.get("id")
    if not new_id:
        raise SystemExit(f"[deliver] conversion returned no file id:\n{json.dumps(copied)[:800]}")

    meta = unwrap(composio("GOOGLEDRIVE_GET_FILE_METADATA",
                           {"fileId": new_id, "fields": "id,name,mimeType,webViewLink,parents",
                            "supportsAllDrives": True}))
    if meta.get("mimeType") != target["mime"]:
        raise SystemExit(f"[deliver] {name} came back as {meta.get('mimeType')}, not a "
                         f"{target['label']}. Nothing was deleted; inspect it in Drive.")
    return meta


def deliver_over_mount(src: Path, folder: Path, name: str, target: dict,
                       keep_upload: bool) -> dict | None:
    """Stage on the Drive mount, convert, bin the staged copy. None if nothing is linked."""
    # Whose Drive are we writing into, and who would we be acting as? Composio keeps its
    # connections server-side under the API key in ~/.composio, so a key copied between
    # machines would silently make everybody deliver as whoever linked Google first. Rather
    # than rely on people setting that up correctly, refuse to act as the wrong account.
    owner = mount_account(folder)
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
            f"[deliver] The file would be created and owned by the wrong person. Fix it with "
            f"`composio link googledrive` signed in as {owner}, or deliver through the browser, "
            f"which always uses the Google session you are actually signed into.")
    if scripted and acting_as:
        print(f"[deliver] acting as {acting_as}")

    # A folder created moments ago has no Drive id yet either, so poll it the same way
    # rather than reporting "not in a Drive mount" for a folder that plainly is.
    try:
        parent_id = wait_for_upload(folder, timeout=60)
    except SystemExit:
        raise SystemExit(f"[deliver] {folder} has no Drive id. Either it is not inside a synced "
                         "Google Drive mount, or Drive for Desktop is not running. Without the "
                         "desktop client, pass the destination as a Drive folder id instead.")

    staged = folder / src.name
    shutil.copy2(src, staged)
    print(f"[deliver] staged {staged.name} in {folder.name}")
    file_id = wait_for_upload(staged)
    print(f"[deliver] Drive id {file_id}")

    try:
        meta = convert(file_id, name, parent_id, target)
    except NoConnection:
        # No linked Google account on this machine. The file is already in the right folder,
        # so the conversion is the only missing step and a logged-in browser does it just as
        # well: same importer, same result. Hand the operator the exact steps rather than
        # making the delivery depend on a one-time CLI login.
        print(f"\n[deliver] No Google account linked to Composio on this machine, so the\n"
              f"conversion could not be scripted. {staged.name} is staged in the destination\n"
              f"folder and nothing was deleted. Finish it either way:\n\n"
              f"  In the browser (no setup, uses the session you are already signed into):\n"
              f"    1. open {target['url'].format(id=file_id)}\n"
              f"    2. {target['menu']}\n"
              f"    3. rename the new file to: {name}\n"
              f"    4. bin {staged.name} and delete {src}\n\n"
              f"  Or once, to script it from here on:\n"
              f"    python3 tools/gdrive-deliver/setup_google.py\n", file=sys.stderr)
        return None

    if not keep_upload:
        staged.unlink()
        print(f"[deliver] binned the uploaded {staged.name}")
    return meta


def deliver_over_api(src: Path, folder_id: str, name: str, target: dict,
                     keep_upload: bool) -> dict:
    """Upload through the API, convert, trash the uploaded original. No mount required."""
    size = src.stat().st_size
    if size > UPLOAD_LIMIT:
        raise SystemExit(
            f"[deliver] {src.name} is {size / 1048576:.1f} MB and the API upload caps at 5 MB. "
            "Deliver it through a Drive for Desktop mount instead, by passing the destination "
            "as a folder path.")

    # An invalid folder id makes the upload fall back to the Drive root silently, so check
    # the destination is a real folder before sending anything.
    parent = unwrap(composio("GOOGLEDRIVE_GET_FILE_METADATA",
                             {"fileId": folder_id, "fields": "id,name,mimeType",
                              "supportsAllDrives": True}))
    if parent.get("mimeType") != FOLDER_MIME:
        raise SystemExit(f"[deliver] {folder_id} is not a Drive folder "
                         f"(it is {parent.get('mimeType')}).")
    print(f"[deliver] acting as {linked_account()}, into folder {parent.get('name')}")

    uploaded = unwrap(composio("GOOGLEDRIVE_UPLOAD_FILE",
                               {"folder_to_upload_to": folder_id}, file=src))
    file_id = uploaded.get("id")
    if not file_id:
        raise SystemExit(f"[deliver] upload returned no file id:\n{json.dumps(uploaded)[:800]}")
    print(f"[deliver] uploaded {src.name}, Drive id {file_id}")

    meta = convert(file_id, name, folder_id, target)

    if not keep_upload:
        composio("GOOGLEDRIVE_TRASH_FILE", {"file_id": file_id})
        print(f"[deliver] binned the uploaded {src.name}")
    return meta


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Deliver a .docx or .xlsx to Drive as a native Google Doc or Sheet.")
    ap.add_argument("file", type=Path, help="local .docx or .xlsx to deliver")
    ap.add_argument("folder", help="destination: a folder inside the Google Drive mount, "
                                   "or a Drive folder id/URL when there is no mount")
    ap.add_argument("--name", help="name for the delivered file (default: the local stem)")
    ap.add_argument("--keep-local", action="store_true",
                    help="keep the local file after conversion")
    ap.add_argument("--keep-upload", "--keep-docx", dest="keep_upload", action="store_true",
                    help="keep the uploaded Office file in Drive too")
    a = ap.parse_args()

    target = TARGETS.get(a.file.suffix.lower())
    if not target:
        raise SystemExit(f"[deliver] {a.file.name} is not a {' or a '.join(TARGETS)}")
    if not a.file.is_file():
        raise SystemExit(f"[deliver] no such file: {a.file}")

    kind, dest = parse_destination(a.folder)
    name = a.name or a.file.stem

    if kind == "mount":
        meta = deliver_over_mount(a.file, dest, name, target, a.keep_upload)
        if meta is None:
            return 2
    else:
        meta = deliver_over_api(a.file, dest, name, target, a.keep_upload)

    print(f"[deliver] {target['label']}: {meta.get('webViewLink') or meta.get('id')}")

    # Only now, with a verified native file in the destination folder, is anything removed.
    if not a.keep_local:
        a.file.unlink()
        print(f"[deliver] deleted local {a.file.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
