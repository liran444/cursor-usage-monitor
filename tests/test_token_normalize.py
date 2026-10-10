import pytest

from cursor_usage.token_normalize import normalize_token

SAMPLE_ENCODED = (
    "user_01TESTUSER%3A%3A"
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJ0ZXN0In0."
    "signature"
)
SAMPLE_DECODED = (
    "user_01TESTUSER::"
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiJ0ZXN0In0."
    "signature"
)


def test_normalize_encoded_separator():
    assert normalize_token(SAMPLE_ENCODED) == SAMPLE_ENCODED


def test_normalize_decoded_separator():
    assert normalize_token(SAMPLE_DECODED) == SAMPLE_ENCODED


def test_normalize_strips_whitespace_and_prefix():
    raw = f"  WorkosCursorSessionToken={SAMPLE_ENCODED}  "
    assert normalize_token(raw) == SAMPLE_ENCODED


def test_normalize_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        normalize_token("   ")


def test_normalize_rejects_malformed_jwt():
    with pytest.raises(ValueError, match="three JWT segments"):
        normalize_token("user_01TESTUSER%3A%3Anot-a-jwt")


def test_normalize_rejects_double_encoding():
    double = SAMPLE_ENCODED.replace("%3A%3A", "%253A%253A")
    with pytest.raises(ValueError, match="double URL-encoded"):
        normalize_token(double)
