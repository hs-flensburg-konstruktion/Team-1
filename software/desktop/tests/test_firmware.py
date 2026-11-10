import json
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace
import unittest

from otoskop.firmware_bundle import (InstallError, confirm_port, install_firmware,
                                      load_bundle, resource_folder, supported_ports, wifi_name)


def port(device="COM7", vid=0x303A, pid=0x1001, serial="same", location="usb-1"):
    return SimpleNamespace(device=device, vid=vid, pid=pid, serial_number=serial,
                           location=location, description="USB ESP")


class FakeESP:
    CHIP_NAME = "ESP32-S3"
    secure_download_mode = False
    secure = False
    encrypted = False
    capacity = 0x17

    def __init__(self):
        self.closed = False
        self._port = SimpleNamespace(close=self.close)

    def close(self): self.closed = True
    def get_secure_boot_enabled(self): return self.secure
    def get_flash_encryption_enabled(self): return self.encrypted
    def read_mac(self): return (0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF)
    def flash_id(self): return self.capacity << 16 | 0x40EF
    def change_baud(self, baud): self.baud = baud


class FakeAPI:
    def __init__(self, esp=None):
        self.esp = esp or FakeESP()
        self.writes, self.verified, self.resets = [], [], []
        self.fail_write = self.fail_verify = self.fail_reset = False

    def detect_chip(self, **_): return self.esp
    def run_stub(self, esp): return esp
    def attach_flash(self, esp): pass

    def write_flash(self, esp, images, **params):
        if self.fail_write: raise RuntimeError("Cable disconnected")
        self.writes.append((images, params))

    def verify_flash(self, esp, images, **params):
        if self.fail_verify: raise RuntimeError("Digest mismatch")
        self.verified = images

    def reset_chip(self, esp, mode):
        if self.fail_reset: raise RuntimeError("Reset not available")
        self.resets.append(mode)


class FirmwareTests(unittest.TestCase):
    def test_only_supported_unique_usb_ports_are_listed(self):
        ports = [port(), port(), port("/dev/tty.usbmodem1"),
                 port("COM8", vid=0x2886, pid=0x0056), port("COM9", vid=0x1234),
                 port("Bluetooth", vid=None, pid=None)]
        self.assertEqual([p["device"] for p in supported_ports(ports)], ["COM7", "COM8"])
        selected = supported_ports([port()])[0]
        self.assertEqual(confirm_port(selected, [port()]), selected)
        with self.assertRaises(InstallError) as error:
            confirm_port(selected, [port(serial="different")])
        self.assertEqual(error.exception.code, "device_changed")
        with self.assertRaises(InstallError) as error:
            confirm_port(selected, [])
        self.assertEqual(error.exception.code, "device_missing")

    def test_bundle_integrity_and_reserved_flash_regions(self):
        bundle = load_bundle()
        self.assertEqual([o for o, _ in bundle.images], [0, 0x8000, 0xE000, 0x10000])
        self.assertTrue(all(not 0x9000 <= o < 0xE000 for o, _ in bundle.images))
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)/"fw"
            shutil.copytree(resource_folder(), folder)
            app = folder/"Otoskop.ino.bin"
            app.write_bytes(app.read_bytes()[:-1]+b"x")
            with self.assertRaises(InstallError) as error:
                load_bundle(folder)
            self.assertEqual(error.exception.code, "bundle")
            shutil.copy2(resource_folder()/app.name, app)
            manifest = json.loads((folder/"manifest.json").read_text())
            manifest["images"][1]["offset"] = 0x9000
            (folder/"manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(InstallError): load_bundle(folder)

    def test_unique_wifi_name_matches_the_base_mac_suffix(self):
        for value in ("aa:bb:cc:dd:ee:ff", "aabbccddeeff", bytes.fromhex("aabbccddeeff")):
            self.assertEqual(wifi_name(value), "Otoskop-DDEEFF")
        with self.assertRaises(InstallError): wifi_name("not-a-mac")

    def test_install_writes_only_fixed_regions_then_verifies_and_resets(self):
        api, events = FakeAPI(), []
        bundle = load_bundle()
        result = install_firmware(bundle, dict(device="COM7"), events.append, api)
        self.assertEqual([entry[0][0][0] for entry in api.writes], [0, 0x8000, 0xE000, 0x10000])
        self.assertTrue(all(not params["erase_all"] for _, params in api.writes))
        self.assertEqual(api.verified, list(bundle.images))
        self.assertEqual(api.resets, ["watchdog-reset"])
        self.assertEqual(result["ssid"], "Otoskop-DDEEFF")
        self.assertEqual(result["device_id"], "aa:bb:cc:dd:ee:ff")
        self.assertFalse(result["reset_required"])
        self.assertEqual(events[-1]["event"], "done")
        self.assertTrue(api.esp.closed)

    def test_wrong_chip_small_flash_and_security_never_write(self):
        for field, value, expected in (("CHIP_NAME", "ESP32-C3", "wrong_chip"),
                                        ("capacity", 0x16, "flash_size"),
                                        ("secure", True, "security"),
                                        ("encrypted", True, "security"),
                                        ("secure_download_mode", True, "security")):
            with self.subTest(field=field):
                api = FakeAPI()
                setattr(api.esp, field, value)
                with self.assertRaises(InstallError) as error:
                    install_firmware(load_bundle(), dict(device="COM7"), lambda _:None, api)
                self.assertEqual(error.exception.code, expected)
                self.assertEqual(api.writes, [])
                self.assertTrue(api.esp.closed)

    def test_transfer_and_verification_failure_never_report_success(self):
        for field, code in (("fail_write", "write"), ("fail_verify", "verification")):
            with self.subTest(field=field):
                api, events = FakeAPI(), []
                setattr(api, field, True)
                with self.assertRaises(InstallError) as error:
                    install_firmware(load_bundle(), dict(device="COM7"), events.append, api)
                self.assertEqual(error.exception.code, code)
                self.assertFalse(any(e.get("event")=="done" for e in events))
                self.assertEqual(api.resets, [])
                self.assertTrue(api.esp.closed)

    def test_reset_failure_is_distinct_from_successful_verified_flash(self):
        api = FakeAPI()
        api.fail_reset = True
        result = install_firmware(load_bundle(), dict(device="COM7"), lambda _:None, api)
        self.assertTrue(result["reset_required"])
        self.assertTrue(api.verified)
