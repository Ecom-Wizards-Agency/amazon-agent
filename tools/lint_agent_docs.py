#!/usr/bin/env python3
"""Lint the agent docs and skills for cross-agent consistency.

Checks:
1. Every skill under skills/ has valid, bounded YAML discovery manifests for
   both runtimes: SKILL.md frontmatter and agents/openai.yaml UI metadata.
2. No spaced em-dash (" -- " as em-dash) in authored surfaces. Captured
   libraries and generated files are exempt.
3. No Claude-only tool names (AskUserQuestion) inside shared skill files.
4. Every skill named in the AGENTS.md routing table resolves to a skill dir.
5. Every repo file path a doc names actually exists. A renamed tool leaves its old
   name behind in every doc that told an agent to run it, and nothing fails until
   somebody runs the command. This is the mechanical half of that.
6. Browser priority, the DataDive CDP route, and local-artifact handoff
   invariants remain explicit.

Exit code 0 when clean, 1 when any check fails.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EM_DASH = " — "

# Authored surfaces for the writing-style check.
AUTHORED_GLOBS = [
    "AGENTS.md",
    "README.md",
    "CLAUDE.md",
    "skills/**/*.md",
    "skills/**/*.yaml",
    "docs/*.md",
    ".claude/commands/*.md",
    "sop-drafts/*.md",
    "sop-updates/*.md",
    "tools/**/*.md",
]

# Generated or captured content inside the authored globs: exempt.
EXEMPT_PARTS = [
    "skills/amazon-seo/references/datadive-support/",
    # Temporary: em-dash sweep deferred while the branding-doc rework is in
    # flight in the operator's working tree (2026-07-15). Remove once swept.
    "tools/amazon-ad-audit/",
    # Third-party dependencies. Our house writing style does not apply to somebody
    # else's README, and an installed package can put thousands of them in the tree.
    "node_modules/",
]

CLAUDE_ONLY_TOOLS = ["AskUserQuestion"]

MAX_SKILL_NAME_LENGTH = 64
MAX_SKILL_DESCRIPTION_LENGTH = 300
MIN_UI_SHORT_DESCRIPTION_LENGTH = 25
MAX_UI_SHORT_DESCRIPTION_LENGTH = 64
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_SKILL_FRONTMATTER = {"name", "description", "license", "allowed-tools", "metadata"}

TABLE_NULL_CELL = re.compile(r"\|\s*—\s*\|")
INLINE_CODE = re.compile(r"`[^`]*`")

# Check 5. Only paths that are unambiguously a real file in THIS repo: rooted in a
# tracked source directory, carrying a real extension, and free of placeholders. The
# gitignored trees (output/, downloads/, evidence/, _local/) are deliberately absent,
# because a doc naming `output/{client}/seo/` is describing a shape, not a file.
CHECKED_ROOTS = ("tools/", "skills/", "docs/", ".claude/", "sop-drafts/", "sop-updates/")
CHECKED_EXTS = (".py", ".md", ".mjs", ".js", ".json", ".sh", ".ps1", ".yaml", ".yml")
# A path written with any of these is a template or a glob, not a file to resolve.
PLACEHOLDER = re.compile(r"[{}<>*$\[\]]")
# Prefixes a doc may use when writing the same path from somewhere else.
PATH_PREFIXES = ("~/os/amazon-agent/", "amazon-agent/", "./")
TRIM = ".,;:!?)]'\"`"

# Files whose whole job is to describe the past. A change log naming a file that was
# deliberately deleted is correct, and rewriting it to satisfy a check would make it
# lie. Same principle the vault linter uses to exclude its decision records.
PATH_CHECK_EXEMPT = ("docs/public-release-checklist.md",)

DATADIVE_ROUTE_REQUIREMENTS = {
    "AGENTS.md": "DataDive web app navigation, read-only endpoint fetches, downloads, and",
    "docs/browser-routing-map.md": (
        '| DataDive full keyword pool (the old "Expanded 1% MKL") | '
        "`amazon-seo` | CDP (9222) |"
    ),
    "skills/amazon-seo/references/keyword-research-workbook.md": (
        "logged-in DataDive session through managed Chrome CDP on port 9222"
    ),
}

DATADIVE_STALE_ROUTES = {
    "AGENTS.md": "DataDive is the standing example",
    "docs/browser-routing-map.md": (
        '| DataDive full keyword pool (the old "Expanded 1% MKL") | '
        " `amazon-seo` | Extension |"
    ),
    "skills/amazon-seo/references/keyword-research-workbook.md": (
        "full keyword pool uses three read-only DataDive endpoints in the extension browser"
    ),
}


def validate_datadive_routing(root: Path = ROOT) -> list[str]:
    """Keep DataDive web work on Evo X1's managed port-9222 browser."""
    errors: list[str] = []
    for rel, required in DATADIVE_ROUTE_REQUIREMENTS.items():
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: missing DataDive routing authority")
            continue
        text = path.read_text(encoding="utf-8")
        if required not in text:
            errors.append(f"{rel}: missing required DataDive CDP routing contract")
        stale = DATADIVE_STALE_ROUTES.get(rel)
        if stale and stale in text:
            errors.append(f"{rel}: contains stale DataDive extension-default route")
    return errors


