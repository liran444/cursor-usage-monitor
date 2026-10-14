"""Widget palettes.

The module-level QColor constants are the dark design-preview colors. The tray
icon keeps using them so it stays readable on a dark taskbar. The floating
window reads ``active_palette()`` and can switch to ``LIGHT``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from PySide6.QtGui import QColor

ThemeName = Literal["dark", "light"]


@dataclass(frozen=True)
class Palette:
    """Hex colors for one widget theme."""

    bg_window: str
    border_window: str
    bg_card: str
    inset_border: str
    border_card: str
    text_primary: str
    section_label: str
    team_label: str
    amount: str
    cyan: str
    violet: str
    green: str
    coral: str
    muted: str
    meta: str
    error: str
    token_bg: str
    token_border: str
    token_text: str
    selection_bg: str
    selection_text: str
    login_error: str
    section_rule: str
    button_bg: str
    button_text: str
    button_border: str
    button_hover: str
    refresh_cooldown_text: str
    refresh_cooldown_bg: str
    refresh_cooldown_border: str
    close_hover: str
    toggle_text: str
    toggle_bg: str
    toggle_border: str
    login_bg: str
    login_text: str
    login_hover: str
    chrome_icon: str
    close_icon: str
    action_icon: str
    team_icon: str
    icon_muted: str
    bell_dim: str
    bell_active: str
    gauge_tag: str
    track: str
    bar_track: str
    popup_bg: str
    popup_border: str
    popup_title: str
    popup_muted: str
    popup_path: str
    popup_radio: str


DARK = Palette(
    bg_window="#2b2b2d",
    border_window="#3a3c3e",
    bg_card="#38393c",
    inset_border="#38393c",
    border_card="#4a4c50",
    text_primary="#f4f4f5",
    section_label="#f2f2f3",
    team_label="#d4d4d6",
    amount="#f7f7f8",
    cyan="#16e7ee",
    violet="#a855f7",
    green="#7dcea0",
    coral="#ee6854",
    muted="#c4c4c6",
    meta="#c8c8ca",
    error="#fca5a5",
    token_bg="#2b2b2d",
    token_border="#52545a",
    token_text="#f4f4f5",
    selection_bg="#16e7ee",
    selection_text="#041316",
    login_error="#ee6854",
    section_rule="#3e4044",
    button_bg="#3a3c3e",
    button_text="#ececee",
    button_border="#52545a",
    button_hover="#45474b",
    refresh_cooldown_text="#7a7a7e",
    refresh_cooldown_bg="#2e3032",
    refresh_cooldown_border="#3a3c3e",
    close_hover="#5c3330",
    toggle_text="#e6d3b0",
    toggle_bg="#6e5c42",
    toggle_border="#8d784f",
    login_bg="#16e7ee",
    login_text="#041316",
    login_hover="#5ef3f8",
    chrome_icon="#c4c4c6",
    close_icon="#e7c4b8",
    action_icon="#ffffff",
    team_icon="#7dcea0",
    icon_muted="#d1d5db",
    bell_dim="#6b6b6e",
    bell_active="#e6d3b0",
    gauge_tag="#c6c6c8",
    track="#4a4a4c",
    bar_track="#2a2c2e",
    popup_bg="#38393c",
    popup_border="#52545a",
    popup_title="#f4f4f5",
    popup_muted="#c4c4c6",
    popup_path="#9a9a9e",
    popup_radio="#ececee",
)

LIGHT = Palette(
    bg_window="#f3f4f6",
    border_window="#d5d8de",
    bg_card="#ffffff",
    inset_border="#e6e8ed",
    border_card="#d8dce3",
    text_primary="#1a1c1f",
    section_label="#1f2126",
    team_label="#3a3d44",
    amount="#16181c",
    cyan="#0e7490",
    violet="#7c3aed",
    green="#18794e",
    coral="#c0362c",
    muted="#5c616b",
    meta="#5e636c",
    error="#b42318",
    token_bg="#ffffff",
    token_border="#cfd3da",
    token_text="#1a1c1f",
    selection_bg="#0e7490",
    selection_text="#ffffff",
    login_error="#c0362c",
    section_rule="#e1e4ea",
    button_bg="#ffffff",
    button_text="#2c2f36",
    button_border="#cfd3da",
    button_hover="#eef0f3",
    refresh_cooldown_text="#8b9098",
    refresh_cooldown_bg="#e7eaee",
    refresh_cooldown_border="#d5d8de",
    close_hover="#f8e4e1",
    toggle_text="#6e5424",
    toggle_bg="#f6edd9",
    toggle_border="#c9ae78",
    login_bg="#0e7490",
    login_text="#ffffff",
    login_hover="#0c6880",
    chrome_icon="#5c616b",
    close_icon="#b4534a",
    action_icon="#000000",
    team_icon="#18794e",
    icon_muted="#4b5058",
    bell_dim="#9aa0a8",
    bell_active="#6e5424",
    gauge_tag="#6a6f78",
    track="#d5d8de",
    bar_track="#e4e7ec",
    popup_bg="#ffffff",
    popup_border="#cfd3da",
    popup_title="#1a1c1f",
    popup_muted="#5c616b",
    popup_path="#8b9098",
    popup_radio="#2c2f36",
)

# Screenshot surround. Not part of either theme's painted card.
BG_OUTER = QColor("#1a1c1e")
BG_WINDOW = QColor(DARK.bg_window)
BORDER_WINDOW = QColor(DARK.border_window)
BG_CARD = QColor(DARK.bg_card)
BORDER_CARD = QColor(DARK.border_card)
TEXT_PRIMARY = QColor(DARK.text_primary)
TEXT_MUTED = QColor("#b7b7b7")
TEXT_DIM = QColor("#8e8e90")
CYAN = QColor(DARK.cyan)
VIOLET = QColor(DARK.violet)
GREEN = QColor(DARK.green)
CORAL = QColor(DARK.coral)
AMBER = QColor(DARK.toggle_text)
TRACK = QColor(DARK.track)
BAR_TRACK = QColor(DARK.bar_track)
BUTTON_BG = QColor(DARK.button_bg)
BUTTON_BORDER = QColor(DARK.button_border)
BUTTON_HOVER = QColor(DARK.button_hover)
BUTTON_GOLD_BG = QColor(DARK.toggle_bg)
BUTTON_GOLD_BORDER = QColor(DARK.toggle_border)
ERROR_TEXT = QColor(DARK.error)

_ACTIVE: ThemeName = "dark"


def active_theme() -> ThemeName:
    return _ACTIVE


def set_active_theme(theme: str) -> None:
    """Select the palette painters and stylesheets read. Unknown values stay dark."""
    global _ACTIVE
    _ACTIVE = "light" if theme == "light" else "dark"


def active_palette() -> Palette:
    if _ACTIVE == "light":
        return LIGHT
    return DARK


def root_stylesheet(palette: Palette | None = None) -> str:
    """Qt stylesheet for the usage card."""
    p = active_palette() if palette is None else palette
    return f"""
