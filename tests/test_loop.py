from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOOP = ROOT / "plugins/forge/skills/forge-loop/SKILL.md"
CORE = ROOT / "plugins/forge/skills/forge-core/SKILL.md"


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    opening, block, _body = text.split("---", 2)
    if opening:
        raise AssertionError("frontmatter must be the first content")
    values: dict[str, str] = {}
    for line in block.strip().splitlines():
        key, raw = line.split(":", 1)
        key = key.strip()
        if key in values:
            raise AssertionError(f"duplicate frontmatter key: {key}")
        value = json.loads(raw.strip())
        if not isinstance(value, str):
            raise AssertionError("frontmatter values must be strings")
        values[key] = value
    return values


def parse_key_state_mapping(lines: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for line in lines:
        if "=>" not in line:
            continue
        key, state = (part.strip() for part in line.split("=>", 1))
        if key in mapping:
            raise AssertionError(f"duplicate condition key: {key}")
        if state not in {"ready", "working", "paused", "blocked", "done"}:
            raise AssertionError(f"unknown Mission state: {state}")
        mapping[key] = state
    return mapping


def parse_redirect_matrix(lines: list[str]) -> dict[str, set[str]]:
    matrix = {"pause": set(), "continue": set()}
    seen: set[str] = set()
    for line in lines:
        if "=>" not in line:
            continue
        action, raw_triggers = (part.strip() for part in line.split("=>", 1))
        if action not in matrix:
            raise AssertionError(f"unknown redirect action: {action}")
        triggers = [trigger.strip() for trigger in raw_triggers.split(",")]
        for trigger in triggers:
            if not trigger:
                raise AssertionError("empty redirect trigger")
            if trigger in seen:
                raise AssertionError(f"duplicate redirect trigger: {trigger}")
            seen.add(trigger)
            matrix[action].add(trigger)
    return matrix


class LoopUserJourneyContractTests(unittest.TestCase):
    def loop_text(self) -> str:
        return " ".join(LOOP.read_text(encoding="utf-8").split())

    def section_lines(self, heading: str, path: Path = LOOP) -> list[str]:
        target = f"## {heading}"
        collecting = False
        in_fence = False
        section: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("```"):
                if collecting:
                    section.append(line)
                in_fence = not in_fence
                continue
            if not in_fence and line == target:
                collecting = True
                continue
            if collecting and not in_fence and line.startswith("## "):
                break
            if collecting:
                section.append(line)
        self.assertTrue(collecting, f"missing section {target}")
        return section

    def section_text(self, heading: str, path: Path = LOOP) -> str:
        return " ".join(" ".join(self.section_lines(heading, path)).split())

    def assert_markers(self, text: str, *markers: str) -> None:
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertIn(marker, text)

    def assert_forbidden_markers(self, text: str, *markers: str) -> None:
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, text)

    def test_skill_keeps_exact_frontmatter_and_line_budget(self) -> None:
        self.assertEqual(
            {
                "name": "forge-loop",
                "description": (
                    "Explicit prompt-only bounded delivery loop with visible "
                    "deltas, falsifying checks, and host-owned checkpoints."
                ),
            },
            parse_frontmatter(LOOP),
        )
        self.assertLess(len(LOOP.read_text(encoding="utf-8").splitlines()), 500)

    def test_duplicate_frontmatter_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "SKILL.md"
            path.write_text(
                '---\nname: "forge-loop"\nname: "other"\n'
                'description: "duplicate fixture"\n---\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                AssertionError, "duplicate frontmatter key: name"
            ):
                parse_frontmatter(path)

    def test_core_recommended_entry_reuses_cores_single_card_without_echo(
        self,
    ) -> None:
        core = self.section_text("Offer Loop once for complex work", CORE)
        loop = self.section_text("Confirm entry")
        self.assert_markers(
            core,
            "Present this one concise card",
            "Enter only after the user accepts the complete card",
        )
        self.assert_markers(
            loop,
            "Only Core proactively recommends Loop, presents the card, and asks",
            "For a Core-recommended entry",
            "validate and record the already accepted card",
            "must not show or echo it again",
        )

    def test_complete_direct_entry_shows_one_acknowledgement_without_reapproval(
        self,
    ) -> None:
        entry = self.section_text("Confirm entry")
        self.assert_markers(
            entry,
            "`forge-loop` alias",
            "clear natural-language request for bounded continuation",
            "entry request",
            "constructs and shows exactly one card as acknowledgement",
            "starts without asking for redundant approval",
        )
        self.assert_forbidden_markers(
            entry,
            "is explicit activation",
            "Loop proactively recommends itself",
            "ask for confirmation again",
        )

    def test_user_gets_one_complete_loop_card_without_guessed_scope(self) -> None:
        text = self.loop_text()
        for field in ("Outcome:", "Done when:", "Boundaries:", "Budget:"):
            self.assertEqual(1, text.count(field), field)
        self.assert_markers(
            text,
            "Specific, Measurable, Achievable, Relevant, and Time-bounded",
            "Scope In",
            "Scope Out",
            "allowed write scope",
            "forbidden or destructive operations",
            "completion conditions",
            "must not guess or infer",
            "execution, acceptance, risk, or external authority",
        )

    def test_incomplete_entry_asks_only_for_material_missing_facts(self) -> None:
        entry = self.section_text("Confirm entry")
        self.assert_markers(
            entry,
            "If the entry request is incomplete",
            "ask only for missing material facts",
            "Do not repeat facts the user already supplied",
            "must not guess or infer",
            "show the completed card exactly once",
            "start only when the user explicitly replies to approve it",
        )

    def test_each_invocation_has_fresh_bounded_budget_with_exact_counting(self) -> None:
        text = self.section_text("Bound one invocation")
        self.assert_markers(
            text,
            "3 delivery iterations",
            "5 temporary-agent invocations",
            "positive integers",
            "Cross-session continuation starts a new invocation with a new budget",
            "Each parallel agent counts separately",
            "Starting a delivery cycle consumes one iteration",
            "no visible delta still consumes",
            "no adaptive budget engine or arbitrary hidden caps",
        )

    def test_user_receives_one_real_delta_per_delivery_cycle(self) -> None:
        text = self.loop_text()
        self.assert_markers(
            text,
            "host performs ordinary actions directly first",
            "Scout or Builder",
            "one user-inspectable visible delta",
            "targeted falsifying check",
            "lightweight economy check",
            "Host accepts",
            "one checkpoint",
            "reading files, launching agents, internal plans, and progress narration",
            "do not count as delivery",
            "does not automatically call Checker",
        )

    def test_parallel_builders_are_safe_or_losslessly_serialized(self) -> None:
        text = self.loop_text()
        self.assert_markers(
            text,
            "only when tasks are independent and do not share write state",
            "Temporary agents cannot delegate",
            "overlapping write scopes cannot run in parallel",
            "cancels them when safe or waits for completion",
            "actual diff",
            "unaccepted",
            "lossless",
            "adopt, adapt, or discard",
            "does not automatically revert user work",
        )

    def test_stop_conditions_parse_to_exact_unique_mission_states(self) -> None:
        mapping = parse_key_state_mapping(
            self.section_lines("Canonical stop mapping")
        )
        self.assertEqual(
            {
                "outcome-complete": "done",
                "budget-exhausted": "working",
                "required-current-plan-decision": "blocked",
                "unsafe-path": "blocked",
                "no-safe-next-action": "blocked",
                "same-root-cause-twice": "blocked",
                "explicit-user-pause": "paused",
                "material-redirect-comparison": "paused",
                "no-visible-delta-safe-recovery": "working",
                "no-visible-delta-no-safe-recovery": "blocked",
            },
            mapping,
        )
        stop = self.section_text("Stop once and preserve evidence")
        self.assertIn("accepted visible delta and stop in one checkpoint", stop)

    def test_stop_mapping_parser_rejects_duplicate_or_conflicting_keys(self) -> None:
        with self.assertRaisesRegex(
            AssertionError, "duplicate condition key: budget-exhausted"
        ):
            parse_key_state_mapping(
                [
                    "budget-exhausted => working",
                    "budget-exhausted => blocked",
                ]
            )

    def test_first_failure_leaves_compact_recovery_evidence(self) -> None:
        text = self.loop_text()
        self.assert_markers(
            text,
            "first failed cycle",
            "classified root cause, key evidence, and attempted recovery",
            "Last Check or Blockers",
        )

    def test_declining_loop_preserves_original_task_authority(self) -> None:
        text = self.loop_text()
        self.assert_markers(
            text,
            "declines Loop",
            "not cancelling the original task",
            "one minimum safe Core delivery",
            "plan-only response",
            "explicit stop",
        )

    def test_redirect_matrix_has_exact_disjoint_pause_and_continue_groups(
        self,
    ) -> None:
        matrix = parse_redirect_matrix(
            self.section_lines("Canonical redirect matrix")
        )
        self.assertEqual(
            {
                "pause": {
                    "material-outcome-change",
                    "material-scope-change",
                    "material-success-criteria-change",
                    "material-authority-change",
                    "in-flight-work-invalidated",
                },
                "continue": {
                    "pure-question",
                    "status-request",
                    "continue-request",
                    "non-authority-clarification",
                },
            },
            matrix,
        )
        self.assertTrue(matrix["pause"].isdisjoint(matrix["continue"]))

    def test_redirect_matrix_parser_rejects_duplicate_or_overlapping_triggers(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            AssertionError, "duplicate redirect trigger: pure-question"
        ):
            parse_redirect_matrix(
                [
                    "continue => pure-question",
                    "pause => pure-question",
                ]
            )

    def test_material_redirect_checkpoints_stale_status_before_disposition(
        self,
    ) -> None:
        text = self.section_text("Redirect safely")
        ordered = (
            "old invocation stops accepting results and checkpointing",
            "cancel in-flight work when safe or wait for completion",
            "inspect the actual working-tree change",
            "write exactly one redirect pause checkpoint",
            "request user disposition",
        )
        self.assert_markers(text.lower(), *(marker.lower() for marker in ordered))
        positions = [text.lower().index(marker.lower()) for marker in ordered]
        self.assertEqual(sorted(positions), positions)
        self.assert_markers(
            text,
            "accepted delivery and stale or unaccepted status",
            "user disposition",
            "disposition and a complete new Loop card in one prompt",
            "waits for an in-place Builder",
            "stale and unaccepted",
            "target Mission and Scope",
            "re-inspects",
            "Discarding in-place changes requires explicit authorization",
            "Subsequent changes belong only to the new authority",
        )

    def test_loop_never_implies_external_effect_authority_or_runtime_state(self) -> None:
        text = self.loop_text()
        self.assert_markers(
            text,
            "specific action and target",
            "No Loop invocation implies permission",
            "Counters remain only in the current conversation",
        )
        self.assert_forbidden_markers(
            text,
            "persist counters in MISSION",
            "start a scheduler",
            "MISSION.md stores invocation counters",
            "nested delegation is allowed",
        )


if __name__ == "__main__":
    unittest.main()
