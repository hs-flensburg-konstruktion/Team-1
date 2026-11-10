"""Non-modal, keyboard-accessible connection guide in the selected language."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QApplication, QButtonGroup, QDialog, QHBoxLayout,
                               QPushButton, QScrollArea, QStackedWidget,
                               QVBoxLayout, QWidget)

from .widgets import STYLE, card, icon, label


class ConnectionGuide(QDialog):
    setup_requested = Signal()
    def __init__(self, tr, parent=None):
        super().__init__(parent)
        self.tr = tr
        self.bindings = []
        self.page = 0
        self.resize(760, 650)
        self.setMinimumSize(660, 590)
        if parent is None:
            self.setStyleSheet(STYLE)
        self.setWindowModality(Qt.WindowModality.NonModal)
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 24)
        root.setSpacing(18)
        self.heading = self._label("help_title", "helpTitle")
        root.addWidget(self.heading)
        root.addWidget(self._label("help_subtitle"))
        nav = QHBoxLayout()
        nav.setSpacing(8)
        self.steps = []
        self.group = QButtonGroup(self)
        for number in range(1, 5):
            button = QPushButton()
            button.setObjectName("step")
            button.setCheckable(True)
            self.group.addButton(button, number - 1)
            button.clicked.connect(lambda _checked=False, index=number-1: self.go(index))
            nav.addWidget(button, 1)
            self.steps.append(button)
        root.addLayout(nav)
        self.stack = QStackedWidget()
        self.step_labels = []
        for number in range(1, 5):
            frame, content = card()
            content.setContentsMargins(24, 24, 24, 24)
            content.setSpacing(16)
            counter = label(name="eyebrow", wrap=False)
            self.step_labels.append(counter)
            content.addWidget(counter)
            content.addWidget(self._label(f"step_{number}_title", "stepTitle"))
            content.addWidget(self._label(f"step_{number}_body", "helpBody"))
            if number == 1:
                setup = QPushButton()
                setup.setObjectName("connect")
                self.bindings.append((setup, "usb_setup"))
                setup.clicked.connect(self.setup_requested.emit)
                content.addWidget(setup, 0, Qt.AlignmentFlag.AlignLeft)
            if number == 2:
                credentials, info = card()
                for key, value in (("network_name", "Otoskop-XXXXXX"), ("password", "Otoskop-2026")):
                    row = QHBoxLayout()
                    row.addWidget(self._label(key))
                    text = label(value, "section", wrap=False)
                    text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                    row.addWidget(text, 0, Qt.AlignmentFlag.AlignRight)
                    info.addLayout(row)
                content.addWidget(credentials)
                self.copy_button = QPushButton()
                self.copy_button.setObjectName("link")
                self.copy_button.clicked.connect(self.copy_wifi)
                content.addWidget(self.copy_button)
            note, note_layout = card()
            note.setObjectName("helpNote")
            note_layout.setContentsMargins(15, 13, 15, 13)
            note_layout.addWidget(self._label(f"step_{number}_note"))
            content.addWidget(note)
            content.addStretch()
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setWidget(frame)
            self.stack.addWidget(scroll)
        trouble = QWidget()
        trouble.setObjectName("sidebar")
        trouble_layout = QVBoxLayout(trouble)
        trouble_layout.setContentsMargins(0, 0, 0, 0)
        trouble_layout.setSpacing(10)
        trouble_layout.addWidget(self._label("trouble_title", "stepTitle"))
        for number in range(1, 5):
            frame, content = card()
            content.setContentsMargins(18, 13, 18, 13)
            content.setSpacing(6)
            content.addWidget(self._label(f"trouble_{number}_title", "section"))
            content.addWidget(self._label(f"trouble_{number}_body"))
            trouble_layout.addWidget(frame)
        trouble_layout.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(trouble)
        self.stack.addWidget(scroll)
        root.addWidget(self.stack, 1)
        footer = QHBoxLayout()
        self.trouble_button = QPushButton()
        self.trouble_button.setObjectName("link")
        self.trouble_button.setIcon(icon("help"))
        self.trouble_button.clicked.connect(lambda: self.go(4))
        footer.addWidget(self.trouble_button)
        footer.addStretch()
        self.back_button = QPushButton()
        self.back_button.clicked.connect(lambda: self.go(max(0, self.page - 1)))
        footer.addWidget(self.back_button)
        self.next_button = QPushButton()
        self.next_button.setObjectName("connect")
        self.next_button.setDefault(True)
        self.next_button.clicked.connect(self.next_page)
        footer.addWidget(self.next_button)
        root.addLayout(footer)
        self.retranslate()

    def _label(self, key, name="muted"):
        widget = label(name=name)
        self.bindings.append((widget, key))
        return widget

    def retranslate(self):
        self.setWindowTitle(self.tr("help"))
        for widget, key in self.bindings:
            widget.setText(self.tr(key))
        for number, button in enumerate(self.steps, 1):
            button.setText(f"0{number}  {self.tr(f'step_{number}_short')}")
        for number, counter in enumerate(self.step_labels, 1):
            counter.setText(self.tr("step", number=number))
        self.copy_button.setText(self.tr("copy_wifi"))
        self.trouble_button.setText(self.tr("troubleshoot"))
        self.back_button.setText(self.tr("back"))
        self.go(self.page)

    def go(self, page):
        self.page = page
        self.stack.setCurrentIndex(page)
        self.group.setExclusive(False)
        for index, button in enumerate(self.steps):
            button.setChecked(index == page)
        self.group.setExclusive(True)
        self.back_button.setVisible(page > 0)
        self.trouble_button.setVisible(page < 4)
        self.next_button.setText(self.tr("done" if page >= 3 else "next"))

    def next_page(self):
        if self.page >= 3:
            self.accept()
        else:
            self.go(self.page + 1)

    def copy_wifi(self):
        QApplication.clipboard().setText("Otoskop-2026")
        self.copy_button.setText(self.tr("copied"))
