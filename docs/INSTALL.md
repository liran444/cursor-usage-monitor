# End user install

You do **not** need Python or git. Download the release for your OS (zip or installer), then:

## 1. Install

| OS | Steps |
|----|-------|
| **Linux** | Extract the tarball, run `./scripts/user/linux/install.sh` (or pass the extracted `CursorUsageMonitor` folder). |
| **Windows** | Extract the zip, run `.\scripts\user\windows\install.ps1`. |
| **macOS** | Run `./scripts/user/macos/install.sh` with the `.app` from the release (copies to Applications and enables login autostart). |

Platform-specific notes and troubleshooting: [platforms.md](platforms.md).

## 2. Session token

Required once; set again when it expires. See [AUTH.md](AUTH.md).

1. Sign in at [cursor.com/dashboard](https://cursor.com/dashboard).
2. DevTools → Application → Cookies → copy `WorkosCursorSessionToken`.
3. Run from the install folder (or PATH):

```bash
cursor-usage token set
cursor-usage token test
```

## 3. Run

- Tray should start at login after install. Or run: `cursor-usage tray`
- Icon shows **personal included usage %**; click for details, refresh, and team pool.

More detail: [README-USER.txt](../README-USER.txt). To remove: [UNINSTALL.md](UNINSTALL.md).
