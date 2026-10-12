import os

import pytest

from cursor_usage_app.app.widget.set_token_dialog import SetTokenDialog
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.auth.token_normalize import normalize_session_token

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_set_token_dialog_persists_via_session_store(qapp, tmp_path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    fallback = tmp_path / "session_token"
    store = SessionStore(fallback_path=fallback)
    dialog = SetTokenDialog(store=store)
    raw = "user_01abc::eyJhbGciOiJIUzI1NiJ9"
    dialog._input.setText(raw)
    assert dialog._persist_token() is True
    assert store.get_token() == normalize_session_token(raw)
