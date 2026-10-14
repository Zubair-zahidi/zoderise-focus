"""Windows-only test of our own native app window and server cleanup."""
import ctypes
import json
import os
import subprocess
import time
from pathlib import Path

import psutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from focus import __version__
from focus.store import Store

ROOT = Path(__file__).resolve().parent.parent
EXE = ROOT / "dist" / f"Zoderise-Focus-{__version__}-Windows-x64.exe"
env = os.environ.copy()
env["FOCUS_DATA_HOME"] = str(ROOT / "test-data" / "desktop")
test_store = Store(Path(env['FOCUS_DATA_HOME'])/'workspace.sqlite3')
test_store.set_settings(desktop_hotkey=True, reminders=True, backup_interval='Daily')
test_store.alert('desktop-probe-'+str(time.time_ns()),'Desktop reminder test','Local notification bridge verification')
user32 = ctypes.windll.user32
callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
user32.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
user32.GetWindowTextW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]
user32.GetClassNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_int]


def find_windows(process_ids):
    found = []
    def inspect_window(hwnd, _):
        pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value in process_ids:
            text = ctypes.create_unicode_buffer(512)
            user32.GetWindowTextW(hwnd, text, 512)
            classname = ctypes.create_unicode_buffer(512)
            user32.GetClassNameW(hwnd, classname, 512)
            if text.value == "Zoderise Focus" and classname.value.startswith("WindowsForms"):
                found.append(int(hwnd))
        return True
    user32.EnumWindows(callback_type(inspect_window), 0)
    return found


rounds = []
for round_number in (1, 2):
    test_store.alert('desktop-round-'+str(time.time_ns()), 'Desktop reminder test', 'Local notification verification')
    process = subprocess.Popen([str(EXE)], env=env, creationflags=subprocess.CREATE_NO_WINDOW)
    observed = set()
    try:
        for _ in range(120):
            parent = psutil.Process(process.pid)
            ids = {parent.pid} | {p.pid for p in parent.children(recursive=True)}
            observed.update(ids)
            windows = find_windows(ids)
            if windows:
                break
            if process.poll() is not None:
                raise RuntimeError("Desktop process exited before the window opened")
            time.sleep(.5)
        else:
            raise RuntimeError("No Zoderise Focus native window appeared")
        time.sleep(4)
        observed.update(p.pid for p in psutil.Process(process.pid).children(recursive=True))
        capabilities_path=Path(env['FOCUS_DATA_HOME'])/'desktop-capabilities.json'
        for _ in range(40):
            capabilities=json.loads(capabilities_path.read_text()) if capabilities_path.exists() else {}
            if capabilities.get('running') and capabilities.get('pid') in observed:
                break
            time.sleep(.25)
        if not capabilities.get('running'):
            raise RuntimeError('Desktop bridge did not start')
        for _ in range(80):
            capabilities = json.loads(capabilities_path.read_text())
            if capabilities.get('notifications_accepted', 0):
                break
            time.sleep(.25)
        if not capabilities.get('notifications_accepted', 0):
            raise RuntimeError('Windows did not accept the test reminder')
        if capabilities.get('shortcut_registered'):
            user32.PostThreadMessageW(capabilities['thread_id'],0x0312,99,0)
            for _ in range(40):
                capabilities=json.loads(capabilities_path.read_text())
                if capabilities.get('capture_requests',0)>0:
                    break
                time.sleep(.25)
            if not capabilities.get('capture_requests'):
                raise RuntimeError('Registered quick-capture shortcut did not route to the app')
        user32.PostMessageW(ctypes.c_void_p(windows[0]), 0x0010, 0, 0)  # Close only our app's window.
        process.wait(timeout=20)
        time.sleep(3)
        alive = [pid for pid in observed if psutil.pid_exists(pid)]
        if alive:
            raise RuntimeError(f"Desktop children remained after close: {alive}")
        rounds.append({"round": round_number, "native_window": True, "exit_code": process.returncode, "remaining_children": alive, 'shortcut':capabilities.get('shortcut_registered'), 'capture_requests':capabilities.get('capture_requests',0), 'notification_api':capabilities.get('notification_api'), 'notifications_accepted':capabilities.get('notifications_accepted',0)})
    finally:
        for pid in observed:
            try:
                psutil.Process(pid).terminate()
            except psutil.Error:
                pass
(ROOT / "test-data").mkdir(exist_ok=True)
(ROOT / "test-data" / "desktop-check.json").write_text(json.dumps(rounds, indent=2))
print(json.dumps(rounds))
