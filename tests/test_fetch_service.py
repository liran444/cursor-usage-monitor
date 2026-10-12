import json
from pathlib import Path

import httpx

from cursor_usage_app.api.client import UsageSummaryClient
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.fetch_service import run_fetch
from fixture_loader import load_fixture


def test_run_fetch_writes_ok_envelope(tmp_path: Path, monkeypatch) -> None:
    payload = load_fixture("usage_summary_personal_only.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, headers={"content-type": "application/json"})

    monkeypatch.setenv("CURSOR_USAGE_TOKEN_TEST", "secret-token")
    cache_path = tmp_path / "usage_cache.json"
    code = run_fetch(
        cache_path=cache_path,
        client=UsageSummaryClient(transport=httpx.MockTransport(handler)),
    )
    assert code == 0
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    assert raw["ok"] is True
    assert raw["data"]["plan_percents"]["total_percent_used"] == 42.0


def test_run_fetch_without_token_writes_auth_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CURSOR_USAGE_TOKEN_TEST", raising=False)
    cache_path = tmp_path / "usage_cache.json"
    store = SessionStore(fallback_path=tmp_path / "session_token")
    code = run_fetch(cache_path=cache_path, store=store)
    assert code == 1
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    assert raw["ok"] is False
    assert raw["error"]["code"] == "not_authenticated"


def test_run_fetch_reads_from_session_store(fake_keyring, tmp_path: Path, monkeypatch) -> None:
    payload = load_fixture("usage_summary_personal_only.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, headers={"content-type": "application/json"})

    monkeypatch.delenv("CURSOR_USAGE_TOKEN_TEST", raising=False)
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::stored")

    cache_path = tmp_path / "usage_cache.json"
    code = run_fetch(
        cache_path=cache_path,
        client=UsageSummaryClient(transport=httpx.MockTransport(handler)),
        store=store,
    )
    assert code == 0
    raw = json.loads(cache_path.read_text(encoding="utf-8"))
    assert raw["ok"] is True
