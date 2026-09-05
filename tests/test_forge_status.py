from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "plugins/forge/scripts/forge-status"
FIXTURE_ROOT = ROOT / "tests/fixtures/memory_first"

EXPECTED_STATUS = """\
# Forge Memory-First

## Mission
- **ID:** `memory-first-fixture`
- **State:** `working`
- **Outcome:** Implement the memory validator.
- **Checkpoint:** `2026-09-01T12:00:00Z`

## Progress
- **Latest delivery:** Added canonical memory fixtures.
- **Next action:** Implement validation against the fixtures.
- **Blockers:** None.

## Verification
- **Last check:** `python -m unittest tests.test_memory_contract -v`
- **Boundary:** The validator implementation does not exist yet.
"""


class ForgeStatusTests(unittest.TestCase):
    def run_status(
        self, *arguments: str, cwd: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(STATUS), *arguments],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_prints_exact_active_memory_status(self):
        result = self.run_status(str(FIXTURE_ROOT))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(EXPECTED_STATUS, result.stdout)
        self.assertEqual("", result.stderr)

    def test_null_checkpoint_prints_none_recorded(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            forge = project / ".forge"
            forge.mkdir(parents=True)
            fixture = FIXTURE_ROOT / ".forge"
            (forge / "INTENT.md").write_bytes((fixture / "INTENT.md").read_bytes())
            mission = (fixture / "MISSION.md").read_text(encoding="utf-8")
            (forge / "MISSION.md").write_text(
                mission.replace(
                    'checkpointed_at: "2026-09-01T12:00:00Z"',
                    "checkpointed_at: null",
                ),
                encoding="utf-8",
            )

            result = self.run_status(str(project))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("- **Checkpoint:** `None recorded.`\n", result.stdout)

    def test_missing_forge_returns_init_hint(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            project.mkdir()
            result = self.run_status(str(project))

        self.assertEqual(1, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-init PROJECT_ROOT", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_reads_only_direct_active_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            forge = project / ".forge"
            forge.mkdir(parents=True)
            fixture = FIXTURE_ROOT / ".forge"
            for name in ("INTENT.md", "MISSION.md"):
                (forge / name).write_bytes((fixture / name).read_bytes())
            for relative in (
                "forge.db",
                "reviews/bad.md",
                "expectations/bad.md",
                "archive/bad/MISSION.md",
                "findings/bad.md",
            ):
                path = forge / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"\xffinvalid")

            result = self.run_status(str(project))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(EXPECTED_STATUS, result.stdout)

    def test_invalid_inputs_are_controlled_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory) / "project"
            forge = project / ".forge"
            forge.mkdir(parents=True)
            fixture = FIXTURE_ROOT / ".forge"
            (forge / "INTENT.md").write_bytes((fixture / "INTENT.md").read_bytes())
            mission = (fixture / "MISSION.md").read_text(encoding="utf-8")
            (forge / "MISSION.md").write_text(
                mission.replace('state: "working"', 'state: "reviewing"'),
                encoding="utf-8",
            )
            cases = (
                (),
                (str(project), str(project)),
                (str(forge),),
                (str(project),),
            )
            for arguments in cases:
                with self.subTest(arguments=arguments):
                    result = self.run_status(*arguments, cwd=project)
                    self.assertNotEqual(0, result.returncode)
                    self.assertEqual("", result.stdout)
                    self.assertIn("forge-status ERROR:", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
