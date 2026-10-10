from unittest.mock import patch

from cursor_usage.token_input import read_token, read_token_file


def test_read_token_file(tmp_path):
    path = tmp_path / "token.txt"
    path.write_text("user_01TEST%3A%3Aabc.def.ghi\n", encoding="utf-8")
    assert read_token(file_path=str(path)) == "user_01TEST%3A%3Aabc.def.ghi"


def test_read_token_clipboard_flag():
    with patch("cursor_usage.token_input.read_clipboard", return_value="clipboard-token"):
        assert read_token(from_clipboard=True) == "clipboard-token"


def test_read_token_default_uses_clipboard_after_enter():
    with patch("cursor_usage.token_input.input", return_value=""):
        with patch("cursor_usage.token_input.read_clipboard", return_value="from-clipboard"):
            assert read_token() == "from-clipboard"
