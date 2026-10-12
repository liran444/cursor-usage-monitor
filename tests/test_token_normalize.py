import pytest

from cursor_usage_app.auth.token_normalize import TokenNormalizeError, normalize_session_token


def test_normalize_plain_value() -> None:
    raw = "user_01::eyJhbGciOiJIUzI1NiJ9.signature"
    assert normalize_session_token(raw) == raw


def test_normalize_url_encoded_colons() -> None:
    raw = "user_01%3A%3AeyJhbGciOiJIUzI1NiJ9"
    assert normalize_session_token(raw) == "user_01::eyJhbGciOiJIUzI1NiJ9"


def test_rejects_cookie_name_prefix() -> None:
    with pytest.raises(TokenNormalizeError, match="cookie value"):
        normalize_session_token("WorkosCursorSessionToken=abc::def")


def test_rejects_empty() -> None:
    with pytest.raises(TokenNormalizeError):
        normalize_session_token("   ")
