"""Fetch usage-summary and write status.json."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import httpx

from cursor_usage import keyring_store
from cursor_usage.map_summary import error_status, map_usage_summary
from cursor_usage.paths import status_path

USAGE_SUMMARY_URL = "https://cursor.com/api/usage-summary"
USER_AGENT = "cursor-usage-monitor/0.1.0"
TIMEOUT_SECONDS = 30.0


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


def run_fetch() -> int:
    token = keyring_store.get_token()
    if token is None:
        status = error_status("not_authenticated", "Set token with: cursor-usage token set")
        write_status_atomic(status_path(), status)
        return 1

    headers = {
        "Cookie": f"WorkosCursorSessionToken={token}",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    try:
        with httpx.Client(timeout=TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(USAGE_SUMMARY_URL, headers=headers)
    except httpx.HTTPError as exc:
        status = error_status("network", str(exc))
        write_status_atomic(status_path(), status)
        return 1

    if response.status_code in (401, 403):
        status = error_status("not_authenticated", f"HTTP {response.status_code}")
        write_status_atomic(status_path(), status)
        return 1

    if response.status_code != 200:
        status = error_status("http_error", f"HTTP {response.status_code}")
        write_status_atomic(status_path(), status)
        return 1

    try:
        payload = response.json()
    except json.JSONDecodeError:
        status = error_status("invalid_response", "Not JSON")
        write_status_atomic(status_path(), status)
        return 1

    if not isinstance(payload, dict):
        status = error_status("invalid_response", "Expected object")
        write_status_atomic(status_path(), status)
        return 1

    status = map_usage_summary(payload)
    write_status_atomic(status_path(), status)
    return 0
