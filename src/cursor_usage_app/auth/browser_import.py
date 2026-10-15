"""Import WorkosCursorSessionToken from installed browsers."""

from __future__ import annotations

import logging
import sys
import threading
from dataclasses import dataclass
from typing import Callable, Literal, Protocol

from cursor_usage_app.api.client import SESSION_COOKIE_NAME

_LOGGER = logging.getLogger(__name__)

ImportScanProfile = Literal["full", "login_poll"]

_CURSOR_DOMAIN_SUFFIXES = (".cursor.com", "cursor.com")

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
_LOGIN_POLL_BROWSER_NAMES: frozenset[str] = frozenset(
    {"firefox", "chrome", "edge", "brave", "chromium"},
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

_import_lock = threading.Lock()
_login_flow_active = False
_login_flow_lock = threading.Lock()


class BrowserImportError(Exception):
    """Could not find or read a cursor.com session cookie."""

    def __init__(self, message: str, *, decrypt_blocked: bool = False) -> None:
        super().__init__(message)
        self.decrypt_blocked = decrypt_blocked


class BrowserImportBusyError(BrowserImportError):
    """Another thread is already scanning browsers."""


@dataclass(frozen=True)
class BrowserImportResult:
    token: str
    source: str


class _CookieLike(Protocol):
    name: str
    value: str
    domain: str


def set_browser_login_flow_active(active: bool) -> None:
    """When the user is in the sign-in flow, skip silent background import."""
    global _login_flow_active
    with _login_flow_lock:
        _login_flow_active = active


def browser_login_flow_active() -> bool:
    with _login_flow_lock:
        return _login_flow_active


def import_session_token_from_browsers(
    *,
    scan_profile: ImportScanProfile = "full",
    wait_for_lock: bool = True,
) -> BrowserImportResult:
    """
    Scan common browsers for WorkosCursorSessionToken on cursor.com.

    Tries rookiepy first, then browser-cookie3. Per-browser only (no library load()).
    """
    if wait_for_lock:
        _import_lock.acquire()
    elif not _import_lock.acquire(blocking=False):
        raise BrowserImportBusyError("Browser import already in progress.")

    try:
        return _import_session_token_from_browsers_locked(scan_profile)
    finally:
        _import_lock.release()


def _import_session_token_from_browsers_locked(
    scan_profile: ImportScanProfile,
) -> BrowserImportResult:
    decrypt_notes: list[str] = []

    token = _try_rookiepy(decrypt_notes, scan_profile)
    if token is not None:
        return token

    token = _try_browser_cookie3(decrypt_notes, scan_profile)
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


def _try_rookiepy(
    decrypt_notes: list[str],
    scan_profile: ImportScanProfile,
) -> BrowserImportResult | None:
    try:
        import rookiepy
    except ImportError:
        return None

    chromium_decrypt_seen = False
    for label, loader in _rookiepy_loaders(rookiepy, scan_profile):
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


def _try_browser_cookie3(
    decrypt_notes: list[str],
    scan_profile: ImportScanProfile,
) -> BrowserImportResult | None:
    try:
        import browser_cookie3
    except ImportError:
        return None

    chromium_decrypt_seen = False
    for label, loader in _bc3_loaders(browser_cookie3, scan_profile):
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


def _browser_names_for_profile(
    names: list[str],
    scan_profile: ImportScanProfile,
) -> list[str]:
    if scan_profile != "login_poll":
        return names
    filtered = [name for name in names if name in _LOGIN_POLL_BROWSER_NAMES]
    if sys.platform == "darwin" and "safari" in names:
        filtered.append("safari")
    return filtered


def _rookiepy_loaders(
    rookiepy: object,
    scan_profile: ImportScanProfile,
) -> list[tuple[str, Callable[[], list[object]]]]:
    names = list(_ROOKIEPY_BROWSER_NAMES)
    if sys.platform == "darwin":
        names.append("safari")
    if sys.platform == "win32":
        names.extend(("internet_explorer", "octo_browser"))
    names = _browser_names_for_profile(names, scan_profile)
    return _callable_loaders(rookiepy, names)


def _bc3_loaders(
    browser_cookie3: object,
    scan_profile: ImportScanProfile,
) -> list[tuple[str, Callable[[], object]]]:
    names = _browser_names_for_profile(list(_BC3_BROWSER_NAMES), scan_profile)
    return _callable_loaders(browser_cookie3, names)


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
    if isinstance(exc, BrowserImportBusyError):
        return True
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
