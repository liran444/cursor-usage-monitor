"""Persisted user preferences (Qt-free)."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from platformdirs import user_config_dir

_LOGGER = logging.getLogger(__name__)

_CONFIG_DIR_NAME = "cursor-usage-app"
_SETTINGS_FILE_NAME = "settings.json"

TrayDisplayMode = Literal["total_percent", "personal"]
DEFAULT_TRAY_DISPLAY_MODE: TrayDisplayMode = "total_percent"


@dataclass(frozen=True)
class UsageNotificationState:
    billing_cycle_end: str | None = None
    fired_keys: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class AppSettings:
    tray_display_mode: TrayDisplayMode = DEFAULT_TRAY_DISPLAY_MODE
    usage_notifications: dict[str, bool] = field(default_factory=dict)
    usage_notification_state: UsageNotificationState = field(default_factory=UsageNotificationState)

    def is_usage_notification_enabled(self, section_id: str) -> bool:
        return bool(self.usage_notifications.get(section_id, False))

    def with_tray_display_mode(self, mode: TrayDisplayMode) -> AppSettings:
        return AppSettings(
            tray_display_mode=mode,
            usage_notifications=dict(self.usage_notifications),
            usage_notification_state=self.usage_notification_state,
        )

    def with_usage_notification(self, section_id: str, enabled: bool) -> AppSettings:
        merged = dict(self.usage_notifications)
        merged[section_id] = enabled
        return AppSettings(
            tray_display_mode=self.tray_display_mode,
            usage_notifications=merged,
            usage_notification_state=self.usage_notification_state,
        )

    def with_usage_notification_state(self, state: UsageNotificationState) -> AppSettings:
        return AppSettings(
            tray_display_mode=self.tray_display_mode,
            usage_notifications=dict(self.usage_notifications),
            usage_notification_state=state,
        )


def default_settings_path() -> Path:
    base = Path(user_config_dir(_CONFIG_DIR_NAME, appauthor=False))
    return base / _SETTINGS_FILE_NAME


def _parse_tray_display_mode(raw: object) -> TrayDisplayMode:
    if raw in ("total_percent", "personal"):
        return raw
    return DEFAULT_TRAY_DISPLAY_MODE


def _parse_usage_notifications(raw: object) -> dict[str, bool]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, bool] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, bool):
            out[key] = value
    return out


def _parse_usage_notification_state(raw: object) -> UsageNotificationState:
    if not isinstance(raw, dict):
        return UsageNotificationState()
    cycle_end = raw.get("billing_cycle_end")
    if cycle_end is not None and not isinstance(cycle_end, str):
        cycle_end = None
    fired_raw = raw.get("fired_keys")
    fired: set[str] = set()
    if isinstance(fired_raw, list):
        for item in fired_raw:
            if isinstance(item, str):
                fired.add(item)
    return UsageNotificationState(billing_cycle_end=cycle_end, fired_keys=frozenset(fired))


def load_app_settings(path: Path | None = None) -> AppSettings:
    settings_path = path or default_settings_path()
    if not settings_path.is_file():
        return AppSettings()

    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _LOGGER.debug("Could not read app settings: %s", exc.__class__.__name__)
        return AppSettings()

    if not isinstance(raw, dict):
        return AppSettings()

    return AppSettings(
        tray_display_mode=_parse_tray_display_mode(raw.get("tray_display_mode")),
        usage_notifications=_parse_usage_notifications(raw.get("usage_notifications")),
        usage_notification_state=_parse_usage_notification_state(raw.get("usage_notification_state")),
    )


def mutate_app_settings(
    mutator: Callable[[AppSettings], AppSettings],
    path: Path | None = None,
) -> AppSettings:
    current = load_app_settings(path)
    updated = mutator(current)
    save_app_settings(updated, path)
    return updated


def save_app_settings(settings: AppSettings, path: Path | None = None) -> None:
    settings_path = path or default_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {"tray_display_mode": settings.tray_display_mode}
    if settings.usage_notifications:
        payload["usage_notifications"] = dict(settings.usage_notifications)
    state = settings.usage_notification_state
    if state.billing_cycle_end is not None or state.fired_keys:
        payload["usage_notification_state"] = {
            "billing_cycle_end": state.billing_cycle_end,
            "fired_keys": sorted(state.fired_keys),
        }
    settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
