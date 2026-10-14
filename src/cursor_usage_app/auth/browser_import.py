"""Import WorkosCursorSessionToken from installed browsers."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from typing import Callable, Protocol

from cursor_usage_app.api.client import SESSION_COOKIE_NAME

_LOGGER = logging.getLogger(__name__)

_CURSOR_DOMAIN_SUFFIXES = (".cursor.com", "cursor.com")
_CURSOR_IMPORT_DOMAINS = ["cursor.com", ".cursor.com"]

# Order is stable; every installed browser we can probe is tried (no single-browser assumption).
_ROOKIEPY_BROWSER_NAMES: tuple[str, ...] = (
    "chrome",
    "chromium",
    "edge",
    "firefox",
    "brave",
    "arc",
    "opera",
    "opera_gx",
    "vivaldi",
    "librewolf",
)
_CHROMIUM_LOADER_LABELS = frozenset(
    {
        "chrome",
        "chromium",
        "edge",
        "brave",
        "arc",
        "opera",
        "opera_gx",
        "vivaldi",
        "load",
    }
)

_BC3_BROWSER_NAMES: tuple[str, ...] = (
    "chrome",
    "chromium",
    "edge",
    "firefox",
    "brave",
    "arc",
    "opera",
    "opera_gx",
    "vivaldi",
    "librewolf",
    "safari",
)


class BrowserImportError(Exception):
    """Could not find or read a cursor.com session cookie."""

    def __init__(self, message: str, *, decrypt_blocked: bool = False) -> None:
        super().__init__(message)
        self.decrypt_blocked = decrypt_blocked


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

    Tries rookiepy first, then browser-cookie3. Does not stop after decrypt errors
    in one library until both have been attempted.
    """
    decrypt_notes: list[str] = []

    token = _try_rookiepy(decrypt_notes)
    if token is not None:
        return token

    token = _try_browser_cookie3(decrypt_notes)
    if token is not None:
        return token

    if decrypt_notes:
        raise BrowserImportError(
            _decrypt_blocked_message(decrypt_notes),
            decrypt_blocked=True,
        )

    raise BrowserImportError(
        "No WorkosCursorSessionToken found. Log in at cursor.com in your browser, "
        "then use Set token if import still fails."
    )


def _try_rookiepy(decrypt_notes: list[str]) -> BrowserImportResult | None:
    try:
        import rookiepy
    except ImportError:
        return None

    chromium_decrypt_seen = False
    load_fn = getattr(rookiepy, "load", None)
    if callable(load_fn):
        try:
            cookies = load_fn(_CURSOR_IMPORT_DOMAINS)
            match = _find_session_cookie(cookies)
            if match is not None:
                return BrowserImportResult(token=match, source="rookiepy:load")
        except Exception as exc:
            if _is_decrypt_failure(exc):
                decrypt_notes.append(f"rookiepy:load: {_short_error(exc)}")
                chromium_decrypt_seen = True
            _LOGGER.debug("rookiepy load failed: %s", exc)
    for label, loader in _rookiepy_loaders(rookiepy):
        if _skip_chromium_loader(chromium_decrypt_seen, label):
            continue
        try:
            cookies = loader()
        except Exception as exc:
            if _is_decrypt_failure(exc):
                decrypt_notes.append(f"rookiepy:{label}: {_short_error(exc)}")
                if label in _CHROMIUM_LOADER_LABELS:
                    chromium_decrypt_seen = True
            _LOGGER.debug("rookiepy %s failed: %s", label, exc)
            continue
        match = _find_session_cookie(cookies)
        if match is not None:
            return BrowserImportResult(token=match, source=f"rookiepy:{label}")
    return None


def _try_browser_cookie3(decrypt_notes: list[str]) -> BrowserImportResult | None:
    try:
        import browser_cookie3
    except ImportError:
        return None

    chromium_decrypt_seen = False
    load_fn = getattr(browser_cookie3, "load", None)
    if callable(load_fn):
        try:
            jar = load_fn(domain_name="cursor.com")
            match = _find_session_in_jar(jar)
            if match is not None:
                return BrowserImportResult(token=match, source="browser_cookie3:load")
        except Exception as exc:
            if _is_decrypt_failure(exc):
                decrypt_notes.append(f"browser_cookie3:load: {_short_error(exc)}")
                chromium_decrypt_seen = True
            _LOGGER.debug("browser_cookie3 load failed: %s", exc)
    for label, loader in _bc3_loaders(browser_cookie3):
        if _skip_chromium_loader(chromium_decrypt_seen, label):
            continue
        try:
            jar = loader()
        except Exception as exc:
            if _is_decrypt_failure(exc):
                decrypt_notes.append(f"browser_cookie3:{label}: {_short_error(exc)}")
                if label in _CHROMIUM_LOADER_LABELS:
                    chromium_decrypt_seen = True
            _LOGGER.debug("browser_cookie3 %s failed: %s", label, exc)
            continue
        match = _find_session_in_jar(jar)
        if match is not None:
            return BrowserImportResult(token=match, source=f"browser_cookie3:{label}")
    return None


