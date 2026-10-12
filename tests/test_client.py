import httpx
import pytest

from cursor_usage_app.api.client import UsageSummaryClient, UsageSummaryHttpError
from fixture_loader import load_fixture


def test_fetch_raw_success() -> None:
    payload = load_fixture("usage_summary_personal_only.json")

    def handler(request: httpx.Request) -> httpx.Response:
        cookie_header = request.headers.get("cookie", "")
        assert "WorkosCursorSessionToken=test-token" in cookie_header
        assert "cursor.com/api/usage-summary" in str(request.url)
        return httpx.Response(200, json=payload, headers={"content-type": "application/json"})

    client = UsageSummaryClient(transport=httpx.MockTransport(handler))
    result = client.fetch_raw("test-token")
    assert result["billingCycleEnd"] == payload["billingCycleEnd"]


def test_detects_html_waf() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"<html><body>blocked</body></html>",
            headers={"content-type": "text/html"},
        )

    client = UsageSummaryClient(transport=httpx.MockTransport(handler))
    with pytest.raises(UsageSummaryHttpError) as exc:
        client.fetch_raw("x")
    assert exc.value.code == "blocked_or_waf"


def test_auth_status_maps_to_not_authenticated() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    client = UsageSummaryClient(transport=httpx.MockTransport(handler))
    with pytest.raises(UsageSummaryHttpError) as exc:
        client.fetch_raw("x")
    assert exc.value.code == "not_authenticated"
    assert exc.value.status_code == 401
