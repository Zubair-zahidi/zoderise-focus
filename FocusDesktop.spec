from PyInstaller.utils.hooks import collect_all, collect_submodules
from focus import __version__

datas, binaries, hiddenimports = [], [], ["focus", "focus.store", "focus.ui", "focus.planning", "focus.crypto", "focus.components", "focus.i18n", "focus.desktop"]
for package in ("streamlit", "webview", "clr_loader", "pythonnet", "altair", "pydeck", "cryptography"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h
datas += [("app.py", "."), ("app_pages", "app_pages"), ("assets", "assets"), (".streamlit", ".streamlit")]
a = Analysis(["desktop_launcher.py"], pathex=["."], binaries=binaries, datas=datas,
             hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=["torch", "tensorflow", "scipy", "matplotlib", "pytest", "playwright"], noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name=f"Zoderise-Focus-{__version__}-Windows-x64",
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False,
          icon="assets/icon.ico", version="version_info.txt")
