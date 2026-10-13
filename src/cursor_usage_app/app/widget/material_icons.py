"""Google Material Symbols as QIcons (via qt-material-icons)."""

from __future__ import annotations

from PySide6.QtGui import QColor, QIcon, QPixmap

from qt_material_icons import MaterialIcon

# qt-material-icons ships outlined assets at 20, 24, 40, and 48 px only.
_ICON_ASSET_SIZE = 20


def material_icon(
    name: str,
    color: QColor | str | None = None,
    *,
    size: int = _ICON_ASSET_SIZE,
) -> QIcon:
    if size not in (20, 24, 40, 48):
        size = _ICON_ASSET_SIZE
    icon = MaterialIcon(name, size=size)
    if color is not None:
        if isinstance(color, str):
            color = QColor(color)
        icon.set_color(color)
    return icon


def material_pixmap(
    name: str,
    color: QColor | str,
    *,
    size: int = 16,
) -> QPixmap:
    icon = material_icon(name, color)
    return icon.pixmap(size, size)
