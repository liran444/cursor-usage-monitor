"""HTTP helpers for Cursor dashboard API requests."""

from __future__ import annotations

import httpx

USAGE_SUMMARY_URL = "https://cursor.com/api/usage-summary"
TIMEOUT_SECONDS = 30.0

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://cursor.com/dashboard",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}


def build_usage_summary_client(token: str) -> httpx.Client:
    cookies = httpx.Cookies()
    cookies.set("WorkosCursorSessionToken", token, domain="cursor.com")
    return httpx.Client(
        timeout=TIMEOUT_SECONDS,
        follow_redirects=True,
        headers=BROWSER_HEADERS,
        cookies=cookies,
    )


def summarize_response_body(text: str, limit: int = 200) -> str:
    snippet = text.strip().replace("\n", " ").replace("\r", " ")
    if len(snippet) > limit:
        snippet = snippet[:limit] + "..."
    return snippet


def is_html_response(text: str) -> bool:
    lowered = text.lstrip().lower()
    return lowered.startswith("<!doctype html") or lowered.startswith("<html")
