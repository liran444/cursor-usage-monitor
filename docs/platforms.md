# Platform notes

## Linux

- Tray requires a desktop with systray / AppIndicator support.
- **Ubuntu GNOME:** enable extension **Ubuntu AppIndicators** (`ubuntu-appindicators@ubuntu.com`) if the icon is missing.
- Check the **hidden icons** chevron on the top bar.
- Dev: `./scripts/install-dev-linux.sh` then `cursor-usage tray`.
- Release: extract tarball, run `scripts/install-user.sh`.

**If `cursor-usage tray` prints nothing but no icon appears:** quit any old instance (`pkill -f 'cursor-usage tray'`), then start again. After an upgrade, ensure you are on a version that sets `visible = True` in the tray setup hook.

## macOS

- Dev: `./scripts/install-dev-macos.sh` then `cursor-usage tray`.
- Menu bar icon via pystray.
- First open without notarize: right-click app → Open.
- Release: `install-user-macos.sh` installs LaunchAgent for tray at login.

## Windows

- Dev: `.\scripts\Install-Dev.ps1` then `cursor-usage tray`.
- Icon shows **percent drawn on the bitmap** (no label beside icon in notification area).
- Check hidden icons overflow if the tray icon is not visible.
- Release: run `Install-User.ps1` from extracted zip.

## Token (all platforms)

See [AUTH.md](AUTH.md).