def git_ignored(paths: set[str]) -> set[str]:
    """Of `paths`, the ones git ignores.

    A gitignored path is per-operator (`config.<client>.json`) or built at runtime, so
    it is absent on a clean checkout by design and a doc may still name it.
    """
    if not paths:
        return set()
    try:
        proc = subprocess.run(["git", "check-ignore", "--stdin"], cwd=ROOT, text=True,
                              input="\n".join(sorted(paths)), capture_output=True)
    except (OSError, subprocess.SubprocessError):
        return set()  # no git here: check every path rather than skipping silently
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def referenced_paths(path: Path) -> list[tuple[int, str]]:
    """Repo-relative file paths a document names, with their line numbers."""
    found = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for raw in line.replace("`", " ").split():
            token = raw.strip(TRIM)
            for prefix in PATH_PREFIXES:
                if token.startswith(prefix):
                    token = token[len(prefix):]
                    break
            if PLACEHOLDER.search(token):
                continue
            if not token.startswith(CHECKED_ROOTS) or not token.endswith(CHECKED_EXTS):
                continue
            found.append((lineno, token))
    return found


def em_dash_violations(path: Path) -> list[int]:
    hits = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        # Literal artifact labels / legacy syntax quoted in inline code are allowed.
        stripped = INLINE_CODE.sub("", line)
        if EM_DASH not in stripped:
            continue
        if f'("{EM_DASH}")' in stripped:  # the writing-style rule quoting itself
            continue
        if TABLE_NULL_CELL.search(stripped):  # "—" as an empty/null table marker
            continue
        hits.append(lineno)
    return hits


def load_yaml_mapping(text: str, label: str) -> tuple[dict | None, str | None]:
    """Parse one YAML document and return a useful lint error instead of raising."""
    try:
        parsed = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, f"{label}: invalid YAML: {exc}"
    if not isinstance(parsed, dict):
        return None, f"{label}: YAML document must be a mapping"
    return parsed, None


def load_skill_frontmatter(path: Path) -> tuple[dict | None, str, str | None]:
    """Return parsed frontmatter, its raw text, and an optional error."""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---(?:\n|$)", content, re.S)
    if not match:
        return None, "", f"{path}: missing or malformed YAML frontmatter"
    raw = match.group(1)
    parsed, error = load_yaml_mapping(raw, str(path))
    return parsed, raw, error


def yaml_scalar_is_quoted(raw: str, key: str) -> bool:
    """The maintained manifests use one-line quoted strings for stable parsing."""
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", raw, re.M)
    if not match:
        return False
    value = match.group(1).lstrip()
    return value.startswith(('"', "'"))


