# Authentication

Session cookie **`WorkosCursorSessionToken`** from https://cursor.com (browser DevTools → Application → Cookies).

## Token format

The value looks like:

```
user_<id>%3A%3A<jwt>
```

DevTools may show `%3A%3A` (URL-encoded `::`) or literal `::` — both are fine. The app canonicalizes to `%3A%3A` on save.

Copy **only the cookie value**, not `WorkosCursorSessionToken=` and no quotes.

## Commands

```bash
cursor-usage token set
cursor-usage token test
cursor-usage token test --verbose
cursor-usage token clear
```

### Setting the token (pick one)

**Easiest (default):** copy from DevTools, then:

```powershell
cursor-usage token set
# Press Enter when the cookie is on your clipboard
```

**From a file** (best if the IDE terminal blocks paste):

```powershell
notepad token.txt   # paste cookie value, save, close
cursor-usage token set --file token.txt
del token.txt
```

**From clipboard explicitly:**

```powershell
cursor-usage token set --clipboard
```

Use `--verbose` on `token test` or `fetch` to print HTTP status and a short error body snippet (the token is never printed).

Stored in the OS keyring when available. On Windows, if Credential Manager fails, the token is saved to a local config file instead (`session.token` under your app config directory).

## Troubleshooting

| Symptom | What to try |
|---------|-------------|
| Can't paste in terminal | Use `token set --file token.txt` |
| `CredWrite` / memory error on Windows | Re-run `token set` — it will fall back to config file storage |
| `HTTP 400` / `http_error` | Re-copy the cookie; run `cursor-usage token test --verbose` |
| `not_authenticated` | Token expired — sign in at cursor.com and set a new token |
| `blocked_or_waf` | Response looked like HTML; retry later or check network/VPN |
| `invalid_token` | Paste was truncated or included the cookie name prefix |

If you pasted a token in chat or committed it anywhere, sign out of cursor.com, sign back in, and set a fresh token.

