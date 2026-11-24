"""Read-only SD import with bounded downloads and verified, exclusive saves."""
import hashlib
import json
import os
from pathlib import Path
import re

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QProgressBar, QPushButton, QVBoxLayout)

from .client import OtoscopeClient
from .protocol import MAX_JPEG, device_urls

PHOTO_NAME = re.compile(r"IMG_([0-9]{10})\.jpg\Z")


def photo_number(name):
    match = PHOTO_NAME.fullmatch(name) if isinstance(name, str) else None
    if not match or not 1 <= int(match[1]) <= 0xFFFFFFFF:
        raise ValueError("sd_invalid_list")
    return int(match[1])


def store_import(folder, device_id, name, data, expected_size, headers):
    photo_number(name)
    digest = hashlib.sha256(data).hexdigest()
    if (len(data) != expected_size or not 4 <= len(data) <= MAX_JPEG
            or headers.get(b"x-photo-sha256") != digest.encode("ascii")
            or headers.get(b"x-photo-bytes") != str(expected_size).encode("ascii")
            or headers.get(b"x-device-id") != device_id.encode("ascii")
            or headers.get(b"content-type", b"").split(b";", 1)[0] != b"image/jpeg"
            or not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9")
            or QImage.fromData(data, "JPEG").isNull()):
        raise ValueError("sd_invalid_photo")
    device = device_id.replace(":", "")
    if not re.fullmatch(r"[0-9a-fA-F]{12}", device):
        raise ValueError("sd_wrong_device")
    target = Path(folder) / "SD-Import" / device.lower()
    target.mkdir(parents=True, exist_ok=True)
    for candidate in (target / name, target / f"{Path(name).stem}_{digest}.jpg"):
        try:
            stream = candidate.open("xb")
        except FileExistsError:
            # A second import skips an identical local original. If a card was
            # replaced/reset, differing content gets its own name instead.
            if candidate.stat().st_size == len(data) and hashlib.sha256(candidate.read_bytes()).hexdigest() == digest:
                return candidate, False
            continue
        try:
            with stream:
                if stream.write(data) != len(data):
                    raise OSError("Short write")
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            candidate.unlink(missing_ok=True)
            raise
        return candidate, True
    raise OSError("No free import filename")


class SDImporter(QObject):
    photos_ready = Signal(list)
    progress = Signal(int, int, str)
    saved = Signal(str, bool)
    failed = Signal(str)
    finished = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.client = OtoscopeClient(self)
        self.busy = False
        self.photos = []
        self.device_id = ""
        self.created = self.skipped = 0

    def cancel(self):
        self.busy = False
        self.client.disconnect_device()

    def _fail(self, message):
        self.busy = False
        self.failed.emit(str(message))

    def scan(self, address, device_id):
        self.cancel()
        self.device_id = device_id
        self.client.base_url, _ = device_urls(address)
        self.busy = True
        self.photos = []

        def status_received(data):
            try:
                status = json.loads(data)
                if status.get("device_id") != self.device_id:
                    raise ValueError("sd_wrong_device")
                if status.get("sd_download_supported") is not True:
                    raise ValueError("sd_unsupported")
                if status.get("sd_ok") is not True:
                    raise ValueError("sd_not_ready")
            except (ValueError, AttributeError) as error:
                self._fail(str(error) if str(error).startswith("sd_") else "sd_invalid_list")
                return
            self._page(0)

        self.client._fetch("/status", status_received, self._fail)

    def _page(self, after):
        def received(data):
            try:
                page = json.loads(data)
                entries, next_after = page["photos"], page["next_after"]
                if not isinstance(entries, list) or len(entries) > 50:
                    raise ValueError()
                previous = after
                for entry in entries:
                    number = photo_number(entry["name"])
                    if number <= previous or type(entry["bytes"]) is not int or entry["bytes"] < 0:
                        raise ValueError()
                    previous = number
                if next_after is not None and (type(next_after) is not int or not entries or next_after != previous):
                    raise ValueError()
                if len(self.photos) + len(entries) > 100000:
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                self._fail("sd_invalid_list")
                return
            self.photos.extend(entries)
            if next_after is not None:
                self._page(next_after)
            else:
                self.busy = False
                self.photos_ready.emit(self.photos)

        self.client._fetch(f"/photos?after={after}", received, self._fail, timeout=60000)

    def start(self, photos, folder):
        if self.busy or not photos:
            return
        # Only entries returned by the validated listing can be requested.
        if any(photo not in self.photos or not 4 <= photo["bytes"] <= MAX_JPEG for photo in photos):
            self._fail("sd_invalid_list")
            return
        self.queue, self.folder = list(photos), Path(folder)
        self.index = self.created = self.skipped = 0
        self.busy = True
        self._next()

    def _next(self):
        if not self.busy:
            return
        if self.index == len(self.queue):
            self.busy = False
            self.finished.emit(self.created, self.skipped)
            return
        photo = self.queue[self.index]
        self.progress.emit(self.index, len(self.queue), photo["name"])

        def received(data, headers):
            try:
                path, created = store_import(self.folder, self.device_id, photo["name"], data, photo["bytes"], headers)
            except ValueError as error:
                self._fail(str(error))
                return
            except OSError:
                self._fail("sd_write_error")
                return
            self.created += int(created)
            self.skipped += int(not created)
            self.saved.emit(str(path), created)
            self.index += 1
            self._next()

        self.client._fetch("/photo?name=" + photo["name"], received, self._fail,
                           limit=MAX_JPEG, timeout=60000, headers=True)


