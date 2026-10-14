from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PySide6.QtWidgets import QApplication

from cursor_usage_app.app.tray_controller import POLL_INTERVAL_MS, TrayController
from cursor_usage_app.auth.browser_import import BrowserImportResult
from cursor_usage_app.auth.session_store import SessionStore


@pytest.fixture
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_poll_interval_default_is_fifteen_minutes() -> None:
    assert POLL_INTERVAL_MS == 60 * 1000


def test_first_launch_attempts_import_when_store_empty(
    qapp,
    fake_keyring,
    tmp_path: Path,
    monkeypatch,
) -> None:
    import_called = {"count": 0}

    def fake_import() -> BrowserImportResult:
        import_called["count"] += 1
        return BrowserImportResult(token="user_01::imported", source="test")

    fetch_calls: list[int] = []

    def fake_start_fetch(parent, cache_path=None, store=None, on_finished=None):
        fetch_calls.append(1)
        if on_finished is not None:
            on_finished(0)
        return MagicMock()

    monkeypatch.setattr(
        "cursor_usage_app.app.tray_controller.import_session_token_from_browsers",
        fake_import,
    )
    monkeypatch.setattr(
        "cursor_usage_app.app.tray_controller.start_fetch_in_thread",
        fake_start_fetch,
    )

    cache_path = tmp_path / "usage_cache.json"
    store = SessionStore(fallback_path=tmp_path / "session_token")
    monkeypatch.setattr(store, "get_token", lambda: None)
    controller = TrayController(store=store, cache_path=cache_path, poll_interval_ms=60_000)
    controller.show_tray()

    for _ in range(200):
        qapp.processEvents()
        if import_called["count"] >= 1 and len(fetch_calls) >= 1:
            break

    assert import_called["count"] == 1
    assert len(fetch_calls) >= 1
    assert controller._poll_timer.interval() == 60_000

    controller._tray.hide()


def test_startup_opens_widget(qapp, tmp_path: Path) -> None:
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::test")

    controller = TrayController(
        store=store,
        cache_path=tmp_path / "usage_cache.json",
        poll_interval_ms=60_000,
    )
    assert controller._window.isVisible() is False
    controller.show_tray()
    for _ in range(50):
        qapp.processEvents()

    assert controller._window.isVisible() is True
    controller._tray.hide()
