from __future__ import annotations

import json
import os
import re
import runpy
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "scripts/release.sh"
MANIFESTS = (
    "plugins/forge/.claude-plugin/plugin.json",
    "plugins/forge/.codex-plugin/plugin.json",
    "plugins/forge/.cursor-plugin/plugin.json",
)


class ReleaseStaticTests(unittest.TestCase):
    def test_version_is_synchronized_across_three_host_manifests(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^[0-9]+\.[0-9]+\.[0-9]+$")
        for relative in MANIFESTS:
            with self.subTest(manifest=relative):
                data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
                self.assertEqual(version, data["version"])

    def test_required_release_checks_propagate_each_failure(self) -> None:
        release = RELEASE.read_text(encoding="utf-8")
        checks = release.split("run_required_checks() {", 1)[1].split(
            "\n}\n", 1
        )[0]
        for command in (
            "python3 scripts/validate-content.py",
            "python3 plugins/forge/scripts/forge-memory-validate .",
            "python3 -m unittest tests.test_platform_agents",
            "FORGE_RELEASE_TESTING=1 python3 -m unittest tests.test_release",
            "bash -n scripts/release.sh",
            "claude plugin validate .",
            "claude plugin validate ./plugins/forge",
        ):
            with self.subTest(command=command):
                self.assertRegex(
                    checks,
                    re.escape(command) + r"[^\n]*\|\| return 1",
                )

    def test_release_allowlist_matches_receipt_validator(self) -> None:
        module = runpy.run_path(str(ROOT / "scripts/validate_release_receipt.py"))
        expected = ["VERSION", *MANIFESTS[1::-1], MANIFESTS[2]]
        self.assertEqual(expected, module["CANONICAL_ALLOWLIST"])
        release = RELEASE.read_text(encoding="utf-8")
        for relative in expected:
            self.assertIn(f'"{relative}"', release)

    def test_missing_host_clis_do_not_fail_static_gate(self) -> None:
        release = RELEASE.read_text(encoding="utf-8")
        self.assertIn("Claude CLI unavailable; static package checks passed", release)
        self.assertIn("Codex CLI unavailable; static package checks passed", release)
        self.assertNotIn("required Claude validation unavailable", release)
        self.assertNotIn("git push", release)
        self.assertNotIn("gh release", release)

    def test_release_uses_memory_first_validator(self) -> None:
        release = RELEASE.read_text(encoding="utf-8")
        self.assertIn("forge-memory-validate .", release)
        self.assertNotIn("validate-intent", release)
        self.assertNotIn("install.sh", release)

    def test_receipt_names_static_host_package_evidence_honestly(self) -> None:
        module = runpy.run_path(str(ROOT / "scripts/validate_release_receipt.py"))
        self.assertIn("host_packages_static", module["CANONICAL_VALIDATION"])
        self.assertNotIn("host_manifests", module["CANONICAL_VALIDATION"])
        self.assertNotIn("installer", module["CANONICAL_VALIDATION"])


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name) / "repo"
        self.repo.mkdir()
        fixture_files = (
            "VERSION",
            "CHANGELOG.md",
            "scripts/release.sh",
            "scripts/validate_release_receipt.py",
            "plugins/forge/lib/forge_memory.py",
            "plugins/forge/scripts/forge-memory-validate",
            *MANIFESTS,
            ".forge/INTENT.md",
            ".forge/MISSION.md",
        )
        for relative in fixture_files:
            target = self.repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        self.bin = Path(self.temp_dir.name) / "bin"
        self.bin.mkdir()
        claude = self.bin / "claude"
        claude.write_bytes(b"#!/bin/sh\nexit 0\n")
        claude.chmod(0o755)
        self.env = os.environ.copy()
        self.env["PATH"] = f"{self.bin}{os.pathsep}{self.env['PATH']}"
        self.env["FORGE_RELEASE_TESTING"] = "1"
        self.run_cmd("git", "init", "-q")
        self.run_cmd("git", "config", "user.email", "forge@example.invalid")
        self.run_cmd("git", "config", "user.name", "Forge Test")
        self.run_cmd("git", "add", ".")
        self.run_cmd("git", "commit", "-qm", "baseline")
        major, minor, patch = map(
            int, (self.repo / "VERSION").read_text().strip().split(".")
        )
        self.current_version = f"{major}.{minor}.{patch}"
        self.target_version = f"{major}.{minor}.{patch + 1}"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_cmd(
        self, *command: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=self.repo,
            capture_output=True,
            text=True,
            check=False,
            env=env or self.env,
        )

    def run_release(
        self, *arguments: str, env: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        values = env or self.env
        names = (
            "FORGE_RELEASE_FAIL_PREPARED_CHECK",
            "FORGE_RELEASE_TEST_MUTATE_AFTER_CHECKS",
            "FORGE_RELEASE_FAIL_TAG",
        )
        assignments = " ".join(
            f"{name}={shlex.quote(values.get(name, ''))}" for name in names
        )
        command_arguments = " ".join(shlex.quote(value) for value in arguments)
        return self.run_cmd(
            "bash",
            "-c",
            f"{assignments} FORGE_RELEASE_TESTING=1 "
            f"bash scripts/release.sh {command_arguments}",
            env=env,
        )

    def commit_target_changelog(self, version: str | None = None) -> str:
        version = version or self.target_version
        changelog = self.repo / "CHANGELOG.md"
        text = changelog.read_text(encoding="utf-8")
        changelog.write_text(
            text.replace(
                "All notable changes to this project are documented in this file.\n",
                "All notable changes to this project are documented in this file."
                f"\n\n## [{version}] - 2026-09-04\n\n- Test release.\n",
                1,
            ),
            encoding="utf-8",
        )
        self.run_cmd("git", "add", "CHANGELOG.md")
        result = self.run_cmd("git", "commit", "-qm", "prepare changelog")
        self.assertEqual(result.returncode, 0, result.stderr)
        return version

    def next_missing_version(self) -> str:
        major, minor, patch = map(
            int, (self.repo / "VERSION").read_text().strip().split(".")
        )
        changelog = (self.repo / "CHANGELOG.md").read_text(encoding="utf-8")
        while True:
            patch += 1
            candidate = f"{major}.{minor}.{patch}"
            if f"## [{candidate}]" not in changelog:
                return candidate

    def test_rejects_equal_version(self) -> None:
        result = self.run_release("prepare", self.current_version)
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_dynamic_missing_changelog_version(self) -> None:
        result = self.run_release("prepare", self.next_missing_version())
        self.assertNotEqual(result.returncode, 0)

    def test_rejects_dirty_tree(self) -> None:
        (self.repo / "README.md").write_text("dirty\n", encoding="utf-8")
        result = self.run_release("prepare", self.target_version)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(
            (self.repo / ".git/forge-release-receipt.json").exists()
        )

    def test_prepare_writes_only_allowlist_and_receipt(self) -> None:
        target = self.commit_target_changelog()
        result = self.run_release("prepare", target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        changed = sorted(
            line[3:]
            for line in self.run_cmd("git", "status", "--porcelain").stdout.splitlines()
        )
        module = runpy.run_path(
            str(self.repo / "scripts/validate_release_receipt.py")
        )
        self.assertEqual(changed, sorted(module["CANONICAL_ALLOWLIST"]))
        receipt = json.loads(
            (self.repo / ".git/forge-release-receipt.json").read_text()
        )
        self.assertTrue(
            (self.repo / ".git/forge-release-receipt.sha256").is_file()
        )
        self.assertEqual(
            receipt["base_head"],
            self.run_cmd("git", "rev-parse", "HEAD").stdout.strip(),
        )
        self.assertEqual(receipt["validation"], module["CANONICAL_VALIDATION"])
        self.assertFalse(
            self.run_cmd("git", "tag", "-l", f"v{target}").stdout.strip()
        )

    def test_prepared_validation_failure_restores_files(self) -> None:
        target = self.commit_target_changelog()
        module = runpy.run_path(
            str(self.repo / "scripts/validate_release_receipt.py")
        )
        before = {
            path: (self.repo / path).read_bytes()
            for path in module["CANONICAL_ALLOWLIST"]
        }
        env = self.env.copy()
        env["FORGE_RELEASE_FAIL_PREPARED_CHECK"] = "1"
        result = self.run_release("prepare", target, env=env)
        self.assertNotEqual(result.returncode, 0)
        for path, content in before.items():
            self.assertEqual((self.repo / path).read_bytes(), content)
        self.assertFalse(self.run_cmd("git", "status", "--porcelain").stdout.strip())

    def prepare(self) -> str:
        target = self.commit_target_changelog()
        result = self.run_release("prepare", target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return target

    def test_commit_rejects_changed_head(self) -> None:
        target = self.prepare()
        self.run_cmd("git", "add", "VERSION")
        self.run_cmd("git", "commit", "-qm", "change head")
        before = self.run_cmd("git", "rev-list", "--count", "HEAD").stdout
        result = self.run_release("commit", target, "--authorized")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            before, self.run_cmd("git", "rev-list", "--count", "HEAD").stdout
        )

    def test_commit_rejects_changed_receipt(self) -> None:
        target = self.prepare()
        receipt = self.repo / ".git/forge-release-receipt.json"
        data = json.loads(receipt.read_text())
        data["prepared_at"] = "2030-01-01T00:00:00Z"
        receipt.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
        result = self.run_release("commit", target, "--authorized")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(
            self.run_cmd("git", "tag", "-l", f"v{target}").stdout.strip()
        )

    def test_commit_revalidates_after_required_checks(self) -> None:
        target = self.prepare()
        before = self.run_cmd("git", "rev-list", "--count", "HEAD").stdout
        env = self.env.copy()
        env["FORGE_RELEASE_TEST_MUTATE_AFTER_CHECKS"] = "1"
        result = self.run_release("commit", target, "--authorized", env=env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            before, self.run_cmd("git", "rev-list", "--count", "HEAD").stdout
        )

    def test_tag_failure_leaves_one_recoverable_release_commit(self) -> None:
        target = self.prepare()
        before = int(
            self.run_cmd("git", "rev-list", "--count", "HEAD").stdout.strip()
        )
        env = self.env.copy()
        env["FORGE_RELEASE_FAIL_TAG"] = "1"
        result = self.run_release("commit", target, "--authorized", env=env)
        self.assertEqual(2, result.returncode, result.stdout + result.stderr)
        after = int(
            self.run_cmd("git", "rev-list", "--count", "HEAD").stdout.strip()
        )
        self.assertEqual(before + 1, after)
        self.assertFalse(
            self.run_cmd("git", "tag", "-l", f"v{target}").stdout.strip()
        )

    def test_success_creates_exactly_one_release_commit_and_tag(self) -> None:
        target = self.prepare()
        before = int(
            self.run_cmd("git", "rev-list", "--count", "HEAD").stdout.strip()
        )
        result = self.run_release("commit", target, "--authorized")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        after = int(
            self.run_cmd("git", "rev-list", "--count", "HEAD").stdout.strip()
        )
        self.assertEqual(before + 1, after)
        self.assertEqual(
            f"v{target}",
            self.run_cmd("git", "tag", "-l", f"v{target}").stdout.strip(),
        )
        self.assertFalse(self.run_cmd("git", "status", "--porcelain").stdout.strip())

    def test_prepare_rejects_existing_target_tag(self) -> None:
        target = self.commit_target_changelog()
        self.run_cmd("git", "tag", f"v{target}")
        before = self.run_cmd("git", "rev-list", "--count", "HEAD").stdout
        result = self.run_release("prepare", target)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            before, self.run_cmd("git", "rev-list", "--count", "HEAD").stdout
        )


if __name__ == "__main__":
    unittest.main()
