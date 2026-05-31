from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QKeyEvent
import state

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(r"screens/main_window.ui", self)
        self.stackedWidget.setCurrentWidget(self.menu_screen)

    def switch_to(self, screen_name):
        screen = getattr(self, screen_name, None)
        if screen:
            self.stackedWidget.setCurrentWidget(screen)

    def keyPressEvent(self, event: QKeyEvent):
        state.ui_queue.put(("key", event.key()))