from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "plugins" / "forge" / "scripts"
PORTABLE = (
    ROOT
    / "plugins"
    / "forge"
    / "skills"
    / "forge-memory"
    / "assets"
    / "portable"
    / "scripts"
)
LIB = ROOT / "plugins" / "forge" / "lib"
sys.path.insert(0, str(LIB))

from forge_memory import load_mission  # noqa: E402


def active_mission() -> str:
    return """\
---
format: "forge-memory-v1"
mission_id: "lifecycle-feature"
state: "ready"
checkpointed_at: null
---
# Current Mission

## Outcome
- Statement: Deliver and repair one lifecycle feature.

## Scope
- In: One feature and its corrective bugfix.
- Out: Unrelated project work.
- Constraints: Preserve the confirmed acceptance boundary.

## Success Criteria
- [ ] The feature and corrective bugfix are verified.

## Latest Delivery
- Activated the confirmed lifecycle feature.

## Next Action
- Implement the feature.

## Blockers
- None.

## Last Check
- Ran: Initial activation validation.
- Boundary: No feature behavior has been delivered.

## Resume
- Read: `.forge/INTENT.md` and `.forge/MISSION.md`.
- Do: Implement the feature.
"""


class MemoryLifecycleTests(unittest.TestCase):
    def run_helper(
        self,
        scripts: Path,
        name: str,
        project: Path,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(scripts / name), str(project), *arguments],
            cwd=project,
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_success(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("", result.stderr)

    def checkpoint(
        self,
        scripts: Path,
        project: Path,
        *,
        state: str,
        delivery: str,
        next_action: str,
        check_run: str,
    ) -> None:
        result = self.run_helper(
            scripts,
            "forge-checkpoint",
            project,
            "--state",
            state,
            "--delivery",
            delivery,
            "--next-action",
            next_action,
            "--check-run",
            check_run,
            "--check-boundary",
            "Only the lifecycle scenario was checked.",
        )
        self.assert_success(result)
        self.assert_success(
            self.run_helper(scripts, "forge-memory-validate", project)
        )

    def test_init_delivery_bugfix_and_completion_lifecycle(self) -> None:
        for label, scripts in (
            ("canonical", CANONICAL),
            ("portable", PORTABLE),
        ):
            with self.subTest(runtime=label), tempfile.TemporaryDirectory() as temp:
                project = Path(temp) / "project"
                project.mkdir()

                initialized = self.run_helper(
                    scripts, "forge-init", project
                )
                self.assert_success(initialized)
                self.assertIn(
                    "activate the placeholder Mission before substantive work",
                    initialized.stdout,
                )
                self.assertEqual(
                    "initial",
                    load_mission(project / ".forge" / "MISSION.md").mission_id,
                )

                replacement = project / "MISSION.next.md"
                replacement.write_text(active_mission(), encoding="utf-8")
                activated = self.run_helper(
                    scripts,
                    "forge-compact",
                    project,
                    "--replace-from",
                    str(replacement),
                )
                self.assert_success(activated)
                self.assert_success(
                    self.run_helper(
                        scripts, "forge-memory-validate", project
                    )
                )

                mission_path = project / ".forge" / "MISSION.md"
                activated_mission = load_mission(mission_path)
                self.assertEqual("lifecycle-feature", activated_mission.mission_id)
                self.assertEqual("ready", activated_mission.state)

                self.checkpoint(
                    scripts,
                    project,
                    state="working",
                    delivery="Implemented the lifecycle feature.",
                    next_action="Repair the reported edge case.",
                    check_run="feature regression passed",
                )
                feature = load_mission(mission_path)
                acceptance_boundary = (
                    feature.mission_id,
                    feature.outcome,
                    feature.scope_in,
                    feature.scope_out,
                    feature.scope_constraints,
                    feature.success_criteria,
                )

                self.checkpoint(
                    scripts,
                    project,
                    state="working",
                    delivery="Repaired the reported edge case.",
                    next_action="Complete the lifecycle mission.",
                    check_run="feature and bugfix regressions passed",
                )
                bugfix = load_mission(mission_path)
                self.assertEqual(
                    acceptance_boundary,
                    (
                        bugfix.mission_id,
                        bugfix.outcome,
                        bugfix.scope_in,
                        bugfix.scope_out,
                        bugfix.scope_constraints,
                        bugfix.success_criteria,
                    ),
                )

                completed_boundary = mission_path.read_text(
                    encoding="utf-8"
                ).replace(
                    "- [ ] The feature and corrective bugfix are verified.",
                    "- [x] The feature and corrective bugfix are verified.",
                )
                mission_path.write_text(completed_boundary, encoding="utf-8")
                self.assert_success(
                    self.run_helper(
                        scripts, "forge-memory-validate", project
                    )
                )
                self.checkpoint(
                    scripts,
                    project,
                    state="done",
                    delivery="Delivered and repaired the lifecycle feature.",
                    next_action="Await the next confirmed mission.",
                    check_run="full lifecycle regression passed",
                )

                completed = load_mission(mission_path)
                self.assertEqual("done", completed.state)
                self.assertEqual(
                    "[x] The feature and corrective bugfix are verified.",
                    completed.success_criteria[0],
                )
                status = self.run_helper(
                    scripts, "forge-status", project
                )
                self.assert_success(status)
                self.assertIn("- **State:** `done`", status.stdout)
                self.assertIn(
                    "Delivered and repaired the lifecycle feature.",
                    status.stdout,
                )
                if label == "portable":
                    self.assertEqual(
                        [],
                        list(PORTABLE.parent.rglob("__pycache__")),
                        "portable helpers must not mutate packaged resources",
                    )


if __name__ == "__main__":
    unittest.main()
