"""Fire tray notifications when usage crosses configured thresholds."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeOk
from cursor_usage_app.settings.app_settings import (
    AppSettings,
    UsageNotificationState,
    load_app_settings,
    save_app_settings,
)
from cursor_usage_app.usage_notifications import (
    format_notification_message,
    notification_fired_key,
    thresholds_to_notify,
    usage_percent_for_section,
)


class UsageNotifier:
    def __init__(self, settings_path: Path | None = None) -> None:
        self._settings_path = settings_path

    def process_envelope(
        self,
        envelope: CacheEnvelope | None,
        show_message: Callable[[str, str], None],
    ) -> None:
        if not isinstance(envelope, CacheEnvelopeOk):
            return

        settings = load_app_settings(self._settings_path)
        snapshot = envelope.data
        state = self._state_for_cycle(settings.usage_notification_state, snapshot.billing_cycle_end)

        new_fired = set(state.fired_keys)
        pending_messages: list[tuple[str, int, float | None]] = []

        for section_id, enabled in settings.usage_notifications.items():
            if not enabled:
                continue
            percent = usage_percent_for_section(snapshot, section_id)
            for threshold in thresholds_to_notify(percent, section_id, frozenset(new_fired)):
                new_fired.add(notification_fired_key(section_id, threshold))
                pending_messages.append((section_id, threshold, percent))

        updated_state = UsageNotificationState(
            billing_cycle_end=snapshot.billing_cycle_end,
            fired_keys=frozenset(new_fired),
        )
        if updated_state != state:
            settings = settings.with_usage_notification_state(updated_state)
            save_app_settings(settings, self._settings_path)

        for section_id, threshold, percent in pending_messages:
            body = format_notification_message(section_id, threshold, percent)
            show_message("Cursor Usage", body)

    @staticmethod
    def _state_for_cycle(
        state: UsageNotificationState,
        billing_cycle_end: str | None,
    ) -> UsageNotificationState:
        if state.billing_cycle_end == billing_cycle_end:
            return state
        return UsageNotificationState(billing_cycle_end=billing_cycle_end, fired_keys=frozenset())
