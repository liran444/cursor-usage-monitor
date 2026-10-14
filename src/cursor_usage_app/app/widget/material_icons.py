"""Google Material Symbols as QIcons (via qt-material-icons)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QIcon, QPixmap

from qt_material_icons import MaterialIcon

# qt-material-icons ships outlined assets at 20, 24, 40, and 48 px only.
_ICON_ASSET_SIZE = 20


def _asset_size_for_render(size: int) -> int:
    if size in (20, 24, 40, 48):
        return size
    return _ICON_ASSET_SIZE


def _coerce_color(color: QColor | str) -> QColor:
    if isinstance(color, str):
        return QColor(color)
    return color


def _colored_pixmap(name: str, color: QColor | str, *, size: int) -> QPixmap:
    """Rasterize a symbol with an explicit fill (not the app palette default)."""
    asset_size = _asset_size_for_render(size)
    icon = MaterialIcon(name, size=asset_size)
    return icon.pixmap(size, color=_coerce_color(color))


def material_icon(
    name: str,
    color: QColor | str | None = None,
    *,
    size: int = _ICON_ASSET_SIZE,
) -> QIcon:
    asset_size = _asset_size_for_render(size)
    icon = MaterialIcon(name, size=asset_size)
    if color is None:
        return icon
    qcolor = _coerce_color(color)
    for mode in (
        QIcon.Mode.Normal,
        QIcon.Mode.Disabled,
        QIcon.Mode.Active,
        QIcon.Mode.Selected,
    ):
        icon.set_color(qcolor, mode, QIcon.State.Off)
    return icon


def material_pixmap(
    name: str,
    color: QColor | str,
    *,
    size: int = 16,
) -> QPixmap:
    return _colored_pixmap(name, color, size=size)
