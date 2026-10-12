"""Read/write usage_cache.json with ok/error envelope."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from platformdirs import user_cache_dir

from cursor_usage_app.domain.models import UsageSnapshot

CACHE_DIR_NAME = "cursor-usage-app"
CACHE_FILE_NAME = "usage_cache.json"

ErrorCode = Literal[
    "not_authenticated",
    "invalid_token",
    "network",
    "blocked_or_waf",
    "unknown",
]


@dataclass(frozen=True)
class CacheError:
    code: ErrorCode
    message: str


@dataclass(frozen=True)
class CacheEnvelopeOk:
    ok: Literal[True]
    data: UsageSnapshot
    fetched_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": True,
            "data": self.data.to_dict(),
            "fetchedAt": self.fetched_at,
        }


@dataclass(frozen=True)
class CacheEnvelopeError:
    ok: Literal[False]
    error: CacheError
    fetched_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": False,
            "error": {"code": self.error.code, "message": self.error.message},
            "fetchedAt": self.fetched_at,
        }


CacheEnvelope = CacheEnvelopeOk | CacheEnvelopeError


def default_cache_path() -> Path:
    base = Path(user_cache_dir(CACHE_DIR_NAME, appauthor=False))
    return base / CACHE_FILE_NAME


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_cache_envelope(path: Path, envelope: CacheEnvelope) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = envelope.to_dict()
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_cache_envelope(path: Path) -> CacheEnvelope | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return parse_cache_envelope(raw)


def parse_cache_envelope(raw: dict[str, Any]) -> CacheEnvelope | None:
    if not isinstance(raw, dict):
        return None
    fetched_at = raw.get("fetchedAt")
    if not isinstance(fetched_at, str):
        return None

    if raw.get("ok") is True:
        data = raw.get("data")
        if not isinstance(data, dict):
            return None
        return CacheEnvelopeOk(ok=True, data=UsageSnapshot.from_dict(data), fetched_at=fetched_at)

    if raw.get("ok") is False:
        err = raw.get("error")
        if not isinstance(err, dict):
            return None
        code = err.get("code")
        message = err.get("message")
        if not isinstance(code, str) or not isinstance(message, str):
            return None
        if code not in _ERROR_CODES:
            code = "unknown"
        return CacheEnvelopeError(
            ok=False,
            error=CacheError(code=code, message=message),
            fetched_at=fetched_at,
        )

    return None


_ERROR_CODES: frozenset[str] = frozenset(
    {
        "not_authenticated",
        "invalid_token",
        "network",
        "blocked_or_waf",
        "unknown",
    }
)
