# Zoderise Focus 1.1.0

A fuller local productivity workspace by **Zubair Zahidi, founder of Zoderise**.

## New in this release

- Drag-and-drop Kanban, keyboard card movement, manual ordering, and prerequisites with cycle protection.
- Today's top three, weekly planning with separate planned dates, and estimate-versus-recorded-time review.
- Weekday, selected-day, monthly, and custom-interval recurrence alongside daily/weekly schedules.
- Built-in and personal project templates with reusable tasks and checklists.
- Markdown typing autosave, restart recovery, and the last 50 published note versions.
- Opt-in Windows Ctrl+Alt+Space quick capture; persistent reminder inbox and optional desktop notifications.
- Password-encrypted backup exports, daily/weekly automatic local backups with retention, and validated restore change previews.
- Dari and Pashto core controls and RTL layouts, alongside English; refreshed real screenshots and animated walkthrough.

## Downloads

**Windows x64:** `Zoderise-Focus-1.1.0-Windows-x64.exe`. Double-click to open. No Python, npm, Node.js, or Ollama is required. Microsoft Edge WebView2 Runtime must be present. The executable is unsigned.

**Source:** `Zoderise-Focus-1.1.0-Source.zip`, with tests, documentation, actual screenshots, and the animated walkthrough. Verify files using `SHA256SUMS.txt`.

## Upgrading and limits

Existing 1.0 workspaces are extended automatically. Version 1 ZIP backups can be restored in 1.1; new version 2 backups require 1.1. Keep a backup before replacing your executable and avoid downgrading an upgraded workspace.

The live SQLite database, automatic backups, plain ZIP backups, and ordinary exports remain unencrypted. Only optional password-protected `.focus` exports are encrypted; forgotten passwords cannot be recovered. Automatic backups run while the app is open or catch up on reopening. Native shortcuts require a restart after enabling them. Windows can suppress notification banners; the inbox retains reminders.

This remains a single-person local app without cloud sync, team accounts, or AI integration. Core Dari/Pashto controls are translated; longer help can remain English. Calendar dates are Gregorian. Activity reflects recorded sessions, not measured attention or guaranteed productivity.

Validation details and reproducible checks are in `docs/VERIFICATION.md`.
