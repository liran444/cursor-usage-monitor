# Authentication

Cursor Usage Monitor calls `GET https://cursor.com/api/usage-summary` using the browser session cookie **`WorkosCursorSessionToken`**. The app stores this value locally so it can refresh usage in the background.

## Manual token (recommended fallback)

1. Log in at [cursor.com](https://cursor.com) in Chrome, Edge, Firefox, or Brave.
2. Open DevTools → **Application** (Chrome) or **Storage** (Firefox) → **Cookies** → `https://cursor.com`.
3. Copy the **Value** of `WorkosCursorSessionToken` only — not the cookie name, not `WorkosCursorSessionToken=...`.

Save it with one of:

```text
cursor-usage token set
```

(paste, then Enter), or:

```text
cursor-usage token set --file path\to\token.txt
cursor-usage token set --clipboard
```

Verify:

```text
cursor-usage token test
```

Remove:

```text
cursor-usage token clear
```

### DevTools formats

The normalizer accepts:

- Plain value with `::` separators (as shown in DevTools).
- URL-encoded value with `%3A%3A` instead of `::`.

It **rejects** pasting the full cookie line (`WorkosCursorSessionToken=...`).

## Browser import

```text
cursor-usage token import
```

The app scans Chrome, Edge, Brave, and Firefox (all profiles the library can open) for `WorkosCursorSessionToken` on `cursor.com`, then saves it the same way as manual entry.

```text
cursor-usage token import --clipboard
```

Reads the clipboard (pyperclip, or PySide6 if installed) and saves after normalization.

### Common failures

| Situation | What to do |
|-----------|------------|
| Not logged in to cursor.com | Log in in a supported browser, then import again or set manually. |
| Safari | Not supported for automatic import; use manual token. |
| macOS | Browser cookie databases may require **Full Disk Access** for Terminal or the packaged app. |
| Linux | Ensure the browser is installed for your user; some distros lock cookie DB permissions. |
| Expired session | Token test fails; log in again and re-import or set a new token. |
| Corporate WAF / VPN | `token test` or `fetch` may report blocked/HTML responses; try another network. |

## Where the token is stored

1. **OS credential store** (Windows Credential Manager, macOS Keychain, Secret Service on Linux) via the `keyring` library.
2. **File fallback** if keyring is unavailable: `session_token` under the app config directory (user-only permissions on Unix).

The token is **never written to logs** or printed by successful commands.

## Security

- Treat the session token like a password: anyone with it can act as your Cursor web session.
- **Do not paste the token into chat, tickets, or screenshots.**
- Do not commit token files to git.
- Use `cursor-usage token clear` before sharing a machine or disk image.
- Prefer OS keyring; the file fallback is a convenience when keyring fails, not a substitute for disk encryption.

## CLI fetch

```text
cursor-usage fetch
```

Uses the stored token and updates `usage_cache.json` (see cache contract in the project plan). With no token, fetch writes a `not_authenticated` error envelope and exits with code 1.
