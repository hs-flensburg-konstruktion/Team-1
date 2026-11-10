"""Native Qt components with a restrained desktop appearance."""

from PySide6.QtCore import QPointF, QRectF, Qt, QSize, Property, QPropertyAnimation
from PySide6.QtGui import (QColor, QFont, QIcon, QImage, QLinearGradient, QPainter,
                          QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractButton, QCheckBox, QFrame, QLabel, QPushButton, QSlider,
                               QStyle, QStyleOptionSlider, QVBoxLayout, QWidget)


STYLE = """
QMainWindow, QDialog, QWidget#root { background: #fafafa; color: #252528; }
QWidget { font-size: 13px; color: #252528; }
QWidget#workspace { background: #fafafa; }
QFrame#sidebarPanel { background: #f0f0f3; border: none; border-right: 1px solid #dcdce1; }
QWidget#sidebar { background: transparent; }
QLabel { background: transparent; }
QToolBar#mainToolbar { background: #f5f5f7; border: none; border-bottom: 1px solid #dcdce1; padding: 5px 12px; spacing: 8px; }
QFrame#card { background: #ffffff; border: 1px solid #e4e4e9; border-radius: 11px; }
QFrame#cameraCard, QFrame#recentCard { background: transparent; border: none; }
QFrame#headerLine { background: #e4e4e8; border: none; max-height: 1px; }
QLabel#brand { font-size: 14px; font-weight: 600; color: #29292d; }
QLabel#viewTitle { font-size: 20px; font-weight: 600; color: #252528; }
QLabel#subtitle, QLabel#muted { color: #82828b; font-size: 11px; }
QLabel#section { color: #37373e; font-size: 12px; font-weight: 600; }
QLabel#eyebrow { color: #909099; font-size: 10px; font-weight: 600; letter-spacing: 1px; }
QLabel#pill { background: #ebebef; color: #7b7b85; border-radius: 9px; padding: 3px 8px; font-size: 10px; font-weight: 500; }
QLabel#pill[tone="live"] { background: #e7f2eb; color: #348057; }
QLabel#pill[tone="demo"] { background: #eaeffc; color: #5578b3; }
QLabel#pill[tone="warning"] { background: #fff2dc; color: #9e7a35; }
QLabel#percentage { font-size: 13px; font-weight: 500; color: #666671; }
QLabel#captureLabel { font-size: 11px; color: #6d6d78; }
QPushButton { background: #ffffff; color: #45454d; border: 1px solid #dcdce1; border-radius: 6px; min-height: 17px; padding: 6px 10px; font-weight: 400; }
QPushButton:hover { background: #f4f4f7; border-color: #c8c8d0; }
QPushButton:pressed { background: #e9e9ef; }
QPushButton:focus { border-color: #5b9cef; }
QPushButton:disabled { background: #f3f3f6; color: #b4b4bd; border-color: #e5e5e9; }
QPushButton#connect { background: #3479e7; color: #ffffff; border-color: #3479e7; font-weight: 500; }
QPushButton#connect:hover { background: #286bd7; border-color: #286bd7; }
QPushButton#connect:pressed { background: #205dc0; }
QPushButton#connect:disabled { background: #e4e5eb; color: #a6a7b1; border-color: #e4e5eb; }
QPushButton#link { border: none; background: transparent; color: #4c7eb8; text-align: left; padding: 3px 0; font-size: 11px; }
QPushButton#link:hover { color: #2362ae; }
QPushButton#ghost { background: transparent; border: 1px solid transparent; padding: 6px 8px; }
QPushButton#ghost:hover { background: #e8e8ee; border-color: #e0e0e7; }
QPushButton#ghost:checked { background: #e0e4ed; color: #3479e7; }
QPushButton#ghost:disabled { background: transparent; border-color: transparent; color: #b0b0ba; }
QPushButton#language { border: none; background: transparent; padding: 3px 8px; min-height: 17px; color: #8f8f99; font-size: 10px; font-weight: 500; }
QPushButton#language:checked, QPushButton#appearance:checked { background: #ffffff; color: #4d4d57; border-color: #dcdce3; }
QFrame#languageGroup, QFrame#appearanceGroup { background: #e8e8ee; border-radius: 7px; }
QPushButton#appearance { background: transparent; border: 1px solid transparent; border-radius: 5px; padding: 2px; }
QPushButton#appearance:hover:!checked { background: #dedee6; }
QPushButton#appearance:focus { border-color: #5b9cef; }
QPushButton#language:checked { border: 1px solid #dcdce3; border-radius: 5px; }
QLineEdit { background: #ffffff; border: 1px solid #dddde4; border-radius: 6px; padding: 7px 8px; min-height: 17px; color: #50505b; selection-background-color: #cee1ff; font-size: 12px; }
QLineEdit:focus { border: 1px solid #6fa3ed; background: #ffffff; }
QLineEdit:disabled { color: #b0b0b8; background: #f6f6f8; }
QSlider { background: transparent; }
QSlider::groove:horizontal { height: 4px; background: #d9d9e1; border: none; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #3479e7; border-radius: 2px; }
QSlider::handle:horizontal { background: white; border: 1px solid #d1d1d8; width: 15px; margin: -6px 0; border-radius: 8px; }
QCheckBox { color: #7d7d88; spacing: 7px; font-size: 11px; }
QListWidget { background: transparent; border: none; outline: none; }
QListWidget::item { border: 1px solid transparent; border-radius: 8px; padding: 4px; color: #8a8a94; font-size: 10px; }
QListWidget::item:selected { background: #e7effb; border-color: #b4cdef; color: #4677b6; }
QListWidget::item:hover { background: #eeeef3; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 5px; margin: 2px 0; }
QScrollBar::handle:vertical { background: #d0d0d8; min-height: 28px; border-radius: 2px; }
QScrollBar:horizontal { background: transparent; height: 5px; margin: 0; }
QScrollBar::handle:horizontal { background: #d0d0d8; min-width: 28px; border-radius: 2px; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; width: 0; }
QScrollBar::add-page, QScrollBar::sub-page { background: transparent; }
QFrame#notice { background: transparent; border: none; border-top: 1px solid #e5e5e9; }
QFrame#notice[error="true"] { background: #fcf2ed; border-top-color: #f0dcd1; border-radius: 5px; }
QLabel#message { color: #92929a; font-size: 11px; }
QLabel#message[error="true"] { color: #a86245; }
QFrame#helpNote { background: #eef3fb; border: 1px solid #e2e9f4; border-radius: 9px; }
QLabel#helpTitle { font-size: 24px; font-weight: 600; color: #303037; }
QLabel#stepTitle { font-size: 20px; font-weight: 600; color: #303037; }
QLabel#helpBody { font-size: 13px; color: #72727e; }
QPushButton#step { background: #ebebf0; color: #9595a0; border: none; padding: 7px; font-size: 10px; }
QPushButton#step:checked { background: #e2ebfb; color: #4c7ec3; }
QToolTip { background: #fdfdfe; color: #575761; border: 1px solid #dcdce3; border-radius: 4px; padding: 6px; }
QLabel#previewTitle { color: #4e5260; font-size: 19px; font-weight: 500; }
QLabel#previewBody { color: #747b8b; font-size: 12px; }
QLabel#keycap { background: #e9edf5; border-radius: 8px; padding: 15px 4px; font-size: 12px; font-weight: 600; }
QLabel#checkImage { background: #f0f2f7; border-radius: 10px; padding: 8px; }
QComboBox, QPlainTextEdit { background: #ffffff; border: 1px solid #dcdce3; border-radius: 7px; padding: 7px 10px; }
QComboBox QAbstractItemView { background: #ffffff; selection-background-color: #dbe9fc; }
QProgressBar { border: 1px solid #e0e3e9; border-radius: 7px; background: #edf0f6; text-align: center; color: #45546b; }
QProgressBar::chunk { background: #95b9f1; border-radius: 6px; }
"""


