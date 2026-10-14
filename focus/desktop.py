"""Opt-in Windows shortcut and local notification bridge. No installed service."""
import ctypes
import json
import logging
import os
import threading
import time
from ctypes import wintypes

from focus.store import Store, data_home


class NotificationData(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("hWnd", wintypes.HWND), ("uID", wintypes.UINT),
                ("uFlags", wintypes.UINT), ("uCallbackMessage", wintypes.UINT), ("hIcon", wintypes.HICON),
                ("szTip", ctypes.c_wchar * 128), ("dwState", wintypes.DWORD), ("dwStateMask", wintypes.DWORD),
                ("szInfo", ctypes.c_wchar * 256), ("uTimeout", wintypes.UINT), ("szInfoTitle", ctypes.c_wchar * 64),
                ("dwInfoFlags", wintypes.DWORD), ("guidItem", ctypes.c_byte * 16), ("hBalloonIcon", wintypes.HICON)]


def windows_text(text, units):
    return str(text).encode("utf-16-le")[:units*2].decode("utf-16-le", errors="ignore")


class DesktopBridge:
    def __init__(self, window, url):
        self.window, self.url = window, url
        self.stop = threading.Event()
        self.thread = None
        self.status = {"shortcut_registered": False, "notification_api": False}

    def start(self):
        self.thread = threading.Thread(target=self.run, name="Focus-desktop-bridge", daemon=True)
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.thread:
            self.thread.join(timeout=12)

    def capture(self):
        self.window.show()
        self.window.restore()
        self.window.load_url(self.url + "/capture")
        self.status['capture_requests'] = self.status.get('capture_requests', 0) + 1
        if os.name == 'nt' and self.status.get('running'):
            self.write_status()

    def write_status(self):
        temp = data_home() / f'desktop-status-{os.getpid()}.pending'
        temp.write_text(json.dumps(self.status), encoding='utf-8')
        temp.replace(data_home() / 'desktop-capabilities.json')

    def run(self):
        if os.name != "nt":
            return
        user = ctypes.WinDLL("user32", use_last_error=True)
        shell = ctypes.WinDLL("shell32", use_last_error=True)
        user.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                         ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                         wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, ctypes.c_void_p]
        user.CreateWindowExW.restype = wintypes.HWND
        user.DestroyWindow.argtypes = [wintypes.HWND]
        user.LoadIconW.argtypes = [wintypes.HINSTANCE, ctypes.c_void_p]
        user.LoadIconW.restype = wintypes.HICON
        user.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        user.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        user.PeekMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT]
        shell.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NotificationData)]
        shell.Shell_NotifyIconW.restype = wintypes.BOOL
        db = Store()
        enabled = db.settings()["desktop_hotkey"]
        hwnd = user.CreateWindowExW(0, "STATIC", "Zoderise Focus reminders", 0, 0, 0, 0, 0, None, None, None, None)
        icon = NotificationData()
        icon.cbSize, icon.hWnd, icon.uID = ctypes.sizeof(icon), hwnd, 1
        icon.hIcon, icon.szTip = user.LoadIconW(None, ctypes.c_void_p(32512)), "Zoderise Focus"
        added = False
        try:
            self.status["shortcut_registered"] = bool(user.RegisterHotKey(None, 99, 0x4003, 0x20)) if enabled else False
            if enabled and not self.status["shortcut_registered"]:
                self.status["shortcut_error"] = "Shortcut is already in use or could not be registered."
            self.status["thread_id"] = ctypes.windll.kernel32.GetCurrentThreadId()
            self.status["notification_api"] = bool(hwnd)
            self.status.update(running=True, pid=os.getpid())
            self.write_status()
            last = 0
            while not self.stop.is_set():
                message = wintypes.MSG()
                while user.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
                    if message.message == 0x0312 and message.wParam == 99 and self.status["shortcut_registered"]:
                        self.capture()
                if time.monotonic() - last >= 15:
                    last = time.monotonic()
                    try:
                        db.maintenance()
                        if db.settings()["reminders"] and hwnd:
                            for alert in db.take_notifications():
                                icon.uFlags, icon.szInfoTitle, icon.dwInfoFlags = 2 | 4 | 16, "Zoderise Focus", 1
                                icon.szInfo = windows_text(alert["title"] + ": " + alert["body"], 255)
                                icon.uTimeout = 6000
                                accepted = bool(shell.Shell_NotifyIconW(1 if added else 0, ctypes.byref(icon)))
                                added = added or accepted
                                if accepted:
                                    self.status['notifications_accepted'] = self.status.get('notifications_accepted', 0) + 1
                                    self.write_status()
                                if not accepted:
                                    logging.warning("Windows did not accept a Focus notification; reminder stays in inbox")
                    except (ValueError, OSError) as exc:
                        logging.warning("Background maintenance failed: %s", exc)
                self.stop.wait(.15)
        finally:
            if self.status["shortcut_registered"]:
                user.UnregisterHotKey(None, 99)
            if added:
                shell.Shell_NotifyIconW(2, ctypes.byref(icon))
            if hwnd:
                user.DestroyWindow(hwnd)
            self.status.update(running=False, shortcut_registered=False)
            self.write_status()
