from types import SimpleNamespace

import pytest

from cursor_usage_app.auth.browser_import import (
    BrowserImportError,
    import_session_token_from_browsers,
)


def test_import_finds_cookie_via_rookiepy(monkeypatch) -> None:
    cookie = SimpleNamespace(
        name="WorkosCursorSessionToken",
        value="user_01::from-browser",
        domain=".cursor.com",
    )

    def fake_chrome() -> list[SimpleNamespace]:
        return [cookie]

    fake_rookiepy = SimpleNamespace(
        chrome=fake_chrome,
        edge=lambda: [],
        brave=lambda: [],
        firefox=lambda: [],
    )
    monkeypatch.setitem(__import__("sys").modules, "rookiepy", fake_rookiepy)
    monkeypatch.setattr(
        "cursor_usage_app.auth.browser_import._try_browser_cookie3",
        lambda: None,
    )

    result = import_session_token_from_browsers()
    assert result.token == "user_01::from-browser"
    assert result.source == "rookiepy:chrome"


def test_import_raises_when_no_libraries(monkeypatch) -> None:
    monkeypatch.setattr("cursor_usage_app.auth.browser_import._try_rookiepy", lambda: None)
    monkeypatch.setattr("cursor_usage_app.auth.browser_import._try_browser_cookie3", lambda: None)
    with pytest.raises(BrowserImportError):
        import_session_token_from_browsers()


def test_import_browser_cookie3_fallback(monkeypatch) -> None:
    monkeypatch.setattr("cursor_usage_app.auth.browser_import._try_rookiepy", lambda: None)

    cookie = SimpleNamespace(
        name="WorkosCursorSessionToken",
        value="edge-token",
        domain="cursor.com",
    )

    def fake_edge() -> list[SimpleNamespace]:
        return [cookie]

    fake_bc3 = SimpleNamespace(
        chrome=lambda: [],
        edge=fake_edge,
        brave=lambda: [],
        firefox=lambda: [],
    )
    monkeypatch.setitem(__import__("sys").modules, "browser_cookie3", fake_bc3)

    result = import_session_token_from_browsers()
    assert result.token == "edge-token"
    assert result.source == "browser_cookie3:edge"
