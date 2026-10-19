"""Resolve package version (pyproject.toml is the single source of truth)."""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

_PACKAGE_NAME = "cursor-usage-app"


def _version_from_pyproject(repo_root: Path) -> str | None:
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.is_file():
        return None
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match is None:
        return None
    return match.group(1)


def resolve_version(repo_root: Path | None = None) -> str:
    """Return the project version for runtime, dev trees, and build scripts."""
    if repo_root is not None:
        from_pyproject = _version_from_pyproject(repo_root)
        if from_pyproject is not None:
            return from_pyproject

    try:
        return version(_PACKAGE_NAME)
    except PackageNotFoundError:
        pass

    from_pyproject = _version_from_pyproject(Path(__file__).resolve().parents[2])
    if from_pyproject is not None:
        return from_pyproject

    return "0.0.0"
