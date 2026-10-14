# Your first day with Focus

1. Open the app. Your personal workspace starts empty.
2. In **Projects & board**, create a project with a name, purpose, and color.
3. Create a task. Add a deadline, priority, tags, and an estimate if useful. Open its Details again to add checklist items.
4. Move it through **Inbox → Next → Doing → Done** using the card actions. Details can choose any status.
5. Save project references in **Notes**. Use Markdown for headings, lists, quotes, and code. Press Save before leaving; Preview displays saved content.
6. In **Today**, choose a focus goal and write one outcome worth making time for.
7. In **Focus room**, optionally link a task, enter an intention, and start a session.
8. Pause before stepping away. Finish & record keeps the actual elapsed time. Cancel excludes the session from activity totals.
9. Review recorded activity, then download a backup from **Settings & backup**.

## A few useful details

**Recurring tasks:** Daily and Weekly recurrence need a due date. Completing a recurring task creates one follow-up due one or seven days after the later of its existing deadline and today. Its checklist is copied unchecked. Reopening and completing the original again does not generate a duplicate. Completing the follow-up continues the series.

**Focus persistence:** A running session keeps counting when you leave the page or close the app, capped at its planned duration. On returning to Focus room, a session that reached its target is completed. Pause stops its clock. Break countdowns are only a convenience in the current app session and do not persist across a restart. The timer does not inspect your applications or measure attention.

**Activity dates:** A completed session counts on the day you finish it. Review shows currently completed, non-trashed tasks; reopening or trashing a task removes it from the completed-work view. A daily reflection is the same text you saved in Today's intention.

**Search:** Quick find supports literal phrases in titles, task details, note bodies, and tags. Task search matches active projects. Notes from archived projects remain accessible. Ctrl+K opens quick find on supported desktop browsers.

**Recovery:** Trash is reversible in Settings. Archiving a project hides its tasks from active views but keeps its notes, history, and data. There is no permanent-delete control in this release.

**Appearance:** Choose accent, spacing, and gentle transitions in Settings. The app respects your system's reduced-motion preference. Light/dark theme is in the top-right app menu → Settings. That theme choice belongs to the browser view; workspace preferences live in the database.

**Sample workspace:** The sidebar opens a separate demo database. The sample projects and activity are examples. Leaving the demo returns to your personal workspace. Neither mode overwrites the other.

## Backup and restoration

Download a ZIP backup regularly. It contains `focus.json` and `manifest.json` with a SHA-256 check; store it securely because its content is readable. Running timers are paused in exports so time spent transferring a backup does not count as work.

Upload a Focus backup in Settings and inspect its counts. Confirm replacement to restore it. The app validates the schema, durations, options, IDs, references, and checksum before changing data. An automatic copy of the current workspace is saved in the local `backups` directory before replacement. Validation failure leaves your workspace unchanged.

JSON is a readable export; use ZIP for restoration. CSV exports all non-trashed tasks, including archived projects, and escapes formula-leading text for spreadsheet safety. Calendar export includes unfinished tasks with deadlines as all-day events. It is a manual snapshot, not two-way synchronization.
