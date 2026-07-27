#!/bin/bash
# Single-video whisper worker, built for `xargs -P N`. Skips completed, cleans audio.
# Transcripts go to $VT_WORKDIR/wh/ (defaults to the current directory).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKDIR="${VT_WORKDIR:-$PWD}"
id="$1"
dir="$WORKDIR/wh"
out="$dir/$id.md"
mkdir -p "$dir"
[ -s "$out" ] && exit 0
if python3 "$HERE/transcribe.py" --out "$dir" -- "$id" > "$out.tmp" 2>"$dir/$id.err"; then
  mv "$out.tmp" "$out"; rm -f "$dir/$id.err"
  rm -rf "$dir/wd-$id"          # drop audio, keep the transcript
  echo "OK   $id  $(grep -c '^\[' "$out") segs"
else
  rm -f "$out.tmp"; rm -rf "$dir/wd-$id"   # audio goes on failure too, see README
  echo "FAIL $id  $(tail -1 "$dir/$id.err" | cut -c1-70)"
fi
