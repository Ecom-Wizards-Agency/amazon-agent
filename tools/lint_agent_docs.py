#!/usr/bin/env python3
"""Lint the agent docs and skills for cross-agent consistency.

Checks:
1. Every skill under skills/ has a SKILL.md with `name:` + `description:`
   frontmatter (Claude discovery) and an agents/openai.yaml with
   display_name / short_description / default_prompt (Codex discovery).
2. No spaced em-dash (" -- " as em-dash) in authored surfaces. Captured
   libraries and generated files are exempt.
3. No Claude-only tool names (AskUserQuestion) inside shared skill files.
4. Every skill named in the AGENTS.md routing table resolves to a skill dir.
5. Every repo file path a doc names actually exists. A renamed tool leaves its old
   name behind in every doc that told an agent to run it, and nothing fails until
   somebody runs the command. This is the mechanical half of that.

Exit code 0 when clean, 1 when any check fails.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

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


def frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    fields = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            fields[m.group(1)] = m.group(2).strip()
    return fields


def main() -> int:
    errors: list[str] = []
    missing_paths: list[tuple[str, int, str]] = []

    # 1. Skill manifests for both agents.
    skill_dirs = sorted(d for d in (ROOT / "skills").iterdir() if d.is_dir())
    for d in skill_dirs:
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{d.relative_to(ROOT)}: missing SKILL.md")
            continue
        fm = frontmatter(skill_md)
        for key in ("name", "description"):
            if not fm.get(key):
                errors.append(f"{skill_md.relative_to(ROOT)}: frontmatter missing `{key}:`")
        if fm.get("name") and fm["name"] != d.name:
            errors.append(f"{skill_md.relative_to(ROOT)}: frontmatter name `{fm['name']}` != dir `{d.name}`")
        body = skill_md.read_text(encoding="utf-8")
        decls = re.findall(r"^Browser: (CDP|Extension|None|Mixed)\b", body, re.M)
        if len(decls) != 1:
            errors.append(
                f"{skill_md.relative_to(ROOT)}: needs exactly one `Browser: CDP|Extension|None|Mixed` line (found {len(decls)})"
            )
        oy = d / "agents" / "openai.yaml"
        if not oy.exists():
            errors.append(f"{d.relative_to(ROOT)}: missing agents/openai.yaml (invisible to Codex)")
        else:
            text = oy.read_text(encoding="utf-8")
            for key in ("display_name:", "short_description:", "default_prompt:"):
                if key not in text:
                    errors.append(f"{oy.relative_to(ROOT)}: missing `{key}`")

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

    # 4. AGENTS.md routing table names resolve to skill dirs.
    agents_md = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    routing = re.search(r"Default routing:\n(.*?)\n\n", agents_md, re.S)
    if not routing:
        errors.append("AGENTS.md: `Default routing:` block not found")
    else:
        skill_names = {d.name for d in skill_dirs}
        for name in re.findall(r"^- `([a-z0-9-]+)`:", routing.group(1), re.M):
            if name not in skill_names:
                errors.append(f"AGENTS.md routing table: `{name}` has no skills/{name}/ dir")

    if errors:
        print(f"lint_agent_docs: {len(errors)} problem(s)")
        for e in errors:
            print(f"  {e}")
        return 1
    print(f"lint_agent_docs: clean ({len(skill_dirs)} skills, {len(seen)} authored files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
