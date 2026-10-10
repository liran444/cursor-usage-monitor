Cursor Usage Monitor — User guide
=================================

Short install overview: see docs/INSTALL.md (or README.md in the repo root).
This file has detailed steps.

Requirements
------------
- Windows 10+, macOS 12+, or Linux with a system tray
- A Cursor account and browser access to https://cursor.com/dashboard

Install
-------
1. Download the release for your OS (zip or installer).
2. Run the included install script (see docs/INSTALL.md or docs/platforms.md).
3. Start "Cursor Usage Monitor" from your menu or autostart.

Session token (required once, again when it expires)
----------------------------------------------------
1. Sign in at https://cursor.com/dashboard in Chrome/Edge/Firefox/Safari.
2. Open DevTools → Application → Cookies → https://cursor.com
3. Copy the cookie named WorkosCursorSessionToken
4. In a terminal (or the app's menu → Set token):
   cursor-usage token set
   Paste the value when prompted.

Treat this token like a password. Never share it.

Tray
----
- Icon shows your personal included usage as a percentage (used / your plan limit).
- Click the icon for details: personal $, team pool $, refresh, open dashboard.

Uninstall
---------
See docs/UNINSTALL.md in the developer package or your install folder.

Disclaimer
----------
Uses an undocumented Cursor dashboard API. It may stop working without notice.
Not an official Cursor product.
