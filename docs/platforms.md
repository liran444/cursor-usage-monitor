# Platform notes

Install steps: [INSTALL.md](INSTALL.md). Dev setup: [DEVELOPMENT.md](DEVELOPMENT.md). Script index: [scripts/README.md](../scripts/README.md).

## Linux

### End user

- Extract release tarball, run `./scripts/user/linux/install.sh`.

### Developer

```bash
./scripts/dev/linux/install.sh
cursor-usage tray
```

Re-activate: `source ./scripts/dev/linux/activate.sh`

### Tray

- Requires a desktop with systray / AppIndicator support.
- **Ubuntu GNOME:** enable extension **Ubuntu AppIndicators** (`ubuntu-appindicators@ubuntu.com`) if the icon is missing.
- Check the **hidden icons** chevron on the top bar.

**If `cursor-usage tray` prints nothing but no icon appears:** quit any old instance (`pkill -f 'cursor-usage tray'`), then start again. After an upgrade, ensure you are on a version that sets `visible = True` in the tray setup hook.

## macOS

### End user

- Run `./scripts/user/macos/install.sh` with the `.app` from the release.

### Developer

```bash
./scripts/dev/macos/install.sh
cursor-usage tray
```

Re-activate: `source ./scripts/dev/macos/activate.sh`

### Tray

- Menu bar icon via pystray.
- First open without notarize: right-click app → Open.

## Windows

### End user

- Extract release zip, run `.\scripts\user\windows\install.ps1`.

### Developer

```powershell
.\scripts\dev\windows\install.ps1
cursor-usage tray --background
```

`cursor-usage tray` blocks the terminal until you Quit from the menu or press Ctrl+C — that is normal. Use `--background` to return to the shell immediately.

Re-activate: `. .\scripts\dev\windows\activate.ps1`

**If no tray icon appears:** click the **^** overflow chevron near the clock (Windows hides new icons there by default). Drag the icon to the visible taskbar if needed.

**If `python` opens the Microsoft Store:** Python is not installed (only the Windows alias stub). Install Python from [python.org](https://www.python.org/downloads/) or accept the winget prompt from the install script. Then disable **App execution aliases** for `python.exe` and `python3.exe`.

### Tray

- Icon shows **percent drawn on the bitmap** (no label beside icon in notification area).
- Check hidden icons overflow if the tray icon is not visible.

## Token (all platforms)

See [AUTH.md](AUTH.md).
