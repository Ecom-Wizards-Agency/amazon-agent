#!/usr/bin/env python3
"""Fact and claims gate for Amazon listing-image copy.

Usage:
  python3 -I -B check_copy.py <copy.json> --skeleton <copy-skeleton.json>
      --profile <profile.json> --facts <facts.json> [--json]

Exit 0 requires zero errors and no profile review holds; 1 means there are errors,
2 on a usage, read or configuration error, 3 when profile review is required.
Warnings alone never change the exit code. Fixed keys must match
the skeleton exactly; only free keys are checked for claims.

Four inputs, each with one job:

copy.json (the filled copy) and copy-skeleton.json share one schema:
  {"frames": [{"id": "PT01", "order": 1, "job": "...",
               "texts": [{"key": "headline", "role": "headline",
                          "fixed": false, "max_chars": 52, "text": ""}]}],
   "approved_sf_lines": ["<structure/function line exactly as approved>"],
   "sf_keys": ["PT06.headline"],
   "optional_empty_keys": ["PT07.sf"],
   "disclaimer_rule": "<the human decision about where the disclaimer shows>"}
  In the skeleton a fixed text carries its exact "text"; a free text carries
  "max_chars". The copy repeats the frames with every text filled in. A key in
  sf_keys must hold exactly one approved_sf_lines entry (or be empty when it is
  also in optional_empty_keys) and is not run through the banned list. Every
  frame named in sf_keys that holds an S/F line must also carry the profile's
  disclaimer key with the profile's prefix.

profile.json (per category, in references/claims-profiles/):
  {"name": "...", "extends": "<name or path of another profile in the same
   folder>", "banned": {"<reason>": ["<regex>", ...]}, "warnings": {...},
   "disclaimer": null | {"key": "disclaimer", "prefix": "*These ...",
                         "name": "FDA disclaimer"},
   "headline_words": {"min": 2, "max": 8, "aim": [3, 7]},
   "eyebrow_caps": true, "no_text_frames": ["MAIN"]}
  banned and warnings may also be flat lists. Patterns run on the normalized
  text and ignore case (see norm below). Lists merge from the base profile
  down, a repeated pattern counting once; scalar keys come from the most
  specific profile that sets them.

facts.json (per product):
  {"product_name": "<name as printed on the pack>",
   "name_stem": "<start of the name>" | ["<stem>", ...],
   "allowed_numbers": ["200", "60"],
   "extra_banned": ["<regex>"],
   "allow": ["<exact profile pattern this product may use>"],
   "unit_values": [{"unit": "mg", "value": "200"}],
   "rules": [{"pattern": "<regex>", "message": "...", "level": "error"}]}
  name_stem catches misspellings: any word that starts with a stem and is not a
  word of product_name (or of the optional "brand") is an error. Pick a stem
  long enough that ordinary words do not start with it. allowed_numbers lists
  every number the label prints; any other number in free text is an error.
  A unit_values entry makes a number written before the unit ("60 mg", "60mg")
  an error unless it is the value, and so is any free text that names the unit
  and contains a digit but not the value. rules patterns run on the normalized
  text and ignore case; level is "error" or "warning". allow lifts a banned
  pattern for this product and must name a pattern the profile actually bans.

Every copy frame must be a skeleton frame and every text key a skeleton key;
a repeated frame id or key is an error. Roles come from the skeleton. Before
matching, free text is NFKC-normalized, typographic apostrophes, hyphens and
dashes become ASCII, no-break spaces become spaces, and case is folded.
The output starts with the command line and the sha256 of every profile file
in the extends chain, so gate.txt records what gated the copy.
"""
import argparse
import hashlib
import json
import pathlib
import re
import shlex
import sys
import unicodedata

