"""Per-section usage notification toggle (bell icon)."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QPushButton

from cursor_usage_app.app.widget import colors
from cursor_usage_app.app.widget.material_icons import material_icon

_BELL_DIM_COLOR = "#6b6b6e"
_BELL_ACTIVE_COLOR = colors.AMBER


class SectionNotifyBell(QPushButton):
    """Dimmed bell when off; bright active bell when notifications are enabled for the section."""

    toggled_enabled = Signal(str, bool)

    def __init__(self, section_id: str, parent=None) -> None:
        super().__init__(parent)
        self._section_id = section_id
        self.setObjectName("sectionNotifyBell")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Notify at 50%, 75%, 90%, and 100% usage")
        self.setIconSize(QSize(18, 18))
        self.setFlat(True)
        self.toggled.connect(self._emit_toggled)
        self.set_notification_enabled(False)

    def section_id(self) -> str:
        return self._section_id

    def set_notification_enabled(self, enabled: bool) -> None:
        self.blockSignals(True)
        self.setChecked(enabled)
        self.blockSignals(False)
        self._apply_icon(enabled)

    def _emit_toggled(self, checked: bool) -> None:
        self._apply_icon(checked)
        self.toggled_enabled.emit(self._section_id, checked)

    def _apply_icon(self, enabled: bool) -> None:
        if enabled:
            self.setIcon(material_icon("notifications_active", _BELL_ACTIVE_COLOR))
            self.setToolTip("Notifications on (50%, 75%, 90%, 100%)")
            return
        self.setIcon(material_icon("notifications", _BELL_DIM_COLOR))
        self.setToolTip("Notify at 50%, 75%, 90%, and 100% usage")
