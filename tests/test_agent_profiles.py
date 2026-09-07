from __future__ import annotations

import json
import re
import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "forge"
SKILLS = PLUGIN / "skills"
AUTHORITY_GRANTS = runpy.run_path(str(ROOT / "scripts/validate-content.py")).get(
    "_profile_authority_grants"
)

PROFILE_NAMES = {"forge-scout", "forge-builder", "forge-checker"}
CORE_SKILL_NAMES = {"forge-core", "forge-init", "forge-memory", "forge-status"}
LEGACY_ROLE_NAMES = {
    "forge-pm",
    "forge-architect",
    "forge-designer",
    "forge-developer",
    "forge-tester",
    "forge-reviewer",
    "forge-security-reviewer",
    "forge-team",
    "forge-quality",
}
LEGACY_TEMPLATE_NAMES = {
    "design.md",
    "design-ui.md",
    "expectations.md",
    "review-finding.md",
    "review-security.md",
    "test-plan.md",
    "verification.md",
    "verification-report.md",
}


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


class AgentProfileContractTests(unittest.TestCase):
    def test_task_f_capability_profile_subset_is_exact(self) -> None:
        actual = {
            path.parent.name
            for path in SKILLS.glob("*/SKILL.md")
            if "temporary capability profile" in path.read_text(encoding="utf-8")
        }
        self.assertEqual(PROFILE_NAMES, actual)
        self.assertTrue(LEGACY_ROLE_NAMES.isdisjoint(actual))

    def test_nonprofile_core_skill_inventory_remains_present(self) -> None:
        actual = {path.parent.name for path in SKILLS.glob("*/SKILL.md")}
        self.assertTrue(CORE_SKILL_NAMES <= actual)

    def test_task_f_removes_legacy_role_surfaces(self) -> None:
        for name in LEGACY_ROLE_NAMES:
            with self.subTest(skill=name):
                self.assertFalse(
                    any(path.is_file() for path in (SKILLS / name).rglob("*"))
                )
        self.assertFalse((PLUGIN / "docs" / "ROLE_GUIDE.md").exists())
        for name in LEGACY_TEMPLATE_NAMES:
            with self.subTest(template=name):
                self.assertFalse((PLUGIN / "templates" / name).exists())

    def test_profiles_are_thin_and_have_exact_frontmatter_names(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                text = read(f"plugins/forge/skills/{name}/SKILL.md")
                self.assertTrue(text.startswith("---\n"))
                frontmatter = text.split("---", 2)[1]
                self.assertRegex(
                    frontmatter,
                    rf'(?m)^name: "{re.escape(name)}"$',
                )
                self.assertRegex(
                    frontmatter,
                    r'(?m)^description: "(?:[^"\\]|\\.)+"$',
                )
                for line in frontmatter.strip().splitlines():
                    _, raw = line.split(":", 1)
                    value = json.loads(raw.strip())
                    self.assertIsInstance(value, str)
                self.assertLess(len(text.splitlines()), 500)

    def test_profiles_are_optional_temporary_and_host_selected(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                text = read(f"plugins/forge/skills/{name}/SKILL.md")
                for marker in (
                    "temporary",
                    "selected by the host for the task",
                    "not a permanent team",
                    "not a mandatory chain",
                    "Core remains the direct default",
                    "agent-return.md",
                ):
                    self.assertIn(marker, text)

    def test_common_request_envelope_is_minimal_and_authority_explicit(self) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                text = read(f"plugins/forge/skills/{name}/SKILL.md")
                for marker in (
                    "Goal or Claim",
                    "Scope only when it differs from the profile default",
                    "Authority",
                    "write and external-effect authority",
                    "Required Return",
                ):
                    self.assertIn(marker, text)

    def test_selected_profile_cannot_nest_delegate_or_write_active_memory(
        self,
    ) -> None:
        for name in PROFILE_NAMES:
            with self.subTest(profile=name):
                text = read(f"plugins/forge/skills/{name}/SKILL.md")
                self.assertIn("Never invoke or delegate to another profile", text)
                self.assertIn("Do not write active memory", text)
                for forbidden in (
                    "unless the host asks",
                    "may invoke another profile",
                    "may write active memory",
                ):
                    self.assertNotIn(forbidden, text)

    def test_affirmative_authority_grants_are_rejected_without_flagging_denials(
        self,
    ) -> None:
        self.assertIsNotNone(AUTHORITY_GRANTS)
        attacks = {
            "forge-checker": (
                "Repair edits are permitted after a failed check.",
                "Checker CAN repair code.",
                "Checker may edit files.",
                "Checker is permitted to write files.",
                "Checker is ALLOWED to modify tests.",
                "Checker is authorized to repair edits.",
                "Checker has permission to repair code.",
                "Checker shall repair edits after a failed check.",
                "Checker may write active memory.",
            ),
            "forge-builder": (
                "A Builder can delegate another profile when blocked.",
                "A Builder may invoke a profile.",
                "A Builder is authorized to delegate another profile.",
                "A Builder has permission to invoke a profile.",
                "A Builder shall delegate another profile when blocked.",
                "A Builder may self-approve and self-integrate.",
            ),
            "forge-scout": (
                "Scout can modify tests when useful.",
                "Scout may edit product.",
                "Scout is permitted to write configuration.",
                "Scout is authorized to modify tests.",
                "Scout has permission to edit tests.",
                "Scout shall modify tests when useful.",
                "Scout is allowed to write active memory.",
            ),
        }
        for profile, profile_attacks in attacks.items():
            for attack in profile_attacks:
                with self.subTest(profile=profile, attack=attack):
                    self.assertTrue(AUTHORITY_GRANTS(profile, attack))

        denials = (
            "Do not make repair edits.",
            "Never invoke or delegate to another profile.",
            "A Builder cannot self-approve or self-integrate.",
            "Scout may not modify tests or write active memory.",
            "Checker is not authorized to repair edits.",
            "Builder does not have permission to delegate another profile.",
            "Scout shall not modify tests.",
        )
        for denial in denials:
            with self.subTest(denial=denial):
                for profile in PROFILE_NAMES:
                    self.assertEqual([], AUTHORITY_GRANTS(profile, denial))

    def test_scout_is_read_only_discovery(self) -> None:
        text = read("plugins/forge/skills/forge-scout/SKILL.md")
        for marker in (
            "read-only discovery and research",
            "focused question",
            "declared read scope",
            "Do not edit product, tests, or configuration",
            "Do not write active memory",
            "findings",
            "provenance",
            "observed facts from inferences",
            "unknowns",
            "smallest useful next action",
        ):
            self.assertIn(marker, text)

    def test_builder_is_limited_to_declared_write_scope(self) -> None:
        text = read("plugins/forge/skills/forge-builder/SKILL.md")
        for marker in (
            "only within the declared write scope",
            "confirmed behavior",
            "acceptance criteria",
            "write and external-effect boundary",
            "targeted tests",
            "Never write `.forge/INTENT.md` or `.forge/MISSION.md`",
            "Never self-approve",
            "changed files",
            "checks",
            "unresolved",
        ):
            self.assertIn(marker, text)

    def test_builder_understands_flow_then_uses_minimum_safe_solution_ladder(
        self,
    ) -> None:
        text = read("plugins/forge/skills/forge-builder/SKILL.md")
        markers = (
            "affected control and data flow",
            "relevant callers",
            "required by the acceptance criteria",
            "existing repository capability",
            "standard library or native platform",
            "already-installed dependency",
            "minimum safe custom implementation",
        )
        positions = []
        for marker in markers:
            self.assertIn(marker, text)
            positions.append(text.index(marker))
        self.assertEqual(sorted(positions), positions)

    def test_builder_fixes_root_cause_and_preserves_falsifying_evidence(
        self,
    ) -> None:
        text = read("plugins/forge/skills/forge-builder/SKILL.md")
        for marker in (
            "root cause",
            "shared location",
            "durable regression",
            "reproducible falsifying command",
            "why a regression is impractical",
            "remaining verification gap",
        ):
            self.assertIn(marker, text)

    def test_builder_stops_outside_scope_and_cannot_self_integrate(self) -> None:
        text = read("plugins/forge/skills/forge-builder/SKILL.md")
        for marker in (
            "Stop before editing outside",
            "Never self-approve",
            "cannot broaden that authority",
            "commit, merge, push, publish, or deploy",
            "API writes",
            "explicit action and target authorization",
            "change location",
            "in-place workspace, worktree, or patch",
            "integration",
        ):
            self.assertIn(marker, text)
        self.assertNotIn("may self-approve", text)
        self.assertNotIn("profile selection authorizes", text)

    def test_checker_attacks_claims_without_repairs(self) -> None:
        text = read("plugins/forge/skills/forge-checker/SKILL.md")
        for marker in (
            "explicit Assurance or independent-check request",
            "checks and attacks only",
            "read-only on the product under check",
            "read-only command execution",
            "Never run commands that mutate",
            "Do not make repair edits",
            "Do not write active memory",
            "claim-scoped pass or fail",
            "reproducible evidence",
            "The host decides follow-up actions",
        ):
            self.assertIn(marker, text)

    def test_checker_is_fresh_claim_scoped_and_never_repairs(self) -> None:
        text = read("plugins/forge/skills/forge-checker/SKILL.md")
        for marker in (
            "fresh agent session",
            "does not inherit Builder history or reasoning",
            "frozen claims",
            "necessary diff, files, and read actions",
            "falsify each claim",
            "PASS, FAIL, or INCOMPLETE",
            "exact gaps",
            "Different model or worktree is optional",
        ):
            self.assertIn(marker, text)
        self.assertNotIn("repair the product", text)
        self.assertNotIn("may make repair edits", text)

    def test_common_return_contract_is_complete(self) -> None:
        text = read("plugins/forge/templates/agent-return.md")
        self.assertTrue(text.startswith("---\n"))
        for heading in (
            "## Summary",
            "## Evidence and exact command outcomes",
            "## Files or areas inspected or changed",
            "## Unknowns and risks",
            "## Recommended next action",
        ):
            self.assertIn(heading, text)

    def test_common_return_frontmatter_schema_is_exact(self) -> None:
        text = read("plugins/forge/templates/agent-return.md")
        match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
        self.assertIsNotNone(match)
        lines = match.group(1).splitlines() if match else []
        pairs = [line.split(":", 1) for line in lines]
        keys = [key.strip() for key, _ in pairs]
        values = {
            key.strip(): value.strip().strip('"').strip("'")
            for key, value in pairs
        }

        self.assertEqual(5, len(keys))
        self.assertEqual(
            {
                "format",
                "profile",
                "task",
                "authority_boundary",
                "change_location",
            },
            set(keys),
        )
        self.assertEqual("forge-agent-return-v1", values["format"])
        self.assertEqual("", values["profile"])
        self.assertEqual("", values["task"])
        self.assertEqual("", values["authority_boundary"])
        self.assertEqual("", values["change_location"])

    def test_common_return_stays_compact_without_copying_workflow(self) -> None:
        text = read("plugins/forge/templates/agent-return.md")
        self.assertEqual(5, len(re.findall(r"(?m)^## ", text)))
        self.assertIn("Authority boundary:", text)
        self.assertIn("Change location:", text)
        self.assertNotIn("Goal or Claim", text)
        self.assertLess(len(text.splitlines()), 40)

    def test_native_capability_metadata_is_profile_only(self) -> None:
        capability = json.loads(
            read("plugins/forge/platform-capabilities.json")
        )

        self.assertEqual(
            {
                "schema_version",
                "shared_profiles",
                "host_adapters",
                "platforms",
            },
            set(capability),
        )
        self.assertEqual(1, capability["schema_version"])
        self.assertEqual(PROFILE_NAMES, set(capability["shared_profiles"]))
        self.assertEqual(
            [
                {"id": "claude-code", "status": "active-native"},
                {"id": "codex", "status": "active-native"},
                {"id": "cursor", "status": "active-native"},
                {"id": "command-code", "status": "active-core"},
                {"id": "pi", "status": "active-core"},
                {"id": "deepseek-harness", "status": "active-core"},
            ],
            capability["host_adapters"],
        )
        serialized = json.dumps(capability)
        for legacy in LEGACY_ROLE_NAMES:
            self.assertNotIn(legacy, serialized)

    def test_native_platform_profiles_are_exact(self) -> None:
        capability = json.loads(
            read("plugins/forge/platform-capabilities.json")
        )
        platforms = {
            entry["id"]: entry for entry in capability["platforms"]
        }
        self.assertEqual(
            {
                "claude-code",
                "codex",
                "cursor",
                "command-code",
                "pi",
                "deepseek-harness",
            },
            set(platforms),
        )
        for host in ("claude-code", "codex", "cursor"):
            entry = platforms[host]
            self.assertEqual(sorted(PROFILE_NAMES), sorted(entry["profiles"]))
            self.assertEqual("native", entry["delivery"])
            self.assertTrue(entry["profile_equivalence"])
            self.assertNotIn("roles", entry)
        for host in ("command-code", "pi", "deepseek-harness"):
            entry = platforms[host]
            self.assertEqual([], entry["profiles"])
            self.assertFalse(entry["profile_equivalence"])
            self.assertNotIn("roles", entry)


if __name__ == "__main__":
    unittest.main()
