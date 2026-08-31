from pathlib import Path

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

        self.screen.setStyleSheet(STYLE_PATH.read_text(encoding="utf-8"))

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

    def update_notifications_text(self, enabled):
        self.window.stngs_notifications_toggle.setText("ON" if enabled else "OFF")
