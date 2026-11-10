"""Asynchronous Qt HTTP client. All callbacks run on the GUI event loop."""

import json
import time

from PySide6.QtCore import QObject, QTimer, QUrl, Signal
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkProxy, QNetworkReply, QNetworkRequest

from .protocol import MAX_JPEG, MjpegParser, device_urls


class OtoscopeClient(QObject):
    status_received = Signal(dict)
    frame_received = Signal(bytes)
    stream_interrupted = Signal(str)
    connection_changed = Signal(bool, str)
    problem = Signal(str)
    photo_received = Signal(bytes, str)
    photo_failed = Signal(str)
    led_confirmed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.network = QNetworkAccessManager(self)
        self.network.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
        self.poll = QTimer(self)
        self.poll.setInterval(3000)
        self.poll.timeout.connect(self._poll_status)
        self.retry = QTimer(self)
        self.retry.setSingleShot(True)
        self.retry.setInterval(2000)
        self.retry.timeout.connect(self._start_stream)
        self.watchdog = QTimer(self)
        self.watchdog.setInterval(1000)
        self.watchdog.timeout.connect(self._check_stream)
        self.heartbeat = QTimer(self)
        self.heartbeat.setInterval(3000)
        self.heartbeat.timeout.connect(self._refresh_led)
        self._generation = 0
        self._replies = set()
        self._stream_reply = None
        self._status_busy = False
        self._photo_busy = False
        self._led_busy = False
        self._wanted = False
        self.connected = False
        self.preview_enabled = True
        self.status = {}
        self.last_frame = b""
        self.last_frame_at = 0.0
        self._led_desired = 0
        self._send_zero = True

    def connect_device(self, address):
        base, stream = device_urls(address)
        self.disconnect_device()
        self.base_url, self.stream_url = base, stream
        self._wanted = True
        self.connection_changed.emit(False, "Verbindung wird hergestellt …")
        self.poll.start()
        self.heartbeat.start()
        self._poll_status()

    def disconnect_device(self):
        # Best effort only; firmware also switches LEDs off after 10 s without
        # a brightness command. This reply is deliberately outside _replies.
        if self._wanted and self.connected and self.status.get("led_supported"):
            off = self.network.post(self._request("/led?brightness=0"), b"")
            off.finished.connect(off.deleteLater)
        self._generation += 1
        self._wanted = False
        for timer in (self.poll, self.retry, self.watchdog, self.heartbeat):
            timer.stop()
        self._stop_stream()
        for reply in list(self._replies):
            reply.abort()
        self._replies.clear()
        self._status_busy = self._photo_busy = self._led_busy = False
        self.connected = False
        self.status = {}
        self.last_frame = b""
        self.last_frame_at = 0
        self._led_desired = 0
        self._send_zero = True
        self.connection_changed.emit(False, "Nicht verbunden")

    def _request(self, path, timeout=4500):
        request = QNetworkRequest(QUrl(self.base_url + path))
        request.setTransferTimeout(timeout)
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        request.setRawHeader(b"Cache-Control", b"no-cache")
        request.setHeader(QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/x-www-form-urlencoded")
        return request

    def _fetch(self, path, callback, failure, *, post=False, limit=65536, timeout=4500):
        generation = self._generation
        request = self._request(path, timeout)
        reply = self.network.post(request, b"") if post else self.network.get(request)
        self._replies.add(reply)
        data = bytearray()
        too_large = False

        def read():
            nonlocal too_large
            if too_large:
                return
            data.extend(bytes(reply.readAll()))
            if len(data) > limit:
                too_large = True
                data.clear()
                reply.abort()

        def finished():
            self._replies.discard(reply)
            if generation != self._generation:
                reply.deleteLater()
                return
            read()
            code = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
            error = reply.error()
            reply.deleteLater()
            if too_large:
                failure("Die Antwort des Otoskops ist zu groß.")
            elif code is not None and not 200 <= int(code) < 300:
                try:
                    message = json.loads(data).get("error", "")
                except (ValueError, AttributeError):
                    message = ""
                failure(message or f"Das Otoskop meldet HTTP {code}.")
            elif error != QNetworkReply.NetworkError.NoError:
                failure("Otoskop nicht erreichbar. WLAN-Verbindung und Geräteadresse prüfen.")
            else:
                callback(bytes(data))

        reply.readyRead.connect(read)
        reply.finished.connect(finished)

    def _poll_status(self):
        if self._wanted and not self._status_busy and not self._photo_busy:
            self._status_busy = True
            self._fetch("/status", self._on_status, self._status_failed)

    def _on_status(self, data):
        self._status_busy = False
        try:
            status = json.loads(data)
            if not isinstance(status, dict) or not isinstance(status.get("camera_ok"), bool):
                raise ValueError()
        except (ValueError, TypeError):
            self._status_failed("Die Adresse liefert keinen gültigen Otoskop-Status.")
            return
        self.status = status
        self.connected = True
        self.connection_changed.emit(True, "Verbunden · lokales WLAN")
        self.status_received.emit(status)
        if status["camera_ok"] and status.get("stream_ok", True):
            if self.preview_enabled and self._stream_reply is None and not self.retry.isActive():
                self._start_stream()
        else:
            self._stop_stream()
            self.problem.emit(str(status.get("camera" if not status["camera_ok"] else "stream", "Kamera nicht bereit.")))

    def _status_failed(self, message):
        self._status_busy = False
        if self._photo_busy:
            return  # A pending control request can wait behind the camera switch.
        self.connected = False
        self.last_frame = b""
        self._stop_stream()
        self.retry.stop()
        self._led_desired = 0
        self.connection_changed.emit(False, message + " Erneuter Versuch läuft automatisch.")

    def set_preview(self, enabled):
        self.preview_enabled = enabled
        if enabled:
            self._start_stream()
        else:
            self.retry.stop()
            self._stop_stream()

    def _stop_stream(self):
        self.watchdog.stop()
        reply, self._stream_reply = self._stream_reply, None
        if reply is not None:
            reply.abort()

    def _start_stream(self):
        if (not self._wanted or not self.connected or not self.preview_enabled
                or self._photo_busy
                or not self.status.get("camera_ok") or not self.status.get("stream_ok", True)
                or self._stream_reply is not None):
            return
        request = QNetworkRequest(QUrl(self.stream_url))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        reply = self.network.get(request)
        reply.setReadBufferSize(128 * 1024)
        self._stream_reply = reply
        parser = MjpegParser()
        last_received = time.monotonic()
        failure_message = ""
        self.watchdog.start()

        def read():
            nonlocal last_received, failure_message
            if self._stream_reply is not reply:
                return
            try:
                while reply.bytesAvailable() > 0:
                    frames = parser.feed(bytes(reply.read(65536)))
                    if frames:
                        last_received = time.monotonic()
                        self.last_frame_at = last_received
                        self.last_frame = frames[-1]
                        self.frame_received.emit(frames[-1])
            except ValueError as exc:
                failure_message = str(exc)
                reply.abort()

        def finished():
            if self._stream_reply is reply:
                self._stream_reply = None
                self.watchdog.stop()
                if self._wanted and self.preview_enabled and self.connected:
                    self.stream_interrupted.emit(failure_message or "Livebild unterbrochen. Verbindung wird erneut aufgebaut …")
                    self.retry.start()
            reply.deleteLater()

        self._stream_last_received = lambda: last_received
        reply.readyRead.connect(read)
        reply.finished.connect(finished)

    def _check_stream(self):
        if self._stream_reply is not None and time.monotonic() - self._stream_last_received() > 8:
            self._stream_reply.abort()

    def capture(self):
        if self._photo_busy:
            return
        if not self.connected or not self.status.get("camera_ok"):
            self.photo_failed.emit("Keine Kamera verbunden.")
            return
        if not self.status.get("snapshot_supported", False):
            if self.last_frame and time.monotonic() - self.last_frame_at < 2.5 and self.preview_enabled:
                self.photo_received.emit(self.last_frame, "Foto aus Livebild · ältere Firmware")
            else:
                self.photo_failed.emit("Für ein neues Foto das Livebild starten oder die Firmware aktualisieren.")
            return
        self._photo_busy = True
        self.retry.stop()
        self._stop_stream()

        def resume():
            self._photo_busy = False
            self._start_stream()  # Respects the user's paused-preview setting.
            self._refresh_led()

        def success(data):
            resume()
            self.photo_received.emit(data, "Neue Kameraaufnahme")

        def failure(message):
            resume()
            self.photo_failed.emit(message)

        self._fetch("/snapshot", success, failure, post=True, limit=MAX_JPEG, timeout=40000)

    def set_brightness(self, value):
        if not self.connected or not self.status.get("led_supported"):
            return
        self._led_desired = max(0, min(100, int(value)))
        self._refresh_led()

    def _refresh_led(self):
        if (not self._wanted or not self.connected or not self.status.get("led_supported")
                or self._led_busy or self._photo_busy):
            return
        # Zero is sent once on request; positive values keep the firmware lease alive.
        if self._led_desired == 0 and not getattr(self, "_send_zero", True):
            return
        self._send_zero = False
        self._led_busy = True
        value = self._led_desired

        def success(data):
            self._led_busy = False
            try:
                brightness = json.loads(data)["led_brightness"]
                if type(brightness) is not int or not 0 <= brightness <= 100:
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                self._led_desired = 0
                self.problem.emit("Ungültige Bestätigung der LED-Helligkeit.")
                return
            self.led_confirmed.emit(brightness)
            if self._led_desired != value:
                self._send_zero = True
                self._refresh_led()

        def failure(message):
            self._led_busy = False
            if self._photo_busy:
                self._send_zero = True
                return
            self._led_desired = 0
            self.problem.emit("LED-Steuerung: " + message)
            self.led_confirmed.emit(0)

        self._fetch(f"/led?brightness={value}", success, failure, post=True)

    def request_brightness(self, value):
        self._send_zero = True
        self.set_brightness(value)
