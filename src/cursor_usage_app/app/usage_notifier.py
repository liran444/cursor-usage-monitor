"""Fire tray notifications when usage crosses configured thresholds."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from cursor_usage_app.cache.usage_cache import CacheEnvelope, CacheEnvelopeOk
from cursor_usage_app.settings.app_settings import load_app_settings, save_app_settings
from cursor_usage_app.usage_notifications import (
    acknowledge_thresholds,
    format_notification_message,
    notification_state_for_cycle,
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
        state = notification_state_for_cycle(
            settings.usage_notification_state,
            snapshot.billing_cycle_end,
        )

        pending_messages: list[tuple[str, int]] = []
        updated_state = state

        for section_id, enabled in settings.usage_notifications.items():
            if not enabled:
                continue
            percent = usage_percent_for_section(snapshot, section_id)
            for threshold in thresholds_to_notify(percent, section_id, updated_state.fired_keys):
                updated_state = acknowledge_thresholds(updated_state, section_id, [threshold])
                pending_messages.append((section_id, threshold))

        if updated_state != state:
            settings = settings.with_usage_notification_state(updated_state)
            save_app_settings(settings, self._settings_path)

        for section_id, threshold in pending_messages:
            body = format_notification_message(section_id, threshold)
            show_message("Cursor Usage", body)
