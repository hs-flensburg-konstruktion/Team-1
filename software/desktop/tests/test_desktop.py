"""Exercise the real Qt network client against a local HTTP device double."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.parse import parse_qs, urlsplit

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QSettings
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from otoskop.app import MainWindow
from otoskop.client import OtoscopeClient

APP = QApplication.instance() or QApplication([])
APP.setStyle("Fusion")
SETTINGS = tempfile.TemporaryDirectory()
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, SETTINGS.name)
image = QImage(64, 48, QImage.Format.Format_RGB32)
image.fill(QColor("#397b70"))
array = QByteArray()
buffer = QBuffer(array)
buffer.open(QIODevice.OpenModeFlag.WriteOnly)
image.save(buffer, "JPEG")
buffer.close()
JPEG = bytes(array)


def until(predicate, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        APP.processEvents()
        if predicate():
            return
        time.sleep(0.005)
    raise AssertionError("Timed out waiting for Qt event")


class DeviceHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_):
        pass

    def send(self, body, content_type="application/json", code=200):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        state = self.server.state
        if self.path == "/status":
            state["status_requests"] += 1
            if state["bad_status"]:
                self.send(b"not-json")
                return
            self.send(json.dumps({"camera_ok": state["camera_ok"], "sd_ok": False,
                                  "snapshot_supported": not state["old"], "led_supported": not state["old"],
                                  "led_brightness": state["brightness"], "camera": "Bereit"}).encode())
        elif self.path == "/stream":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace;boundary=otoskop_frame")
            self.end_headers()
            packet = b"--otoskop_frame\r\nContent-Type: image/jpeg\r\nContent-Length: " + str(len(JPEG)).encode() + b"\r\n\r\n" + JPEG + b"\r\n"
            try:
                while not self.server.stopped.is_set():
                    # Intentionally split headers and JPEG data across writes.
                    for offset in range(0, len(packet), 29):
                        self.wfile.write(packet[offset:offset + 29])
                    self.wfile.flush()
                    time.sleep(0.03)
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.close_connection = True
        else:
            self.send(b'{"error":"Unbekannt"}', code=404)

    def do_POST(self):
        state = self.server.state
        url = urlsplit(self.path)
        if url.path == "/snapshot":
            time.sleep(state["delay"])
            if state["capture_error"]:
                self.send(b'{"error":"Kamera beschaeftigt"}', code=503)
            else:
                self.send(state["photo"], "image/jpeg")
        elif url.path == "/led":
            time.sleep(state["delay"])
            value = int(parse_qs(url.query)["brightness"][0])
            state["brightness"] = value
            state["commands"].append(value)
            self.send(json.dumps({"led_brightness": value}).encode())
        else:
            self.send(b'{}', code=404)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), DeviceHandler)
        self.server.daemon_threads = True
        self.server.stopped = threading.Event()
        self.server.state = dict(bad_status=False, camera_ok=True, old=False,
                                 brightness=0, commands=[], delay=0, capture_error=False,
                                 photo=JPEG, status_requests=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.client = OtoscopeClient()
        self.photos, self.errors, self.frames = [], [], []
        self.client.photo_received.connect(lambda data, source: self.photos.append((data, source)))
        self.client.photo_failed.connect(self.errors.append)
        self.client.frame_received.connect(self.frames.append)
        self.client.connect_device(f"127.0.0.1:{self.server.server_port}")
        # Production ESP32 always serves stream on 81; test server uses a free port.
        self.client.stream_url = self.client.base_url + "/stream"
        until(lambda: self.client.connected)

    def tearDown(self):
        self.client.disconnect_device()
        APP.processEvents()
        self.server.stopped.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        APP.processEvents()

    def test_stream_and_fresh_capture_without_sd(self):
        until(lambda: bool(self.frames))
        self.assertEqual(self.frames[-1], JPEG)
        self.assertFalse(self.client.status["sd_ok"])
        self.client.capture()
        until(lambda: bool(self.photos))
        self.assertEqual(self.photos[0], (JPEG, "Neue Kameraaufnahme"))
        self.client.set_preview(False)
        self.assertIsNone(self.client._stream_reply)
        self.photos.clear()
        self.client.capture()
        until(lambda: bool(self.photos))
        self.assertEqual(self.photos[0][0], JPEG)

    def test_old_firmware_captures_only_recent_live_frame(self):
        self.server.state["old"] = True
        self.client._poll_status()
        until(lambda: not self.client.status["snapshot_supported"] and bool(self.frames))
        self.client.capture()
        self.assertIn("ältere Firmware", self.photos[0][1])
        self.client.last_frame_at -= 3
        self.client.capture()
        self.assertTrue(self.errors)

    def test_large_photo_can_take_longer_than_control_timeout_and_resumes_preview(self):
        image = QImage(2048, 1536, QImage.Format.Format_RGB32)
        image.fill(QColor("#b6c5d4"))
        data = QByteArray()
        buffer = QBuffer(data)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "JPEG", 95)
        buffer.close()
        self.server.state.update(photo=bytes(data), delay=5)
        until(lambda: bool(self.frames))
        self.client.poll.setInterval(60)
        self.client.capture()
        self.assertIsNone(self.client._stream_reply)
        self.assertFalse(self.client.watchdog.isActive())
        request_count = self.server.state["status_requests"]
        until(lambda: bool(self.photos), timeout=8)
        self.assertEqual(self.server.state["status_requests"], request_count)
        self.assertTrue(self.client.connected)
        self.assertFalse(self.errors)
        self.assertEqual(self.photos[0][0], bytes(data))
        self.assertEqual(QImage.fromData(self.photos[0][0]).size(), image.size())
        count = len(self.frames)
        until(lambda: len(self.frames) > count)
        self.assertEqual(self.frames[-1], JPEG)

    def test_capture_error_resumes_preview_and_user_pause_is_preserved(self):
        until(lambda: bool(self.frames))
        self.server.state.update(capture_error=True, delay=0.1)
        self.client.capture()
        until(lambda: bool(self.errors))
        count = len(self.frames)
        until(lambda: len(self.frames) > count)
        self.server.state.update(capture_error=False, delay=0.1)
        self.client.capture()
        self.client.set_preview(False)
        until(lambda: bool(self.photos))
        self.assertIsNone(self.client._stream_reply)
        self.assertFalse(self.client.retry.isActive())

    def test_off_command_is_not_lost_during_inflight_led_request(self):
        self.server.state["delay"] = 0.1
        self.client.request_brightness(73)
        self.client.request_brightness(0)
        until(lambda: len(self.server.state["commands"]) >= 2)
        self.assertEqual(self.server.state["commands"][-2:], [73, 0])

    def test_failed_capture_and_late_response_after_disconnect(self):
        self.server.state["capture_error"] = True
        self.client.capture()
        until(lambda: bool(self.errors))
        self.assertIn("beschaeftigt", self.errors[0])
        self.server.state.update(capture_error=False, delay=0.1)
        self.client.capture()
        self.client.disconnect_device()
        deadline = time.monotonic() + 0.25
        while time.monotonic() < deadline:
            APP.processEvents()
            time.sleep(0.005)
        self.assertEqual(self.photos, [])

    def test_status_failure_recovers_automatically(self):
        self.client.poll.setInterval(80)
        self.server.state["bad_status"] = True
        until(lambda: not self.client.connected)
        self.assertIsNone(self.client._stream_reply)
        self.server.state["bad_status"] = False
        until(lambda: self.client.connected)
        until(lambda: bool(self.frames))


class UiTests(unittest.TestCase):
    def setUp(self):
        settings = QSettings(QSettings.defaultFormat(), QSettings.Scope.UserScope,
                             "GliaOtoskop", "OtoskopDesktop")
        settings.clear()

    def test_native_photo_is_saved_unchanged_and_wrong_resolution_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            window = MainWindow()
            self.addCleanup(window.close)
            window.folder = Path(folder)
            window.client.connected = True
            window.status = dict(camera_ok=True, snapshot_supported=True,
                                 high_res_photo_supported=True, photo_width=2048, photo_height=1536)
            image = QImage(2048, 1536, QImage.Format.Format_RGB32)
            image.fill(QColor("#89abcd"))
            data = QByteArray()
            buffer = QBuffer(data)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "JPEG", 95)
            buffer.close()
            window._save_photo(bytes(data), "Neue Kameraaufnahme")
            files = list(Path(folder).glob("*.jpg"))
            self.assertEqual(len(files), 1)
            self.assertEqual(files[0].read_bytes(), bytes(data))
            self.assertIn("2048 × 1536", window.capture_note.text())
            window.language_buttons["en"].click()
            self.assertIn("Maximum sensor resolution", window.capture_note.text())
            window._save_photo(JPEG, "Neue Kameraaufnahme")
            self.assertEqual(len(list(Path(folder).glob("*.jpg"))), 1)
            self.assertEqual(window.gallery.count(), 1)

    def test_demo_pause_capture_and_switch_to_real_device(self):
        with tempfile.TemporaryDirectory() as folder:
            window = MainWindow(demo=True)
            self.assertTrue(window.settings.fileName().startswith(SETTINGS.name))
            window.folder = Path(folder)
            window.show()
            APP.processEvents()
            window.brightness.setValue(21)
            self.assertEqual(window.demo_brightness, 21)
            window.live_button.setChecked(False)
            self.assertFalse(window.demo_timer.isActive())
            window.capture_button.click()
            files = list((Path(folder) / "Demo").glob("DEMO_*.jpg"))
            self.assertEqual(len(files), 1)
            self.assertFalse(QImage(str(files[0])).isNull())
            self.assertEqual(window.gallery.count(), 1)
            window.demo_check.setChecked(False)
            self.assertFalse(window.capture_button.isEnabled())
            self.assertFalse(window.brightness.isEnabled())
            self.assertFalse(window.client.connected)
            window.address.setText("http://host/path")
            window.connect_button.click()
            self.assertFalse(window.want_connection)
            window.close()

    def test_live_language_switch_preserves_demo_capture_and_open_guide(self):
        with tempfile.TemporaryDirectory() as folder:
            window = MainWindow(demo=True)
            self.addCleanup(window.close)
            window.folder = Path(folder)
            window.show()
            APP.processEvents()
            window.brightness.setValue(31)
            window.live_button.setChecked(False)
            phase = window.demo_phase
            window.capture_button.click()
            self.assertEqual(window.gallery.count(), 1)
            window._show_guide()
            window.guide.go(1)
            window.language_buttons["en"].click()
            self.assertEqual(window.tr.language, "en")
            self.assertEqual(window.capture_button.text(), "Capture photo")
            self.assertEqual(window.connect_button.text(), "Connect")
            self.assertEqual(window.live_button.text(), "Resume live view")
            self.assertIn("Demo photo saved", window.message.text())
            self.assertEqual(window.guide.page, 1)
            self.assertIn("Join Wi-Fi", window.guide.steps[1].text())
            self.assertEqual(window.guide.next_button.text(), "Next")
            self.assertEqual(window.demo_brightness, 31)
            self.assertEqual(window.demo_phase, phase)
            self.assertFalse(window.demo_timer.isActive())
            self.assertFalse(window.client.connected)
            self.assertEqual(window.settings.value("language"), "en")
            window.language_buttons["de"].click()
            self.assertEqual(window.capture_button.text(), "Foto aufnehmen")
            self.assertEqual(window.live_button.text(), "Livebild starten")
            self.assertEqual(window.guide.next_button.text(), "Weiter")
            self.assertIn("Demofoto gespeichert", window.message.text())
            self.assertEqual(window.gallery.count(), 1)

    def test_language_persistence_and_error_translation(self):
        window = MainWindow()
        window.set_language("en")
        window.address.setText("http://host/path")
        window.connect_button.click()
        self.assertIn("Enter a local HTTP address", window.message.text())
        self.assertFalse(window.want_connection)
        window.set_language("de")
        self.assertIn("Bitte eine lokale HTTP-Adresse", window.message.text())
        window.set_language("en")
        window.close()
        reopened = MainWindow()
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.tr.language, "en")
        self.assertEqual(reopened.capture_button.text(), "Capture photo")
        self.assertEqual(reopened.address.text(), "192.168.4.1")

    def test_guide_navigation_and_troubleshooting_in_both_languages(self):
        window = MainWindow()
        self.addCleanup(window.close)
        window._show_guide()
        guide = window.guide
        for number in range(4):
            guide.steps[number].click()
            self.assertEqual(guide.stack.currentIndex(), number)
        guide.trouble_button.click()
        self.assertEqual(guide.page, 4)
        self.assertFalse(any(button.isChecked() for button in guide.steps))
        window.set_language("en")
        self.assertEqual(guide.next_button.text(), "Get started")
        self.assertEqual(guide.page, 4)
        guide.go(0)
        guide.next_button.click()
        self.assertEqual(guide.page, 1)
        guide.back_button.click()
        self.assertEqual(guide.page, 0)
        guide.go(3)
        guide.next_button.click()
        self.assertFalse(guide.isVisible())
        window._show_guide()
        self.assertTrue(guide.isVisible())

    def test_language_switch_does_not_change_device_connection_state(self):
        window = MainWindow()
        self.addCleanup(window.close)
        # Model an already connected device without creating real network traffic.
        window.client.connected = True
        window.want_connection = True
        window.connection_stage = "connected"
        window.status = dict(camera_ok=True, snapshot_supported=True, led_supported=False)
        window.camera_ready = True
        window._frame_received(JPEG)
        before = window.preview.image.cacheKey()
        window.set_language("en")
        self.assertTrue(window.client.connected)
        self.assertTrue(window.want_connection)
        self.assertEqual(window.connect_button.text(), "Disconnect")
        self.assertTrue(window.capture_button.isEnabled())
        self.assertFalse(window.brightness.isEnabled())
        self.assertEqual(window.preview.image.cacheKey(), before)
        self.assertIn("Lighting unavailable", window.led_note.text())

    def test_sidebar_visibility_persists_without_interrupting_preview(self):
        window = MainWindow(demo=True)
        window.show()
        APP.processEvents()
        before = window.preview.image.cacheKey()
        window.sidebar_button.click()
        self.assertTrue(window.sidebar.isHidden())
        self.assertTrue(window.demo_timer.isActive())
        self.assertEqual(window.preview.image.cacheKey(), before)
        self.assertTrue(window.capture_button.isEnabled())
        window.close()
        reopened = MainWindow()
        self.addCleanup(reopened.close)
        self.assertTrue(reopened.sidebar.isHidden())
        self.assertFalse(reopened.sidebar_button.isChecked())
        reopened.sidebar_button.click()
        self.assertFalse(reopened.sidebar.isHidden())

    def test_switch_keyboard_and_round_shutter_mouse_capture(self):
        with tempfile.TemporaryDirectory() as folder:
            window = MainWindow()
            self.addCleanup(window.close)
            window.folder = Path(folder)
            window.show()
            APP.processEvents()
            window.demo_check.setFocus()
            QTest.keyClick(window.demo_check, Qt.Key.Key_Space)
            APP.processEvents()
            self.assertTrue(window.demo)
            self.assertEqual(window.gallery.count(), 0)
            self.assertEqual(window.capture_button.size().toTuple(), (64, 64))
            QTest.mouseClick(window.capture_button, Qt.MouseButton.LeftButton)
            self.assertEqual(window.gallery.count(), 1)
            self.assertEqual(len(list((Path(folder)/"Demo").glob("DEMO_*.jpg"))), 1)
            window.capture_button.setFocus()
            QTest.keyClick(window.capture_button, Qt.Key.Key_Space)
            self.assertEqual(window.gallery.count(), 2)


if __name__ == "__main__":
    unittest.main()
