# Implementation Plan: Cursor Usage Widget Redesign

## Goal Description

Redesign the Cursor Usage Monitor widget interface to faithfully match the dark modern card layout in the provided design mockup image. The redesigned widget features:

- **Personal Usage Header & Progress Bar**: Displaying `${used} / ${limit}` with a cyan progress bar and percentage indicator.
- **Team Usage Row**: Displaying team spend `${used} / ${limit}` with team icon and green percentage.
- **Dashboard API Breakdown with Segmented Total & Grouping**:
  - **TOTAL Gauge**: Features a **segmented composition arc** displaying the API portion (Cyan `#00e5ff`) and the Auto portion (Purple/Violet `#a855f7`).
  - **Subtle Visual Divider**: A sleek vertical divider line separating `TOTAL` from `API` and `AUTO` (`TOTAL │ API AUTO`).
  - **Component Breakdown Gauges**: Individual single-color gauges for **API** (Cyan) and **AUTO** (Purple/Violet) with centered percentage and label tags.
- **On Demand Usage Card**: Distinct container showing on-demand usage, pool details, coral/red progress bar, and spend.
- **Omission of Non-API Metrics**: As explicitly requested, the mock metric **"Demand API Time 40%"** is omitted because it is not provided by the Cursor `usage-summary` API.
- **Text Summary Lines**: Quick glance summary of Personal, Personal on-demand, and Team usage.
- **Dashboard API Metrics & Action Buttons**:
  - `[ 🔄 Refresh ]`: Instantly trigger fetch and update widget data.
  - `[ Set token... ]`: Launch session token configuration.
  - `[ Collapse ]` / `[ Expand ]`: Modern, user-friendly toggle between full details and compact/minimal view.
  - `[ Dashboard ]`: Open `https://cursor.com/dashboard/usage` in browser.
  - `[ 🚪 Quit ]`: Cleanly terminate application.
- **Metadata Section & Readable 24h Formatting**:
  - Readable format: `<Date> at <Time>` (e.g., `Thu 8 Oct 2026 at 12:52:28`).
  - Omit timezone abbreviations (such as `'IDT'`).
  - Use 24-hour time without AM/PM.

---



## User Review Required

> [!IMPORTANT]
> **Omission of "Demand API Time"**: Confirmed and omitted as instructed.
>
> **Total Gauge Design (Combined Option 1 & 2)**:
>
> - **Visual Divider**: `[ TOTAL ]  │  [ API ]   [ AUTO ]` creates intuitive grouping (aggregate sum on the left, breakdown components on the right).
> - **Segmented Composition Arc**: The `TOTAL` ring arc dynamically reflects its composition:
>   - The API portion is drawn in **Cyan** (`#00e5ff`).
>   - The Auto portion is drawn in **Purple/Violet** (`#a855f7`).
>   - The companion **API** gauge uses Cyan, and **AUTO** uses Purple/Violet, creating an immediate visual link.
>
> **Modern View-Toggle Button (**`Expand` **/** `Collapse`**)**:
>
> - In **Full Mode** (default), the button is labeled `Collapse` with an amber accent. Clicking it collapses to essential usage metrics & buttons.
> - In **Compact Mode**, the button is labeled `Expand`. Clicking it restores the full detailed view.
>
> **Readable 24-Hour Datetime Formatting (**`Date at Time`**)**:
>
> - Formatted cleanly as: `Thu 8 Oct 2026 at 12:52:28` (or `Wed 21 Oct 2026 at 00:00:00`).
> - Omits timezone codes like `IDT` and uses standard 24-hour clock without AM/PM.
>
> **Window Display Mode**:
>
> - Can be launched standalone via `cursor-usage widget`.
> - When running via `cursor-usage tray`, clicking the tray icon toggles this widget window.
> - Window is borderless, floating, with rounded corners matching the mockup (`border-radius: 16px`), draggable by mouse drag on header areas, and dismissible via `Esc` key or Quit button.

---



## Architecture & Visual Design

```
+-----------------------------------------------------+
|  Personal                                           |
|  $20.00 / $20.00                              100%  |
|  [================================================] | (Cyan Bar)
|                                                     |
|  Team                                               |
|  👥 $532.58 / $1278.00                         42%  |
|                                                     |
|  Dashboard API Breakdown                            |
|       (TOTAL 26%)   │    (API 26%)     (AUTO 0%)    | (Radial Gauges)
|    [Cyan + Violet]  │      [Cyan]      [Violet]     |
|                                                     |
|  +-----------------------------------------------+  |
|  | On Demand Usage                           60% |  |
|  | On-Demand: $0.00 used / Pool: Team            |  |
|  | [==============-----------------------------] |  | (Coral Bar)
|  | $0.00 / Team Pool                             |  |
|  +-----------------------------------------------+  |
|                                                     |
|  Personal: $20.00 / $20.00                          |
|  Personal on-demand: $0.00                          |
|  Team (42% used)                                    |
|                                                     |
|  Dashboard API Metrics                              |
|  [ 🔄 Refresh ]       [ Set token... ]              |
|  [ Collapse ]         [ Dashboard ]   [ 🚪 Quit ]   |
|                                                     |
|  Metadata                                           |
|  Status & Resets                                    |
|  Last Fetched:  Thu 8 Oct 2026 at 12:52:28          |
|  Next Reset:    Wed 21 Oct 2026 at 00:00:00         |
+-----------------------------------------------------+
```



### Visual Specifications

- **Dimensions**: Width: 295px, Height: ~620px (Full mode) / ~230px (Compact mode).
- **Background**: `#1e2022` (dark charcoal) with 1px border `#32353a` and `16px` corner radius.
- **Card Background**: `#25272b` with 1px border `#35383e` and `8px` corner radius.
- **Accent Colors**:
  - Cyan (`#00e5ff` / `#22d3ee`) for Personal bar and API metrics.
  - Purple/Violet (`#a855f7` / `#c084fc`) for Auto metrics and secondary segment on Total.
  - Emerald Green (`#4ade80` / `#34d399`) for Team percentage.
  - Coral/Salmon Red (`#f87171` / `#ef4444`) for On Demand Usage.
  - Amber/Gold (`#f59e0b` / `#d97706`) for the Expand / Collapse toggle button.
- **Typography**: Clean sans-serif system font with clear hierarchy (16px bold values, 13px section headers, 11px muted labels, 8px gauge tags).

---

