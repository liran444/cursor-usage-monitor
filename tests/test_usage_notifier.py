from unittest.mock import MagicMock

from cursor_usage_app.app.usage_notifier import UsageNotifier
from cursor_usage_app.cache.usage_cache import CacheEnvelopeOk, utc_now_iso
from cursor_usage_app.domain.models import (
    OnDemandDisplay,
    PlanPercents,
    UsagePool,
    UsageSnapshot,
)
from cursor_usage_app.settings.app_settings import AppSettings, save_app_settings


def _envelope(percent: float) -> CacheEnvelopeOk:
    snapshot = UsageSnapshot(
        billing_cycle_end="2026-11-01T00:00:00Z",
        personal=UsagePool(used_usd=percent, limit_usd=100.0),
        plan_percents=PlanPercents(
            total_percent_used=percent,
            api_percent_used=None,
            auto_percent_used=None,
        ),
        team_pool=None,
        personal_on_demand=None,
        team_on_demand=None,
        on_demand_display=OnDemandDisplay(
            show_card=False,
            progress_percent=None,
            pool_kind=None,
            personal_on_demand_used_usd=None,
            on_demand_used_usd=None,
        ),
    )
    return CacheEnvelopeOk(ok=True, data=snapshot, fetched_at=utc_now_iso())


def test_notifier_fires_crossed_thresholds(tmp_path) -> None:
    path = tmp_path / "settings.json"
    save_app_settings(
        AppSettings(usage_notifications={"personal": True}),
        path,
    )
    notifier = UsageNotifier(settings_path=path)
    show = MagicMock()
    notifier.process_envelope(_envelope(55.0), show)
    assert show.call_count == 1
    assert "50%" in show.call_args[0][1]

    show.reset_mock()
    notifier.process_envelope(_envelope(56.0), show)
    show.assert_not_called()

    notifier.process_envelope(_envelope(76.0), show)
    assert show.call_count == 1
    assert "75%" in show.call_args[0][1]
