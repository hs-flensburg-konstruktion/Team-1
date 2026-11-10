"""Generate the app's vector-drawn camera icon using Qt, no external assets."""
from pathlib import Path
import struct

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QLinearGradient, QRadialGradient

app = QGuiApplication([])
assets = Path(__file__).resolve().parent / "assets"
assets.mkdir(exist_ok=True)
image = QImage(1024, 1024, QImage.Format.Format_ARGB32)
image.fill(Qt.GlobalColor.transparent)
painter = QPainter(image)
painter.setRenderHint(QPainter.RenderHint.Antialiasing)
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QColor(30, 56, 100, 16))
painter.drawRoundedRect(QRectF(42, 48, 940, 936), 210, 210)
background = QLinearGradient(0, 40, 0, 984)
background.setColorAt(0, QColor("#fdfdff"))
background.setColorAt(1, QColor("#dce5f3"))
painter.setBrush(background)
painter.setPen(QPen(QColor("#d1dcec"), 2))
painter.drawRoundedRect(QRectF(40, 40, 944, 936), 210, 210)
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QColor(61, 97, 153, 22))
painter.drawRoundedRect(QRectF(182, 274, 660, 512), 110, 110)
body = QLinearGradient(0, 250, 0, 774)
body.setColorAt(0, QColor("#ffffff"))
body.setColorAt(1, QColor("#edf2fa"))
painter.setBrush(body)
painter.setPen(QPen(QColor("#d5dfef"), 2))
painter.drawRoundedRect(QRectF(182, 256, 660, 512), 110, 110)
painter.setBrush(QColor("#b6cdf2"))
painter.setPen(Qt.PenStyle.NoPen)
painter.drawEllipse(QRectF(302, 296, 420, 420))
lens = QRadialGradient(470, 430, 220)
lens.setColorAt(0, QColor("#88b8ff"))
lens.setColorAt(0.55, QColor("#4284e7"))
lens.setColorAt(1, QColor("#2155a7"))
painter.setBrush(lens)
painter.setPen(QPen(QColor("#ffffff"), 10))
painter.drawEllipse(QRectF(329, 323, 366, 366))
painter.setPen(QPen(QColor(255, 255, 255, 120), 4))
painter.setBrush(Qt.BrushStyle.NoBrush)
painter.drawEllipse(QRectF(400, 394, 224, 224))
painter.setPen(QPen(QColor("#d4e6ff"), 14, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
painter.drawArc(QRectF(422, 416, 180, 180), 20*16, 95*16)
painter.setPen(Qt.PenStyle.NoPen)
painter.setBrush(QColor("#8eafe0"))
painter.drawEllipse(QRectF(753, 304, 28, 28))
painter.end()
image.save(str(assets / "otoskop.png"))
image.scaled(256, 256).save(str(assets / "otoskop.ico"), "ICO")
# ICNS supports PNG-compressed entries; writing the container directly also
# makes icon generation reproducible on Windows, without Apple's iconutil.
entries = bytearray()
for kind, size in ((b"icp4", 16), (b"icp5", 32), (b"icp6", 64), (b"ic07", 128),
                   (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024)):
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                 Qt.TransformationMode.SmoothTransformation).save(buffer, "PNG")
    buffer.close()
    entries.extend(kind + struct.pack(">I", len(data) + 8) + bytes(data))
(assets / "otoskop.icns").write_bytes(b"icns" + struct.pack(">I", len(entries) + 8) + entries)
