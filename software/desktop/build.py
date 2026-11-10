"""Build on the target OS: python desktop/build.py. No cross-compilation."""

from pathlib import Path
import platform
import os
import shutil
import subprocess
import sys

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parent
OUT = ROOT / "output" / "desktop"
os.environ.setdefault("PYINSTALLER_CONFIG_DIR", str(ROOT / "build" / "desktop-cache"))

import PyInstaller.__main__


def main():
    sys.path.insert(0, str(SOURCE))
    from otoskop.firmware_bundle import load_bundle
    load_bundle()  # Never ship a partial or stale/corrupt binary set.
    PyInstaller.__main__.run([
        "--noconfirm", "--clean", "--distpath", str(OUT),
        "--workpath", str(ROOT / "build" / "desktop"),
        str(SOURCE / "Otoskop.spec"),
    ])
    if sys.platform == "darwin":
        archive = OUT / f"Otoskop-Mac-{platform.machine()}.zip"
        subprocess.run(["ditto", "-c", "-k", "--sequesterRsrc", "--keepParent",
                        str(OUT / "Otoskop.app"), str(archive)], check=True)
    elif sys.platform == "win32":
        archive = Path(shutil.make_archive(str(OUT / f"Otoskop-Windows-{platform.machine()}"),
                                          "zip", OUT, "Otoskop"))
    else:
        archive = Path(shutil.make_archive(str(OUT / "Otoskop-Linux"), "gztar", OUT, "Otoskop"))
    print(f"Fertig: {archive}")


if __name__ == "__main__":
    main()
