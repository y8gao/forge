from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/validate_release_receipt.py"
spec = importlib.util.spec_from_file_location("validate_release_receipt", MODULE_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


class ReleaseReceiptMutationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp_dir.name) / "repo"
        self.repo.mkdir()
        for relative, content in {
            "VERSION": "0.3.0\n",
            "plugins/forge/.codex-plugin/plugin.json": '{"version":"0.3.0"}\n',
            "plugins/forge/.claude-plugin/plugin.json": '{"version":"0.3.0"}\n',
            "plugins/forge/.cursor-plugin/plugin.json": '{"version":"0.3.0"}\n',
            "package.json": '{"version":"0.3.0"}\n',
            "packages/deepseek-harness/package.json": '{"version":"0.3.0"}\n',
        }.items():
            path = self.repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "forge@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.name", "Forge Test"], cwd=self.repo, check=True)
        subprocess.run(["git", "add", "."], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.repo, check=True)
        self.head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.repo, text=True).strip()
        self.pre = {
            path: self.sha(
                subprocess.check_output(
                    ["git", "show", f"{self.head}:{path}"], cwd=self.repo
                )
            )
            for path in module.CANONICAL_ALLOWLIST
        }
        (self.repo / "VERSION").write_text("0.3.1\n", encoding="utf-8")
        for relative in module.CANONICAL_ALLOWLIST[1:]:
            (self.repo / relative).write_text('{"version":"0.3.1"}\n', encoding="utf-8")
        self.post = {
            path: self.sha((self.repo / path).read_bytes()) for path in module.CANONICAL_ALLOWLIST
        }
        self.receipt = {
            "schema_version": 1,
            "version": "0.3.1",
            "tag": "v0.3.1",
            "base_head": self.head,
            "allowlist": list(module.CANONICAL_ALLOWLIST),
            "pre_sha256": dict(self.pre),
            "post_sha256": dict(self.post),
            "tag_absent": True,
            "prepared_at": "2026-08-23T00:00:00Z",
            "validation": dict(module.CANONICAL_VALIDATION),
        }

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @staticmethod
    def sha(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def validate(self, receipt: dict[str, object]) -> None:
        module.validate_receipt(receipt, version="0.3.1", current_head=self.head, repository=self.repo)

    def assert_rejected(self, receipt: dict[str, object]) -> None:
        with self.assertRaises(module.ReceiptError):
            self.validate(receipt)
        self.assertEqual(subprocess.check_output(["git", "rev-list", "--count", "HEAD"], cwd=self.repo, text=True).strip(), "1")
        self.assertFalse(subprocess.check_output(["git", "tag", "-l", "v0.3.1"], cwd=self.repo, text=True).strip())

    def test_valid_receipt_passes(self) -> None:
        self.validate(copy.deepcopy(self.receipt))

    def test_digest_map_order_is_not_semantic(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["pre_sha256"] = dict(reversed(list(receipt["pre_sha256"].items())))
        receipt["post_sha256"] = dict(reversed(list(receipt["post_sha256"].items())))
        self.validate(receipt)

    def test_each_canonical_scalar_rejects_one_invalid_value(self) -> None:
        mutations = {
            "schema_version": 2,
            "version": "0.3.2",
            "tag": "v9.9.9",
            "base_head": "0" * 40,
            "tag_absent": False,
            "prepared_at": "not-a-timestamp",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                receipt = copy.deepcopy(self.receipt)
                receipt[field] = value
                self.assert_rejected(receipt)

    def test_top_level_and_allowlist_missing_extra_and_order_reject(self) -> None:
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                receipt = copy.deepcopy(self.receipt)
                if mutation == "missing":
                    receipt.pop("prepared_at")
                else:
                    receipt["unexpected"] = True
                self.assert_rejected(receipt)
        for allowlist in (
            module.CANONICAL_ALLOWLIST[:-1],
            module.CANONICAL_ALLOWLIST + ["README.md"],
            list(reversed(module.CANONICAL_ALLOWLIST)),
        ):
            with self.subTest(allowlist=allowlist):
                receipt = copy.deepcopy(self.receipt)
                receipt["allowlist"] = allowlist
                self.assert_rejected(receipt)

    def test_each_validation_key_missing_and_value_mutation_rejects(self) -> None:
        for key in module.CANONICAL_VALIDATION:
            with self.subTest(key=key, mutation="missing"):
                receipt = copy.deepcopy(self.receipt)
                receipt["validation"].pop(key)
                self.assert_rejected(receipt)
            with self.subTest(key=key, mutation="value"):
                receipt = copy.deepcopy(self.receipt)
                receipt["validation"][key] = "failed"
                self.assert_rejected(receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["validation"]["unexpected"] = "passed"
        self.assert_rejected(receipt)

    def test_each_digest_key_missing_and_value_mutation_rejects(self) -> None:
        for map_name in ("pre_sha256", "post_sha256"):
            for key in module.CANONICAL_ALLOWLIST:
                with self.subTest(map_name=map_name, key=key, mutation="missing"):
                    receipt = copy.deepcopy(self.receipt)
                    receipt[map_name].pop(key)
                    self.assert_rejected(receipt)
                with self.subTest(map_name=map_name, key=key, mutation="value"):
                    receipt = copy.deepcopy(self.receipt)
                    receipt[map_name][key] = "0" * 64
                    self.assert_rejected(receipt)
            receipt = copy.deepcopy(self.receipt)
            receipt[map_name]["README.md"] = "0" * 64
            self.assert_rejected(receipt)


if __name__ == "__main__":
    unittest.main()
