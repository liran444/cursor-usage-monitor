"""System tray icon, polling, and widget toggle."""

from __future__ import annotations

import logging
import threading
import webbrowser
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QAction, QCursor
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from cursor_usage_app.app.tray_ring import render_tray_ring_icon, tray_ring_display_from_envelope
from cursor_usage_app.app.tray_tooltip import build_tray_tooltip
from cursor_usage_app.app.widget.fetch_worker import load_cache, start_fetch_in_thread
from cursor_usage_app.app.widget.usage_window import UsageWindow, apply_shell_icon
from cursor_usage_app.auth.browser_import import BrowserImportError, import_session_token_from_browsers
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.cache.usage_cache import default_cache_path
from cursor_usage_app.app.usage_notifier import UsageNotifier
from cursor_usage_app.settings.app_settings import load_app_settings

_LOGGER = logging.getLogger(__name__)

POLL_INTERVAL_MS = 60 * 1000
_DASHBOARD_URL = "https://cursor.com/dashboard/usage"


class TrayController(QObject):
    _silent_import_finished = Signal()
    def __init__(
        self,
        store: SessionStore | None = None,
        cache_path: Path | None = None,
        poll_interval_ms: int = POLL_INTERVAL_MS,
    ) -> None:
        super().__init__()
        self._store = store or SessionStore()
        self._cache_path = cache_path or default_cache_path()
        self._settings = load_app_settings()
        self._usage_notifier = UsageNotifier()
        self._window = UsageWindow(
            cache_path=self._cache_path,
            store=self._store,
            auto_center=False,
        )
        self._window.hide()
        self._widget_positioned = False
        self._fetch_runner = None

        self._silent_import_finished.connect(self.refresh)
        self._window.widget().tray_settings_changed.connect(self._on_tray_settings_changed)

        self._tray = QSystemTrayIcon(self)
        self._tray.setToolTip("Cursor Usage")
        self._build_menu()
        self._tray.activated.connect(self._on_tray_activated)

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(poll_interval_ms)
        self._poll_timer.timeout.connect(self.refresh)

        self._apply_cache_to_tray(load_cache(self._cache_path))
        self._bootstrap_session()

    def show_tray(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            _LOGGER.warning("System tray is not available on this platform.")
        self._tray.show()
        self._poll_timer.start()

    def _build_menu(self) -> None:
        menu = QMenu()

        open_action = QAction("Open", menu)
        open_action.triggered.connect(self._open_widget)
        menu.addAction(open_action)

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._open_settings)
        menu.addAction(settings_action)

        menu.addSeparator()

        refresh_action = QAction("Refresh", menu)
        refresh_action.triggered.connect(self.refresh)
        menu.addAction(refresh_action)

        import_action = QAction("Import session", menu)
        import_action.triggered.connect(self._import_session_interactive)
        menu.addAction(import_action)

        token_action = QAction("Set token", menu)
        token_action.triggered.connect(self._open_set_token)
        menu.addAction(token_action)

        dashboard_action = QAction("Dashboard", menu)
        dashboard_action.triggered.connect(lambda: webbrowser.open(_DASHBOARD_URL))
        menu.addAction(dashboard_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(quit_action)

        self._tray.setContextMenu(menu)

    def _bootstrap_session(self) -> None:
        if self._store.get_token() is None:
            self._start_silent_import_then_fetch()
        else:
            QTimer.singleShot(0, self.refresh)

    def _start_silent_import_then_fetch(self) -> None:
        def task() -> None:
            self._try_silent_browser_import()
            self._silent_import_finished.emit()

        threading.Thread(
            target=task,
            name="cursor-usage-silent-import",
            daemon=True,
        ).start()

    def _try_silent_browser_import(self) -> bool:
        try:
            result = import_session_token_from_browsers()
            self._store.set_token(result.token)
            return True
        except BrowserImportError:
            return False
        except Exception as exc:
            _LOGGER.debug("Silent import failed: %s", exc.__class__.__name__)
            return False

    def _import_session_interactive(self) -> None:
        try:
            result = import_session_token_from_browsers()
            self._store.set_token(result.token)
            self._tray.showMessage(
                "Cursor Usage",
                f"Imported session from {result.source}.",
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )
            self.refresh()
        except BrowserImportError as exc:
            self._tray.showMessage(
                "Cursor Usage",
                str(exc),
                QSystemTrayIcon.MessageIcon.Warning,
                6000,
            )

    def _open_widget(self) -> None:
        self._reveal_widget()

    def _open_settings(self) -> None:
        menu_pos = QCursor.pos()
        QTimer.singleShot(
            0,
            lambda: self._window.widget().open_settings_panel(at_global=menu_pos),
        )

    def _open_set_token(self) -> None:
        self._reveal_widget()
        self._window.widget().show_token_editor()

    def _reveal_widget(self) -> None:
        if not self._widget_positioned:
            self._window.position_near_cursor()
            self._widget_positioned = True
        self._window.widget().reload_from_cache()
        self._settings = load_app_settings()
        self._apply_cache_to_tray(load_cache(self._cache_path))
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()

    def refresh(self) -> None:
        self._fetch_runner = start_fetch_in_thread(
            self,
            cache_path=self._cache_path,
            store=self._store,
            on_finished=self._on_fetch_finished,
        )

    def _on_fetch_finished(self, _exit_code: int) -> None:
        envelope = load_cache(self._cache_path)
        self._apply_cache_to_tray(envelope)
        self._window.widget().reload_from_cache()

    def _on_tray_settings_changed(self) -> None:
        self._settings = load_app_settings()
        self._apply_cache_to_tray(load_cache(self._cache_path))

    def _apply_cache_to_tray(self, envelope) -> None:
        mode = self._settings.tray_display_mode
        display = tray_ring_display_from_envelope(envelope, mode=mode)
        shell_icon = render_tray_ring_icon(display)
        self._tray.setIcon(shell_icon)
        apply_shell_icon(shell_icon, window=self._window)
        self._tray.setToolTip(build_tray_tooltip(envelope, mode=mode))
        self._usage_notifier.process_envelope(envelope, self._show_usage_notification)

    def _show_usage_notification(self, title: str, body: str) -> None:
        self._tray.showMessage(
            title,
            body,
            QSystemTrayIcon.MessageIcon.Information,
            5000,
        )

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_widget()

    def handle_peer_message(self, payload: bytes) -> None:
        if payload.strip() == b"toggle":
            self._toggle_widget()

    def _toggle_widget(self) -> None:
        if self._window.isVisible():
            self._window.hide()
            return
        if not self._widget_positioned:
            self._window.position_near_cursor()
            self._widget_positioned = True
        self._window.widget().reload_from_cache()
        self._settings = load_app_settings()
        self._apply_cache_to_tray(load_cache(self._cache_path))
        self._window.show()
        self._window.raise_()
        self._window.activateWindow()