NUM_RE = re.compile(r"(?<![A-Za-z])\d[\d,]*")
WORD_RE = re.compile(r"[A-Za-z0-9'’,.-]+")
FOLD = {0x2018: "'", 0x2019: "'", 0x02bc: "'", 0x2010: "-", 0x2011: "-", 0x2012: "-",
        0x2013: "-", 0x2014: "-", 0x2212: "-", 0x00a0: " ", 0x2007: " ", 0x202f: " ",
        0x0130: "I"}


def norm(text):
    """The text patterns and numbers run on: NFKC, ASCII punctuation, case folded."""
    return unicodedata.normalize("NFKC", text).translate(FOLD).casefold()


class ConfigError(Exception):
    pass


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def patterns(value, where):
    """Flatten a list or a {reason: [patterns]} mapping into one ordered list."""
    if value is None:
        return []
    if isinstance(value, dict):
        out = []
        for group in value.values():
            out.extend(patterns(group, where))
        return out
    if isinstance(value, list) and all(isinstance(p, str) for p in value):
        return list(value)
    raise ConfigError(f"{where}: expected a list of patterns or a mapping of lists")


def profile_chain(path, seen=None):
    """Each layer of the extends chain as (data, file), base first."""
    path = pathlib.Path(path).resolve()
    seen = seen or []
    if path in seen:
        raise ConfigError(f"profile extends loop at {path}")
    data = load(path)
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: profile must be a JSON object")
    parent = data.get("extends")
    if parent is None:
        return [(data, path)]
    if not isinstance(parent, str) or not parent.strip():
        raise ConfigError(f"{path}: extends must be a profile name or path")
    ref = pathlib.Path(parent)
    if not ref.suffix:
        ref = ref.with_suffix(".json")
    if not ref.is_absolute():
        ref = path.parent / ref
    return profile_chain(ref, seen + [path]) + [(data, path)]


def check_layer(layer, name):
    where = f"profile {name}"
    hw = layer.get("headline_words")
    if hw is not None and not (isinstance(hw, dict) and all(isinstance(hw.get(k), int) for k in ("min", "max"))):
        raise ConfigError(f"{where}: headline_words needs integer min and max")
    aim = (hw or {}).get("aim")
    if aim is not None and not (isinstance(aim, list) and len(aim) == 2 and all(isinstance(x, int) for x in aim)):
        raise ConfigError(f"{where}: headline_words aim must be two integers")
    d = layer.get("disclaimer")
    if d is not None and not (isinstance(d, dict) and all(isinstance(d.get(k), str) for k in ("key", "prefix"))):
        raise ConfigError(f"{where}: disclaimer must be null or have string key and prefix")
    ntf = layer.get("no_text_frames")
    if ntf is not None and not (isinstance(ntf, list) and all(isinstance(x, str) for x in ntf)):
        raise ConfigError(f"{where}: no_text_frames must be a list of frame ids")
    if "eyebrow_caps" in layer and not isinstance(layer["eyebrow_caps"], bool):
        raise ConfigError(f"{where}: eyebrow_caps must be true or false")


def merge_profile(path):
    profile = {"banned": [], "warnings": [], "disclaimer": None, "headline_words": None,
               "eyebrow_caps": False, "no_text_frames": [], "names": [], "files": [],
               "review_reasons": []}
    for layer, file in profile_chain(path):
        name = layer.get("name", "?")
        profile["names"].append(name)
        profile["files"].append((name, str(file), hashlib.sha256(file.read_bytes()).hexdigest()))
        check_layer(layer, layer.get("name") or str(file))
        for key, held in (("status", "draft"), ("verification", "unverified")):
            value = layer.get(key)
            if value is not None and not isinstance(value, str):
                raise ConfigError(f"profile {name}: {key} must be a string")
            if value is not None and value.strip().casefold() == held:
                profile["review_reasons"].append(f"profile {name}: {key} is {held}")
        for key in ("banned", "warnings"):
            for p in patterns(layer.get(key), f"profile {layer.get('name')}.{key}"):
                if p not in profile[key]:
                    profile[key].append(p)
        for key in ("disclaimer", "headline_words", "eyebrow_caps", "no_text_frames"):
            if key in layer:
                profile[key] = layer[key]
    return profile


