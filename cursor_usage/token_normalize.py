"""Normalize and validate WorkosCursorSessionToken values."""

from __future__ import annotations

import re
from urllib.parse import unquote

TOKEN_PREFIX = "workoscursorsessiontoken="
SEPARATOR_ENCODED = "%3A%3A"
JWT_PARTS = 3

# user_<id>%3A%3A<header>.<payload>.<signature> or user_<id>::<jwt>
_TOKEN_RE = re.compile(
    r"^user_[A-Za-z0-9]+(?P<sep>%3A%3A|::)(?P<jwt>[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)$"
)


def normalize_token(raw: str) -> str:
    """Return canonical token form (separator encoded as %3A%3A)."""
    cleaned = raw.strip()
    if cleaned == "":
        raise ValueError("Token cannot be empty")

    lowered = cleaned.lower()
    if lowered.startswith(TOKEN_PREFIX):
        cleaned = cleaned[len(TOKEN_PREFIX) :].strip()

    if "%253a%253a" in cleaned.lower():
        raise ValueError("Token appears double URL-encoded. Paste the value from DevTools as-is.")

    if "%3a%3a" in cleaned.lower() and SEPARATOR_ENCODED not in cleaned:
        cleaned = re.sub(r"%3a%3a", SEPARATOR_ENCODED, cleaned, flags=re.IGNORECASE)

    if SEPARATOR_ENCODED in cleaned:
        user_part, jwt_part = cleaned.split(SEPARATOR_ENCODED, 1)
        candidate = f"{user_part}{SEPARATOR_ENCODED}{jwt_part}"
    elif "::" in cleaned:
        user_part, jwt_part = cleaned.split("::", 1)
        candidate = f"{user_part}{SEPARATOR_ENCODED}{jwt_part}"
    else:
        decoded = unquote(cleaned)
        if decoded != cleaned and "::" in decoded:
            user_part, jwt_part = decoded.split("::", 1)
            candidate = f"{user_part}{SEPARATOR_ENCODED}{jwt_part}"
        else:
            raise ValueError(
                "Token must look like user_<id>%3A%3A<jwt> or user_<id>::<jwt>. "
                "Copy only the cookie value from DevTools."
            )

    match = _TOKEN_RE.match(candidate.replace(SEPARATOR_ENCODED, "::", 1))
    if not match:
        raise ValueError(
            "Token format is invalid. Expected user_<id>%3A%3A<jwt> with three JWT segments."
        )

    jwt = match.group("jwt")
    if len(jwt.split(".")) != JWT_PARTS:
        raise ValueError("Token JWT must have three segments (header.payload.signature).")

    return candidate
