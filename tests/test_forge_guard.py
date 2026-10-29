from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/forge/scripts/forge-guard"
HOOKS = ROOT / "plugins/forge/hooks/hooks.json"
MANIFEST = ROOT / "plugins/forge/.claude-plugin/plugin.json"


def render_mission(mission_id: str = "current-mission", *, state: str = "ready") -> str:
    checkpointed_at = "null" if state == "ready" else '"2026-09-02T01:02:03Z"'
    return (
        "---\n"
        'format: "forge-memory-v1"\n'
        f'mission_id: "{mission_id}"\n'
        f'state: "{state}"\n'
        f"checkpointed_at: {checkpointed_at}\n"
        "---\n"
        "# Current Mission\n\n"
        "## Outcome\n"
        "- Statement: Keep the current increment visible.\n\n"
        "## Scope\n"
        "- In: Current increment.\n"
        "- Out: Unconfirmed work.\n"
        "- Constraints: Keep it small.\n\n"
        "## Success Criteria\n"
        "- [x] The increment is complete.\n\n"
        "## Latest Delivery\n"
        "- Current increment.\n\n"
        "## Next Action\n"
        "- Continue.\n\n"
        "## Blockers\n"
        "- None.\n\n"
        "## Last Check\n"
        "- Ran: focused checks\n"
        "- Boundary: fixture only\n\n"
        "## Resume\n"
        "- Read: `.forge/INTENT.md`.\n"
        "- Do: continue.\n"
    )


class ForgeGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project = self.root / "project"
        self.forge = self.project / ".forge"
        self.forge.mkdir(parents=True)
        (self.project / "src").mkdir()
        self.write_mission()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_mission(
        self, mission_id: str = "current-mission", *, state: str = "ready"
    ) -> None:
        (self.forge / "MISSION.md").write_text(
            render_mission(mission_id, state=state), encoding="utf-8"
        )

    def run_guard(
        self,
        *,
        file_path: str | None = None,
        notebook_path: str | None = None,
        cwd: Path | None = None,
        tool: str = "Edit",
    ) -> subprocess.CompletedProcess[str]:
        tool_input: dict[str, str] = {}
        if file_path is not None:
            tool_input["file_path"] = file_path
        if notebook_path is not None:
            tool_input["notebook_path"] = notebook_path
        payload = {
            "cwd": str(cwd or self.project),
            "tool_name": tool,
            "tool_input": tool_input,
        }
        return subprocess.run(
            [sys.executable, str(SCRIPT)],
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )

    def assert_allowed(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)

    def assert_blocked(
        self, result: subprocess.CompletedProcess[str], *markers: str
    ) -> None:
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        for marker in markers:
            self.assertIn(marker, result.stderr)

    def test_ready_and_working_allow_edits(self) -> None:
        for state in ("ready", "working"):
            with self.subTest(state=state):
                self.write_mission(state=state)
                self.assert_allowed(
                    self.run_guard(file_path=str(self.project / "src/app.py"))
                )

    def test_done_blocks_with_the_mission_replacement_step(self) -> None:
        self.write_mission("shipped-mission", state="done")

        result = self.run_guard(file_path=str(self.project / "src/app.py"))

        self.assert_blocked(
            result,
            'state is "done"',
            "shipped-mission",
            "Ask the user",
            "forge-compact --replace-from",
        )

    def test_paused_and_blocked_each_name_their_required_action(self) -> None:
        cases = {
            "paused": ("`paused` needs the user to resume",),
            "blocked": ("`blocked` needs the blocker resolved",),
        }
        for state, markers in cases.items():
            with self.subTest(state=state):
                self.write_mission(state=state)
                self.assert_blocked(
                    self.run_guard(file_path=str(self.project / "src/app.py")),
                    f'state is "{state}"',
                    *markers,
                )

    def test_initial_mission_blocks_even_though_it_is_ready(self) -> None:
        self.write_mission("initial", state="ready")

        self.assert_blocked(
            self.run_guard(file_path=str(self.project / "src/app.py")),
            'mission_id: "initial"',
            "forge-compact --replace-from",
        )

    def test_forge_memory_edits_are_exempt(self) -> None:
        self.write_mission(state="done")

        self.assert_allowed(
            self.run_guard(file_path=str(self.forge / "MISSION.md"))
        )

    def test_project_without_forge_memory_is_allowed(self) -> None:
        plain = self.root / "plain"
        plain.mkdir()

        self.assert_allowed(self.run_guard(file_path=str(plain / "app.py")))

    def test_malformed_mission_fails_open(self) -> None:
        (self.forge / "MISSION.md").write_text("not a mission\n", encoding="utf-8")

        self.assert_allowed(
            self.run_guard(file_path=str(self.project / "src/app.py"))
        )

    def test_edit_outside_the_project_is_allowed(self) -> None:
        self.write_mission(state="done")
        other = self.root / "other"
        other.mkdir()

        self.assert_allowed(self.run_guard(file_path=str(other / "app.py")))

    def test_nested_file_finds_the_project_root(self) -> None:
        self.write_mission(state="done")

        self.assert_blocked(
            self.run_guard(file_path=str(self.project / "src/deep/app.py")),
            "forge-guard: blocked",
        )

    def test_notebook_edit_uses_notebook_path(self) -> None:
        self.write_mission(state="done")

        self.assert_blocked(
            self.run_guard(
                notebook_path=str(self.project / "src/analysis.ipynb"),
                tool="NotebookEdit",
            ),
            "blocked NotebookEdit",
        )

    def test_relative_path_resolves_against_the_payload_cwd(self) -> None:
        self.write_mission(state="done")

        self.assert_blocked(
            self.run_guard(file_path="src/app.py", cwd=self.project),
            "forge-guard: blocked",
        )

    def test_hook_manifest_wires_the_guard(self) -> None:
        manifest = json.loads(HOOKS.read_text(encoding="utf-8"))
        entry = manifest["hooks"]["PreToolUse"][0]
        self.assertEqual("Edit|Write|MultiEdit|NotebookEdit", entry["matcher"])
        self.assertIn(
            "${CLAUDE_PLUGIN_ROOT}/scripts/forge-guard",
            entry["hooks"][0]["command"],
        )

    def test_plugin_manifest_declares_the_hook_file(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual("./hooks/hooks.json", manifest["hooks"])


if __name__ == "__main__":
    unittest.main()
