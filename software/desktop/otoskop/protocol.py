"""Protocol helpers without a GUI dependency."""

from datetime import datetime
from pathlib import Path
import os
import re
from urllib.parse import urlsplit
from uuid import uuid4

MAX_JPEG = 4 * 1024 * 1024


def device_urls(address: str) -> tuple[str, str]:
    """Return the control URL and port-81 stream URL, accepting IPv6 too."""
    value = address.strip()
    if not value:
        raise ValueError("Bitte die Adresse des Otoskops eingeben.")
    if "://" not in value:
        value = "http://" + value
    try:
        url = urlsplit(value)
        port = url.port
    except ValueError as exc:
        raise ValueError("Die Geräteadresse ist ungültig.") from exc
    if (url.scheme != "http" or not url.hostname or url.username is not None
            or url.password is not None or url.path not in ("", "/")
            or url.query or url.fragment or re.search(r"[\s\\]", value)):
        raise ValueError("Bitte eine lokale HTTP-Adresse ohne Pfad eingeben, z. B. 192.168.4.1.")
    host = f"[{url.hostname}]" if ":" in url.hostname else url.hostname
    return f"http://{host}" + (f":{port}" if port is not None else ""), f"http://{host}:81/stream"


class MjpegParser:
    """Incrementally parse the firmware's length-delimited MJPEG parts.

    Both headers and images can span arbitrary network chunks. Memory is bounded
    even when a peer sends corrupt data. Boundary text inside a JPEG is harmless.
    """

    def __init__(self):
        self.buffer = bytearray()
        self.length = None

    def feed(self, chunk: bytes) -> list[bytes]:
        self.buffer.extend(chunk)
        frames = []
        while True:
            if self.length is None:
                end = self.buffer.find(b"\r\n\r\n")
                if end < 0:
                    if len(self.buffer) > 8192:
                        raise ValueError("Ungültiger Livestream: Bildkopf zu groß.")
                    break
                if end > 8192:
                    raise ValueError("Ungültiger Livestream: Bildkopf zu groß.")
                header = bytes(self.buffer[:end])
                del self.buffer[:end + 4]
                match = re.search(rb"(?im)^Content-Length:\s*([0-9]+)\s*$", header)
                if match is None:
                    raise ValueError("Livestream enthält keine Bildlänge.")
                try:
                    self.length = int(match[1])
                except ValueError as exc:
                    raise ValueError("Ungültige Bildlänge im Livestream.") from exc
                if not 4 <= self.length <= MAX_JPEG:
                    raise ValueError("Ungültige Bildgröße im Livestream.")
            if len(self.buffer) < self.length:
                break
            frame = bytes(self.buffer[:self.length])
            del self.buffer[:self.length]
            self.length = None
            if not frame.startswith(b"\xff\xd8") or not frame.endswith(b"\xff\xd9"):
                raise ValueError("Der Livestream liefert kein vollständiges JPEG.")
            frames.append(frame)
        return frames


def save_photo(folder: Path, jpeg: bytes, demo: bool = False) -> Path:
    """Create a unique file exclusively. Never truncate an existing photo."""
    if not 4 <= len(jpeg) <= MAX_JPEG or not jpeg.startswith(b"\xff\xd8") or not jpeg.endswith(b"\xff\xd9"):
        raise ValueError("Keine vollständigen JPEG-Bilddaten erhalten.")
    folder = folder.expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_%f")
    prefix = "DEMO" if demo else "Otoskop"
    for _ in range(5):
        path = folder / f"{prefix}_{stamp}_{uuid4().hex[:8]}.jpg"
        try:
            stream = path.open("xb")
        except FileExistsError:
            continue
        try:
            with stream:
                stream.write(jpeg)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            path.unlink(missing_ok=True)
            raise
        return path
    raise OSError("Kein freier Dateiname für das Foto verfügbar.")
