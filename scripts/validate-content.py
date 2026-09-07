#!/usr/bin/env python3
"""Validate Forge content-pack invariants without external dependencies."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "forge"

MEMORY_FIRST_MARKERS = {
    PLUGIN / "skills" / "forge-core" / "SKILL.md": (
        "Read only `.forge/INTENT.md` and `.forge/MISSION.md`",
        "act directly or select one useful profile",
        (
            "There is no automatic delegation, review artifact, fixed role "
            "chain, preflight, gate ladder, Loop, or Assurance."
        ),
        "Do not enter Loop automatically",
        "Assurance is also explicit",
        "targeted check and broaden only when justified",
        "Only the host writes active control memory",
        (
            "Checkpoint a user-confirmed outcome or boundary change, visible "
            "delivery, pause, completion, or Mission replacement."
        ),
        (
            "No mode, profile, or workflow choice grants permission for "
            "external side effects."
        ),
        "Do not report Mission completion until post-write validation passes.",
    ),
    PLUGIN / "skills" / "forge-memory" / "SKILL.md": (
        "Only the host agent writes active control memory",
        "one of `ready`, `working`, `blocked`, `paused`, or `done`",
        "Checkpoint only a real transition:",
        (
            "1. the user confirms or changes a decision, Outcome, Scope, or "
            "Success Criteria;"
        ),
        "2. a visible delivery increment completes;",
        "3. work pauses or transfers;",
        "4. the active mission completes;",
        "5. the active mission is replaced.",
        "Do not checkpoint each tool call, edit, test, or internal step.",
        "Use `forge-compact`",
        "Archive is not loaded by default",
        "These are exact wire-format tokens, not prose",
        "`completed` is invalid",
        "`forge-checkpoint PROJECT_ROOT --state done`",
        "After every active-memory write, run `forge-memory-validate`",
        "Do not report a checkpoint or completion until validation passes",
        "External recall is deferred",
        "recall can never become canonical",
    ),
    ROOT / "AGENTS.md": (
        "ordinary tasks directly",
        "five checkpoint transitions",
        "Loop or Assurance only when the user explicitly invokes or requests it",
        "未经用户明确指示，禁止执行 `git commit`",
        "未经用户明确指示，禁止执行 `git push`",
    ),
    ROOT / ".cursorrules": (
        "ordinary tasks directly",
        "five checkpoint transitions",
        "Only the host writes active control memory",
        "Loop and Assurance start only when the user explicitly invokes or requests",
        "不执行 commit 或 push",
    ),
}

FORBIDDEN_DEFAULT_MARKERS = {
    PLUGIN / "skills" / "forge-core" / "SKILL.md": (
        "spawn subagent",
        "Acceptance Contract",
        "Validation Ladder",
        "Role selection & rationale",
        "写入 `.forge/reviews/",
    ),
    PLUGIN / "skills" / "forge-memory" / "SKILL.md": (
        "forge-team 独占",
        "角色 subagent",
        "每个 role/path",
        "expectations/",
        "reviews/<feature>",
    ),
    ROOT / "AGENTS.md": (
        "固定独立角色",
        "fixed independent",
        "fresh full gates",
        "写入 .forge/reviews/",
    ),
    ROOT / ".cursorrules": (
        "按角色规则实现",
        "写入 .forge/reviews/",
        "每次任务自动跑",
    ),
}

ACTIVE_AUTHORITY_PATHS = tuple(MEMORY_FIRST_MARKERS)

CAPABILITY_PROFILES = {
    "forge-scout",
    "forge-builder",
    "forge-checker",
}
CAPABILITY_PROFILE_ALIASES = {
    "forge-auditor",
    "forge-engineer",
    "forge-researcher",
}
LEGACY_ROLE_SKILLS = {
    "forge-pm",
    "forge-architect",
    "forge-designer",
    "forge-developer",
    "forge-tester",
    "forge-reviewer",
    "forge-security-reviewer",
    "forge-team",
    "forge-quality",
}
LEGACY_ROLE_TEMPLATES = {
    "design.md",
    "design-ui.md",
    "expectations.md",
    "review-finding.md",
    "review-security.md",
    "test-plan.md",
    "verification.md",
    "verification-report.md",
}
PROFILE_MARKERS = {
    PLUGIN / "skills" / "forge-scout" / "SKILL.md": (
        "temporary capability profile",
        "selected by the host for the task",
        "not a permanent team",
        "not a mandatory chain",
        "Core remains the direct default",
        "read-only discovery and research",
        "Do not edit product, tests, or configuration",
        "Do not write active memory",
        "findings and their provenance",
        "agent-return.md",
    ),
    PLUGIN / "skills" / "forge-builder" / "SKILL.md": (
        "temporary capability profile",
        "selected by the host for the task",
        "not a permanent team",
        "not a mandatory chain",
        "Core remains the direct default",
        "only within the declared write scope",
        "targeted tests",
        "Never write `.forge/INTENT.md` or `.forge/MISSION.md`",
        "Never self-approve",
        "Never invoke or delegate to another profile",
        "changed files",
        "checks",
        "unresolved",
        "agent-return.md",
    ),
    PLUGIN / "skills" / "forge-checker" / "SKILL.md": (
        "temporary capability profile",
        "selected by the host for the task",
        "not a permanent team",
        "not a mandatory chain",
        "Core remains the direct default",
        "checks and attacks only",
        "read-only on the product under check",
        "claim-scoped pass or fail",
        "reproducible evidence",
        "Do not make repair edits",
        "Do not write active memory",
        "The host decides follow-up actions",
        "agent-return.md",
    ),
    PLUGIN / "templates" / "agent-return.md": (
        "## Summary",
        "## Evidence and exact command outcomes",
        "## Files or areas inspected or changed",
        "## Unknowns and risks",
        "## Recommended next action",
    ),
}

_COMMON_PROFILE_AUTHORITY_ACTIONS = (
    (
        "active-memory write",
        r"(?:write|edit|modify)\s+(?:the\s+)?active(?:\s+control)?\s+memory",
    ),
    ("self-approval", r"self[- ]approve"),
    ("self-integration", r"self[- ]integrate"),
)
PROFILE_AUTHORITY_ACTIONS = {
    "forge-scout": (
        (
            "product/test/config write",
            r"(?:write|edit|modify)\s+(?:product|tests?|configuration|config)\b",
        ),
        (
            "nested profile delegation",
            r"(?:delegate(?:\s+to)?|invoke)\s+(?:another\s+|a\s+)?profile\b",
        ),
        *_COMMON_PROFILE_AUTHORITY_ACTIONS,
    ),
    "forge-builder": (
        (
            "nested profile delegation",
            r"(?:delegate(?:\s+to)?|invoke)\s+(?:another\s+|a\s+)?profile\b",
        ),
        *_COMMON_PROFILE_AUTHORITY_ACTIONS,
    ),
    "forge-checker": (
        (
            "repair or write",
            (
                r"(?:repair\s+edits?|(?:repair|edit|write|modify)"
                r"(?:\s+(?:product|tests?|configuration|config|code|files?))?)\b"
            ),
        ),
        *_COMMON_PROFILE_AUTHORITY_ACTIONS,
    ),
}
_AUTHORITY_GRANT_PHRASE = (
    r"(?:can|may|shall|(?:is|are)\s+(?:allowed|permitted|authorized)\s+to|"
    r"has\s+permission\s+to)"
)


def _profile_authority_grants(profile: str, text: str) -> list[str]:
    """Return affirmative grants that contradict a temporary profile."""
    normalized = _normalized_prose(text)
    grants: list[str] = []
    for label, action in PROFILE_AUTHORITY_ACTIONS.get(profile, ()):
        modal_before_action = re.compile(
            rf"\b{_AUTHORITY_GRANT_PHRASE}\s+{action}",
            re.IGNORECASE,
        )
        action_before_permission = re.compile(
            rf"\b{action}\s+(?:(?:is|are)|(?:can|may)\s+be)\s+"
            r"(?:allowed|permitted)\b",
            re.IGNORECASE,
        )
        if (
            modal_before_action.search(normalized)
            or action_before_permission.search(normalized)
        ):
            grants.append(label)
    return grants


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _normalized_prose(text: str) -> str:
    return " ".join(text.split())


def _validate_exact_frontmatter(
    root: Path,
    path: Path,
    expected: dict[str, str | None],
) -> list[str]:
    relative = _relative(root, path)
    text = path.read_text(encoding="utf-8")
    match = re.match(
        r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n",
        text,
        re.DOTALL,
    )
    if not match:
        return [f"invalid frontmatter block: {relative}"]
    values: dict[str, str] = {}
    keys: list[str] = []
    errors: list[str] = []
    for line in match.group(1).splitlines():
        if ":" not in line:
            errors.append(f"invalid frontmatter line in {relative}: {line!r}")
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        keys.append(key)
        if key in values:
            errors.append(f"duplicate frontmatter key {key!r}: {relative}")
            continue
        raw = value.strip()
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            errors.append(
                f"frontmatter value must be a JSON double-quoted scalar "
                f"for {key!r}: {relative}"
            )
            continue
        if not isinstance(parsed, str):
            errors.append(
                f"frontmatter value must decode to a string "
                f"for {key!r}: {relative}"
            )
            continue
        values[key] = parsed
    if set(keys) != set(expected) or len(keys) != len(expected):
        errors.append(
            "frontmatter keys must be exactly "
            f"{sorted(expected)}: {relative}"
        )
    for key, expected_value in expected.items():
        if key not in values:
            continue
        if expected_value is None and not values[key]:
            errors.append(
                f"frontmatter value for {key!r} must be nonempty: {relative}"
            )
        elif expected_value is not None and values[key] != expected_value:
            errors.append(
                f"invalid frontmatter value for {key!r}: {relative}"
            )
    return errors


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _name_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", value.lower())
        if token
    }


def _source_names(tree: ast.AST) -> tuple[set[str], set[str], list[str]]:
    imports: set[str] = set()
    names: set[str] = set()
    strings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0].lower() for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0].lower())
            names.update(alias.name.lower() for alias in node.names)
        elif isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            names.add(node.attr.lower())
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name.lower())
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append(node.value.lower())
    return imports, names, strings


def _import_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                local = alias.asname or alias.name.split(".", 1)[0]
                aliases[local] = alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            for alias in node.names:
                local = alias.asname or alias.name
                aliases[local] = f"{node.module}.{alias.name}"
    return aliases


def _qualified_name(node: ast.expr, aliases: dict[str, str]) -> str | None:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if not isinstance(node, ast.Attribute):
        return None
    parent = _qualified_name(node.value, aliases)
    return f"{parent}.{node.attr}" if parent else None


def _qualified_call(node: ast.Call, aliases: dict[str, str]) -> str | None:
    return _qualified_name(node.func, aliases)


def _open_is_write_capable(
    node: ast.Call, aliases: dict[str, str]
) -> bool:
    qualified = _qualified_call(node, aliases)
    attribute_open = (
        isinstance(node.func, ast.Attribute) and node.func.attr == "open"
    )
    builtin_open = qualified in {"open", "builtins.open"}
    if not attribute_open and not builtin_open:
        return False

    positional_index = 1 if builtin_open else 0
    mode_node = next(
        (
            keyword.value
            for keyword in node.keywords
            if keyword.arg == "mode"
        ),
        node.args[positional_index]
        if len(node.args) > positional_index
        else None,
    )
    if mode_node is None:
        return False
    if not (
        isinstance(mode_node, ast.Constant)
        and isinstance(mode_node.value, str)
    ):
        return True
    return any(marker in mode_node.value for marker in "wax+")


def _validate_recovery_source(
    root: Path, path: Path, *, allow_file_fsync: bool = False
) -> list[str]:
    relative = _relative(root, path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    except (OSError, SyntaxError, UnicodeError) as error:
        return [f"cannot inspect product source {relative}: {error}"]
    imports, names, strings = _source_names(tree)
    aliases = _import_aliases(tree)
    tokens = set().union(*(_name_tokens(name) for name in names))
    errors: list[str] = []

    journal_machinery = (
        "journal" in tokens
        or any(
            re.search(r"(?:transaction.*\.json|journal.*\.json)", value)
            for value in strings
        )
    )
    if journal_machinery:
        errors.append(f"transaction journal machinery is forbidden: {relative}")
    phase_machinery = any(
        {"transaction", "phase"} <= _name_tokens(value)
        for value in (*names, *strings)
    ) or (
        journal_machinery
        and any("phase" in _name_tokens(value) for value in (*names, *strings))
    )
    if phase_machinery:
        errors.append(f"transaction phase machinery is forbidden: {relative}")
    if (
        "hashlib" in imports
        or {"digest", "hexdigest"} & tokens
        or any(re.fullmatch(r"sha(?:1|224|256|384|512)", token) for token in tokens)
    ):
        errors.append(f"digest integrity machinery is forbidden: {relative}")
    if "ctypes" in imports or "flushfilebuffers" in names:
        errors.append(f"directory flush machinery is forbidden: {relative}")
    invalid_fsync = any(
        _qualified_call(node, aliases) == "os.fsync"
        and not (
            allow_file_fsync
            and len(node.args) == 1
            and isinstance(node.args[0], ast.Call)
            and isinstance(node.args[0].func, ast.Attribute)
            and node.args[0].func.attr == "fileno"
        )
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
    )
    if invalid_fsync:
        errors.append(
            "directory flush machinery is forbidden; os.fsync is allowed only "
            f"for an open file in plugins/forge/lib/forge_files.py: {relative}"
        )
    if (
        {"threading", "multiprocessing", "concurrent", "fcntl", "msvcrt"} & imports
        or {"lock", "locking", "flock", "mutex", "semaphore", "concurrency"}
        & tokens
    ):
        errors.append(f"lock/concurrency enforcement is forbidden: {relative}")
    return errors


def _validate_shared_write_owner(root: Path, path: Path) -> list[str]:
    relative = _relative(root, path)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
    except (OSError, SyntaxError, UnicodeError) as error:
        return [f"cannot inspect product source {relative}: {error}"]
    aliases = _import_aliases(tree)
    imports_atomic_write = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "forge_files"
        and any(alias.name == "atomic_write" for alias in node.names)
        for node in ast.walk(tree)
    )
    errors: list[str] = []
    if not imports_atomic_write:
        errors.append(f"managed writes must reuse forge_files.atomic_write: {relative}")

    primitives: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        qualified = _qualified_call(node, aliases)
        if qualified in {"os.replace", "tempfile.mkstemp"}:
            primitives.add(qualified)
        if isinstance(node.func, ast.Attribute) and node.func.attr in {
            "write_bytes",
            "write_text",
        }:
            primitives.add(f"Path.{node.func.attr}")
        if _open_is_write_capable(node, aliases):
            primitives.add("open(write-capable mode)")
    for primitive in sorted(primitives):
        errors.append(
            f"independent managed-write primitive {primitive} is forbidden; "
            f"reuse forge_files.atomic_write: {relative}"
        )
    return errors


def validate_product_scope(root: Path) -> list[str]:
    """Validate shipped Memory-First inventory and anti-complexity boundaries."""
    plugin = root / "plugins" / "forge"
    errors: list[str] = []
    obsolete_paths = (
        root / "install.sh",
        plugin / "scripts" / "forge-migrate",
        plugin / "scripts" / "validate-intent",
        plugin / "docs" / "DOCTRINE.md",
        plugin / "docs" / "AGENTS-BRIDGE.md",
        root / "tests" / "fixtures" / "legacy_forge",
        root / "docs" / "archive",
        root / "docs" / "superpowers",
        root / "docs" / "dogfood",
        root / "scripts" / "summarize-memory-first-dogfood.py",
    )
    for path in obsolete_paths:
        if path.exists():
            errors.append(
                "obsolete compatibility/history surface is forbidden: "
                f"{_relative(root, path)}"
            )

    forbidden_surfaces = {"runtime", "ledger", "scheduler"}
    workflow_policy = plugin / "scripts" / "forge-workflow-policy"
    if workflow_policy.exists():
        errors.append(
            "runtime workflow policy is forbidden: "
            f"{_relative(root, workflow_policy)}"
        )
    for name in ("forge-index", "forge-history"):
        obsolete_script = plugin / "scripts" / name
        if obsolete_script.exists():
            errors.append(
                "legacy database/reporting script is forbidden: "
                f"{_relative(root, obsolete_script)}"
            )
    obsolete_obligations = plugin / "workflow-obligations.json"
    if obsolete_obligations.is_file():
        errors.append(
            "obsolete fixed-workflow surface is forbidden: "
            f"{_relative(root, obsolete_obligations)}"
        )

    skills = plugin / "skills"
    for skill_file in sorted(skills.glob("*/SKILL.md")):
        name = skill_file.parent.name
        text = skill_file.read_text(encoding="utf-8")
        header = text.split("---", 2)[1].lower() if text.startswith("---\n") else ""
        profile_like = (
            "capability profile" in header
            or re.search(r"\b(?:role|profile) alias\b", header) is not None
        )
        if (
            name not in CAPABILITY_PROFILES
            and (
                name in CAPABILITY_PROFILE_ALIASES
                or profile_like
            )
        ):
            errors.append(
                "unsupported capability or role skill alias: "
                f"{_relative(root, skill_file)}"
            )
    for name in sorted(LEGACY_ROLE_SKILLS):
        path = skills / name
        if any(item.is_file() for item in path.rglob("*")):
            errors.append(
                f"legacy role skill is forbidden: {_relative(root, path)}"
            )

    allowed_wrappers = {
        *(f"agents/{name}.md" for name in CAPABILITY_PROFILES),
        *(f"agent-defs/codex/{name}.toml" for name in CAPABILITY_PROFILES),
        *(f"agent-defs/cursor/{name}.md" for name in CAPABILITY_PROFILES),
    }
    actual_wrappers = {
        _relative(plugin, path)
        for directory_name in ("agents", "agent-defs")
        for path in (plugin / directory_name).rglob("*")
        if path.is_file()
    }
    for relative in sorted(actual_wrappers - allowed_wrappers):
        errors.append(f"unsupported agent wrapper: plugins/forge/{relative}")
    for relative in sorted(allowed_wrappers - actual_wrappers):
        errors.append(f"required agent wrapper is missing: plugins/forge/{relative}")

    for name in sorted(LEGACY_ROLE_TEMPLATES):
        path = plugin / "templates" / name
        if path.exists():
            errors.append(
                f"legacy role template is forbidden: {_relative(root, path)}"
            )
    role_guide = plugin / "docs" / "ROLE_GUIDE.md"
    if role_guide.exists():
        errors.append(
            f"legacy role guide is forbidden: {_relative(root, role_guide)}"
        )

    for path in sorted(plugin.rglob("*")):
        if not path.is_file():
            continue
        relative = _relative(root, path)
        if path.is_relative_to(plugin / "docs"):
            continue
        normalized = relative.lower().replace("_", "-")
        tokens = _name_tokens(normalized)
        surface = next(
            (
                name
                for name in sorted(forbidden_surfaces)
                if name in tokens
            ),
            None,
        )
        if surface is None and "control-plane" in normalized:
            surface = "control-plane"
        if surface is not None:
            errors.append(
                f"forbidden {surface} product surface: {relative}"
            )
        if "policy" in tokens:
            errors.append(
                f"policy runtime surface is forbidden: {relative}"
            )

    limits = {"forge-compact": 250}
    for name, maximum in limits.items():
        path = plugin / "scripts" / name
        relative = _relative(root, path)
        lines = len(path.read_text(encoding="utf-8").splitlines())
        if lines > maximum:
            errors.append(
                f"production LOC limit exceeded ({lines} > {maximum}): {relative}"
            )
        errors.extend(_validate_recovery_source(root, path))

    helper = plugin / "lib" / "forge_files.py"
    errors.extend(
        _validate_recovery_source(root, helper, allow_file_fsync=True)
    )
    for name in ("forge-init", "forge-checkpoint"):
        errors.extend(
            _validate_shared_write_owner(root, plugin / "scripts" / name)
        )
    return errors


def validate() -> list[str]:
    errors = validate_product_scope(ROOT)

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if (
        version != "0.0.0"
        and f"## [{version}]"
        not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    ):
        fail(errors, f"CHANGELOG entry is missing for VERSION {version}")
    for relative in (
        "plugins/forge/.claude-plugin/plugin.json",
        "plugins/forge/.codex-plugin/plugin.json",
        "plugins/forge/.cursor-plugin/plugin.json",
        "package.json",
        "packages/deepseek-harness/package.json",
    ):
        path = ROOT / relative
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if manifest.get("version") != version:
            fail(errors, f"version mismatch: {relative} != VERSION {version}")

    for relative in (
        ".claude-plugin/marketplace.json",
        ".agents/plugins/marketplace.json",
        ".cursor-plugin/marketplace.json",
    ):
        path = ROOT / relative
        try:
            marketplace = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            fail(errors, f"invalid marketplace JSON: {relative}: {error}")
            continue
        plugins = marketplace.get("plugins")
        if not isinstance(plugins, list) or not plugins:
            fail(errors, f"marketplace plugins list is invalid: {relative}")
            continue
        for entry in plugins:
            source = entry.get("source") if isinstance(entry, dict) else None
            if isinstance(source, dict):
                source = source.get("path")
            if not isinstance(source, str):
                fail(errors, f"marketplace source is invalid: {relative}")
                continue
            target = (ROOT / source).resolve()
            if target != PLUGIN.resolve() or not target.is_dir():
                fail(errors, f"marketplace source does not exist: {relative}: {source}")

    for skill_file in sorted((PLUGIN / "skills").glob("*/SKILL.md")):
        text = skill_file.read_text(encoding="utf-8")
        folder_name = skill_file.parent.name
        name_lines = {
            f"name: {folder_name}",
            f'name: "{folder_name}"',
        }
        frontmatter_lines = (
            set(text.split("---", 2)[1].splitlines())
            if text.startswith("---\n")
            else set()
        )
        if not name_lines & frontmatter_lines:
            fail(errors, f"invalid skill frontmatter name: {skill_file}")
        line_count = len(text.splitlines())
        if line_count >= 500:
            fail(errors, f"skill exceeds 499 lines: {skill_file} ({line_count})")

    canonical_skill_files = {
        path.relative_to(PLUGIN / "skills"): path.read_bytes()
        for path in (PLUGIN / "skills").rglob("*")
        if path.is_file()
    }
    portable_root = (
        PLUGIN / "skills" / "forge-memory" / "assets" / "portable"
    )
    portable_sources = {
        **{
            Path("scripts") / name: PLUGIN / "scripts" / name
            for name in (
                "forge-init",
                "forge-status",
                "forge-checkpoint",
                "forge-compact",
                "forge-memory-validate",
            )
        },
        **{
            Path("lib") / name: PLUGIN / "lib" / name
            for name in ("forge_files.py", "forge_memory.py")
        },
        **{
            Path("templates") / name: PLUGIN / "templates" / name
            for name in ("agent-return.md", "assurance-result.md")
        },
    }
    for relative, source in portable_sources.items():
        target = portable_root / relative
        if not target.is_file() or target.read_bytes() != source.read_bytes():
            fail(errors, f"portable helper asset is out of sync: {relative}")
    for relative in (".agents/skills", "packages/deepseek-harness/skills"):
        target = ROOT / relative
        target_files = (
            {
                path.relative_to(target): path.read_bytes()
                for path in target.rglob("*")
                if path.is_file()
            }
            if target.is_dir()
            else {}
        )
        if target_files != canonical_skill_files:
            fail(errors, f"portable skill payload is out of sync: {relative}")

    for template in sorted((PLUGIN / "templates").glob("*.md")):
        if not template.read_text(encoding="utf-8").startswith("---\n"):
            fail(errors, f"template lacks frontmatter: {template}")

    for path, markers in PROFILE_MARKERS.items():
        if not path.is_file():
            fail(errors, f"required Task F profile surface is missing: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if path.name == "SKILL.md":
            errors.extend(
                _validate_exact_frontmatter(
                    ROOT,
                    path,
                    {
                        "name": path.parent.name,
                        "description": None,
                    },
                )
            )
        else:
            errors.extend(
                _validate_exact_frontmatter(
                    ROOT,
                    path,
                    {
                        "format": "forge-agent-return-v1",
                        "profile": "",
                        "task": "",
                        "authority_boundary": "",
                        "change_location": "",
                    },
                )
            )
        normalized = _normalized_prose(text)
        for marker in markers:
            if _normalized_prose(marker) not in normalized:
                fail(errors, f"missing Task F profile marker {marker!r}: {path}")
        if path.name == "SKILL.md":
            for grant in _profile_authority_grants(path.parent.name, text):
                fail(
                    errors,
                    (
                        "contradictory authority grant "
                        f"for {path.parent.name} ({grant}): "
                        f"{_relative(ROOT, path)}"
                    ),
                )

    for path, markers in MEMORY_FIRST_MARKERS.items():
        text = path.read_text(encoding="utf-8")
        normalized = _normalized_prose(text)
        for marker in markers:
            if _normalized_prose(marker) not in normalized:
                fail(errors, f"missing Memory-First marker {marker!r}: {path}")
    for path, markers in FORBIDDEN_DEFAULT_MARKERS.items():
        text = path.read_text(encoding="utf-8")
        normalized = _normalized_prose(text)
        for marker in markers:
            if _normalized_prose(marker) in normalized:
                fail(errors, f"obsolete default-workflow marker {marker!r}: {path}")
    capability_path = PLUGIN / "platform-capabilities.json"
    capability = json.loads(capability_path.read_text(encoding="utf-8"))
    capability_fields = {
        "schema_version",
        "shared_profiles",
        "host_adapters",
        "platforms",
    }
    if (
        set(capability) != capability_fields
        or capability.get("schema_version") != 1
    ):
        fail(errors, "platform capability top-level schema is invalid")
    expected_profiles = [
        "forge-scout",
        "forge-builder",
        "forge-checker",
    ]
    if capability.get("shared_profiles") != expected_profiles:
        fail(errors, "shared capability profiles must be exactly Task F profiles")
    expected_adapters = [
        {"id": "claude-code", "status": "active-native"},
        {"id": "codex", "status": "active-native"},
        {"id": "cursor", "status": "active-native"},
        {"id": "command-code", "status": "active-core"},
        {"id": "pi", "status": "active-core"},
        {"id": "deepseek-harness", "status": "active-core"},
    ]
    if capability.get("host_adapters") != expected_adapters:
        fail(
            errors,
            "host adapters must match the tiered six-host inventory",
        )
    expected_platforms = [
        {
            "id": "claude-code",
            "delivery": "native",
            "support_tier": "profile-equivalent",
            "profile_equivalence": True,
            "manifest": "plugins/forge/.claude-plugin/plugin.json",
            "agents": "plugins/forge/agents",
            "profiles": expected_profiles,
        },
        {
            "id": "codex",
            "delivery": "native",
            "support_tier": "profile-equivalent",
            "profile_equivalence": True,
            "manifest": "plugins/forge/.codex-plugin/plugin.json",
            "agents": "plugins/forge/agent-defs/codex",
            "profiles": expected_profiles,
        },
        {
            "id": "cursor",
            "delivery": "native",
            "support_tier": "profile-equivalent",
            "profile_equivalence": True,
            "manifest": "plugins/forge/.cursor-plugin/plugin.json",
            "agents": "plugins/forge/agent-defs/cursor",
            "profiles": expected_profiles,
        },
        {
            "id": "command-code",
            "delivery": "agent-skills",
            "support_tier": "core",
            "profile_equivalence": False,
            "manifest": ".agents/skills",
            "profiles": [],
        },
        {
            "id": "pi",
            "delivery": "pi-package",
            "support_tier": "core",
            "profile_equivalence": False,
            "manifest": "package.json",
            "profiles": [],
        },
        {
            "id": "deepseek-harness",
            "delivery": "dsh-bundle",
            "support_tier": "core",
            "profile_equivalence": False,
            "manifest": "packages/deepseek-harness/package.json",
            "profiles": [],
        },
    ]
    if capability.get("platforms") != expected_platforms:
        fail(
            errors,
            "tiered platform capability inventory is invalid",
        )

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("validate-content FAIL:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("validate-content PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
