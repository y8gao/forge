from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


ALLOWED_STATES = {"ready", "working", "blocked", "paused", "done"}
INTENT_MAX_LINES = 100
MISSION_MAX_LINES = 60

PUBLIC_API = (
    "load_intent",
    "load_mission",
    "render_initial_intent",
    "render_initial_mission",
    "checkpoint_mission",
)


class MemoryValidationError(ValueError):
    pass


@dataclass(frozen=True)
class IntentMemory:
    purpose_why: str
    purpose_user: str
    direction: str
    decisions: tuple[str, ...]
    constraints: tuple[str, ...]
    non_goals: tuple[str, ...]


@dataclass(frozen=True)
class MissionMemory:
    mission_id: str
    state: str
    checkpointed_at: str | None
    outcome: str
    scope_in: tuple[str, ...]
    scope_out: tuple[str, ...]
    scope_constraints: tuple[str, ...]
    success_criteria: tuple[str, ...]
    latest_delivery: str
    next_action: str
    blockers: tuple[str, ...]
    last_check_run: str
    last_check_boundary: str
    resume_read: str
    resume_do: str


_INITIAL_INTENT = """\
---
format: "forge-memory-v1"
---
# Project Intent

## Purpose
- Why: Keep coding agents oriented across sessions.
- User: A developer working with coding agents.

## Direction
- Current: Confirm the first useful outcome for this project.

## Decisions
### D-001: Markdown is canonical control memory
- Decision: Keep active intent and mission in Git-diffable Markdown.
- Rationale: Every supported host can read it directly.
- Status: active

## Constraints
- Only the host agent writes active memory.

## Non-goals
- No runtime hooks, daemon, scheduler, ledger, or external memory provider.
"""

_INITIAL_MISSION = """\
---
format: "forge-memory-v1"
mission_id: "initial"
state: "ready"
checkpointed_at: null
---
# Current Mission

## Outcome
- Statement: Confirm the first useful outcome for this project.

## Scope
- In: Confirm the first useful project outcome and its acceptance boundary.
- Out: Unconfirmed implementation work.
- Constraints: Use only user-confirmed project facts.

## Success Criteria
- [ ] Outcome, scope, and observable completion criteria are confirmed.

## Latest Delivery
- No delivery recorded yet.

## Next Action
- Ask the user to confirm the active outcome.

## Blockers
- None.

## Last Check
- Ran: None recorded.
- Boundary: None recorded.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md`.
- Do: Ask the user to confirm the active outcome.
"""

_INTENT_HEADINGS = (
    "# Project Intent",
    "## Purpose",
    "## Direction",
    "## Decisions",
    "## Constraints",
    "## Non-goals",
)
_MISSION_HEADINGS = (
    "# Current Mission",
    "## Outcome",
    "## Scope",
    "## Success Criteria",
    "## Latest Delivery",
    "## Next Action",
    "## Blockers",
    "## Last Check",
    "## Resume",
)


def _read(path: str | Path, maximum_lines: int, kind: str) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise MemoryValidationError(f"{kind}: cannot read {path}: {error}") from None
    line_count = len(text.splitlines())
    if line_count > maximum_lines:
        raise MemoryValidationError(
            f"{kind}: exceeds {maximum_lines} lines ({line_count})"
        )
    return text


