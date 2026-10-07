"""Secure storage for WorkosCursorSessionToken."""

from __future__ import annotations

import keyring
import keyring.errors

SERVICE_NAME = "cursor-usage-monitor"
TOKEN_USERNAME = "WorkosCursorSessionToken"


def get_token() -> str | None:
    try:
        value = keyring.get_password(SERVICE_NAME, TOKEN_USERNAME)
    except keyring.errors.KeyringError:
        return None
    if value is None or value.strip() == "":
        return None
    return value.strip()


def set_token(token: str) -> None:
    cleaned = token.strip()
    if cleaned == "":
        raise ValueError("Token cannot be empty")
    keyring.set_password(SERVICE_NAME, TOKEN_USERNAME, cleaned)


def clear_token() -> None:
    try:
        keyring.delete_password(SERVICE_NAME, TOKEN_USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass
