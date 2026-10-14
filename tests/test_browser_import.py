from types import SimpleNamespace

import pytest

from cursor_usage_app.auth.browser_import import (
    BrowserImportError,
    _decrypt_blocked_message,
    import_session_token_from_browsers,
    is_retryable_import_error,
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
        load=lambda _domains: [],
        chrome=fake_chrome,
        edge=lambda: [],
        brave=lambda: [],
        firefox=lambda: [],
    )
    monkeypatch.setitem(__import__("sys").modules, "rookiepy", fake_rookiepy)
    monkeypatch.setattr(
        "cursor_usage_app.auth.browser_import._try_browser_cookie3",
        lambda _notes: None,
    )

    result = import_session_token_from_browsers()
    assert result.token == "user_01::from-browser"
    assert result.source == "rookiepy:chrome"


def test_import_raises_when_no_libraries(monkeypatch) -> None:
    monkeypatch.setattr(
        "cursor_usage_app.auth.browser_import._try_rookiepy",
        lambda _notes: None,
    )
    monkeypatch.setattr(
        "cursor_usage_app.auth.browser_import._try_browser_cookie3",
        lambda _notes: None,
    )
    with pytest.raises(BrowserImportError) as raised:
        import_session_token_from_browsers()
    assert raised.value.decrypt_blocked is False


def test_import_browser_cookie3_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        "cursor_usage_app.auth.browser_import._try_rookiepy",
        lambda _notes: None,
    )

    cookie = SimpleNamespace(
        name="WorkosCursorSessionToken",
        value="edge-token",
        domain="cursor.com",
    )

    def fake_edge() -> list[SimpleNamespace]:
        return [cookie]

    fake_bc3 = SimpleNamespace(
        load=lambda domain_name="": [],
        chrome=lambda: [],
        edge=fake_edge,
        brave=lambda: [],
        firefox=lambda: [],
    )
    monkeypatch.setitem(__import__("sys").modules, "browser_cookie3", fake_bc3)

    result = import_session_token_from_browsers()
    assert result.token == "edge-token"
    assert result.source == "browser_cookie3:edge"


def test_rookiepy_decrypt_still_tries_browser_cookie3(monkeypatch) -> None:
    def fake_brave() -> list[SimpleNamespace]:
        raise RuntimeError("could not decrypt cookie database")

    fake_rookiepy = SimpleNamespace(
        load=lambda _domains: [],
        chrome=lambda: [],
        edge=lambda: [],
        brave=fake_brave,
        firefox=lambda: [],
    )
    monkeypatch.setitem(__import__("sys").modules, "rookiepy", fake_rookiepy)

    cookie = SimpleNamespace(
        name="WorkosCursorSessionToken",
        value="brave-bc3",
        domain=".cursor.com",
    )

    def fake_brave_jar() -> list[SimpleNamespace]:
        return [cookie]

    fake_bc3 = SimpleNamespace(
        load=lambda domain_name="": [],
        chrome=lambda: [],
        edge=lambda: [],
        brave=fake_brave_jar,
        firefox=lambda: [],
    )
    monkeypatch.setitem(__import__("sys").modules, "browser_cookie3", fake_bc3)

    result = import_session_token_from_browsers()
    assert result.token == "brave-bc3"
    assert result.source == "browser_cookie3:brave"


def test_decrypt_failure_raises_decrypt_blocked(monkeypatch) -> None:
    def fail_loader() -> list[SimpleNamespace]:
        raise RuntimeError("Unable to get key for cookie decryption")

    fake_rookiepy = SimpleNamespace(
        load=fail_loader,
        chrome=fail_loader,
        edge=fail_loader,
        brave=fail_loader,
        firefox=fail_loader,
    )
    monkeypatch.setitem(__import__("sys").modules, "rookiepy", fake_rookiepy)
    fake_bc3 = SimpleNamespace(
        load=fail_loader,
        chrome=fail_loader,
        edge=fail_loader,
        brave=fail_loader,
        firefox=fail_loader,
    )
    monkeypatch.setitem(__import__("sys").modules, "browser_cookie3", fake_bc3)

    with pytest.raises(BrowserImportError) as raised:
        import_session_token_from_browsers()
    assert raised.value.decrypt_blocked is True


def test_rookiepy_dict_cookies(monkeypatch) -> None:
    cookie = {
        "name": "WorkosCursorSessionToken",
        "value": "dict-token",
        "domain": ".cursor.com",
    }

    fake_rookiepy = SimpleNamespace(
        load=lambda _domains: [cookie],
        chrome=lambda: [],
    )
    monkeypatch.setitem(__import__("sys").modules, "rookiepy", fake_rookiepy)
    monkeypatch.setattr(
        "cursor_usage_app.auth.browser_import._try_browser_cookie3",
        lambda _notes: None,
    )

    result = import_session_token_from_browsers()
    assert result.token == "dict-token"
    assert result.source == "rookiepy:load"


def test_decrypt_message_mentions_macos_browsers(monkeypatch) -> None:
    monkeypatch.setattr("sys.platform", "darwin")
    text = _decrypt_blocked_message([])
    assert "Full Disk Access" in text
    assert "DevTools" in text


def test_missing_cookie_is_retryable_decrypt_failure_is_not() -> None:
    missing = BrowserImportError("No WorkosCursorSessionToken found.")
    blocked = BrowserImportError("Could not decrypt brave cookies.", decrypt_blocked=True)
    assert is_retryable_import_error(missing) is True
    assert is_retryable_import_error(blocked) is False
