#!/usr/bin/env python3
"""Exact-file lifecycle registry for Amazon Agent local artifacts.

The registry never discovers cleanup candidates by filename or age. A workflow
must register a regular file under a run, and only successfully completed runs
can become eligible for quarantine. Remote data is never deleted here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import stat
import subprocess
import sys
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit


DISPOSITIONS = {
    "source-backed",
    "archive-pcloud",
    "verify-drive",
    "reproducible",
    "preserve",
}
RUN_OUTCOMES = {"success", "failed", "blocked"}
ELIGIBILITY_DAYS = 7
QUARANTINE_DAYS = 30
FLATFILEPRO_ORIGIN = "https://app.flatfile.pro"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | None) -> str | None:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if value else None


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def sha(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_origin(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    port = f":{parsed.port}" if parsed.port else ""
    return f"https://{parsed.hostname.lower()}{port}"


def json_value(value: str | None) -> dict | None:
    if not value:
        return None
    candidate = Path(value).expanduser()
    raw = candidate.read_text(encoding="utf-8") if candidate.is_file() else value
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        raise ValueError("receipt/archive JSON must be an object")
    return loaded


def file_fingerprint(path: Path) -> dict:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise ValueError(f"not an exact regular file: {path}")
    return {
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "sha256": sha(path),
    }


def default_runtime_root() -> Path:
    return Path(os.environ.get(
        "AMAZON_ARTIFACT_RUNTIME_DIR",
        Path.home() / ".amazon-agent" / "artifact-runtime",
    )).expanduser().resolve()


def default_allowed_roots() -> list[Path]:
    configured = os.environ.get("AMAZON_ARTIFACT_ALLOWED_ROOTS")
    if configured:
        return [Path(item).expanduser().resolve() for item in configured.split(os.pathsep) if item]
    repo = Path(__file__).resolve().parents[2]
    return [
        (repo / name).resolve()
        for name in ("downloads", "output", "evidence", "_local-output", ".codex-tmp")
    ] + [(Path.home() / "Downloads").resolve()]


def path_within(path: Path, roots: list[Path]) -> bool:
    for root in roots:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            continue
    return False


class ArtifactRegistry:
    def __init__(
        self,
        runtime_root: Path | None = None,
        allowed_roots: list[Path] | None = None,
        clock: Callable[[], datetime] = utc_now,
        archive_runner: Callable[[list[Path], dict], dict] | None = None,
    ):
        self.root = (runtime_root or default_runtime_root()).resolve()
        self.db_path = self.root / "registry.sqlite3"
        self.quarantine_root = self.root / "quarantine"
        self.allowed_roots = [item.resolve() for item in (allowed_roots or default_allowed_roots())]
        self.clock = clock
        self.archive_runner = archive_runner or self._archive_pcloud
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.quarantine_root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        con.execute("PRAGMA busy_timeout=30000")
        return con

    def _init_db(self) -> None:
        with self.connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                  id TEXT PRIMARY KEY,
                  owner TEXT NOT NULL,
                  client TEXT,
                  workflow TEXT NOT NULL,
                  state TEXT NOT NULL,
                  started_at TEXT NOT NULL,
                  completed_at TEXT,
                  eligible_at TEXT,
                  outcome TEXT
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                  id TEXT PRIMARY KEY,
                  run_id TEXT NOT NULL REFERENCES runs(id),
                  owner TEXT NOT NULL,
                  client TEXT,
                  workflow TEXT NOT NULL,
                  path TEXT NOT NULL,
                  source_origin TEXT,
                  disposition TEXT NOT NULL,
                  state TEXT NOT NULL,
                  registered_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL,
                  size INTEGER NOT NULL,
                  mtime_ns INTEGER NOT NULL,
                  sha256 TEXT NOT NULL,
                  receipt_json TEXT,
                  archive_json TEXT,
                  eligible_at TEXT,
                  quarantine_path TEXT,
                  quarantine_size INTEGER,
                  quarantine_mtime_ns INTEGER,
                  quarantined_at TEXT,
                  purge_at TEXT,
                  review_reason TEXT,
                  claim_at TEXT,
                  UNIQUE(run_id, path)
                );
                CREATE TABLE IF NOT EXISTS journal (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  at TEXT NOT NULL,
                  action TEXT NOT NULL,
                  artifact_id TEXT,
                  detail TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_artifacts_cleanup
                  ON artifacts(state, eligible_at, purge_at);
                """
            )
        if os.name != "nt":
            os.chmod(self.db_path, 0o600)

    def _journal(self, con: sqlite3.Connection, action: str, artifact_id: str | None, detail: str) -> None:
        con.execute(
            "INSERT INTO journal(at, action, artifact_id, detail) VALUES(?,?,?,?)",
            (iso(self.clock()), action, artifact_id, detail),
        )

    def start_run(self, owner: str, workflow: str, client: str | None = None, run_id: str | None = None) -> dict:
        now = iso(self.clock())
        run_id = run_id or f"run_{uuid.uuid4().hex}"
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO runs(id,owner,client,workflow,state,started_at) VALUES(?,?,?,?,?,?)",
                (run_id, owner, client, workflow, "active", now),
            )
            con.commit()
        return self.get_run(run_id)

    def get_run(self, run_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                raise ValueError(f"unknown run: {run_id}")
            artifacts = [dict(item) for item in con.execute(
                "SELECT * FROM artifacts WHERE run_id=? ORDER BY registered_at,path", (run_id,)
            )]
        out = dict(row)
        out["artifacts"] = [self._public_artifact(item) for item in artifacts]
        return out

    def complete_run(self, run_id: str, outcome: str) -> dict:
        if outcome not in RUN_OUTCOMES:
            raise ValueError(f"unsupported run outcome: {outcome}")
        now = self.clock()
        eligible = now + timedelta(days=ELIGIBILITY_DAYS) if outcome == "success" else None
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            run = con.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not run:
                raise ValueError(f"unknown run: {run_id}")
            if run["state"] != "active":
                if run["outcome"] == outcome:
                    con.rollback()
                    return self.get_run(run_id)
                raise ValueError(f"run is already complete: {run_id}")
            con.execute(
                "UPDATE runs SET state='complete',completed_at=?,eligible_at=?,outcome=? WHERE id=?",
                (iso(now), iso(eligible), outcome, run_id),
            )
            if outcome == "success":
                con.execute(
                    """UPDATE artifacts
                       SET state=CASE WHEN disposition='preserve' OR state='review' THEN state ELSE 'eligible-pending' END,
                           eligible_at=CASE WHEN disposition='preserve' OR state='review' THEN eligible_at ELSE ? END,
                           updated_at=? WHERE run_id=?""",
                    (iso(eligible), iso(now), run_id),
                )
            else:
                con.execute(
                    "UPDATE artifacts SET state='preserved',review_reason=?,updated_at=? WHERE run_id=?",
                    (f"run-{outcome}", iso(now), run_id),
                )
            con.commit()
        return self.get_run(run_id)

    def register(
        self,
        run_id: str,
        path: Path,
        disposition: str,
        source_origin: str | None = None,
        receipt: dict | None = None,
        archive: dict | None = None,
    ) -> dict:
        if disposition not in DISPOSITIONS:
            raise ValueError(f"unsupported disposition: {disposition}")
        exact = path.expanduser().resolve(strict=True)
        fingerprint = file_fingerprint(exact)
        origin = exact_origin(source_origin)
        now = iso(self.clock())
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            run = con.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not run:
                raise ValueError(f"unknown run: {run_id}")
            if run["state"] != "active":
                raise ValueError(f"run is not active: {run_id}")
            in_scope = path_within(exact, self.allowed_roots)
            review_reason = None
            state = "registered"
            if disposition == "preserve":
                state = "preserved"
            elif not in_scope:
                state = "review"
                review_reason = "path-outside-allowed-roots"
            elif disposition == "source-backed" and origin != FLATFILEPRO_ORIGIN:
                state = "review"
                review_reason = "source-origin-not-allowlisted"
            artifact_id = f"art_{uuid.uuid4().hex}"
            previous = con.execute(
                "SELECT id,size,mtime_ns,sha256 FROM artifacts WHERE run_id=? AND path=?",
                (run_id, str(exact)),
            ).fetchone()
            if previous:
                if (previous["size"], previous["mtime_ns"], previous["sha256"]) != (
                    fingerprint["size"], fingerprint["mtime_ns"], fingerprint["sha256"]
                ):
                    raise ValueError("registered file changed; start a new run or preserve it for review")
                artifact_id = previous["id"]
                con.execute(
                    """UPDATE artifacts SET disposition=?,source_origin=?,state=?,updated_at=?,
                       receipt_json=COALESCE(?,receipt_json),archive_json=COALESCE(?,archive_json),
                       review_reason=? WHERE id=?""",
                    (
                        disposition, origin, state, now,
                        json.dumps(receipt, sort_keys=True) if receipt else None,
                        json.dumps(archive, sort_keys=True) if archive else None,
                        review_reason, artifact_id,
                    ),
                )
            else:
                con.execute(
                    """INSERT INTO artifacts(
                       id,run_id,owner,client,workflow,path,source_origin,disposition,state,
                       registered_at,updated_at,size,mtime_ns,sha256,receipt_json,archive_json,review_reason
                       ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        artifact_id, run_id, run["owner"], run["client"], run["workflow"],
                        str(exact), origin, disposition, state, now, now,
                        fingerprint["size"], fingerprint["mtime_ns"], fingerprint["sha256"],
                        json.dumps(receipt, sort_keys=True) if receipt else None,
                        json.dumps(archive, sort_keys=True) if archive else None,
                        review_reason,
                    ),
                )
            self._journal(con, "registered", artifact_id, disposition)
            con.commit()
        return self.get_artifact(artifact_id)

    def get_artifact(self, artifact_id: str) -> dict:
        with self.connect() as con:
            row = con.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
        if not row:
            raise ValueError(f"unknown artifact: {artifact_id}")
        return self._public_artifact(dict(row))

    @staticmethod
    def _public_artifact(row: dict) -> dict:
        for key in ("receipt_json", "archive_json"):
            row[key.removesuffix("_json")] = json.loads(row.pop(key)) if row.get(key) else None
        return row

    def _fingerprint_matches(self, path: Path, row: sqlite3.Row, quarantine: bool = False) -> tuple[bool, str]:
        try:
            current = file_fingerprint(path)
        except (FileNotFoundError, ValueError, OSError) as exc:
            return False, f"file-unavailable:{type(exc).__name__}"
        size_key = "quarantine_size" if quarantine else "size"
        mtime_key = "quarantine_mtime_ns" if quarantine else "mtime_ns"
        expected_size = row[size_key] if row[size_key] is not None else row["size"]
        expected_mtime = row[mtime_key] if row[mtime_key] is not None else row["mtime_ns"]
        if current["size"] != expected_size:
            return False, "size-changed"
        if current["mtime_ns"] != expected_mtime:
            return False, "mtime-changed"
        if current["sha256"] != row["sha256"]:
            return False, "hash-changed"
        return True, "verified"

    @staticmethod
    def _drive_receipt_valid(row: sqlite3.Row) -> bool:
        try:
            receipt = json.loads(row["receipt_json"] or "{}")
        except json.JSONDecodeError:
            return False
        return bool(
            receipt.get("provider") == "google-drive"
            and receipt.get("verified") is True
            and receipt.get("remote_id")
            and receipt.get("parents")
            and receipt.get("mime_type") in {
                "application/vnd.google-apps.document",
                "application/vnd.google-apps.spreadsheet",
            }
            and receipt.get("local_sha256") == row["sha256"]
        )

    @staticmethod
    def _source_receipt_valid(row: sqlite3.Row) -> bool:
        return row["source_origin"] == FLATFILEPRO_ORIGIN

    @staticmethod
    def _pcloud_receipt_valid(row: sqlite3.Row) -> bool:
        try:
            receipt = json.loads(row["receipt_json"] or "{}")
        except json.JSONDecodeError:
            return False
        items = receipt.get("files") if isinstance(receipt, dict) else None
        if receipt.get("provider") != "pcloud" or receipt.get("verified") is not True or not isinstance(items, list):
            return False
        source = str(Path(row["path"]).resolve())
        return any(
            item.get("source") == source and item.get("sha256") == row["sha256"]
            and item.get("sha1") and item.get("remote_path")
            for item in items if isinstance(item, dict)
        )

    def _archive_pcloud(self, paths: list[Path], archive: dict) -> dict:
        helper = Path(os.environ.get(
            "AMAZON_ARTIFACT_PCLOUD_HELPER",
            Path.home() / "os" / "company-ai-skills" / "skills" / "pcloud-api" / "scripts" / "archive-raw.py",
        )).expanduser()
        required = ("client", "dataset", "market", "month", "report_type", "scope")
        missing = [key for key in required if not archive.get(key)]
        if missing:
            raise ValueError("pCloud archive metadata missing: " + ", ".join(missing))
        command = [
            sys.executable, str(helper), *[str(path) for path in paths],
            "--client", str(archive["client"]),
            "--dataset", str(archive["dataset"]),
            "--market", str(archive["market"]),
            "--month", str(archive["month"]),
            "--report-type", str(archive["report_type"]),
            "--scope", str(archive["scope"]),
            "--keep-local", "--json",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=1800)
        if result.returncode != 0:
            raise RuntimeError((result.stderr or result.stdout or "pCloud archive failed").strip())
        receipt = json.loads(result.stdout)
        if receipt.get("provider") != "pcloud" or receipt.get("verified") is not True:
            raise RuntimeError("pCloud helper returned an unverified receipt")
        return receipt

    def _recover_interrupted(self, con: sqlite3.Connection) -> None:
        now = iso(self.clock())
        for row in con.execute("SELECT * FROM artifacts WHERE state IN ('archiving','processing','purging','restoring')"):
            original = Path(row["path"])
            quarantine = Path(row["quarantine_path"]) if row["quarantine_path"] else None
            if row["state"] == "processing" and quarantine and quarantine.is_file() and not original.exists():
                ok, reason = self._fingerprint_matches(quarantine, row, quarantine=True)
                if ok:
                    con.execute("UPDATE artifacts SET state='quarantined',claim_at=NULL,updated_at=? WHERE id=?", (now, row["id"]))
                    self._journal(con, "recovered-quarantine", row["id"], "verified")
                else:
                    con.execute("UPDATE artifacts SET state='review',review_reason=?,claim_at=NULL,updated_at=? WHERE id=?", (reason, now, row["id"]))
            elif row["state"] == "purging" and quarantine and not quarantine.exists():
                con.execute("UPDATE artifacts SET state='purged',claim_at=NULL,updated_at=? WHERE id=?", (now, row["id"]))
                self._journal(con, "recovered-purge", row["id"], "exact-file-missing-after-claim")
            elif row["state"] == "restoring" and original.is_file() and (not quarantine or not quarantine.exists()):
                ok, reason = self._fingerprint_matches(original, row)
                if ok:
                    con.execute(
                        """UPDATE artifacts SET state='preserved',review_reason='restored-by-operator',
                           quarantine_path=NULL,quarantined_at=NULL,purge_at=NULL,claim_at=NULL,updated_at=? WHERE id=?""",
                        (now, row["id"]),
                    )
                    self._journal(con, "recovered-restore", row["id"], "verified")
                else:
                    con.execute("UPDATE artifacts SET state='review',review_reason=?,claim_at=NULL,updated_at=? WHERE id=?", (reason, now, row["id"]))
            else:
                claimed = parse_time(row["claim_at"])
                if claimed and self.clock() - claimed > timedelta(hours=1):
                    fallback = "quarantined" if row["state"] in {"purging", "restoring"} else "eligible-pending"
                    con.execute("UPDATE artifacts SET state=?,claim_at=NULL,updated_at=? WHERE id=?", (fallback, now, row["id"]))

    def _quarantine_one(self, artifact_id: str) -> dict:
        now = self.clock()
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            if not row or row["state"] != "eligible-pending":
                con.rollback()
                return {"artifact_id": artifact_id, "action": "preserved", "reason": "claim-lost"}
            original = Path(row["path"])
            ok, reason = self._fingerprint_matches(original, row)
            if not ok:
                con.execute("UPDATE artifacts SET state='review',review_reason=?,updated_at=? WHERE id=?", (reason, iso(now), artifact_id))
                self._journal(con, "review", artifact_id, reason)
                con.commit()
                return {"artifact_id": artifact_id, "path": str(original), "action": "preserved", "reason": reason}
            target = self.quarantine_root / artifact_id / original.name
            con.execute(
                "UPDATE artifacts SET state='processing',quarantine_path=?,claim_at=?,updated_at=? WHERE id=? AND state='eligible-pending'",
                (str(target), iso(now), iso(now), artifact_id),
            )
            if con.total_changes != 1:
                con.rollback()
                return {"artifact_id": artifact_id, "action": "preserved", "reason": "claim-lost"}
            con.commit()
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if target.exists():
            with self.connect() as con:
                con.execute("UPDATE artifacts SET state='review',review_reason='quarantine-target-exists',claim_at=NULL,updated_at=? WHERE id=?", (iso(now), artifact_id))
            return {"artifact_id": artifact_id, "path": str(original), "action": "preserved", "reason": "quarantine-target-exists"}
        os.replace(original, target)
        qfingerprint = file_fingerprint(target)
        purge_at = now + timedelta(days=QUARANTINE_DAYS)
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                """UPDATE artifacts SET state='quarantined',quarantine_size=?,quarantine_mtime_ns=?,
                   quarantined_at=?,purge_at=?,claim_at=NULL,updated_at=? WHERE id=? AND state='processing'""",
                (qfingerprint["size"], qfingerprint["mtime_ns"], iso(now), iso(purge_at), iso(now), artifact_id),
            )
            self._journal(con, "quarantined", artifact_id, str(target))
            con.commit()
        self._remove_empty_workdirs(original.parent)
        return {
            "artifact_id": artifact_id, "path": str(original), "action": "quarantined",
            "quarantine_path": str(target), "purge_at": iso(purge_at),
        }

    def _remove_empty_workdirs(self, directory: Path) -> None:
        current = directory
        while current != current.parent and path_within(current, self.allowed_roots):
            try:
                current.rmdir()
            except OSError:
                return
            current = current.parent

    def _purge_one(self, artifact_id: str) -> dict:
        now = self.clock()
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            if not row or row["state"] != "quarantined":
                con.rollback()
                return {"artifact_id": artifact_id, "action": "preserved", "reason": "claim-lost"}
            target = Path(row["quarantine_path"])
            ok, reason = self._fingerprint_matches(target, row, quarantine=True)
            if not ok:
                con.execute("UPDATE artifacts SET state='review',review_reason=?,updated_at=? WHERE id=?", (reason, iso(now), artifact_id))
                self._journal(con, "review", artifact_id, reason)
                con.commit()
                return {"artifact_id": artifact_id, "path": str(target), "action": "preserved", "reason": reason}
            con.execute("UPDATE artifacts SET state='purging',claim_at=?,updated_at=? WHERE id=? AND state='quarantined'", (iso(now), iso(now), artifact_id))
            if con.total_changes != 1:
                con.rollback()
                return {"artifact_id": artifact_id, "action": "preserved", "reason": "claim-lost"}
            con.commit()
        target.unlink()
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute("UPDATE artifacts SET state='purged',claim_at=NULL,updated_at=? WHERE id=? AND state='purging'", (iso(now), artifact_id))
            self._journal(con, "purged", artifact_id, "exact-file")
            con.commit()
        try:
            target.parent.rmdir()
        except OSError:
            pass
        return {"artifact_id": artifact_id, "path": str(target), "action": "purged"}

    def cleanup(self, audit_only: bool = False) -> dict:
        now = self.clock()
        actions: list[dict] = []
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            if not audit_only:
                self._recover_interrupted(con)
            eligible = list(con.execute(
                """SELECT * FROM artifacts WHERE state='eligible-pending'
                   AND eligible_at IS NOT NULL AND eligible_at<=? ORDER BY run_id,path""",
                (iso(now),),
            ))
            purgeable = list(con.execute(
                "SELECT * FROM artifacts WHERE state='quarantined' AND purge_at IS NOT NULL AND purge_at<=? ORDER BY purge_at",
                (iso(now),),
            ))
            con.commit()

        archive_groups: dict[tuple[str, str], list[sqlite3.Row]] = defaultdict(list)
        normal: list[sqlite3.Row] = []
        for row in eligible:
            if row["disposition"] == "archive-pcloud" and not self._pcloud_receipt_valid(row):
                archive_groups[(row["run_id"], row["archive_json"] or "")].append(row)
            else:
                normal.append(row)

        for (_, archive_raw), rows in archive_groups.items():
            paths = [Path(row["path"]) for row in rows]
            failures = []
            for row, path in zip(rows, paths):
                ok, reason = self._fingerprint_matches(path, row)
                if not ok:
                    failures.append({"artifact_id": row["id"], "path": str(path), "reason": reason})
            try:
                archive = json.loads(archive_raw) if archive_raw else None
            except json.JSONDecodeError:
                archive = None
            if failures or not archive:
                for row in rows:
                    reason = next((item["reason"] for item in failures if item["artifact_id"] == row["id"]), "pcloud-archive-metadata-missing")
                    actions.append({"artifact_id": row["id"], "path": row["path"], "action": "preserved", "reason": reason})
                    if not audit_only:
                        with self.connect() as con:
                            con.execute("UPDATE artifacts SET state='review',review_reason=?,updated_at=? WHERE id=?", (reason, iso(now), row["id"]))
                continue
            if audit_only:
                for row in rows:
                    actions.append({"artifact_id": row["id"], "path": row["path"], "action": "would-archive-and-quarantine"})
                continue
            claimed = False
            with self.connect() as con:
                con.execute("BEGIN IMMEDIATE")
                for row in rows:
                    current = con.execute("SELECT state FROM artifacts WHERE id=?", (row["id"],)).fetchone()
                    if not current or current["state"] != "eligible-pending":
                        break
                else:
                    for row in rows:
                        con.execute(
                            "UPDATE artifacts SET state='archiving',claim_at=?,updated_at=? WHERE id=?",
                            (iso(now), iso(now), row["id"]),
                        )
                    claimed = True
                if claimed:
                    con.commit()
                else:
                    con.rollback()
            if not claimed:
                for row in rows:
                    actions.append({"artifact_id": row["id"], "path": row["path"], "action": "preserved", "reason": "archive-claim-lost"})
                continue
            try:
                receipt = self.archive_runner(paths, archive)
            except Exception as exc:
                with self.connect() as con:
                    con.execute(
                        "UPDATE artifacts SET state='eligible-pending',claim_at=NULL,updated_at=? WHERE run_id=? AND archive_json=? AND state='archiving'",
                        (iso(now), rows[0]["run_id"], archive_raw),
                    )
                for row in rows:
                    actions.append({"artifact_id": row["id"], "path": row["path"], "action": "preserved", "reason": f"pcloud-archive-failed:{type(exc).__name__}"})
                continue
            receipt_items = receipt.get("files") if isinstance(receipt, dict) else None
            receipt_complete = bool(
                receipt.get("provider") == "pcloud"
                and receipt.get("verified") is True
                and isinstance(receipt_items, list)
                and all(any(
                    isinstance(item, dict)
                    and item.get("source") == str(Path(row["path"]).resolve())
                    and item.get("sha256") == row["sha256"]
                    and item.get("sha1")
                    and item.get("remote_path")
                    for item in receipt_items
                ) for row in rows)
            )
            if not receipt_complete:
                with self.connect() as con:
                    con.execute(
                        "UPDATE artifacts SET state='eligible-pending',claim_at=NULL,updated_at=? WHERE run_id=? AND archive_json=? AND state='archiving'",
                        (iso(now), rows[0]["run_id"], archive_raw),
                    )
                for row in rows:
                    actions.append({"artifact_id": row["id"], "path": row["path"], "action": "preserved", "reason": "pcloud-receipt-incomplete"})
                continue
            receipt_json = json.dumps(receipt, sort_keys=True)
            with self.connect() as con:
                con.execute("BEGIN IMMEDIATE")
                for row in rows:
                    con.execute(
                        "UPDATE artifacts SET receipt_json=?,state='eligible-pending',claim_at=NULL,updated_at=? WHERE id=? AND state='archiving'",
                        (receipt_json, iso(now), row["id"]),
                    )
                con.commit()
            normal.extend(rows)

        for row in normal:
            path = Path(row["path"])
            ok, reason = self._fingerprint_matches(path, row)
            if not ok:
                actions.append({"artifact_id": row["id"], "path": str(path), "action": "preserved", "reason": reason})
                if not audit_only:
                    with self.connect() as con:
                        con.execute("UPDATE artifacts SET state='review',review_reason=?,updated_at=? WHERE id=?", (reason, iso(now), row["id"]))
                continue
            receipt_ok = {
                "reproducible": True,
                "source-backed": self._source_receipt_valid(row),
                "verify-drive": self._drive_receipt_valid(row),
                "archive-pcloud": self._pcloud_receipt_valid(self._refresh_row(row["id"])),
                "preserve": False,
            }[row["disposition"]]
            if not receipt_ok:
                actions.append({"artifact_id": row["id"], "path": str(path), "action": "preserved", "reason": "durable-verification-missing"})
                continue
            if audit_only:
                actions.append({"artifact_id": row["id"], "path": str(path), "action": "would-quarantine"})
            else:
                actions.append(self._quarantine_one(row["id"]))

        for row in purgeable:
            target = Path(row["quarantine_path"])
            ok, reason = self._fingerprint_matches(target, row, quarantine=True)
            if not ok:
                actions.append({"artifact_id": row["id"], "path": str(target), "action": "preserved", "reason": reason})
                if not audit_only:
                    with self.connect() as con:
                        con.execute("UPDATE artifacts SET state='review',review_reason=?,updated_at=? WHERE id=?", (reason, iso(now), row["id"]))
            elif audit_only:
                actions.append({"artifact_id": row["id"], "path": str(target), "action": "would-purge"})
            else:
                actions.append(self._purge_one(row["id"]))

        counts = Counter(item["action"] for item in actions)
        return {
            "ok": True,
            "audit_only": audit_only,
            "at": iso(now),
            "actions": actions,
            "counts": dict(sorted(counts.items())),
        }

    def _refresh_row(self, artifact_id: str) -> sqlite3.Row:
        with self.connect() as con:
            row = con.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
        if not row:
            raise ValueError(f"unknown artifact: {artifact_id}")
        return row

    def quarantine_list(self) -> list[dict]:
        with self.connect() as con:
            rows = con.execute("SELECT * FROM artifacts WHERE state='quarantined' ORDER BY purge_at,path").fetchall()
        return [self._public_artifact(dict(row)) for row in rows]

    def restore(self, artifact_id: str) -> dict:
        now = self.clock()
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM artifacts WHERE id=?", (artifact_id,)).fetchone()
            if not row or row["state"] != "quarantined":
                raise ValueError("artifact is not quarantined")
            target = Path(row["quarantine_path"])
            original = Path(row["path"])
            ok, reason = self._fingerprint_matches(target, row, quarantine=True)
            if not ok:
                raise ValueError(f"quarantined artifact changed: {reason}")
            if original.exists():
                raise ValueError(f"restore target already exists: {original}")
            if not path_within(original, self.allowed_roots):
                raise ValueError("restore target is outside allowed roots")
            con.execute("UPDATE artifacts SET state='restoring',claim_at=?,updated_at=? WHERE id=?", (iso(now), iso(now), artifact_id))
            con.commit()
        original.parent.mkdir(parents=True, exist_ok=True)
        os.replace(target, original)
        restored = file_fingerprint(original)
        if restored["sha256"] != row["sha256"]:
            raise RuntimeError("restored file hash mismatch")
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                """UPDATE artifacts SET state='preserved',review_reason='restored-by-operator',
                   quarantine_path=NULL,quarantined_at=NULL,purge_at=NULL,claim_at=NULL,updated_at=? WHERE id=?""",
                (iso(now), artifact_id),
            )
            self._journal(con, "restored", artifact_id, str(original))
            con.commit()
        try:
            target.parent.rmdir()
        except OSError:
            pass
        return self.get_artifact(artifact_id)

    def legacy_inventory(self, output: Path | None = None) -> dict:
        now = self.clock()
        with self.connect() as con:
            registered = {row[0] for row in con.execute("SELECT path FROM artifacts")}
        grouped = defaultdict(lambda: {"files": 0, "bytes": 0, "ages": Counter(), "extensions": Counter()})
        for root in self.allowed_roots:
            if not root.is_dir():
                continue
            for candidate in root.rglob("*"):
                if not candidate.is_file() or candidate.is_symlink() or ".git" in candidate.parts:
                    continue
                exact = str(candidate.resolve())
                if exact in registered:
                    continue
                info = candidate.stat()
                age = (now.timestamp() - info.st_mtime) / 86400
                bucket = "under-7d" if age < 7 else "7-30d" if age < 31 else "31-90d" if age < 91 else "over-90d"
                group = grouped[str(root)]
                group["files"] += 1
                group["bytes"] += info.st_size
                group["ages"][bucket] += 1
                group["extensions"][candidate.suffix.lower() or "[none]"] += 1
        groups = []
        for root, values in sorted(grouped.items()):
            groups.append({
                "root": root,
                "files": values["files"],
                "bytes": values["bytes"],
                "ages": dict(sorted(values["ages"].items())),
                "extensions": dict(values["extensions"].most_common()),
            })
        payload = {
            "generated_at": iso(now),
            "adopted": 0,
            "groups": groups,
            "totals": {"files": sum(item["files"] for item in groups), "bytes": sum(item["bytes"] for item in groups)},
        }
        output = output or self.root / "legacy-inventory.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".new")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, output)
        if os.name != "nt":
            os.chmod(output, 0o600)
        return {**payload, "report_path": str(output)}


def archive_metadata(args) -> dict | None:
    values = {
        "client": args.archive_client,
        "dataset": args.archive_dataset,
        "market": args.archive_market,
        "month": args.archive_month,
        "report_type": args.archive_report_type,
        "scope": args.archive_scope,
    }
    return values if any(values.values()) else None


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="artifactctl", description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run_sub = run.add_subparsers(dest="run_command", required=True)
    start = run_sub.add_parser("start")
    start.add_argument("--id")
    start.add_argument("--owner", required=True)
    start.add_argument("--client")
    start.add_argument("--workflow", required=True)
    complete = run_sub.add_parser("complete")
    complete.add_argument("--run", required=True)
    complete.add_argument("--outcome", choices=sorted(RUN_OUTCOMES), default="success")
    show = run_sub.add_parser("show")
    show.add_argument("--run", required=True)

    register = sub.add_parser("register")
    register.add_argument("--run", required=True)
    register.add_argument("--path", type=Path, required=True)
    register.add_argument("--disposition", choices=sorted(DISPOSITIONS), required=True)
    register.add_argument("--source-origin")
    register.add_argument("--receipt")
    register.add_argument("--archive-client")
    register.add_argument("--archive-dataset")
    register.add_argument("--archive-market")
    register.add_argument("--archive-month")
    register.add_argument("--archive-report-type")
    register.add_argument("--archive-scope", default="ALL-SKUS")

    cleanup = sub.add_parser("cleanup")
    cleanup.add_argument("--audit-only", action="store_true")
    quarantine = sub.add_parser("quarantine")
    qsub = quarantine.add_subparsers(dest="quarantine_command", required=True)
    qsub.add_parser("list")
    restore = qsub.add_parser("restore")
    restore.add_argument("--artifact", required=True)
    legacy = sub.add_parser("legacy-inventory")
    legacy.add_argument("--output", type=Path)
    return ap


def main() -> int:
    args = parser().parse_args()
    registry = ArtifactRegistry()
    try:
        if args.command == "run" and args.run_command == "start":
            result = registry.start_run(args.owner, args.workflow, args.client, args.id)
        elif args.command == "run" and args.run_command == "complete":
            result = registry.complete_run(args.run, args.outcome)
        elif args.command == "run" and args.run_command == "show":
            result = registry.get_run(args.run)
        elif args.command == "register":
            result = registry.register(
                args.run,
                args.path,
                args.disposition,
                args.source_origin,
                json_value(args.receipt),
                archive_metadata(args),
            )
        elif args.command == "cleanup":
            result = registry.cleanup(args.audit_only)
        elif args.command == "quarantine" and args.quarantine_command == "list":
            result = {"artifacts": registry.quarantine_list()}
        elif args.command == "quarantine" and args.quarantine_command == "restore":
            result = registry.restore(args.artifact)
        elif args.command == "legacy-inventory":
            result = registry.legacy_inventory(args.output)
        else:
            raise ValueError("unsupported command")
    except (OSError, ValueError, RuntimeError, sqlite3.Error, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
