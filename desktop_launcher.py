"""Portable Windows wrapper; loopback server with explicit process cleanup."""
from __future__ import annotations

import ctypes
import json
import logging
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import psutil

from focus.store import data_home

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def parent_watchdog(pid, created):
    while True:
        time.sleep(2)
        try:
            parent = psutil.Process(pid)
            if abs(parent.create_time() - created) > 0.01 or not parent.is_running():
                os._exit(0)
        except psutil.Error:
            os._exit(0)


def run_server(port, parent_pid=None, parent_created=None):
    if parent_pid:
        threading.Thread(target=parent_watchdog, args=(int(parent_pid), float(parent_created)), daemon=True).start()
    os.chdir(ROOT)
    from streamlit.web import bootstrap
    options = {
        "server.address": "127.0.0.1", "server.port": int(port), "server.headless": True,
        "global.developmentMode": False,
        "browser.gatherUsageStats": False, "server.fileWatcherType": "none",
        "server.enableCORS": True, "server.enableXsrfProtection": True,
    }
    bootstrap.load_config_options(options)
    bootstrap.run(str(ROOT / "app.py"), False, [], options)


def available_port():
    for port in range(8650, 8671):
        with socket.socket() as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free local port between 8650 and 8670. Close an older Focus window and try again.")


def stop_child(process):
    try:
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for child in reversed(children):
            try:
                child.terminate()
            except psutil.Error:
                pass
        try:
            parent.terminate()
        except psutil.Error:
            pass
        _, alive = psutil.wait_procs(children + [parent], timeout=3)
        for child in alive:
            try:
                child.kill()
            except psutil.Error:
                pass
    except psutil.Error:
        pass


def main():
    if "--focus-server" in sys.argv:
        index = sys.argv.index("--focus-server")
        args = sys.argv[index + 1:]
        run_server(*args)
        return
    home = data_home()
    home.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=home / "desktop.log", level=logging.INFO)
    process = None
    log = None
    bridge = None
    try:
        port = available_port()
        args = [sys.executable]
        if not getattr(sys, "frozen", False):
            args.append(str(ROOT / "desktop_launcher.py"))
        args += ["--focus-server", str(port), str(os.getpid()), str(psutil.Process().create_time())]
        log = open(home / "server.log", "a", encoding="utf-8")
        process = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=log,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        url = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("The local app server could not start. See server.log in your ZoderiseFocus data folder.")
            try:
                with urllib.request.urlopen(url + "/_stcore/health", timeout=1) as response:
                    if response.status == 200:
                        break
            except Exception:
                time.sleep(.3)
        else:
            raise RuntimeError("The local app did not become ready within 90 seconds.")
        import webview
        window = webview.create_window("Zoderise Focus", url, width=1350, height=900, min_size=(430, 650),
                                       background_color="#F7F6F2")
        from focus.desktop import DesktopBridge
        bridge = DesktopBridge(window, url)
        window.events.closed += lambda: bridge.stop.set()
        # Explicitly use the modern installed WebView2 runtime.
        webview.start(func=bridge.start, gui="edgechromium" if os.name == "nt" else None)
    except Exception as exc:
        logging.exception("Desktop startup failed")
        if os.name == "nt":
            ctypes.windll.user32.MessageBoxW(0, f"{exc}\n\nWindows requires Microsoft Edge WebView2 Runtime.\nLogs: {home}", "Zoderise Focus", 0x10)
        else:
            print(exc, file=sys.stderr)
        raise
    finally:
        if bridge:
            bridge.close()
        if process:
            stop_child(process)
        if log:
            log.close()


if __name__ == "__main__":
    main()
