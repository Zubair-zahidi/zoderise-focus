# Zoderise Focus 1.0.0

A personal productivity workspace from **Zubair Zahidi, founder of Zoderise**. Organize projects, capture ideas, and record focused sessions without an account, AI model, or cloud service.

## Included

- Projects and a four-state Kanban board, priorities, deadlines, estimates, checklists, tags, and daily/weekly recurring tasks.
- Searchable project-linked Markdown notes and saved-content preview.
- Focus timer with pause/resume, persistent session state, daily goals, break countdowns, and recorded activity review.
- Quick find with Ctrl+K, agenda views, a weekly reflection, and review download.
- Four accent palettes, compact spacing, reduced motion, and native light/dark appearance.
- Local SQLite storage, JSON/CSV/Markdown/calendar exports, verified ZIP backups, validated restore with a safety copy, and reversible trash/archive.
- Separate labelled sample workspace, real screenshots, animated demo, user guide, architecture notes, source tests, and CI.

## Downloads

**Windows x64:** `Zoderise-Focus-1.0.0-Windows-x64.exe`. Double-click to open the native app. No Python, npm, Node.js, or Ollama is required. Microsoft Edge WebView2 Runtime must be present. The app is unsigned.

**Developers:** `Zoderise-Focus-1.0.0-Source.zip` includes source, tests, documentation, screenshots, and the animated walkthrough. Follow the README to run the browser app.

Use `SHA256SUMS.txt` to check release files. Windows PowerShell: `Get-FileHash .\Zoderise-Focus-1.0.0-Windows-x64.exe -Algorithm SHA256`.

## Verified behavior and limits

Automated tests cover CRUD workflows, checklist recovery, recurring-task idempotency, focus persistence, export safety, and backup restoration. The actual frozen app is checked in a fresh browser on desktop and at a 390px width. The native window is tested across two open/close cycles and checked for server cleanup.

This is a single-person local workspace. It has no cloud sync, team accounts, drag-and-drop board, OS reminders, or automatic integrations. Timer totals represent recorded timer work, not verified attention or productivity. Local data and exports are unencrypted. Keep backups somewhere you trust.
