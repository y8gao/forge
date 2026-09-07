from __future__ import annotations

import json
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "forge"
PROFILES = ("forge-scout", "forge-builder", "forge-checker")


def frontmatter(path: Path) -> tuple[dict[str, object], str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
    if not match:
        raise AssertionError(f"missing frontmatter: {path}")
    values: dict[str, object] = {}
    for line in match.group(1).splitlines():
        key, raw = line.split(":", 1)
        raw = raw.strip()
        if raw.startswith("["):
            values[key] = [
                value.strip()
                for value in raw.removeprefix("[").removesuffix("]").split(",")
            ]
        elif raw in {"true", "false"}:
            values[key] = raw == "true"
        else:
            values[key] = raw.strip('"')
    return values, match.group(2)


class PlatformAgentPackagingTests(unittest.TestCase):
    def test_core_ci_is_cross_platform_least_privilege_and_pinned(self) -> None:
        path = ROOT / ".github/workflows/ci.yml"
        self.assertTrue(path.is_file(), "core CI workflow is missing")
        workflow = path.read_text(encoding="utf-8")
        for phrase in (
            "name: Core CI",
            "pull_request:",
            "push:",
            "workflow_dispatch:",
            "permissions:\n  contents: read",
            "cancel-in-progress: true",
            "timeout-minutes:",
            "os: [ubuntu-latest, windows-latest]",
            'python: ["3.11", "3.14"]',
            "python scripts/validate-content.py",
            "python plugins/forge/scripts/forge-memory-validate .",
            "python -m unittest discover -s tests -p 'test_*.py'",
            "git diff --check",
            "bash -n scripts/release.sh",
            'CLAUDE_CODE_VERSION: "2.1.261"',
            'CODEX_VERSION: "0.153.4"',
            'COMMAND_CODE_VERSION: "1.49.1"',
            'PI_VERSION: "0.85.1"',
            '"@earendil-works/pi-coding-agent@${PI_VERSION}"',
            'DSH_VERSION: "0.1.2-rc.1"',
            'claude plugin marketplace add "$GITHUB_WORKSPACE"',
            "claude plugin install forge@forge --scope user",
            'codex plugin marketplace add "$GITHUB_WORKSPACE" --json',
            "codex plugin add forge@forge --json",
            "HOME: ${{ runner.temp }}/claude-home",
            "CODEX_HOME: ${{ runner.temp }}/codex-home",
            "command-code skills list",
            'pi install "$GITHUB_WORKSPACE"',
            'dsh plugin --profile forge-smoke add "$GITHUB_WORKSPACE/packages/deepseek-harness"',
            "dsh --profile forge-smoke --dump-config",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, workflow)
        self.assertNotIn("@latest", workflow)
        self.assertNotRegex(workflow, r"actions/(?:checkout|setup-python|setup-node)@v\d")

    def test_latest_host_compatibility_is_scheduled_and_public_aware(self) -> None:
        path = ROOT / ".github/workflows/host-compatibility.yml"
        self.assertTrue(path.is_file(), "host compatibility workflow is missing")
        workflow = path.read_text(encoding="utf-8")
        for phrase in (
            "name: Host Compatibility",
            "schedule:",
            "cron:",
            "workflow_dispatch:",
            "permissions:\n  contents: read",
            "cancel-in-progress: true",
            "timeout-minutes:",
            "@anthropic-ai/claude-code@latest",
            "@openai/codex@latest",
            "command-code@latest",
            "@earendil-works/pi-coding-agent@latest",
            "@deepseek-ai/dsh@latest",
            'claude plugin marketplace add "$GITHUB_WORKSPACE"',
            'codex plugin marketplace add "$GITHUB_WORKSPACE" --json',
            "github.repository == 'y8gao/forge'",
            "claude plugin marketplace add y8gao/forge",
            "codex plugin marketplace add y8gao/forge --ref main --json",
            "command-code skills add y8gao/forge@main",
            "pi install git:github.com/y8gao/forge@main",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, workflow)
        self.assertNotIn("ANTHROPIC_API_KEY", workflow)
        self.assertNotIn("OPENAI_API_KEY", workflow)
        self.assertNotRegex(workflow, r"actions/(?:checkout|setup-node)@v\d")

    def test_readme_documents_ci_host_coverage_boundary(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        validation = readme.split("## Validate\n", 1)[1].split(
            "\n## Versioning", 1
        )[0]
        for phrase in (
            "fixed CLI versions",
            "latest",
            "Claude Code",
            "Codex",
            "Cursor",
            "Command Code",
            "Pi",
            "DeepSeek Harness",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, validation)
        self.assertRegex(validation, r"headless\s+installer")

    def test_readme_codex_install_uses_public_git_marketplace(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        codex = readme.split("### Codex\n", 1)[1].split("\n### Cursor", 1)[0]
        self.assertIn(
            "codex plugin marketplace add y8gao/forge --ref main",
            codex,
        )
        self.assertIn("codex plugin add forge@forge", codex)
        self.assertNotIn(".agents/plugins/marketplace.json", codex)
        self.assertNotIn("codex plugin install", codex)

    def test_readme_leads_with_distinctive_value_and_minimum_workflow(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        introduction = readme.split("## First-class hosts\n", 1)[0]
        for phrase in (
            "Keep coding agents aligned across sessions",
            "two small, human-reviewable Markdown files",
            "## Why Forge",
            "Resume from intent, not chat history",
            "Direct by default",
            "Extra control only when asked",
            "Focused capabilities, not a simulated team",
            "Native profile parity on three hosts",
            "Portable Core on three more",
            "No runtime to operate",
            "## How it works",
            "Only the host agent writes active control memory",
            "specific authorization",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, introduction)
        self.assertLessEqual(len(introduction.splitlines()), 40)

    def test_readme_use_is_scenario_first_and_honest_across_hosts(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        use = readme.split("## Use\n", 1)[1].split("\n## Validate", 1)[0]
        for phrase in (
            "Claude Code, Codex, Cursor, Command Code, Pi, or DeepSeek Harness",
            "ordinary work",
            "at most 3 iterations",
            "independent report-only",
            "authorized bounded repair",
            "fresh independent check",
            "pause",
            "resume",
            "specific external action and target",
            "Aliases are optional",
            "does not claim live",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, use)
        self.assertNotIn("Run `forge-init`", use)
        self.assertNotIn("Invoke `forge-loop`", use)
        for internal_term in ("Core", "Assurance", "Checker", "checkpoint", "active mission"):
            self.assertNotIn(internal_term, use)

    def test_readme_documents_new_host_installs_and_profile_boundary(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase in (
            "command-code skills add y8gao/forge",
            "pi install git:github.com/y8gao/forge@main",
            "dsh plugin --profile",
            "0.1.2-rc.1",
            "Core-level support",
            "does not guarantee Scout/Builder/Checker permission isolation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)

    def test_wrapper_inventory_is_exact(self) -> None:
        expected = {f"{name}.md" for name in PROFILES}
        self.assertEqual(expected, {path.name for path in (PLUGIN / "agents").glob("*.md")})
        self.assertEqual(
            {f"{name}.toml" for name in PROFILES},
            {path.name for path in (PLUGIN / "agent-defs/codex").glob("*.toml")},
        )
        self.assertEqual(
            expected,
            {path.name for path in (PLUGIN / "agent-defs/cursor").glob("*.md")},
        )

    def test_claude_wrappers_are_thin_and_reference_shared_contracts(self) -> None:
        for name in PROFILES:
            with self.subTest(profile=name):
                metadata, body = frontmatter(PLUGIN / "agents" / f"{name}.md")
                self.assertEqual(name, metadata["name"])
                self.assertIn("description", metadata)
                self.assertIn("tools", metadata)
                self.assertEqual(
                    [name, "forge-core", "forge-memory"],
                    metadata["skills"],
                )
                if name in {"forge-scout", "forge-checker"}:
                    self.assertNotIn("Write", metadata["tools"])
                    self.assertNotIn("Edit", metadata["tools"])
                if name == "forge-scout":
                    self.assertNotIn("Bash", metadata["tools"])
                elif name == "forge-checker":
                    self.assertIn("Bash", metadata["tools"])
                else:
                    self.assertIn("Write", metadata["tools"])
                    self.assertIn("Edit", metadata["tools"])
                self.assertGreaterEqual(len(body.splitlines()), 5)
                self.assertLessEqual(len(body.splitlines()), 15)
                self.assertIn(f"skills/{name}/SKILL.md", body)
                self.assertIn("templates/agent-return.md", body)
                self.assertLess(len(body), 800)

    def test_codex_permissions_and_shared_skill_refs_are_exact(self) -> None:
        expected_modes = {
            "forge-scout": "read-only",
            "forge-builder": "workspace-write",
            "forge-checker": "read-only",
        }
        for name, mode in expected_modes.items():
            with self.subTest(profile=name):
                data = tomllib.loads(
                    (PLUGIN / "agent-defs/codex" / f"{name}.toml").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(name, data["agent"]["name"])
                self.assertEqual(mode, data["agent"]["sandbox_mode"])
                self.assertEqual(name, data["agent"]["skills"]["profile"])
                self.assertEqual(
                    ["forge-core", "forge-memory"],
                    data["agent"]["skills"]["shared"],
                )
                instructions = data["agent"]["instructions"]["text"]
                self.assertIn(f"skills/{name}/SKILL.md", instructions)
                self.assertIn("templates/agent-return.md", instructions)
                self.assertLess(len(instructions.splitlines()), 10)

    def test_platform_capabilities_claim_exact_tiered_hosts(self) -> None:
        data = json.loads(
            (PLUGIN / "platform-capabilities.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(PROFILES), data["shared_profiles"])
        self.assertEqual(
            [
                {"id": "claude-code", "status": "active-native"},
                {"id": "codex", "status": "active-native"},
                {"id": "cursor", "status": "active-native"},
                {"id": "command-code", "status": "active-core"},
                {"id": "pi", "status": "active-core"},
                {"id": "deepseek-harness", "status": "active-core"},
            ],
            data["host_adapters"],
        )
        self.assertEqual(
            {
                "claude-code",
                "codex",
                "cursor",
                "command-code",
                "pi",
                "deepseek-harness",
            },
            {platform["id"] for platform in data["platforms"]},
        )
        for platform in data["platforms"][:3]:
            self.assertEqual("native", platform["delivery"])
            self.assertEqual(list(PROFILES), platform["profiles"])
            self.assertTrue(platform["profile_equivalence"])
        for platform in data["platforms"][3:]:
            self.assertEqual("core", platform["support_tier"])
            self.assertEqual([], platform["profiles"])
            self.assertFalse(platform["profile_equivalence"])
        serialized = json.dumps(data).lower()
        self.assertNotIn("copilot", serialized)
        self.assertNotIn("vscode", serialized)


if __name__ == "__main__":
    unittest.main()
