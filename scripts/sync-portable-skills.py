#!/usr/bin/env python3
"""Synchronize Forge's portable Agent Skills package and bundled runtime."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "forge"
CANONICAL_SKILLS = PLUGIN / "skills"
RUNTIME = CANONICAL_SKILLS / "forge-memory" / "assets" / "portable"
LEGACY_RUNTIME = CANONICAL_SKILLS / "forge-memory" / "assets" / "runtime"
PORTABLE_SKILLS = ROOT / ".agents" / "skills"
DSH_SKILLS = ROOT / "packages" / "deepseek-harness" / "skills"

RUNTIME_SOURCES = {
    **{
        Path("scripts") / name: PLUGIN / "scripts" / name
        for name in (
            "forge-init",
            "forge-status",
            "forge-checkpoint",
            "forge-compact",
            "forge-memory-validate",
        )
    },
    **{
        Path("lib") / name: PLUGIN / "lib" / name
        for name in ("forge_files.py", "forge_memory.py")
    },
    **{
        Path("templates") / name: PLUGIN / "templates" / name
        for name in ("agent-return.md", "assurance-result.md")
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_map(root: Path) -> dict[Path, str]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root): digest(path)
        for path in root.rglob("*")
        if path.is_file()
    }


def expected_runtime() -> dict[Path, str]:
    return {relative: digest(source) for relative, source in RUNTIME_SOURCES.items()}


def check() -> list[str]:
    errors: list[str] = []
    if file_map(RUNTIME) != expected_runtime():
        errors.append("canonical skill runtime is out of sync")
    canonical = file_map(CANONICAL_SKILLS)
    for label, target in (
        ("portable Agent Skills", PORTABLE_SKILLS),
        ("DeepSeek Harness skills", DSH_SKILLS),
    ):
        if file_map(target) != canonical:
            errors.append(f"{label} payload is out of sync")
    return errors


def synchronize() -> None:
    if LEGACY_RUNTIME.exists():
        shutil.rmtree(LEGACY_RUNTIME)
    if RUNTIME.exists():
        shutil.rmtree(RUNTIME)
    for relative, source in RUNTIME_SOURCES.items():
        target = RUNTIME / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    for target in (PORTABLE_SKILLS, DSH_SKILLS):
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(CANONICAL_SKILLS, target)


def main(arguments: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    options = parser.parse_args(arguments)
    if not options.check:
        synchronize()
    errors = check()
    if errors:
        for error in errors:
            print(f"sync-portable-skills ERROR: {error}", file=sys.stderr)
        return 1
    print("sync-portable-skills PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
