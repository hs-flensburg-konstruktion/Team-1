import json
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import QObject, QProcess, QSettings, Signal
from otoskop.app import MainWindow
from otoskop.flash_process import FlashProcess
from otoskop.usb_setup import USBSetupDialog
from test_desktop import APP, JPEG, until

DEVICE = dict(device="COM7", vid=0x303A, pid=0x1001, serial_number="test",
              location="usb-1", description="USB ESP")
RESULT = dict(device_id="aa:bb:cc:dd:ee:ff", ssid="Otoskop-DDEEFF", password="Otoskop-2026",
              firmware_version="1.4.0", led_configured=False, reset_required=False)


class FakeRunner(QObject):
    event = Signal(dict)
    succeeded = Signal(dict)
    failed = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.busy = False
        self.starts = []

    def start(self, selected):
        self.starts.append(selected)
        self.busy = True

    def finish(self):
        self.busy = False
        self.succeeded.emit(dict(RESULT))


class USBDialogTests(unittest.TestCase):
    def setUp(self):
        QSettings(QSettings.defaultFormat(), QSettings.Scope.UserScope,
                  "GliaOtoskop", "OtoskopDesktop").clear()
        self.windows = []

    def tearDown(self):
        for window, dialog, runner in self.windows:
            runner.busy = False
            dialog.close()
            window.close()
        APP.processEvents()

    def make(self, ports):
        window = MainWindow()
        runner = FakeRunner()
        dialog = USBSetupDialog(window.tr, window, scanner=lambda: ports, runner=runner)
        window.setup_dialog = dialog
        self.windows.append((window, dialog, runner))
        window.show()
        dialog.show()
        APP.processEvents()
        return window, dialog, runner

    def test_no_device_and_multiple_devices_never_start_automatically(self):
        _, dialog, runner = self.make([])
        self.assertFalse(dialog.next_button.isEnabled())
        dialog._next()
        self.assertEqual(runner.starts, [])
        ports = [dict(DEVICE), dict(DEVICE, device="COM8", serial_number="other")]
        _, dialog, runner = self.make(ports)
        self.assertEqual(dialog.ports.currentIndex(), -1)
        self.assertFalse(dialog.next_button.isEnabled())
        dialog.ports.setCurrentIndex(1)
        dialog._next()
        self.assertEqual(dialog.page, 1)
        self.assertEqual(runner.starts, [])
        dialog._next()
        self.assertEqual(runner.starts[0]["device"], "COM8")

    def test_install_close_guard_and_language_change_preserve_progress(self):
        window, dialog, runner = self.make([dict(DEVICE)])
        dialog._next()
        dialog._next()
        self.assertTrue(runner.busy)
        runner.event.emit(dict(event="stage", stage="write", progress=47))
        window.set_language("en")
        self.assertEqual(dialog.progress.value(), 47)
        self.assertIn("Writing firmware", dialog.install_status.text())
        self.assertFalse(dialog.boot_button.isEnabled())
        self.assertFalse(dialog.close_button.isEnabled())
        dialog.reject()
        self.assertTrue(dialog.isVisible())
        window.close()
        self.assertTrue(window.isVisible())
        runner.busy = False
        runner.failed.emit("connection", "A simulated USB error")
        self.assertTrue(dialog.boot_button.isEnabled())
        self.assertIn("bootloader", dialog.install_status.text())

    def test_verified_transfer_does_not_claim_camera_readiness(self):
        window, dialog, runner = self.make([dict(DEVICE)])
        dialog._next()
        dialog._next()
        runner.finish()
        self.assertEqual(dialog.page, 2)
        self.assertEqual(dialog.ssid_label.text(), RESULT["ssid"])
        self.assertFalse(dialog.camera_verified)
        dialog._next()
        self.assertEqual(dialog.page, 3)
        self.assertFalse(dialog.next_button.isEnabled())
        # No network access: feed the same status callback used by the HTTP client.
        dialog.check_timer.start()
        dialog._checked(dict(device_id="other", firmware_version="1.4.0", camera_ok=True))
        self.assertFalse(dialog.camera_verified)
        self.assertIn("anderen Gerät", dialog.check_status.text())
        dialog.check_timer.start()
        dialog._checked(dict(device_id=RESULT["device_id"], firmware_version="1.4.0", camera_ok=False))
        self.assertFalse(dialog.camera_verified)
        dialog.check_timer.start()
        dialog._checked(dict(device_id=RESULT["device_id"], firmware_version="1.4.0", camera_ok=True, stream_ok=True, led_supported=False))
        self.assertFalse(dialog.camera_verified)
        dialog._checked_frame(b"invalid-image")
        self.assertFalse(dialog.camera_verified)
        dialog._checked_frame(JPEG)
        self.assertTrue(dialog.camera_verified)
        self.assertTrue(dialog.next_button.isEnabled())
        window.set_language("en")
        self.assertIn("Lighting has not been configured", dialog.check_status.text())

    def test_boot_help_and_reenumerated_port_selection(self):
        ports = [dict(DEVICE)]
        window, dialog, runner = self.make(ports)
        dialog._boot_help()
        self.assertTrue(dialog.boot_dialog.isVisible())
        window.set_language("en")
        self.assertEqual(dialog.boot_dialog.windowTitle(), "How to enter bootloader mode")
        dialog.boot_dialog.close()
        ports[:] = [dict(DEVICE, device="COM9")]
        dialog._scan()
        dialog._next()
        self.assertEqual(dialog.selected["device"], "COM9")
        self.assertEqual(runner.starts, [])

    def test_retry_follows_same_usb_device_after_boot_mode_port_change(self):
        ports = [dict(DEVICE)]
        _, dialog, runner = self.make(ports)
        dialog._next()
        dialog._next()
        runner.busy = False
        runner.failed.emit("connection", "Enter bootloader")
        ports[:] = [dict(DEVICE, device="COM9")]
        dialog._next()
        self.assertEqual(runner.starts[-1]["device"], "COM9")


class ProcessTests(unittest.TestCase):
    def test_real_worker_self_test_uses_no_usb_device(self):
        runner, results, errors = FlashProcess(), [], []
        runner.succeeded.connect(results.append)
        runner.failed.connect(lambda code, detail: errors.append((code, detail)))
        runner.start({}, action="self-test")
        until(lambda: not runner.busy, timeout=15)
        self.assertEqual(errors, [])
        self.assertEqual(results[0]["esptool_version"], "5.1.0")
        self.assertEqual(results[0]["firmware_version"], "1.5.0")
        self.assertGreater(results[0]["stub_bytes"], 0)

    def test_process_exit_drains_large_logs_and_reports_final_result(self):
        runner, results = FlashProcess(), []
        runner.succeeded.connect(results.append)
        runner.job_dir = tempfile.TemporaryDirectory()
        lines = [dict(event="log", text="x"*1000) for _ in range(100)]
        lines.append(dict(event="done", result=dict(verified=True)))
        (Path(runner.job_dir.name)/"events.jsonl").write_text("".join(json.dumps(e)+"\n" for e in lines))
        runner.busy = True
        runner._finished(0, QProcess.ExitStatus.NormalExit)
        self.assertEqual(results, [dict(verified=True)])
        self.assertIsNone(runner.job_dir)
