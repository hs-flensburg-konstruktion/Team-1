# Build with desktop/build.py on macOS or Windows.
from pathlib import Path
import sys
import sysconfig
import runpy
from importlib.metadata import distribution
from PyInstaller.utils.hooks import collect_all, copy_metadata

source = Path(SPECPATH)
version = runpy.run_path(str(source / "otoskop" / "__init__.py"))["__version__"]
is_mac = sys.platform == "darwin"
license_datas = [(str(file), "Lizenzen") for file in (source / "licenses").glob("*.txt")]
tool_datas, tool_binaries, tool_hidden = collect_all("esptool")
tool_datas += copy_metadata("esptool", recursive=True)
firmware_datas = [(str(file), "firmware") for file in (source / "firmware").iterdir()
                 if file.suffix in (".bin", ".json")]
python_license = Path(sysconfig.get_path("stdlib")) / "LICENSE.txt"
if python_license.exists():
    license_datas.append((str(python_license), "Lizenzen/Python"))
pyinstaller = distribution("PyInstaller")
for file in pyinstaller.files or []:
    if str(file).endswith("licenses/COPYING.txt"):
        license_datas.append((str(pyinstaller.locate_file(file)), "Lizenzen/PyInstaller"))
a = Analysis(
    [str(source / "main.py")], pathex=[str(source)],
    binaries=tool_binaries,
    datas=[(str(source / "assets" / "otoskop.png"), "assets")] + license_datas + firmware_datas + tool_datas,
    hiddenimports=tool_hidden + ["serial.tools.list_ports", "serial.tools.list_ports_windows", "serial.tools.list_ports_osx"],
    hookspath=[], hooksconfig={},
    runtime_hooks=[], excludes=["PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtOpenGL"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="Otoskop",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False, disable_windowed_traceback=False,
    icon=str(source / "assets" / ("otoskop.icns" if is_mac else "otoskop.ico")),
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Otoskop")
if is_mac:
    app = BUNDLE(
        coll, name="Otoskop.app", icon=str(source / "assets" / "otoskop.icns"),
        bundle_identifier="org.glia.otoskop.desktop",
        info_plist={
            "CFBundleShortVersionString": version,
            "CFBundleVersion": version,
            "NSHighResolutionCapable": True,
            "NSLocalNetworkUsageDescription": "Otoskop verbindet sich mit Ihrer Kamera im lokalen WLAN, um Livebilder, Fotos und die Beleuchtung zu steuern.",
            "LSMinimumSystemVersion": "13.0",
        },
    )
