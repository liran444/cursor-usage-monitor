from pathlib import Path

import pytest

from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.auth.token_normalize import TokenNormalizeError


def test_set_and_get_via_keyring(fake_keyring, tmp_path: Path) -> None:
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::secret")
    assert store.get_token() == "user_01::secret"
    assert fake_keyring.get_password("cursor-usage-app", "WorkosCursorSessionToken") == "user_01::secret"


def test_fallback_when_keyring_get_fails(fake_keyring, tmp_path: Path) -> None:
    fallback = tmp_path / "session_token"
    fallback.write_text("from-file", encoding="utf-8")
    fake_keyring.raise_on_get = True
    store = SessionStore(fallback_path=fallback)
    assert store.get_token() == "from-file"


def test_clear_removes_keyring_and_file(fake_keyring, tmp_path: Path) -> None:
    fallback = tmp_path / "session_token"
    store = SessionStore(fallback_path=fallback)
    store.set_token("user_01::secret")
    assert fallback.is_file()
    store.clear()
    assert store.get_token() is None
    assert not fallback.is_file()


def test_prefers_full_token_in_file_over_stale_keyring(fake_keyring, tmp_path: Path) -> None:
    fallback = tmp_path / "session_token"
    full = "user_01::" + ("x" * 400)
    fallback.write_text(full, encoding="utf-8")
    fake_keyring.set_password("cursor-usage-app", "WorkosCursorSessionToken", "stale-short-keyring-value")
    store = SessionStore(fallback_path=fallback)
    assert store.get_token() == full
    assert fake_keyring.get_password("cursor-usage-app", "WorkosCursorSessionToken") == full


def test_set_rejects_invalid_token(fake_keyring, tmp_path: Path) -> None:
    store = SessionStore(fallback_path=tmp_path / "session_token")
    with pytest.raises(TokenNormalizeError):
        store.set_token("WorkosCursorSessionToken=bad")
