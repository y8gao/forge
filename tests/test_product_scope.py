from __future__ import annotations

import runpy
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = runpy.run_path(str(ROOT / "scripts/validate-content.py")).get(
    "validate_product_scope"
)


class ProductScopeTests(unittest.TestCase):
    def validate(self, root: Path) -> list[str]:
        self.assertIsNotNone(
            VALIDATOR,
            "validate-content.py must expose validate_product_scope(root)",
        )
        return VALIDATOR(root)

    def fixture_repo(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        temporary_directory = tempfile.TemporaryDirectory()
        root = Path(temporary_directory.name)
        (root / "plugins").mkdir()
        shutil.copytree(ROOT / "plugins/forge", root / "plugins/forge")
        return temporary_directory, root

    def assert_forbidden_source(
        self, relative: str, source: str, expected: str
    ) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        path = root / relative
        path.write_text(path.read_text(encoding="utf-8") + source, encoding="utf-8")

        errors = self.validate(root)

        joined = "\n".join(errors)
        self.assertIn(relative, joined)
        self.assertIn(expected, joined)

    def assert_forbidden_replacement(
        self, relative: str, source: str, expected: str
    ) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        (root / relative).write_text(source, encoding="utf-8")

        errors = self.validate(root)

        joined = "\n".join(errors)
        self.assertIn(relative, joined)
        self.assertIn(expected, joined)

    def assert_source_allowed(self, relative: str, source: str) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        path = root / relative
        path.write_text(path.read_text(encoding="utf-8") + source, encoding="utf-8")

        errors = self.validate(root)

        matching = [error for error in errors if relative in error]
        self.assertEqual([], matching)

    def test_repository_baseline_has_no_scope_errors(self) -> None:
        self.assertEqual([], self.validate(ROOT))

    def test_compact_stays_within_loc_limit(self) -> None:
        limits = {"forge-compact": 250}
        for name, maximum in limits.items():
            with self.subTest(name=name):
                path = ROOT / "plugins/forge/scripts" / name
                self.assertLessEqual(len(path.read_text(encoding="utf-8").splitlines()), maximum)

    def test_transaction_journal_filename_is_rejected(self) -> None:
        self.assert_forbidden_source(
            "plugins/forge/scripts/forge-compact",
            '\nTRANSACTION_JOURNAL = ".compact-transaction.json"\n',
            "transaction journal",
        )

    def test_transaction_phase_machinery_is_rejected(self) -> None:
        self.assert_forbidden_source(
            "plugins/forge/scripts/forge-compact",
            "\ndef resume_transaction_phase():\n    pass\n",
            "transaction phase",
        )

    def test_digest_integrity_machinery_is_rejected(self) -> None:
        self.assert_forbidden_source(
            "plugins/forge/scripts/forge-compact",
            '\nimport hashlib\narchive_digest = hashlib.sha256(b"x").hexdigest()\n',
            "digest integrity",
        )

    def test_directory_flush_machinery_is_rejected(self) -> None:
        self.assert_forbidden_source(
            "plugins/forge/scripts/forge-compact",
            "\nimport ctypes\nctypes.windll.kernel32.FlushFileBuffers(1)\n",
            "directory flush",
        )

    def test_fsync_outside_file_helper_is_rejected(self) -> None:
        self.assert_forbidden_source(
            "plugins/forge/scripts/forge-compact",
            "\nos.fsync(directory_fd)\n",
            "fsync is allowed only",
        )

    def test_fsync_import_alias_is_resolved_semantically(self) -> None:
        self.assert_forbidden_source(
            "plugins/forge/scripts/forge-compact",
            (
                "\nfrom os import fsync as sync_file\n"
                "sync_file(directory_fd)\n"
            ),
            "fsync is allowed only",
        )
        self.assert_source_allowed(
            "plugins/forge/lib/forge_files.py",
            (
                "\nfrom os import fsync as sync_file\n"
                "with open(__file__, 'rb') as stream:\n"
                "    sync_file(stream.fileno())\n"
            ),
        )

    def test_lock_or_concurrency_enforcement_is_rejected(self) -> None:
        self.assert_forbidden_source(
            "plugins/forge/scripts/forge-compact",
            "\nfrom threading import Lock\nmigration_lock = Lock()\n",
            "lock/concurrency",
        )

    def test_file_helper_rejects_recovery_theater_but_allows_file_fsync(
        self,
    ) -> None:
        relative = "plugins/forge/lib/forge_files.py"
        mutations = (
            (
                '\nTRANSACTION_JOURNAL = ".write-transaction.json"\n',
                "transaction journal",
            ),
            ("\ndef resume_transaction_phase():\n    pass\n", "transaction phase"),
            (
                '\nimport hashlib\npayload_digest = hashlib.sha256(b"x").digest()\n',
                "digest integrity",
            ),
            (
                "\nimport ctypes\nctypes.windll.kernel32.FlushFileBuffers(1)\n",
                "directory flush",
            ),
            ("\nos.fsync(directory_fd)\n", "directory flush"),
            (
                "\nfrom threading import Lock\nwrite_lock = Lock()\n",
                "lock/concurrency",
            ),
        )
        for source, expected in mutations:
            with self.subTest(expected=expected, source=source):
                self.assert_forbidden_source(relative, source, expected)

    def test_init_and_checkpoint_must_reuse_shared_atomic_write(self) -> None:
        compliant = (
            "from forge_files import atomic_write\n\n"
            "def publish(root, path, data):\n"
            "    atomic_write(root, path, data)\n"
        )
        mutations = (
            (
                "plugins/forge/scripts/forge-init",
                compliant + "\nPath('MISSION.md').write_bytes(b'data')\n",
                "Path.write_bytes",
            ),
            (
                "plugins/forge/scripts/forge-init",
                compliant + "\ntemporary_fd, temporary = tempfile.mkstemp()\n",
                "tempfile.mkstemp",
            ),
            (
                "plugins/forge/scripts/forge-checkpoint",
                compliant + "\nos.replace(temporary, mission)\n",
                "os.replace",
            ),
        )
        for relative, source, primitive in mutations:
            with self.subTest(relative=relative, primitive=primitive):
                self.assert_forbidden_replacement(
                    relative,
                    source,
                    f"independent managed-write primitive {primitive}",
                )

    def test_shared_write_ownership_rejects_open_and_alias_bypasses(self) -> None:
        compliant = (
            "from forge_files import atomic_write\n\n"
            "def publish(root, path, data):\n"
            "    atomic_write(root, path, data)\n"
        )
        mutations = (
            (
                "plugins/forge/scripts/forge-init",
                "\ntarget.open('wb').write(b'data')\n",
                "open(write-capable mode)",
            ),
            (
                "plugins/forge/scripts/forge-init",
                "\ntarget.write_text('data', encoding='utf-8')\n",
                "Path.write_text",
            ),
            (
                "plugins/forge/scripts/forge-checkpoint",
                "\ntarget.write_bytes(b'data')\n",
                "Path.write_bytes",
            ),
            (
                "plugins/forge/scripts/forge-checkpoint",
                "\nimport os as operating_system\n"
                "operating_system.replace(temporary, target)\n",
                "os.replace",
            ),
            (
                "plugins/forge/scripts/forge-checkpoint",
                "\nfrom os import replace as swap\nswap(temporary, target)\n",
                "os.replace",
            ),
        )
        for relative, mutation, primitive in mutations:
            with self.subTest(relative=relative, primitive=primitive):
                self.assert_forbidden_replacement(
                    relative,
                    compliant + mutation,
                    f"independent managed-write primitive {primitive}",
                )

    def test_shared_write_ownership_checks_open_mode_at_call_site(self) -> None:
        compliant = (
            "from forge_files import atomic_write\n\n"
            "def publish(root, path, data):\n"
            "    atomic_write(root, path, data)\n"
        )
        write_capable = (
            (
                "with target.open('wb') as stream:\n"
                "    stream.write(data)\n"
            ),
            (
                "with open(target, 'wb') as stream:\n"
                "    stream.write(data)\n"
            ),
            (
                "stream = target.open(mode='ab')\n"
                "stream.write(data)\n"
            ),
            "stream = open(target, mode='r+b')\n",
        )
        for mutation in write_capable:
            with self.subTest(mutation=mutation):
                self.assert_forbidden_replacement(
                    "plugins/forge/scripts/forge-checkpoint",
                    compliant + "\n" + mutation,
                    "independent managed-write primitive open(write-capable mode)",
                )

        read_only = (
            "with target.open('rb') as stream:\n    stream.read()\n",
            "with open(target, mode='r') as stream:\n    stream.read()\n",
            "stream = open(target)\n",
        )
        for mutation in read_only:
            with self.subTest(mutation=mutation):
                temporary_directory, root = self.fixture_repo()
                try:
                    path = root / "plugins/forge/scripts/forge-checkpoint"
                    path.write_text(compliant + "\n" + mutation, encoding="utf-8")

                    errors = self.validate(root)

                    matching = [
                        error
                        for error in errors
                        if "plugins/forge/scripts/forge-checkpoint" in error
                    ]
                    self.assertEqual([], matching)
                finally:
                    temporary_directory.cleanup()

    def test_only_transaction_phase_symbols_are_rejected(self) -> None:
        relative = "plugins/forge/scripts/forge-compact"
        self.assert_source_allowed(
            relative,
            '\ndeployment_phase = "prepare"\n',
        )
        self.assert_forbidden_source(
            relative,
            '\ntransaction_phase = "archive-published"\n',
            "transaction phase",
        )

    def test_runtime_control_plane_inventory_growth_is_rejected(self) -> None:
        additions = (
            ("plugins/forge/runtime/engine.py", "runtime"),
            ("plugins/forge/lib/event_ledger.py", "ledger"),
            ("plugins/forge/scripts/forge-scheduler", "scheduler"),
            ("plugins/forge/commands/control-plane.md", "control-plane"),
        )
        for relative, surface in additions:
            with self.subTest(relative=relative):
                temporary_directory, root = self.fixture_repo()
                try:
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("synthetic product surface\n", encoding="utf-8")

                    errors = self.validate(root)

                    joined = "\n".join(errors)
                    self.assertIn(relative, joined)
                    self.assertIn(surface, joined)
                finally:
                    temporary_directory.cleanup()

    def test_runtime_policy_inventory_growth_is_rejected(self) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        added = root / "plugins/forge/scripts/forge-policy-runtime"
        added.write_text("#!/usr/bin/env python3\n", encoding="utf-8")

        errors = self.validate(root)

        joined = "\n".join(errors)
        self.assertIn("plugins/forge/scripts/forge-policy-runtime", joined)
        self.assertIn("policy", joined)

    def test_runtime_and_legacy_database_surfaces_are_absent(self) -> None:
        for relative in (
            "plugins/forge/scripts/forge-workflow-policy",
            "plugins/forge/scripts/forge-index",
            "plugins/forge/scripts/forge-history",
            "plugins/forge/scripts/forge-migrate",
            "plugins/forge/scripts/validate-intent",
            "plugins/forge/docs/DOCTRINE.md",
            "plugins/forge/workflow-obligations.json",
        ):
            with self.subTest(relative=relative):
                self.assertFalse((ROOT / relative).exists(), relative)

    def test_obsolete_compatibility_surfaces_are_rejected(self) -> None:
        additions = (
            ("install.sh", "#!/usr/bin/env bash\n", "install.sh"),
            (
                "plugins/forge/scripts/forge-migrate",
                "#!/usr/bin/env python3\n",
                "plugins/forge/scripts/forge-migrate",
            ),
            (
                "plugins/forge/scripts/validate-intent",
                "#!/usr/bin/env python3\n",
                "plugins/forge/scripts/validate-intent",
            ),
            (
                "plugins/forge/docs/DOCTRINE.md",
                "# Legacy doctrine\n",
                "plugins/forge/docs/DOCTRINE.md",
            ),
            (
                "plugins/forge/docs/AGENTS-BRIDGE.md",
                "# Legacy bridge notice\n",
                "plugins/forge/docs/AGENTS-BRIDGE.md",
            ),
            ("docs/superpowers/plan.md", "# Historical plan\n", "docs/superpowers"),
            (
                "docs/archive/retrospective.md",
                "# Historical archive\n",
                "docs/archive",
            ),
            ("docs/dogfood/task.json", "{}\n", "docs/dogfood"),
            (
                "scripts/summarize-memory-first-dogfood.py",
                "#!/usr/bin/env python3\n",
                "scripts/summarize-memory-first-dogfood.py",
            ),
        )
        for relative, source, reported in additions:
            with self.subTest(relative=relative):
                temporary_directory, root = self.fixture_repo()
                try:
                    path = root / relative
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(source, encoding="utf-8")

                    joined = "\n".join(self.validate(root))

                    self.assertIn(reported, joined)
                    self.assertIn("obsolete compatibility/history surface", joined)
                finally:
                    temporary_directory.cleanup()

    def test_workflow_obligations_are_not_a_shipped_product_surface(self) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        obligations = root / "plugins/forge/workflow-obligations.json"
        obligations.write_text(
            '{"schema_version": 1, "obligations": []}\n',
            encoding="utf-8",
        )

        errors = self.validate(root)

        joined = "\n".join(errors)
        self.assertIn("plugins/forge/workflow-obligations.json", joined)
        self.assertIn("obsolete fixed-workflow surface", joined)

    def test_task_f_rejects_role_alias_skill_growth(self) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        alias = root / "plugins/forge/skills/forge-engineer/SKILL.md"
        alias.parent.mkdir(parents=True)
        alias.write_text(
            "---\nname: forge-engineer\ndescription: role alias\n---\n",
            encoding="utf-8",
        )

        joined = "\n".join(self.validate(root))

        self.assertIn("plugins/forge/skills/forge-engineer/SKILL.md", joined)
        self.assertIn("unsupported capability or role skill", joined)

    def test_task_f_allows_additional_nonprofile_product_skills(self) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)

        matching = [
            error for error in self.validate(root)
            if "plugins/forge/skills/forge-loop/SKILL.md" in error
        ]

        self.assertEqual([], matching)

    def test_task_h_rejects_agent_wrapper_inventory_growth(self) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        wrapper = root / "plugins/forge/agents/forge-reviewer.md"
        wrapper.parent.mkdir(parents=True, exist_ok=True)
        wrapper.write_text("temporary wrapper\n", encoding="utf-8")

        joined = "\n".join(self.validate(root))

        self.assertIn("plugins/forge/agents/forge-reviewer.md", joined)
        self.assertIn("unsupported agent wrapper", joined)

    def test_task_f_rejects_legacy_role_templates(self) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        legacy = root / "plugins/forge/templates/test-plan.md"
        legacy.write_text("---\nid: legacy\n---\n", encoding="utf-8")

        joined = "\n".join(self.validate(root))

        self.assertIn("plugins/forge/templates/test-plan.md", joined)
        self.assertIn("legacy role template", joined)

    def test_docs_tests_and_forge_archives_are_not_scanned_as_product_source(self) -> None:
        temporary_directory, root = self.fixture_repo()
        self.addCleanup(temporary_directory.cleanup)
        ignored = {
            "plugins/forge/docs/runtime-policy-history.md": (
                "hashlib SHA digest runtime ledger control-plane scheduler\n"
            ),
            "tests/fixtures/synthetic_runtime.py": "from threading import Lock\n",
            ".forge/archive/old-runtime.md": "control-plane scheduler\n",
            ".forge/reviews/runtime-review.md": "directory fsync ctypes\n",
        }
        for relative, text in ignored.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        joined = "\n".join(self.validate(root))
        for relative in ignored:
            self.assertNotIn(relative, joined)


if __name__ == "__main__":
    unittest.main()
