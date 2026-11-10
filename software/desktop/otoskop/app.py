"""Bilingual desktop workspace for the local otoscope camera."""

import argparse
import math
from pathlib import Path
import sys

from PySide6.QtCore import (QBuffer, QByteArray, QEvent, QIODevice, QSettings, QSize,
                            QStandardPaths, Qt, QTimer, QUrl, QRectF, QPointF)
from PySide6.QtGui import (QAction, QColor, QDesktopServices, QFont, QIcon,
                          QImage, QKeySequence, QPainter, QPen, QPixmap, QRadialGradient)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QButtonGroup, QCheckBox, QFileDialog,
                               QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListView,
                               QListWidget, QListWidgetItem, QMainWindow,
                               QPushButton, QScrollArea, QSizePolicy, QSlider, QStackedWidget, QStyleFactory, QToolBar,
                               QVBoxLayout, QWidget)

from . import __version__
from .client import OtoscopeClient
from .guide import ConnectionGuide
from .usb_setup import USBSetupDialog
from .i18n import Translator
from .protocol import device_urls, save_photo
from .widgets import (DARK_STYLE, STYLE, BrightnessSlider, ElidedPath, Preview, ShutterButton,
                      ToggleSwitch, card, icon, label, polish, set_pill)


class MainWindow(QMainWindow):
    def __init__(self, demo=False):
        super().__init__()
        self.settings = QSettings(QSettings.defaultFormat(), QSettings.Scope.UserScope,
                                  "GliaOtoskop", "OtoskopDesktop")
        self.tr = Translator(self.settings.value("language", "de"))
        self.bindings = []
        self.tooltips = []
        self.guide = None
        self.setup_dialog = None
        pictures = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)
        self.folder = Path(self.settings.value("folder", str(Path(pictures or str(Path.home())) / "Otoskop")))
        self.want_connection = False
        self.photo_busy = False
        self.camera_ready = False
        self.was_connected = False
        self.stream_error = False
        self.connection_stage = "offline"
        self.demo = False
        self.demo_frame = QImage()
        self.demo_phase = 0
        self.demo_brightness = 50
        self.photo_count = 0
        self.status = {}
        self.message_data = ("key", "ready_message", {}, False)
        self.client = OtoscopeClient(self)
        self.demo_timer = QTimer(self)
        self.demo_timer.setInterval(80)
        self.demo_timer.timeout.connect(self._demo_tick)
        self.resize(1240, 850)
        self.setMinimumSize(940, 700)
        self._build_ui()
        self.set_appearance(self.settings.value("appearance", "light"))
        self._connect_signals()
        self._retranslate()
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        if demo:
            self.demo_check.setChecked(True)

    def _label(self, key, name="muted", wrap=True):
        widget = label(name=name, wrap=wrap)
        self.bindings.append((widget, key))
        return widget

    def _button(self, key, symbol=None, name=None):
        widget = QPushButton()
        self.bindings.append((widget, key))
        if name:
            widget.setObjectName(name)
        if symbol:
            widget.setIcon(icon(symbol))
        return widget

    def _tooltip(self, widget, key):
        self.tooltips.append((widget, key))

    def _card_heading(self, layout, key, symbol):
        row = QHBoxLayout()
        glyph = QLabel()
        glyph.setPixmap(icon(symbol, "#9397a0", 16).pixmap(QSize(18, 18)))
        row.addWidget(glyph)
        row.addWidget(self._label(key, "section", wrap=False), 1)
        layout.addLayout(row)
        return row

    def _setup_toolbar(self):
        self.toolbar = QToolBar("Otoskop", self)
        self.toolbar.setObjectName("mainToolbar")
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(18, 18))
        self.sidebar_button = QPushButton()
        self.sidebar_button.setObjectName("ghost")
        self.sidebar_button.setIcon(icon("sidebar"))
        self.sidebar_button.setCheckable(True)
        self.sidebar_button.setChecked(True)
        self.sidebar_button.setFixedWidth(34)
        self._tooltip(self.sidebar_button, "sidebar")
        self.toolbar.addWidget(self.sidebar_button)
        self.toolbar.addWidget(label("Otoskop", "brand", wrap=False))
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.toolbar.addWidget(spacer)
        self.setup_button = self._button("usb_setup")
        self._tooltip(self.setup_button, "usb_setup_tip")
        self.toolbar.addWidget(self.setup_button)
        self.demo_check = ToggleSwitch()
        self._tooltip(self.demo_check, "demo_tip")
        self.toolbar.addWidget(self.demo_check)
        languages = QFrame()
        languages.setObjectName("languageGroup")
        language_layout = QHBoxLayout(languages)
        language_layout.setContentsMargins(2, 2, 2, 2)
        language_layout.setSpacing(0)
        self.language_group = QButtonGroup(self)
        self.language_buttons = {}
        for code, text in (("de", "DE"), ("en", "EN")):
            button = QPushButton(text)
            button.setObjectName("language")
            button.setCheckable(True)
            button.setAccessibleName("Deutsch" if code == "de" else "English")
            button.clicked.connect(lambda _checked=False, lang=code: self.set_language(lang))
            self.language_group.addButton(button)
            self.language_buttons[code] = button
            language_layout.addWidget(button)
        self.toolbar.addWidget(languages)
        appearance = QFrame()
        appearance.setObjectName("appearanceGroup")
        appearance_layout = QHBoxLayout(appearance)
        appearance_layout.setContentsMargins(2, 2, 2, 2)
        appearance_layout.setSpacing(1)
        self.appearance_group = QButtonGroup(self)
        self.appearance_buttons = {}
        for mode in ("light", "dark"):
            button = QPushButton()
            button.setObjectName("appearance")
            button.setCheckable(True)
            button.setFixedSize(30, 26)
            button.setIconSize(QSize(16, 16))
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, value=mode: self.set_appearance(value))
            self.appearance_group.addButton(button)
            self.appearance_buttons[mode] = button
            appearance_layout.addWidget(button)
        self.toolbar.addWidget(appearance)
        self.help_button = QPushButton()
        self.help_button.setObjectName("ghost")
        self.help_button.setIcon(icon("help"))
        self.help_button.setFixedWidth(34)
        self._tooltip(self.help_button, "help_tip")
        self.toolbar.addWidget(self.help_button)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        if sys.platform == "darwin" and QApplication.platformName() == "cocoa":
            self.setUnifiedTitleAndToolBarOnMac(True)

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self._setup_toolbar()

        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebarPanel")
        self.sidebar.setFixedWidth(254)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(17, 22, 17, 16)
        sidebar_layout.setSpacing(12)
        sidebar_layout.addWidget(self._label("your_device", "eyebrow", wrap=False))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sidebar_content = QWidget()
        sidebar_content.setObjectName("sidebar")
        controls = QVBoxLayout(sidebar_content)
        controls.setContentsMargins(0, 0, 3, 0)
        controls.setSpacing(14)
        connection_card, connection_layout = card()
        device_heading = QHBoxLayout()
        device_heading.setSpacing(8)
        device_icon = QLabel()
        device_icon.setPixmap(icon("camera", "#4e88d6", 19).pixmap(QSize(19, 19)))
        device_heading.addWidget(device_icon)
        device_heading.addWidget(label("Otoskop", "section", wrap=False), 1)
        self.connection = label(name="pill", wrap=False)
        self.connection.setStyleSheet("font-size: 9px; padding: 3px 5px; border-radius: 6px;")
        device_heading.addWidget(self.connection)
        connection_layout.addLayout(device_heading)
        address_label = self._label("address")
        connection_layout.addWidget(address_label)
        self.address = QLineEdit(str(self.settings.value("address", "192.168.4.1")))
        self.address.setPlaceholderText("192.168.4.1")
        address_label.setBuddy(self.address)
        connection_layout.addWidget(self.address)
        self.connect_button = self._button("connect", name="connect")
        connection_layout.addWidget(self.connect_button)
        self.connection_help = self._button("connection_help", name="link")
        connection_layout.addWidget(self.connection_help)
        controls.addWidget(connection_card)
        controls.addSpacing(5)
        controls.addWidget(self._label("settings", "eyebrow", wrap=False))
        lighting_card, lighting_layout = card()
        light_heading = self._card_heading(lighting_layout, "lighting", "sun")
        self.brightness_label = label("—", "percentage", wrap=False)
        light_heading.addWidget(self.brightness_label)
        self.brightness = BrightnessSlider(Qt.Orientation.Horizontal)
        self.brightness.setRange(0, 100)
        self.brightness.setMinimumHeight(24)
        brightness_row = QHBoxLayout()
        brightness_row.addWidget(self.brightness, 1)
        self.light_off = QPushButton()
        self.light_off.setObjectName("ghost")
        self.light_off.setIcon(icon("power", size=16))
        self.light_off.setFixedWidth(28)
        self._tooltip(self.light_off, "light_off")
        brightness_row.addWidget(self.light_off)
        lighting_layout.addLayout(brightness_row)
        self.led_note = label()
        lighting_layout.addWidget(self.led_note)
        controls.addWidget(lighting_card)
        folder_card, folder_layout = card()
        self._card_heading(folder_layout, "storage", "folder")
        self.folder_label = ElidedPath()
        self.folder_label.set_path(self.folder)
        folder_layout.addWidget(self.folder_label)
        folders = QHBoxLayout()
        folders.setSpacing(6)
        self.choose_folder = self._button("folder")
        self.open_folder = QPushButton()
        self.open_folder.setIcon(icon("arrow", size=16))
        self.open_folder.setFixedWidth(30)
        self._tooltip(self.open_folder, "open_folder")
        folders.addWidget(self.choose_folder, 1)
        folders.addWidget(self.open_folder)
        folder_layout.addLayout(folders)
        controls.addWidget(folder_card)
        controls.addStretch()
        scroll.setWidget(sidebar_content)
        sidebar_layout.addWidget(scroll, 1)
        sidebar_layout.addWidget(self._label("privacy"))
        sidebar_layout.addWidget(label(f"Otoskop  {__version__}", wrap=False))
        outer.addWidget(self.sidebar)

        workspace = QWidget()
        workspace.setObjectName("workspace")
        content = QVBoxLayout(workspace)
        content.setContentsMargins(26, 20, 26, 12)
        content.setSpacing(14)
        heading = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(self._label("live_title", "viewTitle", wrap=False))
        self.resolution = label(wrap=False)
        titles.addWidget(self.resolution)
        heading.addLayout(titles, 1)
        self.camera_badge = label(name="pill", wrap=False)
        heading.addWidget(self.camera_badge)
        self.live_button = self._button("pause", "pause", "ghost")
        self.live_button.setCheckable(True)
        self.live_button.setChecked(True)
        heading.addWidget(self.live_button)
        self.fullscreen_button = self._button("fullscreen", "expand", "ghost")
        self._tooltip(self.fullscreen_button, "fullscreen_tip")
        heading.addWidget(self.fullscreen_button)
        content.addLayout(heading)
        self.preview = Preview(self.tr)
        content.addWidget(self.preview, 1)

        capture_row = QGridLayout()
        capture_row.setContentsMargins(0, 0, 0, 0)
        capture_row.setHorizontalSpacing(8)
        self.capture_note = label()
        self.capture_note.setMaximumWidth(230)
        capture_row.addWidget(self.capture_note, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        capture_center = QWidget()
        capture_layout = QVBoxLayout(capture_center)
        capture_layout.setContentsMargins(0, 0, 0, 0)
        capture_layout.setSpacing(1)
        self.capture_button = ShutterButton()
        self._tooltip(self.capture_button, "capture_tip")
        capture_layout.addWidget(self.capture_button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.capture_label = label(name="captureLabel", wrap=False)
        self.capture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        capture_layout.addWidget(self.capture_label)
        capture_row.addWidget(capture_center, 0, 1, Qt.AlignmentFlag.AlignHCenter)
        shortcut = self._label("capture_shortcut", wrap=False)
        shortcut.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        capture_row.addWidget(shortcut, 0, 2)
        for column in range(3):
            capture_row.setColumnStretch(column, 1)
        content.addLayout(capture_row)
        line = QFrame()
        line.setObjectName("headerLine")
        line.setFixedHeight(1)
        content.addWidget(line)
        recent_header = QHBoxLayout()
        recent_header.addWidget(self._label("recent", "section", wrap=False))
        self.recent_count = label(wrap=False)
        recent_header.addWidget(self.recent_count)
        recent_header.addStretch()
        recent_header.addWidget(self._label("recent_hint", wrap=False))
        content.addLayout(recent_header)
        self.gallery_stack = QStackedWidget()
        self.gallery_stack.setFixedHeight(100)
        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(10, 8, 10, 8)
        empty_label = self._label("recent_empty")
        empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_label)
        self.gallery_stack.addWidget(empty)
        self.gallery = QListWidget()
        self.gallery.setViewMode(QListView.ViewMode.IconMode)
        self.gallery.setFlow(QListView.Flow.LeftToRight)
        self.gallery.setWrapping(False)
        self.gallery.setResizeMode(QListView.ResizeMode.Adjust)
        self.gallery.setIconSize(QSize(96, 60))
        self.gallery.setMinimumWidth(0)
        self.gallery_stack.addWidget(self.gallery)
        content.addWidget(self.gallery_stack)
        self.notice = QFrame()
        self.notice.setObjectName("notice")
        notice_layout = QHBoxLayout(self.notice)
        notice_layout.setContentsMargins(0, 8, 0, 0)
        notice_layout.setSpacing(7)
        info = QLabel()
        info.setPixmap(icon("info", "#a3a3ad", 13).pixmap(QSize(13, 13)))
        notice_layout.addWidget(info)
        self.message = label(name="message")
        self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.message.setAccessibleName("Status")
        notice_layout.addWidget(self.message, 1)
        content.addWidget(self.notice)
        outer.addWidget(workspace, 1)
        self.sidebar_button.toggled.connect(self._toggle_sidebar)
        show_sidebar = self.settings.value("sidebar_visible", True, type=bool)
        self.sidebar_button.setChecked(show_sidebar)
        self.sidebar.setVisible(show_sidebar)
        for shortcut, callback in (("F11", self._fullscreen), ("Escape", self._exit_fullscreen),
                                    ("Space", self._capture), ("Ctrl+O", self._choose_folder),
                                    ("F1", self._show_guide)):
            action = QAction(self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(callback)
            self.addAction(action)
        # Space operates a focused control; elsewhere it remains the camera
        # shortcut. This also prevents toggling Demo from accidentally capturing.
        for kind in (QAbstractButton, QLineEdit, QSlider):
            for widget in self.findChildren(kind):
                widget.installEventFilter(self)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.ShortcutOverride and event.key() == Qt.Key.Key_Space:
            event.accept()
            return True
        return super().eventFilter(watched, event)

    def _toggle_sidebar(self, visible):
        self.sidebar.setVisible(visible)
        self.settings.setValue("sidebar_visible", visible)

    def _connect_signals(self):
        self.setup_button.clicked.connect(self._show_setup)
        self.demo_check.toggled.connect(self._set_demo)
        self.help_button.clicked.connect(self._show_guide)
        self.connection_help.clicked.connect(self._show_guide)
        self.preview.setup_button.clicked.connect(self._show_setup)
        self.connect_button.clicked.connect(self._toggle_connection)
        self.address.returnPressed.connect(self._toggle_connection)
        self.live_button.toggled.connect(self._toggle_live)
        self.fullscreen_button.clicked.connect(self._fullscreen)
        self.capture_button.clicked.connect(self._capture)
        self.choose_folder.clicked.connect(self._choose_folder)
        self.open_folder.clicked.connect(self._open_folder)
        self.gallery.itemDoubleClicked.connect(self._open_photo)
        self.brightness.valueChanged.connect(self._brightness_changed)
        self.brightness.sliderReleased.connect(self._send_brightness)
        self.light_off.clicked.connect(self._light_off)
        self.client.connection_changed.connect(self._connection_changed)
        self.client.status_received.connect(self._status_received)
        self.client.frame_received.connect(self._frame_received)
        self.client.stream_interrupted.connect(self._stream_interrupted)
        self.client.problem.connect(lambda message: self._message(message, True))
        self.client.photo_received.connect(self._save_photo)
        self.client.photo_failed.connect(self._photo_failed)
        self.client.led_confirmed.connect(self._led_confirmed)

    def set_language(self, language):
        if language not in ("de", "en"):
            return
        self.tr.language = language
        self.settings.setValue("language", language)
        self._retranslate()

    def set_appearance(self, mode):
        mode = "dark" if mode == "dark" else "light"
        if self.property("appearance") == mode:
            return
        self.setProperty("appearance", mode)
        self.settings.setValue("appearance", mode)
        dark = mode == "dark"
        QApplication.styleHints().setColorScheme(Qt.ColorScheme.Dark if dark else Qt.ColorScheme.Light)
        self.setStyleSheet(STYLE + (DARK_STYLE if dark else ""))
        for value, symbol in (("light", "sun"), ("dark", "moon")):
            button = self.appearance_buttons[value]
            selected = value == mode
            color = ("#edf3ff" if selected else "#a6a6b4") if dark else (
                "#334a68" if selected else "#71717d")
            button.setChecked(selected)
            button.setIcon(icon(symbol, color, 16))

    def _retranslate(self):
        self.setWindowTitle("Otoskop")
        for widget, key in self.bindings:
            widget.setText(self.tr(key))
        for widget, key in self.tooltips:
            widget.setToolTip(self.tr(key))
        self.demo_check.setText(self.tr("demo"))
        self.language_buttons[self.tr.language].setChecked(True)
        for mode, button in self.appearance_buttons.items():
            name = self.tr("appearance_" + mode)
            button.setToolTip(name)
            button.setAccessibleName(name)
        self.address.setAccessibleName(self.tr("address"))
        self.brightness.setAccessibleName(self.tr("brightness_a11y"))
        self.gallery.setAccessibleName(self.tr("recent"))
        self.open_folder.setAccessibleName(self.tr("open_folder"))
        self.help_button.setAccessibleName(self.tr("help"))
        self.sidebar_button.setAccessibleName(self.tr("sidebar"))
        self.light_off.setAccessibleName(self.tr("light_off"))
        self.preview.retranslate()
        for index in range(self.gallery.count()):
            item = self.gallery.item(index)
            name, is_demo = item.data(Qt.ItemDataRole.UserRole + 1)
            item.setText((self.tr("demo") + " · " if is_demo else "") + name)
        self._render_controls()
        self._render_message()
        if self.demo:
            # Also translate the watermark in any subsequent saved demo photo.
            self._demo_tick(advance=False)
        elif not self.preview.image.isNull():
            self.preview.badge = self.tr("live" if self.live_button.isChecked() else "paused")
            self.preview.update()
        if self.guide is not None:
            self.guide.retranslate()
        if self.setup_dialog is not None:
            self.setup_dialog.retranslate()

    def _render_controls(self):
        self.connect_button.setText(self.tr("disconnect" if self.want_connection else "connect"))
        self.connect_button.setEnabled(not self.demo)
        self.address.setEnabled(not self.demo and not self.want_connection)
        self.live_button.setText(self.tr("pause" if self.live_button.isChecked() else "resume"))
        self.live_button.setIcon(icon("pause" if self.live_button.isChecked() else "play"))
        self.live_button.setEnabled(self.demo or self.camera_ready)
        self.capture_button.setText(self.tr("saving" if self.photo_busy else "capture"))
        self.capture_label.setText(self.capture_button.text())
        self.capture_button.setAccessibleName(self.capture_button.text())
        self.capture_button.setEnabled(not self.photo_busy and (self.demo or (self.client.connected and self.camera_ready)))
        led_available = self.demo or (self.client.connected and self.status.get("led_supported") is True)
        self.brightness.setEnabled(led_available)
        self.light_off.setEnabled(led_available)
        self.brightness_label.setText(f"{self.brightness.value()} %" if led_available else "—")
        led_note = "led_demo" if self.demo else "led_wait"
        if self.client.connected:
            led_note = "led_ready" if led_available else "led_unavailable"
        self.led_note.setText(self.tr(led_note))
        capture_note = "capture_demo" if self.demo else "capture_note"
        if self.client.connected and not self.status.get("snapshot_supported"):
            capture_note = "capture_old"
        self.capture_note.setText(self.tr(capture_note))
        if not self.demo and self.client.connected and self.status.get("snapshot_supported"):
            width, height = self.status.get("photo_width"), self.status.get("photo_height")
            if (self.status.get("high_res_photo_supported") and type(width) is int and
                    type(height) is int and width > 0 and height > 0):
                self.capture_note.setText(self.tr("capture_resolution", width=width, height=height))
            else:
                self.capture_note.setText(self.tr("capture_update"))
        if self.demo:
            set_pill(self.connection, self.tr("demo_status"), "demo")
            set_pill(self.camera_badge, self.tr("demo_status"), "demo")
        else:
            tone = "live" if self.client.connected else "warning" if self.want_connection else "offline"
            short_stage = {"offline": "offline_short", "connecting": "connecting_short",
                           "reconnecting": "reconnecting_short"}.get(self.connection_stage, self.connection_stage)
            set_pill(self.connection, self.tr(short_stage), tone)
            if not self.client.connected:
                camera_key = "offline"
            elif not self.camera_ready:
                camera_key = "unavailable_title"
            elif self.preview.image.isNull():
                camera_key = "camera_wait"
            else:
                camera_key = "live" if self.live_button.isChecked() else "paused"
            set_pill(self.camera_badge, self.tr(camera_key), tone)
        if self.preview.image.isNull():
            self.resolution.setText(self.tr("format_wait"))
        else:
            image = self.preview.image
            suffix = self.tr("demo") if self.demo else "JPEG"
            self.resolution.setText(f"{image.width()} × {image.height()} · {suffix}")
        self.recent_count.setText(self.tr("one_photo") if self.photo_count == 1 else
                                  self.tr("count", count=self.photo_count) if self.photo_count else "")
        self.gallery_stack.setCurrentIndex(1 if self.gallery.count() else 0)

    def _notify(self, key, error=False, **values):
        self.message_data = ("key", key, values, error)
        self._render_message()

    def _message(self, source, error=False):
        self.message_data = ("source", str(source), {}, error)
        self._render_message()

    def _render_message(self):
        kind, text, values, error = self.message_data
        self.message.setText(self.tr(text, **values) if kind == "key" else self.tr.source(text))
        self.notice.setProperty("error", error)
        self.message.setProperty("error", error)
        polish(self.notice)
        polish(self.message)

    def _show_guide(self):
        if self.guide is None:
            self.guide = ConnectionGuide(self.tr, self)
            self.guide.setup_requested.connect(self._setup_from_guide)
        self.guide.retranslate()
        self.guide.show()
        self.guide.raise_()
        self.guide.activateWindow()

    def _setup_from_guide(self):
        self.guide.close()
        self._show_setup()

    def _show_setup(self):
        if self.setup_dialog is None or (not self.setup_dialog.isVisible() and not self.setup_dialog.runner.busy):
            if self.setup_dialog is not None:
                self.setup_dialog.deleteLater()
            self.setup_dialog = USBSetupDialog(self.tr, self)
        self.setup_dialog.show()
        self.setup_dialog.raise_()
        self.setup_dialog.activateWindow()

    def _prepare_for_flash(self):
        if self.demo:
            self.demo_check.setChecked(False)
        self.want_connection = False
        self.client.disconnect_device()

    def _connect_after_setup(self):
        self._prepare_for_flash()
        self.address.setText("192.168.4.1")
        self._toggle_connection()

    def _toggle_connection(self):
        if self.demo:
            return
        if self.want_connection:
            self.want_connection = False
            self.client.disconnect_device()
            self._notify("disconnected_message")
        else:
            try:
                device_urls(self.address.text())
            except ValueError as exc:
                self._message(str(exc), True)
                return
            self.want_connection = True
            self.client.connect_device(self.address.text())
            self._notify("connecting_message")
        self._render_controls()

    def _connection_changed(self, connected, message):
        if self.demo:
            return
        if connected:
            self.connection_stage = "connected"
            if not self.was_connected:
                self._notify("connected_message")
                self.preview.clear("starting")
        else:
            self.camera_ready = False
            self.photo_busy = False
            self.status = {}
            if self.want_connection:
                connecting = message in ("Verbindung wird hergestellt …", "Nicht verbunden")
                self.connection_stage = "connecting" if connecting else "reconnecting"
                self.preview.clear("empty" if connecting else "lost")
                if not connecting:
                    self._message(message, True)
            else:
                self.connection_stage = "offline"
                self.preview.clear()
        self.was_connected = connected
        self._render_controls()

    def _status_received(self, status):
        if self.demo:
            return
        self.status = status
        self.camera_ready = status.get("camera_ok", False)
        enabled = status.get("led_supported") is True
        if enabled and not self.brightness.isSliderDown() and not self.client._led_busy:
            value = status.get("led_brightness", 0)
            if type(value) is int and 0 <= value <= 100:
                self._led_confirmed(value)
        if not self.camera_ready:
            self.preview.clear("unavailable")
        self._render_controls()

    def _frame_received(self, data):
        if self.demo:
            return
        image = QImage.fromData(data, "JPEG")
        if image.isNull():
            self._notify("image_error", error=True)
            return
        self.preview.set_image(image, self.tr("live"))
        if self.stream_error:
            self.stream_error = False
            self._notify("recovered_message")
        self._render_controls()

    def _stream_interrupted(self, message):
        if not self.demo and self.live_button.isChecked():
            self.stream_error = True
            self.preview.clear("stream")
            self._message(message, True)
            self._render_controls()

    def _toggle_live(self, enabled):
        if self.demo:
            self.demo_timer.start() if enabled else self.demo_timer.stop()
        else:
            self.client.set_preview(enabled)
        if not enabled:
            self.preview.badge = self.tr("demo_pause" if self.demo else "paused")
            self.preview.update()
        elif self.demo:
            self._demo_tick()
        elif self.client.connected:
            self.preview.clear("starting")
        self._render_controls()

    def _capture(self):
        if not self.capture_button.isEnabled() or self.photo_busy or self.address.hasFocus():
            return
        self.photo_busy = True
        self._render_controls()
        self._notify("capture_message")
        if self.demo:
            array = QByteArray()
            buffer = QBuffer(array)
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            self.demo_frame.save(buffer, "JPEG", 95)
            buffer.close()
            self._save_photo(bytes(array), "demo")
        else:
            self.client.capture()

    def _save_photo(self, data, _source):
        try:
            image = QImage.fromData(data, "JPEG")
            if image.isNull():
                raise ValueError(self.tr("image_error"))
            if (not self.demo and self.status.get("high_res_photo_supported") and
                    (image.width(), image.height()) != (self.status.get("photo_width"), self.status.get("photo_height"))):
                raise ValueError(self.tr("photo_resolution_error"))
            folder = self.folder / "Demo" if self.demo else self.folder
            path = save_photo(folder, data, self.demo)
        except (OSError, ValueError) as exc:
            self._finish_photo()
            self._notify("save_error", error=True, reason=self.tr.source(str(exc)))
            return
        time_label = path.stem.split("_")[2].replace("-", ":")
        item = QListWidgetItem(QIcon(QPixmap.fromImage(image)), (self.tr("demo") + " · " if self.demo else "") + time_label)
        item.setData(Qt.ItemDataRole.UserRole, str(path))
        item.setData(Qt.ItemDataRole.UserRole + 1, (time_label, self.demo))
        item.setToolTip(f"{image.width()} × {image.height()}\n{path}")
        item.setSizeHint(QSize(142, 92))
        self.gallery.insertItem(0, item)
        self.gallery.setCurrentItem(item)
        if self.gallery.count() > 100:
            self.gallery.takeItem(100)
        self.photo_count += 1
        self._finish_photo()
        self._notify("saved_demo_message" if self.demo else "saved_message", name=path.name,
                     width=image.width(), height=image.height())

    def _finish_photo(self):
        self.photo_busy = False
        self._render_controls()

    def _photo_failed(self, message):
        self._finish_photo()
        self._message(message, True)

    def _brightness_changed(self, value):
        self.brightness_label.setText(f"{value} %")
        if self.demo:
            self.demo_brightness = value
            if self.live_button.isChecked():
                self._demo_tick()
        elif not self.brightness.isSliderDown():
            self._send_brightness()

    def _send_brightness(self):
        if not self.demo and self.brightness.isEnabled():
            self.client.request_brightness(self.brightness.value())

    def _led_confirmed(self, value):
        if self.brightness.isSliderDown():
            return
        self.brightness.blockSignals(True)
        self.brightness.setValue(value)
        self.brightness.blockSignals(False)
        self.brightness_label.setText(f"{value} %")

    def _light_off(self):
        self.brightness.setValue(0)
        if not self.demo:
            self.client.request_brightness(0)

    def _choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, self.tr("folder"), str(self.folder))
        if folder:
            self.folder = Path(folder)
            self.folder_label.set_path(self.folder)
            self.settings.setValue("folder", str(self.folder))

    def _open_folder(self):
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._notify("folder_error", error=True, reason=str(exc))
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.folder))):
            self._notify("open_folder_error", error=True)

    def _open_photo(self, item):
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(item.data(Qt.ItemDataRole.UserRole))):
            self._notify("open_photo_error", error=True)

    def _set_demo(self, enabled):
        self.demo_timer.stop()
        self.client.disconnect_device()
        self.want_connection = False
        self.photo_busy = False
        self.demo = enabled
        self.camera_ready = enabled
        self.was_connected = False
        self.stream_error = False
        self.status = {}
        if enabled:
            self.brightness.setValue(self.demo_brightness)
            self._led_confirmed(self.demo_brightness)
            self._demo_tick()
            if self.live_button.isChecked():
                self.demo_timer.start()
            self._notify("demo_message")
        else:
            self.connection_stage = "offline"
            self.preview.clear()
            self._notify("demo_end_message")
        self._render_controls()

    def _demo_tick(self, advance=True):
        if advance:
            self.demo_phase += 0.025
        image = QImage(960, 720, QImage.Format.Format_RGB32)
        image.fill(QColor("#f5f7fc"))
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        glow = QRadialGradient(480, 330, 212)
        glow.setColorAt(0, QColor("#f9fbff"))
        glow.setColorAt(0.55, QColor("#e3ecfc"))
        glow.setColorAt(1, QColor("#b4cbf0"))
        painter.setBrush(glow)
        painter.setPen(QPen(QColor("#c6d6ef"), 1))
        painter.drawEllipse(QRectF(280, 130, 400, 400))
        alpha = 45 + round(self.demo_brightness * 1.4)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for radius in (65, 115, 165):
            painter.setPen(QPen(QColor(255, 255, 255, alpha), 1.6))
            painter.drawEllipse(QRectF(480-radius, 330-radius, radius*2, radius*2))
        painter.setPen(QPen(QColor("#8eacd9"), 1.2))
        painter.drawLine(468, 330, 492, 330)
        painter.drawLine(480, 318, 480, 342)
        angle = self.demo_phase
        painter.setBrush(QColor("#6e9bdf"))
        painter.setPen(QPen(QColor("#ffffff"), 2))
        x, y = 480 + math.cos(angle)*165, 330 + math.sin(angle)*165
        painter.drawEllipse(QPointF(x, y), 5, 5)
        font = QFont(self.font())
        font.setPointSize(13)
        font.setWeight(QFont.Weight.Medium)
        painter.setFont(font)
        painter.setPen(QColor("#7c8da5"))
        painter.drawText(QRectF(30, 568, 900, 35), Qt.AlignmentFlag.AlignCenter,
                         self.tr("demo_image_title"))
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.setPen(QColor("#a6afbf"))
        painter.drawText(QRectF(30, 608, 900, 30), Qt.AlignmentFlag.AlignCenter,
                         self.tr("demo_image_caption", value=self.demo_brightness))
        painter.end()
        self.demo_frame = image
        self.preview.set_image(image, self.tr("demo_badge" if self.live_button.isChecked() else "demo_pause"), demo=True)
        self._render_controls()

    def _fullscreen(self):
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    def closeEvent(self, event):
        if self.setup_dialog is not None and self.setup_dialog.runner.busy:
            self.setup_dialog.show()
            event.ignore()
            return
        try:
            device_urls(self.address.text())
        except ValueError:
            pass
        else:
            self.settings.setValue("address", self.address.text().strip())
        self.settings.setValue("folder", str(self.folder))
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("language", self.tr.language)
        self.settings.setValue("sidebar_visible", not self.sidebar.isHidden())
        if self.guide is not None:
            self.guide.close()
        if self.setup_dialog is not None:
            self.setup_dialog.close()
        self.demo_timer.stop()
        self.client.disconnect_device()
        event.accept()


def main():
    parser = argparse.ArgumentParser(description="Otoskop · Camera & lighting")
    parser.add_argument("--demo", action="store_true", help="Start with a generated test image")
    args = parser.parse_args()
    app = QApplication(sys.argv[:1])
    app.setApplicationName("Otoskop")
    app.setOrganizationName("GliaOtoskop")
    app.setApplicationVersion(__version__)
    native_mac = sys.platform == "darwin" and app.platformName() == "cocoa" and "macOS" in QStyleFactory.keys()
    app.setStyle("macOS" if native_mac else "Fusion")
    resource_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    app.setWindowIcon(QIcon(str(resource_root / "assets" / "otoskop.png")))
    window = MainWindow(demo=args.demo)
    window.show()
    return app.exec()
