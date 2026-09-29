"""Machine-readable quality reports for campaign-builder runs.

The report is a local artifact. It contains no credentials and performs no
network calls. A separate, explicitly configured integration may publish the
report to an approved reporting system later.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_quality_report(path, *, mode, phase, cfg, errors=None, warnings=None,
                         notes=None, metrics=None):
    """Write one atomic JSON quality report and return its resolved path."""
    destination = Path(path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    errors = list(errors or [])
    warnings = list(warnings or [])
    notes = list(notes or [])
    report = {
        "schema_version": 1,
        "producer": "amazon-agent/amazon-campaign-builder",
        "mode": mode,
        "phase": phase,
        "status": "fail" if errors else "pass",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "context": {
            "client": str(cfg.get("client") or ""),
            "marketplace": str(cfg.get("marketplace") or ""),
        },
        "summary": {
            "error_count": len(errors),
            "warning_count": len(warnings),
            "note_count": len(notes),
            **dict(metrics or {}),
        },
        "checks": [
            *({"severity": "error", "status": "fail", "message": message}
              for message in errors),
            *({"severity": "warning", "status": "warn", "message": message}
              for message in warnings),
            *({"severity": "note", "status": "pass", "message": message}
              for message in notes),
        ],
    }
    temporary = destination.with_name(destination.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                         encoding="utf-8")
    temporary.replace(destination)
    return destination
