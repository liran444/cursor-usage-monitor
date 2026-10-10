# Platform notes

Install steps: [INSTALL.md](INSTALL.md). Dev setup: [DEVELOPMENT.md](DEVELOPMENT.md).

## Linux

### End user

- Extract release tarball, run `scripts/install-user.sh`.

### Developer

```bash
./scripts/install-dev-linux.sh
cursor-usage tray
```

Re-activate: `source ./scripts/enter-dev.sh`

### Tray

- Requires a desktop with systray / AppIndicator support.
- **Ubuntu GNOME:** enable extension **Ubuntu AppIndicators** (`ubuntu-appindicators@ubuntu.com`) if the icon is missing.
- Check the **hidden icons** chevron on the top bar.

**If `cursor-usage tray` prints nothing but no icon appears:** quit any old instance (`pkill -f 'cursor-usage tray'`), then start again. After an upgrade, ensure you are on a version that sets `visible = True` in the tray setup hook.

## macOS

### End user

- Run `scripts/install-user-macos.sh` with the `.app` from the release.

### Developer

```bash
./scripts/install-dev-macos.sh
cursor-usage tray
```

Re-activate: `source ./scripts/enter-dev.sh`

### Tray

- Menu bar icon via pystray.
- First open without notarize: right-click app → Open.

## Windows

### End user

- Extract release zip, run `scripts\Install-User.ps1`.

### Developer

```powershell
.\scripts\Install-Dev.ps1
cursor-usage tray
```

Re-activate: `. .\scripts\enter-dev.ps1`

### Tray

- Icon shows **percent drawn on the bitmap** (no label beside icon in notification area).
- Check hidden icons overflow if the tray icon is not visible.

## Token (all platforms)

See [AUTH.md](AUTH.md).