def compile_all(items, where):
    out = []
    for p in items:
        try:
            out.append(re.compile(p, re.IGNORECASE))
        except re.error as e:
            raise ConfigError(f"{where}: bad pattern {p!r} ({e})")
    return out


def check_facts(facts):
    if not isinstance(facts, dict):
        raise ConfigError("facts must be a JSON object")
    for key in ("product_name", "brand"):
        if key in facts and not isinstance(facts[key], str):
            raise ConfigError(f"facts {key} must be a string")
    for key in ("allowed_numbers", "extra_banned", "allow"):
        v = facts.get(key, [])
        if not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
            raise ConfigError(f"facts {key} must be a list of strings")
    stems = facts.get("name_stem")
    stems = [stems] if isinstance(stems, str) else stems
    if stems is not None and not (isinstance(stems, list) and stems
                                  and all(isinstance(x, str) and x.strip() for x in stems)):
        raise ConfigError("facts name_stem must be a non-empty string or a list of them")
    for key in ("unit_values", "rules"):
        v = facts.get(key, [])
        if not (isinstance(v, list) and all(isinstance(x, dict) for x in v)):
            raise ConfigError(f"facts {key} must be a list of objects")
    for u in facts.get("unit_values", []):
        if not (isinstance(u.get("unit"), str) and u["unit"].strip() and isinstance(u.get("value"), str)):
            raise ConfigError(f"facts unit_values entry {u!r}: needs string unit and value")
    for r in facts.get("rules", []):
        if (r.get("level", "error") not in ("error", "warning") or not isinstance(r.get("pattern"), str)
                or not isinstance(r.get("message"), str)):
            raise ConfigError(f"facts rule {r!r}: needs pattern, message and level error or warning")


def check_skeleton(skel):
    if not isinstance(skel, dict) or not isinstance(skel.get("frames"), list):
        raise ConfigError("skeleton has no frames list")
    ids = [sf.get("id") for sf in skel["frames"] if isinstance(sf, dict)]
    for fid in sorted({i for i in ids if ids.count(i) > 1}, key=str):
        raise ConfigError(f"skeleton frame id {fid!r} is repeated")
    for sf in skel["frames"]:
        if "id" not in sf or not isinstance(sf.get("texts", []), list):
            raise ConfigError(f"skeleton frame {sf!r:.60} needs an id and a texts list")
        for st in sf.get("texts", []):
            loc = f"{sf['id']}.{st.get('key')}"
            if "key" not in st or not isinstance(st.get("fixed"), bool):
                raise ConfigError(f"skeleton {loc}: needs key and fixed (true or false)")
            if st["fixed"] and not isinstance(st.get("text"), str):
                raise ConfigError(f"skeleton {loc}: a fixed text needs its text")
            if not st["fixed"] and not isinstance(st.get("max_chars"), int):
                raise ConfigError(f"skeleton {loc}: a free text needs max_chars")
        keys = [st["key"] for st in sf.get("texts", [])]
        for k in sorted({k for k in keys if keys.count(k) > 1}):
            raise ConfigError(f"skeleton {sf['id']}.{k}: key is repeated")


