from __future__ import annotations

import errno
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest import mock
import unittest


ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / "plugins/forge/lib"
sys.path.insert(0, str(LIB))

import forge_files  # noqa: E402
from forge_files import atomic_write, validate_managed_path  # noqa: E402


def sharing_violation(winerror: int) -> PermissionError:
    error = PermissionError(errno.EACCES, "sharing denied")
    error.winerror = winerror
    return error


class ForgeFilesTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name) / "project"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def create_symlink(
        self, link: Path, target: Path, *, target_is_directory: bool
    ) -> None:
        try:
            link.symlink_to(target, target_is_directory=target_is_directory)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EPERM) or getattr(
                error, "winerror", None
            ) == 1314:
                self.skipTest(f"symlink creation is not permitted: {error}")
            raise
        except NotImplementedError as error:
            self.skipTest(f"symlinks are unsupported: {error}")

    def create_junction(self, link: Path, target: Path) -> None:
        if os.name != "nt":
            self.skipTest("Windows junction regression")
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            self.skipTest(
                f"junction creation failed: {result.stdout}{result.stderr}"
            )

    def test_atomic_write_replaces_target_and_cleans_temporary_file(self) -> None:
        target = self.root / "MISSION.md"
        target.write_bytes(b"old\n")

        atomic_write(self.root, target, b"new\n")

        self.assertEqual(b"new\n", target.read_bytes())
        self.assertEqual([], list(self.root.glob(".MISSION.*.tmp")))

    def test_atomic_write_preserves_existing_target_mode(self) -> None:
        target = self.root / "MISSION.md"
        target.write_bytes(b"old\n")
        target.chmod(0o444)
        original_mode = stat.S_IMODE(target.stat().st_mode)
        observed_mode = None

        def inspect_mode(
            source: os.PathLike[str] | str, destination: Path
        ) -> None:
            nonlocal observed_mode
            observed_mode = stat.S_IMODE(Path(source).stat().st_mode)
            raise OSError("stop before replacement")

        try:
            with mock.patch.object(
                forge_files.os, "replace", side_effect=inspect_mode
            ):
                with self.assertRaisesRegex(OSError, "stop before replacement"):
                    atomic_write(self.root, target, b"new\n")
        finally:
            target.chmod(0o666)

        self.assertEqual(original_mode, observed_mode)

    def test_successful_replace_preserves_existing_target_mode(self) -> None:
        target = self.root / "MISSION.md"
        target.write_bytes(b"old\n")
        target.chmod(0o666 if os.name == "nt" else 0o640)
        original_mode = stat.S_IMODE(target.stat().st_mode)

        atomic_write(self.root, target, b"new\n")

        self.assertEqual(original_mode, stat.S_IMODE(target.stat().st_mode))

    def test_new_file_uses_explicit_mode(self) -> None:
        target = self.root / "MISSION.md"

        try:
            atomic_write(self.root, target, b"new\n", mode=0o444)
            self.assertEqual(0o444, stat.S_IMODE(target.stat().st_mode))
        finally:
            target.chmod(0o666)

    def test_validate_managed_path_rejects_escape(self) -> None:
        outside = self.root.parent / "outside.md"

        with self.assertRaisesRegex(ValueError, "escapes managed root"):
            validate_managed_path(self.root, outside)

    def test_validate_managed_path_rejects_symlink_component(self) -> None:
        external = self.root.parent / "external"
        external.mkdir()
        linked = self.root / "linked"
        self.create_symlink(linked, external, target_is_directory=True)

        with self.assertRaisesRegex(ValueError, "symlink, junction, or reparse"):
            validate_managed_path(self.root, linked / "MISSION.md")

    def test_validate_managed_path_rejects_reparse_attribute(self) -> None:
        target = self.root / "MISSION.md"
        reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        real_lstat = forge_files.os.lstat

        def reparse_target(path: os.PathLike[str] | str):
            if Path(path) == target:
                return SimpleNamespace(st_file_attributes=reparse_flag)
            return real_lstat(path)

        with mock.patch.object(forge_files.os, "lstat", side_effect=reparse_target):
            with self.assertRaisesRegex(
                ValueError, "symlink, junction, or reparse"
            ):
                validate_managed_path(self.root, target)

    def test_validate_managed_path_rejects_windows_junction(self) -> None:
        external = self.root.parent / "external-junction"
        external.mkdir()
        junction = self.root / "junction"
        self.create_junction(junction, external)

        with self.assertRaisesRegex(ValueError, "symlink, junction, or reparse"):
            validate_managed_path(self.root, junction / "MISSION.md")

    def test_replace_retries_windows_error_5_then_succeeds(self) -> None:
        target = self.root / "MISSION.md"
        target.write_bytes(b"old\n")
        real_replace = forge_files.os.replace
        attempts = 0

        def fail_twice(source: os.PathLike[str] | str, destination: Path) -> None:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise sharing_violation(5)
            real_replace(source, destination)

        with mock.patch.object(forge_files.os, "replace", side_effect=fail_twice):
            with mock.patch.object(forge_files.time, "sleep"):
                atomic_write(self.root, target, b"new\n")

        self.assertEqual(3, attempts)
        self.assertEqual(b"new\n", target.read_bytes())

    def test_replace_retries_windows_error_32_then_exhausts(self) -> None:
        target = self.root / "MISSION.md"
        original = b"old\n"
        target.write_bytes(original)
        denied = sharing_violation(32)

        with mock.patch.object(
            forge_files.os, "replace", side_effect=denied
        ) as replace:
            with mock.patch.object(forge_files.time, "sleep") as sleep:
                with self.assertRaises(PermissionError) as raised:
                    atomic_write(self.root, target, b"new\n")

        self.assertIs(denied, raised.exception)
        self.assertEqual(3, replace.call_count)
        self.assertEqual(2, sleep.call_count)
        self.assertEqual(original, target.read_bytes())
        self.assertEqual([], list(self.root.glob(".MISSION.*.tmp")))

    def test_replace_does_not_retry_other_permission_errors(self) -> None:
        target = self.root / "MISSION.md"
        original = b"old\n"
        target.write_bytes(original)
        denied = sharing_violation(13)

        with mock.patch.object(
            forge_files.os, "replace", side_effect=denied
        ) as replace:
            with mock.patch.object(forge_files.time, "sleep") as sleep:
                with self.assertRaises(PermissionError):
                    atomic_write(self.root, target, b"new\n")

        self.assertEqual(1, replace.call_count)
        sleep.assert_not_called()
        self.assertEqual(original, target.read_bytes())

    def test_failed_replace_does_not_damage_existing_target(self) -> None:
        target = self.root / "MISSION.md"
        original = b"old\n"
        target.write_bytes(original)

        with mock.patch.object(
            forge_files.os, "replace", side_effect=OSError("replace failed")
        ):
            with self.assertRaisesRegex(OSError, "replace failed"):
                atomic_write(self.root, target, b"new\n")

        self.assertEqual(original, target.read_bytes())
        self.assertEqual([], list(self.root.glob(".MISSION.*.tmp")))

    def test_cleanup_unlinks_when_best_effort_chmod_fails(self) -> None:
        target = self.root / "MISSION.md"
        replace_error = OSError("replace failed")

        with mock.patch.object(
            forge_files.os, "replace", side_effect=replace_error
        ):
            with mock.patch.object(
                forge_files.os, "chmod", side_effect=OSError("chmod failed")
            ):
                with self.assertRaises(OSError) as raised:
                    atomic_write(self.root, target, b"new\n")

        self.assertIs(replace_error, raised.exception)
        self.assertEqual([], list(self.root.glob(".MISSION.*.tmp")))

    def test_write_failure_cleans_temporary_file(self) -> None:
        target = self.root / "MISSION.md"
        real_fdopen = forge_files.os.fdopen

        class WriteFailingStream:
            def __init__(self, descriptor: int, mode: str) -> None:
                self.stream = real_fdopen(descriptor, mode)

            def __enter__(self):
                self.stream.__enter__()
                return self

            def __exit__(self, *arguments):
                return self.stream.__exit__(*arguments)

            def write(self, data: bytes) -> int:
                raise OSError("write failed")

        with mock.patch.object(
            forge_files.os, "fdopen", side_effect=WriteFailingStream
        ):
            with self.assertRaisesRegex(OSError, "write failed"):
                atomic_write(self.root, target, b"new\n")

        self.assertEqual([], list(self.root.glob(".MISSION.*.tmp")))

    def test_fsync_failure_cleans_temporary_file(self) -> None:
        target = self.root / "MISSION.md"

        with mock.patch.object(
            forge_files.os, "fsync", side_effect=OSError("fsync failed")
        ):
            with self.assertRaisesRegex(OSError, "fsync failed"):
                atomic_write(self.root, target, b"new\n")

        self.assertEqual([], list(self.root.glob(".MISSION.*.tmp")))

    def test_mode_chmod_failure_cleans_temporary_file(self) -> None:
        target = self.root / "MISSION.md"

        with mock.patch.object(
            forge_files.os, "chmod", side_effect=OSError("chmod failed")
        ):
            with self.assertRaisesRegex(OSError, "chmod failed"):
                atomic_write(self.root, target, b"new\n", mode=0o444)

        self.assertEqual([], list(self.root.glob(".MISSION.*.tmp")))

    def test_mode_is_applied_while_open_and_fsynced_before_replace(self) -> None:
        target = self.root / "MISSION.md"
        events: list[tuple[str, bool]] = []
        state = {"open": False}
        real_fdopen = forge_files.os.fdopen
        real_chmod = forge_files.os.chmod
        real_fsync = forge_files.os.fsync
        real_replace = forge_files.os.replace

        class TrackingStream:
            def __init__(self, descriptor: int, mode: str) -> None:
                self.stream = real_fdopen(descriptor, mode)

            def __enter__(self):
                self.stream.__enter__()
                state["open"] = True
                return self

            def __exit__(self, *arguments):
                try:
                    return self.stream.__exit__(*arguments)
                finally:
                    state["open"] = False

            def write(self, data: bytes) -> int:
                return self.stream.write(data)

            def flush(self) -> None:
                self.stream.flush()

            def fileno(self) -> int:
                return self.stream.fileno()

        def record_chmod(path: Path, mode: int) -> None:
            events.append(("chmod", state["open"]))
            real_chmod(path, mode)

        def record_fsync(descriptor: int) -> None:
            events.append(("fsync", state["open"]))
            real_fsync(descriptor)

        def record_replace(source: Path, destination: Path) -> None:
            events.append(("replace", state["open"]))
            real_replace(source, destination)

        with mock.patch.object(
            forge_files.os, "fdopen", side_effect=TrackingStream
        ):
            with mock.patch.object(
                forge_files.os, "chmod", side_effect=record_chmod
            ):
                with mock.patch.object(
                    forge_files.os, "fsync", side_effect=record_fsync
                ):
                    with mock.patch.object(
                        forge_files.os, "replace", side_effect=record_replace
                    ):
                        atomic_write(
                            self.root, target, b"new\n", mode=stat.S_IWRITE
                        )

        self.assertEqual(
            [("chmod", True), ("fsync", True), ("replace", False)],
            events,
        )


if __name__ == "__main__":
    unittest.main()
