from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

import state


STYLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "styles"
    / "settings_screen.qss"
)


class SettingsController:
    """Builds and manages the visual content of the Designer Settings page."""

    def __init__(self, window):
        self.window = window
        self.screen = window.settings_screen
        self._hide_designer_placeholders()
        self._build_ui()
        self.screen.setStyleSheet(STYLE_PATH.read_text(encoding="utf-8"))

    def _hide_designer_placeholders(self):
        self.window.stngs_about_btn.hide()
        self.window.stngs_about_frame.hide()

    def _build_ui(self):
        root_layout = QVBoxLayout(self.screen)
        root_layout.setContentsMargins(4, 4, 4, 4)
        root_layout.setSpacing(0)

        shell = QFrame()
        shell.setObjectName("settingsShell")
        root_layout.addWidget(shell)

        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(5, 4, 5, 4)
        shell_layout.setSpacing(4)
        shell_layout.addWidget(self._build_header())
        shell_layout.addWidget(self._build_body(), 1)

    def _build_header(self):
        header = QFrame()
        header.setObjectName("settingsHeader")
        header.setFixedHeight(31)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(5, 0, 6, 0)
        layout.setSpacing(6)

        self.settings_back_btn = QPushButton("<")
        self.settings_back_btn.setObjectName("settingsBackButton")
        self.settings_back_btn.setToolTip("Back to menu")
        self.settings_back_btn.setFixedSize(27, 22)
        self.settings_back_btn.clicked.connect(self.back_to_menu)
        layout.addWidget(self.settings_back_btn)

        brand = QLabel("NEURODECK")
        brand.setObjectName("settingsBrand")
        layout.addWidget(brand)
        layout.addStretch()
        return header

    def back_to_menu(self):
        state.ui_queue.put(("menu", None))

    def _build_body(self):
        body = QFrame()
        body.setObjectName("settingsBody")

        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._build_navigation())
        layout.addWidget(self._build_content(), 1)
        return body

    def _build_navigation(self):
        navigation = QFrame()
        navigation.setObjectName("settingsNavigation")
        navigation.setFixedWidth(104)

        layout = QVBoxLayout(navigation)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        self.stngs_system_btn = QPushButton("SYSTEM")
        self.stngs_system_btn.setObjectName("stngs_system_btn")
        self.stngs_system_btn.setProperty("navItem", True)
        self.stngs_system_btn.setProperty("active", True)
        self.stngs_system_btn.setFixedHeight(34)
        layout.addWidget(self.stngs_system_btn)

        layout.addStretch()
        return navigation

    def _build_content(self):
        content = QFrame()
        content.setObjectName("settingsContent")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_content_header())

        scroll = QScrollArea()
        scroll.setObjectName("settingsOptionsScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        options = QWidget()
        options.setObjectName("settingsOptions")
        options_layout = QVBoxLayout(options)
        options_layout.setContentsMargins(0, 0, 0, 0)
        options_layout.setSpacing(0)

        options_layout.addWidget(self._slider_row("BRIGHTNESS", 70, "brightness"))
        options_layout.addWidget(self._toggle_row("NOTIFICATIONS", True))
        options_layout.addWidget(
            self._combo_row("LANGUAGE", ("ENGLISH", "POLSKI", "RUSSIAN"), "language")
        )
        options_layout.addWidget(
            self._combo_row("AUTO LOCK", ("1 MIN", "5 MIN", "15 MIN", "NEVER"), "auto_lock", 1)
        )
        options_layout.addWidget(self._about_row())
        options_layout.addStretch()

        scroll.setWidget(options)
        layout.addWidget(scroll, 1)
        return content

    def _build_content_header(self):
        header = QFrame()
        header.setObjectName("settingsContentHeader")
        header.setFixedHeight(37)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(9, 0, 9, 0)
        layout.setSpacing(7)

        index = QLabel("SYS")
        index.setObjectName("settingsSectionIndex")
        index.setAlignment(Qt.AlignmentFlag.AlignCenter)
        index.setFixedSize(29, 21)
        layout.addWidget(index)

        title = QLabel("SETTINGS")
        title.setObjectName("settingsSectionTitle")
        layout.addWidget(title)

        subtitle = QLabel("// SYSTEM CONTROL")
        subtitle.setProperty("role", "subtitle")
        layout.addWidget(subtitle)
        layout.addStretch()
        return header

    def _base_row(self, height):
        row = QFrame()
        row.setProperty("settingRow", True)
        row.setFixedHeight(height)
        return row

    def _slider_row(self, title, value, key):
        row = self._base_row(45)
        layout = QVBoxLayout(row)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(1)

        labels = QHBoxLayout()
        labels.setContentsMargins(0, 0, 0, 0)
        name = QLabel(title)
        name.setProperty("role", "settingName")
        labels.addWidget(name)
        labels.addStretch()

        value_label = QLabel(f"{value}%")
        value_label.setProperty("role", "settingValue")
        labels.addWidget(value_label)
        layout.addLayout(labels)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(value)
        slider.valueChanged.connect(lambda current, label=value_label: label.setText(f"{current}%"))
        layout.addWidget(slider)

        setattr(self, f"stngs_{key}_slider", slider)
        setattr(self, f"stngs_{key}_value", value_label)
        return row

    def _toggle_row(self, title, checked):
        row = self._base_row(39)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 4, 10, 4)

        name = QLabel(title)
        name.setProperty("role", "settingName")
        layout.addWidget(name)
        layout.addStretch()

        self.stngs_notifications_toggle = QPushButton("ON" if checked else "OFF")
        self.stngs_notifications_toggle.setObjectName("stngs_notifications_toggle")
        self.stngs_notifications_toggle.setProperty("toggle", True)
        self.stngs_notifications_toggle.setCheckable(True)
        self.stngs_notifications_toggle.setChecked(checked)
        self.stngs_notifications_toggle.setFixedSize(56, 24)
        self.stngs_notifications_toggle.toggled.connect(
            lambda active: self.stngs_notifications_toggle.setText("ON" if active else "OFF")
        )
        layout.addWidget(self.stngs_notifications_toggle)
        return row

    def _combo_row(self, title, values, key, selected=0):
        row = self._base_row(39)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 4, 10, 4)

        name = QLabel(title)
        name.setProperty("role", "settingName")
        layout.addWidget(name)
        layout.addStretch()

        combo = QComboBox()
        combo.addItems(values)
        combo.setCurrentIndex(selected)
        combo.setFixedSize(105, 25)
        combo.setObjectName(f"stngs_{key}_combo")
        layout.addWidget(combo)
        setattr(self, f"stngs_{key}_combo", combo)
        return row

    def _about_row(self):
        row = self._base_row(40)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 4, 10, 4)

        name = QLabel("ABOUT DEVICE")
        name.setProperty("role", "settingName")
        layout.addWidget(name)
        layout.addStretch()

        value = QLabel("RADXA ZERO  >")
        value.setProperty("role", "settingValue")
        layout.addWidget(value)
        return row
