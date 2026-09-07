from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/forge/scripts/forge-intent"
FIXTURE = ROOT / "tests/fixtures/memory_first/.forge"
sys.path.insert(0, str(ROOT / "plugins/forge/lib"))


class ForgeIntentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary_directory.name) / "project"
        self.forge = self.project / ".forge"
        self.forge.mkdir(parents=True)
        for name in ("INTENT.md", "MISSION.md"):
            (self.forge / name).write_bytes((FIXTURE / name).read_bytes())
        self.replacement = self.project / "INTENT.next.md"
        self.replacement.write_text(
            (FIXTURE / "INTENT.md").read_text(encoding="utf-8").replace(
                "- Current: Ship a small memory-first plugin.",
                "- Current: Keep project control memory durable across sessions.",
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def arguments(self) -> list[str]:
        return [
            str(self.project),
            "--replace-from",
            str(self.replacement),
        ]

    def run_cli(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *self.arguments()],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_in_process(
        self, atomic_write
    ) -> tuple[subprocess.CompletedProcess[str], list[Path]]:
        self.assertTrue(SCRIPT.is_file(), "missing forge-intent helper")
        namespace = runpy.run_path(str(SCRIPT), run_name="forge_intent_test")
        writes: list[Path] = []

        def recording_write(root, path, data, *, mode=None):
            writes.append(Path(path))
            return atomic_write(root, path, data, mode=mode)

        stdout = StringIO()
        stderr = StringIO()
        with mock.patch.dict(
            namespace["main"].__globals__,
            {"atomic_write": recording_write},
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            returncode = namespace["main"](self.arguments())
        return (
            subprocess.CompletedProcess(
                self.arguments(),
                returncode,
                stdout.getvalue(),
                stderr.getvalue(),
            ),
            writes,
        )

    def test_valid_replacement_publishes_exact_prevalidated_bytes(self) -> None:
        original_mission = (self.forge / "MISSION.md").read_bytes()
        replacement = self.replacement.read_bytes()

        result = self.run_cli()

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            f"forge-intent updated {self.forge / 'INTENT.md'}\n",
            result.stdout,
        )
        self.assertEqual("", result.stderr)
        self.assertEqual(replacement, (self.forge / "INTENT.md").read_bytes())
        self.assertEqual(original_mission, (self.forge / "MISSION.md").read_bytes())
        self.assertEqual(
            [],
            [path for path in self.forge.iterdir() if path.name.startswith(".INTENT.")],
        )

    def test_invalid_replacement_fails_before_any_active_write(self) -> None:
        from forge_files import atomic_write as real_atomic_write

        original = (self.forge / "INTENT.md").read_bytes()
        self.replacement.write_text("invalid intent\n", encoding="utf-8")

        result, writes = self.run_in_process(real_atomic_write)

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-intent ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual([], writes)
        self.assertEqual(original, (self.forge / "INTENT.md").read_bytes())

    def test_atomic_write_failure_is_controlled_and_preserves_active_bytes(self) -> None:
        original = (self.forge / "INTENT.md").read_bytes()

        def failing_write(root, path, data, *, mode=None):
            raise OSError("replace failed")

        result, writes = self.run_in_process(failing_write)

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-intent ERROR: replace failed", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual([self.forge / "INTENT.md"], writes)
        self.assertEqual(original, (self.forge / "INTENT.md").read_bytes())

    def test_replacement_uses_shared_atomic_write_once(self) -> None:
        from forge_files import atomic_write as real_atomic_write

        result, writes = self.run_in_process(real_atomic_write)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([self.forge / "INTENT.md"], writes)


if __name__ == "__main__":
    unittest.main()
