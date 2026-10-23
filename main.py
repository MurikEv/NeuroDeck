from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import MainWindow
from screens.keyboard_controller import KeyboardController
from screens.ai_screen import AIController
from screens.menu_screen import MenuController
from screens.notepad_screen import NotepadController
from screens.calculator_screen import CalculatorController
from screens.camera_screen import CameraController
from screens.file_explorer_screen import FileExplorerController
from screens.settings_screen import SettingsController
from services import network_service
from services.developer_keyboard import DeveloperKeyboardController
import os
import sys
import queue
import state


# Developer-only opt-in. Keep False for the touch-operated device.
ENABLE_DEVELOPER_KEYBOARD = False


def main():
    app = QApplication(sys.argv)
    display = None
    display_mirror = None
    display_safe_to_close = True
    developer_keyboard = None
    touch_service = None

    try:
        # --- Optional SPI status display --- #
        try:
            from services.display_service import ST7796Display

            display = ST7796Display()
            display.fill_color(0x0000)
            display.draw_text("NEURODECK", x=10, y=20, background=0x0000)
            display.draw_text("BOOTING...", x=10, y=60, background=0x0000)
        except Exception as exc:
            print(f"ST7796 display unavailable: {exc}", file=sys.stderr)
            if display is not None:
                display.close()
                display = None

        # --- Creating main window --- #
        window = MainWindow()
        state.main_window = window
        window.show()

        if display is not None:
            try:
                display.draw_text("UI READY", x=10, y=100, background=0x0000)
            except Exception as exc:
                print(f"ST7796 display unavailable: {exc}", file=sys.stderr)
                display.close()
                display = None

        # --- Controllers --- #
        menu_controller = MenuController(window)
        window.menu_controller = menu_controller
        developer_keyboard = DeveloperKeyboardController(
            app, window, enabled=ENABLE_DEVELOPER_KEYBOARD
        )

        keyboard_controller = KeyboardController(window)
        window.keyboard_controller = keyboard_controller

        ai_controller = AIController(window)
        window.ai_controller = ai_controller

        calculator_controller = CalculatorController(window)
        window.calculator_controller = calculator_controller

        camera_controller = CameraController(window)
        window.camera_controller = camera_controller

        file_explorer_controller = FileExplorerController(window)
        window.file_explorer_controller = file_explorer_controller

        settings_controller = SettingsController(window)
        window.settings_controller = settings_controller

        notepad_controller = NotepadController(window)
        window.notepad_controller = notepad_controller

        # --- Network --- #
        network_service.start_network_monitoring()

        # --- Screen switcher (queue) --- #
        def process_ui_queue():
            try:
                while True:
                    action, _payload = state.ui_queue.get_nowait()
                    if action != "notepad" and not notepad_controller.save_pending():
                        continue
                    if action == "menu":
                        camera_controller.stop()
                        window.switch_to("menu_screen")
                    elif action == "calculator":
                        camera_controller.stop()
                        window.switch_to("calculator_screen")
                    elif action == "camera":
                        window.switch_to("camera_screen")
                        camera_controller.start()
                    elif action == "ai":
                        camera_controller.stop()
                        window.switch_to("ai_screen")
                        window.ai_input.setFocus()
                    elif action == "file_explorer":
                        camera_controller.stop()
                        window.switch_to("fileexplorer_screen")
                    elif action == "settings":
                        camera_controller.stop()
                        window.switch_to("settings_screen")
                    elif action == "notepad":
                        camera_controller.stop()
                        window.switch_to("notepad_screen")
            except queue.Empty:
                pass

        ui_queue_timer = QTimer()
        ui_queue_timer.timeout.connect(process_ui_queue)
        ui_queue_timer.start(10)

        # --- Transitional HDMI -> SPI mirror --- #
        display_mirror_enabled = os.getenv("NEURODECK_SPI_MIRROR", "1").lower()
        if (
            display is not None
            and display_mirror_enabled not in ("0", "false", "no")
        ):
            try:
                from services.qt_display_mirror import QtDisplayMirror

                display_rotation = int(
                    os.getenv("NEURODECK_SPI_ROTATION", "90")
                )
                display_mirror = QtDisplayMirror(
                    window,
                    display,
                    rotation=display_rotation,
                )
                display_mirror.start()
            except Exception as exc:
                print(f"ST7796 mirror unavailable: {exc}", file=sys.stderr)
                if display_mirror is not None:
                    if display_mirror.stop():
                        display_mirror = None

        # --- Optional touch input for the SPI mirror --- #
        if (
            display_mirror is not None
            and os.getenv("NEURODECK_TOUCH", "1").lower() not in ("0", "false", "no")
        ):
            try:
                from services.touch_service import QtTouchService

                touch_service = QtTouchService(window, rotation=display_rotation)
                touch_service.start()
            except Exception as exc:
                print(f"FT6336 touch unavailable: {exc}", file=sys.stderr)
                if touch_service is not None:
                    touch_service.close()
                    touch_service = None

        return app.exec()
    finally:
        if touch_service is not None:
            touch_service.close()
        if developer_keyboard is not None:
            developer_keyboard.close()
        if display_mirror is not None:
            display_safe_to_close = display_mirror.stop()
        if display is not None and display_safe_to_close:
            display.close()


if __name__ == "__main__":
    sys.exit(main())
