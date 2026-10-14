"""Persisted user preferences (Qt-free)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from platformdirs import user_config_dir

_LOGGER = logging.getLogger(__name__)

_CONFIG_DIR_NAME = "cursor-usage-app"
_SETTINGS_FILE_NAME = "settings.json"

TrayDisplayMode = Literal["total_percent", "personal"]
DEFAULT_TRAY_DISPLAY_MODE: TrayDisplayMode = "total_percent"


@dataclass(frozen=True)
class AppSettings:
    tray_display_mode: TrayDisplayMode = DEFAULT_TRAY_DISPLAY_MODE


def default_settings_path() -> Path:
    base = Path(user_config_dir(_CONFIG_DIR_NAME, appauthor=False))
    return base / _SETTINGS_FILE_NAME


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

    mode = raw.get("tray_display_mode")
    if mode not in ("total_percent", "personal"):
        return AppSettings()

    return AppSettings(tray_display_mode=mode)


def save_app_settings(settings: AppSettings, path: Path | None = None) -> None:
    settings_path = path or default_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"tray_display_mode": settings.tray_display_mode}
    settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
