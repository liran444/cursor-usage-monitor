# Authentication

Cursor Usage Monitor calls `GET https://cursor.com/api/usage-summary` using the browser session cookie **`WorkosCursorSessionToken`**. The app stores this value locally so it can refresh usage in the background.

For privacy (what is stored, browser cookie import, polling) and disclaimers, see
[PRIVACY.md](PRIVACY.md) and [DISCLAIMER.md](DISCLAIMER.md).

## Manual token (recommended fallback)

1. Log in at [cursor.com](https://cursor.com) in any browser you use (Chrome, Edge, Firefox, Safari, Brave, Opera, etc.).
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

The app scans installed browsers the import libraries support (Chrome, Chromium, Edge, Firefox, Brave, Arc, Opera, Vivaldi, LibreWolf, Safari on macOS, and others) for `WorkosCursorSessionToken` on `cursor.com`, then saves it the same way as manual entry.

```text
cursor-usage token import --clipboard
```

Reads the clipboard (pyperclip, or PySide6 if installed) and saves after normalization.

### Common failures

| Situation | What to do |
|-----------|------------|
| Not logged in to cursor.com | Log in in a supported browser, then import again or set manually. |
| Safari (macOS) | Import is attempted; may still fail without **Full Disk Access**—use **Set token** if needed. |
| macOS | Chromium and Safari cookie data may require **Full Disk Access** for Terminal or the packaged app. |
| Linux | Chromium-based browsers need **gnome-keyring** or **KWallet** unlocked; Snap/Flatpak browsers may use paths import cannot read. Prefer **Set token** if import fails. |
| Windows Chromium v130+ | **App-bound encryption** often blocks import for normal apps; use **Set token** or one elevated import attempt. |
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

## Installed application (frozen builds)

Release installers ship a **GUI app only** (system tray + widget). Set or import your token from the tray menu or widget (**Set token…**, **Import session**). There is no separate command-line tool in the installed package.

See [INSTALL.md](INSTALL.md) and [platforms.md](platforms.md). For terminal-based token management, use a [development install](DEVELOPMENT.md).
