"""Application paths via platformdirs."""

from __future__ import annotations

import json
from pathlib import Path

from platformdirs import PlatformDirs

APP_NAME = "cursor-usage"
APP_AUTHOR = "cursor-usage-monitor"

_dirs = PlatformDirs(appname=APP_NAME, appauthor=APP_AUTHOR)


def cache_dir() -> Path:
    path = Path(_dirs.user_cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def config_dir() -> Path:
    path = Path(_dirs.user_config_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def status_path() -> Path:
    return cache_dir() / "status.json"


def settings_path() -> Path:
    return config_dir() / "settings.json"


def lock_path() -> Path:
    return cache_dir() / "tray.lock"


DEFAULT_SETTINGS = {
    "pollMinutes": 15,
    "warnPercentThreshold": 80,
    "showDashboardPercentsInMenu": True,
}


def load_settings() -> dict:
    path = settings_path()
    if not path.is_file():
        return dict(DEFAULT_SETTINGS)
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)
    merged = dict(DEFAULT_SETTINGS)
    if isinstance(data, dict):
        merged.update(data)
    return merged


def save_settings(settings: dict) -> None:
    path = settings_path()
    with path.open("w", encoding="utf-8") as handle:
        json.dump(settings, handle, indent=2)
