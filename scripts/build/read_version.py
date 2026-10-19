"""Print project version for shell/build scripts (reads pyproject via package helper)."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "src"))

from cursor_usage_app._version import resolve_version  # noqa: E402


def read_version(repo_root: Path | None = None) -> str:
    return resolve_version(repo_root or _REPO_ROOT)


if __name__ == "__main__":
    print(read_version())
