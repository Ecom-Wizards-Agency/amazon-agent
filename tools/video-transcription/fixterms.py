#!/usr/bin/env python3
"""Repair whisper-1's systematic Amazon-jargon errors in place.

Each rule below was verified against gpt-4o-transcribe on identical audio
spans, or against surrounding context in the corpus — none are guesses.
Guards keep legitimate English ("a cost per click of $1.20") untouched.

  fixterms.py DIR [--apply]      # dry-run by default
"""
import argparse, pathlib, re, sys

RULES = [
    # (pattern, replacement, note)
    # "a cost" -> ACOS, but NOT "a cost of/per ..." which is real English.
    (re.compile(r'\ba cost\b(?!\s+(?:of|per)\b)', re.I), 'ACOS',
     'ACOS misheard as "a cost"'),
    (re.compile(r'\bPBC\b'), 'PPC', 'PPC misheard as "PBC"'),
    # "T-ACOS"/"T ACOS" is unambiguous on its own.
    (re.compile(r'\bT[- ]ACOS\b', re.I), 'TACOS', 'TACOS written as "T-ACOS"'),
    (re.compile(r'\basens\b|\baces\b(?=[^.!?]*\b(?:you have|targets|catalog|child)\b)', re.I),
     'ASINs', 'ASINs misheard'),
    (re.compile(r'\bclawed\b(?=[^.!?]*\b(?:skill|code|AI|prompt|upload)\b)', re.I),
     'Claude', 'Claude misheard as "clawed"'),
    (re.compile(r'\brorowaz\b|\broaz\b', re.I), 'ROAS', 'ROAS misheard'),
]


# Bare "tacos" is the metric only when the surrounding line talks about one.
# Checked across the whole line, not just forward — the cue often precedes it
# ("the ACoS of the tacos is really high").
TACOS_WORD = re.compile(r'\btacos\b', re.I)
TACOS_CONTEXT = re.compile(
    r'\b(?:ACOS|ACoS|ad spend|advertising|revenue|percent|profit|margin|sales|%)\b', re.I)


def fix(text):
    counts = {}
    for pat, rep, note in RULES:
        text, n = pat.subn(rep, text)
        if n:
            counts[note] = counts.get(note, 0) + n

    out, n = [], 0
    for line in text.split('\n'):
        if TACOS_WORD.search(line) and TACOS_CONTEXT.search(line):
            line, k = TACOS_WORD.subn('TACOS', line)
            n += k
        out.append(line)
    if n:
        counts['TACOS misheard as "tacos"'] = n
    return '\n'.join(out), counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('directory')
    ap.add_argument('--apply', action='store_true', help='write changes (default: dry run)')
    a = ap.parse_args()

    total, touched = {}, 0
    for p in sorted(pathlib.Path(a.directory).glob('*.md')):
        original = p.read_text()
        fixed, counts = fix(original)
        if not counts:
            continue
        touched += 1
        for k, v in counts.items():
            total[k] = total.get(k, 0) + v
        if a.apply:
            p.write_text(fixed)

    mode = 'APPLIED' if a.apply else 'DRY RUN (use --apply to write)'
    print(f'{mode}: {touched} files affected')
    for note, n in sorted(total.items(), key=lambda kv: -kv[1]):
        print(f'  {n:>5}  {note}')
    if not total:
        print('  nothing to fix')


if __name__ == '__main__':
    main()
