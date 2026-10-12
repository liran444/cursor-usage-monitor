"""Persist session token in OS keyring with local file fallback."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from platformdirs import user_config_dir

import keyring
import keyring.errors

from cursor_usage_app.auth.token_normalize import TokenNormalizeError, normalize_session_token

_LOGGER = logging.getLogger(__name__)

_KEYRING_SERVICE = "cursor-usage-app"
_KEYRING_USERNAME = "WorkosCursorSessionToken"
_CONFIG_DIR_NAME = "cursor-usage-app"
_FALLBACK_FILE_NAME = "session_token"


class SessionStore:
    """Read/write the WorkOS session token without ever logging its value."""

    def __init__(
        self,
        keyring_service: str = _KEYRING_SERVICE,
        keyring_username: str = _KEYRING_USERNAME,
        fallback_path: Path | None = None,
    ) -> None:
        self._keyring_service = keyring_service
        self._keyring_username = keyring_username
        self._fallback_path = fallback_path or _default_fallback_path()

    def get_token(self) -> str | None:
        keyring_token = self._get_from_keyring()
        file_token = self._get_from_fallback_file()
        best = _pick_best_token(keyring_token, file_token)
        if (
            best is not None
            and file_token is not None
            and best == file_token
            and keyring_token is not None
            and keyring_token != best
        ):
            self._set_keyring(best)
        return best

    def set_token(self, raw_token: str) -> None:
        token = normalize_session_token(raw_token)
        self._set_keyring(token)
        self._write_fallback_file(token)

    def clear(self) -> None:
        self._clear_keyring()
        self._clear_fallback_file()

    def has_token(self) -> bool:
        return self.get_token() is not None

    def _get_from_keyring(self) -> str | None:
        try:
            value = keyring.get_password(self._keyring_service, self._keyring_username)
        except Exception as exc:
            _LOGGER.debug("Keyring read failed: %s", exc.__class__.__name__)
            return None
        if value is None:
            return None
        stripped = value.strip()
        if stripped == "":
            return None
        return stripped

    def _set_keyring(self, token: str) -> None:
        try:
            keyring.set_password(self._keyring_service, self._keyring_username, token)
        except Exception as exc:
            _LOGGER.debug("Keyring write failed: %s", exc.__class__.__name__)

    def _clear_keyring(self) -> None:
        try:
            keyring.delete_password(self._keyring_service, self._keyring_username)
        except keyring.errors.PasswordDeleteError:
            pass
        except Exception as exc:
            _LOGGER.debug("Keyring delete failed: %s", exc.__class__.__name__)

    def _get_from_fallback_file(self) -> str | None:
        path = self._fallback_path
        if not path.is_file():
            return None
        try:
            text = path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            _LOGGER.debug("Fallback token read failed: %s", exc.__class__.__name__)
            return None
        if text == "":
            return None
        return text

    def _write_fallback_file(self, token: str) -> None:
        path = self._fallback_path
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(token, encoding="utf-8")
            _restrict_file_permissions(path)
        except OSError as exc:
            _LOGGER.debug("Fallback token write failed: %s", exc.__class__.__name__)

    def _clear_fallback_file(self) -> None:
        path = self._fallback_path
        try:
            if path.is_file():
                path.unlink()
        except OSError as exc:
            _LOGGER.debug("Fallback token delete failed: %s", exc.__class__.__name__)


def _pick_best_token(
    keyring_token: str | None,
    file_token: str | None,
) -> str | None:
    candidates = [t for t in (keyring_token, file_token) if t is not None and t.strip() != ""]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]
    return max(candidates, key=_token_quality_score)


def _token_quality_score(token: str) -> int:
    score = len(token)
    if "::" in token:
        score += 10_000
    return score


def _default_fallback_path() -> Path:
    base = Path(user_config_dir(_CONFIG_DIR_NAME, appauthor=False))
    return base / _FALLBACK_FILE_NAME


def _restrict_file_permissions(path: Path) -> None:
    if os.name != "posix":
        return
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
