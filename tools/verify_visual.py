"""Run an isolated local server and an actual-browser visual check."""
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
env = os.environ.copy()
env["FOCUS_DATA_HOME"] = os.environ.get('FOCUS_VISUAL_DATA_HOME', str(ROOT / "visual-data" / "upgrade-110"))
port = env.get("FOCUS_TEST_PORT", "8650")
env["FOCUS_URL"] = f"http://127.0.0.1:{port}"
command = ([env["FOCUS_EXE"], "--focus-server", port] if env.get("FOCUS_EXE") else
           [sys.executable, "-m", "streamlit", "run", "app.py", f"--server.port={port}", "--server.headless=true", "--server.fileWatcherType=none"])
with open(ROOT / "visual-server.log", "w", encoding="utf-8") as log:
    process = subprocess.Popen(command, env=env, stdout=log, stderr=log,
                               creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    try:
        for attempt in range(180):
            try:
                urllib.request.urlopen(env["FOCUS_URL"] + "/_stcore/health", timeout=1).close()
                break
            except Exception:
                if process.poll() is not None:
                    raise RuntimeError("App server exited: " + (ROOT / "visual-server.log").read_text())
                time.sleep(.5)
        else:
            raise RuntimeError("Server did not start")
        subprocess.run([env.get("NODE_EXE", "node"), str(ROOT / "tools" / "capture.cjs")], env=env, check=True, timeout=180)
    finally:
        import psutil
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for child in children:
                child.terminate()
            parent.terminate()
            _, alive = psutil.wait_procs(children + [parent], timeout=3)
            for child in alive:
                child.kill()
        except psutil.Error:
            pass
