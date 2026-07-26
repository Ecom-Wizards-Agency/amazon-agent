#!/bin/bash
SC="/private/tmp/claude-501/-Users-victoruhl-Obsidian-Victors-Second-Brain/2e1b33af-de0d-4790-8c01-26683fcb2053/scratchpad"
id="$1"; out="$SC/di/$id.md"
[ -s "$out" ] && exit 0
if python3 "$SC/transcribe.py" --backend diarize --out "$SC/di" -- "$id" > "$out.tmp" 2>"$SC/di/$id.err"; then
  mv "$out.tmp" "$out"; rm -f "$SC/di/$id.err"; rm -rf "$SC/di/wd-$id"
  echo "OK   $id  $(grep -c '^\[' "$out") segs, $(grep -oE '\] [A-Z]: ' "$out" | sort -u | wc -l | tr -d ' ') speakers"
else rm -f "$out.tmp"; echo "FAIL $id  $(tail -1 "$SC/di/$id.err" | cut -c1-60)"; fi
