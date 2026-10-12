"""CLI handlers for cursor-usage token subcommands."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cursor_usage_app.api.client import UsageSummaryClient, UsageSummaryHttpError
from cursor_usage_app.api.usage_summary import fetch_usage_snapshot
from cursor_usage_app.auth.browser_import import BrowserImportError, import_session_token_from_browsers
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.auth.token_normalize import TokenNormalizeError, normalize_session_token


def cmd_token_set(args: argparse.Namespace, store: SessionStore | None = None) -> int:
    session_store = store or SessionStore()
    try:
        raw = _read_token_input(args)
    except OSError as exc:
        print(f"Could not read token input: {exc}", file=sys.stderr)
        return 1

    try:
        session_store.set_token(raw)
    except TokenNormalizeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print("Session token saved.")
    return 0


def cmd_token_clear(_args: argparse.Namespace, store: SessionStore | None = None) -> int:
    session_store = store or SessionStore()
    session_store.clear()
    print("Session token cleared.")
    return 0


def cmd_token_test(_args: argparse.Namespace, store: SessionStore | None = None) -> int:
    session_store = store or SessionStore()
    token = session_store.get_token()
    if token is None:
        print(
            "No session token stored. Use 'cursor-usage token set' or 'cursor-usage token import'.",
            file=sys.stderr,
        )
        return 1

    client = UsageSummaryClient()
    try:
        fetch_usage_snapshot(token, client=client)
    except UsageSummaryHttpError as exc:
        print(f"Session test failed: {exc.message}", file=sys.stderr)
        return 1

    print("Session token is valid.")
    return 0


def cmd_token_import(args: argparse.Namespace, store: SessionStore | None = None) -> int:
    session_store = store or SessionStore()
    try:
        if getattr(args, "clipboard", False):
            raw = _read_clipboard()
        else:
            result = import_session_token_from_browsers()
            raw = result.token
            print(f"Imported session from {result.source}.")
    except BrowserImportError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Clipboard read failed: {exc}", file=sys.stderr)
        return 1

    try:
        session_store.set_token(raw)
    except TokenNormalizeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if not getattr(args, "clipboard", False):
        print("Session token saved.")
    else:
        print("Session token imported from clipboard and saved.")
    return 0


def _read_token_input(args: argparse.Namespace) -> str:
    if args.file is not None:
        return Path(args.file).read_text(encoding="utf-8")
    if getattr(args, "clipboard", False):
        return _read_clipboard()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise OSError("No token provided. Pipe token on stdin, or use --file / --clipboard.")


def _read_clipboard() -> str:
    text = _try_qt_clipboard()
    if text is not None:
        return text
    try:
        import pyperclip
    except ImportError:
        raise OSError(
            "Clipboard support requires pyperclip or PySide6. Install pyperclip or paste via stdin/--file."
        ) from None
    content = pyperclip.paste()
    if content is None or str(content).strip() == "":
        raise OSError("Clipboard is empty.")
    return str(content)


def _try_qt_clipboard() -> str | None:
    try:
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return None

    app = QGuiApplication.instance()
    if app is None:
        app = QApplication([])
    clipboard = app.clipboard()
    if clipboard is None:
        return None
    text = clipboard.text()
    if text is None or text.strip() == "":
        raise OSError("Clipboard is empty.")
    return text


def add_token_subparser(sub: argparse._SubParsersAction) -> None:
    token = sub.add_parser("token", help="Manage session token")
    token_sub = token.add_subparsers(dest="token_command")

    set_parser = token_sub.add_parser("set", help="Save session token")
    set_parser.add_argument("--file", type=str, help="Read token from file")
    set_parser.add_argument("--clipboard", action="store_true", help="Read token from clipboard")
    set_parser.set_defaults(handler=cmd_token_set)

    token_sub.add_parser("clear", help="Remove stored session token").set_defaults(
        handler=cmd_token_clear
    )

    token_sub.add_parser("test", help="Verify stored token against API").set_defaults(
        handler=cmd_token_test
    )

    import_parser = token_sub.add_parser("import", help="Import from browser or clipboard")
    import_parser.add_argument(
        "--clipboard",
        action="store_true",
        help="Import token value from clipboard instead of browsers",
    )
    import_parser.set_defaults(handler=cmd_token_import)
