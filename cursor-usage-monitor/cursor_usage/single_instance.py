"""Prevent multiple tray instances."""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path


def _try_flock(handle) -> bool:
    try:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except ImportError:
        return True
    except OSError:
        return False


def acquire(lock_file: Path) -> bool:
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_file.open("w")
    if not _try_flock(handle):
        handle.close()
        return False

    handle.write(str(os.getpid()))
    handle.flush()

    def _release() -> None:
        try:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        except ImportError:
            pass
        handle.close()
        try:
            lock_file.unlink(missing_ok=True)
        except OSError:
            pass

    atexit.register(_release)
    return True


def ensure_single_instance(lock_file: Path) -> None:
    if not acquire(lock_file):
        print(
            "Another tray instance is already running (check hidden tray icons on GNOME).",
            file=sys.stderr,
        )
        sys.exit(0)
