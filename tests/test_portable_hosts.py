from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "forge"
SKILL_NAMES = {
    "forge-core",
    "forge-memory",
    "forge-init",
    "forge-status",
    "forge-loop",
    "forge-assurance",
    "forge-scout",
    "forge-builder",
    "forge-checker",
}


class PortableHostPackageTests(unittest.TestCase):
    def test_portable_agent_skills_are_exact_canonical_mirrors(self) -> None:
        canonical = PLUGIN / "skills"
        portable = ROOT / ".agents" / "skills"
        self.assertEqual(SKILL_NAMES, {path.name for path in portable.iterdir()})
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                canonical_files = {
                    path.relative_to(canonical / name): path.read_bytes()
                    for path in (canonical / name).rglob("*")
                    if path.is_file()
                }
                portable_files = {
                    path.relative_to(portable / name): path.read_bytes()
                    for path in (portable / name).rglob("*")
                    if path.is_file()
                }
                self.assertEqual(canonical_files, portable_files)

    def test_portable_skill_payload_is_self_contained_and_in_sync(self) -> None:
        runtime = PLUGIN / "skills" / "forge-memory" / "assets" / "portable"
        for relative in (
            "scripts/forge-init",
            "scripts/forge-status",
            "scripts/forge-checkpoint",
            "scripts/forge-compact",
            "scripts/forge-memory-validate",
            "lib/forge_files.py",
            "lib/forge_memory.py",
            "templates/agent-return.md",
            "templates/assurance-result.md",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((runtime / relative).is_file())
        for skill in (
            "forge-init",
            "forge-status",
            "forge-memory",
            "forge-assurance",
            "forge-scout",
            "forge-builder",
            "forge-checker",
        ):
            body = (PLUGIN / "skills" / skill / "SKILL.md").read_text(
                encoding="utf-8"
            )
            self.assertNotIn("plugins/forge/scripts", body)
            self.assertNotIn("plugins/forge/templates", body)
            self.assertIn("forge-memory/assets/portable", body)
        result = subprocess.run(
            [sys.executable, "scripts/sync-portable-skills.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_pi_package_declares_all_portable_skills_without_install_hooks(self) -> None:
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("forge-memory-first", package["name"])
        self.assertEqual((ROOT / "VERSION").read_text().strip(), package["version"])
        self.assertIn("pi-package", package["keywords"])
        self.assertEqual(["./.agents/skills"], package["pi"]["skills"])
        self.assertNotIn("scripts", package)
        self.assertNotIn("dependencies", package)

    def test_dsh_bundle_is_pinned_experimental_and_contains_all_skills(self) -> None:
        root = ROOT / "packages" / "deepseek-harness"
        package = json.loads((root / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("forge-memory-first-dsh", package["name"])
        self.assertEqual((ROOT / "VERSION").read_text().strip(), package["version"])
        self.assertEqual(
            {"patch": "./cordis.patch.yml"},
            package["dsh"]["bundle"],
        )
        self.assertEqual("0.1.2-rc.1", package["engines"]["dsh"])
        self.assertEqual(">=22.19.0", package["engines"]["node"])
        self.assertEqual("0.1.2-rc.1", package["peerDependencies"]["@deepseek-ai/dsh-skill"])
        self.assertEqual(
            SKILL_NAMES,
            {path.name for path in (root / "skills").iterdir()},
        )
        provider = (root / "index.js").read_text(encoding="utf-8")
        self.assertIn("registerProvider", provider)
        self.assertIn("BUNDLED_SKILL_RANK", provider)
        self.assertIn("resourceBase", provider)
        self.assertIn(
            "const SKILLS_ROOT = new URL('./skills/', import.meta.url)",
            provider,
        )
        self.assertIn("resourceBase: SHARED_RESOURCE_BASE", provider)
        for name in SKILL_NAMES:
            self.assertIn(f"'{name}'", provider)
        patch = (root / "cordis.patch.yml").read_text(encoding="utf-8")
        self.assertIn("name: forge-memory-first-dsh", patch)

    def test_new_hosts_are_core_level_without_profile_equivalence(self) -> None:
        capability = json.loads(
            (PLUGIN / "platform-capabilities.json").read_text(encoding="utf-8")
        )
        adapters = {entry["id"]: entry for entry in capability["host_adapters"]}
        self.assertEqual(
            {
                "claude-code",
                "codex",
                "cursor",
                "command-code",
                "pi",
                "deepseek-harness",
            },
            set(adapters),
        )
        for host in ("command-code", "pi", "deepseek-harness"):
            self.assertEqual("active-core", adapters[host]["status"])
        platforms = {entry["id"]: entry for entry in capability["platforms"]}
        for host in ("claude-code", "codex", "cursor"):
            self.assertEqual("profile-equivalent", platforms[host]["support_tier"])
            self.assertTrue(platforms[host]["profile_equivalence"])
        for host in ("command-code", "pi", "deepseek-harness"):
            self.assertEqual("core", platforms[host]["support_tier"])
            self.assertFalse(platforms[host]["profile_equivalence"])
            self.assertEqual([], platforms[host]["profiles"])


if __name__ == "__main__":
    unittest.main()
