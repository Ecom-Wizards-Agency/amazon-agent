#!/bin/bash
# Single-video diarizing worker, built for `xargs -P N`. Skips completed, cleans audio.
# Transcripts go to $VT_WORKDIR/di/ (defaults to the current directory).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="${VT_WORKDIR:-$PWD}"
id="$1"
dir="$WORKDIR/di"
out="$dir/$id.md"
mkdir -p "$dir"
[ -s "$out" ] && exit 0
if python3 "$HERE/transcribe.py" --backend diarize --out "$dir" -- "$id" > "$out.tmp" 2>"$dir/$id.err"; then
  mv "$out.tmp" "$out"; rm -f "$dir/$id.err"; rm -rf "$dir/wd-$id"
  echo "OK   $id  $(grep -c '^\[' "$out") segs, $(grep -oE '\] [A-Z]: ' "$out" | sort -u | wc -l | tr -d ' ') speakers"
else
  rm -f "$out.tmp"; rm -rf "$dir/wd-$id"   # audio goes on failure too, see README
  echo "FAIL $id  $(tail -1 "$dir/$id.err" | cut -c1-60)"
fi
