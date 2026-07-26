#!/bin/bash
SC="/private/tmp/claude-501/-Users-victoruhl-Obsidian-Victors-Second-Brain/2e1b33af-de0d-4790-8c01-26683fcb2053/scratchpad"
id="$1"
out="$SC/wh/$id.md"
[ -s "$out" ] && exit 0
if python3 "$SC/transcribe.py" --out "$SC/wh" -- "$id" > "$out.tmp" 2>"$SC/wh/$id.err"; then
  mv "$out.tmp" "$out"; rm -f "$SC/wh/$id.err"
  rm -rf "$SC/wh/wd-$id"          # drop audio, keep the transcript
  echo "OK   $id  $(grep -c '^\[' "$out") segs"
else
  rm -f "$out.tmp"; echo "FAIL $id  $(tail -1 "$SC/wh/$id.err" | cut -c1-70)"
fi