def gate(doc, skel, profile, facts):
    errors, warnings = [], []
    check_skeleton(skel)
    check_facts(facts)
    allow = facts.get("allow", [])
    for p in allow:
        if p not in profile["banned"]:
            raise ConfigError(f"facts allow {p!r} is not a banned pattern in the profile")
    banned = compile_all([p for p in profile["banned"] if p not in allow]
                         + [p for p in facts.get("extra_banned", []) if p not in profile["banned"]],
                         "banned")
    warn = compile_all(profile["warnings"], "warnings")
    rules = []
    for r in facts.get("rules", []):
        rules.append((compile_all([r["pattern"]], "facts rules")[0], r["message"], r.get("level", "error")))
    allowed_numbers = set(facts.get("allowed_numbers", []))
    units = []
    for u in facts.get("unit_values", []):
        unit = re.escape(norm(u["unit"]))
        units.append((u["unit"], u["value"], re.compile(r"(?<![a-z])" + unit + r"\b"),
                      re.compile(r"(?<![\d.,])(\d[\d,.]*)\s*" + unit + r"\b")))
    stems = facts.get("name_stem") or []
    if isinstance(stems, str):
        stems = [stems]
    names = set(re.findall(r"[a-z]+", norm(" ".join([facts.get("product_name", ""), facts.get("brand", "")]))))
    stem_res = [re.compile(r"\b" + re.escape(norm(s)) + r"[a-z]+\b") for s in stems]
    hw = profile["headline_words"]
    no_text = set(profile["no_text_frames"] or [])
    sf_keys = skel.get("sf_keys", [])
    approved = skel.get("approved_sf_lines", [])
    optional_empty = skel.get("optional_empty_keys", [])

    doc_ids = [f["id"] for f in doc.get("frames", [])]
    for fid in sorted({i for i in doc_ids if doc_ids.count(i) > 1}, key=str):
        errors.append(f"{fid}: duplicate frame id")
    for fid in sorted(set(doc_ids) - {sf["id"] for sf in skel["frames"]}, key=str):
        errors.append(f"{fid}: frame not in skeleton")
    frames = {f["id"]: f for f in doc.get("frames", [])}
    for sf in skel["frames"]:
        f = frames.get(sf["id"])
        if f is None:
            errors.append(f"{sf['id']}: frame missing")
            continue
        keys = [t["key"] for t in f.get("texts", [])]
        for k in sorted({k for k in keys if keys.count(k) > 1}):
            errors.append(f"{sf['id']}.{k}: duplicate key")
        texts = {t["key"]: t for t in f.get("texts", [])}
        extra = set(texts) - {t["key"] for t in sf.get("texts", [])}
        for k in sorted(extra):
            errors.append(f"{sf['id']}.{k}: key not in skeleton")
        if sf["id"] in no_text and f.get("texts"):
            errors.append(f"{sf['id']}: must have no texts")
        for st in sf.get("texts", []):
            k = st["key"]
            t = texts.get(k)
            loc = f"{sf['id']}.{k}"
            if t is None:
                errors.append(f"{loc}: missing")
                continue
            txt = t.get("text", "")
            if st["fixed"]:
                if txt != st["text"]:
                    errors.append(f"{loc}: fixed text changed (expected {st['text']!r}, got {txt!r})")
                continue
            if not txt.strip():
                if loc in optional_empty:
                    continue
                errors.append(f"{loc}: empty")
                continue
            if loc in sf_keys:
                if txt not in approved:
                    errors.append(f"{loc}: structure/function line must be exactly one of {approved} (got {txt!r})")
                continue
            if len(txt) > st["max_chars"]:
                errors.append(f"{loc}: {len(txt)} chars > max {st['max_chars']}")
            low = norm(txt)
            for pat in banned:
                m = pat.search(low)
                if m:
                    errors.append(f"{loc}: banned term {m.group(0)!r} in {txt!r}")
            for pat in warn:
                m = pat.search(low)
                if m:
                    warnings.append(f"{loc}: check {m.group(0)!r} in {txt!r}")
            for n in NUM_RE.findall(low):
                n = n.rstrip(",")
                if n not in allowed_numbers:
                    errors.append(f"{loc}: number {n!r} is not a label fact")
            for pat, message, level in rules:
                if pat.search(low):
                    (errors if level == "error" else warnings).append(f"{loc}: {message}")
            for unit, value, unit_re, pair_re in units:
                if not unit_re.search(low) or unit_re.search(norm(st.get("text") or "")):
                    continue
                wrong_pair = any(n.rstrip(",.") != value for n in pair_re.findall(low))
                if wrong_pair or (value not in low and re.search(r"\d", low)):
                    errors.append(f"{loc}: {unit} with a number other than {value}")
            for stem_re in stem_res:
                for tok in stem_re.findall(low):
                    if tok not in names:
                        errors.append(f"{loc}: product name spelled {tok!r}")
            role = st.get("role")
            if hw and role == "headline":
                words = len(WORD_RE.findall(txt.replace("\n", " ")))
                if words < hw["min"] or words > hw["max"]:
                    aim = hw.get("aim") or [hw["min"], hw["max"]]
                    warnings.append(f"{loc}: headline has {words} words (aim {aim[0]}-{aim[1]})")
            if profile["eyebrow_caps"] and role == "eyebrow" and txt != txt.upper():
                warnings.append(f"{loc}: eyebrow not in capitals")

    # A frame that holds an S/F line needs the fixed disclaimer on the same frame.
    sf_frames = {}
    for key in sf_keys:
        fid, _, k = key.partition(".")
        sf_frames.setdefault(fid, []).append(k)
    disclaimer = profile["disclaimer"]
    if sf_frames and not disclaimer:
        warnings.append("sf_keys are set but the profile has no disclaimer rule")
    elif disclaimer:
        for fid, keys in sf_frames.items():
            t = {x["key"]: x.get("text", "") for x in frames.get(fid, {}).get("texts", [])}
            holds_sf = any(t.get(k, "") for k in keys)
            if holds_sf and not t.get(disclaimer["key"], "").startswith(disclaimer["prefix"]):
                errors.append(f"{fid}: S/F line without the {disclaimer.get('name', 'disclaimer')}")
    return errors, warnings


