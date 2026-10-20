# Third-party notices

Installers bundle open-source libraries. Application source is under the
[MIT License](LICENSE).

## PySide6 / Qt

- **Use:** graphical UI  
- **License:** LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only (this project uses Qt under LGPL)  
- **Links:** https://www.qt.io/ · https://pypi.org/project/PySide6/

You may replace the Qt libraries shipped with this application with your own
compatible build. Bundled Qt binaries live under the install directory (for example
`PySide6` inside `_internal` on Windows/Linux, or inside `Cursor Usage.app` on macOS).

## qt-material-icons

- **License:** MIT  
- **Link:** https://pypi.org/project/qt-material-icons/

## browser-cookie3

- **Use:** optional local browser cookie import  
- **License:** LGPL  
- **Link:** https://pypi.org/project/browser-cookie3/

## Other bundled Python dependencies (representative)

| Component | License |
| --- | --- |
| httpx, httpcore, h11, anyio, sniffio, idna | BSD-3-Clause |
| keyring | MIT |
| rookiepy | MIT |
| pyperclip | BSD |
| platformdirs | MIT |
| certifi | MPL-2.0 |

See each package on PyPI for full license text.

## Microsoft Visual C++ Redistributable (Windows)

The Windows installer may run Microsoft’s VC++ 2015–2022 x64 redistributable when it
is not already installed:  
https://learn.microsoft.com/en-us/visualstudio/releases/2015/2015-redistribution-vs

## Corresponding source (LGPL)

Source for LGPL components matches the versions in `pyproject.toml` at the release
tag. Obtain PySide6 and browser-cookie3 source from the links above or from that tag
in this repository.
