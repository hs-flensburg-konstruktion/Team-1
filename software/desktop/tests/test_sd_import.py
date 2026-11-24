from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from urllib.parse import parse_qs, urlsplit

from PySide6.QtCore import Qt
from otoskop.sd_import import SDImporter, SDImportDialog, store_import
from otoskop.i18n import Translator
from otoskop.app import MainWindow
from test_desktop import APP, JPEG, until

DEVICE = "aa:bb:cc:dd:ee:ff"
NAMES = [f"IMG_{n:010d}.jpg" for n in (1, 2, 3)]


def headers(data=JPEG, device=DEVICE):
    return {b"x-photo-sha256": hashlib.sha256(data).hexdigest().encode(),
            b"x-photo-bytes": str(len(data)).encode(), b"content-type": b"image/jpeg",
            b"x-device-id": device.encode()}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *_): pass
    def send(self, body, extra=None):
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {b"content-type": b"application/json"}).items():
            self.send_header(k.decode(), v.decode())
        self.end_headers()
        try: self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError): pass
    def do_GET(self):
        state = self.server.state
        url = urlsplit(self.path)
        query = parse_qs(url.query)
        if url.path == "/status":
            self.send(json.dumps(dict(camera_ok=False, device_id=state["device"],
                                      sd_ok=True, sd_download_supported=True)).encode())
        elif url.path == "/photos":
            after = int(query["after"][0])
            state["pages"].append(after)
            names = NAMES[:2] if after == 0 else NAMES[2:]
            if state["bad_list"]: names = ["../IMG_0000000001.jpg"]
            self.send(json.dumps(dict(photos=[dict(name=n, bytes=len(JPEG)) for n in names],
                                      next_after=2 if after == 0 else None)).encode())
        elif url.path == "/photo":
            state["downloads"].append(query["name"][0])
            time.sleep(state["delay"])
            extra = headers()
            if state["corrupt"]: extra[b"x-photo-sha256"] = b"0" * 64
            self.send(JPEG, extra)


class SDTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.server.state = dict(device=DEVICE, pages=[], downloads=[], bad_list=False, corrupt=False, delay=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.address = f"127.0.0.1:{self.server.server_port}"
        self.importer = SDImporter()
        self.lists, self.errors, self.done = [], [], []
        self.importer.photos_ready.connect(self.lists.append)
        self.importer.failed.connect(self.errors.append)
        self.importer.finished.connect(lambda a,b:self.done.append((a,b)))

    def tearDown(self):
        self.importer.cancel()
        APP.processEvents()
        self.server.shutdown(); self.server.server_close()
        self.thread.join(2)
        self.folder.cleanup()

    def scan(self):
        self.importer.scan(self.address, DEVICE)
        until(lambda: bool(self.lists) or bool(self.errors))

    def test_paginated_import_without_camera_and_repeat_preserves_files(self):
        self.scan()
        self.assertEqual(self.server.state["pages"], [0,2])
        self.assertEqual(len(self.lists[0]),3)
        self.importer.start(self.lists[0], self.folder.name)
        until(lambda: bool(self.done))
        self.assertEqual(self.done, [(3,0)])
        files = sorted(Path(self.folder.name).rglob("*.jpg"))
        self.assertEqual([f.name for f in files], NAMES)
        self.assertTrue(all(f.read_bytes() == JPEG for f in files))
        times = [f.stat().st_mtime_ns for f in files]
        self.done.clear()
        self.importer.start(self.lists[0], self.folder.name)
        until(lambda: bool(self.done))
        self.assertEqual(self.done, [(0,3)])
        self.assertEqual([f.stat().st_mtime_ns for f in files], times)

    def test_corrupt_transfer_is_not_committed(self):
        self.scan(); self.server.state["corrupt"] = True
        self.importer.start(self.lists[0], self.folder.name)
        until(lambda: bool(self.errors))
        self.assertEqual(self.errors, ["sd_invalid_photo"])
        self.assertEqual(list(Path(self.folder.name).rglob("*.jpg")), [])
        self.assertEqual(self.done, [])

    def test_cancel_ignores_late_download(self):
        self.scan(); self.server.state["delay"] = .15
        self.importer.start(self.lists[0], self.folder.name)
        until(lambda: bool(self.server.state["downloads"]))
        self.importer.cancel()
        end = time.monotonic() + .25
        while time.monotonic() < end: APP.processEvents(); time.sleep(.005)
        self.assertEqual(list(Path(self.folder.name).rglob("*.jpg")), [])
        self.assertEqual(self.done, [])

    def test_wrong_device_and_path_traversal_stop_before_download(self):
        self.server.state["device"] = "11:22:33:44:55:66"
        self.scan()
        self.assertEqual(self.errors, ["sd_wrong_device"])
        self.server.state["device"] = DEVICE
        self.server.state["bad_list"] = True
        self.errors.clear(); self.scan()
        self.assertEqual(self.errors, ["sd_invalid_list"])
        self.assertEqual(self.server.state["downloads"], [])

    def test_local_collision_keeps_both_versions_and_bad_jpeg_is_rejected(self):
        first, created = store_import(self.folder.name, DEVICE, NAMES[0], JPEG, len(JPEG), headers())
        self.assertTrue(created)
        first.write_bytes(b"existing-different-content")
        other, created = store_import(self.folder.name, DEVICE, NAMES[0], JPEG, len(JPEG), headers())
        self.assertTrue(created); self.assertNotEqual(first, other)
        self.assertEqual(first.read_bytes(), b"existing-different-content")
        invalid = b"\xff\xd8garbage\xff\xd9"
        with self.assertRaises(ValueError):
            store_import(self.folder.name, DEVICE, NAMES[1], invalid, len(invalid), headers(invalid))
        with self.assertRaises(ValueError):
            store_import(self.folder.name, DEVICE, NAMES[1], JPEG, len(JPEG) + 1, headers())

    def test_dialog_selection_import_and_language_switch(self):
        dialog = SDImportDialog(Translator(), self.address, DEVICE, self.folder.name)
        dialog.show()
        try:
            until(lambda: dialog.list.count() == 3)
            dialog.list.item(1).setCheckState(Qt.CheckState.Unchecked)
            dialog.list.item(2).setCheckState(Qt.CheckState.Unchecked)
            dialog.tr.language = "en"; dialog.retranslate()
            self.assertEqual(dialog.windowTitle(), "Import photos from SD card")
            dialog._start()
            until(lambda: not dialog.importer.busy)
            self.assertEqual(self.server.state["downloads"], [NAMES[0]])
            self.assertIn("Imported 1", dialog.status.text())
        finally:
            dialog.close()

    def test_main_window_opens_import_and_recovers_connection(self):
        window = MainWindow()
        window.folder = Path(self.folder.name)
        window.address.setText(self.address)
        window.want_connection = True
        window.client.connected = True
        window.status = dict(device_id=DEVICE, sd_ok=True, sd_download_supported=True)
        window._render_controls()
        window._show_sd_import()
        dialog = window.import_dialog
        try:
            until(lambda: dialog.list.count() == 3)
            dialog._start()
            until(lambda: not dialog.importer.busy)
            self.assertEqual(window.gallery.count(),3)
            dialog.reject()
            until(lambda: window.client.connected)
            self.assertIsNone(window.import_dialog)
        finally:
            window.close()

    def test_window_close_cancels_requests_and_emits_finished(self):
        self.server.state["delay"] = .15
        dialog = SDImportDialog(Translator(), self.address, DEVICE, self.folder.name)
        results = []
        dialog.finished.connect(results.append)
        dialog.show()
        until(lambda: dialog.list.count() == 3)
        dialog._start()
        dialog.close()
        APP.processEvents()
        self.assertFalse(dialog.importer.busy)
        self.assertFalse(dialog.isVisible())
        self.assertEqual(len(results), 1)
