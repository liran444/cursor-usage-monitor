# Disclaimer

**Unofficial tool.** Cursor Usage Monitor is an independent open-source project. It
is **not** affiliated with, endorsed by, or supported by **Cursor** or **Anysphere**.

## No warranty

Application source is provided under the [MIT License](../LICENSE): use at your own
risk, without warranty of any kind. The same “as is” limitation applies to
**installers** distributed free of charge from this project’s releases.

## Service and API

- The app calls Cursor’s **`usage-summary`** HTTP API using **your** session. That
  API is not documented here as a stable public contract; it may change, rate-limit,
  or block clients at any time.
- Your use of Cursor’s website and services remains subject to **Cursor’s terms**,
  not this repository.
- The maintainer is not responsible for account lockouts, billing surprises, API
  outages, or changes that break this app.

## Security and session tokens

- A stored **WorkosCursorSessionToken** is equivalent to a logged-in browser session
  for Cursor web APIs. Anyone with access to your machine or token file may abuse it.
- **Browser cookie import** reads sensitive data from browser profiles on your PC.
  Only install and run software you trust. Corporate policies may forbid this
  behavior on managed devices.
- You are responsible for securing your computer, keyring, backups, and screenshots.

## Privacy

See [PRIVACY.md](PRIVACY.md) for what the app accesses locally and what it sends to
`cursor.com`. The maintainer does not collect usage data from you.

## Third-party software

Installers bundle Qt (LGPL), cookie-import libraries, and other components. See
[THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) for licenses and attribution.
Those components are governed by **their** licenses, not this disclaimer.

## Not legal advice

This file is a plain-language summary for users. It does not replace professional
legal advice for your jurisdiction or situation.
