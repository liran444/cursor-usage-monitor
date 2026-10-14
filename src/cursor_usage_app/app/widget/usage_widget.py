"""Main usage card content."""

from __future__ import annotations

import webbrowser
from pathlib import Path

from PySide6.QtCore import QEvent, QPoint, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
    format_pool_percent,
    format_usd,
)
from cursor_usage_app.app.widget.gauge_widget import DonutGauge, MiniTotalGauge, SegmentedTotalGauge
from cursor_usage_app.app.widget.material_icons import material_icon, material_pixmap
from cursor_usage_app.app.widget.progress_bar import HorizontalBar
from cursor_usage_app.app.widget.opacity_fade import OpacityFader
from cursor_usage_app.app.widget.section_notify_bell import SectionNotifyBell
from cursor_usage_app.app.widget.tray_settings_popup import TraySettingsPopup
from cursor_usage_app.app.widget.view_model import (
    WidgetViewModel,
    shows_browser_login,
    view_model_from_envelope,
    view_model_loading,
)
from cursor_usage_app.auth.browser_import import (
    BrowserImportError,
    import_session_token_from_browsers,
    is_retryable_import_error,
)
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.auth.token_normalize import TokenNormalizeError
from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeOk, parse_cache_envelope
from cursor_usage_app.domain.models import UsageSnapshot
from cursor_usage_app.settings.app_settings import ThemeId, load_app_settings, mutate_app_settings
from cursor_usage_app.usage_notifications import (
    acknowledge_thresholds,
    notification_state_for_cycle,
    thresholds_already_reached,
    usage_percent_for_section,
)

_WIDGET_WIDTH = 303
_FULL_HEIGHT = 620
_COMPACT_HEIGHT = 230
_DASHBOARD_URL = "https://cursor.com/dashboard/usage"
_LOGIN_URL = "https://cursor.com/login"
_LOGIN_POLL_MS = 2000
_LOGIN_WAIT_MS = 120_000
_MANUAL_REFRESH_COOLDOWN_MS = 5000
_REFRESH_DIM_OPACITY = 0.42
_DATA_DIM_OPACITY = 0.35
_OPACITY_FADE_MS = 300
_SPINNER_FRAMES = ("◐", "◓", "◑", "◒")
_CARD_SECTION_INSET_MARGINS = (8, 10, 8, 10)
_SECTION_INSET_MARGINS = (8, 2, 8, 2)


