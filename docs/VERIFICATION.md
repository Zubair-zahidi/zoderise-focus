# Release verification · 1.1.0

Checked on 14 October 2026 using isolated local workspaces.

| Check | Evidence |
| --- | --- |
| Behavior | 22 passing unit/workflow tests: dependencies and cycles, ordering, recurrence, top-three planning, templates, drafts/history, timers, encrypted exports, retention, version 1 import, and validated restore |
| Source CI | Windows/Linux with Python 3.12/3.14; see the workflow run for the release commit |
| Packaged frontend | Fresh Edge browser against the executable's loopback server; no page errors |
| Interactive board | Actual card drag between lanes and status selector verified |
| Draft recovery | Typed a new note, cleared the test browser's local cache, reloaded, and recovered its database draft |
| Encrypted restore | Created/downloaded `.focus`, rejected a wrong password, accepted the correct one, and displayed the change preview |
| Languages | English, Dari, and Pashto core interfaces checked; actual RTL screenshots |
| Mobile | 390px viewport and 390px document width; banner clear of header |
| Native window | Two successful open/close cycles; shortcut registered and capture route invoked; no remaining observed child processes |
| Media | Screenshots from the real labelled sample workspace; GIF assembled from them |

Native notification acceptance is checked separately from visible banner delivery, which depends on Windows settings. Test scripts do not change personal workspaces or browser profiles. This verifies the listed flows, not every environment or input. The executable requires WebView2 and is unsigned; live SQLite and automatic backups remain unencrypted.

Repeat `python -m unittest discover -s tests -v`. Maintainer tools `verify_visual.py` and `test_desktop.py` cover the packaged app. `docs/media/visual-check.json` records the browser results. User data, runtime logs, and test databases are excluded from source and release files.
