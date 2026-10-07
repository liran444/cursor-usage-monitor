"""CLI entry: fetch, tray, token."""

from __future__ import annotations

import argparse
import getpass
import sys
import webbrowser

from cursor_usage import keyring_store
from cursor_usage.fetch import run_fetch
from cursor_usage.paths import load_settings, save_settings


def _cmd_fetch(_args: argparse.Namespace) -> int:
    return run_fetch()


def _cmd_token_set(_args: argparse.Namespace) -> int:
    print("Paste WorkosCursorSessionToken from browser DevTools (cursor.com cookies).")
    print("Input is hidden.")
    try:
        token = getpass.getpass("Token: ")
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.", file=sys.stderr)
        return 1
    try:
        keyring_store.set_token(token)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print("Token saved to OS keyring.")
    return 0


def _cmd_token_test(_args: argparse.Namespace) -> int:
    code = run_fetch()
    if code == 0:
        print("Fetch succeeded.")
    else:
        print("Fetch failed. Check token or network.", file=sys.stderr)
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


def _cmd_tray(_args: argparse.Namespace) -> int:
    from ui.tray.app import run_tray

    run_tray()
    return 0


def _cmd_open_dashboard(_args: argparse.Namespace) -> int:
    webbrowser.open("https://cursor.com/dashboard/usage")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cursor-usage")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("fetch", help="Fetch usage-summary into cache")
    sub.add_parser("tray", help="Run system tray UI")
    sub.add_parser("open-dashboard", help="Open Cursor usage dashboard in browser")

    token = sub.add_parser("token", help="Session token management")
    token_sub = token.add_subparsers(dest="token_cmd", required=True)
    token_sub.add_parser("set", help="Save token to keyring")
    token_sub.add_parser("test", help="Run fetch to verify token")
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
