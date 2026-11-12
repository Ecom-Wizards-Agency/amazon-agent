#!/usr/bin/env python3
"""Synthetic, client-neutral tests for check_copy.py.

Run: python3 -I -B skills/amazon-listing-images/scripts/selftest_check_copy.py
Builds an invented product in a temp folder, checks that the clean copy passes
with the US dietary-supplement profile (which extends amazon-standard), then
runs one mutation per rule and expects its error, a few mutations that must
warn, ordinary wording that must pass, and broken profiles or facts that must
exit 2. Stdlib only. Prints PASS or FAIL per case and exits 0 only when every
case passes.
"""
import copy
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE / "check_copy.py"
PROFILES = HERE.parent / "references" / "claims-profiles"
PROFILE = PROFILES / "us-dietary-supplement.json"
STANDARD = PROFILES / "amazon-standard.json"
COSMETIC = PROFILES / "us-cosmetic.json"
DISCLAIMER = ("*These statements have not been evaluated by the Food and Drug Administration. "
              "This product is not intended to diagnose, treat, cure, or prevent any disease.")
SF_LINE = "Supports muscle function*"


def free(key, role, max_chars):
    return {"key": key, "role": role, "fixed": False, "max_chars": max_chars, "text": ""}


def fixed(key, role, text):
    return {"key": key, "role": role, "fixed": True, "text": text}


SKELETON = {
    "product": "Northwind Magnesium",
    "approved_sf_lines": [SF_LINE],
    "sf_keys": ["PT03.headline", "PT04.sf"],
    "optional_empty_keys": ["PT04.sf"],
    "disclaimer_rule": "Every frame that shows an S/F line carries the disclaimer.",
    "frames": [
        {"id": "MAIN", "order": 0, "job": "Recognition: bottle on white", "texts": []},
        {"id": "PT01", "order": 1, "job": "Core message", "texts": [
            free("eyebrow", "eyebrow", 26), free("headline", "headline", 52),
            free("sub", "subheadline", 80), fixed("disclaimer", "fine-print", DISCLAIMER)]},
        {"id": "PT02", "order": 2, "job": "Amount per serving", "texts": [
            fixed("stat", "stat", "200"), fixed("unit", "stat", "mg"),
            free("headline", "headline", 46), fixed("disclaimer", "fine-print", DISCLAIMER)]},
        {"id": "PT03", "order": 3, "job": "Approved S/F line", "texts": [
            free("eyebrow", "eyebrow", 26), free("headline", "headline", 44),
            fixed("disclaimer", "fine-print", DISCLAIMER)]},
        {"id": "PT04", "order": 4, "job": "Brand", "texts": [
            free("headline", "headline", 52), free("sf", "sf-line", 40),
            free("signoff", "signoff", 56), fixed("disclaimer", "fine-print", DISCLAIMER)]},
    ],
}

FILL = {
    "PT01.eyebrow": "ONE DAILY ROUTINE",
    "PT01.headline": "Two capsules.\nOne simple routine.",
    "PT01.sub": "Magnesium glycinate in 60 capsules, a 30 day supply.",
    "PT02.headline": "200 mg in every serving",
    "PT03.eyebrow": "WHY IT IS HERE",
    "PT03.headline": SF_LINE,
    "PT04.headline": "Made by Northwind",
    "PT04.sf": "",
    "PT04.signoff": "Northwind Magnesium, 2 capsules a day",
}

FACTS = {
    "product_name": "Northwind Magnesium",
    "name_stem": "northw",
    "allowed_numbers": ["200", "60", "30", "2"],
    "extra_banned": ["\\bsleep"],
    "unit_values": [{"unit": "mg", "value": "200"}],
    "rules": [{"pattern": "per capsule|each capsule", "message": "per-capsule figure or wording",
               "level": "error"},
              {"pattern": "\\bHCl\\b", "message": "hydrochloride named", "level": "error"}],
}


def clean_copy():
    doc = copy.deepcopy(SKELETON)
    for frame in doc["frames"]:
        for t in frame["texts"]:
            if not t["fixed"]:
                t["text"] = FILL[f"{frame['id']}.{t['key']}"]
    return doc


def text(doc, loc):
    fid, key = loc.split(".")
    frame = next(f for f in doc["frames"] if f["id"] == fid)
    return next(t for t in frame["texts"] if t["key"] == key)


def set_text(loc, value):
    def mutate(doc):
        text(doc, loc)["text"] = value
    return mutate


def drop_disclaimer(doc):
    frame = next(f for f in doc["frames"] if f["id"] == "PT03")
    frame["texts"] = [t for t in frame["texts"] if t["key"] != "disclaimer"]


