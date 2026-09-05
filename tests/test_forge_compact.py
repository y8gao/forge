from __future__ import annotations

import errno
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/forge/scripts/forge-compact"
FIXTURE = ROOT / "tests/fixtures/memory_first/.forge"
LIB = ROOT / "plugins/forge/lib"
sys.path.insert(0, str(LIB))

from forge_memory import load_mission  # noqa: E402


def render_mission(
    mission_id: str = "current-mission",
    *,
    state: str = "done",
    outcome: str = "Ship the current visible increment.",
) -> str:
    return (
        "---\n"
        'format: "forge-memory-v1"\n'
        f'mission_id: "{mission_id}"\n'
        f'state: "{state}"\n'
        'checkpointed_at: "2026-09-02T01:02:03Z"\n'
        "---\n"
        "# Current Mission\n\n"
        "## Outcome\n"
        f"- Statement: {outcome}\n\n"
        "## Scope\n"
        "- In: Complete the current visible increment.\n"
        "- Out: Unconfirmed follow-up work.\n"
        "- Constraints: Keep MISSION within 60 lines.\n\n"
        "## Success Criteria\n"
        "- [x] The current visible increment is complete.\n\n"
        "## Latest Delivery\n"
        "- Implemented the current mission.\n\n"
        "## Next Action\n"
        "- Compact the current mission.\n\n"
        "## Blockers\n"
        "- None.\n\n"
        "## Last Check\n"
        "- Ran: focused checks\n"
        "- Boundary: compaction only\n\n"
        "## Resume\n"
        "- Read: `.forge/INTENT.md` and `.forge/MISSION.md`.\n"
        "- Do: compact the current mission.\n"
    )


class ForgeCompactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary_directory.name) / "project"
        self.forge = self.project / ".forge"
        self.forge.mkdir(parents=True)
        (self.forge / "INTENT.md").write_bytes((FIXTURE / "INTENT.md").read_bytes())
        (self.forge / "MISSION.md").write_text(render_mission(), encoding="utf-8")
        (self.forge / "archive").mkdir()
        (self.forge / "decisions").mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @property
    def mission_path(self) -> Path:
        return self.forge / "MISSION.md"

    @property
    def archive_path(self) -> Path:
        return self.forge / "archive/current-mission/MISSION.final.md"

    def run_compact(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(self.project), *arguments],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_in_process(
        self,
        arguments: list[str],
        atomic_write,
    ) -> tuple[int, dict[str, object]]:
        namespace = runpy.run_path(str(SCRIPT), run_name="forge_compact_test")
        with mock.patch.dict(
            namespace["main"].__globals__,
            {"atomic_write": atomic_write},
        ):
            code = namespace["main"](arguments)
        return code, namespace

    def assert_controlled_failure(self, result) -> None:
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-compact ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def replacement_path(
        self,
        mission_id: str = "next-mission",
        outcome: str = "Ship the next visible increment.",
    ) -> Path:
        path = self.project / f"{mission_id}.md"
        path.write_text(
            render_mission(
                mission_id,
                state="ready",
                outcome=outcome,
            ).replace(
                "- In: Complete the current visible increment.",
                "- In: Deliver only the user-confirmed next increment.",
            ).replace(
                "- [x] The current visible increment is complete.",
                "- [ ] The user-confirmed next increment has observable evidence.",
            ),
            encoding="utf-8",
        )
        return path

    def test_help_uses_normal_argparse_success_output(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage: forge-compact", result.stdout)
        self.assertEqual("", result.stderr)
        self.assertNotIn("forge-compact ERROR:", result.stdout)
        self.assertNotIn("Traceback", result.stdout)

    def create_symlink(
        self, link: Path, target: Path, *, target_is_directory: bool
    ) -> None:
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EPERM) or getattr(
                error, "winerror", None
            ) == 1314:
                self.skipTest(f"symlink creation is not permitted: {error}")
            raise
        except NotImplementedError as error:
            self.skipTest(f"symlinks are unsupported: {error}")

    def test_complete_archives_exact_bytes_and_leaves_done_mission_closed(self) -> None:
        original = self.mission_path.read_bytes()
        intent = (self.forge / "INTENT.md").read_bytes()

        result = self.run_compact("--complete")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "forge-compact archived current-mission; active mission remains done\n",
            result.stdout,
        )
        self.assertEqual(original, self.archive_path.read_bytes())
        self.assertEqual(original, self.mission_path.read_bytes())
        self.assertEqual(intent, (self.forge / "INTENT.md").read_bytes())

    def test_replace_activates_exact_prevalidated_mission(self) -> None:
        original = self.mission_path.read_bytes()
        outcome = "Ship the next visible increment."
        replacement_path = self.replacement_path(outcome=outcome)
        replacement = replacement_path.read_bytes()

        result = self.run_compact("--replace-from", str(replacement_path))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(original, self.archive_path.read_bytes())
        self.assertEqual(replacement, self.mission_path.read_bytes())
        mission = load_mission(self.mission_path)
        self.assertEqual("next-mission", mission.mission_id)
        self.assertEqual("ready", mission.state)
        self.assertEqual(outcome, mission.outcome)
        self.assertEqual(
            ("Deliver only the user-confirmed next increment.",), mission.scope_in
        )
        self.assertEqual(
            ("[ ] The user-confirmed next increment has observable evidence.",),
            mission.success_criteria,
        )
        self.assertLess(len(self.mission_path.read_text(encoding="utf-8").splitlines()), 60)

    def test_invalid_replacement_fails_before_any_managed_write(self) -> None:
        from forge_files import atomic_write as real_atomic_write

        original = self.mission_path.read_bytes()
        writes: list[Path] = []
        replacement = self.project / "replacement.md"
        replacement.write_text("invalid mission\n", encoding="utf-8")

        def recording_write(root, path, data, *, mode=None):
            writes.append(Path(path))
            return real_atomic_write(root, path, data, mode=mode)

        namespace = runpy.run_path(str(SCRIPT), run_name="forge_compact_test")
        with mock.patch.dict(
            namespace["main"].__globals__,
            {"atomic_write": recording_write},
        ), mock.patch.object(namespace["sys"], "stderr") as error_stream:
            code = namespace["main"](
                [str(self.project), "--replace-from", str(replacement)]
            )

        self.assertNotEqual(0, code)
        error_text = "".join(
            call.args[0] for call in error_stream.write.call_args_list
        )
        self.assertIn("forge-compact ERROR:", error_text)
        self.assertNotIn("Traceback", error_text)
        self.assertEqual(original, self.mission_path.read_bytes())
        self.assertFalse(self.archive_path.exists())
        self.assertEqual([], writes)

    def test_archive_atomic_write_precedes_active_atomic_write(self) -> None:
        from forge_files import atomic_write as real_atomic_write

        writes: list[Path] = []

        def recording_write(root, path, data, *, mode=None):
            writes.append(Path(path))
            return real_atomic_write(root, path, data, mode=mode)

        code, _ = self.run_in_process(
            [
                str(self.project),
                "--replace-from",
                str(self.replacement_path()),
            ],
            recording_write,
        )

        self.assertEqual(0, code)
        self.assertEqual([self.archive_path, self.mission_path], writes)

    def test_identical_existing_archive_is_reused(self) -> None:
        original = self.mission_path.read_bytes()
        self.archive_path.parent.mkdir()
        self.archive_path.write_bytes(original)

        result = self.run_compact("--complete")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(original, self.archive_path.read_bytes())
        self.assertEqual(original, self.mission_path.read_bytes())

    def test_different_existing_archive_fails_closed(self) -> None:
        original = self.mission_path.read_bytes()
        self.archive_path.parent.mkdir()
        self.archive_path.write_bytes(b"different archive\n")

        result = self.run_compact("--complete")

        self.assert_controlled_failure(result)
        self.assertIn("archive", result.stderr.lower())
        self.assertEqual(original, self.mission_path.read_bytes())
        self.assertEqual(b"different archive\n", self.archive_path.read_bytes())

    def test_archive_publication_failure_preserves_active(self) -> None:
        from forge_files import atomic_write as real_atomic_write

        original = self.mission_path.read_bytes()

        def fail_archive(root, path, data, *, mode=None):
            if Path(path) == self.archive_path:
                raise OSError("archive publish failed")
            return real_atomic_write(root, path, data, mode=mode)

        code, _ = self.run_in_process(
            [str(self.project), "--complete"], fail_archive
        )

        self.assertNotEqual(0, code)
        self.assertEqual(original, self.mission_path.read_bytes())
        self.assertFalse(self.archive_path.exists())

    def test_active_replace_failure_keeps_archive_and_explains_retry(self) -> None:
        from forge_files import atomic_write as real_atomic_write

        original = self.mission_path.read_bytes()
        replacement = self.replacement_path()

        def fail_active(root, path, data, *, mode=None):
            if Path(path) == self.mission_path:
                raise ValueError("active path became unsafe")
            return real_atomic_write(root, path, data, mode=mode)

        stderr = []
        namespace = runpy.run_path(str(SCRIPT), run_name="forge_compact_test")
        with mock.patch.dict(
            namespace["main"].__globals__, {"atomic_write": fail_active}
        ), mock.patch.object(namespace["sys"], "stderr") as error_stream:
            error_stream.write.side_effect = stderr.append
            code = namespace["main"](
                [str(self.project), "--replace-from", str(replacement)]
            )

        self.assertNotEqual(0, code)
        self.assertEqual(original, self.mission_path.read_bytes())
        self.assertEqual(original, self.archive_path.read_bytes())
        message = "".join(stderr).lower()
        self.assertIn("archive", message)
        self.assertRegex(message, r"retry|recover")

    def test_retry_after_active_failure_reuses_archive(self) -> None:
        from forge_files import atomic_write as real_atomic_write

        original = self.mission_path.read_bytes()
        replacement = self.replacement_path()

        def fail_active(root, path, data, *, mode=None):
            if Path(path) == self.mission_path:
                raise OSError("active replace failed")
            return real_atomic_write(root, path, data, mode=mode)

        code, _ = self.run_in_process(
            [str(self.project), "--replace-from", str(replacement)], fail_active
        )
        self.assertNotEqual(0, code)

        retry = self.run_compact("--replace-from", str(replacement))

        self.assertEqual(0, retry.returncode, retry.stderr)
        self.assertEqual(original, self.archive_path.read_bytes())
        self.assertEqual("next-mission", load_mission(self.mission_path).mission_id)

    def test_identical_replace_retry_after_success_is_noop(self) -> None:
        replacement = self.replacement_path()
        arguments = ("--replace-from", str(replacement))
        first = self.run_compact(*arguments)
        self.assertEqual(0, first.returncode, first.stderr)
        active = self.mission_path.read_bytes()
        archives = {
            path.relative_to(self.forge): path.read_bytes()
            for path in (self.forge / "archive").rglob("*.md")
        }

        retry = self.run_compact(*arguments)

        self.assertEqual(0, retry.returncode, retry.stderr)
        self.assertEqual("forge-compact already active: next-mission\n", retry.stdout)
        self.assertEqual(active, self.mission_path.read_bytes())
        self.assertEqual(
            archives,
            {
                path.relative_to(self.forge): path.read_bytes()
                for path in (self.forge / "archive").rglob("*.md")
            },
        )

    def test_same_id_with_different_outcome_fails_before_writes(self) -> None:
        first_replacement = self.replacement_path(outcome="First outcome.")
        first = self.run_compact("--replace-from", str(first_replacement))
        self.assertEqual(0, first.returncode, first.stderr)
        active = self.mission_path.read_bytes()
        snapshot = {
            path.relative_to(self.forge): path.read_bytes()
            for path in (self.forge / "archive").rglob("*.md")
        }

        different = self.replacement_path(outcome="Different outcome.")
        result = self.run_compact("--replace-from", str(different))

        self.assert_controlled_failure(result)
        self.assertIn("active mission ID", result.stderr)
        self.assertEqual(active, self.mission_path.read_bytes())
        self.assertEqual(
            snapshot,
            {
                path.relative_to(self.forge): path.read_bytes()
                for path in (self.forge / "archive").rglob("*.md")
            },
        )

    def test_invalid_state_and_inputs_fail_without_writes(self) -> None:
        missing = self.project / "missing.md"
        unsafe = self.project / "unsafe.md"
        unsafe.write_text(
            render_mission("../escape", state="ready"),
            encoding="utf-8",
        )
        nonready = self.replacement_path("nonready")
        nonready.write_text(render_mission("nonready", state="working"), encoding="utf-8")
        cases = [
            ("working state", ["--complete"]),
            ("missing replacement", ["--replace-from", str(missing)]),
            ("unsafe id", ["--replace-from", str(unsafe)]),
            ("nonready replacement", ["--replace-from", str(nonready)]),
        ]
        for name, arguments in cases:
            with self.subTest(name=name):
                self.mission_path.write_text(
                    render_mission(state="working" if name == "working state" else "done"),
                    encoding="utf-8",
                )
                original = self.mission_path.read_bytes()
                result = self.run_compact(*arguments)
                self.assert_controlled_failure(result)
                self.assertEqual(original, self.mission_path.read_bytes())
                self.assertFalse(self.archive_path.exists())

    def test_invalid_intent_and_mission_fail_without_writes(self) -> None:
        for name in ("INTENT.md", "MISSION.md"):
            with self.subTest(name=name):
                path = self.forge / name
                saved = path.read_bytes()
                path.write_bytes(b"invalid\n")
                result = self.run_compact("--complete")
                self.assert_controlled_failure(result)
                self.assertFalse(self.archive_path.exists())
                path.write_bytes(saved)

    def test_managed_paths_are_validated_through_shared_helper(self) -> None:
        from forge_files import validate_managed_path as real_validate

        checked: list[Path] = []

        def recording_validate(root, path):
            checked.append(Path(path))
            return real_validate(root, path)

        namespace = runpy.run_path(str(SCRIPT), run_name="forge_compact_test")
        with mock.patch.dict(
            namespace["main"].__globals__,
            {"validate_managed_path": recording_validate},
        ):
            code = namespace["main"]([str(self.project), "--complete"])

        self.assertEqual(0, code)
        self.assertTrue(
            {
                self.project,
                self.forge,
                self.forge / "archive",
                self.archive_path.parent,
                self.archive_path,
                self.mission_path,
            }.issubset(set(checked))
        )

    def test_symlinked_mission_and_archive_descendant_are_rejected(self) -> None:
        external = self.project.parent / "external"
        external.mkdir()

        with self.subTest("MISSION"):
            external_mission = external / "MISSION.md"
            external_mission.write_text(render_mission(), encoding="utf-8")
            self.mission_path.unlink()
            self.create_symlink(
                self.mission_path, external_mission, target_is_directory=False
            )
            result = self.run_compact("--complete")
            self.assert_controlled_failure(result)
            self.assertEqual(render_mission(), external_mission.read_text(encoding="utf-8"))
            self.mission_path.unlink()
            self.mission_path.write_text(render_mission(), encoding="utf-8")

        with self.subTest("archive descendant"):
            self.create_symlink(
                self.archive_path.parent, external, target_is_directory=True
            )
            result = self.run_compact("--complete")
            self.assert_controlled_failure(result)
            self.assertEqual([], list(external.glob("MISSION.final.md")))

    def test_compact_does_not_create_transaction_journal(self) -> None:
        result = self.run_compact("--complete")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertFalse((self.forge / ".compact-transaction.json").exists())


if __name__ == "__main__":
    unittest.main()
