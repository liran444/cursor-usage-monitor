"""Default widget display preference when the usage window opens."""

import json
import os

import pytest

from cursor_usage_app.auth.session_store import SessionStore
from cursor_usage_app.cache.usage_cache import CacheEnvelopeOk, utc_now_iso
from cursor_usage_app.domain.mapper import UsageSummaryMapper
from cursor_usage_app.settings.app_settings import AppSettings, load_app_settings, save_app_settings
from fixture_loader import load_fixture

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


def _team_cache_dict() -> dict:
    snapshot = UsageSummaryMapper.from_api_payload(load_fixture("usage_summary_team_pool.json"))
    envelope = CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso())
    return envelope.to_dict()


def _widget_with_team_cache(qapp, tmp_path, monkeypatch, *, display: str = "expanded"):
    from cursor_usage_app.app.widget.usage_widget import UsageWidget

    settings_path = tmp_path / "settings.json"
    cache_path = tmp_path / "usage_cache.json"
    cache_path.write_text(json.dumps(_team_cache_dict()), encoding="utf-8")
    save_app_settings(AppSettings(widget_default_display=display), settings_path)
    monkeypatch.setattr(
        "cursor_usage_app.settings.app_settings.default_settings_path",
        lambda: settings_path,
    )
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::test")
    widget = UsageWidget(cache_path=cache_path, store=store)
    qapp.processEvents()
    return widget


def test_startup_compact_default_matches_manual_set_compact(qapp, tmp_path, monkeypatch) -> None:
    expanded = _widget_with_team_cache(qapp, tmp_path, monkeypatch, display="expanded")
    expanded.show()
    qapp.processEvents()
    assert expanded.is_compact() is False
    expanded.set_compact(True)
    expected_height = expanded.height()

    compact = _widget_with_team_cache(qapp, tmp_path, monkeypatch, display="compact")
    compact.show()
    qapp.processEvents()
    assert compact.is_compact() is True
    assert compact._btn_toggle.text() == "Expand"
    assert compact.height() == expected_height
    assert compact._layout_anim is None


def test_startup_compact_show_does_not_start_layout_animation(qapp, tmp_path, monkeypatch) -> None:
    widget = _widget_with_team_cache(qapp, tmp_path, monkeypatch, display="compact")
    widget.show()
    qapp.processEvents()
    assert widget.is_compact() is True
    assert widget._layout_anim is None


def test_compact_default_through_window_matches_manual_collapse_height(
    qapp,
    tmp_path,
    monkeypatch,
) -> None:
    from cursor_usage_app.app.widget.usage_window import UsageWindow

    settings_path = tmp_path / "settings.json"
    cache_path = tmp_path / "usage_cache.json"
    cache_path.write_text(json.dumps(_team_cache_dict()), encoding="utf-8")
    monkeypatch.setattr(
        "cursor_usage_app.settings.app_settings.default_settings_path",
        lambda: settings_path,
    )
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::test")

    save_app_settings(AppSettings(widget_default_display="expanded"), settings_path)
    reference = UsageWindow(cache_path=cache_path, store=store, auto_center=False)
    reference.show()
    qapp.processEvents()
    reference.widget().set_compact(True)
    qapp.processEvents()
    expected_window_height = reference.height()
    expected_card_height = reference.widget().height()
    reference.hide()

    save_app_settings(AppSettings(widget_default_display="compact"), settings_path)
    window = UsageWindow(cache_path=cache_path, store=store, auto_center=False)
    card = window.widget()
    window.show()
    shown_height = window.height()
    qapp.processEvents()
    assert card.is_compact() is True
    assert window.height() == shown_height
    assert window.height() == expected_window_height
    assert card.height() == expected_card_height
    assert card._layout_anim is None


def test_changing_default_display_persists_without_snapping_live_widget(
    qapp,
    monkeypatch,
    tmp_path,
) -> None:
    from cursor_usage_app.app.widget.usage_widget import UsageWidget

    settings_path = tmp_path / "settings.json"
    save_app_settings(AppSettings(widget_default_display="expanded"), settings_path)
    monkeypatch.setattr(
        "cursor_usage_app.settings.app_settings.default_settings_path",
        lambda: settings_path,
    )

    def fake_mutate(mutator, path=None):
        updated = mutator(load_app_settings(settings_path))
        save_app_settings(updated, settings_path)
        return updated

    monkeypatch.setattr(
        "cursor_usage_app.app.widget.usage_widget.mutate_app_settings",
        fake_mutate,
    )

    widget = UsageWidget()
    assert widget.is_compact() is False
    widget._ensure_settings_popup()
    widget._app_settings = AppSettings(widget_default_display="expanded")
    widget._sync_widget_default_display_radios()

    widget._radio_widget_collapsed.setChecked(True)

    assert load_app_settings(settings_path).widget_default_display == "compact"
    assert widget.is_compact() is False


def test_reopening_applies_saved_default_display(qapp, tmp_path, monkeypatch) -> None:
    from cursor_usage_app.app.widget.usage_window import UsageWindow

    settings_path = tmp_path / "settings.json"
    cache_path = tmp_path / "usage_cache.json"
    cache_path.write_text(json.dumps(_team_cache_dict()), encoding="utf-8")
    save_app_settings(AppSettings(widget_default_display="expanded"), settings_path)
    monkeypatch.setattr(
        "cursor_usage_app.settings.app_settings.default_settings_path",
        lambda: settings_path,
    )
    store = SessionStore(fallback_path=tmp_path / "session_token")
    store.set_token("user_01::test")
    window = UsageWindow(cache_path=cache_path, store=store, auto_center=False)
    card = window.widget()

    window.show()
    qapp.processEvents()
    assert card.is_compact() is False
    card.set_compact(True)
    assert card.is_compact() is True

    window.hide()
    save_app_settings(AppSettings(widget_default_display="expanded"), settings_path)
    window.show()
    qapp.processEvents()
    assert card.is_compact() is False
    assert card._layout_anim is None

    card.set_compact(True)
    collapsed_height = card.height()
    card.set_compact(False)
    window.hide()
    save_app_settings(AppSettings(widget_default_display="compact"), settings_path)
    assert card.is_compact() is True
    window.show()
    qapp.processEvents()
    assert card.is_compact() is True
    assert card.height() == collapsed_height
    assert card._layout_anim is None
