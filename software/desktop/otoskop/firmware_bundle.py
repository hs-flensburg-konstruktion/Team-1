"""Validate the built-in, fixed-target firmware before opening any USB port."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sys


class InstallError(Exception):
    def __init__(self, code, detail=""):
        self.code, self.detail = code, str(detail)
        super().__init__(self.detail or code)


@dataclass(frozen=True)
class FirmwareBundle:
    manifest: dict
    images: tuple  # (offset, immutable bytes); verified once, no TOCTOU reads


def resource_folder():
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return root / "firmware"


def load_bundle(folder=None):
    folder = Path(folder) if folder is not None else resource_folder()
    try:
        manifest = json.loads((folder / "manifest.json").read_text())
        if (manifest["schema"] != 1 or manifest["chip"] != "ESP32-S3"
                or manifest["board"] != "XIAO_ESP32S3_SENSE"
                or manifest["flash_bytes"] != 8 * 1024 * 1024
                or manifest["flash_mode"] != "dio" or manifest["flash_freq"] != "80m"
                or manifest["ssid_prefix"] != "Otoskop"
                or type(manifest["led_configured"]) is not bool
                or not isinstance(manifest["version"], str)
                or not isinstance(manifest["password"], str)):
            raise ValueError("Unsupported firmware target")
        expected = {0x0: 0x8000, 0x8000: 0x1000, 0xE000: 0x2000, 0x10000: 0x330000}
        images = {}
        for entry in manifest["images"]:
            name, offset = entry["file"], entry["offset"]
            if (Path(name).name != name or offset not in expected or offset in images):
                raise ValueError("Invalid firmware layout")
            data = (folder / name).read_bytes()
            if (not 0 < len(data) <= expected[offset] or len(data) != entry["bytes"]
                    or hashlib.sha256(data).hexdigest() != entry["sha256"]):
                raise ValueError("Firmware integrity check failed: " + name)
            if offset in (0, 0x10000) and data[0] != 0xE9:
                raise ValueError("Invalid ESP image")
            images[offset] = data
        if set(images) != set(expected):
            raise ValueError("Incomplete firmware bundle")
        return FirmwareBundle(manifest, tuple(sorted(images.items())))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise InstallError("bundle", str(exc)) from exc


def wifi_name(mac, prefix="Otoskop"):
    if isinstance(mac, bytes):
        mac = mac.hex()
    compact = str(mac).replace(":", "").replace("-", "").lower()
    if len(compact) != 12 or any(c not in "0123456789abcdef" for c in compact):
        raise InstallError("identity", "Invalid device MAC address")
    return prefix + "-" + compact[-6:].upper()


def supported_ports(ports=None):
    if ports is None:
        from serial.tools.list_ports import comports
        ports = comports()
    known = {(0x2886, 0x0056), (0x2886, 0x8056), (0x303A, 0x1001), (0x303A, 0x0002)}
    devices = {}
    for port in ports:
        if (port.vid, port.pid) not in known:
            continue
        # macOS also exposes /dev/tty.* aliases for the same device.
        if str(port.device).startswith("/dev/tty."):
            continue
        devices[port.device] = dict(device=port.device, vid=port.vid, pid=port.pid,
                                    serial_number=port.serial_number or "", location=port.location or "",
                                    description=port.description or "USB ESP")
    return [devices[name] for name in sorted(devices)]


def confirm_port(selected, ports=None):
    for current in supported_ports(ports):
        if current["device"] != selected.get("device"):
            continue
        for key in ("vid", "pid", "serial_number", "location"):
            if selected.get(key) and selected[key] != current[key]:
                raise InstallError("device_changed", "USB device identity changed")
        return current
    raise InstallError("device_missing", "Selected USB device is not connected")


def install_firmware(bundle, selected, emit, api=None):
    """One connection, fixed offsets, explicit chip/security/size checks, then verify."""
    if api is None:
        from esptool import cmds as api
    esp = None
    stage = "connect"
    try:
        emit(dict(event="stage", stage=stage, progress=3))
        esp = api.detect_chip(port=selected["device"], baud=115200, connect_attempts=3)
        stage = "identify"
        emit(dict(event="stage", stage=stage, progress=10))
        if esp.CHIP_NAME != "ESP32-S3":
            raise InstallError("wrong_chip", esp.CHIP_NAME)
        if (esp.secure_download_mode or esp.get_secure_boot_enabled()
                or esp.get_flash_encryption_enabled()):
            raise InstallError("security", "Protected devices are not supported")
        mac = bytes(esp.read_mac())
        ssid = wifi_name(mac, bundle.manifest["ssid_prefix"])
        identity = ":".join(f"{b:02x}" for b in mac)
        esp = api.run_stub(esp)
        api.attach_flash(esp)
        capacity_code = (esp.flash_id() >> 16) & 0xFF
        if not 0x17 <= capacity_code <= 0x1F:
            raise InstallError("flash_size", "At least 8 MB NOR flash is required")
        esp.change_baud(460800)
        params = dict(flash_freq=bundle.manifest["flash_freq"],
                      flash_mode=bundle.manifest["flash_mode"], flash_size="8MB")
        stage = "write"
        total = sum(len(data) for _, data in bundle.images)
        written = 0
        for offset, data in bundle.images:
            emit(dict(event="stage", stage=stage, progress=15 + int(65 * written / total),
                      base=15 + 65 * written / total, span=65 * len(data) / total))
            api.write_flash(esp, [(offset, data)], **params, erase_all=False)
            written += len(data)
        stage = "verify"
        emit(dict(event="stage", stage=stage, progress=85))
        api.verify_flash(esp, list(bundle.images), **params)
        emit(dict(event="stage", stage="restart", progress=97))
        reset_required = False
        try:
            api.reset_chip(esp, "watchdog-reset")
        except Exception as exc:
            reset_required = True
            emit(dict(event="log", text="Restart manually: " + str(exc)))
        result = dict(device_id=identity, ssid=ssid, password=bundle.manifest["password"],
                      firmware_version=bundle.manifest["version"], reset_required=reset_required,
                      led_configured=bundle.manifest["led_configured"])
        emit(dict(event="done", progress=100, result=result))
        return result
    except InstallError:
        raise
    except Exception as exc:
        code = "connection" if stage in ("connect", "identify") else "verification" if stage == "verify" else "write"
        raise InstallError(code, str(exc)) from exc
    finally:
        if esp is not None:
            try:
                esp._port.close()
            except Exception:
                pass
