"""Import WorkosCursorSessionToken from installed browsers."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Protocol

from cursor_usage_app.api.client import SESSION_COOKIE_NAME

_LOGGER = logging.getLogger(__name__)

_CURSOR_DOMAIN_SUFFIXES = (".cursor.com", "cursor.com")


class BrowserImportError(Exception):
    """Could not find a cursor.com session cookie in any browser."""


@dataclass(frozen=True)
class BrowserImportResult:
    token: str
    source: str


class _CookieLike(Protocol):
    name: str
    value: str
    domain: str


def import_session_token_from_browsers() -> BrowserImportResult:
    """
    Scan common browsers for WorkosCursorSessionToken on cursor.com.

    Tries rookiepy first, then browser-cookie3.
    """
    token = _try_rookiepy()
    if token is not None:
        return token

    token = _try_browser_cookie3()
    if token is not None:
        return token

    raise BrowserImportError(
        "No WorkosCursorSessionToken found. Log in at cursor.com in Chrome, Edge, "
        "Brave, or Firefox, or set the token manually."
    )


def _try_rookiepy() -> BrowserImportResult | None:
    try:
        import rookiepy
    except ImportError:
        return None

    browsers: list[tuple[str, Callable[[], list[_CookieLike]]]] = [
        ("chrome", rookiepy.chrome),
        ("edge", rookiepy.edge),
        ("brave", rookiepy.brave),
        ("firefox", rookiepy.firefox),
    ]
    last_appbound: str | None = None
    for label, loader in browsers:
        try:
            cookies = loader()
        except Exception as exc:
            if _is_chromium_appbound_error(exc):
                last_appbound = label
            _LOGGER.debug("rookiepy %s failed: %s", label, exc.__class__.__name__)
            continue
        match = _find_session_cookie(cookies)
        if match is not None:
            return BrowserImportResult(token=match, source=f"rookiepy:{label}")
    if last_appbound is not None:
        raise BrowserImportError(_appbound_help_message(last_appbound))
    return None


def _try_browser_cookie3() -> BrowserImportResult | None:
    try:
        import browser_cookie3
    except ImportError:
        return None

    loaders: list[tuple[str, Callable[[], object]]] = [
        ("chrome", browser_cookie3.chrome),
        ("edge", browser_cookie3.edge),
        ("brave", browser_cookie3.brave),
        ("firefox", browser_cookie3.firefox),
    ]
    for label, loader in loaders:
        try:
            jar = loader()
        except Exception as exc:
            _LOGGER.debug("browser_cookie3 %s failed: %s", label, exc.__class__.__name__)
            continue
        match = _find_session_in_jar(jar)
        if match is not None:
            return BrowserImportResult(token=match, source=f"browser_cookie3:{label}")
    return None


def _find_session_cookie(cookies: list[_CookieLike]) -> str | None:
    for cookie in cookies:
        if cookie.name != SESSION_COOKIE_NAME:
            continue
        if not _domain_matches(cookie.domain):
            continue
        value = (cookie.value or "").strip()
        if value != "":
            return value
    return None


def _find_session_in_jar(jar: object) -> str | None:
    if not hasattr(jar, "__iter__"):
        return None
    for cookie in jar:
        name = getattr(cookie, "name", None)
        if name != SESSION_COOKIE_NAME:
            continue
        domain = getattr(cookie, "domain", "") or ""
        if not _domain_matches(domain):
            continue
        value = getattr(cookie, "value", "") or ""
        value = value.strip()
        if value != "":
            return value
    return None


def _is_chromium_appbound_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return "appbound" in text or "running as admin" in text


def is_retryable_import_error(exc: BrowserImportError) -> bool:
    """Cookie not present yet (user still signing in). Decrypt failures are not retried."""
    text = str(exc).lower()
    if "appbound" in text or "decrypt" in text or "running as admin" in text:
        return False
    return True


def _appbound_help_message(browser_label: str) -> str:
    return (
        f"Could not decrypt {browser_label} cookies on this Windows build (Chromium app-bound "
        "encryption). Close the browser, run Import session from an elevated terminal, or use "
        "Set token with the WorkosCursorSessionToken value from DevTools."
    )


def _domain_matches(domain: str) -> bool:
    d = domain.lstrip(".").lower()
    for suffix in _CURSOR_DOMAIN_SUFFIXES:
        if d == suffix.lstrip(".") or d.endswith(suffix):
            return True
    return False
