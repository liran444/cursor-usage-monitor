"""Secure storage for WorkosCursorSessionToken."""

from __future__ import annotations

import stat
import sys

import keyring
import keyring.errors

from cursor_usage.paths import token_path
from cursor_usage.token_normalize import normalize_token

SERVICE_NAME = "cursor-usage-monitor"
TOKEN_USERNAME = "session"


class TokenStorageError(RuntimeError):
    """Token could not be saved to any backend."""


def _read_token_file() -> str | None:
    path = token_path()
    if not path.is_file():
        return None
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if value == "":
        return None
    return value


def _write_token_file(token: str) -> None:
    path = token_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token, encoding="utf-8")
    if sys.platform != "win32":
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)


def _delete_token_file() -> None:
    path = token_path()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _normalize_or_raw(value: str) -> str:
    try:
        return normalize_token(value)
    except ValueError:
        return value.strip()


def get_token() -> str | None:
    try:
        value = keyring.get_password(SERVICE_NAME, TOKEN_USERNAME)
        if value is not None and value.strip() != "":
            return _normalize_or_raw(value)
    except keyring.errors.KeyringError:
        pass

    # Legacy keyring entry from older builds.
    try:
        value = keyring.get_password(SERVICE_NAME, "WorkosCursorSessionToken")
        if value is not None and value.strip() != "":
            return _normalize_or_raw(value)
    except keyring.errors.KeyringError:
        pass

    file_value = _read_token_file()
    if file_value is None:
        return None
    return _normalize_or_raw(file_value)


def set_token(token: str) -> str:
    cleaned = normalize_token(token)

    keyring_error: Exception | None = None
    try:
        try:
            keyring.delete_password(SERVICE_NAME, TOKEN_USERNAME)
        except keyring.errors.PasswordDeleteError:
            pass
        try:
            keyring.delete_password(SERVICE_NAME, "WorkosCursorSessionToken")
        except keyring.errors.PasswordDeleteError:
            pass
        keyring.set_password(SERVICE_NAME, TOKEN_USERNAME, cleaned)
        _delete_token_file()
        return "keyring"
    except keyring.errors.KeyringError as exc:
        keyring_error = exc

    try:
        _write_token_file(cleaned)
    except OSError as exc:
        if keyring_error is not None:
            raise TokenStorageError(
                "Could not save token to Windows Credential Manager or config file."
            ) from exc
        raise TokenStorageError("Could not save token to config file.") from exc

    return "file"


def clear_token() -> None:
    for username in (TOKEN_USERNAME, "WorkosCursorSessionToken"):
        try:
            keyring.delete_password(SERVICE_NAME, username)
        except keyring.errors.PasswordDeleteError:
            pass
        except keyring.errors.KeyringError:
            pass
    _delete_token_file()
