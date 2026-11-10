"""Developer release step: package a freshly compiled, fixed-board firmware."""
import hashlib
import json
from pathlib import Path
import re
import shutil

root = Path(__file__).resolve().parent.parent
source = root / "firmware" / "Otoskop"
settings = (source / "settings.h").read_text()
target = root / "desktop" / "firmware"
target.mkdir(exist_ok=True)
inputs = [(0, root/"build/artifacts/Otoskop.ino.bootloader.bin"),
          (0x8000, root/"build/artifacts/Otoskop.ino.partitions.bin"),
          (0xE000, root/"build/compiler/boot_app0.bin"),
          (0x10000, root/"build/artifacts/Otoskop.ino.bin")]
app = inputs[-1][1]
for file in source.glob("*"):
    if file.suffix in (".ino", ".h") and file.stat().st_mtime > app.stat().st_mtime:
        raise SystemExit("Firmware source changed. Run ./scripts/build.sh first.")
manifest = dict(schema=1, board="XIAO_ESP32S3_SENSE", chip="ESP32-S3", flash_bytes=8*1024*1024,
                flash_mode="dio", flash_freq="80m",
                version=re.search(r'FIRMWARE_VERSION\[\] = "([^"]+)"', settings)[1],
                ssid_prefix=re.search(r'AP_SSID\[\] = "([^"]+)"', settings)[1],
                password=re.search(r'AP_PASSWORD\[\] = "([^"]+)"', settings)[1],
                led_configured=int(re.search(r'LIGHT_GPIO = (-?\d+)', settings)[1]) >= 0,
                source_sha256={file.name:hashlib.sha256(file.read_bytes()).hexdigest()
                               for file in source.iterdir() if file.suffix in (".ino", ".h")}, images=[])
for offset, file in inputs:
    shutil.copy2(file, target/file.name)
    data = file.read_bytes()
    manifest["images"].append(dict(file=file.name, offset=offset, bytes=len(data),
                                    sha256=hashlib.sha256(data).hexdigest()))
(target/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
print("Prepared firmware",manifest["version"],"in",target)
