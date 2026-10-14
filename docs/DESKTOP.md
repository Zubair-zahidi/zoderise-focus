# Windows desktop build

Prerequisites: Windows x64, Python 3.12–3.14, and Microsoft Edge WebView2 Runtime for launch. End users of the compiled app do not need Python or npm.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-desktop.txt
python build_icon.py
python -m unittest discover -s tests -v
python -m PyInstaller --noconfirm FocusDesktop.spec
```

Output: `dist/Zoderise-Focus-1.1.0-Windows-x64.exe`.

To test the wrapper before packaging:

```powershell
python desktop_launcher.py
```

The desktop opens a native window around a local Streamlit server. It automatically chooses a free port between 8650 and 8670, always on 127.0.0.1. The database and diagnostic logs live under `%LOCALAPPDATA%\ZoderiseFocus`, separate from the executable. Moving the executable does not move the workspace.

Closing the desktop window stops its child server. Source users stop Streamlit with Ctrl+C. If startup fails, check `desktop.log` and `server.log` in the data directory. Never share those logs without checking them for private file paths or task text.

The build is unsigned. Do not disable antivirus or system protections to run an untrusted copy. Release assets should be accompanied by checksums, and their source should match the tagged release.

`tools/verify_visual.py` supports `FOCUS_EXE` for a fresh-browser smoke test of the frozen server. This test does not substitute for opening and closing the actual desktop window, checking WebView2, and confirming that child processes stop.
