import io
import sys
from argparse import Namespace

import httpx

from cursor_usage_app.api.client import UsageSummaryClient
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.auth.token_cli import cmd_token_clear, cmd_token_set, cmd_token_test
from fixture_loader import load_fixture


def test_token_test_fails_without_token(fake_keyring, tmp_path, capsys) -> None:
    store = SessionStore(fallback_path=tmp_path / "session_token")
    args = Namespace()
    code = cmd_token_test(args, store=store)
    assert code == 1
    err = capsys.readouterr().err
    assert "No session token" in err


def test_token_test_succeeds_with_mocked_http(fake_keyring, tmp_path, monkeypatch) -> None:
    payload = load_fixture("usage_summary_personal_only.json")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, headers={"content-type": "application/json"})

    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::test-secret")

    monkeypatch.setattr(
        "cursor_usage_app.auth.token_cli.UsageSummaryClient",
        lambda: UsageSummaryClient(transport=httpx.MockTransport(handler)),
    )

    args = Namespace()
    code = cmd_token_test(args, store=store)
    assert code == 0


def test_token_set_from_string(fake_keyring, tmp_path) -> None:
    store = SessionStore(fallback_path=tmp_path / "session_token")
    args = Namespace(file=None, clipboard=False)
    stdin = io.StringIO("user_01::stdin-token\n")
    old = sys.stdin
    sys.stdin = stdin
    try:
        code = cmd_token_set(args, store=store)
    finally:
        sys.stdin = old
    assert code == 0
    assert store.get_token() == "user_01::stdin-token"


def test_token_clear(fake_keyring, tmp_path) -> None:
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::x")
    code = cmd_token_clear(Namespace(), store=store)
    assert code == 0
    assert store.get_token() is None
