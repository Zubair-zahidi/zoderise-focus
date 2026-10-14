# Using Zoderise Focus

1. Create a project and tasks in **Projects & board**. Add priorities, estimates, deadlines, checklists, and prerequisites.
2. Drag cards between Inbox, Next, Doing, and Done. Each card also has a status selector and ordering buttons for keyboard use. A blocked task cannot start or finish until its prerequisites are complete.
3. In **Today**, choose up to three important tasks and a daily focus goal.
4. Use **Planning & templates** to assign planned dates separately from deadlines. The weekly view shows scheduled work; the effort view compares estimates with linked, completed focus sessions.
5. Create projects from a built-in template or save a project's active tasks as your own template. Templates reuse task metadata and checklists, not deadlines or dependencies.
6. Write project-linked Markdown in **Notes**. The editor saves a draft after a short typing pause. Save note publishes it; Preview shows the current draft. Recover drafts after restarting, or restore a previous published version from history. The most recent 50 previous versions are retained. A plain editor is available and saves on field blur.
7. Start a task-linked or independent session in **Focus room**. Pause when stepping away; Finish & record keeps elapsed time, while Cancel excludes it from activity totals.
8. Check **Activity & review**, then export or back up your workspace.

## Recurrence and timers

Recurring tasks need a deadline. Daily, weekly, weekdays, selected weekdays, monthly, and intervals of 1–365 days are supported. A successor is based on the later of the existing deadline and completion day. Monthly schedules clamp to the target month's last valid day. Completion creates one successor with fresh unchecked items; repeating completion of the original does not create duplicates. Prerequisites apply to an occurrence and are not copied to its successor.

Running sessions persist and count wall-clock time up to their planned duration, including while the app is closed. Pausing stops the clock. On reopening, expired sessions are recorded. A break timer is a convenience; scheduled reminders are stored separately. The timer does not inspect applications or measure attention.

## Capture and reminders

Ctrl+K searches tasks and notes inside the app. In the Windows executable, enable **Desktop quick-capture shortcut** in Settings, restart, and use Ctrl+Alt+Space while Focus is open. It brings the app to its quick-capture page. A shortcut already used by another app may not register.

Enable reminders for deadlines, completed sessions, and breaks. The app inbox retains them; Windows banners are available only from the native executable while it is open and depend on Windows notification settings. No background service is installed.

## Appearance and languages

Choose an accent, spacing, and reduced motion. Light/dark theme is in the app menu's Settings. English, Dari, and Pashto are available for core controls; Dari/Pashto use right-to-left layouts. Extended help can fall back to English, user text is not translated, and dates remain Gregorian.

The sample workspace is a separate database. Leaving it returns to your personal workspace. Trash is reversible; archiving retains notes and history. Daily review reflects currently completed, non-trashed work and recorded sessions.

## Backup and restoration

Plain ZIP backups contain readable `focus.json` and a checksum manifest. Optional password-protected `.focus` exports encrypt the ZIP. Use a password of at least 12 characters; the app does not save it or offer password recovery. The live database and automatic local backups remain unencrypted.

Enable daily or weekly automatic backups and choose a retention limit of 3–30. They run while the app is open and catch up on reopening; they are not operating-system scheduled jobs. Personal and sample backups stay separate.

Upload ZIP or `.focus`, enter the password when needed, and inspect added/removed/changed counts before confirming replacement. Validation failures leave your workspace unchanged. A safety ZIP is saved locally before restoration. Running sessions are paused in backup snapshots. Version 1 backups remain readable; version 2 backups need Focus 1.1 or newer.

JSON/CSV/Markdown/calendar downloads are ordinary exports. CSV escapes formula-leading text. Calendar export is a manual snapshot of unfinished deadlines, not two-way sync.
