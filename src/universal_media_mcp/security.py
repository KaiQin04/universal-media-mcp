"""Filesystem safety helpers."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable


class PathValidator:
    """Validate paths stay within allowed base directories."""

    def __init__(self, allowed_base_dirs: Iterable[Path]) -> None:
        bases = []
        for base_dir in allowed_base_dirs:
            bases.append(base_dir.expanduser().resolve())
        self._allowed_base_dirs = tuple(bases)

    @property
    def allowed_base_dirs(self) -> tuple[Path, ...]:
        """Allowed base directories."""

        return self._allowed_base_dirs

    def ensure_within_allowed(self, path: Path) -> Path:
        """Resolve path and ensure it is within one of allowed base dirs."""

        resolved = path.expanduser().resolve()
        for base_dir in self._allowed_base_dirs:
            if self._is_relative_to(resolved, base_dir):
                return resolved
        raise ValueError("Path is outside allowed directories.")

    def safe_unlink(self, path: Path) -> None:
        """Delete a file only if it is within allowed base dirs."""

        resolved = self.ensure_within_allowed(path)
        if resolved.is_file():
            resolved.unlink()

    @staticmethod
    def _is_relative_to(path: Path, base_dir: Path) -> bool:
        try:
            path.relative_to(base_dir)
        except ValueError:
            return False
        return True


_FILENAME_SAFE_RE = re.compile(r"[^A-Za-z0-9._ -]+")


def sanitize_filename(filename: str, max_length: int = 128) -> str:
    """Return a filesystem-safe filename without path separators."""

    cleaned = filename.replace("/", "_").replace("\\", "_")
    cleaned = _FILENAME_SAFE_RE.sub("_", cleaned).strip(" ._")
    if not cleaned:
        cleaned = "file"
    return cleaned[:max_length]
