"""Versioned capability evidence, without imports from the inspected repositories."""
from __future__ import annotations

import ast
import hashlib
import json
import re
from datetime import date
from pathlib import Path

STATES = {"allowed", "approval-gated", "forbidden", "undocumented", "consent-outdated", "open"}
REPOS = {"amazon-agent", "wizards-ai", "company-ai-skills"}
GATE_FIELDS = {
    "python_symbol_contains": ("file", "symbol", "value"),
    "json_pointer_equals": ("file", "pointer", "value"),
    "json_pointer_contains": ("file", "pointer", "value"),
    "file_literal": ("file", "literal"),
    "doc_only": ("justification",),
}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows_by_id(matrix):
    return {row["id"]: row for row in matrix["rows"]}


def _date(value):
    return isinstance(value, str) and bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and date.fromisoformat(value)


def _relative(value):
    return (isinstance(value, str) and bool(value) and not Path(value).is_absolute()
            and ".." not in Path(value).parts and not value.startswith("~"))


def validate(matrix, roots=None) -> list[str]:
    """Validate evidence; roots maps repository names to checkout paths.

    By default, use this checkout and its siblings. Missing checkouts and
    unversioned vault documents are not resolved.
    """
    if roots is None:
        checkout = Path(__file__).resolve().parents[2]
        roots = {repo: checkout.parent / repo for repo in REPOS}
        roots["amazon-agent"] = checkout
    errors = []
    if not isinstance(matrix, dict):
        return ["matrix must be an object"]
    if type(matrix.get("schema_version")) is not int or matrix["schema_version"] != 1:
        errors.append("schema_version must be 1")
    try:
        if not _date(matrix.get("updated_on")):
            raise ValueError()
    except ValueError:
        errors.append("updated_on must be an ISO date")
    if not isinstance(matrix.get("rows"), list) or not matrix["rows"]:
        return errors + ["rows must be a nonempty list"]
    seen = set()
    for index, row in enumerate(matrix["rows"]):
        label = f"row {index}"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in ("id", "domain", "capability", "identity", "notes"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                errors.append(f"{label}: {key} must be a nonempty string")
        ident = row.get("id")
        if isinstance(ident, str):
            label = ident
            if ident in seen:
                errors.append(f"{label}: duplicate id")
            seen.add(ident)
        for actor in ("grimoire", "amazon_agent"):
            state = row.get(actor)
            if not isinstance(state, dict) or not isinstance(state.get("state"), str) or state["state"] not in STATES or not isinstance(state.get("how"), str) or not state["how"].strip():
                errors.append(f"{label}: invalid {actor} state/how")
        if row.get("port") not in (None, 9222, 9223) or "port" not in row:
            errors.append(f"{label}: port must be null, 9222 or 9223")
        if not isinstance(row.get("spp_rows"), list) or not all(isinstance(x, str) and x for x in row["spp_rows"]):
            errors.append(f"{label}: spp_rows must be a string list")
        for key in ("verified_on", "expires_on"):
            if key == "expires_on" and key not in row:
                continue
            try:
                if not _date(row.get(key)):
                    raise ValueError()
            except ValueError:
                errors.append(f"{label}: {key} must be an ISO date")
        for key in ("tags", "modes"):
            if key in row and (not isinstance(row[key], list) or not all(isinstance(x, str) and x for x in row[key])):
                errors.append(f"{label}: {key} must be a string list")
        docs = row.get("docs")
        if not isinstance(docs, list) or not docs:
            errors.append(f"{label}: docs must be nonempty")
        else:
            for doc in docs:
                if (not isinstance(doc, dict) or not isinstance(doc.get("repo"), str) or doc["repo"] not in REPOS | {"vault"}
                        or not _relative(doc.get("path")) or not isinstance(doc.get("note"), str) or not doc["note"].strip()):
                    errors.append(f"{label}: invalid docs entry")
                    continue
                if doc["repo"] in REPOS and doc["repo"] in roots:
                    base = Path(roots[doc["repo"]]).resolve()
                    if base.is_dir():
                        path = (base / doc["path"]).resolve()
                        if not path.is_relative_to(base) or not path.is_file():
                            errors.append(f"{label}: docs path missing or outside repository: {doc['repo']}/{doc['path']}")
        gates = row.get("gates")
        if not isinstance(gates, list) or not gates:
            errors.append(f"{label}: at least one gate is required (doc_only needs justification)")
            continue
        for gate in gates:
            if not isinstance(gate, dict) or not isinstance(gate.get("kind"), str) or gate["kind"] not in GATE_FIELDS:
                errors.append(f"{label}: unknown gate kind")
                continue
            kind = gate["kind"]
            for key in GATE_FIELDS[kind]:
                if key not in gate or (key != "value" and (not isinstance(gate[key], str) or (key != "pointer" and not gate[key].strip()))):
                    errors.append(f"{label}: {kind} needs {key}")
            if kind != "doc_only":
                if not isinstance(gate.get("repo"), str) or gate["repo"] not in REPOS or not _relative(gate.get("file")):
                    errors.append(f"{label}: gate needs repo and relative file")
                pointer = gate.get("pointer")
                if kind.startswith("json_pointer") and isinstance(pointer, str) and (pointer and not pointer.startswith("/") or re.search(r"~(?![01])", pointer)):
                    errors.append(f"{label}: invalid JSON pointer")
    return errors


def resolve_gate(root, gate) -> tuple[bool, str]:
    """Resolve a gate against {repo_name: checkout_root}, never importing code."""
    try:
        kind = gate["kind"]
        if kind == "doc_only":
            return bool(str(gate.get("justification", "")).strip()), "documented policy only"
        if kind not in GATE_FIELDS or not _relative(gate["file"]):
            return False, "invalid gate kind or path"
        base = Path(root[gate["repo"]]).resolve()
        path = (base / gate["file"]).resolve()
        if not path.is_relative_to(base):
            return False, "gate escapes repository"
        source = path.read_text(encoding="utf-8")
        if kind == "file_literal":
            ok = gate["literal"] in source
        elif kind == "python_symbol_contains":
            node = None
            for statement in ast.parse(source).body:
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target] if isinstance(statement, ast.AnnAssign) else []
                if any(isinstance(target, ast.Name) and target.id == gate["symbol"] for target in targets):
                    node = statement.value
            if isinstance(node, ast.Dict):
                values = node.keys
            elif isinstance(node, (ast.List, ast.Tuple)):
                values = node.elts
            else:
                return False, f"{gate['symbol']} is not a module-level dict/list/tuple literal"
            # Dict values can be executable references; inspect only literal keys.
            ok = any(ast.literal_eval(value) == gate["value"] for value in values)
        else:
            value = json.loads(source)
            pointer = gate["pointer"]
            if pointer and (not pointer.startswith("/") or re.search(r"~(?![01])", pointer)):
                return False, "invalid JSON pointer"
            for token in pointer.split("/")[1:] if pointer else []:
                token = token.replace("~1", "/").replace("~0", "~")
                if isinstance(value, list):
                    if not re.fullmatch(r"0|[1-9][0-9]*", token):
                        return False, "invalid array index"
                    value = value[int(token)]
                else:
                    value = value[token]
            ok = (type(value) is type(gate["value"]) and value == gate["value"]) if kind == "json_pointer_equals" else isinstance(value, (dict, list)) and gate["value"] in value
        return bool(ok), f"{gate['repo']}/{gate['file']}: {kind} {'matched' if ok else 'did not match'}"
    except (OSError, ValueError, TypeError, KeyError, IndexError, SyntaxError) as exc:
        return False, f"gate could not resolve: {exc}"


def digest(matrix) -> str:
    return hashlib.sha256(json.dumps(matrix, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def render_table(matrix) -> str:
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", "<br>")
    lines = ["| Row / capability | Grimoire | Amazon Agent | Identity / port | Evidence and notes |", "| --- | --- | --- | --- | --- |"]
    for row in matrix["rows"]:
        evidence = "; ".join(f"{d['repo']}/{d['path']}: {d['note']}" for d in row["docs"])
        notes = f"{row['notes']} Verified {row['verified_on']}."
        if row.get("expires_on"):
            notes += f" Review expires {row['expires_on']}."
        values = [f"<a id=\"{row['id']}\"></a>`{row['id']}`: {row['capability']}",
                  *[f"**{row[actor]['state']}**: {row[actor]['how']}" for actor in ("grimoire", "amazon_agent")],
                  f"{row['identity']} / {row['port'] or 'API or local'}", f"{notes} {evidence}"]
        lines.append("| " + " | ".join(cell(v) for v in values) + " |")
    return "\n".join(lines) + "\n"
