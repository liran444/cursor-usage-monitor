"""CLI entry: cursor-usage."""

from __future__ import annotations

import argparse
import sys

from cursor_usage_app.fetch_service import run_fetch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cursor-usage")
    sub = parser.add_subparsers(dest="command")

    fetch_parser = sub.add_parser("fetch", help="Fetch usage-summary and update cache")
    fetch_parser.set_defaults(handler=_cmd_fetch)

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)


def _cmd_fetch(_args: argparse.Namespace) -> int:
    return run_fetch()


if __name__ == "__main__":
    sys.exit(main())
