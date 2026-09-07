#!/usr/bin/env python3
"""Validate a prepared Forge release receipt before irreversible Git mutation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

CANONICAL_ALLOWLIST = [
    "VERSION",
    "plugins/forge/.codex-plugin/plugin.json",
    "plugins/forge/.claude-plugin/plugin.json",
    "plugins/forge/.cursor-plugin/plugin.json",
    "package.json",
    "packages/deepseek-harness/package.json",
]
CANONICAL_VALIDATION = {
    "content": "passed",
    "memory": "passed",
    "packaging": "passed",
    "product_scope": "passed",
    "release_matrix": "passed",
    "shell_syntax": "passed",
    "host_packages_static": "passed",
}
CANONICAL_KEYS = {
    "schema_version",
    "version",
    "tag",
    "base_head",
    "allowlist",
    "pre_sha256",
    "post_sha256",
    "tag_absent",
    "prepared_at",
    "validation",
}


class ReceiptError(ValueError):
    pass


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def validate_receipt(
    receipt: dict[str, Any],
    *,
    version: str,
    current_head: str,
    repository: Path,
) -> None:
    if set(receipt) != CANONICAL_KEYS or receipt.get("schema_version") != 1:
        raise ReceiptError("invalid receipt schema")
    if (
        receipt.get("version") != version
        or receipt.get("tag") != f"v{version}"
        or receipt.get("base_head") != current_head
        or receipt.get("allowlist") != CANONICAL_ALLOWLIST
        or receipt.get("tag_absent") is not True
        or receipt.get("validation") != CANONICAL_VALIDATION
    ):
        raise ReceiptError("receipt canonical values changed")
    try:
        prepared_at = datetime.fromisoformat(str(receipt["prepared_at"]).replace("Z", "+00:00"))
        if prepared_at.tzinfo is None:
            raise ValueError
    except (TypeError, ValueError) as error:
        raise ReceiptError("invalid receipt timestamp") from error

    for map_name in ("pre_sha256", "post_sha256"):
        digest_map = receipt.get(map_name)
        if not isinstance(digest_map, dict) or set(digest_map) != set(CANONICAL_ALLOWLIST):
            raise ReceiptError(f"{map_name} keys changed")
        if any(not isinstance(value, str) or len(value) != 64 for value in digest_map.values()):
            raise ReceiptError(f"{map_name} value is invalid")

    for path in CANONICAL_ALLOWLIST:
        try:
            previous = subprocess.check_output(
                ["git", "show", f"{current_head}:{path}"],
                cwd=repository,
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError as error:
            raise ReceiptError(f"pre-image missing at base HEAD: {path}") from error
        if sha256(previous) != receipt["pre_sha256"][path]:
            raise ReceiptError(f"pre-image digest changed: {path}")
        current_path = repository / path
        if not current_path.is_file() or sha256(current_path.read_bytes()) != receipt["post_sha256"][path]:
            raise ReceiptError(f"prepared file changed: {path}")

    tag = f"v{version}"
    if subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
        cwd=repository,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0:
        raise ReceiptError("target tag now exists")

    changed = sorted(
        line[3:]
        for line in subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=repository, text=True
        ).splitlines()
    )
    if changed != sorted(CANONICAL_ALLOWLIST):
        raise ReceiptError("worktree diff does not match receipt allowlist")


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: validate_release_receipt.py <receipt> <version> <head>", file=sys.stderr)
        return 1
    receipt_path, version, current_head = sys.argv[1:]
    repository = Path.cwd()
    try:
        receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        validate_receipt(receipt, version=version, current_head=current_head, repository=repository)
    except (OSError, json.JSONDecodeError, ReceiptError) as error:
        print(f"release: {error}", file=sys.stderr)
        return 1
    print("release receipt valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
