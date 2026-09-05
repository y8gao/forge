from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins/forge/lib"
ASSETS = ROOT / "plugins/forge/skills/forge-memory/assets"
VALIDATE = ROOT / "plugins/forge/scripts/forge-memory-validate"
FIXTURES = ROOT / "tests/fixtures/memory_first/.forge"
sys.path.insert(0, str(LIB))

from forge_memory import (  # noqa: E402
    ALLOWED_STATES,
    INTENT_MAX_LINES,
    MISSION_MAX_LINES,
    PUBLIC_API,
    IntentMemory,
    MemoryValidationError,
    MissionMemory,
    checkpoint_mission,
    load_intent,
    load_mission,
    render_initial_intent,
    render_initial_mission,
)


class MemoryContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temp_root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def temp_path(self, text: str, name: str = "memory.md") -> Path:
        path = self.temp_root / name
        path.write_text(text, encoding="utf-8")
        return path

    def fixture_text(self, name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    def test_public_contract_is_frozen(self):
        self.assertEqual(
            {"ready", "working", "blocked", "paused", "done"}, ALLOWED_STATES
        )
        self.assertEqual(100, INTENT_MAX_LINES)
        self.assertEqual(60, MISSION_MAX_LINES)
        self.assertEqual(
            (
                "load_intent",
                "load_mission",
                "render_initial_intent",
                "render_initial_mission",
                "checkpoint_mission",
            ),
            PUBLIC_API,
        )
        self.assertEqual(
            (
                "purpose_why",
                "purpose_user",
                "direction",
                "decisions",
                "constraints",
                "non_goals",
            ),
            tuple(field.name for field in fields(IntentMemory)),
        )
        self.assertEqual(
            (
                "mission_id",
                "state",
                "checkpointed_at",
                "outcome",
                "scope_in",
                "scope_out",
                "scope_constraints",
                "success_criteria",
                "latest_delivery",
                "next_action",
                "blockers",
                "last_check_run",
                "last_check_boundary",
                "resume_read",
                "resume_do",
            ),
            tuple(field.name for field in fields(MissionMemory)),
        )
        with self.assertRaises(FrozenInstanceError):
            load_intent(FIXTURES / "INTENT.md").direction = "changed"

    def test_valid_control_memory_loads(self):
        intent = load_intent(FIXTURES / "INTENT.md")
        mission = load_mission(FIXTURES / "MISSION.md")

        self.assertEqual(
            "Help a solo developer keep coding-agent context across sessions.",
            intent.purpose_why,
        )
        self.assertEqual("A solo vibe coder.", intent.purpose_user)
        self.assertEqual("Ship a small memory-first plugin.", intent.direction)
        self.assertEqual(
            ("D-001: Markdown is canonical control memory",), intent.decisions
        )
        self.assertEqual(
            ("Temporary agents never write active memory.",), intent.constraints
        )
        self.assertEqual(
            ("No daemon, scheduler, ledger, or GraphRAG in the MVP.",),
            intent.non_goals,
        )
        self.assertEqual("memory-first-fixture", mission.mission_id)
        self.assertEqual("working", mission.state)
        self.assertEqual("2026-09-01T12:00:00Z", mission.checkpointed_at)
        self.assertEqual("Implement the memory validator.", mission.outcome)
        self.assertEqual(
            ("Parser and template.", "Checkpoint renderer."),
            mission.scope_in,
        )
        self.assertEqual(("Runtime workflow engine.",), mission.scope_out)
        self.assertEqual(
            ("Keep MISSION within 60 lines.",),
            mission.scope_constraints,
        )
        self.assertEqual(
            (
                "[ ] Parser accepts the new schema.",
                "[x] Checkpoint preserves frozen criteria.",
            ),
            mission.success_criteria,
        )
        self.assertEqual(
            "Added canonical memory fixtures.", mission.latest_delivery
        )
        self.assertEqual(
            "Implement validation against the fixtures.", mission.next_action
        )
        self.assertEqual(("None.",), mission.blockers)
        self.assertEqual(
            "`python -m unittest tests.test_memory_contract -v`",
            mission.last_check_run,
        )
        self.assertEqual(
            "The validator implementation does not exist yet.",
            mission.last_check_boundary,
        )
        self.assertEqual(
            "`plugins/forge/lib/forge_memory.py`", mission.resume_read
        )
        self.assertEqual(
            "implement `load_intent` and `load_mission`.", mission.resume_do
        )

    def test_unknown_mission_state_is_rejected(self):
        for state in ("reviewing", "completed"):
            with self.subTest(state=state):
                text = self.fixture_text("MISSION.md").replace(
                    'state: "working"', f'state: "{state}"'
                )
                with self.assertRaisesRegex(MemoryValidationError, "state"):
                    load_mission(self.temp_path(text))

    def test_mission_line_budget_is_enforced(self):
        text = self.fixture_text("MISSION.md")
        padding = "\n".join(["extra"] * (MISSION_MAX_LINES + 1))
        with self.assertRaisesRegex(MemoryValidationError, "60 lines"):
            load_mission(self.temp_path(text + padding))

    def test_intent_line_budget_is_enforced(self):
        text = self.fixture_text("INTENT.md")
        padding = "\n".join(["extra"] * (INTENT_MAX_LINES + 1))
        with self.assertRaisesRegex(MemoryValidationError, "100 lines"):
            load_intent(self.temp_path(text + padding))

    def test_each_missing_intent_heading_is_rejected(self):
        text = self.fixture_text("INTENT.md")
        for heading in (
            "# Project Intent",
            "## Purpose",
            "## Direction",
            "## Decisions",
            "## Constraints",
            "## Non-goals",
        ):
            with self.subTest(heading=heading):
                path = self.temp_path(
                    text.replace(heading, f"{heading} removed", 1),
                    "INTENT.md",
                )
                with self.assertRaisesRegex(MemoryValidationError, "heading"):
                    load_intent(path)

    def test_each_missing_mission_heading_is_rejected(self):
        text = self.fixture_text("MISSION.md")
        for heading in (
            "# Current Mission",
            "## Outcome",
            "## Scope",
            "## Success Criteria",
            "## Latest Delivery",
            "## Next Action",
            "## Blockers",
            "## Last Check",
            "## Resume",
        ):
            with self.subTest(heading=heading):
                path = self.temp_path(
                    text.replace(heading, f"{heading} removed", 1),
                    "MISSION.md",
                )
                with self.assertRaisesRegex(MemoryValidationError, "heading"):
                    load_mission(path)

    def test_each_missing_intent_labeled_field_is_rejected(self):
        text = self.fixture_text("INTENT.md")
        for field in ("Why", "User", "Current", "Decision", "Rationale", "Status"):
            with self.subTest(field=field):
                path = self.temp_path(
                    text.replace(f"- {field}:", f"- Missing-{field}:", 1),
                    "INTENT.md",
                )
                with self.assertRaisesRegex(MemoryValidationError, field):
                    load_intent(path)

    def test_each_missing_mission_frontmatter_field_is_rejected(self):
        text = self.fixture_text("MISSION.md")
        for field in ("mission_id", "state", "checkpointed_at"):
            with self.subTest(field=field):
                line = next(
                    line for line in text.splitlines() if line.startswith(f"{field}:")
                )
                path = self.temp_path(text.replace(line + "\n", "", 1), "MISSION.md")
                with self.assertRaisesRegex(MemoryValidationError, field):
                    load_mission(path)

    def test_scope_requires_each_label_and_accepts_repeated_labels(self):
        text = self.fixture_text("MISSION.md")
        for field in ("In", "Out", "Constraints"):
            with self.subTest(field=field):
                malformed = "\n".join(
                    line
                    for line in text.splitlines()
                    if not line.startswith(f"- {field}:")
                )
                with self.assertRaisesRegex(MemoryValidationError, field):
                    load_mission(
                        self.temp_path(malformed + "\n", "MISSION.md")
                    )

    def test_success_criteria_require_nonempty_checklist_items(self):
        text = self.fixture_text("MISSION.md")
        for replacement in (
            "- Parser accepts the new schema.",
            "- [ ] ",
            "- [X] Parser accepts the new schema.",
        ):
            with self.subTest(replacement=replacement):
                malformed = text.replace(
                    "- [ ] Parser accepts the new schema.",
                    replacement,
                )
                with self.assertRaisesRegex(
                    MemoryValidationError, "Success Criteria"
                ):
                    load_mission(self.temp_path(malformed, "MISSION.md"))

    def test_done_mission_requires_all_success_criteria_complete(self):
        text = self.fixture_text("MISSION.md").replace(
            'state: "working"', 'state: "done"'
        )

        with self.assertRaisesRegex(
            MemoryValidationError, "done.*success criteria"
        ):
            load_mission(self.temp_path(text, "MISSION.md"))

    def test_each_missing_mission_labeled_field_is_rejected(self):
        text = self.fixture_text("MISSION.md")
        for field in ("Statement", "Ran", "Boundary", "Read", "Do"):
            with self.subTest(field=field):
                path = self.temp_path(
                    text.replace(f"- {field}:", f"- Missing-{field}:", 1),
                    "MISSION.md",
                )
                with self.assertRaisesRegex(MemoryValidationError, field):
                    load_mission(path)

    def test_missing_unlabeled_mission_field_is_rejected(self):
        text = self.fixture_text("MISSION.md")
        for value, field in (
            ("- Added canonical memory fixtures.\n", "Latest Delivery"),
            ("- Implement validation against the fixtures.\n", "Next Action"),
            ("- None.\n", "Blockers"),
        ):
            with self.subTest(field=field):
                path = self.temp_path(text.replace(value, "", 1), "MISSION.md")
                with self.assertRaisesRegex(MemoryValidationError, field):
                    load_mission(path)

    def test_missing_intent_collection_field_is_rejected(self):
        text = self.fixture_text("INTENT.md")
        cases = (
            ("### D-001: Markdown is canonical control memory\n", "Decisions"),
            ("- Temporary agents never write active memory.\n", "Constraints"),
            (
                "- No daemon, scheduler, ledger, or GraphRAG in the MVP.\n",
                "Non-goals",
            ),
        )
        for line, field in cases:
            with self.subTest(field=field):
                path = self.temp_path(text.replace(line, "", 1), "INTENT.md")
                with self.assertRaisesRegex(MemoryValidationError, field):
                    load_intent(path)

    def test_duplicate_heading_is_rejected(self):
        intent = self.fixture_text("INTENT.md").replace(
            "## Purpose", "## Purpose\n## Purpose", 1
        )
        mission = self.fixture_text("MISSION.md").replace(
            "## Outcome", "## Outcome\n## Outcome", 1
        )
        for loader, text, name in (
            (load_intent, intent, "INTENT.md"),
            (load_mission, mission, "MISSION.md"),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(MemoryValidationError, "duplicate heading"):
                    loader(self.temp_path(text, name))

    def test_duplicate_labeled_field_is_rejected(self):
        intent = self.fixture_text("INTENT.md").replace(
            "- Why: Help",
            "- Why: Duplicate.\n- Why: Help",
            1,
        )
        mission = self.fixture_text("MISSION.md").replace(
            "- Ran: `python",
            "- Ran: duplicate\n- Ran: `python",
            1,
        )
        for loader, text, name, field in (
            (load_intent, intent, "INTENT.md", "Why"),
            (load_mission, mission, "MISSION.md", "Ran"),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(
                    MemoryValidationError, f"duplicate.*{field}"
                ):
                    loader(self.temp_path(text, name))

    def test_duplicate_frontmatter_field_is_rejected(self):
        text = self.fixture_text("MISSION.md").replace(
            'state: "working"', 'state: "ready"\nstate: "working"', 1
        )
        with self.assertRaisesRegex(MemoryValidationError, "duplicate.*state"):
            load_mission(self.temp_path(text, "MISSION.md"))

    def test_nonempty_preamble_before_root_heading_is_rejected(self):
        for name, loader in (
            ("INTENT.md", load_intent),
            ("MISSION.md", load_mission),
        ):
            with self.subTest(name=name):
                text = self.fixture_text(name).replace(
                    "---\n#", "---\nunexpected preamble\n#", 1
                )
                with self.assertRaisesRegex(MemoryValidationError, "root heading"):
                    loader(self.temp_path(text, name))

    def test_wrong_format_is_rejected(self):
        for name, loader in (
            ("INTENT.md", load_intent),
            ("MISSION.md", load_mission),
        ):
            with self.subTest(name=name):
                text = self.fixture_text(name).replace(
                    'format: "forge-memory-v1"', 'format: "forge-memory-v0"', 1
                )
                with self.assertRaisesRegex(MemoryValidationError, "format"):
                    loader(self.temp_path(text, name))

    def test_checkpointed_at_null_is_accepted(self):
        text = self.fixture_text("MISSION.md").replace(
            'checkpointed_at: "2026-09-01T12:00:00Z"', "checkpointed_at: null"
        )
        mission = load_mission(self.temp_path(text, "MISSION.md"))
        self.assertIsNone(mission.checkpointed_at)

    def test_initial_renderers_equal_installed_assets_and_round_trip(self):
        intent_text = render_initial_intent()
        mission_text = render_initial_mission()
        self.assertTrue(intent_text.endswith("\n"))
        self.assertFalse(intent_text.endswith("\n\n"))
        self.assertTrue(mission_text.endswith("\n"))
        self.assertFalse(mission_text.endswith("\n\n"))
        self.assertEqual(
            (ASSETS / "INTENT.md").read_text(encoding="utf-8"), intent_text
        )
        self.assertEqual(
            (ASSETS / "MISSION.md").read_text(encoding="utf-8"), mission_text
        )
        intent = load_intent(self.temp_path(intent_text, "INTENT.md"))
        mission = load_mission(self.temp_path(mission_text, "MISSION.md"))
        self.assertIn("host agent", intent.constraints[0].lower())
        self.assertIn("runtime", intent.non_goals[0].lower())
        self.assertEqual("initial", mission.mission_id)
        self.assertEqual("ready", mission.state)
        self.assertIsNone(mission.checkpointed_at)
        self.assertEqual(
            "Confirm the first useful outcome for this project.", mission.outcome
        )
        self.assertEqual(
            "Ask the user to confirm the active outcome.", mission.next_action
        )
        self.assertEqual("None recorded.", mission.last_check_run)
        self.assertEqual("None recorded.", mission.last_check_boundary)

    def test_checkpoint_round_trip_preserves_frozen_fields(self):
        original = load_mission(FIXTURES / "MISSION.md")
        rendered = checkpoint_mission(
            original,
            state="blocked",
            checkpointed_at="2026-09-02T01:02:03Z",
            latest_delivery="Validated canonical memory.",
            next_action="Resolve the remaining blocker.",
            last_check_run="python -m unittest tests.test_memory_contract -v",
            last_check_boundary="Only the memory contract was checked.",
            blockers=("User decision required.",),
        )
        updated = load_mission(self.temp_path(rendered, "MISSION.md"))
        self.assertEqual(original.mission_id, updated.mission_id)
        self.assertEqual(original.outcome, updated.outcome)
        self.assertEqual(original.scope_in, updated.scope_in)
        self.assertEqual(original.scope_out, updated.scope_out)
        self.assertEqual(original.scope_constraints, updated.scope_constraints)
        self.assertEqual(original.success_criteria, updated.success_criteria)
        self.assertEqual(("User decision required.",), updated.blockers)
        self.assertEqual(original.resume_read, updated.resume_read)
        self.assertEqual("Resolve the remaining blocker.", updated.resume_do)
        self.assertEqual("blocked", updated.state)
        self.assertEqual("2026-09-02T01:02:03Z", updated.checkpointed_at)
        self.assertEqual("Validated canonical memory.", updated.latest_delivery)
        self.assertEqual("Resolve the remaining blocker.", updated.next_action)
        self.assertTrue(rendered.endswith("\n"))
        self.assertFalse(rendered.endswith("\n\n"))

    def test_checkpoint_rejects_done_with_incomplete_success_criteria(self):
        mission = load_mission(FIXTURES / "MISSION.md")

        with self.assertRaisesRegex(
            MemoryValidationError, "done.*success criteria"
        ):
            checkpoint_mission(
                mission,
                state="done",
                checkpointed_at="2026-09-02T01:02:03Z",
                latest_delivery="Delivered.",
                next_action="Continue.",
                last_check_run="A check.",
                last_check_boundary="A boundary.",
            )

    def test_checkpoint_accepts_done_only_when_all_success_criteria_are_checked(self):
        text = self.fixture_text("MISSION.md").replace("[ ] Parser", "[x] Parser")
        mission = load_mission(self.temp_path(text, "MISSION.md"))

        rendered = checkpoint_mission(
            mission,
            state="done",
            checkpointed_at="2026-09-02T01:02:03Z",
            latest_delivery="Delivered.",
            next_action="No further action.",
            last_check_run="A check.",
            last_check_boundary="A boundary.",
        )

        self.assertEqual("done", load_mission(self.temp_path(rendered)).state)

    def test_checkpoint_allows_mixed_success_criteria_for_other_states(self):
        mission = load_mission(FIXTURES / "MISSION.md")

        for state in ALLOWED_STATES - {"done"}:
            with self.subTest(state=state):
                extra = (
                    {"blockers": ("User decision required.",)}
                    if state == "blocked"
                    else {}
                )
                rendered = checkpoint_mission(
                    mission,
                    state=state,
                    checkpointed_at="2026-09-02T01:02:03Z",
                    latest_delivery="Delivered.",
                    next_action="Continue.",
                    last_check_run="A check.",
                    last_check_boundary="A boundary.",
                    **extra,
                )
                updated = load_mission(self.temp_path(rendered, f"{state}.md"))
                self.assertEqual(state, updated.state)
                self.assertEqual("Continue.", updated.resume_do)
                if state != "blocked":
                    self.assertEqual(("None.",), updated.blockers)

    def test_checkpoint_blocked_requires_a_current_blocker(self):
        mission = load_mission(FIXTURES / "MISSION.md")

        with self.assertRaisesRegex(MemoryValidationError, "blocked.*blocker"):
            checkpoint_mission(
                mission,
                state="blocked",
                checkpointed_at="2026-09-02T01:02:03Z",
                latest_delivery="Delivered.",
                next_action="Await a decision.",
                last_check_run="A check.",
                last_check_boundary="A boundary.",
            )

    def test_checkpoint_rejects_invalid_updates(self):
        mission = load_mission(FIXTURES / "MISSION.md")
        valid = {
            "state": "working",
            "checkpointed_at": "2026-09-02T01:02:03Z",
            "latest_delivery": "Delivered.",
            "next_action": "Continue.",
            "last_check_run": "A check.",
            "last_check_boundary": "A boundary.",
        }
        for field, value in (
            ("state", "reviewing"),
            ("checkpointed_at", ""),
            ("latest_delivery", " "),
            ("next_action", ""),
            ("last_check_run", "\t"),
            ("last_check_boundary", ""),
        ):
            with self.subTest(field=field):
                arguments = dict(valid)
                arguments[field] = value
                with self.assertRaisesRegex(MemoryValidationError, field):
                    checkpoint_mission(mission, **arguments)

    def test_checkpoint_rejects_quote_in_checkpointed_at(self):
        mission = load_mission(FIXTURES / "MISSION.md")
        with self.assertRaisesRegex(MemoryValidationError, "checkpointed_at"):
            checkpoint_mission(
                mission,
                state="working",
                checkpointed_at='2026-09-02T01:02:03Z"oops',
                latest_delivery="Delivered.",
                next_action="Continue.",
                last_check_run="A check.",
                last_check_boundary="A boundary.",
            )

    def test_checkpoint_rejects_all_splitlines_unicode_separators(self):
        mission = load_mission(FIXTURES / "MISSION.md")
        valid = {
            "state": "working",
            "checkpointed_at": "2026-09-02T01:02:03Z",
            "latest_delivery": "Delivered.",
            "next_action": "Continue.",
            "last_check_run": "A check.",
            "last_check_boundary": "A boundary.",
        }
        checkpoint_fields = (
            "checkpointed_at",
            "latest_delivery",
            "next_action",
            "last_check_run",
            "last_check_boundary",
        )
        for separator in ("\u0085", "\u2028", "\u2029"):
            for field in checkpoint_fields:
                with self.subTest(separator=hex(ord(separator)), field=field):
                    arguments = dict(valid)
                    arguments[field] = f"before{separator}after"
                    with self.assertRaisesRegex(MemoryValidationError, field):
                        checkpoint_mission(mission, **arguments)

    def test_cli_accepts_only_a_project_root(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATE), str(FIXTURES.parent)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("forge-memory-validate PASS\n", result.stdout)
        self.assertEqual("", result.stderr)

        direct_forge = subprocess.run(
            [sys.executable, str(VALIDATE), str(FIXTURES)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, direct_forge.returncode)
        self.assertEqual("", direct_forge.stdout)
        self.assertEqual(
            "forge-memory-validate ERROR: PROJECT_ROOT must not be a .forge directory\n",
            direct_forge.stderr,
        )
        self.assertNotIn("Traceback", direct_forge.stderr)

    def test_cli_usage_and_validation_fail_without_tracebacks(self):
        usage = subprocess.run(
            [sys.executable, str(VALIDATE)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, usage.returncode)
        self.assertEqual("", usage.stdout)
        self.assertEqual(
            "forge-memory-validate ERROR: expected exactly one PROJECT_ROOT\n",
            usage.stderr,
        )

        project = self.temp_root / "project"
        forge = project / ".forge"
        forge.mkdir(parents=True)
        (forge / "INTENT.md").write_text(
            self.fixture_text("INTENT.md"), encoding="utf-8"
        )
        (forge / "MISSION.md").write_text(
            self.fixture_text("MISSION.md").replace(
                'state: "working"', 'state: "reviewing"'
            ),
            encoding="utf-8",
        )
        invalid = subprocess.run(
            [sys.executable, str(VALIDATE), str(project)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, invalid.returncode)
        self.assertEqual("", invalid.stdout)
        self.assertRegex(
            invalid.stderr, r"^forge-memory-validate ERROR: .*state.*\n$"
        )
        self.assertNotIn("Traceback", invalid.stderr)


if __name__ == "__main__":
    unittest.main()