def _frontmatter(
    text: str, *, kind: str, required: tuple[str, ...]
) -> tuple[dict[str, str | None], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise MemoryValidationError(f"{kind}: missing frontmatter")
    try:
        closing = lines.index("---", 1)
    except ValueError:
        raise MemoryValidationError(f"{kind}: unterminated frontmatter") from None

    values: dict[str, str | None] = {}
    for line in lines[1:closing]:
        match = re.fullmatch(r"([a-z_]+): (.+)", line)
        if match is None:
            raise MemoryValidationError(f"{kind}: invalid frontmatter line")
        key, raw_value = match.groups()
        if key not in required:
            raise MemoryValidationError(f"{kind}: unknown frontmatter field {key}")
        if key in values:
            raise MemoryValidationError(
                f"{kind}: duplicate frontmatter field {key}"
            )
        if raw_value == "null":
            value: str | None = None
        else:
            quoted = re.fullmatch(r'"([^"]+)"', raw_value)
            if quoted is None:
                raise MemoryValidationError(
                    f"{kind}: invalid frontmatter field {key}"
                )
            value = quoted.group(1)
        values[key] = value

    for field in required:
        if field not in values:
            raise MemoryValidationError(f"{kind}: missing frontmatter field {field}")
    if values["format"] != "forge-memory-v1":
        raise MemoryValidationError(f'{kind}: format must be "forge-memory-v1"')
    return values, lines[closing + 1 :]


def _sections(
    lines: list[str], *, kind: str, headings: tuple[str, ...]
) -> dict[str, list[str]]:
    first_nonempty = next((line for line in lines if line), None)
    if first_nonempty != headings[0]:
        raise MemoryValidationError(
            f"{kind}: root heading {headings[0]} must be the first nonempty body line"
        )

    observed = [line for line in lines if line.startswith("#")]
    for heading in headings:
        count = observed.count(heading)
        if count == 0:
            raise MemoryValidationError(f"{kind}: missing heading {heading}")
        if count > 1:
            raise MemoryValidationError(f"{kind}: duplicate heading {heading}")

    allowed_dynamic = kind == "INTENT" and all(
        heading in headings or heading.startswith("### ") for heading in observed
    )
    if not allowed_dynamic and any(heading not in headings for heading in observed):
        unknown = next(heading for heading in observed if heading not in headings)
        raise MemoryValidationError(f"{kind}: unknown heading {unknown}")

    positions = [lines.index(heading) for heading in headings]
    if positions != sorted(positions):
        raise MemoryValidationError(f"{kind}: headings are out of order")

    sections: dict[str, list[str]] = {}
    for index, heading in enumerate(headings):
        start = positions[index] + 1
        end = positions[index + 1] if index + 1 < len(positions) else len(lines)
        sections[heading] = lines[start:end]
    return sections


def _labeled_fields(
    lines: list[str], *, kind: str, section: str, labels: tuple[str, ...]
) -> dict[str, str]:
    values: dict[str, str] = {}
    nonempty = [line for line in lines if line]
    for line in nonempty:
        matched = False
        for label in labels:
            prefix = f"- {label}:"
            if line.startswith(prefix):
                if label in values:
                    raise MemoryValidationError(
                        f"{kind}: duplicate labeled field {label}"
                    )
                value = line[len(prefix) :].strip()
                if not value:
                    raise MemoryValidationError(f"{kind}: empty field {label}")
                values[label] = value
                matched = True
                break
        if not matched:
            raise MemoryValidationError(
                f"{kind}: invalid field in {section}: {line}"
            )
    for label in labels:
        if label not in values:
            raise MemoryValidationError(f"{kind}: missing field {label}")
    return values


def _bullet_values(
    lines: list[str], *, kind: str, section: str, exactly_one: bool = False
) -> tuple[str, ...]:
    nonempty = [line for line in lines if line]
    if not nonempty:
        raise MemoryValidationError(f"{kind}: missing field {section}")
    if exactly_one and len(nonempty) != 1:
        raise MemoryValidationError(f"{kind}: {section} requires one bullet")
    values: list[str] = []
    for line in nonempty:
        if not line.startswith("- ") or not line[2:].strip():
            raise MemoryValidationError(f"{kind}: invalid field in {section}")
        values.append(line[2:].strip())
    return tuple(values)


def _scope_values(lines: list[str]) -> dict[str, tuple[str, ...]]:
    labels = ("In", "Out", "Constraints")
    values: dict[str, list[str]] = {label: [] for label in labels}
    for line in (line for line in lines if line):
        matched = False
        for label in labels:
            prefix = f"- {label}:"
            if line.startswith(prefix):
                value = line[len(prefix) :].strip()
                if not value:
                    raise MemoryValidationError(f"MISSION: empty field {label}")
                values[label].append(value)
                matched = True
                break
        if not matched:
            raise MemoryValidationError(f"MISSION: invalid field in Scope: {line}")
    for label in labels:
        if not values[label]:
            raise MemoryValidationError(f"MISSION: missing field {label}")
    return {label: tuple(items) for label, items in values.items()}


def _checklist_values(lines: list[str]) -> tuple[str, ...]:
    nonempty = [line for line in lines if line]
    if not nonempty:
        raise MemoryValidationError("MISSION: missing field Success Criteria")
    values: list[str] = []
    for line in nonempty:
        match = re.fullmatch(r"- (\[[ x]\]) (.+)", line)
        if match is None or not match.group(2).strip():
            raise MemoryValidationError(
                "MISSION: invalid field in Success Criteria"
            )
        values.append(f"{match.group(1)} {match.group(2).strip()}")
    return tuple(values)


def _parse_decisions(lines: list[str]) -> tuple[str, ...]:
    nonempty = [line for line in lines if line]
    headings = [line for line in nonempty if line.startswith("### ")]
    if not headings:
        raise MemoryValidationError("INTENT: missing field Decisions")
    if len(headings) != len(set(headings)):
        raise MemoryValidationError("INTENT: duplicate heading in Decisions")

    decisions: list[str] = []
    for index, heading in enumerate(headings):
        start = nonempty.index(heading) + 1
        end = (
            nonempty.index(headings[index + 1])
            if index + 1 < len(headings)
            else len(nonempty)
        )
        title = heading[4:].strip()
        if not title:
            raise MemoryValidationError("INTENT: empty decision heading")
        _labeled_fields(
            nonempty[start:end],
            kind="INTENT",
            section=title,
            labels=("Decision", "Rationale", "Status"),
        )
        decisions.append(title)
    return tuple(decisions)


def load_intent(path: str | Path) -> IntentMemory:
    text = _read(path, INTENT_MAX_LINES, "INTENT")
    _, body = _frontmatter(text, kind="INTENT", required=("format",))
    sections = _sections(body, kind="INTENT", headings=_INTENT_HEADINGS)
    purpose = _labeled_fields(
        sections["## Purpose"],
        kind="INTENT",
        section="Purpose",
        labels=("Why", "User"),
    )
    direction = _labeled_fields(
        sections["## Direction"],
        kind="INTENT",
        section="Direction",
        labels=("Current",),
    )
    return IntentMemory(
        purpose_why=purpose["Why"],
        purpose_user=purpose["User"],
        direction=direction["Current"],
        decisions=_parse_decisions(sections["## Decisions"]),
        constraints=_bullet_values(
            sections["## Constraints"], kind="INTENT", section="Constraints"
        ),
        non_goals=_bullet_values(
            sections["## Non-goals"], kind="INTENT", section="Non-goals"
        ),
    )


def load_mission(path: str | Path) -> MissionMemory:
    text = _read(path, MISSION_MAX_LINES, "MISSION")
    frontmatter, body = _frontmatter(
        text,
        kind="MISSION",
        required=("format", "mission_id", "state", "checkpointed_at"),
    )
    mission_id = frontmatter["mission_id"]
    state = frontmatter["state"]
    checkpointed_at = frontmatter["checkpointed_at"]
    if not isinstance(mission_id, str):
        raise MemoryValidationError("MISSION: mission_id must be a string")
    if not isinstance(state, str) or state not in ALLOWED_STATES:
        raise MemoryValidationError(
            f"MISSION: state must be one of {', '.join(sorted(ALLOWED_STATES))}"
        )
    if checkpointed_at is not None and not isinstance(checkpointed_at, str):
        raise MemoryValidationError(
            "MISSION: checkpointed_at must be a string or null"
        )

    sections = _sections(body, kind="MISSION", headings=_MISSION_HEADINGS)
    outcome = _labeled_fields(
        sections["## Outcome"],
        kind="MISSION",
        section="Outcome",
        labels=("Statement",),
    )
    scope = _scope_values(sections["## Scope"])
    last_check = _labeled_fields(
        sections["## Last Check"],
        kind="MISSION",
        section="Last Check",
        labels=("Ran", "Boundary"),
    )
    resume = _labeled_fields(
        sections["## Resume"],
        kind="MISSION",
        section="Resume",
        labels=("Read", "Do"),
    )
    success_criteria = _checklist_values(sections["## Success Criteria"])
    if state == "done" and any(
        not criterion.startswith("[x] ") for criterion in success_criteria
    ):
        raise MemoryValidationError(
            "MISSION: state done requires all success criteria to be complete"
        )
    return MissionMemory(
        mission_id=mission_id,
        state=state,
        checkpointed_at=checkpointed_at,
        outcome=outcome["Statement"],
        scope_in=scope["In"],
        scope_out=scope["Out"],
        scope_constraints=scope["Constraints"],
        success_criteria=success_criteria,
        latest_delivery=_bullet_values(
            sections["## Latest Delivery"],
            kind="MISSION",
            section="Latest Delivery",
            exactly_one=True,
        )[0],
        next_action=_bullet_values(
            sections["## Next Action"],
            kind="MISSION",
            section="Next Action",
            exactly_one=True,
        )[0],
        blockers=_bullet_values(
            sections["## Blockers"], kind="MISSION", section="Blockers"
        ),
        last_check_run=last_check["Ran"],
        last_check_boundary=last_check["Boundary"],
        resume_read=resume["Read"],
        resume_do=resume["Do"],
    )


def render_initial_intent() -> str:
    return _INITIAL_INTENT


def render_initial_mission() -> str:
    return _INITIAL_MISSION


def _checkpoint_value(name: str, value: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value.splitlines() != [value]
    ):
        raise MemoryValidationError(
            f"MISSION: checkpoint field {name} must be a nonempty single line"
        )
    return value.strip()


def checkpoint_mission(
    mission: MissionMemory,
    *,
    state: str,
    checkpointed_at: str,
    latest_delivery: str,
    next_action: str,
    last_check_run: str,
    last_check_boundary: str,
    blockers: tuple[str, ...] | None = None,
) -> str:
    if state not in ALLOWED_STATES:
        raise MemoryValidationError(
            f"MISSION: checkpoint field state must be one of "
            f"{', '.join(sorted(ALLOWED_STATES))}"
        )
    if state == "done" and any(
        not criterion.startswith("[x] ")
        for criterion in mission.success_criteria
    ):
        raise MemoryValidationError(
            "MISSION: state done requires all success criteria to be complete"
        )
    checkpointed_at = _checkpoint_value("checkpointed_at", checkpointed_at)
    if '"' in checkpointed_at:
        raise MemoryValidationError(
            "MISSION: checkpoint field checkpointed_at must not contain a quote"
        )
    latest_delivery = _checkpoint_value("latest_delivery", latest_delivery)
    next_action = _checkpoint_value("next_action", next_action)
    last_check_run = _checkpoint_value("last_check_run", last_check_run)
    last_check_boundary = _checkpoint_value(
        "last_check_boundary", last_check_boundary
    )
    if state == "blocked":
        if not blockers or any(blocker.strip().lower() == "none." for blocker in blockers):
            raise MemoryValidationError(
                "MISSION: state blocked requires a current blocker"
            )
        blocker_values = tuple(
            _checkpoint_value("blockers", blocker) for blocker in blockers
        )
    else:
        if blockers is not None:
            raise MemoryValidationError(
                "MISSION: checkpoint field blockers is valid only for state blocked"
            )
        blocker_values = ("None.",)
    rendered_blockers = "\n".join(f"- {blocker}" for blocker in blocker_values)
    scope_in = "\n".join(f"- In: {value}" for value in mission.scope_in)
    scope_out = "\n".join(f"- Out: {value}" for value in mission.scope_out)
    scope_constraints = "\n".join(
        f"- Constraints: {value}" for value in mission.scope_constraints
    )
    success_criteria = "\n".join(
        f"- {criterion}" for criterion in mission.success_criteria
    )
    return (
        f'---\n'
        f'format: "forge-memory-v1"\n'
        f'mission_id: "{mission.mission_id}"\n'
        f'state: "{state}"\n'
        f'checkpointed_at: "{checkpointed_at}"\n'
        f'---\n'
        f'# Current Mission\n'
        f'\n'
        f'## Outcome\n'
        f'- Statement: {mission.outcome}\n'
        f'\n'
        f'## Scope\n'
        f'{scope_in}\n'
        f'{scope_out}\n'
        f'{scope_constraints}\n'
        f'\n'
        f'## Success Criteria\n'
        f'{success_criteria}\n'
        f'\n'
        f'## Latest Delivery\n'
        f'- {latest_delivery}\n'
        f'\n'
        f'## Next Action\n'
        f'- {next_action}\n'
        f'\n'
        f'## Blockers\n'
        f'{rendered_blockers}\n'
        f'\n'
        f'## Last Check\n'
        f'- Ran: {last_check_run}\n'
        f'- Boundary: {last_check_boundary}\n'
        f'\n'
        f'## Resume\n'
        f'- Read: {mission.resume_read}\n'
        f'- Do: {next_action}\n'
    )
