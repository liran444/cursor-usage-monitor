import json
from pathlib import Path

from cursor_usage.map_summary import map_usage_summary

FIXTURES = Path(__file__).parent / "fixtures"


def test_map_enterprise_personal_percent():
    payload = json.loads((FIXTURES / "usage_summary_enterprise.json").read_text(encoding="utf-8"))
    status = map_usage_summary(payload)
    assert status["ok"] is True
    personal = status["personalIncluded"]
    assert personal["usedUsd"] == 17.32
    assert personal["limitUsd"] == 20.0
    assert personal["percentUsed"] == 87
    assert personal["percentRemaining"] == 13
    team = status["teamPool"]
    assert team is not None
    assert team["usedUsd"] == 329.11
    assert team["limitUsd"] == 1278.0
    assert status["dashboardPercents"]["apiPercentUsed"] == 22


def test_map_no_team_pool():
    payload = json.loads((FIXTURES / "usage_summary_enterprise.json").read_text(encoding="utf-8"))
    del payload["teamUsage"]
    status = map_usage_summary(payload)
    assert status["teamPool"] is None
