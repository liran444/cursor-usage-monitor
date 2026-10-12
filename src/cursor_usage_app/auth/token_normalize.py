"""Normalize user-provided WorkOS session token values."""

from __future__ import annotations

import re
from urllib.parse import unquote

_COOKIE_NAME = "WorkosCursorSessionToken"
_PREFIX_RE = re.compile(
    rf"^{re.escape(_COOKIE_NAME)}\s*=\s*",
    re.IGNORECASE,
)


class TokenNormalizeError(ValueError):
    """Token input could not be normalized."""


def normalize_session_token(raw: str) -> str:
    """
    Accept DevTools cookie value (``::`` or URL-encoded ``%3A%3A``).

    Rejects values that include the cookie name prefix.
    """
    if raw is None:
        raise TokenNormalizeError("Token is empty")

    text = raw.strip()
    if text == "":
        raise TokenNormalizeError("Token is empty")

    if _PREFIX_RE.match(text):
        raise TokenNormalizeError(
            f"Paste only the cookie value, not '{_COOKIE_NAME}=...'"
        )

    decoded = unquote(text)
    normalized = decoded.strip()
    if normalized == "":
        raise TokenNormalizeError("Token is empty after decoding")

    if _PREFIX_RE.match(normalized):
        raise TokenNormalizeError(
            f"Paste only the cookie value, not '{_COOKIE_NAME}=...'"
        )

    return normalized
