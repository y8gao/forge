from __future__ import annotations

from pathlib import Path
import errno
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "plugins/forge/scripts/forge-init"
LIB = ROOT / "plugins/forge/lib"
SKILLS = ROOT / "plugins/forge/skills"
sys.path.insert(0, str(LIB))

from forge_memory import render_initial_intent, render_initial_mission  # noqa: E402


EXPECTED_FORGE_ENTRIES = {"INTENT.md", "MISSION.md", "archive"}
BEGIN_MARKER = "<!-- BEGIN FORGE MEMORY-FIRST -->"
END_MARKER = "<!-- END FORGE MEMORY-FIRST -->"


class ForgeInitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.project = Path(self.temporary_directory.name) / "project"
        self.project.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_init(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(INIT), *arguments],
            cwd=self.project,
            text=True,
            capture_output=True,
            check=False,
        )

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

    def test_initializes_exact_memory_first_layout_and_bridges(self):
        result = self.run_init(str(self.project))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(f"forge-init initialized {self.project}\n", result.stdout)
        self.assertEqual("", result.stderr)
        forge = self.project / ".forge"
        self.assertEqual(EXPECTED_FORGE_ENTRIES, {path.name for path in forge.iterdir()})
        self.assertEqual(
            render_initial_intent(),
            (forge / "INTENT.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(
            render_initial_mission(),
            (forge / "MISSION.md").read_text(encoding="utf-8"),
        )
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.project / name).read_text(encoding="utf-8")
            self.assertEqual(1, text.count(BEGIN_MARKER))
            self.assertEqual(1, text.count(END_MARKER))
            self.assertIn("Forge Memory-First", text)
            self.assertIn(".forge/INTENT.md", text)
            self.assertIn(".forge/MISSION.md", text)
            self.assertIn("outcome", text.lower())
            self.assertIn("next action", text.lower())
            self.assertIn("checkpoint transitions", text.lower())
            for legacy in ("thin protocol", "preflight", "reviewer", "gate"):
                self.assertNotIn(legacy, text.lower())

        forbidden = (
            "decisions",
            "expectations",
            "reviews",
            "designs",
            "verification",
            "forge.db",
            "review.md",
        )
        for name in forbidden:
            self.assertFalse((forge / name).exists(), name)
        self.assertFalse((self.project / ".cursorrules").exists())
        for name in (
            ".windsurfrules",
            "CONVENTIONS.md",
            "GEMINI.md",
            ".clinerules",
            ".github/copilot-instructions.md",
        ):
            self.assertFalse((self.project / name).exists(), name)

    def test_rerun_preserves_memory_bytes_and_does_not_duplicate_bridges(self):
        first = self.run_init(str(self.project))
        self.assertEqual(0, first.returncode, first.stderr)
        intent = self.project / ".forge/INTENT.md"
        mission = self.project / ".forge/MISSION.md"
        before = (intent.read_bytes(), mission.read_bytes())

        second = self.run_init(str(self.project))

        self.assertEqual(0, second.returncode, second.stderr)
        self.assertEqual(before, (intent.read_bytes(), mission.read_bytes()))
        for name in ("AGENTS.md", "CLAUDE.md"):
            text = (self.project / name).read_text(encoding="utf-8")
            self.assertEqual(1, text.count(BEGIN_MARKER))
            self.assertEqual(1, text.count(END_MARKER))

    def test_preserves_existing_bridges_and_single_active_memory_file(self):
        (self.project / "AGENTS.md").write_text("agents sentinel", encoding="utf-8")
        (self.project / "CLAUDE.md").write_text("claude sentinel\n", encoding="utf-8")
        forge = self.project / ".forge"
        forge.mkdir()
        existing = render_initial_intent().encode("utf-8")
        (forge / "INTENT.md").write_bytes(existing)

        result = self.run_init(str(self.project))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(existing, (forge / "INTENT.md").read_bytes())
        self.assertEqual(
            render_initial_mission(),
            (forge / "MISSION.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(EXPECTED_FORGE_ENTRIES, {path.name for path in forge.iterdir()})
        self.assertTrue(
            (self.project / "AGENTS.md").read_text(encoding="utf-8").startswith(
                "agents sentinel"
            )
        )
        self.assertTrue(
            (self.project / "CLAUDE.md").read_text(encoding="utf-8").startswith(
                "claude sentinel"
            )
        )

    def test_invalid_existing_active_memory_fails_before_any_write(self):
        for invalid_name, missing_name in (
            ("INTENT.md", "MISSION.md"),
            ("MISSION.md", "INTENT.md"),
        ):
            with self.subTest(invalid_name=invalid_name):
                project = self.project.parent / f"invalid-{invalid_name.lower()}"
                project.mkdir()
                forge = project / ".forge"
                forge.mkdir()
                invalid = b"not valid Forge memory\r\n"
                (forge / invalid_name).write_bytes(invalid)
                bridges = {
                    project / "AGENTS.md": b"agents sentinel\r\n",
                    project / "CLAUDE.md": b"claude sentinel\n",
                }
                for path, content in bridges.items():
                    path.write_bytes(content)

                result = subprocess.run(
                    [sys.executable, str(INIT), str(project)],
                    cwd=project,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("forge-init ERROR:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(invalid, (forge / invalid_name).read_bytes())
                self.assertFalse((forge / missing_name).exists())
                self.assertFalse((forge / "archive").exists())
                for path, content in bridges.items():
                    self.assertEqual(content, path.read_bytes())

    def test_appending_bridge_preserves_existing_file_bytes(self):
        existing = b"first\r\nsecond\r\n"
        agents = self.project / "AGENTS.md"
        agents.write_bytes(existing)

        result = self.run_init(str(self.project))

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(agents.read_bytes().startswith(existing))

    def test_rejects_forge_directory_symlink_without_external_mutation(self):
        external = self.project.parent / "external-forge"
        external.mkdir()
        self.create_symlink(
            self.project / ".forge", external, target_is_directory=True
        )

        result = self.run_init(str(self.project))

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-init ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual([], list(external.iterdir()))

    def test_rejects_forge_junction_without_external_mutation(self):
        external = self.project.parent / "external-junction"
        external.mkdir()
        self.create_junction(self.project / ".forge", external)

        result = self.run_init(str(self.project))

        self.assertNotEqual(0, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertIn("forge-init ERROR:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual([], list(external.iterdir()))

    def test_rejects_symlinked_managed_descendants_without_external_mutation(
        self,
    ):
        cases = (
            (".forge/INTENT.md", False),
            (".forge/MISSION.md", False),
            (".forge/archive", True),
            (".forge/decisions", True),
            ("AGENTS.md", False),
            ("CLAUDE.md", False),
        )
        for index, (relative, is_directory) in enumerate(cases):
            with self.subTest(relative=relative):
                project = self.project.parent / f"project-{index}"
                project.mkdir()
                forge = project / ".forge"
                forge.mkdir()
                external = self.project.parent / f"external-{index}"
                if is_directory:
                    external.mkdir()
                    expected = []
                else:
                    external.write_bytes(b"external sentinel\r\n")
                    expected = external.read_bytes()
                link = project / relative
                link.parent.mkdir(parents=True, exist_ok=True)
                self.create_symlink(
                    link, external, target_is_directory=is_directory
                )

                result = subprocess.run(
                    [sys.executable, str(INIT), str(project)],
                    cwd=project,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("forge-init ERROR:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                if is_directory:
                    self.assertEqual(expected, list(external.iterdir()))
                else:
                    self.assertEqual(expected, external.read_bytes())

    def test_rejects_malformed_bridge_markers_without_changing_file(self):
        cases = (
            f"prefix\n{BEGIN_MARKER}\n",
            f"prefix\n{END_MARKER}\n",
            f"{BEGIN_MARKER}\n{BEGIN_MARKER}\n{END_MARKER}\n",
            f"{BEGIN_MARKER}\n{END_MARKER}\n{END_MARKER}\n",
            f"{END_MARKER}\nprefix\n{BEGIN_MARKER}\n",
        )
        for index, text in enumerate(cases):
            with self.subTest(index=index):
                project = self.project.parent / f"markers-{index}"
                project.mkdir()
                agents = project / "AGENTS.md"
                original = text.encode("utf-8")
                agents.write_bytes(original)

                result = subprocess.run(
                    [sys.executable, str(INIT), str(project)],
                    cwd=project,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("forge-init ERROR:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(original, agents.read_bytes())

    def test_rejects_invalid_project_root_arguments_without_traceback(self):
        missing = self.project / "missing"
        regular_file = self.project / "file"
        regular_file.write_text("not a directory", encoding="utf-8")
        direct_forge = self.project / ".forge"
        direct_forge.mkdir()
        cases = (
            (),
            (str(self.project), str(self.project)),
            (str(missing),),
            (str(regular_file),),
            (str(direct_forge),),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = self.run_init(*arguments)
                self.assertNotEqual(0, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertIn("forge-init ERROR:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_installed_skills_are_thin_and_wire_bundled_scripts(self):
        for name, script in (
            ("forge-init", "forge-init"),
            ("forge-status", "forge-status"),
        ):
            with self.subTest(name=name):
                path = SKILLS / name / "SKILL.md"
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                self.assertLess(len(text.splitlines()), 500)
                self.assertIn("PROJECT_ROOT", text)
                self.assertIn(f"scripts/{script}", text)
                self.assertIn("sys.executable", text)
                for copied_protocol in ("Orient ->", "Preflight", "role pipeline"):
                    self.assertNotIn(copied_protocol, text)


if __name__ == "__main__":
    unittest.main()
