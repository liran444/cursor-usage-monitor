"""Fetch usage-summary and write status.json."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import httpx

from cursor_usage import keyring_store
from cursor_usage.http_client import (
    USAGE_SUMMARY_URL,
    build_usage_summary_client,
    is_html_response,
    summarize_response_body,
)
from cursor_usage.map_summary import error_status, map_usage_summary
from cursor_usage.paths import status_path
from cursor_usage.token_normalize import normalize_token


@dataclass
class FetchResult:
    code: int
    http_status: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    response_snippet: str | None = None


def write_status_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".status-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _http_error_status(status_code: int, body: str) -> tuple[str, str]:
    snippet = summarize_response_body(body)
    if is_html_response(body):
        return (
            "blocked_or_waf",
            f"HTTP {status_code}: response looks like HTML (possible bot protection). {snippet}",
        )
    if snippet:
        return ("http_error", f"HTTP {status_code}: {snippet}")
    return ("http_error", f"HTTP {status_code}")


def run_fetch(verbose: bool = False) -> int:
    return run_fetch_detailed(verbose=verbose).code


def run_fetch_detailed(verbose: bool = False) -> FetchResult:
    raw_token = keyring_store.get_token()
    if raw_token is None:
        status = error_status("not_authenticated", "Set token with: cursor-usage token set")
        write_status_atomic(status_path(), status)
        return FetchResult(
            code=1,
            error_code="not_authenticated",
            error_message=status["error"],
        )

    try:
        token = normalize_token(raw_token)
    except ValueError as exc:
        status = error_status("invalid_token", str(exc))
        write_status_atomic(status_path(), status)
        return FetchResult(code=1, error_code="invalid_token", error_message=str(exc))

    try:
        with build_usage_summary_client(token) as client:
            response = client.get(USAGE_SUMMARY_URL)
    except httpx.HTTPError as exc:
        status = error_status("network", str(exc))
        write_status_atomic(status_path(), status)
        return FetchResult(code=1, error_code="network", error_message=str(exc))

    body = response.text
    snippet = summarize_response_body(body) if body else None

    if response.status_code in (401, 403):
        message = f"HTTP {response.status_code}"
        if snippet:
            message = f"{message}: {snippet}"
        status = error_status("not_authenticated", message)
        write_status_atomic(status_path(), status)
        result = FetchResult(
            code=1,
            http_status=response.status_code,
            error_code="not_authenticated",
            error_message=message,
            response_snippet=snippet,
        )
        if verbose:
            _print_verbose(result)
        return result

    if response.status_code != 200:
        error_code, message = _http_error_status(response.status_code, body)
        status = error_status(error_code, message)
        write_status_atomic(status_path(), status)
        result = FetchResult(
            code=1,
            http_status=response.status_code,
            error_code=error_code,
            error_message=message,
            response_snippet=snippet,
        )
        if verbose:
            _print_verbose(result)
        return result

    try:
        payload = response.json()
    except json.JSONDecodeError:
        status = error_status("invalid_response", "Not JSON")
        write_status_atomic(status_path(), status)
        result = FetchResult(
            code=1,
            http_status=response.status_code,
            error_code="invalid_response",
            error_message="Not JSON",
            response_snippet=snippet,
        )
        if verbose:
            _print_verbose(result)
        return result

    if not isinstance(payload, dict):
        status = error_status("invalid_response", "Expected object")
        write_status_atomic(status_path(), status)
        result = FetchResult(
            code=1,
            http_status=response.status_code,
            error_code="invalid_response",
            error_message="Expected object",
            response_snippet=snippet,
        )
        if verbose:
            _print_verbose(result)
        return result

    status = map_usage_summary(payload)
    write_status_atomic(status_path(), status)
    result = FetchResult(code=0, http_status=response.status_code)
    if verbose:
        _print_verbose(result)
    return result


def _print_verbose(result: FetchResult) -> None:
    if result.http_status is not None:
        print(f"HTTP {result.http_status}")
    if result.code == 0:
        print("Response: OK (usage-summary JSON)")
        return
    if result.error_code:
        print(f"Error: {result.error_code}")
    if result.error_message:
        print(result.error_message)
    elif result.response_snippet:
        print(result.response_snippet)
