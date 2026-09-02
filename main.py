from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import MainWindow
from screens.keyboard_controller import KeyboardController
from screens.ai_screen import AIController
from screens.menu_screen import MenuController
from screens.calculator_screen import CalculatorController
from screens.camera_screen import CameraController
from screens.file_explorer_screen import FileExplorerController
from screens.settings_screen import SettingsController
from services import network_service
import sys
import queue
import keyboard
import state

    # --- Creating main window --- #

app = QApplication(sys.argv)
window = MainWindow()
state.main_window = window
window.show()

    # --- Controllers --- #

menu_controller = MenuController(window)
window.menu_controller = menu_controller

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


# --- Network --- #
network_service.start_network_monitoring()


# --- Screen switcher (queue) --- #
def process_ui_queue():
    try:
        while True:
            action, _payload = state.ui_queue.get_nowait()
            if action == "menu":
                camera_controller.stop()
                window.switch_to("menu_screen")       #  _screen load from .ui
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
    except queue.Empty:
        pass

ui_queue_timer = QTimer()
ui_queue_timer.timeout.connect(process_ui_queue)
ui_queue_timer.start(10)

sys.exit(app.exec())
