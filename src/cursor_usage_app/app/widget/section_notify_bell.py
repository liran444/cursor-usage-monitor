"""Per-section usage notification toggle (bell icon)."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QPushButton

from cursor_usage_app.app.widget.colors import active_palette
from cursor_usage_app.app.widget.instant_hint import InstantHint
from cursor_usage_app.app.widget.material_icons import material_icon

_HINT_OFF = "Notify at 50%, 75%, 90%, and 100% usage"
_HINT_ON = "Notifications on (50%, 75%, 90%, 100%)"


class SectionNotifyBell(QPushButton):
    """Dimmed bell when off; bright active bell when notifications are enabled for the section."""

    toggled_enabled = Signal(str, bool)

    def __init__(self, section_id: str, parent=None) -> None:
        super().__init__(parent)
        self._section_id = section_id
        self._hint = InstantHint(self)
        self._hint_text = _HINT_OFF
        self._hint.set_text(self._hint_text)
        self.setObjectName("sectionNotifyBell")
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setIconSize(QSize(18, 18))
        self.setFlat(True)
        self.toggled.connect(self._emit_toggled)
        self.set_notification_enabled(False)

    def section_id(self) -> str:
        return self._section_id

    def apply_active_palette(self) -> None:
        self._hint.apply_active_palette()

    def set_notification_enabled(self, enabled: bool) -> None:
        self.blockSignals(True)
        self.setChecked(enabled)
        self.blockSignals(False)
        self._apply_icon(enabled)

    def _emit_toggled(self, checked: bool) -> None:
        self._apply_icon(checked)
        self.toggled_enabled.emit(self._section_id, checked)

    def _apply_icon(self, enabled: bool) -> None:
        palette = active_palette()
        if enabled:
            self.setIcon(material_icon("notifications_active", palette.bell_active))
            self._hint_text = _HINT_ON
        else:
            self.setIcon(material_icon("notifications", palette.bell_dim))
            self._hint_text = _HINT_OFF
        self._hint.set_text(self._hint_text)

    def enterEvent(self, event) -> None:  # noqa: N802
        self._hint.show_for(self)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._hint.hide()
        super().leaveEvent(event)

    def hideEvent(self, event) -> None:  # noqa: N802
        self._hint.hide()
        super().hideEvent(event)
