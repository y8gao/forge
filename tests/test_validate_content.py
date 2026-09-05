from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins/forge/lib"))

from forge_memory import load_intent  # noqa: E402


class ValidateContentMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name) / "repo"
        shutil.copytree(
            ROOT,
            self.repo,
            ignore=shutil.ignore_patterns(".git", "forge.db", "__pycache__", "*.pyc"),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_validator(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/validate-content.py"],
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
        )

    def mutate_text(self, relative_path: str, old: str, new: str) -> None:
        path = self.repo / relative_path
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def assert_mutation_fails(self) -> None:
        result = self.run_validator()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_profile_authority_attack_fails(
        self,
        profile: str,
        attack: str,
    ) -> None:
        relative = f"plugins/forge/skills/{profile}/SKILL.md"
        path = self.repo / relative
        path.write_text(
            path.read_text(encoding="utf-8") + f"\n{attack}\n",
            encoding="utf-8",
        )

        result = self.run_validator()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("contradictory authority grant", result.stdout)
        self.assertIn(profile, result.stdout)
        self.assertIn(relative, result.stdout)

    def test_baseline_passes(self) -> None:
        result = self.run_validator()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_malformed_marketplace_json_fails_cleanly(self) -> None:
        (self.repo / ".cursor-plugin/marketplace.json").write_text(
            "{malformed", encoding="utf-8"
        )

        result = self.run_validator()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("invalid marketplace JSON", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_marketplace_source_must_resolve_to_packaged_plugin(self) -> None:
        path = self.repo / ".claude-plugin/marketplace.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["plugins"][0]["source"] = "./missing-plugin"
        path.write_text(json.dumps(data), encoding="utf-8")

        result = self.run_validator()

        self.assertNotEqual(0, result.returncode)
        self.assertIn("marketplace source does not exist", result.stdout)

    def test_product_scope_growth_fails_with_path_and_reason(self) -> None:
        added = self.repo / "plugins/forge/lib/event_ledger.py"
        added.write_text("class EventLedger:\n    pass\n", encoding="utf-8")

        result = self.run_validator()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("plugins/forge/lib/event_ledger.py", result.stdout)
        self.assertIn("ledger", result.stdout)

    def test_file_helper_recovery_theater_fails_with_path_and_reason(self) -> None:
        helper = self.repo / "plugins/forge/lib/forge_files.py"
        helper.write_text(
            helper.read_text(encoding="utf-8")
            + '\nTRANSACTION_JOURNAL = ".write-transaction.json"\n',
            encoding="utf-8",
        )

        result = self.run_validator()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("plugins/forge/lib/forge_files.py", result.stdout)
        self.assertIn("transaction journal", result.stdout)

    def test_task_e_contract_is_present_in_source(self) -> None:
        core = (ROOT / "plugins/forge/skills/forge-core/SKILL.md").read_text(
            encoding="utf-8"
        )
        memory = (ROOT / "plugins/forge/skills/forge-memory/SKILL.md").read_text(
            encoding="utf-8"
        )
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        cursor = (ROOT / ".cursorrules").read_text(encoding="utf-8")

        for marker in (
            "Read only `.forge/INTENT.md` and `.forge/MISSION.md`",
            "act directly or select one useful profile",
            "There is no automatic delegation",
            "Do not enter Loop automatically",
            "Assurance is also explicit",
            "Only the host writes active control memory",
        ):
            self.assertIn(marker, core)
        for marker in (
            "Only the host agent writes active control memory",
            "Archive is not loaded by default",
            "External recall is deferred",
        ):
            self.assertIn(marker, memory)
        for text in (agents, cursor):
            self.assertIn("ordinary tasks directly", text)
            self.assertIn("five checkpoint transitions", text)
            self.assertNotIn("fixed independent", text)
        self.assertFalse(
            (ROOT / "plugins/forge/workflow-obligations.json").exists()
        )

    def test_repository_active_intent_is_current_memory_first_authority(self) -> None:
        path = ROOT / ".forge/INTENT.md"
        text = path.read_text(encoding="utf-8")
        intent = load_intent(path)

        self.assertEqual(
            intent.direction,
            "Keep coding agents oriented across sessions with small active "
            "Memory-First control memory, then help them continue useful work.",
        )
        self.assertLessEqual(len(text.splitlines()), 100)
        self.assertLessEqual(len(intent.decisions), 5)
        self.assertIn(
            "The public Forge repository starts from a clean current-product "
            "snapshot; private development history remains separate.",
            text,
        )
        for obsolete_authority in (
            "SQLite index",
            "event ledger",
            "fixed seven-role",
            "forge-workflow-policy",
        ):
            self.assertNotIn(obsolete_authority, text)

    def test_core_ordinary_direct_execution_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-core/SKILL.md",
            "act directly or select one useful profile",
            "The host dispatches ordinary tasks through a role pipeline",
        )
        self.assert_mutation_fails()

    def test_core_automatic_delegation_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-core/SKILL.md",
            "There is no automatic delegation",
            "Automatic delegation is required",
        )
        self.assert_mutation_fails()

    def test_core_automatic_review_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-core/SKILL.md",
            "review artifact, fixed role chain, preflight",
            "mandatory review artifact and fixed role preflight",
        )
        self.assert_mutation_fails()

    def test_core_automatic_loop_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-core/SKILL.md",
            "Do not enter Loop automatically",
            "Enter Loop automatically",
        )
        self.assert_mutation_fails()

    def test_core_explicit_assurance_boundary_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-core/SKILL.md",
            "Assurance is also explicit",
            "Assurance starts automatically for risky work",
        )
        self.assert_mutation_fails()

    def test_host_only_checkpoint_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-memory/SKILL.md",
            "Only the host agent writes active control memory",
            "Temporary agents may write active control memory",
        )
        self.assert_mutation_fails()

    def test_five_checkpoint_trigger_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-memory/SKILL.md",
            "Checkpoint only a real transition:",
            "Checkpoint every implementation step:",
        )
        self.assert_mutation_fails()

    def test_mission_replacement_checkpoint_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-memory/SKILL.md",
            "5. the active mission is replaced.",
            "5. every implementation step completes.",
        )
        self.assert_mutation_fails()

    def test_archive_opt_in_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-memory/SKILL.md",
            "Archive is not loaded by default",
            "Archive is loaded during every orientation",
        )
        self.assert_mutation_fails()

    def test_workflow_obligations_reintroduction_fails(self) -> None:
        path = self.repo / "plugins/forge/workflow-obligations.json"
        path.write_text('{"schema_version": 1, "obligations": []}\n', encoding="utf-8")
        self.assert_mutation_fails()

    def test_task_f_role_alias_reintroduction_fails(self) -> None:
        path = self.repo / "plugins/forge/skills/forge-engineer/SKILL.md"
        path.parent.mkdir(parents=True)
        path.write_text(
            "---\nname: forge-engineer\ndescription: role alias\n---\n",
            encoding="utf-8",
        )
        self.assert_mutation_fails()

    def test_task_f_legacy_role_reintroduction_fails(self) -> None:
        path = self.repo / "plugins/forge/skills/forge-reviewer/SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "---\nname: forge-reviewer\ndescription: legacy role\n---\n",
            encoding="utf-8",
        )
        self.assert_mutation_fails()

    def test_task_f_profile_scope_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-checker/SKILL.md",
            "Do not make repair edits",
            "Make repair edits when useful",
        )
        self.assert_mutation_fails()

    def test_task_f_exact_affirmative_authority_attacks_fail(self) -> None:
        attacks = (
            (
                "forge-checker",
                "Repair edits are permitted after a failed check.",
            ),
            (
                "forge-builder",
                "A Builder can delegate another profile when blocked.",
            ),
            (
                "forge-scout",
                "Scout can modify tests when useful.",
            ),
        )
        for profile, attack in attacks:
            with self.subTest(profile=profile, attack=attack):
                original = (
                    self.repo / f"plugins/forge/skills/{profile}/SKILL.md"
                ).read_text(encoding="utf-8")
                try:
                    self.assert_profile_authority_attack_fails(profile, attack)
                finally:
                    (
                        self.repo / f"plugins/forge/skills/{profile}/SKILL.md"
                    ).write_text(original, encoding="utf-8")

    def test_task_f_additive_self_and_memory_authority_grants_fail(self) -> None:
        attacks = (
            ("forge-builder", "A Builder may self-approve after tests pass."),
            ("forge-builder", "A Builder is allowed to self-integrate."),
            ("forge-scout", "Scout may write active memory when blocked."),
            ("forge-checker", "Checker is permitted to modify active memory."),
        )
        for profile, attack in attacks:
            with self.subTest(profile=profile, attack=attack):
                original = (
                    self.repo / f"plugins/forge/skills/{profile}/SKILL.md"
                ).read_text(encoding="utf-8")
                try:
                    self.assert_profile_authority_attack_fails(profile, attack)
                finally:
                    (
                        self.repo / f"plugins/forge/skills/{profile}/SKILL.md"
                    ).write_text(original, encoding="utf-8")

    def test_task_f_reviewer_authority_grant_forms_fail(self) -> None:
        attacks = (
            ("forge-checker", "Checker is authorized to repair edits."),
            ("forge-checker", "Checker has permission to repair code."),
            ("forge-checker", "Checker shall repair edits after a failed check."),
            (
                "forge-builder",
                "A Builder is authorized to delegate another profile.",
            ),
            (
                "forge-builder",
                "A Builder has permission to invoke a profile.",
            ),
            (
                "forge-builder",
                "A Builder shall delegate another profile when blocked.",
            ),
            ("forge-scout", "Scout is authorized to modify tests."),
            ("forge-scout", "Scout has permission to edit tests."),
            ("forge-scout", "Scout shall modify tests when useful."),
        )
        for profile, attack in attacks:
            with self.subTest(profile=profile, attack=attack):
                original = (
                    self.repo / f"plugins/forge/skills/{profile}/SKILL.md"
                ).read_text(encoding="utf-8")
                try:
                    self.assert_profile_authority_attack_fails(profile, attack)
                finally:
                    (
                        self.repo / f"plugins/forge/skills/{profile}/SKILL.md"
                    ).write_text(original, encoding="utf-8")

    def test_task_f_builder_declared_scope_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-builder/SKILL.md",
            "Implement only within the declared write scope",
            "Implement anywhere useful",
        )
        self.assert_mutation_fails()

    def test_task_f_builder_self_approval_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-builder/SKILL.md",
            "Never self-approve",
            "Self-approve when checks pass",
        )
        self.assert_mutation_fails()

    def test_task_f_builder_nested_delegation_weakening_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-builder/SKILL.md",
            "Never invoke or delegate to another profile",
            "Delegate to another profile when useful",
        )
        self.assert_mutation_fails()

    def test_task_f_profile_frontmatter_mutations_fail(self) -> None:
        relative = "plugins/forge/skills/forge-checker/SKILL.md"
        mutations = (
            (
                'name: "forge-checker"',
                'name: "forge-checker"\nname: "forge-checker"',
            ),
            ('name: "forge-checker"', 'name: "forge-scout"'),
            ("---\n\n# Forge Checker", "---junk\n\n# Forge Checker"),
        )
        for old, new in mutations:
            with self.subTest(old=old, new=new):
                path = self.repo / relative
                original = path.read_text(encoding="utf-8")
                self.assertIn(old, original)
                try:
                    path.write_text(
                        original.replace(old, new, 1),
                        encoding="utf-8",
                    )
                    self.assert_mutation_fails()
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_task_f_profile_frontmatter_scalar_mutations_fail(self) -> None:
        relative = "plugins/forge/skills/forge-checker/SKILL.md"
        replacements = (
            "description: [unterminated",
            "description: unquoted",
            'description: "invalid\\q"',
            'description: "valid" trailing',
        )
        for replacement in replacements:
            with self.subTest(replacement=replacement):
                path = self.repo / relative
                original = path.read_text(encoding="utf-8")
                description = next(
                    line for line in original.splitlines()
                    if line.startswith("description:")
                )
                try:
                    path.write_text(
                        original.replace(description, replacement, 1),
                        encoding="utf-8",
                    )
                    self.assert_mutation_fails()
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_task_f_active_memory_write_grant_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-builder/SKILL.md",
            "Never write `.forge/INTENT.md` or `.forge/MISSION.md`",
            "May write `.forge/INTENT.md` or `.forge/MISSION.md`",
        )
        self.assert_mutation_fails()

    def test_task_f_mandatory_chain_rule_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/skills/forge-scout/SKILL.md",
            "not a mandatory chain",
            "a mandatory chain",
        )
        self.assert_mutation_fails()

    def test_task_f_common_return_drift_fails(self) -> None:
        self.mutate_text(
            "plugins/forge/templates/agent-return.md",
            "## Evidence and exact command outcomes",
            "## Evidence",
        )
        self.assert_mutation_fails()

    def test_task_f_common_return_frontmatter_mutations_fail(self) -> None:
        relative = "plugins/forge/templates/agent-return.md"
        mutations = (
            (
                'format: "forge-agent-return-v1"',
                'format: "forge-agent-return-v0"',
            ),
            (
                'format: "forge-agent-return-v1"',
                'format: "forge-agent-return-v1',
            ),
            ("profile: \"\"", "profile: \"\"\nprofile: duplicate"),
            ("authority_boundary: \"\"\n", ""),
            ("change_location: \"\"\n", ""),
            (
                "change_location: \"\"\n---",
                "change_location: \"\"\nunknown: forbidden\n---",
            ),
        )
        for old, new in mutations:
            with self.subTest(old=old, new=new):
                path = self.repo / relative
                original = path.read_text(encoding="utf-8")
                self.assertIn(old, original)
                try:
                    path.write_text(
                        original.replace(old, new, 1),
                        encoding="utf-8",
                    )
                    self.assert_mutation_fails()
                finally:
                    path.write_text(original, encoding="utf-8")

    def test_version_mismatch_fails(self) -> None:
        manifest = self.repo / "plugins/forge/.claude-plugin/plugin.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["version"] = "9.9.9"
        manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assert_mutation_fails()

    def test_nonzero_version_without_changelog_entry_fails(self) -> None:
        (self.repo / "VERSION").write_text("9.9.8\n", encoding="utf-8")
        for relative in (
            "plugins/forge/.claude-plugin/plugin.json",
            "plugins/forge/.codex-plugin/plugin.json",
            "plugins/forge/.cursor-plugin/plugin.json",
        ):
            manifest = self.repo / relative
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["version"] = "9.9.8"
            manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        result = self.run_validator()

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "CHANGELOG entry is missing for VERSION 9.9.8",
            result.stdout,
        )

    def test_capability_unknown_field_fails(self) -> None:
        capability = self.repo / "plugins/forge/platform-capabilities.json"
        data = json.loads(capability.read_text(encoding="utf-8"))
        data["unexpected"] = True
        capability.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assert_mutation_fails()

    def test_capability_profile_drift_fails(self) -> None:
        capability = self.repo / "plugins/forge/platform-capabilities.json"
        data = json.loads(capability.read_text(encoding="utf-8"))
        data["shared_profiles"] = [
            "forge-scout",
            "forge-builder",
            "forge-reviewer",
        ]
        capability.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assert_mutation_fails()

    def test_adapter_status_drift_fails(self) -> None:
        capability = self.repo / "plugins/forge/platform-capabilities.json"
        data = json.loads(capability.read_text(encoding="utf-8"))
        data["host_adapters"][0]["status"] = "pending-task-h"
        capability.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        self.assert_mutation_fails()

if __name__ == "__main__":
    unittest.main()