def _rookiepy_loaders(
    rookiepy: object,
) -> list[tuple[str, Callable[[], list[object]]]]:
    names = list(_ROOKIEPY_BROWSER_NAMES)
    if sys.platform == "darwin":
        names.append("safari")
    if sys.platform == "win32":
        names.extend(("internet_explorer", "octo_browser"))
    return _callable_loaders(rookiepy, names)


def _bc3_loaders(browser_cookie3: object) -> list[tuple[str, Callable[[], object]]]:
    return _callable_loaders(browser_cookie3, list(_BC3_BROWSER_NAMES))


def _callable_loaders(
    module: object,
    names: list[str],
) -> list[tuple[str, Callable[..., object]]]:
    loaders: list[tuple[str, Callable[..., object]]] = []
    for name in names:
        fn = getattr(module, name, None)
        if callable(fn):
            loaders.append((name, fn))
    return loaders


def _find_session_cookie(cookies: list[object]) -> str | None:
    for cookie in cookies:
        name = _cookie_field(cookie, "name")
        if name != SESSION_COOKIE_NAME:
            continue
        domain = _cookie_field(cookie, "domain")
        if not _domain_matches(domain):
            continue
        value = _cookie_field(cookie, "value").strip()
        if value != "":
            return value
    return None


def _find_session_in_jar(jar: object) -> str | None:
    if not hasattr(jar, "__iter__"):
        return None
    for cookie in jar:
        name = _cookie_field(cookie, "name")
        if name != SESSION_COOKIE_NAME:
            continue
        domain = _cookie_field(cookie, "domain")
        if not _domain_matches(domain):
            continue
        value = _cookie_field(cookie, "value").strip()
        if value != "":
            return value
    return None


def _cookie_field(cookie: object, key: str) -> str:
    if isinstance(cookie, dict):
        raw = cookie.get(key, "")
    else:
        raw = getattr(cookie, key, "")
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    return str(raw)


def _is_decrypt_failure(exc: BaseException) -> bool:
    text = str(exc).lower()
    return (
        "appbound" in text
        or "decrypt" in text
        or "running as admin" in text
        or "unable to get key" in text
        or "keychain" in text
        or "full disk access" in text
    )


def _short_error(exc: BaseException) -> str:
    text = str(exc).strip().splitlines()[0]
    if len(text) > 120:
        return text[:117] + "..."
    return text


def is_retryable_import_error(exc: BrowserImportError) -> bool:
    """Cookie not present yet (user still signing in). Decrypt failures are not retried."""
    if getattr(exc, "decrypt_blocked", False):
        return False
    text = str(exc).lower()
    if "appbound" in text or "decrypt" in text or "running as admin" in text:
        return False
    return True


def _skip_chromium_loader(chromium_decrypt_seen: bool, label: str) -> bool:
    """Within one library, avoid scanning every Chromium profile after decrypt failed."""
    if not chromium_decrypt_seen:
        return False
    if label not in _CHROMIUM_LOADER_LABELS:
        return False
    return sys.platform == "win32"


def _decrypt_blocked_message(notes: list[str]) -> str:
    _ = notes  # reserved for debug logging; user message stays short
    if sys.platform == "win32":
        return (
            "Automatic import cannot read Chromium cookies on this PC (Windows encryption). "
            "Paste WorkosCursorSessionToken below from DevTools → Application → Cookies → "
            "cursor.com."
        )
    if sys.platform == "darwin":
        return (
            "Automatic import could not read browser cookies. Grant Full Disk Access to this "
            "app, or paste WorkosCursorSessionToken from DevTools → Application → Cookies → "
            "cursor.com."
        )
    return (
        "Automatic import could not decrypt browser cookies (unlock your login keyring). "
        "Paste WorkosCursorSessionToken from DevTools → Application → Cookies → cursor.com."
    )


def _domain_matches(domain: str) -> bool:
    d = domain.lstrip(".").lower()
    for suffix in _CURSOR_DOMAIN_SUFFIXES:
        if d == suffix.lstrip(".") or d.endswith(suffix):
            return True
    return False
