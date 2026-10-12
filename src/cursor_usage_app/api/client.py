"""Low-level HTTP client for cursor.com APIs."""

from __future__ import annotations

import re
from typing import Any

import httpx

USAGE_SUMMARY_URL = "https://cursor.com/api/usage-summary"
SESSION_COOKIE_NAME = "WorkosCursorSessionToken"

_HTML_PREFIX_RE = re.compile(rb"^\s*<(!DOCTYPE|html\b)", re.IGNORECASE)


class UsageSummaryHttpError(Exception):
    def __init__(self, code: str, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class UsageSummaryClient:
    """Fetches usage-summary with a WorkOS session token."""

    def __init__(
        self,
        timeout_seconds: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._timeout = timeout_seconds
        self._transport = transport

    def fetch_raw(self, session_token: str) -> dict[str, Any]:
        """
        Return parsed JSON body on success.

        Raises UsageSummaryHttpError for auth, network, WAF, and parse failures.
        """
        headers = _browser_headers()
        cookies = {SESSION_COOKIE_NAME: session_token}

        client_kwargs: dict[str, Any] = {
            "timeout": self._timeout,
            "follow_redirects": True,
        }
        if self._transport is not None:
            client_kwargs["transport"] = self._transport

        try:
            with httpx.Client(**client_kwargs) as client:
                response = client.get(USAGE_SUMMARY_URL, headers=headers, cookies=cookies)
        except httpx.TimeoutException:
            raise UsageSummaryHttpError(
                code="network",
                message="Request timed out",
            ) from None
        except httpx.RequestError as exc:
            raise UsageSummaryHttpError(
                code="network",
                message=str(exc) or "Network request failed",
            ) from None

        if _looks_like_html(response):
            raise UsageSummaryHttpError(
                code="blocked_or_waf",
                message="Received HTML instead of JSON (possible WAF or login page)",
                status_code=response.status_code,
            )

        if response.status_code in (401, 403):
            raise UsageSummaryHttpError(
                code="not_authenticated",
                message="Session token rejected",
                status_code=response.status_code,
            )

        if response.status_code < 200 or response.status_code >= 300:
            raise UsageSummaryHttpError(
                code="unknown",
                message=f"Unexpected HTTP status {response.status_code}",
                status_code=response.status_code,
            )

        try:
            body = response.json()
        except ValueError:
            raise UsageSummaryHttpError(
                code="unknown",
                message="Response body is not valid JSON",
                status_code=response.status_code,
            ) from None

        if not isinstance(body, dict):
            raise UsageSummaryHttpError(
                code="unknown",
                message="Expected JSON object from usage-summary",
                status_code=response.status_code,
            )

        return body


def _browser_headers() -> dict[str, str]:
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        ),
        "Referer": "https://cursor.com/dashboard",
        "Origin": "https://cursor.com",
    }


def _looks_like_html(response: httpx.Response) -> bool:
    content_type = (response.headers.get("content-type") or "").lower()
    if ("text/html" in content_type) or ("application/xhtml" in content_type):
        return True
    raw = response.content[:512]
    return bool(_HTML_PREFIX_RE.match(raw))
