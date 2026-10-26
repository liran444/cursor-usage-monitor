"""Main usage card content."""

from __future__ import annotations

import webbrowser
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QEvent,
    QPoint,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPixmap, QTextDocument
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from cursor_usage_app.app.widget.appearance_theme import (
    apply_theme_preference,
    applied_theme_matches_preference,
)
from cursor_usage_app.app.widget.colors import active_palette, active_theme, root_stylesheet
from cursor_usage_app.app.widget.fetch_worker import load_cache, start_fetch_in_thread
from cursor_usage_app.app.widget.formatting import (
    format_datetime_display,
    format_percent,
    format_personal_bonus_chip,
    format_personal_bonus_tooltip,
    format_pool_percent,
    format_usd,
)
from cursor_usage_app.app.widget.gauge_widget import DonutGauge, MiniTotalGauge, SegmentedTotalGauge
from cursor_usage_app.app.widget.instant_info_button import InstantInfoButton
from cursor_usage_app.app.widget.material_icons import material_icon, material_pixmap
from cursor_usage_app.app.widget.progress_bar import HorizontalBar
from cursor_usage_app.app.widget.opacity_fade import OpacityFader
from cursor_usage_app.app.widget.reveal_clip import TopClip, TrailingSlot
from cursor_usage_app.app.widget.section_notify_bell import SectionNotifyBell
from cursor_usage_app.app.widget.tray_settings_popup import TraySettingsPopup
from cursor_usage_app.app.widget.view_model import (
    WidgetViewModel,
    shows_browser_login,
    view_model_from_envelope,
    view_model_loading,
)
from cursor_usage_app.auth.browser_import import (
    BrowserImportBusyError,
    BrowserImportError,
    import_session_token_from_browsers,
    is_retryable_import_error,
    set_browser_login_flow_active,
)
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.auth.token_normalize import TokenNormalizeError, normalize_session_token
from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeOk, parse_cache_envelope
from cursor_usage_app.domain.models import UsageSnapshot
from cursor_usage_app.settings.app_settings import ThemeId, load_app_settings, mutate_app_settings
from cursor_usage_app.usage_notifications import (
    acknowledge_thresholds,
    notification_state_for_cycle,
    thresholds_already_reached,
    usage_percent_for_section,
)

_WIDGET_WIDTH = 320
_LOGIN_WIDGET_WIDTH = 380
_FULL_HEIGHT = 620
_COMPACT_HEIGHT = 230
_LOGIN_CARD_MARGINS = (12, 10, 12, 10)
_LOGIN_CARD_SPACING = 8
_TOKEN_CARD_MARGINS = (12, 8, 12, 8)
_TOKEN_CARD_SPACING = 6
_LOGIN_ROOT_SPACING = 8
_DASHBOARD_URL = "https://cursor.com/dashboard/usage"
_LOGIN_URL = "https://cursor.com/login"
_LOGIN_POLL_MS = 5000
_LOGIN_FIRST_IMPORT_MS = 1500
_LOGIN_WAIT_MS = 120_000
_MANUAL_REFRESH_COOLDOWN_MS = 5000
_REFRESH_DIM_OPACITY = 0.42
_DATA_DIM_OPACITY = 0.35
_OPACITY_FADE_MS = 300
_LAYOUT_TRANSITION_MS = 420
_LAYOUT_TRANSITION_MIN_MS = 160
_ACTION_BUTTON_GAP = 6
_STATIC_ANIM_SECTION_ATTRS = (
    "_personal_card",
    "_loading_card",
    "_login_card",
    "_token_panel",
    "_btn_token",
    "_rule_before_actions",
    "_action_row",
)
_BUSY_SPINNER_INTERVAL_MS = 70
_CARD_SECTION_INSET_MARGINS = (8, 10, 8, 10)
_SECTION_INSET_MARGINS = (8, 2, 8, 2)
_QT_MAX = 16777215


@dataclass(frozen=True)
class _LayoutMetrics:
    """Heights captured once per transition so frames do not re-measure the tree."""

    content_width: int
    details_h: int
    compact_h: int
    meta_h: int
    expanded_height: int
    compact_height: int


