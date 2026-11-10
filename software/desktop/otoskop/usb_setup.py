"""Guided USB installation, bootloader help, and honest post-flash checks."""

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QFrame, QHBoxLayout,
                               QLabel, QPlainTextEdit, QProgressBar, QPushButton, QScrollArea,
                               QStackedWidget, QVBoxLayout, QWidget)

from .client import OtoscopeClient
from .firmware_bundle import InstallError, load_bundle, supported_ports
from .flash_process import FlashProcess
from .i18n import TEXT
from .widgets import STYLE, card, icon, label, set_pill


class BootHelp(QDialog):
    def __init__(self, tr, parent=None):
        super().__init__(parent)
        self.tr, self.bindings = tr, []
        self.setWindowModality(Qt.WindowModality.WindowModal)
        if parent is None:
            self.setStyleSheet(STYLE)
        self.resize(690, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(26, 24, 26, 22)
        root.setSpacing(18)
        for key, name in (("usb_boot_title", "helpTitle"), ("usb_boot_body", "helpBody")):
            text = label(name=name)
            self.bindings.append((text, key))
            root.addWidget(text)
        steps = QHBoxLayout()
        for number, keycap in ((1, "BOOT"), (2, "RESET"), (3, "BOOT")):
            frame, content = card()
            content.addWidget(label(f"0{number}", "eyebrow"))
            cap = label(keycap, "keycap", wrap=False)
            cap.setAlignment(Qt.AlignmentFlag.AlignCenter)
            content.addWidget(cap)
            text = label()
            text.setMinimumHeight(32)
            self.bindings.append((text, f"usb_boot_{number}"))
            content.addWidget(text)
            steps.addWidget(frame, 1)
        root.addLayout(steps)
        note = label()
        self.bindings.append((note, "usb_boot_note"))
        root.addWidget(note)
        root.addStretch()
        close = QPushButton()
        close.setObjectName("connect")
        self.bindings.append((close, "usb_boot_close"))
        close.clicked.connect(self.accept)
        root.addWidget(close, 0, Qt.AlignmentFlag.AlignRight)
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(self.tr("usb_boot_title"))
        for widget, key in self.bindings:
            widget.setText(self.tr(key))


class USBSetupDialog(QDialog):
    def __init__(self, tr, parent=None, *, scanner=supported_ports, runner=None, bundle=None):
        super().__init__(parent)
        self.tr, self.scanner = tr, scanner
        self.bindings, self.steps = [], []
        self.page, self.stage = 0, ""
        self.selected, self.port_list, self.install_result = None, [], None
        self.install_error = ""
        self.check_key = "usb_check_idle"
        self.camera_verified = False
        self.checked_status = None
        self.boot_dialog = None
        self.bundle_error = False
        self.scan_error = False
        try:
            self.bundle = bundle or load_bundle()
        except InstallError:
            self.bundle, self.bundle_error = None, True
        self.runner = runner or FlashProcess(self)
        self.runner.event.connect(self._worker_event)
        self.runner.succeeded.connect(self._installed)
        self.runner.failed.connect(self._failed)
        self.check_client = OtoscopeClient(self)
        self.check_client.status_received.connect(self._checked)
        self.check_client.frame_received.connect(self._checked_frame)
        self.check_timer = QTimer(self)
        self.check_timer.setSingleShot(True)
        self.check_timer.setInterval(15000)
        self.check_timer.timeout.connect(self._check_timeout)
        self.scan_timer = QTimer(self)
        self.scan_timer.setInterval(1000)
        self.scan_timer.timeout.connect(self._scan)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        if parent is None:
            self.setStyleSheet(STYLE)
        self.resize(820, 730)
        self.setMinimumSize(720, 650)
        self._build_ui()
        self.retranslate()
        self._scan()
        self.scan_timer.start()

    def _label(self, key, name="muted"):
        widget = label(name=name)
        self.bindings.append((widget, key))
        return widget

    def _page(self, title, body):
        panel, content = card()
        content.setContentsMargins(24, 22, 24, 22)
        content.setSpacing(14)
        content.addWidget(self._label(title, "stepTitle"))
        content.addWidget(self._label(body, "helpBody"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(panel)
        self.stack.addWidget(scroll)
        return content

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 22)
        root.setSpacing(16)
        title_row = QHBoxLayout()
        title_row.addWidget(self._label("usb_title", "helpTitle"), 1)
        self.language_buttons = {}
        for language in ("de", "en"):
            button = QPushButton(language.upper())
            button.setObjectName("language")
            button.setCheckable(True)
            button.setAccessibleName("Deutsch" if language == "de" else "English")
            button.clicked.connect(lambda _checked=False, code=language: self._language(code))
            title_row.addWidget(button)
            self.language_buttons[language] = button
        root.addLayout(title_row)
        root.addWidget(self._label("usb_intro"))
        step_row = QHBoxLayout()
        for number in range(4):
            text = label(name="pill", wrap=False)
            text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.steps.append(text)
            step_row.addWidget(text, 1)
        root.addLayout(step_row)
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)
        connect = self._page("usb_plug_title", "usb_plug_body")
        self.device_status = label(name="section")
        connect.addWidget(self.device_status)
        self.ports = QComboBox()
        self.ports.setMinimumHeight(36)
        self.ports.currentIndexChanged.connect(lambda _index: self._render())
        connect.addWidget(self.ports)
        connect.addWidget(self._label("usb_board_note"))
        connect.addStretch()
        install = self._page("usb_install_title", "usb_install_body")
        self.firmware_label = label(name="section")
        self.target_label = label()
        install.addWidget(self.firmware_label)
        install.addWidget(self.target_label)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setMinimumHeight(22)
        install.addWidget(self.progress)
        self.install_status = label(name="section")
        install.addWidget(self.install_status)
        self.busy_note = self._label("usb_busy_hint")
        install.addWidget(self.busy_note)
        self.details_button = QPushButton()
        self.details_button.setObjectName("link")
        self.details_button.clicked.connect(lambda: self.log.setVisible(not self.log.isVisible()))
        install.addWidget(self.details_button)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(300)
        self.log.setMinimumHeight(90)
        self.log.setMaximumHeight(150)
        self.log.hide()
        install.addWidget(self.log)
        install.addStretch()
        wifi = self._page("usb_wifi_title", "usb_wifi_body")
        credentials, rows = card()
        self.ssid_label = label(name="section", wrap=False)
        self.password_label = label(name="section", wrap=False)
        for key, value in (("network_name", self.ssid_label), ("password", self.password_label)):
            row = QHBoxLayout()
            row.addWidget(self._label(key))
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(value)
            rows.addLayout(row)
        wifi.addWidget(credentials)
        self.copy_button = QPushButton()
        self.copy_button.clicked.connect(self._copy_wifi)
        wifi.addWidget(self.copy_button, 0, Qt.AlignmentFlag.AlignLeft)
        wifi.addWidget(self._label("usb_wifi_note"))
        wifi.addWidget(self._label("usb_reset_note"))
        self.led_note = label()
        wifi.addWidget(self.led_note)
        wifi.addStretch()
        check = self._page("usb_check_title", "usb_check_body")
        self.check_status = label(name="section")
        check.addWidget(self.check_status)
        self.check_button = QPushButton()
        self.check_button.clicked.connect(self._start_check)
        check.addWidget(self.check_button, 0, Qt.AlignmentFlag.AlignLeft)
        self.check_image = QLabel()
        self.check_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check_image.setMinimumHeight(180)
        self.check_image.setObjectName("checkImage")
        self.check_image.hide()
        check.addWidget(self.check_image)
        check.addStretch()
        footer = QHBoxLayout()
        self.boot_button = QPushButton()
        self.boot_button.setObjectName("link")
        self.boot_button.setIcon(icon("help"))
        self.boot_button.clicked.connect(self._boot_help)
        footer.addWidget(self.boot_button)
        footer.addStretch()
        self.close_button = QPushButton()
        self.close_button.clicked.connect(self.reject)
        footer.addWidget(self.close_button)
        self.back_button = QPushButton()
        self.back_button.clicked.connect(self._back)
        footer.addWidget(self.back_button)
        self.next_button = QPushButton()
        self.next_button.setObjectName("connect")
        self.next_button.clicked.connect(self._next)
        footer.addWidget(self.next_button)
        root.addLayout(footer)

    def _language(self, code):
        parent = self.parent()
        if parent is not None and hasattr(parent, "set_language"):
            parent.set_language(code)
        else:
            self.tr.language = code
        self.retranslate()

    def retranslate(self):
        self.setWindowTitle(self.tr("usb_setup"))
        for widget, key in self.bindings:
            widget.setText(self.tr(key))
        for language, button in self.language_buttons.items():
            button.setChecked(self.tr.language == language)
        self.ports.setPlaceholderText(self.tr("usb_choose"))
        self.ports.setAccessibleName(self.tr("usb_choose"))
        self.copy_button.setText(self.tr("usb_copy"))
        self.details_button.setText(self.tr("usb_details"))
        self.check_button.setText(self.tr("usb_check"))
        self.boot_button.setText(self.tr("usb_boot_link"))
        self.close_button.setText(self.tr("usb_close"))
        self.back_button.setText(self.tr("back"))
        version = self.bundle.manifest["version"] if self.bundle else "—"
        self.firmware_label.setText(self.tr("usb_firmware", version=version))
        if self.boot_dialog:
            self.boot_dialog.retranslate()
        self._render()

    def _render(self):
        busy = self.runner.busy
        for number, text in enumerate(self.steps):
            set_pill(text, f"0{number+1}  {self.tr(f'usb_step_{number}')}", "demo" if self.page == number else "offline")
        self.stack.setCurrentIndex(self.page)
        found_key = "usb_one_device" if len(self.port_list) == 1 else "usb_many_devices" if self.port_list else "usb_no_device"
        self.device_status.setText(self.tr("usb_error_bundle" if self.bundle_error else "usb_scan_error" if self.scan_error else found_key))
        self.target_label.setText(self.tr("usb_selected", port=self.selected["device"]) if self.selected else "")
        status_key = "usb_error_"+self.install_error if self.install_error else "usb_stage_"+self.stage if busy and self.stage else "usb_install_ready"
        self.install_status.setText(self.tr(status_key))
        self.busy_note.setVisible(busy)
        self.ports.setEnabled(not busy and not self.bundle_error)
        self.boot_button.setEnabled(not busy)
        self.boot_button.setVisible(self.page < 2)
        self.close_button.setEnabled(not busy)
        self.back_button.setVisible(self.page > 0 and not self.install_result)
        self.back_button.setEnabled(not busy)
        self.next_button.setVisible(not busy)
        key = "usb_finish" if self.page == 3 else "usb_retry" if self.page == 1 and self.install_error else "usb_install" if self.page == 1 else "next"
        self.next_button.setText(self.tr(key))
        enabled = (not self.bundle_error and self.ports.currentIndex() >= 0) if self.page == 0 else self.camera_verified if self.page == 3 else True
        self.next_button.setEnabled(enabled and not busy)
        self.check_button.setEnabled(not self.check_timer.isActive())
        self.check_status.setText(self.tr(self.check_key))
        if self.install_result:
            self.ssid_label.setText(self.install_result["ssid"])
            self.password_label.setText(self.install_result["password"])
            led_note = "usb_led_note_enabled" if self.install_result.get("led_configured") else "usb_led_note"
            self.led_note.setText(self.tr(led_note))

    def _scan(self):
        if self.page != 0 or self.runner.busy:
            return
        try:
            ports = [dict(port) for port in self.scanner()]
            self.scan_error = False
        except Exception:
            self.scan_error = True
            self.port_list = []
            self.ports.clear()
            self._render()
            return
        if ports != self.port_list:
            previous = self.ports.currentData()
            self.port_list = ports
            self.ports.blockSignals(True)
            self.ports.clear()
            for port in ports:
                self.ports.addItem(f"{port['description']} — {port['device']}", port)
            index = next((i for i, port in enumerate(ports) if port == previous), 0 if len(ports) == 1 else -1)
            self.ports.setCurrentIndex(index)
            self.ports.blockSignals(False)
        self._render()

    def _next(self):
        if self.runner.busy:
            return
        if self.page == 0:
            if self.ports.currentIndex() < 0 or self.bundle_error:
                return
            self.selected = dict(self.ports.currentData())
            self.page = 1
        elif self.page == 1:
            self._install()
            return
        elif self.page == 2:
            self.page = 3
        elif self.page == 3 and self.camera_verified:
            parent = self.parent()
            self._cleanup()
            self.accept()
            if parent is not None and hasattr(parent, "_connect_after_setup"):
                parent._connect_after_setup()
            return
        self._render()

    def _back(self):
        if not self.runner.busy and not self.install_result:
            self.page = max(0, self.page - 1)
            self._scan()
            self._render()

    def _install(self):
        if not self.selected or self.bundle_error:
            return
        # BOOT/RESET can change the port name. Follow the same physical USB
        # location/serial where available; otherwise return to explicit selection.
        try:
            current = [dict(port) for port in self.scanner()]
        except Exception:
            current = []
        if not any(port["device"] == self.selected["device"] for port in current):
            same_device = [port for port in current if any(
                self.selected.get(key) and self.selected[key] == port.get(key)
                for key in ("serial_number", "location"))]
            if len(same_device) == 1:
                self.selected = same_device[0]
            else:
                self.page = 0
                self._scan()
                return
        parent = self.parent()
        if parent is not None and hasattr(parent, "_prepare_for_flash"):
            parent._prepare_for_flash()
        self.install_error, self.stage = "", "connect"
        self.log.clear()
        self.progress.setValue(0)
        self.runner.start(self.selected)
        self._render()

    def _worker_event(self, event):
        if event.get("event") == "stage":
            self.stage = event["stage"]
        if event.get("event") == "log":
            self.log.appendPlainText(event.get("text", ""))
        if "progress" in event:
            self.progress.setValue(max(self.progress.value(), int(event["progress"])))
        self._render()

    def _installed(self, result):
        self.install_result = result
        self.page = 2
        self._render()

    def _failed(self, code, detail):
        self.install_error = code if "usb_error_"+code in TEXT else "internal"
        self.log.appendPlainText(detail)
        self._render()

    def _boot_help(self):
        if self.runner.busy:
            return
        if self.boot_dialog is None:
            self.boot_dialog = BootHelp(self.tr, self)
        self.boot_dialog.retranslate()
        self.boot_dialog.show()

    def _copy_wifi(self):
        if self.install_result:
            QApplication.clipboard().setText(f"{self.install_result['ssid']}\n{self.install_result['password']}")
            self.copy_button.setText(self.tr("copied"))

    def _start_check(self):
        if not self.install_result or self.check_timer.isActive():
            return
        self.camera_verified = False
        self.checked_status = None
        self.check_image.hide()
        self.check_key = "usb_check_wait"
        self.check_timer.start()
        self.check_client.connect_device("192.168.4.1")
        self._render()

    def _checked(self, status):
        if not self.install_result or not self.check_timer.isActive():
            return
        if status.get("device_id") != self.install_result["device_id"]:
            self.check_key = "usb_check_wrong"
        elif status.get("firmware_version") != self.install_result["firmware_version"]:
            self.check_key = "usb_check_version"
        elif not status.get("camera_ok") or not status.get("stream_ok"):
            self.check_key = "usb_check_camera"
        else:
            self.checked_status = status
            self.check_key = "usb_check_image"
            self._render()
            return
        self.checked_status = None
        self.check_timer.stop()
        self.check_client.disconnect_device()
        self._render()

    def _checked_frame(self, data):
        if not self.check_timer.isActive() or self.checked_status is None:
            return
        image = QImage.fromData(data, "JPEG")
        if image.isNull():
            return
        self.camera_verified = True
        self.check_key = "usb_check_ok" if self.checked_status.get("led_supported") else "usb_check_led_off"
        self.check_image.setPixmap(QPixmap.fromImage(image).scaled(QSize(420, 200),
                                   Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        self.check_image.show()
        self.check_timer.stop()
        self.check_client.disconnect_device()
        self._render()

    def _check_timeout(self):
        self.check_key = "usb_check_timeout"
        self.check_client.disconnect_device()
        self._render()

    def _cleanup(self):
        self.scan_timer.stop()
        self.check_timer.stop()
        self.check_client.disconnect_device()
        if self.boot_dialog:
            self.boot_dialog.close()

    def reject(self):
        if not self.runner.busy:
            self._cleanup()
            super().reject()

    def closeEvent(self, event):
        if self.runner.busy:
            event.ignore()
        else:
            self._cleanup()
            event.accept()
