import pytest

from cursor_usage_app.app.widget.gauge_segments import compute_plan_arc_segments


def test_degraded_mode_when_only_total() -> None:
    segments = compute_plan_arc_segments(26.0, None, None)
    assert segments.degraded_single_color is True
    assert segments.total_span == 26.0
    assert segments.api_span == 26.0
    assert segments.auto_span == 0.0


def test_segments_match_team_fixture_percents() -> None:
    segments = compute_plan_arc_segments(64.0, 38.0, 26.0)
    assert segments.degraded_single_color is False
    assert segments.total_span == 64.0
    assert segments.api_span == 38.0
    assert segments.auto_span == 26.0


def test_clamps_when_api_plus_auto_exceeds_total() -> None:
    segments = compute_plan_arc_segments(50.0, 40.0, 40.0)
    assert segments.total_span == 50.0
    assert segments.api_span == pytest.approx(25.0)
    assert segments.auto_span == pytest.approx(25.0)


def test_auto_fills_remainder_when_sum_below_total() -> None:
    segments = compute_plan_arc_segments(64.0, 30.0, 10.0)
    assert segments.api_span == 30.0
    assert segments.auto_span == 34.0