class SDImportDialog(QDialog):
    def __init__(self, tr, address, device_id, folder, parent=None):
        super().__init__(parent)
        self.tr, self.address, self.device_id, self.folder = tr, address, device_id, Path(folder)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(640, 560)
        self.importer = SDImporter(self)
        self.message_key, self.message_args = "sd_loading", {}
        self.message_source = None
        root = QVBoxLayout(self)
        self.intro = QLabel()
        self.intro.setWordWrap(True)
        root.addWidget(self.intro)
        self.list = QListWidget()
        self.list.itemChanged.connect(self._selection_changed)
        root.addWidget(self.list, 1)
        self.status = QLabel()
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        root.addWidget(self.progress)
        row = QHBoxLayout()
        self.select_all = QPushButton()
        self.select_all.clicked.connect(self._select_all)
        row.addWidget(self.select_all)
        self.refresh = QPushButton()
        self.refresh.clicked.connect(self._scan)
        row.addWidget(self.refresh)
        row.addStretch()
        self.import_button = QPushButton()
        self.import_button.setObjectName("connect")
        self.import_button.clicked.connect(self._start)
        row.addWidget(self.import_button)
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.reject)
        row.addWidget(self.close_button)
        root.addLayout(row)
        self.importer.photos_ready.connect(self._loaded)
        self.importer.progress.connect(self._progress)
        self.importer.failed.connect(self._failed)
        self.importer.finished.connect(self._finished)
        self.retranslate()
        self._scan()

    def _message(self, key, **values):
        self.message_key, self.message_args, self.message_source = key, values, None
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(self.tr("sd_title"))
        self.intro.setText(self.tr("sd_intro", folder=str(self.folder / "SD-Import")))
        for widget, key in ((self.select_all, "sd_select_all"), (self.refresh, "sd_refresh"),
                            (self.import_button, "sd_import_selected"), (self.close_button, "sd_cancel" if self.importer.busy else "usb_close")):
            widget.setText(self.tr(key))
        self.status.setText(self.tr.source(self.message_source) if self.message_source else self.tr(self.message_key, **self.message_args))
        self.list.setEnabled(not self.importer.busy)
        self.refresh.setEnabled(not self.importer.busy)
        self.select_all.setEnabled(not self.importer.busy and bool(self.list.count()))
        self._selection_changed()

    def _selection_changed(self, *_):
        selected = any(self.list.item(i).checkState() == Qt.CheckState.Checked for i in range(self.list.count()))
        self.import_button.setEnabled(not self.importer.busy and selected)

    def _select_all(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)

    def _scan(self):
        self.list.clear()
        self.progress.setRange(0, 0)
        self.importer.scan(self.address, self.device_id)
        self._message("sd_loading")

    def _loaded(self, photos):
        for photo in photos:
            item = QListWidgetItem(f'{photo["name"]}  ·  {photo["bytes"] / 1024:.0f} KB')
            item.setData(Qt.ItemDataRole.UserRole, photo)
            if 4 <= photo["bytes"] <= MAX_JPEG:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                item.setToolTip(self.tr("sd_invalid_photo"))
            self.list.addItem(item)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self._message("sd_found", count=len(photos))

    def _start(self):
        photos = [self.list.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.list.count())
                  if self.list.item(i).checkState() == Qt.CheckState.Checked]
        self.importer.start(photos, self.folder)
        self.retranslate()

    def _progress(self, done, total, name):
        self.progress.setRange(0, total)
        self.progress.setValue(done)
        self._message("sd_progress", current=done + 1, total=total, name=name)

    def _failed(self, message):
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        from .i18n import TEXT
        if message in TEXT:
            self._message(message)
        else:
            self.message_source = message
            self.retranslate()

    def _finished(self, created, skipped):
        self.progress.setValue(self.progress.maximum())
        self._message("sd_complete", count=created, skipped=skipped)

    def reject(self):
        if self.importer.busy:
            self.importer.cancel()
            self.progress.setRange(0, 1)
            self.progress.setValue(0)
            self._message("sd_cancelled")
        else:
            super().reject()

    def closeEvent(self, event):
        self.importer.cancel()
        super().closeEvent(event)
