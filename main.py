from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from main_window import MainWindow
from screens.ai_screen import AiScreen
from screens.menu_screen import MainMenu
from screens.calculator_screen import Calculator
from services.camera_service import camera
from services import network_service
import sys
import threading
import queue
import keyboard
import state



app = QApplication(sys.argv)
window = MainWindow()
state.main_window = window
window.show()

ai = AiScreen(window)
menu = MainMenu(window)
window.menu_controller = menu
calculator = Calculator(window)
window.calculator_controller = calculator

network_service.start_network_monitoring()

keyboard.add_hotkey("q", lambda: state.ui_queue.put(("menu", None)))

def check_queue():
    try:
        while True:
            action, data = state.ui_queue.get_nowait()
            if action == "menu":
                window.switch_to("menu_screen")       #  _screen load from .ui
            elif action == "calculator":
                window.switch_to("calculator_screen")
            elif action == "camera":
                state.stop_camera.clear()
                threading.Thread(target=camera, daemon=True).start()
            elif action == "ai":
                window.switch_to("ai_screen")
    except queue.Empty:
        pass

timer = QTimer()
timer.timeout.connect(check_queue)
timer.start(10)

sys.exit(app.exec())