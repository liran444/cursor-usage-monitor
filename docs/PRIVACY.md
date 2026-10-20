# Privacy

Cursor Usage Monitor is **local-first**. The application runs on your computer. The
project maintainer does **not** operate a backend that receives your data, and the
app includes **no analytics or telemetry**.

This document describes what the app accesses and stores on your device. It is not
legal advice.

## What leaves your computer

| Destination | When | What is sent |
| --- | --- | --- |
| `https://cursor.com/api/usage-summary` | You refresh usage, automatic tray polling (~every 60 seconds while the tray app runs), or CLI `fetch` / `token test` | Your **WorkosCursorSessionToken** session cookie (same as your browser would use), plus HTTP headers that identify the request as coming from a desktop client (User-Agent, Referer, Origin). |

The app does **not** contact the maintainer’s servers, ad networks, or other third
parties for usage display.

Opening **Dashboard** or **Sign in** in the UI uses your system browser to
`cursor.com` URLs; that traffic is between you and Cursor, not the app author.

## What stays on your computer

| Data | Purpose | Typical location |
| --- | --- | --- |
| Session token | Authenticate to Cursor’s API | OS credential store (keyring), with optional file fallback `session_token` under the app config directory |
| Usage cache | Show last-known meters offline | `usage_cache.json` in the app cache directory (usage amounts and percents only—no account email in the mapped fields) |
| Settings | Tray mode, theme, notification toggles | `settings.json` in the app config directory |

Paths follow [platformdirs](https://pypi.org/project/platformdirs/) (`cursor-usage-app`).
See [AUTH.md](AUTH.md) for token handling and [UNINSTALL.md](UNINSTALL.md) for removal.

The session token is **not** written to application logs on success paths. Treat it
like a password.

## Browser cookie import (sensitive)

To avoid manual copy-paste, the app can read **one** cookie from browsers installed
on **this machine**:

- **Name:** `WorkosCursorSessionToken`
- **Domains:** `cursor.com` / `.cursor.com` only

Implementation uses local libraries (`rookiepy`, `browser-cookie3`). They read
browser cookie databases on disk and decrypt using your OS login session (keyring /
DPAPI / Keychain). **No cookie dump is uploaded to the maintainer** or to any server
other than Cursor when you fetch usage.

Import runs when you choose **Import session**, use CLI `token import`, or—if no
token is stored yet—**once silently at tray startup** (then only the matching
cursor.com session cookie is saved locally).

On some platforms (for example Windows Chromium app-bound encryption), automatic
import may fail; you can paste the token manually instead.

## Clipboard

The GUI does not read the clipboard for tokens unless you use development CLI
commands with `--clipboard`. Clipboard access is local to your machine.

## Your choices

- **Set token** / **Import session** — you control when a token is stored.
- **Clear token** — tray/widget token UI or `cursor-usage token clear` (dev install).
- **Quit the tray app** — stops periodic API polling.
- **Uninstall** — remove the app; clear the token first if you want credentials gone
  before deleting files (see [UNINSTALL.md](UNINSTALL.md)).

## Maintainer / open source

Source code is public under [MIT](../LICENSE). Building or running from source
follows the same local-only behavior. Installers bundle open-source libraries; see
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).

If you report issues on GitHub, do **not** paste session tokens, cookie values, or
cache files containing live credentials.