DARK_STYLE = """
QMainWindow, QDialog, QWidget#root, QWidget#workspace { background: #1c1c1e; color: #f2f2f7; }
QWidget { color: #f2f2f7; }
QFrame#sidebarPanel { background: #232326; border-right-color: #37373d; }
QToolBar#mainToolbar { background: #27272a; border-bottom-color: #3b3b40; }
QFrame#card { background: #2c2c2f; border-color: #3d3d43; }
QFrame#headerLine { background: #36363b; }
QLabel#brand, QLabel#viewTitle, QLabel#section, QLabel#helpTitle, QLabel#stepTitle,
QLabel#previewTitle { color: #f2f2f7; }
QLabel#subtitle, QLabel#muted, QLabel#eyebrow, QLabel#percentage,
QLabel#captureLabel, QLabel#helpBody, QLabel#message, QLabel#previewBody, QCheckBox { color: #ababb6; }
QLabel#pill { background: #38383e; color: #c5c5ce; }
QLabel#pill[tone="live"] { background: #203c31; color: #8ce1b6; }
QLabel#pill[tone="demo"] { background: #263750; color: #a8cdff; }
QLabel#pill[tone="warning"] { background: #423522; color: #f3cc88; }
QPushButton { background: #36363a; color: #e7e7ed; border-color: #494950; }
QPushButton:hover { background: #414147; border-color: #575760; }
QPushButton:pressed { background: #2e2e33; }
QPushButton:focus, QLineEdit:focus { border-color: #79b2ff; }
QPushButton:disabled { background: #303035; color: #84848f; border-color: #3b3b42; }
QPushButton#connect { background: #2471d5; color: #ffffff; border-color: #3b84e5; }
QPushButton#connect:hover { background: #2c7ae3; border-color: #5195ee; }
QPushButton#connect:pressed { background: #1e60b9; }
QPushButton#connect:disabled { background: #33353d; color: #91929e; border-color: #41434c; }
QPushButton#connect:focus { border-color: #a8cfff; }
QPushButton#link { color: #91bfff; }
QPushButton#link:hover { color: #bad8ff; }
QPushButton#ghost:hover { background: #38383d; border-color: #424249; }
QPushButton#ghost:checked { background: #343e4d; color: #a4caff; }
QPushButton#ghost:disabled { color: #82828e; }
QFrame#languageGroup, QFrame#appearanceGroup { background: #19191c; }
QPushButton#language { color: #b1b1bc; }
QPushButton#language:checked, QPushButton#appearance:checked { background: #414147; color: #f2f2f7; border-color: #55555d; }
QPushButton#appearance:hover:!checked { background: #323239; }
QPushButton#appearance:focus { border-color: #79b2ff; }
QLineEdit, QComboBox, QPlainTextEdit, QComboBox QAbstractItemView {
    background: #202023; color: #eeeef3; border-color: #494950; selection-background-color: #345d91;
}
QLineEdit:disabled { background: #28282c; color: #858590; }
QLineEdit:focus { background: #25252a; }
QListWidget::item { color: #b8b8c4; }
QListWidget::item:hover { background: #2c2c32; }
QListWidget::item:selected { background: #263a56; border-color: #426798; color: #b4d5ff; }
QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #55555e; }
QFrame#notice { border-top-color: #37373e; }
QFrame#notice[error="true"] { background: #372826; border-top-color: #63413a; }
QLabel#message[error="true"] { color: #f4b5a0; }
QFrame#helpNote { background: #233046; border-color: #344a66; }
QPushButton#step, QLabel#keycap, QLabel#checkImage { background: #34343a; color: #c1c1cc; }
QPushButton#step:checked { background: #2d4463; color: #b0d2ff; }
QProgressBar { background: #24262c; border-color: #454854; color: #f2f2f7; }
QProgressBar::chunk { background: #3b659c; }
QToolTip { background: #333339; color: #eeeef3; border-color: #53535c; }
"""


