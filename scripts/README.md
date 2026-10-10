# Scripts

Path pattern: `scripts/<audience>/<os>/...`

## Developer (`dev/`)

| OS | Install | Activate | Verify |
|----|---------|----------|--------|
| Windows | `.\scripts\dev\windows\install.ps1` | `. .\scripts\dev\windows\activate.ps1` | `.\scripts\dev\windows\verify.ps1` |
| Linux | `./scripts/dev/linux/install.sh` | `source ./scripts/dev/linux/activate.sh` | `./scripts/dev/linux/verify.sh` |
| macOS | `./scripts/dev/macos/install.sh` | `source ./scripts/dev/macos/activate.sh` | `./scripts/dev/macos/verify.sh` |

Shared bash helpers: `dev/_common.sh` (used by Linux and macOS install scripts).

## End user (`user/`)

| OS | Install |
|----|---------|
| Windows | `.\scripts\user\windows\install.ps1` |
| Linux | `./scripts/user/linux/install.sh` |
| macOS | `./scripts/user/macos/install.sh` |

## Build (`build/`)

| OS | Build |
|----|-------|
| Linux | `./scripts/build/linux/build.sh` |

Windows and macOS builds use PyInstaller directly — see [docs/BUILD.md](../docs/BUILD.md).
