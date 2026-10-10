"""System tray application."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
import webbrowser

import pystray

from cursor_usage.datetime_format import format_datetime_local
from cursor_usage.icon_builder import build_icon
from cursor_usage.paths import load_settings, lock_path, status_path
from cursor_usage.single_instance import ensure_single_instance
from cursor_usage.status_io import read_status
from cursor_usage.subprocess_fetch import spawn_fetch

DASHBOARD_URL = "https://cursor.com/dashboard/usage"


def _format_usd(value: float | None) -> str:
    if value is None:
        return "—"
    return f"${value:.2f}"


def _format_pct(value: float | int | None) -> str:
    if value is None:
        return "—"
    return f"{round(float(value))}%"


def _icon_label(status: dict | None) -> tuple[str | None, bool]:
    if status is None:
        return "—", False
    if not status.get("ok"):
        err = status.get("error") or ""
        if "not_authenticated" in str(err):
            return "!", True
        return "—", False
    personal = status.get("personalIncluded") or {}
    pct = personal.get("percentUsed")
    if pct is None:
        return "—", False
    settings = load_settings()
    warn_at = settings.get("warnPercentThreshold", 80)
    warn = isinstance(warn_at, (int, float)) and float(pct) >= float(warn_at)
    return f"{round(float(pct))}", warn


def _build_menu(status: dict | None, icon: pystray.Icon) -> pystray.Menu:
    items: list[pystray.MenuItem | pystray.Menu] = []

    if status is None:
        items.append(pystray.MenuItem("No data yet — Refresh", lambda: spawn_fetch()))
    elif not status.get("ok"):
        items.append(pystray.MenuItem(f"Error: {status.get('error', 'unknown')}", None, enabled=False))
    else:
        personal = status.get("personalIncluded") or {}
        items.append(
            pystray.MenuItem(
                f"Personal: {_format_usd(personal.get('usedUsd'))} / "
                f"{_format_usd(personal.get('limitUsd'))} "
                f"({_format_pct(personal.get('percentUsed'))} used, "
                f"{_format_pct(personal.get('percentRemaining'))} left)",
                None,
                enabled=False,
            )
        )
        on_demand = status.get("personalOnDemandUsd")
        if on_demand is not None:
            items.append(
                pystray.MenuItem(
                    f"Personal on-demand: {_format_usd(on_demand)}",
                    None,
                    enabled=False,
                )
            )
        team = status.get("teamPool")
        if team:
            items.append(
                pystray.MenuItem(
                    f"Team pool: {_format_usd(team.get('usedUsd'))} / "
                    f"{_format_usd(team.get('limitUsd'))} "
                    f"({_format_pct(team.get('percentUsed'))} used)",
                    None,
                    enabled=False,
                )
            )
        settings = load_settings()
        if settings.get("showDashboardPercentsInMenu", True):
            dash = status.get("dashboardPercents") or {}
            api_p = dash.get("apiPercentUsed")
            total_p = dash.get("totalPercentUsed")
            auto_p = dash.get("autoPercentUsed")
            if api_p is not None or total_p is not None:
                items.append(
                    pystray.MenuItem(
                        f"Dashboard API %: total={_format_pct(total_p)} "
                        f"api={_format_pct(api_p)} auto={_format_pct(auto_p)}",
                        None,
                        enabled=False,
                    )
                )
        end = status.get("billingCycleEnd")
        end_label = format_datetime_local(end) if end else None
        if end_label:
            items.append(pystray.MenuItem(f"Resets: {end_label}", None, enabled=False))
        fetched = status.get("fetchedAt")
        fetched_label = format_datetime_local(fetched) if fetched else None
        if fetched_label:
            items.append(pystray.MenuItem(f"Updated: {fetched_label}", None, enabled=False))

    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Refresh", lambda: spawn_fetch()))
    items.append(pystray.MenuItem("Set token…", lambda: _run_token_set()))
    items.append(pystray.MenuItem("Open dashboard", lambda: webbrowser.open(DASHBOARD_URL)))
    items.append(pystray.MenuItem("Quit", lambda: icon.stop()))

    return pystray.Menu(*items)


def _run_token_set() -> None:
    if getattr(sys, "frozen", False):
        cmd = [sys.executable, "token", "set"]
    else:
        cmd = [sys.executable, "-m", "cursor_usage.__main__", "token", "set"]
    subprocess.Popen(cmd)


def _poll_loop(icon: pystray.Icon, stop: threading.Event) -> None:
    last_mtime = 0.0
    last_fetch = time.time()
    path = status_path()
    while not stop.is_set():
        settings = load_settings()
        poll_min = settings.get("pollMinutes", 15)
        try:
            poll_sec = max(60, int(poll_min) * 60)
        except (TypeError, ValueError):
            poll_sec = 900

        if path.is_file():
            mtime = path.stat().st_mtime
            if mtime != last_mtime:
                last_mtime = mtime
                status = read_status(path)
                label, warn = _icon_label(status)
                icon.icon = build_icon(label, warn=warn)
                icon.menu = _build_menu(status, icon)
                if label is not None and hasattr(icon, "title"):
                    icon.title = f"Cursor usage {label}%"

        stop.wait(5)

        if time.time() - last_fetch >= poll_sec:
            spawn_fetch()
            last_fetch = time.time()


def run_tray() -> None:
    ensure_single_instance(lock_path())
    spawn_fetch()

    print("Cursor Usage Monitor tray is running.", flush=True)
    print(
        "This terminal stays open until you choose Quit from the tray menu or press Ctrl+C.",
        flush=True,
    )
    print(
        "On Windows, check the ^ overflow area near the clock if you do not see the icon.",
        flush=True,
    )

    path = status_path()
    status = read_status(path)
    label, warn = _icon_label(status)
    icon = pystray.Icon(
        "cursor-usage",
        build_icon(label, warn=warn),
        "Cursor Usage Monitor",
        menu=pystray.Menu(pystray.MenuItem("Loading…", None, enabled=False)),
    )

    def _setup(tray_icon: pystray.Icon) -> None:
        tray_icon.visible = True
        tray_icon.menu = _build_menu(read_status(path), tray_icon)
        stop = threading.Event()
        thread = threading.Thread(target=_poll_loop, args=(tray_icon, stop), daemon=True)
        thread.start()
        tray_icon._poll_stop = stop  # type: ignore[attr-defined]

    icon.run(setup=_setup)
