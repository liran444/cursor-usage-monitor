"""Background fetch for widget refresh."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.cache.usage_cache import default_cache_path, read_cache_envelope
from cursor_usage_app.fetch_service import run_fetch


class FetchWorker(QObject):
    finished = Signal(int)

    def __init__(
        self,
        cache_path: Path | None = None,
        store: SessionStore | None = None,
    ) -> None:
        super().__init__()
        self._cache_path = cache_path or default_cache_path()
        self._store = store

    def run(self) -> None:
        code = run_fetch(cache_path=self._cache_path, store=self._store)
        self.finished.emit(code)


def start_fetch_in_thread(
    parent: QObject,
    cache_path: Path | None = None,
    store: SessionStore | None = None,
    on_finished: Callable[[int], None] | None = None,
) -> QThread:
    thread = QThread(parent)
    worker = FetchWorker(cache_path=cache_path, store=store)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    if on_finished is not None:
        worker.finished.connect(on_finished)
    thread.start()
    return thread


def load_cache(cache_path: Path | None = None):
    path = cache_path or default_cache_path()
    return read_cache_envelope(path)
