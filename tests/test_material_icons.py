"""Material icon rasterization (explicit colors, not app palette defaults)."""

import os

import pytest

from cursor_usage_app.app.widget.colors import DARK, LIGHT, set_active_theme
from cursor_usage_app.app.widget.material_icons import material_pixmap

pytestmark = pytest.mark.skipif(
    os.environ.get("CURSOR_USAGE_SKIP_GUI") == "1",
    reason="GUI tests skipped",
)


def _mean_rgb(pixmap) -> tuple[float, float, float]:
    image = pixmap.toImage()
    total_r = 0.0
    total_g = 0.0
    total_b = 0.0
    count = 0
    for y in range(image.height()):
        for x in range(image.width()):
            color = image.pixelColor(x, y)
            if color.alpha() < 128:
                continue
            total_r += color.red()
            total_g += color.green()
            total_b += color.blue()
            count += 1
    if count == 0:
        return (0.0, 0.0, 0.0)
    return (total_r / count, total_g / count, total_b / count)


@pytest.fixture
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_refresh_icon_uses_explicit_black_on_light_theme(qapp) -> None:
    set_active_theme("light")
    pixmap = material_pixmap("refresh", LIGHT.action_icon, size=18)
    red, green, blue = _mean_rgb(pixmap)
    assert red < 80.0
    assert green < 80.0
    assert blue < 80.0


def test_refresh_icon_uses_explicit_white_on_dark_theme(qapp) -> None:
    set_active_theme("dark")
    pixmap = material_pixmap("refresh", DARK.action_icon, size=18)
    red, green, blue = _mean_rgb(pixmap)
    assert red > 200.0
    assert green > 200.0
    assert blue > 200.0


def test_team_icon_darkens_for_light_theme(qapp) -> None:
    dark_pm = material_pixmap("group", DARK.team_icon, size=16)
    light_pm = material_pixmap("group", LIGHT.team_icon, size=16)
    dark_mean = sum(_mean_rgb(dark_pm))
    light_mean = sum(_mean_rgb(light_pm))
    assert light_mean < dark_mean
