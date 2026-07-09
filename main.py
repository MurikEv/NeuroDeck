from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import MainWindow
from screens.keyboard_controller import KeyboardController
from screens.ai_screen import AiScreen
from screens.menu_screen import MainMenu
from screens.calculator_screen import Calculator
from screens.camera_screen import CameraScreen
from services import network_service
from services.ai_service import AiService
import sys
import queue
import keyboard
import state

    # --- Creating main window --- #

app = QApplication(sys.argv)
window = MainWindow()
state.main_window = window
window.show()

    # --- Screens --- #

menu = MainMenu(window)
window.menu_controller = menu

virtual_keyboard = KeyboardController(window)
window.keyboard_controller = virtual_keyboard

ai = AiScreen(window)
window.ai_controller = ai

calculator = Calculator(window)
window.calculator_controller = calculator

camera_controller = CameraScreen(window)
window.camera_controller = camera_controller


# --- Network --- #
network_service.start_network_monitoring()


keyboard.add_hotkey("q", lambda: state.ui_queue.put(("menu", None)))

# --- Screen switcher (queue) --- #

def check_queue():
    try:
        while True:
            action, data = state.ui_queue.get_nowait()
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
                AiService
    except queue.Empty:
        pass

timer = QTimer()
timer.timeout.connect(check_queue)
timer.start(10)

sys.exit(app.exec())
