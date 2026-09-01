from pathlib import Path

from PyQt6.QtCore import Qt

import state


STYLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "styles"
    / "settings_screen.qss"
)


class SettingsController:
    def __init__(self, window):
        self.window = window
        self.screen = window.settings_screen
        self.brightness_overlay = window.brightness_overlay

        self.screen.setStyleSheet(STYLE_PATH.read_text(encoding="utf-8"))

        self.brightness_overlay.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents,
            True,
        )
        self.brightness_overlay.raise_()

        self.window.settingsBackButton.clicked.connect(self.back_to_menu)
        self.window.stngs_brightness_slider.valueChanged.connect(
            self.update_brightness_value
        )
        self.window.stngs_notifications_toggle.toggled.connect(
            self.update_notifications_text
        )

        self.update_brightness_value(self.window.stngs_brightness_slider.value())
        self.update_notifications_text(
            self.window.stngs_notifications_toggle.isChecked()
        )

    def back_to_menu(self):
        state.ui_queue.put(("menu", None))

    def update_brightness_value(self, value):
        self.window.stngs_brightness_value.setText(f"{value}%")
        overlay_alpha = round(255 * (100 - value) / 100)
        self.brightness_overlay.setStyleSheet(
            f"background-color: rgba(0, 0, 0, {overlay_alpha}); border: none;"
        )

    def update_notifications_text(self, enabled):
        self.window.stngs_notifications_toggle.setText("ON" if enabled else "OFF")
