from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "forge"
PROFILES = ("forge-scout", "forge-builder", "forge-checker")


class CursorPackageTests(unittest.TestCase):
    def test_manifest_has_explicit_component_paths_and_synced_version(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".cursor-plugin/plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual("forge", manifest["name"])
        self.assertEqual((ROOT / "VERSION").read_text().strip(), manifest["version"])
        self.assertEqual("./agent-defs/cursor", manifest["agents"])
        self.assertEqual("./skills", manifest["skills"])
        self.assertNotIn("commands", manifest)
        self.assertEqual("./rules", manifest["rules"])

    def test_marketplace_entry_is_minimal_and_points_to_plugin(self) -> None:
        marketplace = json.loads(
            (ROOT / ".cursor-plugin/marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual({"name", "owner", "metadata", "plugins"}, set(marketplace))
        self.assertIn("description", marketplace["metadata"])
        self.assertEqual(
            [{"name": "forge", "source": "./plugins/forge", "description": marketplace["plugins"][0]["description"]}],
            marketplace["plugins"],
        )

    def test_cursor_agents_use_native_readonly_boundary(self) -> None:
        for name in PROFILES:
            with self.subTest(profile=name):
                text = (PLUGIN / "agent-defs/cursor" / f"{name}.md").read_text(
                    encoding="utf-8"
                )
                match = re.match(r"\A---\n(.*?)\n---\n(.*)\Z", text, re.DOTALL)
                self.assertIsNotNone(match)
                header = match.group(1) if match else ""
                body = match.group(2) if match else ""
                self.assertIn(f"name: {name}", header)
                self.assertIn("model: inherit", header)
                expected = "false" if name == "forge-builder" else "true"
                self.assertIn(f"readonly: {expected}", header)
                self.assertIn(f"skills/{name}/SKILL.md", body)
                self.assertIn("templates/agent-return.md", body)
                self.assertLessEqual(len(body.splitlines()), 15)

    def test_skills_are_only_slash_entrypoints_and_orientation_rule_is_thin(self) -> None:
        command_dir = PLUGIN / "commands"
        self.assertFalse(command_dir.exists())
        for name in ("forge-init", "forge-status", "forge-loop", "forge-assurance"):
            with self.subTest(skill=name):
                self.assertTrue((PLUGIN / "skills" / name / "SKILL.md").is_file())
        rule = (PLUGIN / "rules/forge-orientation.mdc").read_text(encoding="utf-8")
        self.assertIn(".forge/INTENT.md", rule)
        self.assertIn(".forge/MISSION.md", rule)
        self.assertIn("skills/forge-core/SKILL.md", rule)
        self.assertLessEqual(len(rule.splitlines()), 20)


if __name__ == "__main__":
    unittest.main()
