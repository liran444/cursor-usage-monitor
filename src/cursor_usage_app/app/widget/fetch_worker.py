"""Background fetch for widget refresh."""

from __future__ import annotations

import threading
from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.cache.usage_cache import default_cache_path, read_cache_envelope
from cursor_usage_app.fetch_service import run_fetch


class _FetchRunner(QObject):
    """Run run_fetch on a worker thread; emit finished on the GUI thread."""

    finished = Signal(int)

    def __init__(
        self,
        cache_path: Path,
        store: SessionStore | None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._cache_path = cache_path
        self._store = store

    def start(self) -> None:
        def task() -> None:
            code = run_fetch(cache_path=self._cache_path, store=self._store)
            self.finished.emit(code)

        threading.Thread(
            target=task,
            name="cursor-usage-fetch",
            daemon=True,
        ).start()


def start_fetch_in_thread(
    parent: QObject,
    cache_path: Path | None = None,
    store: SessionStore | None = None,
    on_finished: Callable[[int], None] | None = None,
) -> _FetchRunner:
    path = cache_path or default_cache_path()
    runner = _FetchRunner(path, store, parent=parent)
    if on_finished is not None:
        runner.finished.connect(on_finished)
    runner.start()
    return runner


def load_cache(cache_path: Path | None = None):
    path = cache_path or default_cache_path()
    return read_cache_envelope(path)
