"""CLI entry: fetch, tray, token."""

from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser

from cursor_usage import keyring_store
from cursor_usage.keyring_store import TokenStorageError
from cursor_usage.fetch import run_fetch
from cursor_usage.paths import load_settings, save_settings
from cursor_usage.token_input import read_token


def _cmd_fetch(args: argparse.Namespace) -> int:
    return run_fetch(verbose=getattr(args, "verbose", False))


def _cmd_token_set(args: argparse.Namespace) -> int:
    try:
        token = read_token(
            hidden=args.hidden,
            from_stdin=args.stdin,
            from_clipboard=args.clipboard,
            file_path=args.file,
            manual=args.manual,
        )
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if token == "":
        print("Token cannot be empty.", file=sys.stderr)
        return 1
    try:
        storage = keyring_store.set_token(token)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print("Try: cursor-usage token set --file token.txt", file=sys.stderr)
        return 1
    except TokenStorageError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if storage == "keyring":
        print(f"Token saved to OS keyring ({len(token)} characters).")
    else:
        print(f"Token saved to config file ({len(token)} characters).")
        print("Windows Credential Manager was unavailable; using local config file instead.")
    return 0


def _cmd_token_test(args: argparse.Namespace) -> int:
    code = run_fetch(verbose=getattr(args, "verbose", False))
    if code == 0:
        print("Fetch succeeded.")
    else:
        if not getattr(args, "verbose", False):
            print("Fetch failed. Check token or network.", file=sys.stderr)
            print("Run: cursor-usage token test --verbose", file=sys.stderr)
    return code


def _cmd_token_clear(_args: argparse.Namespace) -> int:
    keyring_store.clear_token()
    print("Token removed from keyring.")
    return 0


def _cmd_config_show(_args: argparse.Namespace) -> int:
    settings = load_settings()
    for key, value in settings.items():
        print(f"{key}={value}")
    return 0


def _cmd_tray(args: argparse.Namespace) -> int:
    from ui.tray.app import run_tray

    if getattr(args, "background", False):
        return _spawn_tray_background()

    run_tray()
    return 0


def _spawn_tray_background() -> int:
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "tray"]
    else:
        cmd = [sys.executable, "-m", "cursor_usage.__main__", "tray"]

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
        close_fds=True,
    )
    print("Tray started in the background.")
    return 0


def _cmd_open_dashboard(_args: argparse.Namespace) -> int:
    webbrowser.open("https://cursor.com/dashboard/usage")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cursor-usage")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Fetch usage-summary into cache")
    fetch.add_argument(
        "--verbose",
        action="store_true",
        help="Print HTTP status and error details",
    )
    tray = sub.add_parser("tray", help="Run system tray UI")
    tray.add_argument(
        "--background",
        action="store_true",
        help="Start tray detached so the terminal returns immediately (Windows-friendly)",
    )
    sub.add_parser("open-dashboard", help="Open Cursor usage dashboard in browser")

    token = sub.add_parser("token", help="Session token management")
    token_sub = token.add_subparsers(dest="token_cmd", required=True)
    token_set = token_sub.add_parser("set", help="Save token to keyring")
    token_set.add_argument(
        "--file",
        metavar="PATH",
        help="Read token from a text file (recommended if paste fails)",
    )
    token_set.add_argument(
        "--clipboard",
        action="store_true",
        help="Read token from clipboard (default: press Enter after copying)",
    )
    token_set.add_argument(
        "--stdin",
        action="store_true",
        help="Read full token from stdin",
    )
    token_set.add_argument(
        "--manual",
        action="store_true",
        help="Type or paste token at a prompt (often unreliable in IDE terminals)",
    )
    token_set.add_argument(
        "--hidden",
        action="store_true",
        help="Hide input while typing (may break paste on Windows)",
    )
    token_test = token_sub.add_parser("test", help="Run fetch to verify token")
    token_test.add_argument(
        "--verbose",
        action="store_true",
        help="Print HTTP status and error details",
    )
    token_sub.add_parser("clear", help="Remove token from keyring")

    config = sub.add_parser("config", help="Settings")
    config_sub = config.add_subparsers(dest="config_cmd", required=True)
    config_sub.add_parser("show", help="Show settings")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "fetch":
        sys.exit(_cmd_fetch(args))
    if args.command == "tray":
        sys.exit(_cmd_tray(args))
    if args.command == "open-dashboard":
        sys.exit(_cmd_open_dashboard(args))
    if args.command == "token":
        if args.token_cmd == "set":
            sys.exit(_cmd_token_set(args))
        if args.token_cmd == "test":
            sys.exit(_cmd_token_test(args))
        if args.token_cmd == "clear":
            sys.exit(_cmd_token_clear(args))
    if args.command == "config":
        if args.config_cmd == "show":
            sys.exit(_cmd_config_show(args))

    parser.print_help()
    sys.exit(2)


if __name__ == "__main__":
    main()
