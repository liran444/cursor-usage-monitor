"""Read session tokens reliably across platforms."""

from __future__ import annotations

import getpass
import shutil
import subprocess
import sys
from pathlib import Path


def read_clipboard() -> str | None:
    if sys.platform == "win32":
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            value = result.stdout.strip()
            return value or None
        except (OSError, subprocess.SubprocessError):
            return None

    if sys.platform == "darwin":
        if not shutil.which("pbpaste"):
            return None
        try:
            result = subprocess.run(
                ["pbpaste"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            value = result.stdout.strip()
            return value or None
        except (OSError, subprocess.SubprocessError):
            return None

    for cmd in (["xclip", "-selection", "clipboard", "-o"], ["xsel", "--clipboard", "--output"]):
        if not shutil.which(cmd[0]):
            continue
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            )
            value = result.stdout.strip()
            return value or None
        except (OSError, subprocess.SubprocessError):
            continue
    return None


def read_token_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8").strip()


def read_token(
    *,
    hidden: bool = False,
    from_stdin: bool = False,
    from_clipboard: bool = False,
    file_path: str | None = None,
    manual: bool = False,
) -> str:
    if file_path is not None:
        return read_token_file(file_path)

    if from_stdin:
        if sys.stdin.isatty():
            print(
                "Paste token on stdin, then end input (PowerShell: Ctrl+Z Enter; bash: Ctrl+D).",
                file=sys.stderr,
            )
        return sys.stdin.read().strip()

    if from_clipboard:
        value = read_clipboard()
        if value is None:
            raise RuntimeError("Could not read clipboard on this system.")
        return value

    if hidden:
        try:
            return getpass.getpass("Token: ")
        except (EOFError, KeyboardInterrupt):
            raise

    if manual:
        print("Paste the full cookie value, then press Enter.")
        try:
            return input("Token: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise

    # Default: clipboard flow (most reliable in IDE terminals on Windows).
    print("1. Copy WorkosCursorSessionToken from browser DevTools (cursor.com cookies).")
    print("2. Press Enter here to load the token from your clipboard.")
    print("   Other options: --file token.txt | --stdin | --manual")
    try:
        input("Press Enter when the token is copied to clipboard... ")
    except (EOFError, KeyboardInterrupt):
        raise

    value = read_clipboard()
    if value is None:
        raise RuntimeError(
            "Could not read clipboard. Save the token to token.txt and run: "
            "cursor-usage token set --file token.txt"
        )
    return value