def dark_appearance(widget):
    return widget.window().property("appearance") == "dark"


def label(text="", name="muted", wrap=True):
    widget = QLabel(text)
    widget.setObjectName(name)
    widget.setWordWrap(wrap)
    return widget


def polish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)
    widget.update()


def set_pill(widget, text, tone="offline"):
    if widget.text() == text and widget.property("tone") == tone:
        return
    widget.setText(text)
    widget.setProperty("tone", tone)
    polish(widget)


def icon(name, color="#80808b", size=18):
    """24-unit outline symbols, equally legible without platform icon fonts."""
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size * 2 / 24, size * 2 / 24)
    painter.setPen(QPen(QColor(color), 1.5, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if name == "camera":
        path = QPainterPath()
        path.moveTo(4, 6); path.lineTo(8, 6); path.lineTo(10, 3.5)
        path.lineTo(15, 3.5); path.lineTo(17, 6); path.lineTo(20, 6)
        path.quadTo(22, 6, 22, 8); path.lineTo(22, 19)
        path.quadTo(22, 21, 20, 21); path.lineTo(4, 21)
        path.quadTo(2, 21, 2, 19); path.lineTo(2, 8); path.quadTo(2, 6, 4, 6)
        painter.drawPath(path); painter.drawEllipse(QRectF(8, 9, 8, 8))
    elif name == "wifi":
        for box in (QRectF(1, 3, 22, 22), QRectF(5, 7, 14, 14), QRectF(9, 11, 6, 6)):
            painter.drawArc(box, 42*16, 96*16)
        painter.drawPoint(QPointF(12, 19))
    elif name == "folder":
        path = QPainterPath(); path.moveTo(3, 6); path.lineTo(9, 6); path.lineTo(11, 8)
        path.lineTo(21, 8); path.lineTo(21, 20); path.lineTo(3, 20); path.closeSubpath()
        painter.drawPath(path)
    elif name == "sidebar":
        painter.drawRoundedRect(QRectF(3, 4, 18, 16), 2, 2)
        painter.drawLine(9, 4, 9, 20)
        painter.drawLine(5, 8, 7, 8); painter.drawLine(5, 11, 7, 11)
    elif name == "help":
        painter.drawEllipse(QRectF(3, 3, 18, 18))
        path = QPainterPath(); path.moveTo(9, 9)
        path.cubicTo(9, 5.5, 16, 6, 15, 10)
        path.cubicTo(14.5, 12, 12, 11.5, 12, 14)
        painter.drawPath(path); painter.drawPoint(QPointF(12, 17))
    elif name == "pause":
        painter.drawLine(9, 5, 9, 19); painter.drawLine(15, 5, 15, 19)
    elif name == "play":
        path = QPainterPath(); path.moveTo(8, 5); path.lineTo(19, 12)
        path.lineTo(8, 19); path.closeSubpath(); painter.drawPath(path)
    elif name == "expand":
        for points in (((3,9),(3,3),(9,3)), ((15,3),(21,3),(21,9)),
                       ((21,15),(21,21),(15,21)), ((9,21),(3,21),(3,15))):
            path = QPainterPath(QPointF(*points[0]))
            for point in points[1:]: path.lineTo(QPointF(*point))
            painter.drawPath(path)
    elif name == "power":
        painter.drawArc(QRectF(4, 4, 16, 16), 130*16, 280*16); painter.drawLine(12, 2, 12, 11)
    elif name == "sun":
        painter.drawEllipse(QRectF(8, 8, 8, 8))
        for a,b in (((12,2),(12,4)), ((12,20),(12,22)), ((2,12),(4,12)), ((20,12),(22,12)),
                    ((5,5),(6,6)), ((18,18),(19,19)), ((5,19),(6,18)), ((18,6),(19,5))):
            painter.drawLine(*a,*b)
    elif name == "moon":
        path = QPainterPath(QPointF(13.2, 3.2))
        path.cubicTo(7.9, 2.6, 3.5, 6.7, 3.5, 12)
        path.cubicTo(3.5, 17, 7.5, 21, 12.5, 21)
        path.cubicTo(16.2, 21, 19.5, 18.8, 20.8, 15.4)
        path.cubicTo(15.7, 16.7, 10.8, 13, 10.8, 8.3)
        path.cubicTo(10.8, 6.3, 11.7, 4.5, 13.2, 3.2)
        path.closeSubpath()
        painter.drawPath(path)
    elif name == "arrow":
        painter.drawLine(5,12,19,12); painter.drawLine(14,7,19,12); painter.drawLine(14,17,19,12)
    else:
        painter.drawEllipse(QRectF(3,3,18,18)); painter.drawPoint(QPointF(12,7)); painter.drawLine(12,11,12,17)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return QIcon(pixmap)


def card():
    widget = QFrame(); widget.setObjectName("card")
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(10)
    return widget, layout


class ElidedPath(QLabel):
    def __init__(self):
        super().__init__(); self.path = ""; self.setObjectName("muted"); self.setMinimumWidth(0)

    def set_path(self, path):
        self.path = str(path); self.setToolTip(self.path); self.setAccessibleName(self.path); self._update()

    def _update(self):
        self.setText(self.fontMetrics().elidedText(self.path, Qt.TextElideMode.ElideMiddle, self.width()))

    def resizeEvent(self, event):
        self._update(); super().resizeEvent(event)


class BrightnessSlider(QSlider):
    def paintEvent(self, _event):
        option = QStyleOptionSlider(); self.initStyleOption(option)
        handle = self.style().subControlRect(QStyle.ComplexControl.CC_Slider, option,
                                             QStyle.SubControl.SC_SliderHandle, self)
        center = handle.center(); y = self.height()/2
        dark = dark_appearance(self)
        track, accent, disabled = ("#474750", "#5ca2ff", "#62626d") if dark else (
            "#d9d9e0", "#3479e7", "#c4c4cd")
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(track), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(handle.width()/2, y), QPointF(self.width()-handle.width()/2, y))
        painter.setPen(QPen(QColor(accent if self.isEnabled() else disabled), 3,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(handle.width()/2,y), QPointF(center.x(),y))
        thumb = ("#e6e6ed" if self.isEnabled() else "#777783") if dark else "#ffffff"
        painter.setBrush(QColor(thumb)); painter.setPen(QPen(QColor("#565662" if dark else "#ccccd4"),0.8))
        painter.drawEllipse(QPointF(center.x(),y+0.8),8,8)
        painter.drawEllipse(QPointF(center.x(),y),7.5,7.5)
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(QColor("#b3d0fc"),1.3))
            painter.drawEllipse(QPointF(center.x(),y),10,10)


class ToggleSwitch(QCheckBox):
    """A switch that retains QCheckBox signals, focus and accessibility."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._position = 0.0
        self.animation = QPropertyAnimation(self,b"position",self)
        self.animation.setDuration(140)
        self.toggled.connect(self._animate)
        self.setMinimumHeight(30)

    def sizeHint(self):
        return QSize(46+self.fontMetrics().horizontalAdvance(self.text()),30)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def get_position(self): return self._position
    def set_position(self, value): self._position=value; self.update()
    position = Property(float,get_position,set_position)

    def _animate(self, checked):
        self.animation.stop(); self.animation.setStartValue(self._position)
        self.animation.setEndValue(1.0 if checked else 0.0); self.animation.start()

    def paintEvent(self,_event):
        painter=QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        x,y=1,(self.height()-19)/2
        dark = dark_appearance(self)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#3479e7" if self.isChecked() else ("#51515c" if dark else "#d4d4dc")))
        painter.drawRoundedRect(QRectF(x,y,32,19),9.5,9.5)
        painter.setBrush(QColor(0,0,0,18)); painter.drawEllipse(QRectF(x+2+self._position*13,y+2.5,15,15))
        painter.setBrush(QColor("#ffffff")); painter.drawEllipse(QRectF(x+2+self._position*13,y+2,15,15))
        painter.setPen(QColor("#b9b9c4" if dark else "#85858e"))
        painter.drawText(self.rect().adjusted(41,0,0,0),Qt.AlignmentFlag.AlignVCenter,self.text())
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(QColor("#a9c9fb"),1.5))
            painter.drawRoundedRect(QRectF(x-0.5,y-1.5,35,22),11,11)


class ShutterButton(QAbstractButton):
    """Camera-style capture button; the text remains available to assistive tools."""
    def __init__(self):
        super().__init__()
        self.setFixedSize(64,64)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        return QSize(64, 64)

    def paintEvent(self,_event):
        painter=QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        dark = dark_appearance(self)
        active, disabled = ("#5ca2ff", "#51515d") if dark else ("#3479e7", "#d4d8e0")
        color = QColor(active if self.isEnabled() else disabled)
        painter.setPen(QPen(color,1.5)); painter.setBrush(QColor("#26262d" if dark else "#ffffff"))
        painter.drawEllipse(QRectF(5,5,54,54))
        if self.isDown(): color=color.darker(112)
        elif self.underMouse() and self.isEnabled(): color=color.lighter(108)
        painter.setBrush(color); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(10,10,44,44))
        if self.hasFocus():
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.setPen(QPen(QColor("#a7c9fa"),1.5))
            painter.drawEllipse(QRectF(1.5,1.5,61,61))


class Preview(QWidget):
    def __init__(self,tr):
        super().__init__(); self.tr=tr; self.image=QImage(); self.badge=""; self.empty_state="empty"; self.demo_mode=False
        self.setMinimumSize(430,230)
        layout=QVBoxLayout(self); layout.setContentsMargins(35,25,35,25); layout.addStretch()
        self.empty=QWidget(); inner=QVBoxLayout(self.empty); inner.setSpacing(13)
        glyph=QLabel(); glyph.setPixmap(icon("camera","#a9b1bf",54).pixmap(QSize(54,54)))
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter); inner.addWidget(glyph)
        self.empty_title=label(name="previewTitle"); self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(self.empty_title)
        self.empty_body=label(name="previewBody"); self.empty_body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(self.empty_body)
        self.setup_button=QPushButton(); self.setup_button.setObjectName("connect")
        inner.addWidget(self.setup_button,0,Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty); layout.addStretch(); self.retranslate()

    def retranslate(self):
        self.setAccessibleName(self.tr("live_title")); self.setup_button.setText(self.tr("setup_cta"))
        self.empty_title.setText(self.tr(self.empty_state+"_title")); self.empty_body.setText(self.tr(self.empty_state+"_body")); self.update()

    def set_image(self,image,badge="",demo=False):
        self.image,self.badge,self.demo_mode=image,badge,demo; self.empty.hide(); self.update()

    def clear(self,state="empty"):
        self.image=QImage(); self.empty_state=state; self.badge=""; self.demo_mode=False
        self.empty.show(); self.retranslate()

    def paintEvent(self,_event):
        painter=QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area=QRectF(self.rect()).adjusted(0.5,0.5,-0.5,-0.5)
        dark = dark_appearance(self)
        start, end, edge = ("#282932", "#202129", "#3a3c48") if dark else (
            "#fbfcfe", "#edf0f6", "#e1e4eb")
        gradient=QLinearGradient(0,0,self.width(),self.height())
        gradient.setColorAt(0,QColor(start)); gradient.setColorAt(1,QColor(end))
        painter.setBrush(gradient if self.image.isNull() else QColor("#f5f7fc" if self.demo_mode and not dark else "#18191d"))
        painter.setPen(QPen(QColor(edge),1)); painter.drawRoundedRect(area,16,16)
        clip=QPainterPath(); clip.addRoundedRect(area,16,16); painter.setClipPath(clip)
        if not self.image.isNull():
            size=self.image.size().scaled(self.size(),Qt.AspectRatioMode.KeepAspectRatio)
            target=QRectF(0,0,size.width(),size.height()); target.moveCenter(area.center())
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform); painter.drawImage(target,self.image)
        if self.badge:
            font=QFont(self.font()); font.setPointSize(9); font.setWeight(QFont.Weight.Medium); painter.setFont(font)
            width=painter.fontMetrics().horizontalAdvance(self.badge)+24
            light_badge = self.demo_mode and not dark
            painter.setBrush(QColor(255,255,255,215) if light_badge else QColor(30,31,37,215))
            painter.setPen(Qt.PenStyle.NoPen); painter.drawRoundedRect(QRectF(16,16,width,25),8,8)
            painter.setPen(QColor("#657084" if light_badge else "#d6d9df"))
            painter.drawText(QRectF(16,16,width,25),Qt.AlignmentFlag.AlignCenter,self.badge)
