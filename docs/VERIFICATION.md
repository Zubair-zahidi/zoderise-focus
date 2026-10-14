# Release verification · 1.0.0

Checked on 14 October 2026.

| Check | Evidence |
| --- | --- |
| Local behavior | 12 passing unit/workflow tests; isolated temporary workspaces |
| Source portability | GitHub Actions matrix: Windows/Linux, Python 3.12/3.14; see the repository's current workflow run |
| Frozen frontend | Fresh Edge browser connected to the packaged executable's loopback server; page checks, task-linked focus start/pause, and note preview |
| Quick find | Native Ctrl+K opens search; submitted search returns the expected sample task |
| Mobile layout | 390px viewport with document width 390px; no horizontal overflow in the board |
| Native window | Final executable opened and closed twice; zero leftover processes observed in the app process tree |
| Media | Real app screenshots of the labelled sample workspace; GIF assembled from those screenshots |
| Data isolation | Empty personal workspace and separate demo workspace checked; backups pause active timer snapshots |

These checks establish the tested flows, not a guarantee that every possible environment or input is covered. The Windows launcher requires WebView2 and is unsigned. The desktop data path is outside the executable and its extraction directory. No actual user database, private notes, or credentials are included in the release.

Run `python -m unittest discover -s tests -v` to repeat behavior checks. `tools/verify_visual.py` and `tools/test_desktop.py` document the packaged-app checks. `docs/media/visual-check.json` records the visual capture result.
