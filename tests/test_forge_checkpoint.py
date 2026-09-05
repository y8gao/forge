from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock
import errno
import os
import runpy
import stat
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = ROOT / "plugins/forge/scripts/forge-checkpoint"
FIXTURE = ROOT / "tests/fixtures/memory_first/.forge"
LIB = ROOT / "plugins/forge/lib"
sys.path.insert(0, str(LIB))

import forge_files  # noqa: E402
from forge_memory import load_mission  # noqa: E402


class ForgeCheckpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary_directory.name) / "project"
        self.forge = self.project / ".forge"
        self.forge.mkdir(parents=True)
        for name in ("INTENT.md", "MISSION.md"):
            (self.forge / name).write_bytes((FIXTURE / name).read_bytes())
        (self.forge / "archive").mkdir()
        (self.forge / "decisions").mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def arguments(self, *, state: str = "working") -> list[str]:
        arguments = [
            str(self.project),
            "--state",
            state,
            "--delivery",
            "Added the first resumable checkpoint.",
            "--next-action",
            "Run the focused checkpoint test.",
            "--check-run",
            "python -m unittest tests.test_forge_checkpoint -v",
            "--check-boundary",
            "Only checkpoint behavior was tested.",
        ]
        if state == "blocked":
            arguments.extend(["--blocker", "User decision required."])
        return arguments

    def run_checkpoint(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKPOINT), *arguments],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_checkpoint_in_process(
        self, *arguments: str
    ) -> subprocess.CompletedProcess[str]:
        namespace = runpy.run_path(
            str(CHECKPOINT), run_name="forge_checkpoint_test"
        )
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            returncode = namespace["main"](list(arguments))
        return subprocess.CompletedProcess(
            list(arguments),
            returncode,
            stdout.getvalue(),
            stderr.getvalue(),
        )

    def test_help_uses_normal_argparse_success_output(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CHECKPOINT), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("usage: forge-checkpoint", result.stdout)
        self.assertEqual("", result.stderr)
        self.assertNotIn("forge-checkpoint ERROR:", result.stdout)
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

    def create_junction(self, link: Path, target: Path) -> None:
        if os.name != "nt":
            self.skipTest("Windows junction regression")
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            self.skipTest(
                f"junction creation failed: {result.stdout}{result.stderr}"
            )

    def test_updates_only_mutable_mission_fields(self):
        before_entries = {
            path.relative_to(self.project).as_posix()
            for path in self.project.rglob("*")
        }
        original = load_mission(self.forge / "MISSION.md")

        result = self.run_checkpoint(*self.arguments(state="blocked"))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        updated = load_mission(self.forge / "MISSION.md")
        self.assertEqual("blocked", updated.state)
        self.assertRegex(
            updated.checkpointed_at or "",
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        )
        self.assertEqual(
            "Added the first resumable checkpoint.", updated.latest_delivery
        )
        self.assertEqual(
            "Run the focused checkpoint test.", updated.next_action
        )
        self.assertEqual(
            "python -m unittest tests.test_forge_checkpoint -v",
            updated.last_check_run,
        )
        self.assertEqual(
            "Only checkpoint behavior was tested.", updated.last_check_boundary
        )
        self.assertEqual(original.mission_id, updated.mission_id)
        self.assertEqual(original.outcome, updated.outcome)
        self.assertEqual(("User decision required.",), updated.blockers)
        self.assertEqual(original.resume_read, updated.resume_read)
        self.assertEqual(
            "Run the focused checkpoint test.", updated.resume_do
        )
        self.assertEqual(
            before_entries,
            {
                path.relative_to(self.project).as_posix()
                for path in self.project.rglob("*")
            },
        )

    def test_cli_update_uses_shared_helper_and_cleans_temp_file(self):
        target = self.forge / "MISSION.md"

        result = self.run_checkpoint(*self.arguments())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(f"forge-checkpoint updated {target}\n", result.stdout)
        self.assertEqual("", result.stderr)
        self.assertEqual(
            [],
            [path for path in self.forge.iterdir() if path.name.startswith(".MISSION.")],
        )

    def test_shared_helper_failure_is_controlled_and_preserves_target(self):
        target = self.forge / "MISSION.md"
        original = target.read_bytes()

        with mock.patch.object(
            forge_files.os, "replace", side_effect=OSError("boom")
        ):
            result = self.run_checkpoint_in_process(*self.arguments())

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-checkpoint ERROR: boom", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original, target.read_bytes())
        self.assertEqual(
            [],
            [path for path in self.forge.iterdir() if path.name.startswith(".MISSION.")],
        )

    def test_done_with_incomplete_criteria_is_controlled_and_preserves_target(self):
        target = self.forge / "MISSION.md"
        original = target.read_bytes()

        result = self.run_checkpoint(*self.arguments(state="done"))

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertRegex(
            result.stderr,
            r"^forge-checkpoint ERROR: .*done.*success criteria.*\n$",
        )
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original, target.read_bytes())

    def test_blocked_requires_current_blocker_and_preserves_target(self):
        target = self.forge / "MISSION.md"
        original = target.read_bytes()
        arguments = self.arguments(state="blocked")
        blocker_index = arguments.index("--blocker")
        del arguments[blocker_index : blocker_index + 2]

        result = self.run_checkpoint(*arguments)

        self.assertEqual(1, result.returncode)
        self.assertRegex(result.stderr, r"blocked.*blocker")
        self.assertEqual(original, target.read_bytes())

    def test_nonblocked_checkpoint_clears_blocker_and_syncs_resume(self):
        target = self.forge / "MISSION.md"
        target.write_text(
            target.read_text(encoding="utf-8").replace(
                "- None.", "- Stale blocker from a prior stop.", 1
            ),
            encoding="utf-8",
        )

        result = self.run_checkpoint(*self.arguments(state="working"))

        self.assertEqual(0, result.returncode, result.stderr)
        updated = load_mission(target)
        self.assertEqual(("None.",), updated.blockers)
        self.assertEqual(updated.next_action, updated.resume_do)

    def test_shared_helper_applies_original_mode_before_replace(self):
        target = self.forge / "MISSION.md"
        target.chmod(0o444)
        original_mode = stat.S_IMODE(target.stat().st_mode)
        observed_mode = None

        def inspect_mode(source: str | os.PathLike[str], destination: Path) -> None:
            nonlocal observed_mode
            observed_mode = stat.S_IMODE(Path(source).stat().st_mode)
            raise OSError("stop before replacement")

        try:
            with mock.patch.object(
                forge_files.os, "replace", side_effect=inspect_mode
            ):
                result = self.run_checkpoint_in_process(*self.arguments())
        finally:
            target.chmod(0o666)

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-checkpoint ERROR: stop before replacement", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original_mode, observed_mode)

    @unittest.skipIf(os.name == "nt", "POSIX mode semantics")
    def test_cli_update_preserves_existing_posix_mode(self):
        target = self.forge / "MISSION.md"
        target.chmod(0o640)

        result = self.run_checkpoint(*self.arguments())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(0o640, stat.S_IMODE(target.stat().st_mode))

    def test_rejects_symlinked_forge_directory_without_external_mutation(self):
        external = self.project.parent / "external-forge"
        external.mkdir()
        for name in ("INTENT.md", "MISSION.md"):
            (external / name).write_bytes((FIXTURE / name).read_bytes())
        (external / "archive").mkdir()
        (external / "decisions").mkdir()
        original = (external / "MISSION.md").read_bytes()
        for path in tuple(self.forge.iterdir()):
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
        self.forge.rmdir()
        self.create_symlink(self.forge, external, target_is_directory=True)

        result = self.run_checkpoint(*self.arguments())

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-checkpoint ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original, (external / "MISSION.md").read_bytes())

    def test_rejects_forge_junction_without_external_mutation(self):
        external = self.project.parent / "external-junction"
        external.mkdir()
        for name in ("INTENT.md", "MISSION.md"):
            (external / name).write_bytes((FIXTURE / name).read_bytes())
        (external / "archive").mkdir()
        (external / "decisions").mkdir()
        original = (external / "MISSION.md").read_bytes()
        for path in tuple(self.forge.iterdir()):
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
        self.forge.rmdir()
        self.create_junction(self.forge, external)

        result = self.run_checkpoint(*self.arguments())

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-checkpoint ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original, (external / "MISSION.md").read_bytes())

    def test_rejects_symlinked_mission_without_replacing_link(self):
        mission = self.forge / "MISSION.md"
        mission.unlink()
        external = self.project.parent / "external-mission.md"
        external.write_bytes((FIXTURE / "MISSION.md").read_bytes())
        original = external.read_bytes()
        self.create_symlink(mission, external, target_is_directory=False)

        result = self.run_checkpoint(*self.arguments())

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-checkpoint ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertTrue(mission.is_symlink())
        self.assertEqual(original, external.read_bytes())

    def test_invalid_cli_inputs_return_controlled_errors_without_changes(self):
        original = (self.forge / "MISSION.md").read_bytes()
        missing = self.project / "missing"
        cases = (
            [],
            [str(self.project)],
            self.arguments(state="reviewing"),
            [str(self.forge), *self.arguments()[1:]],
            [str(missing), *self.arguments()[1:]],
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = self.run_checkpoint(*arguments)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("forge-checkpoint ERROR:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(original, (self.forge / "MISSION.md").read_bytes())

    def test_invalid_current_mission_is_controlled_and_unchanged(self):
        path = self.forge / "MISSION.md"
        invalid = path.read_text(encoding="utf-8").replace(
            'state: "working"', 'state: "reviewing"'
        )
        path.write_text(invalid, encoding="utf-8")
        original = path.read_bytes()

        result = self.run_checkpoint(*self.arguments())

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-checkpoint ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(original, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