#usageRoot {{
    background: transparent;
    color: {p.text_primary};
    font-family: "Segoe UI";
    font-size: 12px;
}}
QLabel {{
    background: transparent;
    border: none;
    color: {p.text_primary};
}}
QLabel#sectionLabel {{
    color: {p.section_label};
    font-size: 13px;
    font-weight: 600;
}}
QLabel#teamLabel {{
    color: {p.team_label};
    font-size: 12px;
    font-weight: 500;
}}
QLabel#sectionTitle {{
    color: {p.text_primary};
    font-size: 14px;
    font-weight: 650;
}}
QLabel#amountLabel {{
    color: {p.amount};
    font-size: 16px;
    font-weight: 700;
}}
QLabel#cyanPercent {{
    color: {p.cyan};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#greenPercent {{
    color: {p.green};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#coralPercent {{
    color: {p.coral};
    font-size: 15px;
    font-weight: 700;
}}
QLabel#onDemandAmount {{
    color: {p.amount};
    font-size: 14px;
    font-weight: 700;
}}
QLabel#onDemandPercent {{
    color: {p.coral};
    font-size: 13px;
    font-weight: 700;
}}
QLabel#mutedLabel {{
    color: {p.muted};
    font-size: 12px;
}}
QLabel#cardTitle {{
    color: {p.text_primary};
    font-size: 13px;
    font-weight: 650;
}}
QLabel#cardFooter {{
    color: {p.text_primary};
    font-size: 13px;
    font-weight: 650;
}}
QLabel#metaLine {{
    color: {p.meta};
    font-size: 11px;
}}
QLabel#inlineError {{
    color: {p.error};
    font-size: 11px;
}}
QLineEdit#tokenInput {{
    background-color: {p.token_bg};
    color: {p.token_text};
    border: 1px solid {p.token_border};
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 12px;
    selection-background-color: {p.selection_bg};
    selection-color: {p.selection_text};
}}
QLabel#loginError {{
    color: {p.login_error};
    font-size: 12px;
    font-weight: 600;
}}
QFrame#insetCard {{
    background-color: {p.bg_card};
    border: 1px solid {p.inset_border};
    border-radius: 10px;
}}
QFrame#onDemandCard {{
    background-color: {p.bg_card};
    border: 1px solid {p.border_card};
    border-radius: 10px;
}}
QFrame#insetCard QLabel, QFrame#onDemandCard QLabel {{
    border: none;
    background: transparent;
}}
QWidget#sectionRule {{
    background-color: {p.section_rule};
    border: none;
    min-height: 1px;
    max-height: 1px;
}}
QPushButton {{
    background-color: {p.button_bg};
    color: {p.button_text};
    border: 1px solid {p.button_border};
    border-radius: 8px;
    padding: 4px 8px;
    font-size: 11px;
    min-height: 26px;
}}
QPushButton:hover {{
    background-color: {p.button_hover};
}}
QPushButton#refreshButton:disabled[refreshState="loading"] {{
    color: {p.button_text};
    background-color: {p.button_bg};
    border-color: {p.button_border};
}}
QPushButton#refreshButton:disabled[refreshState="cooldown"] {{
    color: {p.refresh_cooldown_text};
    background-color: {p.refresh_cooldown_bg};
    border-color: {p.refresh_cooldown_border};
}}
QPushButton#windowChromeButton, QPushButton#windowCloseButton,
QPushButton#sectionNotifyBell {{
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 2px;
    min-width: 24px;
    max-width: 24px;
    min-height: 22px;
    max-height: 22px;
}}
QPushButton#sectionNotifyBell:hover {{
    background-color: {p.button_hover};
}}
QPushButton#windowChromeButton:hover {{
    background-color: {p.button_hover};
}}
QPushButton#windowCloseButton:hover {{
    background-color: {p.close_hover};
}}
QPushButton#toggleButton {{
    color: {p.toggle_text};
    background-color: {p.toggle_bg};
    border: 1px solid {p.toggle_border};
    font-weight: 650;
    padding: 4px 10px;
}}
QPushButton#loginButton {{
    color: {p.login_text};
    background-color: {p.login_bg};
    border: 1px solid {p.login_bg};
    font-weight: 700;
}}
QPushButton#loginButton:hover {{
    background-color: {p.login_hover};
}}
"""


def popup_stylesheet(palette: Palette | None = None) -> str:
    """Qt stylesheet for the settings popup."""
    p = active_palette() if palette is None else palette
    return f"""
#traySettingsPopup {{
    background-color: {p.popup_bg};
    border: 1px solid {p.popup_border};
    border-radius: 10px;
}}
#traySettingsPopup QLabel {{
    background: transparent;
    border: none;
    color: {p.popup_title};
}}
#traySettingsPopup QLabel#sectionTitle {{
    font-size: 14px;
    font-weight: 600;
}}
#traySettingsPopup QLabel#mutedLabel {{
    color: {p.popup_muted};
    font-size: 11px;
}}
#traySettingsPopup QLabel#settingsPathLabel {{
    color: {p.popup_path};
    font-size: 10px;
}}
#traySettingsPopup QRadioButton {{
    color: {p.popup_radio};
    font-size: 12px;
    spacing: 6px;
    padding-left: 4px;
}}
#traySettingsPopup QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    margin-left: 2px;
}}
"""
