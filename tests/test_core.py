from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "plugins/forge/skills/forge-core/SKILL.md"
MEMORY = ROOT / "plugins/forge/skills/forge-memory/SKILL.md"


class CoreUserJourneyContractTests(unittest.TestCase):
    def core_text(self) -> str:
        return " ".join(CORE.read_text(encoding="utf-8").split())

    def memory_text(self) -> str:
        return " ".join(MEMORY.read_text(encoding="utf-8").split())

    def section_text(self, path: Path, heading: str) -> str:
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
        self.assertTrue(collecting, f"missing section {target} in {path}")
        return " ".join(" ".join(section).split())

    def assert_forbidden_markers(self, text: str, *markers: str) -> None:
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, text)

    def test_skill_files_keep_exact_frontmatter_and_line_budget(self) -> None:
        expected = {
            CORE: (
                "forge-core",
                "Forge Memory-First default behavior for orientation, ordinary "
                "execution, checkpoints, proportional checks, and explicit "
                "Loop or Assurance entry.",
            ),
            MEMORY: (
                "forge-memory",
                "Forge Memory-First control memory, mission state, checkpoints, "
                "compaction, archives, and deferred external recall.",
            ),
        }
        for path, (name, description) in expected.items():
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(
                    [
                        "---",
                        f"name: {name}",
                        f"description: {description}",
                        "---",
                    ],
                    text.splitlines()[:4],
                )
                self.assertLess(len(text.splitlines()), 500)

    def test_user_starts_in_natural_language_without_workflow_jargon(self) -> None:
        text = self.core_text()
        self.assertIn("Natural-language requests are the primary entry point", text)
        self.assertIn("Aliases are optional", text)
        self.assertIn(
            "does not need to understand profiles, checkpoints, or invocation syntax",
            text,
        )

    def test_core_takes_the_first_minimum_sufficient_delivery_path(self) -> None:
        text = self.core_text()
        for marker in (
            "Orient -> understand the request -> choose the first minimum sufficient path",
            "act directly or select one useful profile",
            "targeted check -> checkpoint only on a real transition",
        ):
            self.assertIn(marker, text)

    def test_pure_question_does_not_disturb_active_mission(self) -> None:
        text = self.core_text()
        self.assertIn("pure question or read-only lookup", text)
        self.assertIn("does not replace or checkpoint the active Mission", text)

    def test_single_turn_incidental_change_does_not_replace_unrelated_mission(
        self,
    ) -> None:
        text = self.core_text()
        self.assertIn("single-turn, reversible incidental change", text)
        self.assertIn("does not checkpoint it into an unrelated Mission", text)
        memory = self.memory_text()
        self.assertIn("Incidental work", memory)
        self.assertIn("must not be written into an unrelated Mission", memory)

    def test_fresh_resume_is_state_sensitive(self) -> None:
        text = self.core_text()
        for marker in (
            "`ready` or `working`",
            "`paused` requires the user to resume",
            "`blocked` requires resolving",
            "`done` stays closed",
        ):
            self.assertIn(marker, text)

    def test_initial_mission_is_activated_before_substantive_work(self) -> None:
        core = self.core_text()
        memory = self.memory_text()
        for marker in (
            '`mission_id: "initial"`',
            "treat that request as confirmation",
            "before substantive implementation",
            "Do not classify substantive first-project work as incidental",
        ):
            self.assertIn(marker, core)
        for marker in (
            "publish and validate a real `ready` Mission",
            "`forge-compact --replace-from`",
            "Only then may substantive implementation begin",
        ):
            self.assertIn(marker, memory)

    def test_completion_uses_exact_state_tokens_and_post_write_validation(
        self,
    ) -> None:
        state = self.section_text(MEMORY, "Mission state")
        checkpoint = self.section_text(MEMORY, "Checkpoint triggers")
        for marker in (
            "wire-format tokens",
            "`completed` is invalid",
        ):
            self.assertIn(marker, state)
        for marker in (
            "`forge-checkpoint PROJECT_ROOT --state done`",
            "publish a validated `working` Mission first",
            "After every active-memory write, run `forge-memory-validate`",
            "Do not report a checkpoint or completion until validation passes",
        ):
            self.assertIn(marker, checkpoint)
        self.assertIn(
            "Do not report Mission completion until post-write validation passes",
            self.core_text(),
        )

    def test_complex_task_asks_once_and_loop_refusal_keeps_original_authority(
        self,
    ) -> None:
        text = self.core_text()
        for marker in ("Outcome:", "Done when:", "Boundaries:", "Budget:"):
            self.assertEqual(1, text.count(marker), marker)
        self.assertIn("Ask once", text)
        self.assertIn("Do not enter Loop automatically", text)
        self.assertIn("Declining Loop is not cancelling the original task", text)
        self.assertIn(
            "one minimum safe Core delivery, a plan-only response, or stop",
            text,
        )

    def test_solution_choice_uses_the_minimum_solution_ladder(self) -> None:
        text = self.core_text()
        self.assertIn("understand the existing control flow and data flow first", text)
        markers = (
            "1. Confirm each criterion is necessary",
            "2. Reuse the existing repository",
            "3. Prefer the standard library or native capability",
            "4. Use an already-installed dependency",
            "5. Build the minimum safe custom solution",
        )
        positions = [text.index(marker) for marker in markers]
        self.assertEqual(sorted(positions), positions)

    def test_core_uses_one_systems_reasoning_kernel_across_artifacts(self) -> None:
        kernel = self.section_text(CORE, "Reason through the current artifact")
        for marker in (
            "outcome and boundary",
            "system position",
            "flow and state",
            "failure and risk",
            "falsifying evidence",
            "evolution cost",
        ):
            self.assertIn(marker, kernel)
        for lens in (
            "Documentation",
            "Architecture",
            "UI/UX",
            "Code",
            "Testing",
        ):
            self.assertIn(lens, kernel)
        self.assertIn("one primary lens", kernel)
        self.assertIn("supporting lens", kernel)
        self.assertIn("changes a design, action, or check", kernel)
        self.assertIn("not roles", kernel)

    def test_artifact_lens_titles_are_closed_and_distinct_from_actions(self) -> None:
        kernel = self.section_text(CORE, "Reason through the current artifact")
        selection = self.section_text(CORE, "Select the minimum host capability set")
        self.assertIn(
            "The canonical artifact lens titles are exactly Documentation, "
            "Architecture, UI/UX, Code, and Testing",
            kernel,
        )
        self.assertIn("closed set", kernel)
        self.assertIn(
            "Discovery, design, implementation, verification, and external "
            "interaction are capability or action categories, not artifact lenses",
            selection,
        )

    def test_active_mission_is_a_validated_destination_not_a_draft(self) -> None:
        memory = self.memory_text()
        for marker in (
            "active `.forge/MISSION.md` is a publication destination, never a draft",
            "outside the active `.forge/MISSION.md` path",
            "`ready` with `checkpointed_at: null`",
            "preserve the current State and checkpointed_at",
            "then use `forge-checkpoint` for the real state transition",
        ):
            self.assertIn(marker, memory)

    def test_routine_checkpoints_do_not_mirror_mission_into_intent(self) -> None:
        memory = self.memory_text()
        for marker in (
            "Routine checkpoints update MISSION only",
            "user-confirmed durable project-level",
            "Do not mirror Mission Outcome, State, Latest Delivery, Next Action, "
            "Blockers, Last Check, or Resume into INTENT Direction",
        ):
            self.assertIn(marker, memory)

    def test_durable_intent_updates_use_prevalidated_atomic_publication(self) -> None:
        memory = self.memory_text()
        for marker in (
            "render the complete INTENT candidate outside the active path",
            "`forge-intent PROJECT_ROOT --replace-from INTENT_FILE`",
            "prevalidates all candidate bytes",
            "atomically replaces `.forge/INTENT.md`",
            "Never create, truncate, or patch active INTENT as an intermediate draft",
        ):
            self.assertIn(marker, memory)

    def test_core_selects_a_minimum_host_capability_set_without_a_router(
        self,
    ) -> None:
        selection = self.section_text(CORE, "Select the minimum host capability set")
        for action in (
            "discovery",
            "design",
            "implementation",
            "verification",
            "external interaction",
        ):
            self.assertIn(action, selection)
        markers = (
            "direct native capability",
            "one specialized Skill",
            "specialized MCP or external tool",
            "necessary combination",
            "generic capability",
        )
        positions = [selection.index(marker) for marker in markers]
        self.assertEqual(sorted(positions), positions)
        self.assertIn("host actually exposes", selection)
        self.assertIn("Re-evaluate", selection)
        self.assertIn("visible delta, artifact, or risk changes", selection)
        self.assertIn("Do not persist lens or tool selection", selection)
        self.assertIn("central registry", selection)
        self.assertIn("scoring database", selection)
        self.assertIn("deterministic router", selection)

    def test_capability_matching_uses_discoverable_host_descriptions(
        self,
    ) -> None:
        selection = self.section_text(CORE, "Select the minimum host capability set")
        for marker in (
            "task or artifact triggers",
            "expected output and check",
            "non-use cases",
            "authority and side-effect boundary",
            "safe combinations",
            "unsupported custom frontmatter",
        ):
            self.assertIn(marker, selection)

    def test_clarification_is_reserved_for_material_ambiguity(self) -> None:
        text = self.core_text()
        self.assertIn("Clarify only material ambiguity", text)
        self.assertIn("small, reversible assumption", text)
        self.assertIn("report it", text)

    def test_verification_uses_minimum_falsifying_evidence_and_honest_levels(
        self,
    ) -> None:
        text = self.core_text()
        self.assertIn("minimum sufficient falsifying evidence", text)
        self.assertIn(
            "`unverified -> smoke_verified -> locally_verified -> reviewed -> ci_verified`",
            text,
        )
        self.assertIn("cumulative", text)
        self.assertIn("independent", text)
        self.assertIn("real CI", text)

    def test_workflow_choice_never_grants_external_side_effect_authority(self) -> None:
        text = self.core_text()
        self.assertIn(
            "No mode, profile, or workflow choice grants permission for external side effects",
            text,
        )

    def test_core_rejects_automatic_modes_and_fixed_role_pipelines(self) -> None:
        loop = self.section_text(CORE, "Offer Loop once for complex work")
        self.assert_forbidden_markers(
            loop,
            "Enter Loop automatically.",
            "Start Loop automatically.",
            "Assurance starts automatically.",
        )
        self.assert_forbidden_markers(
            self.core_text(),
            "PM -> Architect -> Developer -> Tester -> Reviewer",
            "PM/Architect/Developer/Tester/Reviewer",
            "Always select a profile",
            "Delegate every task",
        )

    def test_core_rejects_unconditional_checkpoints_for_unrelated_work(self) -> None:
        unrelated = self.section_text(CORE, "Keep unrelated work separate")
        self.assert_forbidden_markers(
            unrelated,
            "Always checkpoint",
            "checkpoint every pure question",
            "checkpoint every incidental change",
            "checkpoint after every request",
        )

    def test_core_rejects_implied_external_effect_authority(self) -> None:
        authority = self.section_text(CORE, "Preserve external-effect authority")
        self.assert_forbidden_markers(
            authority,
            "implies permission",
            "grants permission to commit",
            "may push without user",
            "may deploy without user",
        )

    def test_memory_names_frozen_and_mutable_mission_fields(self) -> None:
        text = self.memory_text()
        self.assertIn("Outcome, Scope, and Success Criteria", text)
        for marker in (
            "Latest Delivery",
            "Next Action",
            "Blockers",
            "Last Check",
            "Resume",
        ):
            self.assertIn(marker, text)

    def test_memory_checkpoints_only_real_transitions(self) -> None:
        text = self.memory_text()
        self.assertIn("Checkpoint only a real transition", text)
        self.assertIn("A checkpoint is mandatory when a real transition occurs", text)
        self.assertIn("pure question", text)
        self.assertIn("read-only lookup", text)

    def test_core_confirms_only_after_comparing_for_material_conflict(self) -> None:
        text = self.core_text()
        self.assertIn("compare it with active INTENT and MISSION", text)
        self.assertIn("expose the conflict and ask the user", text)
        self.assertIn("Do not add another confirmation turn", text)

    def test_archive_promotion_requires_separate_confirmation(self) -> None:
        text = self.memory_text()
        self.assertIn("archive promotion", text)
        self.assertIn("separate user confirmation", text)

    def test_memory_gives_an_executable_concise_schema_summary(self) -> None:
        text = MEMORY.read_text(encoding="utf-8")
        schema = self.section_text(MEMORY, "Concise active-memory schema")
        for marker in ("- In:", "- Out:", "- Constraints:"):
            self.assertIn(marker, text)
        self.assertIn("at least one of each Scope line", schema)
        self.assertIn("- [ ] <nonempty criterion>", text)
        self.assertIn("- [x] <nonempty completed criterion>", text)
        self.assertIn("one or more nonempty checklist items", schema)
        self.assertIn("INTENT has a maximum of 100 lines", schema)
        self.assertIn("MISSION has a maximum of 60 lines", schema)

    def test_checkpoint_and_acceptance_boundary_updates_use_safe_paths(self) -> None:
        checkpoint = self.section_text(MEMORY, "Checkpoint triggers")
        self.assertIn("forge-checkpoint mutates only continuity fields", checkpoint)
        self.assertIn(
            "State, checkpoint timestamp, Latest Delivery, Next Action, "
            "Blockers, Last Check, and Resume.Do",
            checkpoint,
        )
        self.assertIn("replacement MISSION file", self.memory_text())
        self.assertIn(
            "direct validated host rewrite through the shared safe-write semantics",
            checkpoint,
        )
        self.assertIn(
            "user-confirmed Scope or Success Criteria",
            checkpoint,
        )


if __name__ == "__main__":
    unittest.main()
