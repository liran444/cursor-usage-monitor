from pathlib import Path

import keyring.errors
import pytest

from fixture_loader import FIXTURES_DIR


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


class FakeKeyring:
    def __init__(self) -> None:
        self._passwords: dict[tuple[str, str], str] = {}
        self.raise_on_get = False
        self.raise_on_set = False

    def get_password(self, service: str, username: str) -> str | None:
        if self.raise_on_get:
            raise keyring.errors.KeyringError("keyring unavailable")
        return self._passwords.get((service, username))

    def set_password(self, service: str, username: str, password: str) -> None:
        if self.raise_on_set:
            raise keyring.errors.KeyringError("keyring unavailable")
        self._passwords[(service, username)] = password

    def delete_password(self, service: str, username: str) -> None:
        self._passwords.pop((service, username), None)


@pytest.fixture
def fake_keyring(monkeypatch) -> FakeKeyring:
    backend = FakeKeyring()
    monkeypatch.setattr("cursor_usage_app.auth.session_store.keyring.get_password", backend.get_password)
    monkeypatch.setattr("cursor_usage_app.auth.session_store.keyring.set_password", backend.set_password)
    monkeypatch.setattr(
        "cursor_usage_app.auth.session_store.keyring.delete_password",
        backend.delete_password,
    )
    return backend