class UsageWidget(QWidget):
    """Usage monitor card; supports full and compact layouts."""

    hide_requested = Signal()
    compact_changed = Signal(bool)
    tray_settings_changed = Signal()
    _login_imported = Signal(str)
    _login_import_failed = Signal(str)

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
        self._login_deadline_ms = 0
        self._activation_hooked = False
        self._login_timer = QTimer(self)
        self._login_timer.setInterval(_LOGIN_POLL_MS)
        self._login_timer.timeout.connect(self._attempt_browser_import)
        self._spinner_index = 0
        self._spinner_timer = QTimer(self)
        self._spinner_timer.setInterval(120)
        self._spinner_timer.timeout.connect(self._advance_login_spinner)
        self._refresh_busy = False
        self._content_busy = False
        self._busy_index = 0
        self._busy_timer = QTimer(self)
        self._busy_timer.setInterval(70)
        self._busy_timer.timeout.connect(self._advance_busy_spinner)
        self._login_imported.connect(self._on_import_success)
        self._login_import_failed.connect(self._on_import_error)
        self._refresh_metrics_locked = False
        self._app_settings = load_app_settings()
        apply_theme_preference(self._app_settings.theme)
        self._refresh_frames: list[QIcon] = []
        self._content_frames: list[QIcon] = []
        self._settings_popup: TraySettingsPopup | None = None
        self._suppress_settings_open = False
        self._manual_refresh_cooldown = False
        self._refresh_cooldown_timer = QTimer(self)
        self._refresh_cooldown_timer.setSingleShot(True)
        self._refresh_cooldown_timer.timeout.connect(self._end_manual_refresh_cooldown)
        self._opacity_fader = OpacityFader(_OPACITY_FADE_MS)
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
        if self._compact == compact:
            return
        self._compact = compact
        self._apply_compact_visibility()
        self._update_toggle_button()
        self.compact_changed.emit(compact)
        self._resize_to_mode()

    def toggle_compact(self) -> None:
        self.set_compact(not self._compact)

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
        self.hide_requested.emit()

    def preferred_height(self) -> int:
        layout = self.layout()
        if layout is None:
            return _COMPACT_HEIGHT if self._compact else _FULL_HEIGHT
        layout.invalidate()
        layout.activate()
        return layout.sizeHint().height()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(8)

        self._btn_settings = _icon_tool_button(
            QIcon(),
            "Settings",
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
        chrome_row.addStretch()
        chrome_row.addWidget(self._btn_settings)
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
        login_layout = QVBoxLayout(self._login_card)
        login_layout.setContentsMargins(12, 12, 12, 12)
        login_layout.setSpacing(8)
        login_title = QLabel("Sign in to Cursor")
        login_title.setObjectName("sectionTitle")
        login_layout.addWidget(login_title)
        self._login_body = QLabel(
            "Open Cursor in your browser and sign in. "
            "This window reads the session when you come back."
        )
        self._login_body.setObjectName("mutedLabel")
        self._login_body.setWordWrap(True)
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
        personal_row.addStretch()
        personal_row.addWidget(self._personal_pct)
        personal_layout.addLayout(personal_row)

        self._personal_bar = HorizontalBar(QColor(active_palette().cyan))
        personal_layout.addWidget(self._personal_bar)
        root.addWidget(self._personal_card)

        self._rule_before_team = _section_rule()
        root.addWidget(self._rule_before_team)

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
        root.addWidget(self._compact_total_row)

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
        root.addWidget(self._team_block)

        self._rule_before_gauges = _section_rule()
        root.addWidget(self._rule_before_gauges)

        # Gauges
        self._gauge_block = QWidget()
        gauge_outer = QVBoxLayout(self._gauge_block)
        gauge_outer.setContentsMargins(*_SECTION_INSET_MARGINS)
        gauge_outer.setSpacing(10)
        gauge_header_row = QHBoxLayout()
        gauge_header_row.setContentsMargins(0, 0, 0, 0)
        gauge_header_row.setSpacing(4)
        gauge_title = QLabel("Dashboard API Breakdown")
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
        root.addWidget(self._gauge_block)

        self._rule_before_on_demand = _section_rule()
        root.addWidget(self._rule_before_on_demand)

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
        root.addWidget(self._on_demand_card)

        self._rule_before_actions = _section_rule()
        root.addWidget(self._rule_before_actions)

        self._token_panel = QFrame()
        self._token_panel.setObjectName("insetCard")
        token_layout = QVBoxLayout(self._token_panel)
        token_layout.setContentsMargins(12, 10, 12, 10)
        token_layout.setSpacing(6)
        token_title = QLabel("Session token")
        token_title.setObjectName("sectionTitle")
        token_layout.addWidget(token_title)
        token_hint = QLabel(
            "Paste WorkosCursorSessionToken from DevTools → Application → Cookies → cursor.com."
        )
        token_hint.setObjectName("mutedLabel")
        token_hint.setWordWrap(True)
        token_layout.addWidget(token_hint)
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
        action_layout = QHBoxLayout(self._action_row)
        action_layout.setContentsMargins(*_SECTION_INSET_MARGINS)
        action_layout.setSpacing(6)
        action_layout.addWidget(self._btn_toggle)
        action_layout.addWidget(self._btn_refresh, 1)
        action_layout.addWidget(self._btn_dashboard, 1)
        root.addWidget(self._action_row)

        self._rule_before_metadata = _section_rule()
        root.addWidget(self._rule_before_metadata)

        self._btn_refresh.clicked.connect(self._on_manual_refresh_clicked)
        self._btn_token.clicked.connect(self.show_token_editor)
        self._btn_toggle.clicked.connect(self.toggle_compact)
        self._btn_dashboard.clicked.connect(self._open_dashboard)
        self._btn_settings.clicked.connect(self._toggle_settings_popup)
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
        root.addWidget(self._metadata_block)

        self._apply_compact_visibility()
        self._apply_active_theme()
        self._sync_notify_bells_from_settings()
        self._resize_to_mode()

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
            popup.position_near_global(at_global)
        else:
            popup.position_below(self._btn_settings)
        popup.show()

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
        self._btn_quit.setIcon(material_icon("close", palette.close_icon))
        self._refresh_frames = _rotated_icons("refresh", palette.action_icon, 18)
        self._content_frames = _rotated_icons("progress_activity", palette.cyan, 28)
        if self._refresh_busy or self._content_busy:
            self._paint_busy_frame()
        else:
            self._btn_refresh.setIcon(self._refresh_frames[0])
            self._loading_icon.setPixmap(self._content_frames[0].pixmap(28, 28))
        self._btn_dashboard.setIcon(material_icon("open_in_new", palette.action_icon))
        self._update_toggle_button()
        self._personal_icon.setPixmap(material_pixmap("person", palette.cyan, size=16))
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

        self._team_block.setVisible(vm.show_team_row and not self._compact)
        self._on_demand_card.setVisible(vm.show_on_demand_card and not self._compact)
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
            self._od_pct.setText(format_percent(od.progress_percent))
            footer_pool = "Team Pool" if od.pool_kind == "team" else "Personal Pool"
            self._od_amount.setText(f"{format_usd(od.on_demand_used_usd)} / {footer_pool}")
            self._od_bar.set_percent(od.progress_percent)

    def _clear_data_fields(self) -> None:
        self._personal_amount.setText("—")
        self._personal_pct.setText("—")
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
        compact = self._compact
        empty_loading = self._empty_loading()
        show_data = not login and not empty_loading
        self._loading_card.setVisible(empty_loading)
        self._login_card.setVisible(login)
        self._personal_card.setVisible(show_data)
        self._compact_total_row.setVisible(compact and show_data)
        self._team_block.setVisible(show_data and not compact and self._view_model.show_team_row)
        self._gauge_block.setVisible(show_data and not compact)
        self._on_demand_card.setVisible(
            show_data and not compact and self._view_model.show_on_demand_card
        )
        self._metadata_block.setVisible(show_data and not compact)
        self._action_row.setVisible(not login)
        self._btn_settings.setVisible(not login)
        self._btn_token.setVisible(login)
        if login or empty_loading:
            self._hide_settings_popup()
        self._btn_dashboard.setVisible(not login and not compact)
        self._sync_section_rules()

    def _sync_section_rules(self) -> None:
        """One hairline between each visible section; hidden sections take their rule with them."""
        if self._needs_browser_login() or self._empty_loading():
            self._rule_before_team.setVisible(False)
            self._rule_before_gauges.setVisible(False)
            self._rule_before_on_demand.setVisible(False)
            self._rule_before_actions.setVisible(True)
            self._rule_before_metadata.setVisible(False)
            return
        compact = self._compact
        self._rule_before_team.setVisible(not self._team_block.isHidden())
        self._rule_before_gauges.setVisible(not compact)
        self._rule_before_on_demand.setVisible(not self._on_demand_card.isHidden())
        self._rule_before_actions.setVisible(True)
        self._rule_before_metadata.setVisible(not compact)

    def _start_browser_login(self) -> None:
        import time

        webbrowser.open(_LOGIN_URL)
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
        self._attempt_browser_import()

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
                "Could not read a Cursor session from the browser. Set the token manually."
            )
            return
        self._login_busy = True

        def task() -> None:
            try:
                result = import_session_token_from_browsers()
            except BrowserImportError as exc:
                self._login_import_failed.emit(str(exc))
                return
            except Exception:
                self._login_import_failed.emit("Could not read the browser session.")
                return
            self._login_imported.emit(result.token)

        import threading

        threading.Thread(target=task, name="cursor-usage-login-import", daemon=True).start()

    def _on_import_success(self, token: str) -> None:
        self._login_busy = False
        if not self._login_waiting:
            return
        try:
            self._store.set_token(token)
        except Exception as exc:
            self._finish_login_failed(str(exc))
            return
        self._stop_login_wait()
        self._login_error.hide()
        self._login_status.setText("Session saved. Refreshing usage…")
        self._login_status.show()
        self._resize_to_mode()
        self.refresh()

    def _on_import_error(self, message: str) -> None:
        self._login_busy = False
        if not self._login_waiting:
            return
        if not is_retryable_import_error(BrowserImportError(message)):
            self._finish_login_failed(message)
            return
        self._login_status.setText(
            "Still waiting for a cursor.com session. Finish signing in, then return here."
        )
        self._resize_to_mode()

    def _finish_login_failed(self, message: str) -> None:
        self._stop_login_wait()
        self._login_status.hide()
        self._login_status.setText("")
        self._login_error.setText(_login_failure_text(message))
        self._login_error.show()
        self._resize_to_mode()

    def _stop_login_wait(self) -> None:
        self._login_waiting = False
        self._login_timer.stop()
        self._set_login_spinner(False)

    def _set_login_spinner(self, active: bool) -> None:
        if active:
            self._spinner_index = 0
            self._btn_login.setEnabled(False)
            self._btn_login.setText(_SPINNER_FRAMES[0])
            self._spinner_timer.start()
            return
        self._spinner_timer.stop()
        self._btn_login.setEnabled(True)
        self._btn_login.setText("Log in to Cursor")

    def _advance_login_spinner(self) -> None:
        self._spinner_index = (self._spinner_index + 1) % len(_SPINNER_FRAMES)
        self._btn_login.setText(_SPINNER_FRAMES[self._spinner_index])

    def _update_toggle_button(self) -> None:
        icon_color = active_palette().toggle_text
        if self._compact:
            self._btn_toggle.setIcon(material_icon("expand_more", icon_color))
            self._btn_toggle.setText("Expand")
            self._btn_toggle.setToolTip("Show full details")
        else:
            self._btn_toggle.setIcon(material_icon("expand_less", icon_color))
            self._btn_toggle.setText("Collapse")
            self._btn_toggle.setToolTip("Show less detail")

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        self._app_settings = load_app_settings()
        self._sync_theme_from_settings()
        self._sync_notify_bells_from_settings()
        if self._settings_popup is not None:
            self._sync_tray_display_radios()
            self._sync_theme_radios()
        if self._refresh_metrics_locked:
            return
        self._refresh_metrics_locked = True
        QTimer.singleShot(0, self._lock_refresh_button_metrics)

    def _lock_refresh_button_metrics(self) -> None:
        """Keep the on-screen Refresh size. Later icon frames must not relayout it."""
        self._btn_refresh.setFixedHeight(self._btn_toggle.height())
        self._btn_refresh.setMinimumWidth(self._btn_refresh.width())
        self._resize_to_mode()

    def _resize_to_mode(self) -> None:
        self.setFixedHeight(self.preferred_height())
        window = self.window()
        if window is not None and hasattr(window, "resize_for_content"):
            if getattr(window, "_card", None) is not None:
                window.resize_for_content()

    def _set_data_dimmed(self, dimmed: bool) -> None:
        for widget in (
            self._personal_card,
            self._rule_before_team,
            self._compact_total_row,
            self._team_block,
            self._rule_before_gauges,
            self._gauge_block,
            self._rule_before_on_demand,
            self._on_demand_card,
            self._rule_before_metadata,
            self._metadata_block,
        ):
            if not dimmed:
                self._opacity_fader.fade_to(widget, 1.0, remove_at_full=True)
                continue
            self._opacity_fader.fade_to(widget, _DATA_DIM_OPACITY)


def _login_failure_text(message: str) -> str:
    lowered = message.lower()
    if "appbound" in lowered or "decrypt" in lowered or "running as admin" in lowered:
        return (
            "Couldn’t read the browser session. Windows blocked cookie access. "
            "Use Set token and paste WorkosCursorSessionToken from DevTools."
        )
    return (
        "No Cursor session was found. Sign in in the browser and try again, "
        "or use Set token to paste it manually."
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
