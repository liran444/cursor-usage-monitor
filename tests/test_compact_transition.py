"""Collapse / expand motion keeps anchored controls in place."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QAbstractAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QImage

from cursor_usage_app.app.widget.usage_widget import UsageWidget, _LAYOUT_TRANSITION_MS
from cursor_usage_app.app.widget.usage_window import UsageWindow
from cursor_usage_app.cache.usage_cache import CacheEnvelopeOk, utc_now_iso
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from fixture_loader import load_fixture

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


@pytest.fixture
def qapp():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _team_envelope() -> dict:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_team_pool.json"))
    return CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()).to_dict()


def _ready_widget(qapp) -> UsageWidget:
    widget = UsageWidget()
    widget.apply_fixture_envelope_dict(_team_envelope())
    widget.show()
    qapp.processEvents()
    widget._lock_refresh_button_metrics()
    qapp.processEvents()
    return widget


def _root_pos(widget: UsageWidget, child) -> QPoint:
    return child.mapTo(widget, QPoint(0, 0))


def test_collapse_progress_does_not_move_anchored_controls(qapp) -> None:
    widget = _ready_widget(qapp)
    personal = widget._personal_card.geometry()
    settings = widget._btn_settings.geometry()
    toggle_x = _root_pos(widget, widget._btn_toggle).x()
    toggle_width = widget._btn_toggle.width()
    refresh_x = _root_pos(widget, widget._btn_refresh).x()
    action_height = widget._action_row.height()
    details_height = widget._details_panel.height()
    team_pos = widget._team_block.pos()
    gauge_size = widget._total_gauge.size()
    expanded_height = widget.height()
    previous_action_y = _root_pos(widget, widget._action_row).y()
    widget._refresh_layout_metrics()

    for progress in (0.0, 0.15, 0.28, 0.45, 0.7, 1.0):
        widget._apply_layout_progress(progress)
        qapp.processEvents()
        assert widget._personal_card.geometry() == personal
        assert widget._btn_settings.geometry() == settings
        assert _root_pos(widget, widget._btn_toggle).x() == toggle_x
        assert widget._btn_toggle.width() == toggle_width
        assert _root_pos(widget, widget._btn_refresh).x() == refresh_x
        assert widget._action_row.height() == action_height
        assert widget._details_panel.height() == details_height
        assert widget._team_block.pos() == team_pos
        assert widget._total_gauge.size() == gauge_size
        action_y = _root_pos(widget, widget._action_row).y()
        assert action_y <= previous_action_y
        previous_action_y = action_y

    assert widget.height() < expanded_height
    assert widget._btn_dashboard.isHidden() is True
    widget.set_compact(True)
    assert widget.is_compact() is True
    assert widget._btn_toggle.text() == "Expand"
    assert widget._btn_toggle.width() == toggle_width
    widget.set_compact(False)
    assert widget.is_compact() is False
    assert abs(widget.height() - expanded_height) <= 1
    assert _root_pos(widget, widget._btn_refresh).x() == refresh_x
    assert widget._btn_toggle.text() == "Collapse"
    assert widget._btn_toggle.width() == toggle_width


def test_header_pixels_stay_fixed_while_the_panel_closes(qapp) -> None:
    widget = _ready_widget(qapp)
    widget._refresh_layout_metrics()
    before = widget._personal_card.grab()
    before_image = before.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    for progress in (0.2, 0.55, 1.0):
        widget._apply_layout_progress(progress)
        qapp.processEvents()
        after = widget._personal_card.grab()
        after_image = after.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        assert before_image.size() == after_image.size()
        assert before_image.constBits().tobytes() == after_image.constBits().tobytes()


def test_toggle_click_runs_inoutsine_and_can_reverse(qapp) -> None:
    widget = _ready_widget(qapp)
    expanded_height = widget.height()
    refresh_x = _root_pos(widget, widget._btn_refresh).x()
    widget._btn_toggle.click()
    animation = widget._layout_anim
    assert animation is not None
    assert animation.state() == QAbstractAnimation.State.Running
    assert animation.easingCurve().type() == QEasingCurve.Type.InOutSine
    assert animation.duration() == _LAYOUT_TRANSITION_MS
    assert widget._btn_toggle.text() == "Expand"
    assert widget._chevron_degrees == 0.0 or widget._layout_progress == 0.0

    animation.setCurrentTime(animation.duration() // 2)
    qapp.processEvents()
    assert 0.0 < widget._layout_progress < 1.0
    assert widget._btn_toggle.width() > 0

    widget._btn_toggle.click()
    animation.setCurrentTime(animation.duration())
    qapp.processEvents()
    assert widget.is_compact() is False
    assert abs(widget.height() - expanded_height) <= 1
    assert _root_pos(widget, widget._btn_refresh).x() == refresh_x
    assert widget._btn_toggle.text() == "Collapse"


def test_widget_height_steps_monotonically_during_collapse(qapp) -> None:
    widget = _ready_widget(qapp)
    widget._refresh_layout_metrics()
    heights: list[int] = []
    for step in range(21):
        progress = step / 20.0
        widget._apply_layout_progress(progress)
        qapp.processEvents()
        heights.append(widget.height())
    for previous, current in zip(heights, heights[1:]):
        assert current <= previous
        assert previous - current <= 20


def test_window_top_left_stays_put_while_height_animates(qapp) -> None:
    window = UsageWindow(auto_center=False)
    window.show()
    qapp.processEvents()
    card = window.widget()
    card.apply_fixture_envelope_dict(_team_envelope())
    qapp.processEvents()
    card._lock_refresh_button_metrics()
    qapp.processEvents()
    origin = window.pos()
    width = window.width()
    card._btn_toggle.click()
    animation = card._layout_anim
    assert animation is not None
    for step in (0, animation.duration() // 3, animation.duration()):
        animation.setCurrentTime(step)
        qapp.processEvents()
        assert window.pos() == origin
        assert window.width() == width
    assert card.is_compact() is True
    assert window.pos() == origin