def main_text(doc):
    doc["frames"][0]["texts"] = [{"key": "badge", "role": "badge", "fixed": False, "text": "NEW"}]


def extra_frame(doc):
    doc["frames"].append({"id": "PT09", "texts": [
        {"key": "headline", "role": "headline", "fixed": False, "text": "Best price, cures disease"}]})


def duplicate_frame(doc):
    bad = copy.deepcopy(doc["frames"][1])
    text({"frames": [bad]}, "PT01.headline")["text"] = "Best price cures disease"
    doc["frames"].insert(1, bad)


def duplicate_key(doc):
    doc["frames"][1]["texts"].insert(0, {"key": "headline", "role": "headline", "fixed": False,
                                         "text": "Best price, guaranteed results"})


def chain(*mutations):
    def mutate(doc):
        for m in mutations:
            m(doc)
    return mutate


def set_role(loc, role):
    def mutate(doc):
        text(doc, loc)["role"] = role
    return mutate


MUTATIONS = [
    ("banned term", set_text("PT01.headline", "The best routine"), "PT01.headline: banned term 'best'"),
    ("changed fixed text", set_text("PT02.stat", "250"), "PT02.stat: fixed text changed"),
    ("over max_chars", set_text("PT01.sub", "Magnesium glycinate in 60 capsules, a 30 day supply, "
                                "in one bottle that sits on the shelf."), "PT01.sub: 90 chars > max 80"),
    ("unknown number", set_text("PT01.sub", "Magnesium glycinate in 90 capsules."),
     "PT01.sub: number '90' is not a label fact"),
    ("wrong unit value", set_text("PT02.headline", "60 mg in every serving"),
     "PT02.headline: mg with a number other than 200"),
    ("per-unit rule from facts", set_text("PT01.sub", "The same amount in each capsule."),
     "PT01.sub: per-capsule figure or wording"),
    ("misspelt product name", set_text("PT04.headline", "Made by Northwnd"),
     "PT04.headline: product name spelled 'northwnd'"),
    ("S/F line not approved", set_text("PT03.headline", "Supports calm muscles*"),
     "PT03.headline: structure/function line must be exactly one of"),
    ("S/F line without disclaimer", drop_disclaimer, "PT03: S/F line without the FDA disclaimer"),
    ("text on MAIN", main_text, "MAIN: must have no texts"),
    ("frame not in skeleton", extra_frame, "PT09: frame not in skeleton"),
    ("duplicate frame id", duplicate_frame, "PT01: duplicate frame id"),
    ("duplicate key", duplicate_key, "PT01.headline: duplicate key"),
    ("typographic apostrophe", set_text("PT01.sub", "An Amazon\u2019s Choice pick."),
     "PT01.sub: banned term \"amazon's choice\""),
    ("non-breaking hyphen", set_text("PT01.sub", "A money\u2011back promise."),
     "PT01.sub: banned term 'money-back'"),
    ("unit written onto its number", set_text("PT02.headline", "60mg in every serving"),
     "PT02.headline: mg with a number other than 200"),
    ("wrong unit value beside the right one", set_text("PT02.headline", "200 mg here, 60 mg there"),
     "PT02.headline: mg with a number other than 200"),
    ("number before a hyphen", set_text("PT01.sub", "Take 9-2 capsules."), "PT01.sub: number '9'"),
    ("organic as its own claim", set_text("PT01.sub", "Organic magnesium glycinate."),
     "PT01.sub: banned term 'organic'"),
    ("facts rule written in capitals", set_text("PT01.sub", "Magnesium HCl in 60 capsules."),
     "PT01.sub: hydrochloride named"),
]

# (label, mutation, expected warning prefix)
WARNINGS = [
    ("headline role taken from the skeleton", chain(set_text("PT01.headline", "Routine"),
                                                  set_role("PT01.headline", "x")),
     "PT01.headline: headline has 1 words"),
    ("eyebrow role taken from the skeleton", chain(set_text("PT01.eyebrow", "one daily routine"),
                                                 set_role("PT01.eyebrow", "x")),
     "PT01.eyebrow: eyebrow not in capitals"),
]

# (label, mutation, profile): ordinary wording that must give no errors
CLEAN = [
    ("supplement profile: ordinary words", set_text("PT01.sub", "A smarter starter pack, clearly labelled cloth pouch."),
     PROFILE),
    ("standard profile: spec words", set_text("PT01.sub", "Seven compartment organiser, live preview, power rating 60 W."),
     STANDARD),
    ("standard profile: rated to", set_text("PT01.sub", "Water rated to 30 m."), STANDARD),
]