def validate_skill_directory(skill_dir: Path) -> list[str]:
    """Validate both discovery manifests and the shared Browser declaration."""
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"{skill_dir}: missing SKILL.md"]

    fm, raw_frontmatter, fm_error = load_skill_frontmatter(skill_md)
    if fm_error:
        errors.append(fm_error)
        fm = {}

    unexpected = set(fm) - ALLOWED_SKILL_FRONTMATTER
    if unexpected:
        errors.append(
            f"{skill_md}: unexpected frontmatter keys: {', '.join(sorted(unexpected))}"
        )

    name = fm.get("name")
    if not isinstance(name, str) or not name:
        errors.append(f"{skill_md}: frontmatter `name` must be a non-empty string")
        name = skill_dir.name
    else:
        if name != skill_dir.name:
            errors.append(f"{skill_md}: frontmatter name `{name}` != dir `{skill_dir.name}`")
        if len(name) > MAX_SKILL_NAME_LENGTH or not SKILL_NAME.fullmatch(name):
            errors.append(
                f"{skill_md}: name must be hyphen-case and at most {MAX_SKILL_NAME_LENGTH} characters"
            )

    description = fm.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(f"{skill_md}: frontmatter `description` must be a non-empty string")
    else:
        if len(description) > MAX_SKILL_DESCRIPTION_LENGTH:
            errors.append(
                f"{skill_md}: description is {len(description)} characters; maximum is "
                f"{MAX_SKILL_DESCRIPTION_LENGTH}"
            )
        if "<" in description or ">" in description:
            errors.append(f"{skill_md}: description cannot contain angle brackets")
        if not yaml_scalar_is_quoted(raw_frontmatter, "description"):
            errors.append(f"{skill_md}: description must be a quoted one-line YAML string")

    body = skill_md.read_text(encoding="utf-8")
    decls = re.findall(r"^Browser: (CDP|Extension|None|Mixed)\b", body, re.M)
    if len(decls) != 1:
        errors.append(
            f"{skill_md}: needs exactly one `Browser: CDP|Extension|None|Mixed` line "
            f"(found {len(decls)})"
        )

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        errors.append(f"{skill_dir}: missing agents/openai.yaml (invisible to Codex)")
        return errors

    raw_openai = openai_yaml.read_text(encoding="utf-8")
    openai, openai_error = load_yaml_mapping(raw_openai, str(openai_yaml))
    if openai_error:
        errors.append(openai_error)
        return errors
    interface = openai.get("interface")
    if not isinstance(interface, dict):
        errors.append(f"{openai_yaml}: `interface` must be a mapping")
        return errors

    for key in ("display_name", "short_description", "default_prompt"):
        value = interface.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{openai_yaml}: `interface.{key}` must be a non-empty string")

    short_description = interface.get("short_description")
    if isinstance(short_description, str) and not (
        MIN_UI_SHORT_DESCRIPTION_LENGTH
        <= len(short_description)
        <= MAX_UI_SHORT_DESCRIPTION_LENGTH
    ):
        errors.append(
            f"{openai_yaml}: short_description is {len(short_description)} characters; "
            f"expected {MIN_UI_SHORT_DESCRIPTION_LENGTH}-{MAX_UI_SHORT_DESCRIPTION_LENGTH}"
        )

    default_prompt = interface.get("default_prompt")
    if isinstance(default_prompt, str) and f"${name}" not in default_prompt:
        errors.append(f"{openai_yaml}: default_prompt must mention `${name}` exactly")

    for key in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^\s*{key}:\s*[\"']", raw_openai, re.M):
            errors.append(f"{openai_yaml}: `{key}` must be a quoted YAML string")

    return errors