def main(argv):
    ap = argparse.ArgumentParser(description="Fact and claims gate for Amazon listing-image copy.")
    ap.add_argument("copy")
    ap.add_argument("--skeleton", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--facts", required=True)
    ap.add_argument("--json", action="store_true")
    try:
        args = ap.parse_args(argv)
    except SystemExit as e:
        return 0 if e.code == 0 else 2
    try:
        doc, skel, facts = load(args.copy), load(args.skeleton), load(args.facts)
        profile = merge_profile(args.profile)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    except (OSError, ValueError) as e:
        print(f"read error: {e}", file=sys.stderr)
        return 2
    try:
        errors, warnings = gate(doc, skel, profile, facts)
    except ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, AttributeError) as e:
        print(f"read error: copy or facts file is malformed ({e!r})", file=sys.stderr)
        return 2
    command = shlex.join(["python3", "-I", "-B", str(pathlib.Path(__file__).resolve())] + list(argv))
    review_reasons = profile["review_reasons"]
    status = "failed" if errors else "review_required" if review_reasons else "passed"
    result = {"file": args.copy, "command": command, "cwd": str(pathlib.Path.cwd()),
              "profiles": [{"name": n, "path": f, "sha256": h} for n, f, h in profile["files"]],
              "errors": errors, "warnings": warnings, "status": status,
              "review_required": bool(review_reasons), "review_reasons": review_reasons,
              "ok": status == "passed"}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("command:", command)
        print("cwd:    ", result["cwd"])
        for n, f, h in profile["files"]:
            print(f"profile: {n} sha256 {h} {f}")
        for e in errors:
            print("ERROR  ", e)
        for w in warnings:
            print("WARN   ", w)
        for reason in review_reasons:
            print("REVIEW ", reason)
        if review_reasons:
            print("REVIEW REQUIRED: record meaning-level refuter clearance and named human sign-off in claims.md before clearing the pack.")
        print(f"{len(errors)} errors, {len(warnings)} warnings; {status}")
    return 1 if errors else 3 if review_reasons else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
