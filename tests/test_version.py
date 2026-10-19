"""Project version resolution."""

import re
from pathlib import Path

from cursor_usage_app._version import resolve_version


def test_resolve_version_from_repo_root_matches_pyproject() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
    assert match is not None
    assert resolve_version(repo_root) == match.group(1)
