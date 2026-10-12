"""In-app session token dialog."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from cursor_usage_app.api.client import UsageSummaryClient, UsageSummaryHttpError
from cursor_usage_app.api.usage_summary import fetch_usage_snapshot
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.auth.token_normalize import TokenNormalizeError, normalize_session_token


class SetTokenDialog(QDialog):
    def __init__(
        self,
        parent=None,
        store: SessionStore | None = None,
    ) -> None:
        super().__init__(parent)
        self._store = store or SessionStore()
        self.setWindowTitle("Set session token")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        hint = QLabel(
            "Paste the WorkosCursorSessionToken value from browser DevTools "
            "(Application → Cookies → cursor.com). It is stored locally and never logged."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._input = QLineEdit()
        self._input.setEchoMode(QLineEdit.EchoMode.Password)
        self._input.setPlaceholderText("Session token")
        layout.addWidget(self._input)

        buttons = QDialogButtonBox()
        self._test_button = QPushButton("Test && save")
        self._save_button = QPushButton("Save")
        self._cancel_button = QPushButton("Cancel")
        buttons.addButton(self._test_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self._save_button, QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(self._cancel_button, QDialogButtonBox.ButtonRole.RejectRole)
        layout.addWidget(buttons)

        self._test_button.clicked.connect(self._on_test_and_save)
        self._save_button.clicked.connect(self._on_save)
        self._cancel_button.clicked.connect(self.reject)

    def _on_save(self) -> None:
        if not self._persist_token():
            return
        self.accept()

    def _on_test_and_save(self) -> None:
        raw = self._input.text()
        if raw.strip() == "":
            QMessageBox.warning(self, "Set token", "Token cannot be empty.")
            return
        try:
            normalized = normalize_session_token(raw)
        except TokenNormalizeError as exc:
            QMessageBox.warning(self, "Set token", str(exc))
            return

        client = UsageSummaryClient()
        try:
            fetch_usage_snapshot(normalized, client=client)
        except UsageSummaryHttpError as exc:
            QMessageBox.warning(self, "Session test failed", exc.message)
            return

        if not self._persist_token():
            return
        QMessageBox.information(self, "Set token", "Session token is valid and saved.")
        self.accept()

    def _persist_token(self) -> bool:
        raw = self._input.text()
        if raw.strip() == "":
            QMessageBox.warning(self, "Set token", "Token cannot be empty.")
            return False
        try:
            self._store.set_token(raw)
        except TokenNormalizeError as exc:
            QMessageBox.warning(self, "Set token", str(exc))
            return False
        return True
