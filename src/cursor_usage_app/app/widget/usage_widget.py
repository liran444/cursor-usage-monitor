"""Main usage card content."""

from __future__ import annotations

import webbrowser
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cursor_usage_app.app.widget import colors
from cursor_usage_app.app.widget.fetch_worker import load_cache, start_fetch_in_thread
from cursor_usage_app.app.widget.formatting import (
    format_datetime_display,
    format_percent,
    format_pool_percent,
    format_usd,
)
from cursor_usage_app.app.widget.gauge_widget import DonutGauge, MiniTotalGauge, SegmentedTotalGauge
from cursor_usage_app.app.widget.progress_bar import HorizontalBar
from cursor_usage_app.app.widget.set_token_dialog import SetTokenDialog
from cursor_usage_app.app.widget.view_model import WidgetViewModel, view_model_from_envelope, view_model_loading
from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.cache.usage_cache import CacheEnvelope, parse_cache_envelope
from cursor_usage_app.domain.models import UsageSnapshot

_WIDGET_WIDTH = 295
_FULL_HEIGHT = 620
_COMPACT_HEIGHT = 230
_DASHBOARD_URL = "https://cursor.com/dashboard/usage"


class UsageWidget(QWidget):
    """Usage monitor card; supports full and compact layouts."""

    quit_requested = Signal()
    hide_requested = Signal()
    compact_changed = Signal(bool)

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
        """Test/dev hook: load cache JSON from disk."""
        import json

        raw = json.loads(path.read_text(encoding="utf-8"))
        envelope = parse_cache_envelope(raw)
        self.apply_envelope(envelope)

    def apply_fixture_envelope_dict(self, raw: dict) -> None:
        envelope = parse_cache_envelope(raw)
        self.apply_envelope(envelope)

    def refresh(self) -> None:
        self._view_model = view_model_loading(self._view_model)
        self._render_view_model()
        self._fetch_thread = start_fetch_in_thread(
            self,
            cache_path=self._cache_path,
            store=self._store,
            on_finished=self._on_fetch_finished,
        )

    def preferred_height(self) -> int:
        return _COMPACT_HEIGHT if self._compact else _FULL_HEIGHT

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        self._inline_error = QLabel()
        self._inline_error.setWordWrap(True)
        self._inline_error.setStyleSheet(f"color: {colors.ERROR_TEXT.name()}; font-size: 11px;")
        self._inline_error.hide()
        root.addWidget(self._inline_error)

        # Personal
        self._personal_header = QLabel("Personal")
        self._personal_header.setStyleSheet("font-size: 13px; font-weight: 600; color: #e5e7eb;")
        root.addWidget(self._personal_header)

        personal_row = QHBoxLayout()
        self._personal_amount = QLabel()
        self._personal_amount.setStyleSheet("font-size: 14px; font-weight: bold;")
        self._personal_pct = QLabel()
        self._personal_pct.setStyleSheet(f"color: {colors.CYAN.name()}; font-weight: bold;")
        personal_row.addWidget(self._personal_amount)
        personal_row.addStretch()
        personal_row.addWidget(self._personal_pct)
        root.addLayout(personal_row)

        self._personal_bar = HorizontalBar(colors.CYAN)
        root.addWidget(self._personal_bar)

        # Compact mini total
        self._compact_total_row = QWidget()
        compact_layout = QHBoxLayout(self._compact_total_row)
        compact_layout.setContentsMargins(0, 0, 0, 0)
        compact_layout.addWidget(QLabel("TOTAL"))
        self._mini_total = MiniTotalGauge()
        compact_layout.addWidget(self._mini_total)
        compact_layout.addStretch()
        self._compact_total_pct = QLabel()
        self._compact_total_pct.setStyleSheet("font-size: 16px; font-weight: bold;")
        compact_layout.addWidget(self._compact_total_pct)
        root.addWidget(self._compact_total_row)

        # Team
        self._team_block = QWidget()
        team_layout = QVBoxLayout(self._team_block)
        team_layout.setContentsMargins(0, 0, 0, 0)
        team_layout.setSpacing(6)
        self._team_header = QLabel("Team")
        self._team_header.setStyleSheet("font-size: 13px; font-weight: 600;")
        team_layout.addWidget(self._team_header)
        team_row = QHBoxLayout()
        self._team_amount = QLabel()
        self._team_amount.setStyleSheet("font-size: 14px; font-weight: bold;")
        self._team_pct = QLabel()
        self._team_pct.setStyleSheet(f"color: {colors.GREEN.name()}; font-weight: bold;")
        team_row.addWidget(self._team_amount)
        team_row.addStretch()
        team_row.addWidget(self._team_pct)
        team_layout.addLayout(team_row)
        root.addWidget(self._team_block)

        # Gauges
        self._gauge_block = QWidget()
        gauge_outer = QVBoxLayout(self._gauge_block)
        gauge_outer.setContentsMargins(0, 0, 0, 0)
        gauge_title = QLabel("Dashboard API Breakdown")
        gauge_title.setStyleSheet("font-size: 13px; font-weight: 600;")
        gauge_outer.addWidget(gauge_title)

        gauge_row = QHBoxLayout()
        self._total_gauge = SegmentedTotalGauge()
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.VLine)
        divider.setStyleSheet(f"color: {colors.BORDER_WINDOW.name()};")
        divider.setFixedWidth(1)
        self._api_gauge = DonutGauge("API", colors.CYAN)
        self._auto_gauge = DonutGauge("AUTO", colors.VIOLET)
        gauge_row.addWidget(self._total_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gauge_row.addWidget(divider)
        gauge_row.addWidget(self._api_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gauge_row.addWidget(self._auto_gauge, alignment=Qt.AlignmentFlag.AlignCenter)
        gauge_outer.addLayout(gauge_row)
        root.addWidget(self._gauge_block)

        # On demand card
        self._on_demand_card = QFrame()
        self._on_demand_card.setStyleSheet(
            f"background: {colors.BG_CARD.name()}; border: 1px solid {colors.BORDER_CARD.name()}; "
            "border-radius: 8px;"
        )
        od_layout = QVBoxLayout(self._on_demand_card)
        od_layout.setContentsMargins(10, 10, 10, 10)
        od_header = QHBoxLayout()
        od_title = QLabel("On Demand Usage")
        od_title.setStyleSheet("font-weight: 600;")
        self._od_pct = QLabel()
        self._od_pct.setStyleSheet(f"color: {colors.CORAL.name()}; font-weight: bold;")
        od_header.addWidget(od_title)
        od_header.addStretch()
        od_header.addWidget(self._od_pct)
        od_layout.addLayout(od_header)
        self._od_subcopy = QLabel()
        self._od_subcopy.setStyleSheet(f"color: {colors.TEXT_MUTED.name()}; font-size: 11px;")
        od_layout.addWidget(self._od_subcopy)
        self._od_bar = HorizontalBar(colors.CORAL)
        od_layout.addWidget(self._od_bar)
        self._od_footer = QLabel()
        self._od_footer.setStyleSheet("font-size: 11px;")
        od_layout.addWidget(self._od_footer)
        root.addWidget(self._on_demand_card)

        # Summary lines
        self._summary_block = QWidget()
        summary_layout = QVBoxLayout(self._summary_block)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        self._summary_personal = QLabel()
        self._summary_personal_od = QLabel()
        self._summary_team = QLabel()
        for label in (self._summary_personal, self._summary_personal_od, self._summary_team):
            label.setStyleSheet(f"color: {colors.TEXT_MUTED.name()}; font-size: 11px;")
            summary_layout.addWidget(label)
        root.addWidget(self._summary_block)

        # Actions
        actions_title = QLabel("Dashboard API Metrics")
        actions_title.setStyleSheet("font-size: 13px; font-weight: 600;")
        root.addWidget(actions_title)

        btn_grid = QGridLayout()
        btn_grid.setHorizontalSpacing(8)
        btn_grid.setVerticalSpacing(6)
        self._btn_refresh = QPushButton("🔄 Refresh")
        self._btn_token = QPushButton("Set token...")
        self._btn_toggle = QPushButton("Collapse")
        self._btn_toggle.setStyleSheet(f"color: {colors.AMBER.name()}; font-weight: 600;")
        self._btn_dashboard = QPushButton("Open dashboard")
        self._btn_quit = QPushButton("🚪 Quit")

        btn_grid.addWidget(self._btn_refresh, 0, 0)
        btn_grid.addWidget(self._btn_token, 0, 1)
        btn_grid.addWidget(self._btn_toggle, 1, 0)
        btn_grid.addWidget(self._btn_dashboard, 1, 1)
        btn_grid.addWidget(self._btn_quit, 1, 2)
        root.addLayout(btn_grid)

        self._btn_refresh.clicked.connect(self.refresh)
        self._btn_token.clicked.connect(self._open_set_token)
        self._btn_toggle.clicked.connect(self.toggle_compact)
        self._btn_dashboard.clicked.connect(lambda: webbrowser.open(_DASHBOARD_URL))
        self._btn_quit.clicked.connect(self.quit_requested.emit)

        # Metadata
        self._metadata_block = QWidget()
        meta_layout = QVBoxLayout(self._metadata_block)
        meta_layout.setContentsMargins(0, 0, 0, 0)
        meta_title = QLabel("Metadata")
        meta_title.setStyleSheet("font-size: 13px; font-weight: 600;")
        meta_layout.addWidget(meta_title)
        status_label = QLabel("Status & Resets")
        status_label.setStyleSheet(f"color: {colors.TEXT_MUTED.name()}; font-size: 11px;")
        meta_layout.addWidget(status_label)
        self._meta_fetched = QLabel()
        self._meta_reset = QLabel()
        for label in (self._meta_fetched, self._meta_reset):
            label.setStyleSheet("font-size: 11px;")
            meta_layout.addWidget(label)
        root.addWidget(self._metadata_block)

        self._apply_compact_visibility()
        self._resize_to_mode()

    def _on_fetch_finished(self, _exit_code: int) -> None:
        self.reload_from_cache()

    def _open_set_token(self) -> None:
        dialog = SetTokenDialog(self, store=self._store)
        if dialog.exec():
            self.refresh()

    def _render_view_model(self) -> None:
        vm = self._view_model
        self._show_inline_message(vm.inline_message)

        snapshot = vm.snapshot
        if snapshot is not None:
            self._fill_snapshot(snapshot)
        elif vm.phase == "error":
            self._clear_data_fields()

        self._team_block.setVisible(vm.show_team_row and not self._compact)
        self._on_demand_card.setVisible(vm.show_on_demand_card and not self._compact)

        fetched = format_datetime_display(vm.fetched_at)
        self._meta_fetched.setText(f"Last Fetched:  {fetched}")
        reset = format_datetime_display(snapshot.billing_cycle_end if snapshot else None)
        self._meta_reset.setText(f"Next Reset:    {reset}")

    def _show_inline_message(self, message: str | None) -> None:
        if message is None or message == "":
            self._inline_error.hide()
            self._inline_error.setText("")
            return
        self._inline_error.setText(message)
        self._inline_error.show()

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
                f"👥 {format_usd(snapshot.team_pool.used_usd)} / "
                f"{format_usd(snapshot.team_pool.limit_usd)}"
            )
            self._team_pct.setText(format_percent(team_pct))
            self._summary_team.setText(f"Team ({format_percent(team_pct)})")
            self._summary_team.show()
        else:
            self._summary_team.hide()

        od = snapshot.on_demand_display
        if od.show_card:
            self._od_pct.setText(format_percent(od.progress_percent))
            pool = "Team" if od.pool_kind == "team" else "Personal"
            self._od_subcopy.setText(
                f"On-Demand: {format_usd(od.personal_on_demand_used_usd)} used / Pool: {pool}"
            )
            self._od_bar.set_percent(od.progress_percent)
            footer_pool = "Team Pool" if od.pool_kind == "team" else "Personal Pool"
            self._od_footer.setText(f"{format_usd(od.on_demand_used_usd)} / {footer_pool}")

        self._summary_personal.setText(
            f"Personal: {format_usd(snapshot.personal.used_usd)} / "
            f"{format_usd(snapshot.personal.limit_usd)}"
        )
        personal_od = snapshot.personal_on_demand.used_usd if snapshot.personal_on_demand else None
        self._summary_personal_od.setText(f"Personal on-demand: {format_usd(personal_od)}")

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
        self._summary_personal.setText("Personal: —")
        self._summary_personal_od.setText("Personal on-demand: —")
        self._summary_team.hide()
        self._meta_reset.setText("Next Reset:    —")

    def _apply_compact_visibility(self) -> None:
        compact = self._compact
        self._compact_total_row.setVisible(compact)
        self._team_block.setVisible(not compact and self._view_model.show_team_row)
        self._gauge_block.setVisible(not compact)
        self._on_demand_card.setVisible(not compact and self._view_model.show_on_demand_card)
        self._summary_block.setVisible(not compact)
        self._metadata_block.setVisible(not compact)

    def _update_toggle_button(self) -> None:
        if self._compact:
            self._btn_toggle.setText("Expand")
        else:
            self._btn_toggle.setText("Collapse")

    def _resize_to_mode(self) -> None:
        self.setFixedHeight(self.preferred_height())
        window = self.window()
        if window is not None and hasattr(window, "resize_for_content"):
            if getattr(window, "_card", None) is not None:
                window.resize_for_content()
