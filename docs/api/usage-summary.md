# usage-summary API

- **Endpoint:** `GET https://cursor.com/api/usage-summary`
- **Session cookie:** `WorkosCursorSessionToken` (value is the WorkOS session token from the browser; do not log or commit it)

## Request

The client sends browser-like headers (`User-Agent`, `Accept`, `Referer`, `Origin`) and the session cookie above.

## Response (JSON object)

Fields read by `UsageSummaryMapper`:

| JSON path | Type | Mapped to |
| --- | --- | --- |
| `billingCycleEnd` | string (ISO-8601) | `UsageSnapshot.billing_cycle_end` |
| `individualUsage.used` | number (cents) | Personal pool `used_usd` (÷ 100) |
| `individualUsage.limit` | number (cents) | Personal pool `limit_usd` (÷ 100) |
| `individualUsage.plan.used` | number (cents) | Personal pool `used_usd` when top-level `used`/`limit` absent |
| `individualUsage.plan.limit` | number (cents) | Personal pool `limit_usd` when top-level `used`/`limit` absent |
| `individualUsage.plan.totalPercentUsed` | number | Dashboard TOTAL % (tray ring, widget) |
| `individualUsage.plan.apiPercentUsed` | number | API segment of TOTAL arc |
| `individualUsage.plan.autoPercentUsed` | number | Auto segment of TOTAL arc |
| `individualUsage.onDemand.used` | number (cents) | Personal on-demand spend (subcopy) |
| `individualUsage.onDemand.limit` | number (cents) | Personal on-demand pool limit |
| `teamUsage.used` | number (cents) | Team pool `used_usd` (row hidden if absent) |
| `teamUsage.limit` | number (cents) | Team pool `limit_usd` |
| `teamUsage.onDemand.used` | number (cents) | Team pool `used_usd` when top-level `used`/`limit` absent |
| `teamUsage.onDemand.limit` | number (cents) | Team pool `limit_usd` when top-level `used`/`limit` absent |

`teamUsage` may be omitted for personal-only accounts.

## Team pool rules (mapper)

- **Team row:** `teamUsage.used` / `teamUsage.limit` when present; otherwise the same fields from `teamUsage.onDemand` (limit may be derived from `used` + `remaining`).
- **On-demand card:** `individualUsage.onDemand` only (personal pay-as-you-go). Team budget is never shown on this card.

## Errors (HTTP)

| Condition | Cache `error.code` |
| --- | --- |
| HTTP 401 / 403 | `not_authenticated` |
| HTML body or `text/html` content type | `blocked_or_waf` |
| Timeout / connection failure | `network` |
| Other non-success status or invalid JSON | `unknown` |

Successful fetches are stored locally as `{ "ok": true, "data": <UsageSnapshot>, "fetchedAt": "<ISO-8601 UTC>" }`.
