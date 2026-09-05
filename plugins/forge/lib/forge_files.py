from __future__ import annotations

import os
from pathlib import Path
import stat
import tempfile
import time


_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
_RETRYABLE_WINDOWS_ERRORS = frozenset((5, 32))
_REPLACE_ATTEMPTS = 3
_RETRY_DELAY_SECONDS = 0.01


def _absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _is_link_or_reparse(path: Path) -> bool:
    try:
        status = os.lstat(path)
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(getattr(status, "st_mode", 0)):
        return True
    if getattr(status, "st_file_attributes", 0) & _REPARSE_POINT:
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def validate_managed_path(managed_root: Path, path: Path) -> Path:
    """Return an absolute managed path after rejecting escapes and links."""
    root = _absolute(managed_root)
    target = _absolute(path)
    try:
        inside_root = os.path.commonpath((root, target)) == os.fspath(root)
    except ValueError:
        inside_root = False
    if not inside_root:
        raise ValueError(f"path escapes managed root {root}: {target}")

    relative_parts = target.relative_to(root).parts
    descendants = (
        root.joinpath(*relative_parts[:index])
        for index in range(1, len(relative_parts) + 1)
    )
    for candidate in (root, *descendants):
        if _is_link_or_reparse(candidate):
            raise ValueError(
                "managed path component must not be a symlink, junction, "
                f"or reparse point: {candidate}"
            )
    return target


def _replace_with_retry(source: Path, destination: Path) -> None:
    for attempt in range(_REPLACE_ATTEMPTS):
        try:
            os.replace(source, destination)
            return
        except PermissionError as error:
            if (
                getattr(error, "winerror", None) not in _RETRYABLE_WINDOWS_ERRORS
                or attempt == _REPLACE_ATTEMPTS - 1
            ):
                raise
            time.sleep(_RETRY_DELAY_SECONDS)


def atomic_write(
    managed_root: Path,
    path: Path,
    data: bytes,
    *,
    mode: int | None = None,
) -> None:
    """Write bytes through a same-directory temporary file and replace."""
    target = validate_managed_path(managed_root, path)
    target_mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else mode
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.stem}.",
        suffix=".tmp",
        dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            if target_mode is not None:
                os.chmod(temporary, target_mode)
            os.fsync(stream.fileno())
        _replace_with_retry(temporary, target)
    except BaseException:
        try:
            os.chmod(temporary, stat.S_IWRITE)
        except OSError:
            pass
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise
