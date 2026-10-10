from unittest.mock import patch

import keyring.errors

from cursor_usage.keyring_store import clear_token, get_token, set_token

SAMPLE_TOKEN = (
    "user_01TESTUSER%3A%3A"
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJ0ZXN0In0."
    "signature"
)


def test_set_token_falls_back_to_file_on_keyring_error(tmp_path, monkeypatch):
    token_file = tmp_path / "session.token"
    monkeypatch.setattr("cursor_usage.keyring_store.token_path", lambda: token_file)

    with patch("cursor_usage.keyring_store.keyring.get_password", return_value=None):
        with patch("cursor_usage.keyring_store.keyring.set_password", side_effect=keyring.errors.KeyringError()):
            with patch(
                "cursor_usage.keyring_store.keyring.delete_password",
                side_effect=keyring.errors.PasswordDeleteError(),
            ):
                storage = set_token(SAMPLE_TOKEN)

    assert storage == "file"
    assert token_file.read_text(encoding="utf-8") == SAMPLE_TOKEN
    with patch("cursor_usage.keyring_store.keyring.get_password", return_value=None):
        assert get_token() == SAMPLE_TOKEN


def test_clear_token_removes_file(tmp_path, monkeypatch):
    token_file = tmp_path / "session.token"
    monkeypatch.setattr("cursor_usage.keyring_store.token_path", lambda: token_file)
    token_file.write_text(SAMPLE_TOKEN, encoding="utf-8")

    with patch("cursor_usage.keyring_store.keyring.delete_password", side_effect=keyring.errors.PasswordDeleteError()):
        clear_token()

    assert not token_file.exists()
