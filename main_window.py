from PyQt6 import uic
from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtGui import QKeyEvent

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(r"screens/main_window.ui", self)
        self.stackedWidget.setCurrentWidget(self.menu_screen)
        self.menu_controller = None
        self.calculator_controller = None

    def switch_to(self, screen_name):
        screen = getattr(self, screen_name, None)
        if screen:
            self.stackedWidget.setCurrentWidget(screen)

    def keyPressEvent(self, event: QKeyEvent):
        current_screen = self.stackedWidget.currentWidget()
        if current_screen == self.menu_screen and self.menu_controller is not None:
            self.menu_controller.handle_key(event)
        elif current_screen == self.calculator_screen and self.calculator_controller is not None:
            self.calculator_controller.handle_key(event)