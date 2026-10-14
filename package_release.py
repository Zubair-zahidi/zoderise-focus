"""Package only tracked source files; no workspace data, logs, or build folders."""
import hashlib
import shutil
import subprocess
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
release = root / "release"
release.mkdir(exist_ok=True)
exe_name = "Zoderise-Focus-1.0.0-Windows-x64.exe"
shutil.copy2(root / "dist" / exe_name, release / exe_name)
files = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")
source = release / "Zoderise-Focus-1.0.0-Source.zip"
with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as z:
    for name in sorted(filter(None, files)):
        path = root / name
        if path.is_file():
            z.write(path, "zoderise-focus/" + name)
checksums = []
for path in (release / exe_name, source):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    checksums.append(f"{digest}  {path.name}")
    print(f"{path.name}: {path.stat().st_size:,} bytes · SHA256 {digest}")
(release / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n")