class UsageWidget(QWidget):
    """Usage monitor card; supports full and compact layouts."""

    hide_requested = Signal()
    minimize_requested = Signal()
    compact_changed = Signal(bool)
    tray_settings_changed = Signal()
    cache_or_session_changed = Signal()
    _login_imported = Signal(str)
    _login_import_failed = Signal(object)
    _login_import_idle = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        cache_path: Path | None = None,
        store: SessionStore | None = None,
    ) -> None:
        super().__init__(parent)
        self._cache_path = cache_path
        self._store = store or SessionStore()
        self._compact = False
        self._view_model = view_model_from_envelope(None)
        self._fetch_thread = None
        self._login_waiting = False
        self._login_busy = False
        self._login_verify_pending = False
        self._prepare_shutdown_done = False
        self._login_deadline_ms = 0
        self._activation_hooked = False
        self._login_timer = QTimer(self)
        self._login_timer.setInterval(_LOGIN_POLL_MS)
        self._login_timer.timeout.connect(self._attempt_browser_import)
        self._spinner_index = 0
        self._login_spinner_timer = QTimer(self)
        self._login_spinner_timer.setInterval(_BUSY_SPINNER_INTERVAL_MS)
        self._login_spinner_timer.timeout.connect(self._advance_login_spinner)
        self._refresh_busy = False
        self._content_busy = False
        self._busy_index = 0
        self._busy_timer = QTimer(self)
        self._busy_timer.setInterval(_BUSY_SPINNER_INTERVAL_MS)
        self._busy_timer.timeout.connect(self._advance_busy_spinner)
        self._login_imported.connect(self._on_import_success)
        self._login_import_failed.connect(self._on_import_error)
        self._login_import_idle.connect(self._clear_login_import_busy)
        self._refresh_metrics_locked = False
        self._app_settings = load_app_settings()
        apply_theme_preference(self._app_settings.theme)
        self._refresh_frames: list[QIcon] = []
        self._content_frames: list[QIcon] = []
        self._login_spinner_frames: list[QIcon] = []
        self._settings_popup: TraySettingsPopup | None = None
        self._suppress_settings_open = False
        self._manual_refresh_cooldown = False
        self._refresh_cooldown_timer = QTimer(self)
        self._refresh_cooldown_timer.setSingleShot(True)
        self._refresh_cooldown_timer.timeout.connect(self._end_manual_refresh_cooldown)
        self._opacity_fader = OpacityFader(_OPACITY_FADE_MS)
        self._layout_progress = 0.0
        self._layout_anim: QVariantAnimation | None = None
        self._layout_retargeting = False
        self._applying_layout = False
        self._toggle_width_locked = False
        self._chevron_degrees = 0.0
        self._chevron_base: QPixmap | None = None
        self._chevron_base_key: str | None = None
        self._layout_metrics: _LayoutMetrics | None = None
        self._transition_followers: list[tuple[QWidget, int]] = []
        self._summary_rest_height = 0
        self._notify_bells_by_section: dict[str, list[SectionNotifyBell]] = {}
        self._system_theme_listener_hooked = False

        self.setObjectName("usageRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(_WIDGET_WIDTH)
        self._build_ui()
        self.reload_from_cache()

    def is_compact(self) -> bool:
        return self._compact

    def set_compact(self, compact: bool) -> None:
        """Snap to a layout. The collapse button animates; callers that set state do not."""
        at_rest = abs(self._layout_progress - (1.0 if compact else 0.0)) < 0.001
        if self._compact == compact and at_rest and not self._layout_transition_running():
            return
        self._stop_layout_transition()
        self._thaw_layout_after_transition()
        self._layout_metrics = None
        self._release_static_root_sections()
        self._compact = compact
        self._layout_progress = 1.0 if compact else 0.0
        self._apply_compact_visibility()
        self._update_toggle_button()
        self.compact_changed.emit(compact)
        self._resize_to_mode()

    def toggle_compact(self) -> None:
        target = not self._compact
        if (not self.isVisible()) or self._prefers_reduced_motion():
            self.set_compact(target)
            return
        self._lock_toggle_button_width()
        self._compact = target
        self._update_toggle_button()
        if self._layout_metrics is None:
            self._refresh_layout_metrics()
        self._freeze_layout_for_transition()
        self._start_layout_transition()

    def reload_from_cache(self) -> None:
        envelope = load_cache(self._cache_path)
        self.apply_envelope(envelope)

    def apply_envelope(self, envelope: CacheEnvelope | None) -> None:
        self._view_model = view_model_from_envelope(envelope)
        self._render_view_model()

    def load_fixture_file(self, path: Path) -> None:
        """Load a cache envelope or a raw usage-summary API payload."""
        import json

        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "ok" not in raw and "individualUsage" in raw:
            from cursor_usage_app.cache.usage_cache import CacheEnvelopeOk, utc_now_iso
            from cursor_usage_app.domain.mapper import UsageSummaryMapper

            snapshot = UsageSummaryMapper.from_api_payload(raw)
            self.apply_envelope(CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso()))
            return
        envelope = parse_cache_envelope(raw)
        self.apply_envelope(envelope)

    def apply_fixture_envelope_dict(self, raw: dict) -> None:
        envelope = parse_cache_envelope(raw)
        self.apply_envelope(envelope)

    def _on_manual_refresh_clicked(self) -> None:
        if not self._btn_refresh.isEnabled():
            return
        self._manual_refresh_cooldown = True
        self._set_refresh_button_state("loading")
        self.refresh()

    def refresh(self) -> None:
        if self._view_model.phase == "loading":
            return
        self._view_model = view_model_loading(self._view_model)
        self._render_view_model()
        self._fetch_thread = start_fetch_in_thread(
            self,
            cache_path=self._cache_path,
            store=self._store,
            on_finished=self._on_fetch_finished,
        )

    def _open_dashboard(self) -> None:
        webbrowser.open(_DASHBOARD_URL)

    def preferred_width(self) -> int:
        if self._needs_browser_login():
            return _LOGIN_WIDGET_WIDTH
        return _WIDGET_WIDTH

    def preferred_height(self) -> int:
        if self._layout_metrics is not None:
            return self._animated_content_height()
        if self.layout() is None:
            return _COMPACT_HEIGHT if self._compact else _FULL_HEIGHT
        self.ensurePolished()
        return self._measure_root_layout_height()

    def _measure_root_layout_height(self) -> int:
        """Natural content height; temporarily ignores a prior setFixedSize on this widget."""
        layout = self._root_layout
        if layout is None:
            return _COMPACT_HEIGHT if self._compact else _FULL_HEIGHT
        width = self.preferred_width()
        saved_min_h = self.minimumHeight()
        saved_max_h = self.maximumHeight()
        saved_w = self.width()
        saved_h = self.height()
        fixed_size = saved_min_h == saved_max_h and saved_max_h < _QT_MAX
        self.setMinimumHeight(0)
        self.setMaximumHeight(_QT_MAX)
        if saved_w != width:
            self.setFixedWidth(width)
        self._pin_wrapped_labels()
        if self._needs_browser_login():
            height = self._measure_browser_login_height()
        else:
            layout.invalidate()
            layout.activate()
            height = layout.sizeHint().height()
        if fixed_size and saved_w > 0 and saved_h > 0:
            self.setFixedSize(saved_w, saved_h)
        else:
            self.setMinimumHeight(saved_min_h)
            self.setMaximumHeight(saved_max_h)
            if saved_w > 0 and saved_h > 0:
                self.resize(saved_w, saved_h)
        return height

    def _frame_layout_height(self, frame: QFrame) -> int:
        card_layout = frame.layout()
        if card_layout is None:
            return max(0, frame.sizeHint().height())
        card_layout.invalidate()
        card_layout.activate()
        return max(0, card_layout.sizeHint().height())

    def _measure_browser_login_height(self) -> int:
        """Sum login chrome explicitly; root sizeHint is wrong before the window is shown."""
        root = self._root_layout
        margins = root.contentsMargins()
        spacing = root.spacing()
        total = margins.top() + margins.bottom()
        blocks: list[int] = []

        chrome = root.itemAt(0).layout()
        if chrome is not None:
            chrome.invalidate()
            chrome.activate()
            blocks.append(max(0, chrome.sizeHint().height()))

        if (not self._inline_error.isHidden()) and self._inline_error.text().strip() != "":
            blocks.append(self._inline_error.sizeHint().height())
        if not self._loading_card.isHidden():
            blocks.append(self._frame_layout_height(self._loading_card))

        blocks.append(self._frame_layout_height(self._login_card))
        blocks.append(self._rule_before_actions.sizeHint().height())
        # isVisible() is false for the whole tree while the window is hidden; isHidden() reflects .show().
        if not self._token_panel.isHidden():
            blocks.append(self._frame_layout_height(self._token_panel))
        blocks.append(self._btn_token.sizeHint().height())

        for index, block_h in enumerate(blocks):
            total += block_h
            if index > 0:
                total += spacing
        return total

    def _animated_content_height(self) -> int:
        """Linear height between the two measured rest states. No layout pass."""
        metrics = self._layout_metrics
        if metrics is None:
            return self.preferred_height()
        progress = self._layout_progress
        if progress <= 0.0:
            return metrics.expanded_height
        if progress >= 1.0:
            return metrics.compact_height
        span = metrics.compact_height - metrics.expanded_height
        return int(round(metrics.expanded_height + (span * progress)))

    def _layout_height_after_clips(self) -> int:
        """Height implied by clip widgets only; skips label pinning used at rest."""
        root = self._root_layout
        root.invalidate()
        root.activate()
        return root.sizeHint().height()

    def _clear_wrapped_label_pins(self) -> None:
        labels = (
            self._login_body,
            self._login_status,
            self._login_error,
            self._token_hint,
            self._token_error,
        )
        for label in labels:
            label.setProperty("_wrap_pin", None)
            label.setMinimumHeight(0)
            label.setMaximumHeight(_QT_MAX)

    def _pin_wrapped_labels(self) -> None:
        """Keep wrapped labels at text height so leftover window space cannot open gaps inside cards."""
        width = self._wrapped_text_width()
        labels = (
            self._login_body,
            self._login_status,
            self._login_error,
            self._token_hint,
            self._token_error,
        )
        for label in labels:
            # isHidden(), not isVisible(): a hidden window makes every child
            # "not visible", which was clearing the pin before the first paint.
            if label.isHidden() or label.text().strip() == "":
                if label.property("_wrap_pin") is None and label.maximumHeight() == 16777215:
                    continue
                label.setProperty("_wrap_pin", None)
                label.setMinimumHeight(0)
                label.setMaximumHeight(16777215)
                continue
            text_height = self._wrapped_label_height(label, width)
            pin_key = (label.text(), width, text_height)
            if label.property("_wrap_pin") == pin_key:
                continue
            label.setProperty("_wrap_pin", pin_key)
            label.setMinimumHeight(text_height)
            label.setMaximumHeight(text_height)

    def _wrapped_text_width(self) -> int:
        root_left, _, root_right, _ = self.layout().getContentsMargins()
        card_left, _, card_right, _ = self._login_card.layout().getContentsMargins()
        # Stylesheet border is not included in frameWidth(); the laid-out label is 2px narrower.
        border = 2
        return max(
            1,
            self.preferred_width() - root_left - root_right - card_left - card_right - border,
        )

    def _wrapped_label_height(self, label: QLabel, body_width: int) -> int:
        text = label.text().strip()
        if text == "":
            return 0
        label.ensurePolished()
        rect = label.fontMetrics().boundingRect(
            0,
            0,
            body_width,
            10_000,
            int(Qt.TextFlag.TextWordWrap),
            text,
        )
        doc = QTextDocument()
        doc.setDefaultFont(label.font())
        doc.setTextWidth(float(body_width))
        doc.setPlainText(text)
        doc_height = int(doc.size().height())
        label.setWordWrap(True)
        for_width = label.heightForWidth(body_width)
        height = max(rect.height(), doc_height, for_width)
        return height + (label.margin() * 2)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        self._root_layout = root
        root.setSpacing(8)

        self._btn_settings = _icon_tool_button(
            QIcon(),
            "Settings",
            object_name="windowChromeButton",
        )
        self._btn_minimize = _icon_tool_button(
            QIcon(),
            "Minimize",
            object_name="windowChromeButton",
        )
        self._btn_quit = _icon_tool_button(
            QIcon(),
            "Hide",
            object_name="windowCloseButton",
        )
        chrome_row = QHBoxLayout()
        chrome_row.setContentsMargins(0, 0, 0, 0)
        chrome_row.setSpacing(2)
        chrome_row.addWidget(self._btn_settings)
        chrome_row.addStretch()
        chrome_row.addWidget(self._btn_minimize)
        chrome_row.addWidget(self._btn_quit)
        root.addLayout(chrome_row)

        self._inline_error = QLabel()
        self._inline_error.setObjectName("inlineError")
        self._inline_error.setWordWrap(True)
        self._inline_error.hide()
        root.addWidget(self._inline_error)

        self._loading_card = QFrame()
        self._loading_card.setObjectName("insetCard")
        loading_layout = QVBoxLayout(self._loading_card)
        loading_layout.setContentsMargins(12, 28, 12, 28)
        loading_layout.setSpacing(10)
        self._loading_icon = QLabel()
        self._loading_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(self._loading_icon)
        loading_caption = QLabel("Loading usage")
        loading_caption.setObjectName("mutedLabel")
        loading_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_layout.addWidget(loading_caption)
        self._loading_card.hide()
        root.addWidget(self._loading_card)

        self._login_card = QFrame()
        self._login_card.setObjectName("insetCard")
        self._login_card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        login_layout = QVBoxLayout(self._login_card)
        login_layout.setContentsMargins(*_LOGIN_CARD_MARGINS)
        login_layout.setSpacing(_LOGIN_CARD_SPACING)
        login_title = QLabel("Sign in to Cursor")
        login_title.setObjectName("sectionTitle")
        login_title.setContentsMargins(0, 0, 0, 0)
        login_layout.addWidget(login_title)
        self._login_body = QLabel(
            "Sign in at cursor.com in any browser you use, then return here. "
            "Automatic import often fails (Windows Chromium encryption, macOS permissions, "
            "Linux keyring)—use Set token below if import does not work."
        )
        self._login_body.setObjectName("mutedLabel")
        self._login_body.setWordWrap(True)
        self._login_body.setContentsMargins(0, 0, 0, 0)
        login_layout.addWidget(self._login_body)
        self._btn_login = _pill_button("Log in to Cursor")
        self._btn_login.setObjectName("loginButton")
        self._btn_login.clicked.connect(self._start_browser_login)
        login_layout.addWidget(self._btn_login)
        self._btn_login.setMinimumWidth(self._btn_login.sizeHint().width())
        self._login_status = QLabel()
        self._login_status.setObjectName("mutedLabel")
        self._login_status.setWordWrap(True)
        self._login_status.hide()
        login_layout.addWidget(self._login_status)
        self._login_error = QLabel()
        self._login_error.setObjectName("loginError")
        self._login_error.setWordWrap(True)
        self._login_error.hide()
        login_layout.addWidget(self._login_error)
        self._login_card.hide()
        root.addWidget(self._login_card)

        self._personal_card = QFrame()
        self._personal_card.setObjectName("insetCard")
        personal_layout = QVBoxLayout(self._personal_card)
        personal_layout.setContentsMargins(*_CARD_SECTION_INSET_MARGINS)
        personal_layout.setSpacing(4)

        personal_header_row = QHBoxLayout()
        personal_header_row.setContentsMargins(0, 0, 0, 0)
        personal_header_row.setSpacing(4)
        self._personal_icon = QLabel()
        self._personal_icon.setFixedSize(16, 16)
        personal_header_row.addWidget(self._personal_icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._personal_header = QLabel("Personal")
        self._personal_header.setObjectName("sectionLabel")
        personal_header_row.addWidget(self._personal_header)
        personal_header_row.addStretch()
        self._bell_personal = self._make_notify_bell("personal")
        personal_header_row.addWidget(self._bell_personal)
        personal_layout.addLayout(personal_header_row)

        personal_row = QHBoxLayout()
        personal_row.setSpacing(8)
        self._personal_amount = QLabel()
        self._personal_amount.setObjectName("amountLabel")
        self._personal_pct = QLabel()
        self._personal_pct.setObjectName("cyanPercent")
        personal_row.addWidget(self._personal_amount)
        bonus_cluster = QWidget()
        bonus_cluster_layout = QHBoxLayout(bonus_cluster)
        bonus_cluster_layout.setContentsMargins(0, 0, 0, 0)
        bonus_cluster_layout.setSpacing(2)
        self._personal_bonus = QLabel()
        self._personal_bonus.setObjectName("bonusChip")
        self._personal_bonus.hide()
        bonus_cluster_layout.addWidget(self._personal_bonus, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._personal_bonus_info = InstantInfoButton()
        bonus_cluster_layout.addWidget(self._personal_bonus_info, alignment=Qt.AlignmentFlag.AlignVCenter)
        personal_row.addWidget(bonus_cluster, alignment=Qt.AlignmentFlag.AlignVCenter)
        personal_row.addStretch()
        personal_row.addWidget(self._personal_pct)
        personal_layout.addLayout(personal_row)

        self._personal_bar = HorizontalBar(QColor(active_palette().cyan))
        personal_layout.addWidget(self._personal_bar)
        root.addWidget(self._personal_card)

        self._rule_before_team = _section_rule()

        # Compact mini total
        self._compact_total_row = QWidget()
        compact_layout = QHBoxLayout(self._compact_total_row)
        compact_layout.setContentsMargins(*_SECTION_INSET_MARGINS)
        total_caption = QLabel("TOTAL")
        total_caption.setObjectName("mutedLabel")
        compact_layout.addWidget(total_caption)
        self._mini_total = MiniTotalGauge()
        compact_layout.addWidget(self._mini_total)
        compact_layout.addStretch()
        self._bell_plan_total_compact = self._make_notify_bell("plan_total")
        compact_layout.addWidget(self._bell_plan_total_compact)
        self._compact_total_pct = QLabel()
        self._compact_total_pct.setObjectName("amountLabel")
        compact_layout.addWidget(self._compact_total_pct)

        # Team
        self._team_block = QWidget()
        team_layout = QVBoxLayout(self._team_block)
        team_layout.setContentsMargins(*_SECTION_INSET_MARGINS)
        team_layout.setSpacing(2)
        team_header_row = QHBoxLayout()
        team_header_row.setContentsMargins(0, 0, 0, 0)
        team_header_row.setSpacing(4)
        self._team_icon = QLabel()
        self._team_icon.setFixedSize(16, 16)
        team_header_row.addWidget(self._team_icon, alignment=Qt.AlignmentFlag.AlignVCenter)
        self._team_header = QLabel("Team")
        self._team_header.setObjectName("teamLabel")
        team_header_row.addWidget(self._team_header)
        team_header_row.addStretch()
        self._bell_team = self._make_notify_bell("team")
        team_header_row.addWidget(self._bell_team)
        team_layout.addLayout(team_header_row)
        team_row = QHBoxLayout()
        team_row.setSpacing(6)
        self._team_amount = QLabel()
        self._team_amount.setObjectName("amountLabel")
        self._team_pct = QLabel()
        self._team_pct.setObjectName("greenPercent")
        team_row.addWidget(self._team_amount)
        team_row.addStretch()
        team_row.addWidget(self._team_pct)
        team_layout.addLayout(team_row)

        self._rule_before_gauges = _section_rule()

        # Gauges
        self._gauge_block = QWidget()
        gauge_outer = QVBoxLayout(self._gauge_block)
        gauge_outer.setContentsMargins(*_SECTION_INSET_MARGINS)
        gauge_outer.setSpacing(10)
        gauge_header_row = QHBoxLayout()
        gauge_header_row.setContentsMargins(0, 0, 0, 0)
        gauge_header_row.setSpacing(4)
        gauge_title = QLabel("Personal Usage Breakdown")
        gauge_title.setObjectName("sectionTitle")
        gauge_header_row.addWidget(gauge_title)
        gauge_header_row.addStretch()
        self._bell_plan_total = self._make_notify_bell("plan_total")
        gauge_header_row.addWidget(self._bell_plan_total)
        gauge_outer.addLayout(gauge_header_row)

        gauge_row = QHBoxLayout()
        gauge_row.setSpacing(10)
        self._total_gauge = SegmentedTotalGauge()
        palette = active_palette()
        self._api_gauge = DonutGauge("API", QColor(palette.api_gauge))
        self._auto_gauge = DonutGauge("AUTO", QColor(palette.violet))
        gauge_row.addStretch(1)
        gauge_row.addWidget(self._total_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gauge_row.addWidget(self._api_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gauge_row.addWidget(self._auto_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gauge_row.addStretch(1)
        gauge_outer.addLayout(gauge_row)

        self._rule_before_on_demand = _section_rule()

        # On demand card
        self._on_demand_card = QFrame()
        self._on_demand_card.setObjectName("onDemandCard")
        od_layout = QVBoxLayout(self._on_demand_card)
        od_layout.setContentsMargins(*_CARD_SECTION_INSET_MARGINS)
        od_layout.setSpacing(5)
        od_header = QHBoxLayout()
        od_title = QLabel("On Demand Usage")
        od_title.setObjectName("cardTitle")
        od_header.addWidget(od_title)
        od_header.addStretch()
        self._bell_on_demand = self._make_notify_bell("on_demand")
        od_header.addWidget(self._bell_on_demand)
        od_layout.addLayout(od_header)
        od_usage_row = QHBoxLayout()
        od_usage_row.setSpacing(8)
        self._od_amount = QLabel()
        self._od_amount.setObjectName("onDemandAmount")
        self._od_pct = QLabel()
        self._od_pct.setObjectName("onDemandPercent")
        od_usage_row.addWidget(self._od_amount)
        od_usage_row.addStretch()
        od_usage_row.addWidget(self._od_pct)
        od_layout.addLayout(od_usage_row)
        self._od_bar = HorizontalBar(QColor(active_palette().coral))
        od_layout.addWidget(self._od_bar)

        self._rule_before_actions = _section_rule()
        root.addWidget(self._rule_before_actions)

        self._token_panel = QFrame()
        self._token_panel.setObjectName("insetCard")
        self._token_panel.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        token_layout = QVBoxLayout(self._token_panel)
        token_layout.setContentsMargins(*_TOKEN_CARD_MARGINS)
        token_layout.setSpacing(_TOKEN_CARD_SPACING)
        token_title = QLabel("Session token")
        token_title.setObjectName("sectionTitle")
        token_title.setContentsMargins(0, 0, 0, 0)
        token_layout.addWidget(token_title)
        self._token_hint = QLabel(
            "Paste WorkosCursorSessionToken from DevTools → Application → Cookies → cursor.com."
        )
        self._token_hint.setObjectName("mutedLabel")
        self._token_hint.setWordWrap(True)
        self._token_hint.setContentsMargins(0, 0, 0, 0)
        token_layout.addWidget(self._token_hint)
        self._token_input = QLineEdit()
        self._token_input.setObjectName("tokenInput")
        self._token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._token_input.setPlaceholderText("Session token")
        self._token_input.returnPressed.connect(self._save_inline_token)
        token_layout.addWidget(self._token_input)
        token_actions = QHBoxLayout()
        token_actions.setSpacing(6)
        self._btn_token_save = _pill_button("Save")
        self._btn_token_save.setObjectName("loginButton")
        self._btn_token_cancel = _pill_button("Cancel")
        token_actions.addWidget(self._btn_token_save)
        token_actions.addWidget(self._btn_token_cancel)
        token_layout.addLayout(token_actions)
        self._token_error = QLabel()
        self._token_error.setObjectName("loginError")
        self._token_error.setWordWrap(True)
        self._token_error.hide()
        token_layout.addWidget(self._token_error)
        self._token_panel.hide()
        self._btn_token_save.clicked.connect(self._save_inline_token)
        self._btn_token_cancel.clicked.connect(self._hide_token_editor)
        root.addWidget(self._token_panel)

        self._btn_token = _pill_button("Set token...")
        root.addWidget(self._btn_token)

        self._btn_toggle = _pill_button("Collapse")
        self._btn_toggle.setObjectName("toggleButton")
        self._btn_toggle.setToolTip("Show less detail")
        self._btn_toggle.setIconSize(QSize(18, 18))
        self._btn_refresh = _pill_button("Refresh")
        self._btn_refresh.setObjectName("refreshButton")
        self._btn_refresh.setProperty("refreshState", "idle")
        self._btn_refresh.setIconSize(QSize(18, 18))
        self._btn_dashboard = _pill_button("Dashboard")
        self._btn_dashboard.setIconSize(QSize(18, 18))

        self._action_row = QWidget()
        self._action_row.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        action_layout = QHBoxLayout(self._action_row)
        action_layout.setContentsMargins(*_SECTION_INSET_MARGINS)
        action_layout.setSpacing(0)
        action_layout.addWidget(self._btn_toggle)
        action_layout.addSpacing(_ACTION_BUTTON_GAP)
        action_layout.addWidget(self._btn_refresh, 1)
        self._dashboard_gap = QWidget()
        self._dashboard_gap.setFixedSize(_ACTION_BUTTON_GAP, 1)
        action_layout.addWidget(self._dashboard_gap)
        self._dashboard_slot = TrailingSlot(leading=0)
        self._dashboard_slot.set_child(self._btn_dashboard)
        action_layout.addWidget(self._dashboard_slot, 1)

        self._rule_before_metadata = _section_rule()

        self._btn_refresh.clicked.connect(self._on_manual_refresh_clicked)
        self._btn_token.clicked.connect(self.show_token_editor)
        self._btn_toggle.clicked.connect(self.toggle_compact)
        self._btn_dashboard.clicked.connect(self._open_dashboard)
        self._btn_settings.clicked.connect(self._toggle_settings_popup)
        self._btn_minimize.clicked.connect(self.minimize_requested.emit)
        self._btn_quit.clicked.connect(self.hide_requested.emit)

        # Metadata
        self._metadata_block = QWidget()
        meta_layout = QVBoxLayout(self._metadata_block)
        meta_layout.setContentsMargins(*_SECTION_INSET_MARGINS)
        meta_layout.setSpacing(2)
        meta_title = QLabel("Metadata")
        meta_title.setObjectName("sectionTitle")
        meta_layout.addWidget(meta_title)
        status_label = QLabel("Status & Resets")
        status_label.setObjectName("sectionLabel")
        meta_layout.addWidget(status_label)
        self._meta_fetched = QLabel()
        self._meta_reset = QLabel()
        for label in (self._meta_fetched, self._meta_reset):
            label.setObjectName("metaLine")
            meta_layout.addWidget(label)

        self._mount_collapsible_sections()
        self._apply_compact_visibility()
        self._apply_active_theme()
        self._sync_notify_bells_from_settings()
        self._resize_to_mode()

    def _mount_collapsible_sections(self) -> None:
        """Stack detail and summary in one clip so neither pushes the other aside."""
        root = self._root_layout
        gap = root.spacing()

        self._details_panel = QWidget()
        details_layout = QVBoxLayout(self._details_panel)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(gap)
        details_layout.addWidget(self._rule_before_gauges)
        details_layout.addWidget(self._gauge_block)
        details_layout.addWidget(self._rule_before_on_demand)
        details_layout.addWidget(self._on_demand_card)
        details_layout.addWidget(self._rule_before_team)
        details_layout.addWidget(self._team_block)

        self._compact_panel = QWidget()
        compact_host = QVBoxLayout(self._compact_panel)
        compact_host.setContentsMargins(0, 0, 0, 0)
        compact_host.setSpacing(0)
        compact_host.addWidget(self._compact_total_row)

        self._summary_viewport = TopClip()
        self._details_panel.setParent(self._summary_viewport)
        self._compact_panel.setParent(self._summary_viewport)
        root.insertWidget(root.indexOf(self._rule_before_actions), self._summary_viewport)

        self._metadata_panel = QWidget()
        metadata_layout = QVBoxLayout(self._metadata_panel)
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(0)
        metadata_layout.addSpacing(gap)
        metadata_layout.addWidget(self._rule_before_metadata)
        metadata_layout.addSpacing(gap)
        metadata_layout.addWidget(self._metadata_block)

        self._metadata_viewport = TopClip()
        self._metadata_panel.setParent(self._metadata_viewport)

        self._mode_tail = QWidget()
        self._mode_tail.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        tail_layout = QVBoxLayout(self._mode_tail)
        tail_layout.setContentsMargins(0, 0, 0, 0)
        tail_layout.setSpacing(0)
        tail_layout.addWidget(self._action_row)
        tail_layout.addWidget(self._metadata_viewport)
        root.addWidget(self._mode_tail)

    def _make_notify_bell(self, section_id: str) -> SectionNotifyBell:
        bell = SectionNotifyBell(section_id, self)
        bell.toggled_enabled.connect(self._on_notify_bell_toggled)
        self._notify_bells_by_section.setdefault(section_id, []).append(bell)
        return bell

    def _sync_notify_bells_from_settings(self) -> None:
        for section_id, bells in self._notify_bells_by_section.items():
            enabled = self._app_settings.is_usage_notification_enabled(section_id)
            for bell in bells:
                bell.set_notification_enabled(enabled)

    def _on_notify_bell_toggled(self, section_id: str, enabled: bool) -> None:
        def mutator(current):
            updated = current.with_usage_notification(section_id, enabled)
            if not enabled:
                return updated
            envelope = load_cache(self._cache_path)
            if not isinstance(envelope, CacheEnvelopeOk):
                return updated
            snapshot = envelope.data
            state = notification_state_for_cycle(
                updated.usage_notification_state,
                snapshot.billing_cycle_end,
            )
            percent = usage_percent_for_section(snapshot, section_id)
            state = acknowledge_thresholds(
                state,
                section_id,
                thresholds_already_reached(percent),
            )
            return updated.with_usage_notification_state(state)

        self._app_settings = mutate_app_settings(mutator)
        self._sync_notify_bells_from_settings()

    def _on_fetch_finished(self, _exit_code: int) -> None:
        self.reload_from_cache()
        if self._login_verify_pending:
            self._finish_login_after_fetch()
        self.cache_or_session_changed.emit()
        if self._manual_refresh_cooldown:
            self._set_refresh_button_state("cooldown")
            self._refresh_cooldown_timer.start(_MANUAL_REFRESH_COOLDOWN_MS)

    def _end_manual_refresh_cooldown(self) -> None:
        self._manual_refresh_cooldown = False
        self._set_refresh_button_state("idle")

    def _set_refresh_button_state(self, state: str) -> None:
        """idle: clickable; loading: fetching (full brightness); cooldown: post-fetch wait (dimmed)."""
        button = self._btn_refresh
        if state == "idle":
            self._apply_refresh_dim(False)
            button.setEnabled(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
        elif state == "loading":
            self._apply_refresh_dim(False)
            button.setEnabled(False)
            button.setCursor(Qt.CursorShape.ArrowCursor)
        elif state == "cooldown":
            self._apply_refresh_dim(True)
            button.setEnabled(False)
            button.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            return
        button.setProperty("refreshState", state)
        style = button.style()
        style.unpolish(button)
        style.polish(button)
        button.update()

    def _apply_refresh_dim(self, dimmed: bool) -> None:
        if not dimmed:
            self._opacity_fader.fade_to(
                self._btn_refresh,
                1.0,
                remove_at_full=True,
            )
            return
        self._opacity_fader.fade_to(self._btn_refresh, _REFRESH_DIM_OPACITY)

    def _ensure_settings_popup(self) -> TraySettingsPopup:
        if self._settings_popup is not None:
            return self._settings_popup
        host = self.window() or self
        popup = TraySettingsPopup(host, anchor=self._btn_settings)
        popup.dismissed_via_anchor.connect(self._on_settings_dismissed_via_anchor)
        popup.button_group.buttonToggled.connect(self._on_tray_display_button_toggled)
        popup.theme_group.buttonToggled.connect(self._on_theme_button_toggled)
        self._settings_popup = popup
        self._radio_total = popup.radio_total
        self._radio_personal = popup.radio_personal
        self._tray_display_group = popup.button_group
        self._radio_theme_system = popup.radio_theme_system
        self._radio_theme_dark = popup.radio_theme_dark
        self._radio_theme_light = popup.radio_theme_light
        self._theme_group = popup.theme_group
        self._sync_tray_display_radios()
        self._sync_theme_radios()
        return popup

    def _on_settings_dismissed_via_anchor(self) -> None:
        """Qt.Popup closes before the gear button's clicked signal; swallow the reopen."""
        self._suppress_settings_open = True
        QTimer.singleShot(300, self._release_settings_suppress)

    def _release_settings_suppress(self) -> None:
        self._suppress_settings_open = False

    def open_settings_panel(self, at_global: QPoint | None = None) -> None:
        """Show appearance and tray settings (tray menu or in-widget gear)."""
        self._suppress_settings_open = False
        self._show_settings_popup(at_global=at_global)

    def _show_settings_popup(self, at_global: QPoint | None = None) -> None:
        self._hide_token_editor()
        self._app_settings = load_app_settings()
        self._sync_theme_from_settings()
        popup = self._ensure_settings_popup()
        self._sync_tray_display_radios()
        self._sync_theme_radios()
        if at_global is not None:
            popup.show_near_point(at_global)
        else:
            popup.show_below_anchor(self._btn_settings)

    def _toggle_settings_popup(self) -> None:
        if self._suppress_settings_open:
            self._suppress_settings_open = False
            return
        popup = self._ensure_settings_popup()
        if popup.isVisible():
            popup.hide()
            return
        self._show_settings_popup()

    def _hide_settings_popup(self) -> None:
        if self._settings_popup is not None:
            self._settings_popup.hide()

    def _sync_tray_display_radios(self) -> None:
        if self._settings_popup is None:
            return
        self._tray_display_group.blockSignals(True)
        if self._app_settings.tray_display_mode == "personal":
            self._radio_personal.setChecked(True)
        else:
            self._radio_total.setChecked(True)
        self._tray_display_group.blockSignals(False)

    def _sync_theme_radios(self) -> None:
        if self._settings_popup is None:
            return
        self._theme_group.blockSignals(True)
        if self._app_settings.theme == "light":
            self._radio_theme_light.setChecked(True)
        elif self._app_settings.theme == "dark":
            self._radio_theme_dark.setChecked(True)
        else:
            self._radio_theme_system.setChecked(True)
        self._theme_group.blockSignals(False)

    def _sync_theme_from_settings(self) -> None:
        self._ensure_system_theme_listener()
        if applied_theme_matches_preference(self._app_settings.theme):
            return
        apply_theme_preference(self._app_settings.theme)
        self._apply_active_theme()

    def _ensure_system_theme_listener(self) -> None:
        if self._system_theme_listener_hooked:
            return
        from PySide6.QtGui import QGuiApplication

        app = QGuiApplication.instance()
        if app is None:
            return
        hints = app.styleHints()
        if not hasattr(hints, "colorSchemeChanged"):
            return
        hints.colorSchemeChanged.connect(self._on_system_color_scheme_changed)
        self._system_theme_listener_hooked = True

    def _on_system_color_scheme_changed(self, _scheme) -> None:
        self._app_settings = load_app_settings()
        if self._app_settings.theme != "system":
            return
        previous = active_theme()
        resolved = apply_theme_preference("system")
        if resolved == previous:
            return
        self._apply_active_theme()

    def _on_theme_button_toggled(self, button, checked: bool) -> None:
        if not checked:
            return
        if button is self._radio_theme_light:
            theme: ThemeId = "light"
        elif button is self._radio_theme_dark:
            theme = "dark"
        else:
            theme = "system"
        if self._app_settings.theme == theme:
            return
        self._app_settings = mutate_app_settings(lambda current: current.with_theme(theme))
        apply_theme_preference(theme)
        self._apply_active_theme()

    def _apply_active_theme(self) -> None:
        palette = active_palette()
        self.setStyleSheet(root_stylesheet(palette))
        self._btn_settings.setIcon(material_icon("settings", palette.chrome_icon))
        self._btn_minimize.setIcon(material_icon("minimize", palette.chrome_icon))
        self._btn_quit.setIcon(material_icon("close", palette.close_icon))
        self._refresh_frames = _rotated_icons("refresh", palette.action_icon, 18)
        self._content_frames = _rotated_icons("refresh", palette.cyan, 28)
        self._login_spinner_frames = _rotated_icons("refresh", palette.login_text, 18)
        if self._refresh_busy or self._content_busy:
            self._paint_busy_frame()
        else:
            self._btn_refresh.setIcon(self._refresh_frames[0])
            self._loading_icon.setPixmap(self._content_frames[0].pixmap(28, 28))
        if self._login_spinner_timer.isActive():
            self._paint_login_spinner_frame()
        self._btn_dashboard.setIcon(material_icon("open_in_new", palette.action_icon))
        self._update_toggle_button()
        self._personal_icon.setPixmap(material_pixmap("person", palette.cyan, size=16))
        self._personal_bonus_info.apply_active_palette()
        self._team_icon.setPixmap(material_pixmap("group", palette.team_icon, size=16))
        self._personal_bar.set_fill_color(QColor(palette.cyan))
        self._od_bar.set_fill_color(QColor(palette.coral))
        self._api_gauge.set_arc_color(QColor(palette.api_gauge))
        self._auto_gauge.set_arc_color(QColor(palette.violet))
        self._total_gauge.update()
        self._mini_total.update()
        for bells in self._notify_bells_by_section.values():
            for bell in bells:
                bell.set_notification_enabled(bell.isChecked())
        if self._settings_popup is not None:
            self._settings_popup.apply_active_palette()
        window = self.window()
        if window is not None and window is not self:
            window.update()

    def _on_tray_display_button_toggled(self, button, checked: bool) -> None:
        if not checked:
            return
        mode = "personal" if button is self._radio_personal else "total_percent"
        if self._app_settings.tray_display_mode == mode:
            return
        self._app_settings = mutate_app_settings(
            lambda current: current.with_tray_display_mode(mode),
        )
        self.tray_settings_changed.emit()

    def show_token_editor(self) -> None:
        self._hide_settings_popup()
        self._token_error.hide()
        self._token_error.setText("")
        self._token_panel.show()
        self._token_input.setFocus()
        self._resize_to_mode()

    def _hide_token_editor(self) -> None:
        self._token_input.clear()
        self._token_error.hide()
        self._token_error.setText("")
        self._token_panel.hide()
        self._resize_to_mode()

    def _save_inline_token(self) -> None:
        try:
            self._store.set_token(self._token_input.text())
            self.cache_or_session_changed.emit()
        except TokenNormalizeError as exc:
            self._token_error.setText(str(exc))
            self._token_error.show()
            self._resize_to_mode()
            return
        self._token_input.clear()
        self._token_panel.hide()
        self.refresh()

    def _render_view_model(self) -> None:
        vm = self._view_model
        self._show_inline_message(vm.inline_message)
        self._sync_busy_spinner()

        snapshot = vm.snapshot
        if snapshot is not None:
            self._fill_snapshot(snapshot)
        elif vm.phase == "error":
            self._clear_data_fields()

        self._apply_section_visibility()
        self._resize_to_mode()

        fetched = format_datetime_display(vm.fetched_at)
        self._meta_fetched.setText(f"Last Fetched:  {fetched}")
        reset = format_datetime_display(snapshot.billing_cycle_end if snapshot else None)
        self._meta_reset.setText(f"Next Reset:    {reset}")

    def _show_inline_message(self, message: str | None) -> None:
        if self._view_model.phase == "loading" or self._needs_browser_login() or message is None or message == "":
            self._inline_error.hide()
            self._inline_error.setText("")
            return
        self._inline_error.setText(message)
        self._inline_error.show()

    def _empty_loading(self) -> bool:
        return (
            self._view_model.phase == "loading"
            and self._view_model.snapshot is None
            and not self._needs_browser_login()
        )

    def _sync_busy_spinner(self) -> None:
        loading = self._view_model.phase == "loading"
        self._refresh_busy = loading
        self._content_busy = self._empty_loading()
        self._set_data_dimmed(loading and self._view_model.snapshot is not None)
        if self._refresh_busy or self._content_busy:
            if not self._busy_timer.isActive():
                self._busy_index = 0
                self._busy_timer.start()
            self._paint_busy_frame()
            return
        self._busy_timer.stop()
        if self._refresh_frames:
            self._btn_refresh.setIcon(self._refresh_frames[0])
            self._btn_refresh.setIconSize(QSize(18, 18))

    def _advance_busy_spinner(self) -> None:
        self._busy_index = (self._busy_index + 1) % len(self._refresh_frames)
        self._paint_busy_frame()

    def _paint_busy_frame(self) -> None:
        if self._refresh_busy:
            self._btn_refresh.setIcon(self._refresh_frames[self._busy_index])
            self._btn_refresh.setIconSize(QSize(18, 18))
        if self._content_busy:
            frame = self._content_frames[self._busy_index % len(self._content_frames)]
            self._loading_icon.setPixmap(frame.pixmap(28, 28))

    def _fill_snapshot(self, snapshot: UsageSnapshot) -> None:
        personal_pct = format_pool_percent(snapshot.personal.used_usd, snapshot.personal.limit_usd)
        self._personal_amount.setText(
            f"{format_usd(snapshot.personal.used_usd)} / {format_usd(snapshot.personal.limit_usd)}"
        )
        self._personal_pct.setText(format_percent(personal_pct))
        self._personal_bar.set_percent(personal_pct)
        bonus_chip = format_personal_bonus_chip(snapshot.personal_plan_bonus)
        if bonus_chip is not None:
            self._personal_bonus.setText(bonus_chip)
            self._personal_bonus.show()
            self._personal_bonus_info.set_hint(format_personal_bonus_tooltip(snapshot.personal_plan_bonus))
        else:
            self._personal_bonus.clear()
            self._personal_bonus.hide()
            self._personal_bonus_info.set_hint(None)

        plan = snapshot.plan_percents
        self._total_gauge.set_plan_percents(
            plan.total_percent_used,
            plan.api_percent_used,
            plan.auto_percent_used,
        )
        self._api_gauge.set_percent(plan.api_percent_used)
        self._auto_gauge.set_percent(plan.auto_percent_used)
        self._mini_total.set_plan_percents(
            plan.total_percent_used,
            plan.api_percent_used,
            plan.auto_percent_used,
        )
        self._compact_total_pct.setText(format_percent(plan.total_percent_used))

        if snapshot.team_pool is not None:
            team_pct = format_pool_percent(snapshot.team_pool.used_usd, snapshot.team_pool.limit_usd)
            self._team_amount.setText(
                f"{format_usd(snapshot.team_pool.used_usd)} / "
                f"{format_usd(snapshot.team_pool.limit_usd)}"
            )
            self._team_pct.setText(format_percent(team_pct))

        od = snapshot.on_demand_display
        if od.show_card:
            personal_od = snapshot.personal_on_demand
            limit_usd = personal_od.limit_usd if personal_od is not None else None
            self._od_pct.setText(format_percent(od.progress_percent))
            self._od_amount.setText(
                f"{format_usd(od.on_demand_used_usd)} / {format_usd(limit_usd)}",
            )
            self._od_bar.set_percent(od.progress_percent)

    def _clear_data_fields(self) -> None:
        self._personal_amount.setText("—")
        self._personal_pct.setText("—")
        self._personal_bonus.clear()
        self._personal_bonus.hide()
        self._personal_bonus_info.set_hint(None)
        self._personal_bar.set_percent(None)
        self._team_amount.setText("—")
        self._team_pct.setText("—")
        self._total_gauge.set_plan_percents(None, None, None)
        self._api_gauge.set_percent(None)
        self._auto_gauge.set_percent(None)
        self._compact_total_pct.setText("—")
        self._meta_reset.setText("Next Reset:    —")

    def _apply_compact_visibility(self) -> None:
        self._apply_section_visibility()

    def _needs_browser_login(self) -> bool:
        return shows_browser_login(self._view_model, self._store.has_token())

    def _apply_section_visibility(self) -> None:
        login = self._needs_browser_login()
        empty_loading = self._empty_loading()
        show_data = not login and not empty_loading
        self._loading_card.setVisible(empty_loading)
        self._login_card.setVisible(login)
        if login:
            self._resize_to_mode()
        self._personal_card.setVisible(show_data)
        # Detail blocks stay in the clip. Compact mode hides the clip, not the blocks,
        # so expanding does not restack them mid-animation.
        self._compact_total_row.setVisible(show_data)
        self._team_block.setVisible(show_data and self._view_model.show_team_row)
        self._gauge_block.setVisible(show_data)
        self._on_demand_card.setVisible(show_data and self._view_model.show_on_demand_card)
        self._metadata_block.setVisible(show_data)
        self._action_row.setVisible(not login)
        self._mode_tail.setVisible(not login)
        if login or empty_loading:
            self._release_widget_vertical_lock(self._mode_tail)
        self._btn_settings.setVisible(not login)
        self._btn_token.setVisible(login)
        if login or empty_loading:
            self._hide_settings_popup()
        self._sync_section_rules()
        self._apply_layout_progress(self._layout_progress)
        if show_data and self.isVisible():
            self._schedule_refresh_metrics_lock()

    def _sync_section_rules(self) -> None:
        """One hairline between each visible section; hidden sections take their rule with them."""
        if self._needs_browser_login() or self._empty_loading():
            self._rule_before_team.setVisible(False)
            self._rule_before_gauges.setVisible(False)
            self._rule_before_on_demand.setVisible(False)
            self._rule_before_actions.setVisible(True)
            self._rule_before_metadata.setVisible(False)
            return
        self._rule_before_team.setVisible(self._view_model.show_team_row)
        self._rule_before_gauges.setVisible(True)
        self._rule_before_on_demand.setVisible(self._view_model.show_on_demand_card)
        self._rule_before_actions.setVisible(True)
        self._rule_before_metadata.setVisible(True)

    def _start_browser_login(self) -> None:
        import time

        webbrowser.open(_LOGIN_URL)
        set_browser_login_flow_active(True)
        self._login_waiting = True
        self._login_deadline_ms = int(time.monotonic() * 1000) + _LOGIN_WAIT_MS
        self._login_error.hide()
        self._login_error.setText("")
        self._login_status.setText(
            "Sign in in the browser, then return to this window. "
            "The session is read automatically."
        )
        self._login_status.show()
        self._set_login_spinner(True)
        self._resize_to_mode()
        self._hook_window_activation()
        if not self._login_timer.isActive():
            self._login_timer.start()
        QTimer.singleShot(_LOGIN_FIRST_IMPORT_MS, self._attempt_browser_import)

    def _hook_window_activation(self) -> None:
        window = self.window()
        if window is None or self._activation_hooked:
            return
        window.installEventFilter(self)
        self._activation_hooked = True

    def eventFilter(self, watched, event) -> bool:  # noqa: N802
        if (
            getattr(self, "_login_waiting", False)
            and event.type() == QEvent.Type.WindowActivate
            and watched is self.window()
        ):
            self._attempt_browser_import()
        return False

    def _attempt_browser_import(self) -> None:
        import time

        if not self._login_waiting or self._login_busy:
            return
        if int(time.monotonic() * 1000) >= self._login_deadline_ms:
            self._finish_login_failed(
                BrowserImportError(
                    "Could not read a Cursor session from the browser. Set the token manually.",
                ),
            )
            return
        self._login_busy = True
        self._login_status.setText("Checking installed browsers for a cursor.com session…")
        self._login_status.show()
        QTimer.singleShot(0, self._resize_to_mode)

        def task() -> None:
            try:
                result = import_session_token_from_browsers(
                    scan_profile="login_poll",
                    wait_for_lock=False,
                )
            except BrowserImportBusyError:
                self._login_import_idle.emit()
                return
            except BrowserImportError as exc:
                self._login_import_failed.emit(exc)
                return
            except Exception:
                self._login_import_failed.emit(
                    BrowserImportError("Could not read the browser session."),
                )
                return
            self._login_imported.emit(result.token)

        import threading

        threading.Thread(target=task, name="cursor-usage-login-import", daemon=True).start()

    def _on_import_success(self, token: str) -> None:
        self._login_busy = False
        if not self._login_waiting:
            return
        try:
            normalized = normalize_session_token(token)
        except TokenNormalizeError as exc:
            self._on_import_error(BrowserImportError(str(exc)))
            return
        current = self._store.get_token()
        if current is not None and current == normalized:
            self._login_status.setText(
                "Still waiting for a cursor.com session. Finish signing in, then return here."
            )
            self._login_status.show()
            QTimer.singleShot(0, self._resize_to_mode)
            return
        try:
            self._store.set_token(normalized)
            self.cache_or_session_changed.emit()
        except Exception as exc:
            self._finish_login_failed(BrowserImportError(str(exc)))
            return
        self._login_verify_pending = True
        self._login_error.hide()
        self._login_error.setText("")
        self._login_status.setText("Verifying session…")
        self._login_status.show()
        self._resize_to_mode()
        self.refresh()

    def _finish_login_after_fetch(self) -> None:
        self._login_verify_pending = False
        if not self._login_waiting:
            return
        view_model = self._view_model
        if view_model.phase == "ok" and view_model.snapshot is not None:
            self._stop_login_wait()
            self._login_status.hide()
            self._login_status.setText("")
            QTimer.singleShot(0, self._resize_to_mode)
            return
        if view_model.error_code in ("invalid_token", "not_authenticated"):
            self._login_status.setText(
                "Still waiting for a cursor.com session. Finish signing in, then return here."
            )
            self._login_status.show()
            QTimer.singleShot(0, self._resize_to_mode)
            return
        message = view_model.inline_message or view_model.error_message
        self._finish_login_failed(
            BrowserImportError(message or "Could not verify the browser session."),
        )

    def _on_import_error(self, exc: object) -> None:
        self._login_busy = False
        if not self._login_waiting:
            return
        if not isinstance(exc, BrowserImportError):
            exc = BrowserImportError(str(exc))
        if not is_retryable_import_error(exc):
            self._finish_login_failed(exc)
            return
        self._login_status.setText(
            "Still waiting for a cursor.com session. Finish signing in, then return here."
        )
        self._resize_to_mode()

    def _finish_login_failed(self, exc: BrowserImportError | str) -> None:
        if isinstance(exc, str):
            exc = BrowserImportError(exc)
        self._stop_login_wait()
        self._login_busy = False
        self._login_status.hide()
        self._login_status.setText("")
        self._login_error.setText(_login_failure_text(exc))
        self._login_error.show()
        self._login_error.adjustSize()
        QTimer.singleShot(0, self._resize_to_mode)
        if exc.decrypt_blocked:
            self.show_token_editor()

    def _clear_login_import_busy(self) -> None:
        self._login_busy = False

    def _stop_login_wait(self) -> None:
        self._login_waiting = False
        self._login_verify_pending = False
        self._login_timer.stop()
        self._set_login_spinner(False)
        set_browser_login_flow_active(False)
        if not self._prepare_shutdown_done:
            QTimer.singleShot(0, self._resize_to_mode)

    def prepare_for_shutdown(self) -> None:
        """Stop UI timers and login polling; do not relayout during app quit."""
        if self._prepare_shutdown_done:
            return
        self._prepare_shutdown_done = True
        self._login_timer.stop()
        self._login_spinner_timer.stop()
        self._busy_timer.stop()
        self._refresh_cooldown_timer.stop()
        if self._layout_anim is not None:
            self._layout_anim.stop()
        self._login_waiting = False
        self._login_verify_pending = False
        self._login_busy = False
        set_browser_login_flow_active(False)
        self._set_login_spinner(False)

    def _set_login_spinner(self, active: bool) -> None:
        if active:
            self._spinner_index = 0
            self._btn_login.setEnabled(False)
            self._btn_login.setText("")
            self._btn_login.setIconSize(QSize(18, 18))
            self._paint_login_spinner_frame()
            self._login_spinner_timer.start()
            return
        self._login_spinner_timer.stop()
        self._btn_login.setEnabled(True)
        self._btn_login.setText("Log in to Cursor")
        self._btn_login.setIcon(QIcon())

    def _advance_login_spinner(self) -> None:
        if not self._login_spinner_frames:
            return
        self._spinner_index = (self._spinner_index + 1) % len(self._login_spinner_frames)
        self._paint_login_spinner_frame()

    def _paint_login_spinner_frame(self) -> None:
        if not self._login_spinner_frames:
            return
        icon = self._login_spinner_frames[self._spinner_index % len(self._login_spinner_frames)]
        self._btn_login.setIcon(icon)

    def _update_toggle_button(self) -> None:
        if self._compact:
            self._btn_toggle.setText("Expand")
            self._btn_toggle.setToolTip("Show full details")
        else:
            self._btn_toggle.setText("Collapse")
            self._btn_toggle.setToolTip("Show less detail")
        self._set_chevron_angle(180.0 * self._layout_progress)

    def _chevron_base_pixmap(self) -> QPixmap:
        color = active_palette().toggle_text
        key = str(color)
        if self._chevron_base is None or self._chevron_base_key != key:
            self._chevron_base = material_pixmap("expand_less", color, size=18)
            self._chevron_base_key = key
        return self._chevron_base

    def _set_chevron_angle(self, degrees: float) -> None:
        """Rotate one chevron so Collapse and Expand share a single glyph."""
        self._chevron_degrees = degrees
        size = 18
        canvas = QPixmap(size, size)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(size / 2, size / 2)
        painter.rotate(degrees)
        painter.translate(-size / 2, -size / 2)
        painter.drawPixmap(0, 0, self._chevron_base_pixmap())
        painter.end()
        self._btn_toggle.setIcon(QIcon(canvas))
        self._btn_toggle.setIconSize(QSize(size, size))

    def _prefers_reduced_motion(self) -> bool:
        app = QGuiApplication.instance()
        if app is None:
            return False
        try:
            preference = app.styleHints().motionPreference()
        except AttributeError:
            return False
        return preference == Qt.MotionPreference.ReducedMotion

    def _layout_transition_running(self) -> bool:
        anim = self._layout_anim
        if anim is None:
            return False
        return anim.state() == QAbstractAnimation.State.Running

    def _stop_layout_transition(self) -> None:
        anim = self._layout_anim
        if anim is None:
            return
        self._layout_retargeting = True
        anim.stop()
        self._layout_retargeting = False

    def _start_layout_transition(self) -> None:
        """InOutSine spreads the travel so a 60fps frame never jumps."""
        target = 1.0 if self._compact else 0.0
        start = self._layout_progress
        if abs(start - target) < 0.001:
            self._layout_progress = target
            self._apply_layout_progress(target)
            return
        self._dashboard_slot.note_span()
        distance = abs(target - start)
        duration = max(_LAYOUT_TRANSITION_MIN_MS, int(round(_LAYOUT_TRANSITION_MS * distance)))
        if self._layout_anim is None:
            anim = QVariantAnimation(self)
            anim.valueChanged.connect(self._apply_layout_progress)
            anim.finished.connect(self._on_layout_transition_finished)
            self._layout_anim = anim
        else:
            anim = self._layout_anim
            self._layout_retargeting = True
            anim.stop()
            self._layout_retargeting = False
        anim.setStartValue(start)
        anim.setEndValue(target)
        anim.setDuration(duration)
        anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        anim.start()

    def _on_layout_transition_finished(self) -> None:
        if self._layout_retargeting:
            return
        target = 1.0 if self._compact else 0.0
        if abs(self._layout_progress - target) > 0.02:
            return
        metrics = self._layout_metrics
        rest_height: int | None = None
        if metrics is not None:
            rest_height = metrics.expanded_height if target <= 0.0 else metrics.compact_height
        self._thaw_layout_after_transition()
        self._layout_metrics = None
        self._release_static_root_sections()
        self._layout_progress = target
        self._apply_layout_progress(target)
        if rest_height is not None:
            width = self.preferred_width()
            self.setFixedSize(width, rest_height)
            window = self.window()
            if window is not None and hasattr(window, "resize_for_content"):
                if getattr(window, "_card", None) is not None:
                    window.resize_for_content()
        self.compact_changed.emit(self._compact)
        self._resize_to_mode()

    def _apply_layout_progress(self, value: object) -> None:
        if self._applying_layout:
            return
        progress = min(1.0, max(0.0, float(value)))
        if progress >= 0.9995:
            progress = 1.0
        if progress <= 0.0005:
            progress = 0.0
        self._layout_progress = progress
        self._applying_layout = True
        try:
            self._place_collapsible_panels(progress)
            self._set_chevron_angle(180.0 * progress)
            self._resize_to_mode()
        finally:
            self._applying_layout = False

    def _freeze_layout_for_transition(self) -> None:
        """Stop the root layout from reflowing on every frame.

        Sections under the summary keep the y they had at rest and slide by the
        same amount the summary clip grows or shrinks.
        """
        root = self._root_layout
        if root is None or not root.isEnabled():
            return
        summary = self._summary_viewport
        self._summary_rest_height = summary.height()
        followers: list[tuple[QWidget, int]] = []
        for index in range(root.count()):
            widget = root.itemAt(index).widget()
            if widget is None or widget is summary or widget.isHidden():
                continue
            if widget.y() > summary.y():
                followers.append((widget, widget.y()))
        self._transition_followers = followers
        root.setEnabled(False)

    def _thaw_layout_after_transition(self) -> None:
        self._transition_followers = []
        root = getattr(self, "_root_layout", None)
        if root is not None and not root.isEnabled():
            root.setEnabled(True)

    def _slide_transition_followers(self, summary_height: int) -> None:
        if not self._transition_followers:
            return
        delta = summary_height - self._summary_rest_height
        for widget, rest_y in self._transition_followers:
            next_y = rest_y + delta
            if widget.y() != next_y:
                widget.move(widget.x(), next_y)

    def _section_content_width(self) -> int:
        laid_out = self._summary_viewport.width()
        if laid_out > 1:
            return laid_out
        left, _, right, _ = self._root_layout.getContentsMargins()
        return max(1, self.width() - left - right)

    def _pin_static_root_sections(self) -> None:
        """Keep header rows from absorbing slack while the window height animates."""
        for attr in _STATIC_ANIM_SECTION_ATTRS:
            widget = getattr(self, attr)
            if widget.isHidden():
                self._release_widget_vertical_lock(widget)
                continue
            widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            height = widget.height()
            if height <= 0:
                height = widget.sizeHint().height()
            if height > 0:
                widget.setFixedHeight(height)

    def _release_static_root_sections(self) -> None:
        for attr in _STATIC_ANIM_SECTION_ATTRS:
            self._release_widget_vertical_lock(getattr(self, attr))
        self._release_widget_vertical_lock(self._mode_tail)

    def _release_widget_vertical_lock(self, widget: QWidget) -> None:
        widget.setMinimumHeight(0)
        widget.setMaximumHeight(_QT_MAX)
        widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

    def _measure_panel_height(self, panel: QWidget, width: int) -> int:
        panel.setMinimumHeight(0)
        panel.setMaximumHeight(_QT_MAX)
        if panel.width() != width:
            panel.setFixedWidth(width)
        layout = panel.layout()
        if layout is None:
            height = max(0, panel.sizeHint().height())
        else:
            layout.invalidate()
            layout.activate()
            height = max(0, layout.sizeHint().height())
        panel.setFixedHeight(height)
        if panel.pos() != QPoint(0, 0):
            panel.move(0, 0)
        return height

    def _refresh_layout_metrics(self) -> None:
        login = self._needs_browser_login()
        show_data = (not login) and (not self._empty_loading())
        if not show_data:
            self._layout_metrics = None
            self._release_static_root_sections()
            return
        self._pin_static_root_sections()
        width = self._section_content_width()
        details_h = self._measure_panel_height(self._details_panel, width)
        compact_h = self._measure_panel_height(self._compact_panel, width)
        meta_h = self._measure_panel_height(self._metadata_panel, width)
        saved_progress = self._layout_progress
        expanded_height = self._layout_height_for_clip_state(0.0, details_h, compact_h, meta_h)
        compact_height = self._layout_height_for_clip_state(1.0, details_h, compact_h, meta_h)
        self._layout_progress = saved_progress
        self._apply_clip_geometry(saved_progress, details_h, compact_h, meta_h)
        # Measuring the compact state moves every section. Put them back before
        # the animation records its starting positions, or collapse runs from
        # the wrong place and snaps at the end.
        root = self._root_layout
        root.invalidate()
        root.activate()
        self._layout_metrics = _LayoutMetrics(
            content_width=width,
            details_h=details_h,
            compact_h=compact_h,
            meta_h=meta_h,
            expanded_height=expanded_height,
            compact_height=compact_height,
        )

    def _layout_height_for_clip_state(
        self,
        progress: float,
        details_h: int,
        compact_h: int,
        meta_h: int,
    ) -> int:
        self._apply_clip_geometry(progress, details_h, compact_h, meta_h)
        root = self._root_layout
        root.invalidate()
        root.activate()
        return root.sizeHint().height()

    def _apply_clip_geometry(
        self,
        progress: float,
        details_h: int,
        compact_h: int,
        meta_h: int,
    ) -> None:
        summary_h = int(round(details_h + ((compact_h - details_h) * progress)))
        self._summary_viewport.set_shown_height(summary_h)
        meta_shown = int(round(meta_h * (1.0 - progress)))
        self._metadata_viewport.set_shown_height(meta_shown)
        self._sync_mode_tail_height(meta_shown)

    def _sync_mode_tail_height(self, meta_viewport_height: int) -> None:
        action_height = self._action_row.height()
        if action_height <= 0:
            action_height = self._action_row.sizeHint().height()
        tail_height = action_height + max(0, meta_viewport_height)
        self._mode_tail.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self._mode_tail.setFixedHeight(tail_height)

    def _place_collapsible_panels(self, progress: float) -> None:
        if self._layout_metrics is None:
            login = self._needs_browser_login()
            show_data = (not login) and (not self._empty_loading())
            if not show_data:
                self._summary_viewport.set_shown_height(0)
                self._metadata_viewport.set_shown_height(0)
                self._dashboard_slot.set_fraction(0.0)
                self._set_dashboard_gap(0.0)
                self._btn_dashboard.hide()
                self._clear_reveal_opacity(self._btn_dashboard)
                return
        metrics = self._layout_metrics
        if metrics is not None:
            details_h = metrics.details_h
            compact_h = metrics.compact_h
            meta_h = metrics.meta_h
        else:
            width = self._section_content_width()
            details_h = self._measure_panel_height(self._details_panel, width)
            compact_h = self._measure_panel_height(self._compact_panel, width)
            meta_h = self._measure_panel_height(self._metadata_panel, width)
        summary_height = int(round(details_h + ((compact_h - details_h) * progress)))
        self._apply_clip_geometry(progress, details_h, compact_h, meta_h)
        self._slide_transition_followers(summary_height)
        details_opacity = _details_opacity(progress)
        compact_opacity = _compact_opacity(progress)
        self._set_crossfade(self._details_panel, details_opacity)
        self._set_crossfade(self._compact_panel, compact_opacity)
        if compact_opacity > details_opacity:
            self._compact_panel.raise_()
        else:
            self._details_panel.raise_()

        self._set_crossfade(self._metadata_panel, _metadata_opacity(progress))

        width_fraction = _dashboard_width_fraction(progress)
        self._dashboard_slot.set_fraction(width_fraction)
        self._set_dashboard_gap(width_fraction)
        if width_fraction <= 0.0:
            self._btn_dashboard.hide()
            self._clear_reveal_opacity(self._btn_dashboard)
            self._btn_dashboard.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        else:
            self._btn_dashboard.show()
            self._set_crossfade(self._btn_dashboard, _dashboard_opacity(progress), allow_hide=False)

    def _set_dashboard_gap(self, fraction: float) -> None:
        if fraction <= 0.0:
            self._dashboard_gap.hide()
            return
        if fraction >= 1.0:
            width = _ACTION_BUTTON_GAP
        else:
            width = max(0, int(round(_ACTION_BUTTON_GAP * fraction)))
        if width <= 0:
            self._dashboard_gap.hide()
            self._dashboard_gap.updateGeometry()
            return
        self._dashboard_gap.show()
        if self._dashboard_gap.width() != width:
            self._dashboard_gap.setFixedWidth(width)
            self._dashboard_gap.updateGeometry()

    def _set_crossfade(self, widget: QWidget, opacity: float, *, allow_hide: bool = True) -> None:
        if allow_hide and opacity <= 0.01:
            widget.hide()
            self._clear_reveal_opacity(widget)
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            return
        if widget.isHidden():
            widget.show()
        widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, opacity < 0.5)
        if opacity >= 0.99:
            self._clear_reveal_opacity(widget)
            return
        effect = widget.graphicsEffect()
        if not isinstance(effect, QGraphicsOpacityEffect):
            effect = QGraphicsOpacityEffect(widget)
            widget.setGraphicsEffect(effect)
        effect.setOpacity(max(0.0, opacity))

    def _clear_reveal_opacity(self, widget: QWidget) -> None:
        effect = widget.graphicsEffect()
        if isinstance(effect, QGraphicsOpacityEffect):
            widget.setGraphicsEffect(None)

    def _lock_toggle_button_width(self) -> None:
        """Keep Collapse/Expand the same width so the label swap cannot push Refresh."""
        if self._toggle_width_locked:
            return
        button = self._btn_toggle
        width = button.width()
        if width <= 0:
            return
        button.setFixedWidth(width)
        self._toggle_width_locked = True

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._app_settings = load_app_settings()
        self._sync_theme_from_settings()
        self._sync_notify_bells_from_settings()
        if self._settings_popup is not None:
            self._sync_tray_display_radios()
            self._sync_theme_radios()
        if self._needs_browser_login():
            QTimer.singleShot(0, self._relayout_browser_login_after_show)
        self._schedule_refresh_metrics_lock()

    def _relayout_browser_login_after_show(self) -> None:
        """Tray reopen measures height while hidden; re-pin and resize once the window is visible."""
        self._clear_wrapped_label_pins()
        self._resize_to_mode()

    def _schedule_refresh_metrics_lock(self) -> None:
        """Lock Refresh size only once the usage actions are on screen.

        Doing this on the sign-in view resized the window a frame after it appeared.
        """
        if self._refresh_metrics_locked or not self._action_row.isVisible():
            return
        self._refresh_metrics_locked = True
        QTimer.singleShot(0, self._lock_refresh_button_metrics)

    def _lock_refresh_button_metrics(self) -> None:
        """Keep the on-screen Refresh size. Later icon frames must not relayout it."""
        self._lock_toggle_button_width()
        height = self._btn_toggle.height()
        self._btn_refresh.setFixedHeight(height)
        self._btn_dashboard.setFixedHeight(height)
        self._btn_refresh.setMinimumWidth(self._btn_refresh.width())
        self._dashboard_slot.note_span()
        self._resize_to_mode()

    def _resize_to_mode(self) -> None:
        if (not self._applying_layout) and hasattr(self, "_summary_viewport"):
            self._apply_layout_progress(self._layout_progress)
            return
        if self._layout_metrics is not None:
            width = self.width() if self.width() > 1 else _WIDGET_WIDTH
            height = self._animated_content_height()
        else:
            root = getattr(self, "_root_layout", None)
            if root is not None:
                spacing = _LOGIN_ROOT_SPACING if self._needs_browser_login() else 8
                if root.spacing() != spacing:
                    root.setSpacing(spacing)
            width = self.preferred_width()
            height = self.preferred_height()
        if self.width() != width or self.height() != height:
            self.setFixedSize(width, height)
        window = self.window()
        if window is not None and hasattr(window, "resize_for_content"):
            if getattr(window, "_card", None) is not None:
                window.resize_for_content()

    def _set_data_dimmed(self, dimmed: bool) -> None:
        for widget in (
            self._personal_card,
            self._compact_total_row,
            self._rule_before_gauges,
            self._gauge_block,
            self._rule_before_on_demand,
            self._on_demand_card,
            self._rule_before_team,
            self._team_block,
            self._rule_before_metadata,
            self._metadata_block,
        ):
            if not dimmed:
                self._opacity_fader.fade_to(widget, 1.0, remove_at_full=True)
                continue
            self._opacity_fader.fade_to(widget, _DATA_DIM_OPACITY)


def _smoothstep(t: float) -> float:
    clamped = min(1.0, max(0.0, t))
    return clamped * clamped * (3.0 - (2.0 * clamped))


def _details_opacity(progress: float) -> float:
    """Stay solid while the lower sections clip away, then dissolve into the summary."""
    if progress <= 0.62:
        return 1.0
    if progress >= 0.84:
        return 0.0
    return 1.0 - _smoothstep((progress - 0.62) / 0.22)


def _compact_opacity(progress: float) -> float:
    """Summary appears as the detail text leaves, so the card never goes blank."""
    if progress <= 0.7:
        return 0.0
    if progress >= 0.92:
        return 1.0
    return _smoothstep((progress - 0.7) / 0.22)


def _metadata_opacity(progress: float) -> float:
    """Metadata is clipped by the window edge, so it stays solid until it is gone."""
    if progress >= 1.0:
        return 0.0
    return 1.0


def _dashboard_width_fraction(progress: float) -> float:
    """Hold the slot until the label has dissolved, then close it from the leading edge."""
    hold = 0.28
    if progress <= hold:
        return 1.0
    return 1.0 - ((progress - hold) / (1.0 - hold))


def _dashboard_opacity(progress: float) -> float:
    hold = 0.28
    if progress <= 0.0:
        return 1.0
    if progress >= hold:
        return 0.0
    return 1.0 - _smoothstep(progress / hold)


def _login_failure_text(exc: BrowserImportError) -> str:
    if exc.decrypt_blocked:
        return str(exc)
    message = str(exc)
    lowered = message.lower()
    if "appbound" in lowered or "decrypt" in lowered or "running as admin" in lowered:
        return str(exc)
    return (
        "No Cursor session was found. Sign in in the browser and try again, "
        "or use Set token to paste WorkosCursorSessionToken from DevTools."
    )


def _section_rule() -> QWidget:
    line = QWidget()
    line.setObjectName("sectionRule")
    line.setFixedHeight(1)
    return line


def _rotated_icons(name: str, color: str | QColor, size: int, steps: int = 12) -> list[QIcon]:
    base = material_pixmap(name, color, size=size)
    frames: list[QIcon] = []
    for step in range(steps):
        canvas = QPixmap(size, size)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.translate(size / 2, size / 2)
        painter.rotate(step * (360 / steps))
        painter.translate(-size / 2, -size / 2)
        painter.drawPixmap(0, 0, base)
        painter.end()
        frames.append(QIcon(canvas))
    return frames


def _pill_button(text: str, icon: QIcon | None = None) -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    if icon is not None:
        button.setIcon(icon)
        button.setIconSize(QSize(18, 18))
    return button


def _icon_tool_button(icon: QIcon, tooltip: str, object_name: str = "iconToolButton") -> QPushButton:
    button = QPushButton()
    button.setObjectName(object_name)
    button.setIcon(icon)
    button.setIconSize(QSize(18, 18))
    button.setToolTip(tooltip)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button
