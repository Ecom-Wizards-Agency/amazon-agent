#!/usr/bin/env bash
# Debug-Chrome launcher — WRAPPER ONLY. The implementation is
# launch-chrome-debug.py, so macOS and Windows share one code path.
# The .sh name stays because docs, skills and muscle memory refer to it.
# Do NOT reimplement the launch logic here; two copies would drift.
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else echo "no python interpreter on PATH" >&2; exit 1; fi
exec "$PY" "$DIR/launch-chrome-debug.py" "$@"
