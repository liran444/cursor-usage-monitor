# usage-summary field map (structure reference)

## Endpoint

`GET https://cursor.com/api/usage-summary`  
Cookie: `WorkosCursorSessionToken`

## Personal included (icon % source)

| Field | Type | Use |
|-------|------|-----|
| `individualUsage.plan.used` | cents | Personal used USD |
| `individualUsage.plan.limit` | cents | Personal limit USD |
| `individualUsage.plan.remaining` | cents | Personal remaining USD |
| Computed | — | **Icon %** = `used/limit*100`, not `apiPercentUsed` |

## Team pool

| Field | Type | Use |
|-------|------|-----|
| `teamUsage.onDemand.used` | cents | Team spend used |
| `teamUsage.onDemand.limit` | cents | Team cap |
| `teamUsage.onDemand.remaining` | cents | Team remaining |

## Dashboard-only percents

| Field | Notes |
|-------|--------|
| `autoPercentUsed` | Cursor Models meter; may stay 0 on enterprise Composer-only |
| `apiPercentUsed` | Dashboard "API usage" %; may use ~$80 internal denominator |
| `totalPercentUsed` | Often equals `apiPercentUsed` when auto is 0 |

## Other

| Field | Use |
|-------|-----|
| `billingCycleEnd` | Reset date in menu |
| `individualUsage.onDemand.used` | Personal on-demand USD line |

See `tests/fixtures/usage_summary_enterprise.json` for anonymized shape (amounts illustrative).
