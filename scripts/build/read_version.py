"""Read project version from pyproject.toml (no TOML dependency)."""

from __future__ import annotations

import re
from pathlib import Path


def read_version(repo_root: Path | None = None) -> str:
    root = repo_root or Path(__file__).resolve().parents[2]
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if match is None:
        return "0.0.0"
    return match.group(1)


if __name__ == "__main__":
    print(read_version())
