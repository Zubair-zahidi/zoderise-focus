# Architecture

Focus is a small local application with three layers:

```text
Streamlit pages / Windows WebView2 window
                  ↓
    Shared UI helpers and workspace selection
                  ↓
 Transactional SQLite store + validated file exports
```

`app.py` owns navigation, theme CSS, workspace selection, and persistent dialog state. `app_pages/` contains ten page scripts, including the hidden quick-capture route. `focus/ui.py` supplies shared dialogs, task cards, formatting, and quick find. `focus/store.py` owns the schema and parameterized mutations; it has no Streamlit dependency.

The store opens and closes a connection per operation, uses WAL and foreign keys, and acquires an immediate transaction for writes. A partial unique index permits one running or paused timer. Elapsed time uses persisted accumulated seconds plus the current wall-clock segment, capped at the plan. Completion and creation of a recurring successor happen in one transaction; the unique successor reference prevents duplicate recurrence on re-completion.

Backup export uses a read transaction for a consistent snapshot and converts running timers to paused snapshots. Restoration never executes uploaded SQL or extracts paths from a ZIP. It permits only two named files, checks bounded archive sizes and content hashes, validates row structure in a disposable known-schema database, validates semantics and foreign keys, saves a safety snapshot, and transactionally replaces rows.

The desktop launcher starts a child Streamlit server on an available loopback port, waits for its health endpoint, then opens WebView2. Closing the window terminates the child tree. A child watchdog detects a missing parent to prevent an orphan server after an abrupt exit. Data and logs stay outside PyInstaller's temporary extraction directory.

The first version deliberately has no network backend, accounts, remote AI, analytics pipeline, or collaborative permissions. A multi-user service would need a separate security and deployment architecture; do not bind this personal app to a public address.

## Version 1.1 additions

The Planning mixin extends SQLite with task order, schedules, dependency edges, daily picks, drafts, note versions, templates, and alerts. Atomic writes guard dependency cycles, blocked work, recurrence, and timer completion. Inline Streamlit custom components v2 provide the board and autosaving editor; ordinary native controls remain available for accessible actions and plain editing.

Encrypted exports wrap validated ZIP backups through cryptography AESGCM and scrypt. Background maintenance runs from the open UI and optional Windows bridge, with serialized automatic-backup reservations and bounded retention. The bridge registers a global capture shortcut and submits Windows notifications; it is not a system service. Version 1 imports are upgraded to the extended schema. A restore epoch prevents stale browser drafts from replacing intentionally restored content.
