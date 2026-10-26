import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_bonus_info_hint_stays_in_the_same_window(qapp) -> None:
    from cursor_usage_app.app.widget.instant_info_button import InstantInfoButton

    button = InstantInfoButton()
    button.set_hint("Used bonus credit · $41.81 total pool")
    button.enterEvent(None)
    assert button._hint.isWindow() is False


def test_notify_bell_hint_stays_in_the_same_window(qapp) -> None:
    from cursor_usage_app.app.widget.section_notify_bell import SectionNotifyBell

    bell = SectionNotifyBell("personal")
    bell.enterEvent(None)
    assert bell._hint.isWindow() is False
