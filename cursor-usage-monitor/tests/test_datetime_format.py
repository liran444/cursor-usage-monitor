from datetime import timezone

from cursor_usage.datetime_format import format_datetime_local, parse_iso_datetime


def test_parse_iso_z_suffix():
    dt = parse_iso_datetime("2026-10-20T11:08:43.000Z")
    assert dt.year == 2026
    assert dt.month == 10
    assert dt.day == 20
    assert dt.hour == 11
    assert dt.minute == 8
    assert dt.tzinfo == timezone.utc


def test_format_invalid_passthrough():
    assert format_datetime_local("not-a-date") == "not-a-date"


def test_format_utc_to_local_same_shape():
    raw = "2026-10-20T11:08:43.000Z"
    formatted = format_datetime_local(raw)
    assert formatted is not None
    assert formatted != raw
    assert format_datetime_local(raw) == formatted
