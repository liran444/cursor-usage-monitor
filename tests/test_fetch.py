import json
from unittest.mock import MagicMock, patch

import httpx

from cursor_usage.fetch import run_fetch_detailed
from cursor_usage.http_client import BROWSER_HEADERS, build_usage_summary_client
from cursor_usage.paths import status_path

SAMPLE_TOKEN = (
    "user_01TESTUSER%3A%3A"
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJ0ZXN0In0."
    "signature"
)


def test_build_usage_summary_client_sets_browser_headers_and_cookie():
    with build_usage_summary_client(SAMPLE_TOKEN) as client:
        assert client.headers["User-Agent"] == BROWSER_HEADERS["User-Agent"]
        assert client.headers["Referer"] == BROWSER_HEADERS["Referer"]
        assert client.cookies.get("WorkosCursorSessionToken") == SAMPLE_TOKEN


def test_run_fetch_detailed_success(tmp_path, monkeypatch):
    monkeypatch.setattr("cursor_usage.fetch.status_path", lambda: tmp_path / "status.json")
    payload = {"individualUsage": {"plan": {"used": 100, "limit": 200}}}

    response = MagicMock()
    response.status_code = 200
    response.text = json.dumps(payload)
    response.json.return_value = payload

    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False

    with patch("cursor_usage.fetch.keyring_store.get_token", return_value=SAMPLE_TOKEN):
        with patch("cursor_usage.fetch.build_usage_summary_client", return_value=client):
            result = run_fetch_detailed()

    assert result.code == 0
    assert result.http_status == 200
    saved = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert saved["ok"] is True


def test_run_fetch_detailed_http_400_includes_body(tmp_path, monkeypatch):
    monkeypatch.setattr("cursor_usage.fetch.status_path", lambda: tmp_path / "status.json")

    response = MagicMock()
    response.status_code = 400
    response.text = '{"error":"bad request"}'

    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False

    with patch("cursor_usage.fetch.keyring_store.get_token", return_value=SAMPLE_TOKEN):
        with patch("cursor_usage.fetch.build_usage_summary_client", return_value=client):
            result = run_fetch_detailed()

    assert result.code == 1
    assert result.http_status == 400
    assert "bad request" in (result.error_message or "")
    saved = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert "HTTP 400" in saved["error"]


def test_run_fetch_detailed_html_response_maps_to_waf(tmp_path, monkeypatch):
    monkeypatch.setattr("cursor_usage.fetch.status_path", lambda: tmp_path / "status.json")

    response = MagicMock()
    response.status_code = 403
    response.text = "<!doctype html><html><body>blocked</body></html>"

    client = MagicMock()
    client.get.return_value = response
    client.__enter__.return_value = client
    client.__exit__.return_value = False

    with patch("cursor_usage.fetch.keyring_store.get_token", return_value=SAMPLE_TOKEN):
        with patch("cursor_usage.fetch.build_usage_summary_client", return_value=client):
            result = run_fetch_detailed()

    assert result.code == 1
    assert result.error_code == "not_authenticated"
    saved = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert saved["error"].startswith("not_authenticated: HTTP 403")