def main() -> int:
    errors: list[str] = []
    missing_paths: list[tuple[str, int, str]] = []

    errors.extend(validate_datadive_routing())

    # 1. Skill manifests for both agents.
    skill_dirs = sorted(d for d in (ROOT / "skills").iterdir() if d.is_dir())
    for d in skill_dirs:
        errors.extend(validate_skill_directory(d))

    # 2 + 3. Writing style and Claude-only tool names.
    seen: set[Path] = set()
    for pattern in AUTHORED_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            rel = str(path.relative_to(ROOT))
            if any(part in rel for part in EXEMPT_PARTS):
                continue
            for lineno in em_dash_violations(path):
                errors.append(f"{rel}:{lineno}: spaced em-dash (rewrite the sentence)")
            if rel.startswith("skills/"):
                for tool in CLAUDE_ONLY_TOOLS:
                    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                        if tool in line:
                            errors.append(f"{rel}:{lineno}: Claude-only tool `{tool}` in a shared skill file")
            # 5. Paths that name a file in this repo have to resolve. Collected now,
            # judged in one pass below so git is consulted once rather than per path.
            if rel not in PATH_CHECK_EXEMPT:
                for lineno, ref in referenced_paths(path):
                    if not (ROOT / ref).exists():
                        missing_paths.append((rel, lineno, ref))

    ignored = git_ignored({ref for _, _, ref in missing_paths})
    for rel, lineno, ref in missing_paths:
        if ref not in ignored:
            errors.append(f"{rel}:{lineno}: names `{ref}`, which does not exist")

    # 6. No personal machine identity in tracked files. A committed
    # /Users/<name>/ path publishes who ran the tool and breaks on every other
    # machine; the public-release checklist demands neither ever happens. A
    # path spelled with a <placeholder> is describing the rule, not leaking.
    try:
        tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, text=True,
                                 capture_output=True, check=True).stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        tracked = []
    for rel in tracked:
        if rel in PATH_CHECK_EXEMPT or rel == "tools/lint_agent_docs.py":
            continue
        if not rel.endswith((".py", ".md", ".mjs", ".js", ".json", ".sh",
                             ".ps1", ".yaml", ".yml")):
            continue
        try:
            lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(lines, 1):
            # /Users/<name> and /Users/{name} are placeholders describing the
            # rule; /Users/ followed by a real username segment is a leak. The
            # earlier "line contains a brace" exemption let a JSON fixture
            # carry a personal path straight past this check (12.08.2026).
            if re.search(r"/Users/[A-Za-z0-9._-]+/", line):
                errors.append(f"{rel}:{lineno}: personal absolute path "
                              "(/Users/...); resolve through ew_paths, a "
                              "pointer file, or ~ instead")

    # 7. No untracked-and-unignored top-level directory. That state is one
    # `git add -A` away from committing client work to a public remote; .tmp/
    # sat that way for weeks before 12.08.2026. New work goes in a sanctioned
    # scratch root or gets an explicit .gitignore entry in the same change.
    try:
        status = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                                text=True, capture_output=True, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        status = ""
    for line in status.splitlines():
        if line.startswith("?? "):
            entry = line[3:]
            if entry.endswith("/") and entry.count("/") == 1:
                errors.append(f"{entry}: untracked top-level directory that is "
                              "not gitignored; move the contents to a "
                              "sanctioned scratch root or gitignore it")

    # 4. AGENTS.md routing table names resolve to skill dirs.
    agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    required_operating_rules = (
        "Managed Chrome CDP on port 9222 is the default browser",
        "Port 9223 is the separate Wizards AI browser",
        "The T3 Code in-app browser is not a first-choice browser",
        "Verified weekly cleanup is the sole permitted",
    )
    for rule in required_operating_rules:
        if rule not in agents_md:
            errors.append(f"AGENTS.md: missing operating invariant `{rule}`")
    routing = re.search(
        r"^Default routing:\s*\n(.*?)(?=^Operational-check trigger phrases:)",
        agents_md,
        re.S | re.M,
    )
    if not routing:
        errors.append("AGENTS.md: `Default routing:` block not found")
    else:
        skill_names = {d.name for d in skill_dirs}
        routed_names = re.findall(r"^- `([a-z0-9-]+)`:", routing.group(1), re.M)
        for name in sorted(set(routed_names) - skill_names):
            errors.append(f"AGENTS.md routing table: `{name}` has no skills/{name}/ dir")
        for name in sorted(skill_names - set(routed_names)):
            errors.append(f"AGENTS.md routing table: missing `{name}`")
        for name in sorted({name for name in routed_names if routed_names.count(name) > 1}):
            errors.append(f"AGENTS.md routing table: duplicate `{name}`")

    if errors:
        print(f"lint_agent_docs: {len(errors)} problem(s)")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"lint_agent_docs: clean ({len(skill_dirs)} skills, {len(seen)} authored files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