# (label, file to replace, content): broken configuration that must exit 2
CONFIG = [
    ("extends is a number", "profile", {"name": "broken", "extends": 5}),
    ("extends is a list", "profile", {"name": "broken", "extends": ["amazon-standard"]}),
    ("headline_words without min", "profile", {"name": "broken", "extends": "amazon-standard",
                                               "headline_words": {"max": 8}}),
    ("extra_banned as a string", "facts", dict(FACTS, extra_banned="sleep")),
    ("allowed_numbers as a string", "facts", dict(FACTS, allowed_numbers="200,60,30,2")),
    ("empty name_stem", "facts", dict(FACTS, name_stem=[""])),
]


def run(tmp, name, doc, profile=PROFILE, facts=None):
    path = tmp / f"{name}.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-I", "-B", str(GATE), str(path), "--skeleton", str(tmp / "skeleton.json"),
         "--profile", str(profile), "--facts", str(facts or tmp / "facts.json"), "--json"],
        capture_output=True, text=True)
    try:
        result = json.loads(proc.stdout)
    except ValueError:
        result = {"errors": [], "warnings": [], "stderr": proc.stderr}
    return proc.returncode, result


def main():
    failures = []
    with tempfile.TemporaryDirectory(prefix="check-copy-selftest-") as d:
        tmp = pathlib.Path(d)
        (tmp / "skeleton.json").write_text(json.dumps(SKELETON, indent=2), encoding="utf-8")
        (tmp / "facts.json").write_text(json.dumps(FACTS, indent=2), encoding="utf-8")

        code, result = run(tmp, "clean", clean_copy())
        ok = code == 0 and not result["errors"] and not result["warnings"]
        print(("PASS" if ok else "FAIL"), "clean copy: exit", code, result.get("errors"), result.get("warnings"))
        if not ok:
            failures.append("clean copy")

        for i, (label, mutate, expected) in enumerate(MUTATIONS, 1):
            doc = clean_copy()
            mutate(doc)
            code, result = run(tmp, f"mutation-{i:02d}", doc)
            hit = [e for e in result["errors"] if e.startswith(expected)]
            ok = code == 1 and bool(hit)
            print(("PASS" if ok else "FAIL"), f"{i:02d} {label}: exit {code}", hit or result["errors"])
            if not ok:
                failures.append(label)

        for label, mutate, expected in WARNINGS:
            doc = clean_copy()
            mutate(doc)
            code, result = run(tmp, "warning", doc)
            hit = [w for w in result["warnings"] if w.startswith(expected)]
            ok = code == 0 and bool(hit)
            print(("PASS" if ok else "FAIL"), f"{label}: exit {code}", hit or result["warnings"])
            if not ok:
                failures.append(label)

        for label, mutate, profile in CLEAN:
            doc = clean_copy()
            mutate(doc)
            code, result = run(tmp, "ordinary", doc, profile=profile)
            ok = code == 0 and not result["errors"]
            print(("PASS" if ok else "FAIL"), f"{label}: exit {code}", result["errors"])
            if not ok:
                failures.append(label)

        for i, (label, which, content) in enumerate(CONFIG, 1):
            target = tmp / (f"profile-{i:02d}.json" if which == "profile" else f"facts-{i:02d}.json")
            if which == "profile":
                # The broken profile extends the real base profile, so it lives in a copy of that folder.
                (tmp / "amazon-standard.json").write_text(STANDARD.read_text(encoding="utf-8"), encoding="utf-8")
            target.write_text(json.dumps(content), encoding="utf-8")
            code, result = run(tmp, "config", clean_copy(),
                               profile=target if which == "profile" else PROFILE,
                               facts=target if which == "facts" else None)
            stderr = result.get("stderr", "")
            ok = code == 2 and stderr.startswith("config error:")
            print(("PASS" if ok else "FAIL"), f"config error, {label}: exit {code}", stderr.strip())
            if not ok:
                failures.append(label)

        proc = subprocess.run([sys.executable, "-I", "-B", str(GATE), str(tmp / "clean.json"),
                               "--skeleton", str(tmp / "skeleton.json"), "--profile", str(PROFILE),
                               "--facts", str(tmp / "facts.json")], capture_output=True, text=True)
        head = proc.stdout.splitlines()[:4]
        ok = (proc.returncode == 0 and head[0].startswith("command: python3 -I -B ")
              and [h.split()[1] for h in head[2:4] if h.startswith("profile:")]
              == ["amazon-standard", "us-dietary-supplement"])
        print(("PASS" if ok else "FAIL"), "output starts with the command and the profile hashes:", head[:1])
        if not ok:
            failures.append("command and profile header")

        proc = subprocess.run([sys.executable, "-I", "-B", str(GATE), str(tmp / "clean.json"),
                               "--skeleton", str(tmp / "skeleton.json")], capture_output=True, text=True)
        ok = proc.returncode == 2
        print(("PASS" if ok else "FAIL"), "usage error without --profile and --facts: exit", proc.returncode)
        if not ok:
            failures.append("usage error")

        cosmetic_skeleton = {"frames": [{"id": "MAIN", "texts": []}, {"id": "PT01", "texts": [free("sub", "subheadline", 180)]}]}
        (tmp / "skeleton.json").write_text(json.dumps(cosmetic_skeleton), encoding="utf-8")
        cosmetic_cases = [
            ("cosmetic product fact", "Serum in a glass bottle.", 3),
            ("sourced ingredient fact", "Glycerin is a humectant.", 3),
            ("drug claim", "Promotes hair regrowth.", 1),
            ("ingredient implies product efficacy", "Glycerin grows hair.", 1),
            ("device mechanism", "Creates micro-channels for absorption.", 1),
            ("safety claim", "Painless and hypoallergenic.", 1),
            ("disease claim", "Treats eczema.", 1),
            ("health effect", "Supports blood circulation.", 1),
            ("detox", "A detox routine.", 1),
            ("result promise", "Visible results in days.", 1),
            ("testing needs approval", "Lab tested serum.", 1),
            ("free-from needs approval", "Gluten free serum.", 1),
            ("inherited Amazon ban", "The best serum.", 1),
        ]
        for label, line, expected_code in cosmetic_cases:
            doc = copy.deepcopy(cosmetic_skeleton)
            doc["frames"][1]["texts"][0]["text"] = line
            code, result = run(tmp, "cosmetic", doc, profile=COSMETIC)
            ok = code == expected_code and bool(result["errors"]) == (expected_code == 1)
            print(("PASS" if ok else "FAIL"), label, result["errors"])
            if not ok:
                failures.append(label)
        # A hold in any inherited profile survives even an approved child.
        review_cases = [
            ({"status": "draft"}, "status is draft"),
            ({"verification": "unverified"}, "verification is unverified"),
            ({"status": "draft", "verification": "unverified"}, "verification is unverified"),
        ]
        for fields, reason in review_cases:
            parent = tmp / "review-parent.json"
            parent.write_text(json.dumps({"name": "review-parent", **fields}), encoding="utf-8")
            child = tmp / "review-child.json"
            child.write_text(json.dumps({"name": "review-child", "extends": str(parent),
                                         "status": "approved", "verification": "verified"}), encoding="utf-8")
            doc = copy.deepcopy(cosmetic_skeleton)
            doc["frames"][1]["texts"][0]["text"] = "Serum in a glass bottle."
            code, result = run(tmp, "review", doc, profile=child)
            ok = (code == 3 and result["status"] == "review_required" and not result["ok"]
                  and result["review_required"] and not result["errors"]
                  and any(reason in r for r in result["review_reasons"]))
            print(("PASS" if ok else "FAIL"), "profile review hold", fields)
            if not ok:
                failures.append(f"profile review hold {fields}")
        proc = subprocess.run([sys.executable, "-I", "-B", str(GATE), str(tmp / "review.json"),
                               "--skeleton", str(tmp / "skeleton.json"), "--profile", str(COSMETIC),
                               "--facts", str(tmp / "facts.json")], capture_output=True, text=True)
        ok = (proc.returncode == 3 and "status is draft" in proc.stdout and "verification is unverified" in proc.stdout
              and "meaning-level refuter clearance and named human sign-off in claims.md" in proc.stdout)
        print(("PASS" if ok else "FAIL"), "text output explains profile review hold")
        if not ok:
            failures.append("text output explains profile review hold")
        profile = json.loads(COSMETIC.read_text(encoding="utf-8"))
        ok = profile["status"] == "draft" and profile["verification"] == "unverified" and profile["disclaimer"] is None
        print(("PASS" if ok else "FAIL"), "cosmetic profile awaits human review without supplement disclaimer")
        if not ok:
            failures.append("cosmetic review status")

    total = len(MUTATIONS) + len(WARNINGS) + len(CLEAN) + len(CONFIG) + 3 + len(cosmetic_cases) + 1 + len(review_cases) + 1
    print(f"{total - len(failures)}/{total} passed")
    if failures:
        print("FAILED:", ", ".join(failures))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
